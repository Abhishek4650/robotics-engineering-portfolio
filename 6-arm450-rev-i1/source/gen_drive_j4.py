#!/usr/bin/env python3
"""
ARM-450 rev I -- J4 forearm roll, redesigned around the ST3215 (world frame,
J4 axis = Z through x=y=0, forearm face at z=328).

Pattern proven at J1 (verify_j1.py: 0 failures): servo fixed to the PREVIOUS
link, output up the axis, horn bolted to a hub on the NEXT link.

  j4_base  bolts to the rev-I forearm face (4 x M3 into its inserts at
           (+-17, +-7), Ø23.8 hollow spigot into its Ø24 socket -- cables go
           down the forearm). Pinch walls 24.50, locating end wall at the
           case end, one pedestal under the case back, side cable window.
           The servo slides in along -X, exactly as at J1.
  j4_cap   bolts on the wall tops once the servo is in. Captures the cap face
           under its lips and holds a 6806 inserted from below.
  j4_hub   Ø29.95 journal in the 6806, bolted to the horn on the proven
           BCD-14 pattern with screws driven from ABOVE (reachable until J5
           goes on); collar on the inner race; top face with 4 x M3 inserts
           at (+-17, +-7) for the J5 fork, the same interface as the forearm.
"""
import os
import sys

import numpy as np
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_common as DC       # noqa: E402

Z_FACE = 328.0
PLATE_T = 4.0
Z_PLATE_TOP = Z_FACE + PLATE_T
CABLE_SPACE = 12.0
Z_TIP = Z_PLATE_TOP + CABLE_SPACE
Z_BACK_FULL = Z_TIP + 3.905
Z_CAP = Z_TIP + DC.CASE_ABOVE_CAP
Z_HORN = Z_CAP + DC.HORN_BELOW_CAP
LIP_T = 4.0
Z_LIP_TOP = Z_CAP + LIP_T
SLOT_Y = 10.0
WALL_T = 6.5
CASE_X0 = -10.112
X_OPEN = 35.51
END_T = 3.8                       # its outer face at -13.91 clears the (-17,+-7) bolt heads
BOLTS = [(sx * 17.0, sy * 7.0) for sx in (-1, 1) for sy in (-1, 1)]
SPIGOT_D, SPIGOT_L, SPIGOT_BORE = 23.8, 10.0, 16.0
M3_HEAD_D = 6.0
# cap + bearing
# 6706 (30 x 37 x 4), as the released design had at J4: keeps the user's
# bearing list unchanged. The cap shoulder (Ø34) bears on the OUTER race only
# and the hub collar (Ø32) on the INNER race only.
BRG_OD, BRG_ID, BRG_W = 37.0, 30.0, 4.0
SHOULDER_D = 34.0
INNER_CLR_R = 32.4 / 2 + 0.55            # SKF 61706 d1 = 32.4: stationary parts stay 0.55 outside
CAP_T = 10.0
CB_HEAD_D, CB_HEAD_T = 6.2, 3.8          # M3 socket head recess in the cap (3.3 left the head 0.8 mm
                                          # under the turning hub flange: 3.8 -> 1.3, verify_head_clearance)
Z_CAP_TOP = Z_LIP_TOP + CAP_T
Z_BRG_TOP = Z_LIP_TOP + BRG_W
# x = 14.5, not -6: at -6 the bolts were 16.6 from the axis and their shanks
# ran THROUGH the bearing (found by the manual pocket check)
CAP_BOLTS = [(x, s * (DC.PINCH / 2 + WALL_T / 2)) for x in (14.5, 31.0) for s in (-1, 1)]
# hub
COLLAR_D = 32.0
FLANGE_D, FLANGE_T = 46.0, 9.0
Z_FLANGE_BOT = Z_CAP_TOP + 0.5
Z_HUB_TOP = Z_FLANGE_BOT + FLANGE_T
CENTRE_D, CB_D, UNDER_HEAD = 7.0, 4.8, 3.0
M3_INS_D, M3_INS_L = 4.1, 7.5


