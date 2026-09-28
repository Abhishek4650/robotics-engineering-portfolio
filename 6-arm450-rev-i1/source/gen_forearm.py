#!/usr/bin/env python3
"""
ARM-450 rev I -- forearm halves.

1. SOCKET end instead of the J4 journal (J4 servicing no longer needs the
   forearm split open).
2. VALID SOLIDS. The released forearm halves fail OpenCascade's BRepCheck and
   ShapeFix cannot repair them. Cause, measured: link_pro puts the seam-screw
   bosses at y = +-(25 - 2.4 - 4.75) = +-17.85, so the O9.5 boss is exactly
   TANGENT to the flange's inner wall (y 22.6) -- a line-contact union. The
   three invalid faces sit on that wall and split exactly at the boss x
   positions (29.75, 59.5). The boss is carried 0.5 mm INTO the wall.
   Both halves move together, so their seam screws still align.
"""
import inspect
import os
import sys

import cadquery as cq

PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARTS)
import link_pro as LP                       # noqa: E402

SEAM_BOSS_OVERLAP = 0.5
_src = inspect.getsource(LP.build)
_old = "y = sy * (half_h - WALL_FLANGE - BOSS_OD / 2.0)"
assert _src.count(_old) == 1, "link_pro seam-boss line changed; re-check the fix"
_ns = dict(vars(LP)); _ns["SEAM_BOSS_OVERLAP"] = SEAM_BOSS_OVERLAP
_src = _src.replace(_old, "y = sy * (half_h - WALL_FLANGE - BOSS_OD / 2.0 + SEAM_BOSS_OVERLAP)")
# cable bore: centred 9.0 below the seam it left 0.5 mm of outer skin (audit);
# 8.3 leaves 1.2 mm
_cab = ".center(0, HALF_D - 9.0).circle(CABLE_D / 2)"
assert _src.count(_cab) == 1, "link_pro cable bore line changed"
exec(_src.replace(_cab, ".center(0, HALF_D - 8.3).circle(CABLE_D / 2)"), _ns)
build = _ns["build"]

# FLUSH HEADS on the tongue (outer face z = 0). The link face runs 1.0 mm
# from the fork cheek, so a seam screw head near the joint (and the ear
# screw's) stood 3 mm proud INTO the cheek -- and the collars sit on the
# seam screws at x 89 (fastener check). Every seam hole gets a counterbore:
# M3 socket head O5.5 x 3 -> O6.0 x 3.2 (M3 x 16 then reaches 4.7 into the
# groove half's insert); the ear's M2.5 head O4.5 x 2.5 -> O5.0 x 2.7.
CB_M3_D, CB_M3_T = 6.0, 3.2
CB_M25_D, CB_M25_T = 5.0, 2.7


def seam_holes(face_x, dy):
    n = max(2, int(face_x // LP.SEAM_PITCH) + 1)
    out = []
    for x in [face_x * i / (n - 1) for i in range(n)]:
        if x < LP.BOSS_R * 0.8 or x > face_x - 12.0:
            continue
        for sy in (-1, 1):
            out.append((x, sy * (LP.SEC_H / 2.0 - LP.WALL_FLANGE - LP.BOSS_OD / 2.0 + dy)))
    return out


EAR_XC = -(LP.BOSS_R - LP.EAR_OUT / 2.0 - 1.0)


def counterbores(s, face_x, dy, holes=None):
    for (x, y) in (holes or seam_holes(face_x, dy)):
        s = s.cut(cq.Workplane("XY").center(x, y).circle(CB_M3_D / 2).extrude(CB_M3_T + 1)
                  .translate((0, 0, -1)))
    return s.cut(cq.Workplane("XY").center(EAR_XC, 0).circle(CB_M25_D / 2).extrude(CB_M25_T + 1)
                 .translate((0, 0, -1)))


if __name__ == "__main__":
    from OCP.BRepCheck import BRepCheck_Analyzer
    for t, nm in ((True, "link_fore_tongue"), (False, "link_fore_groove")):
        s = build(t, LP.FORE_FACE_X, "socket")
        if not t:
            # recut the seam groove AFTER the bosses: carrying the boss 0.5 mm
            # into the wall also refilled part of the groove band, and the
            # tongue's lip met it (0.27 mm, static all-pairs audit)
            h, clr = LP.SEC_H / 2.0, LP.SEAM_LIP_CLR
            depth = LP.SEAM_LIP + LP.SEAM_GROOVE_EXTRA + clr
            go = LP.capsule(LP.FORE_FACE_X, h - 0.2 + clr, LP.BOSS_R - 0.2 + clr, depth + 0.2)
            gi = LP.capsule(LP.FORE_FACE_X, h - 0.2 - 2.0 - clr, LP.BOSS_R - 0.2 - 2.0 - clr,
                            depth + 2.2).translate((0, 0, -1))
            s = s.cut(go.cut(gi).translate((0, 0, LP.HALF_D - depth)))
        if t:
            s = counterbores(s, LP.FORE_FACE_X, SEAM_BOSS_OVERLAP)
        sol = s.val()
        valid = BRepCheck_Analyzer(sol.wrapped).IsValid()
        bb = sol.BoundingBox()
        print("%-18s %9.1f mm3  solids %d  BRep valid %s  x %.2f..%.2f"
              % (nm, sol.Volume(), len(sol.Solids()), valid, bb.xmin, bb.xmax))
        cq.exporters.export(s, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(s, os.path.join(HERE, nm + ".stl"), tolerance=0.01, angularTolerance=0.1)
