#!/usr/bin/env python3
"""
Does the STEP assembly agree with the mesh assembly the analysis was run on?

`assemble_step.py` exists so the arm can be opened and sectioned in real CAD.
That makes it a SECOND description of where every part sits, and a second
description is only worth having if something checks it against the first --
otherwise an inspector is shown one arm while the interference sweep, the sine
clearance check and the FEA were all run on another.

This compares them component by component:
  * every printed part in the STEP has a mesh at the same centroid
  * the two assemblies occupy the same bounding box
  * the TCP is where the kinematics say it is
  * bearings sit inside their housings, not floating in space
  * pocket count in the CAD against the quantities in BUY.md
"""
import os
import sys
import numpy as np
import cadquery as cq
import trimesh

import assemble as A
import assemble_step as S
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad"))
import params as P

TOL = 0.05          # mm; the two paths differ only by STEP vs STL tessellation
# (a tessellated bounding box can only be INSIDE the true one, and at the
#  0.01 mm chord tolerance these parts are exported at, by well under 0.05)
ok = fail = 0


def chk(cond, label, detail=""):
    global ok, fail
    print(f"  [{'  ok  ' if cond else ' FAIL '}] {label:<46} {detail}")
    ok, fail = ok + bool(cond), fail + (not cond)


def centroids_step(assy):
    """Centroid of every component, in assembly coordinates. The assembly is
    flat -- every part is a direct child of the root -- so no recursion."""
    out = {}
    for ch in assy.children:
        shp = ch.obj.val() if hasattr(ch.obj, "val") else ch.obj
        # BOUNDING-BOX centre, not centre of mass. trimesh's .centroid is
        # area-weighted over the triangles and OCC's Center() is the volume
        # centre of mass; comparing those two put the base 6.9 mm out when
        # nothing was actually misplaced. A bounding box means the same thing
        # in both libraries.
        bb = shp.located(ch.loc).BoundingBox()
        out[ch.name] = np.array([(bb.xmin + bb.xmax) / 2,
                                 (bb.ymin + bb.ymax) / 2,
                                 (bb.zmin + bb.zmax) / 2])
    return out


def main():
    print("=" * 74)
    print("STEP ASSEMBLY vs MESH ASSEMBLY")
    print("=" * 74)

    assy, tcp_step = S.build_step()
    P_mesh, tcp_mesh = A.build(tool="gripper")

    # --- TCP -----------------------------------------------------------
    chk(np.allclose(tcp_step, tcp_mesh, atol=1e-6), "TCP identical in both paths",
        f"({tcp_step[0]:.1f}, {tcp_step[1]:.1f}, {tcp_step[2]:.1f})")
    chk(abs(np.linalg.norm(tcp_step) - 450.0) < 0.05,
        "home-pose reach is 450 mm", f"{np.linalg.norm(tcp_step):.2f} mm")

    # --- per-part centroids -------------------------------------------
    cs = centroids_step(assy)
    mesh_c = [m.bounds.mean(axis=0) for m, _ in P_mesh]
    worst, worst_n = 0.0, ""
    unmatched = []
    for n, c in cs.items():
        if "bearing" in n:
            continue                       # meshes carry no bearings
        d = min(np.linalg.norm(c - mc) for mc in mesh_c)
        if d > worst:
            worst, worst_n = d, n
        if d > TOL:
            unmatched.append((n, d))
    chk(not unmatched, "every printed part matches a mesh centroid",
        f"worst {worst:.3f} mm on {worst_n}" if not unmatched
        else f"{len(unmatched)} off: " + ", ".join(f"{n} {d:.2f}mm"
                                                   for n, d in unmatched[:4]))

    # --- bounding box --------------------------------------------------
    stepbb = cq.importers.importStep(
        "output/cad/arm450_assembly_home.step").val().BoundingBox()
    allm = trimesh.util.concatenate([m for m, _ in P_mesh])
    mb = allm.bounds
    for i, ax in enumerate("xyz"):
        lo = (stepbb.xmin, stepbb.ymin, stepbb.zmin)[i]
        hi = (stepbb.xmax, stepbb.ymax, stepbb.zmax)[i]
        # bearings extend the STEP box slightly; only check it is not SMALLER
        chk(lo <= mb[0][i] + 0.5 and hi >= mb[1][i] - 0.5,
            f"assembly extent in {ax} covers the mesh",
            f"STEP {lo:.1f}..{hi:.1f}  mesh {mb[0][i]:.1f}..{mb[1][i]:.1f}")

    # --- bearings sit inside their housings ----------------------------
    housings = {n: s for n, s in cs.items() if "bearing" not in n}
    stray = []
    for n, c in cs.items():
        if "bearing" not in n:
            continue
        if min(np.linalg.norm(c - h) for h in housings.values()) > 120.0:
            stray.append(n)
    chk(not stray, "no bearing floats clear of the structure",
        f"{len([n for n in cs if 'bearing' in n])} bearings placed"
        if not stray else ", ".join(stray))

    # --- pocket census against the buy list ----------------------------
    n6806 = len([n for n in cs if "6806" in n])
    n6706 = len([n for n in cs if "6706" in n])
    print()
    print("  BEARING SEAT CENSUS — every Ø42 and Ø37 pocket in the CAD")
    print(f"    Ø42 (6806) seats  {n6806:>3}      BUY.md orders  6")
    print(f"    Ø37 (6706) seats  {n6706:>3}      BUY.md orders  6")
    print(f"    total             {n6806 + n6706:>3}      BUY.md orders 12")
    print()
    print("  This is NOT necessarily a defect. `link_half_tongue` and")
    print("  `link_half_groove` are each printed FOUR times and carry a pocket")
    print("  at BOTH ends, so a part reused at four positions inherently")
    print("  offers more seats than the chain has joints: six joints x two")
    print("  bearings = 12 loaded seats, and the three spare seats are at the")
    print("  chain ends where nothing mates.")
    print()
    print("  What has NOT been established is WHICH seats are the loaded ones")
    print("  at a shared joint, where the outboard end of one link and the")
    print("  inboard end of the next both present a pocket. Until that is")
    print("  fixed, the assembly shows a bearing in every seat, which is")
    print("  geometrically honest and numerically 3 more than will be bought.")
    global fail
    fail += 1

    print("=" * 74)
    print(f"  {ok} ok   {fail} FAILURES")
    print("=" * 74)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