def base():
    yw = DC.PINCH / 2 + WALL_T / 2
    x0p = -20.0
    s = (cq.Workplane("XY").center((x0p + X_OPEN) / 2, 0)
         .rect(X_OPEN - x0p, DC.PINCH + 2 * WALL_T).extrude(PLATE_T)
         .translate((0, 0, Z_FACE)))
    # spigot into the forearm socket, hollow for the cables
    s = s.union(cq.Workplane("XY").circle(SPIGOT_D / 2).extrude(SPIGOT_L)
                .translate((0, 0, Z_FACE - SPIGOT_L)))
    s = s.cut(cq.Workplane("XY").circle(SPIGOT_BORE / 2)
              .extrude(SPIGOT_L + PLATE_T + 2).translate((0, 0, Z_FACE - SPIGOT_L - 1)))
    for sy in (-1, 1):
        s = s.union(cq.Workplane("XY").center((CASE_X0 + X_OPEN) / 2, sy * yw)
                    .rect(X_OPEN - CASE_X0, WALL_T).extrude(Z_LIP_TOP - Z_PLATE_TOP)
                    .translate((0, 0, Z_PLATE_TOP)))
        s = s.union(cq.Workplane("XY")
                    .center((CASE_X0 + X_OPEN) / 2, sy * (SLOT_Y + DC.PINCH / 2) / 2)
                    .rect(X_OPEN - CASE_X0, DC.PINCH / 2 - SLOT_Y).extrude(LIP_T)
                    .translate((0, 0, Z_CAP)))
    s = s.union(cq.Workplane("XY").center(CASE_X0 - END_T / 2, 0)
                .rect(END_T, DC.PINCH + 2 * WALL_T).extrude(Z_LIP_TOP - Z_PLATE_TOP)
                .translate((0, 0, Z_PLATE_TOP)))
    s = s.union(cq.Workplane("XY").center((CASE_X0 - 3.4) / 2, 0)
                .rect(-3.4 - CASE_X0, 24.0).extrude(Z_BACK_FULL - DC.CLR - Z_PLATE_TOP)
                .translate((0, 0, Z_PLATE_TOP)))
    # hub journal + horn pass the lips
    s = s.cut(cq.Workplane("XY").circle(DC.BORE_CLR_D / 2)
              .extrude(LIP_T + 2).translate((0, 0, Z_CAP - 1)))
    # Rule 4: the lip tops reached r 15.5 under the 6706 -- a STATIONARY face
    # on the TURNING inner ring (d1/2 = 16.2, SKF 61706). 0.5 mm relief inside
    # d1/2 + 0.5; walls and lips still carry the outer ring.
    s = s.cut(cq.Workplane("XY").circle(INNER_CLR_R).extrude(0.5 + 1.0).translate((0, 0, Z_LIP_TOP - 0.5)))
    # forearm bolts: clearance, heads on the plate
    for (x, y) in BOLTS:
        s = s.cut(cq.Workplane("XY").center(x, y).circle(3.4 / 2)
                  .extrude(PLATE_T + 2).translate((0, 0, Z_FACE - 1)))
    # side cable window in the -Y wall, below the case (J4 -> J5 service loop)
    s = s.cut(cq.Workplane("XY").center(12.0, -yw).rect(20.0, WALL_T + 2)
              .extrude(CABLE_SPACE - 1.0).translate((0, 0, Z_PLATE_TOP)))
    # M3 inserts in the wall tops for the cap
    for (x, y) in CAP_BOLTS:
        s = s.cut(cq.Workplane("XY").center(x, y).circle(M3_INS_D / 2)
                  .extrude(M3_INS_L + 0.5).translate((0, 0, Z_LIP_TOP - M3_INS_L)))
    # SERVO SCREWED BY ITS OWN BACK HOLES (audit M1): the far pair only --
    # behind the near pair the plate sits on the forearm, no screwdriver gets
    # there. Posts from the plate, screws from under the plate's overhang.
    s = s.union(DC.screw_pads(Z_CAP, -1, DC.SCREW_FAR, Z_CAP - Z_PLATE_TOP + 0.5, d=DC.POST_D))
    # SEATED, NOT FLOATING (Rule 8): the near end rests on 2 posts as well (no
    # screw there), so the servo stands on 4 posts, not on friction
    s = s.union(DC.screw_pads(Z_CAP, -1, DC.SCREW_NEAR, Z_CAP - Z_PLATE_TOP + 0.5, d=DC.POST_D))
    s = DC.screw_holes(s, Z_CAP, -1, DC.SCREW_FAR, Z_CAP - Z_FACE + 1.0, counterbore=True)
    # the servo's rear IDLER horn (official ST3215 model) turns inside the back
    # pedestal: 169 mm3 of overlap -- keep it clear
    return s.cut(DC.idler_clearance(Z_CAP, -1))


