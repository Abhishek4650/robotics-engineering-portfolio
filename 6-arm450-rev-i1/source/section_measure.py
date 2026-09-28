#!/usr/bin/env python3
"""
MANUAL VERIFICATION BY SLICING (user request).

Each joint of the FINAL ASSEMBLY (every printed part + servos, bearings,
screws, inserts, springs) is cut by the plane that contains the joint axis and
the servo. In that section every pair of parts is MEASURED from the 2D cut:

  overlap thickness  where two cuts overlap: <= 0.15 mm is a designed pinch /
                     press fit / seated face; more is a CLASH
  gap                where they do not touch: the running clearances

Nothing here is computed from a parameter -- only from the cut.
"""
import glob
import itertools
import os
import sys

import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_final_pdf import JOINTS, category, in_box   # noqa: E402

MD = os.path.join(HERE, "_asm_meshes")
AX = {"x": 0, "y": 1, "z": 2}


def section_polys(m, o, n, i0, i1):
    sl = m.section(plane_origin=o, plane_normal=n)
    if sl is None:
        return None
    polys = []
    for ent in sl.discrete:
        pts = np.asarray(ent)[:, [i0, i1]]
        if len(pts) >= 3:
            p = Polygon(pts).buffer(0)
            if p.area > 1e-4:
                polys.append(p)
    if not polys:
        return None
    # even-odd: holes are separate loops inside outer loops
    polys.sort(key=lambda p: -p.area)
    shape = None
    for p in polys:
        if shape is None:
            shape = p
        elif shape.contains(p):
            shape = shape.difference(p)
        else:
            shape = shape.symmetric_difference(p)
    return shape


# The only overlaps that are MEANT: an M3 grub cutting its own thread in a
# printed O2.5 pilot (0.25 per side). Everything else > 0.15 is a clash.
import re                                                  # noqa: E402
LINK_OF = {"1": "link_upper_groove", "2": "link_upper_tongue", "3": "link_fore_groove", "4": "link_fore_tongue"}
DESIGNED = [(re.compile(r"^link_set_(\d)_\d+$"), lambda a, m: LINK_OF[m.group(1)], 0.45,
             "M5 set screw forms its thread in the link's O4.2 hole"),
            (re.compile(r"^j5_grub$"), lambda a, m: "j6_body", 0.30, "grub forms its thread in the O2.6 pilot"),
            (re.compile(r"^servo_scr_J(\d)_\d$"), lambda a, m: "servo_J" + m.group(1), 0.15,
             "self-tapping screw forms its thread in the servo's O2.0 back hole")]


def designed(a, b, t):
    for x, y in ((a, b), (b, a)):
        for rx, host, tmax, why in DESIGNED:
            mm = rx.match(x)
            if mm and host(x, mm) == y and t <= tmax:
                return why
    return None


def thickness(poly):
    """~ thickness of an overlap region: twice the erosion that empties it."""
    if poly.is_empty or poly.area < 1e-5:
        return 0.0
    lo, hi = 0.0, 5.0
    for _ in range(18):
        mid = (lo + hi) / 2
        if poly.buffer(-mid).is_empty:
            hi = mid
        else:
            lo = mid
    return 2 * hi


def main():
    ms = {os.path.basename(f)[:-4]: trimesh.load(f) for f in glob.glob(os.path.join(MD, "*.stl"))}
    lines = ["# Manual verification by slicing -- measured in each joint's section", ""]
    clashes = 0
    for jn, jd in JOINTS.items():
        o, n = np.array(jd["plane"][0], float), np.array(jd["plane"][1], float)
        i0, i1 = AX[jd["axes"][0]], AX[jd["axes"][1]]
        S = {}
        for k, m in ms.items():
            if in_box(m, jd["box"]):
                p = section_polys(m, o, n, i0, i1)
                if p is not None and not p.is_empty:
                    S[k] = p
        rows = []
        for a, b in itertools.combinations(sorted(S), 2):
            pa, pb = S[a], S[b]
            if pa.distance(pb) > 2.0:
                continue
            ov = pa.intersection(pb)
            t = thickness(ov) if ov.area > 1e-3 else 0.0
            gap = 0.0 if ov.area > 1e-3 else pa.distance(pb)
            why = designed(a, b, t) if t > 0.15 else None
            verdict = ("thread %.2f (%s)" % (t, why)) if why else (
                "CLASH" if t > 0.15 else ("fit/seat %.3f" % t if ov.area > 1e-3 else
                                         ("contact" if gap < 0.01 else "gap %.2f" % gap)))
            clashes += verdict == "CLASH"
            rows.append((a, b, ov.area, t, gap, verdict))
        lines += ["## %s  (cut: point %s, normal %s; %d parts in the cut)" % (jn, tuple(o), tuple(n), len(S)), "",
                  "| part A | part B | overlap mm2 | overlap thickness | gap | verdict |", "|---|---|---|---|---|---|"]
        for a, b, ar, t, g, v in rows:
            lines.append("| %s | %s | %.2f | %.3f | %.2f | %s |" % (a, b, ar, t, g, "**CLASH**" if v == "CLASH" else v))
        lines.append("")
        nc = sum(1 for r in rows if r[5] == "CLASH")
        print("%-16s parts in cut %2d   pairs measured %3d   clashes %d" % (jn, len(S), len(rows), nc))
        for r in rows:
            if r[5] == "CLASH":
                print("      CLASH %s | %s  thickness %.2f  area %.1f" % (r[0], r[1], r[3], r[2]))
    lines.insert(2, "**Total clashes: %d**\n" % clashes)
    open(os.path.join(HERE, "SECTION_MEASURE.md"), "w").write("\n".join(lines))
    print("\nTOTAL CLASHES IN THE SECTIONS: %d  (SECTION_MEASURE.md)" % clashes)


if __name__ == "__main__":
    main()
