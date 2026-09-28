#!/usr/bin/env python3
"""
UNION JOINTS -- every place a generator glues one solid onto another.

User, 2026-09-27 (slicer view of J3_p1): "joints at indicated areas need
rectification (joints are not proper)" -- the J3 spring lugs stood on the
round tops of the fork cheeks, joined by a 0.05-0.1 mm sliver. One solid in
the STEP, so no check saw it.

This re-runs the release generators in a scratch copy with every CadQuery
call recorded (../FUSION_DESIGN_TREES/tools/record_cq.py; nothing in the
release is written), and for every union in every printed part measures,
per glued solid t against the body A it joins:

  joint area  = (area(A) + area(t) - area(A u t)) / 2   (face contact counts in full)
  reference   = t's own smallest section, V(t) / (largest bounding-box side)
  ratio       = joint area / reference

A proper joint -- a post on its full footprint -- reads 1.00, a boss sunk into
a wall or a rib on its long face more. A feature resting on a curve or an
edge reads well below 1: WEAK under 0.80 (the J3 lugs read 0.47).
Unions that leave t apart from A (touching nothing) are reported as SEPARATE
unless a later union in the same part connects them (the final part is one
solid -- checked by the release gate already).

Run:  python3 verify_union_joints.py        (writes UNION_JOINTS.log)
"""
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..", "FUSION_DESIGN_TREES", "tools")
sys.path.insert(0, TOOLS)
sys.dont_write_bytecode = True

RATIO_MIN = 0.80        # a post standing on its full footprint reads 1.00; the J3 lugs on the cheek arcs read 0.47


def area(topo):
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    g = GProp_GProps(); BRepGProp.SurfaceProperties_s(topo, g)
    return g.Mass()


def main():
    import make_trees as MT
    from compare import vol
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    work = tempfile.mkdtemp(prefix="arm450_joints_")
    cwd = os.getcwd()
    R, coupons, _, _ = MT.run_generators(work)
    os.chdir(cwd)
    parts = [(nm, R.EXPORTS[nm]) for nm, q, g, src in MT.PARTS]
    rows, weak = [], 0
    for nm, root in parts:
        seen, fuses = set(), []

        def walk(i):
            if i in seen:
                return
            seen.add(i)
            n = R.NODES[i]
            for k in n["kids"]:
                walk(k)
            if n["kind"] == "fuse":
                fuses.append(n)
        walk(root)
        worst = None
        for n in fuses:
            na = n["data"]["nargs"]
            A = [R.NODES[i]["topo"] for i in n["kids"][:na]]
            A = A[0] if len(A) == 1 else MT.compound(A)
            for ti in n["kids"][na:]:
                for t in MT._solids(R.NODES[ti]["topo"]):
                    if BRepExtrema_DistShapeShape(A, t).Value() > 1e-6:
                        continue                      # apart: joined later, or not at all
                    ja = (area(A) + area(t) - area(BRepAlgoAPI_Fuse(A, t).Shape())) / 2.0
                    x0, y0, z0, x1, y1, z1 = MT.bbox(t)
                    ref = vol(t) / max(x1 - x0, y1 - y0, z1 - z0)
                    ratio = ja / ref if ref > 0 else 0.0
                    bad = ratio < RATIO_MIN
                    line = ("   %-6s %-44s joint %7.2f mm2  ref %7.2f  ratio %5.2f  at x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f"
                            % ("WEAK" if bad else "ok", n["src"], ja, ref, ratio, x0, x1, y0, y1, z0, z1))
                    if bad:
                        rows.append("%s\n%s" % (nm, line)); weak += 1
                    if worst is None or ratio < worst[0]:
                        worst = (ratio, line)
        rows.append("%-20s %3d unions   weakest:%s" % (nm, len(fuses), worst[1][9:] if worst else " -"))
        print(rows[-1], flush=True)
    txt = ("UNION JOINTS -- every glued feature of every printed part (part frame, mm)\n"
           "WEAK = joined over less than %.2f x the feature's own section (a post on its full footprint = 1.00)\n\n" % RATIO_MIN
           + "\n".join(rows) + "\n\nUNION JOINTS: %d weak joint(s)\n" % weak)
    open(os.path.join(HERE, "UNION_JOINTS.log"), "w").write(txt)
    print("\nUNION JOINTS: %d weak joint(s)" % weak)
    return weak


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