def cap():
    # +1.45: the O6.2 head counterbores at y +-15.5 reached y 18.6 against a cap
    # side at 18.75 (0.15 mm wall, audit) -> 1.6 mm
    yw = DC.PINCH / 2 + WALL_T + 1.45
    s = (cq.Workplane("XY").center((CASE_X0 - END_T + X_OPEN) / 2, 0)
         .rect(X_OPEN - CASE_X0 + END_T, 2 * yw).extrude(CAP_T)
         .translate((0, 0, Z_LIP_TOP)))
    s = s.union(cq.Workplane("XY").circle(BRG_OD / 2 + 4.0).extrude(CAP_T)
                .translate((0, 0, Z_LIP_TOP)))
    # 6806 pocket from BELOW, shoulder on top keeps the outer race in
    # exactly BRG_W deep from the lip plane (it ended 0.01 short: the cap
    # overlapped the bearing by 1.67 mm3)
    s = s.cut(cq.Workplane("XY").circle((BRG_OD + 0.02) / 2).extrude(BRG_W + 0.01)
              .translate((0, 0, Z_LIP_TOP - 0.01)))
    s = s.cut(cq.Workplane("XY").circle(SHOULDER_D / 2).extrude(CAP_T + 2)
              .translate((0, 0, Z_LIP_TOP - 1)))
    for (x, y) in CAP_BOLTS:
        s = s.cut(cq.Workplane("XY").center(x, y).circle(3.4 / 2)
                  .extrude(CAP_T + 2).translate((0, 0, Z_LIP_TOP - 1)))
        # heads BELOW the cap top: the hub flange turns 0.5 mm above it and
        # covers r < 23 (the head-vs-flange clash found by verify_hw)
        s = s.cut(cq.Workplane("XY").center(x, y).circle(CB_HEAD_D / 2)
                  .extrude(CB_HEAD_T + 1).translate((0, 0, Z_CAP_TOP - CB_HEAD_T)))
    return s


def hub():
    s = (cq.Workplane("XY").circle(DC.SHAFT_OD / 2).extrude(Z_BRG_TOP - Z_HORN)
         .translate((0, 0, Z_HORN)))
    s = s.union(cq.Workplane("XY").circle(COLLAR_D / 2).extrude(Z_FLANGE_BOT - Z_BRG_TOP)
                .translate((0, 0, Z_BRG_TOP)))
    s = s.union(cq.Workplane("XY").circle(FLANGE_D / 2).extrude(FLANGE_T)
                .translate((0, 0, Z_FLANGE_BOT)))
    s = s.cut(cq.Workplane("XY").circle(CENTRE_D / 2)
              .extrude(Z_HUB_TOP - Z_HORN + 2).translate((0, 0, Z_HORN - 1)))
    for a in (0, 90, 180, 270):
        x, y = DC.HORN_BCD / 2 * np.cos(np.radians(a)), DC.HORN_BCD / 2 * np.sin(np.radians(a))
        s = s.cut(cq.Workplane("XY").center(x, y).circle(DC.HORN_HOLE_D / 2)
                  .extrude(Z_HUB_TOP - Z_HORN + 2).translate((0, 0, Z_HORN - 1)))
        zh = Z_HORN + UNDER_HEAD
        s = s.cut(cq.Workplane("XY").center(x, y).circle(CB_D / 2)
                  .extrude(Z_HUB_TOP - zh + 1).translate((0, 0, zh)))
    for (x, y) in BOLTS:
        s = s.cut(cq.Workplane("XY").center(x, y).circle(M3_INS_D / 2)
                  .extrude(M3_INS_L + 0.5).translate((0, 0, Z_HUB_TOP - M3_INS_L)))
    return s


def main():
    print("J4 rev I (world z): face %.1f  tip %.3f  cap face %.3f  horn %.3f  lips top %.3f"
          % (Z_FACE, Z_TIP, Z_CAP, Z_HORN, Z_LIP_TOP))
    print("   bearing %.3f..%.3f   hub top %.3f  <- J5 fork mounting face"
          % (Z_LIP_TOP, Z_BRG_TOP, Z_HUB_TOP))
    ok = True
    for nm, fn in (("j4_base", base), ("j4_cap", cap), ("j4_hub", hub)):
        p = fn()
        n = len(p.val().Solids())
        bb = p.val().BoundingBox()
        print("   %-8s %9.1f mm3  solids %d  z %7.2f..%7.2f" % (nm, p.val().Volume(), n, bb.zmin, bb.zmax))
        ok &= n == 1
        cq.exporters.export(p, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(p, os.path.join(HERE, nm + ".stl"), tolerance=0.01, angularTolerance=0.1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
