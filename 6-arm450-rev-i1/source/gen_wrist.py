#!/usr/bin/env python3
"""
ARM-450 rev I -- wrist J5 (pitch) + J6 (roll), both ST3215, redesigned.

Frames. Everything here is built in the J5 fork's LOCAL frame, the frame the
J3/J5 forks have always used:  z = J5 joint axis (world y), x = along the arm
(world z), y = across (world x). World placement is FORK_R with
t = (0, 0, Z_J5), exactly as J3 at z = 209.

  J5_p1 / J5_p2   gen_j5_new's fork, re-cut on the drive-train rules proven at
                  J3 (drive_common): cap-face seat on the parting plane, stepped
                  floor, wiring window, no strap inserts. J5_FACE 25.28 -> 28.28
                  so the new blade hub (r 18.1) clears the bridge. The old
                  tool-flange corner clip is gone -- the flange has moved out.
  J5_shaft        printed, through both 6706s and the blade, bolted to the J5
                  horn on BCD 14; D-flat keys the blade.
  J5_spacer x2    3-mm rings: blade clamped between the two INNER races, so it
                  turns with them and never rubs a cheek.
  j6_body         the J5 blade (D-bore on the shaft) carrying the J6 ST3215 in
                  the J4-style slide-in housing, output ALONG the arm. Cap
                  bosses only beyond r = 39 from the J5 axis, clear of the
                  cheeks through the whole J5 swing.
  j6_cap, j6_flange  as J4's cap + hub, on a 6706; the flange carries the
                  released tool face (4 x M3 on Ø30).

The J6 housing is drawn in a "J1-like" frame (a = channel, b = pinch,
c = output) and turned into the J5 frame by +120 deg about (1,1,1), which maps
a->y, b->z, c->x.
"""
import os
import sys

import numpy as np
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_common as DC        # noqa: E402
import gen_j5_new as J5          # noqa: E402
import gen_drive_j4 as J4        # noqa: E402

# ---------------- J5 fork -------------------------------------------------
J5.J5_FACE = 28.28
# fork() cuts the bay "BAY_T + 1" deep: pass BAY_T - 1 so the bay is exactly
# DC.BAY_T and the back wall keeps its 2.4 (Z_DRIVE is set explicitly below)
J5.BAY_L, J5.BAY_W, J5.BAY_T = DC.BAY_L, DC.PINCH, DC.BAY_T - 1.0
J5.Z_DRIVE = J5.Z_BAY + DC.BAY_T + J5.BACK_T
J5.FLANGE_X = 1.0e3                     # disables the old flange-corner clip
P5 = J5.Z_BAY                           # 26.0 parting plane = cap face
Z5_HORN = P5 - DC.HORN_BELOW_CAP        # 22.989
Z5_IDLE_END = -(J5.Z_IDLE + 0.5)        # -22.5
Z_J5_WORLD = J4.Z_HUB_TOP + J5.J5_FACE  # 430.369


def j5_p1():
    s = J5.fork()
    s = s.cut(cq.Workplane("XY").rect(400, 400).extrude(400).translate((0, 0, P5)))
    s = DC.split_bolts(s, P5, J5.Z_IN, J5.Z_DRIVE, "p1")
    s = DC.p1_floor_cuts(s, J5.Z_SEAT_TOP, P5, recess_d=DC.RACE_RECESS_D_6706)
    s = DC.open_drive_pocket(s, J5.Z_IN, J5.SEAT_T, J5.BRG_OD)
    # the 4 fork -> J4-hub bolt heads sit on this floor (world z hub top + 8)
    # right under the swinging blade: sunk 3.2 mm into it (M3 x 10 now)
    return s.cut(DC.floor_head_counterbores(J4.BOLTS, J4.Z_HUB_TOP + 8.0, Z_J5_WORLD))


def j5_p2():
    s = J5.fork()
    s = s.cut(cq.Workplane("XY").rect(400, 400).extrude(-400).translate((0, 0, P5)))
    s = DC.split_bolts(s, P5, J5.Z_IN, J5.Z_DRIVE, "p2")
    return DC.bay_shell(s, P5, J5.Z_DRIVE, J5.BACK_T)


def j5_shaft():
    # the axle goes in (and out) through the blade's D-bore idle end first:
    # its flat must run out of that end (disassembly check: a round idle end
    # jammed in the D-bore, 30 mm3 -- the J5 wrist could not be assembled)
    return DC.shaft(Z5_IDLE_END, Z5_HORN, flat_half=15.5, flat_to_idle_end=True)


BLADE_HALF = J5.J5_GAP - 1.0            # 15.0
# Rule 4: EXACTLY the gap from the blade face to the inner ring (3.0). At
# 2.9 (placed 0.05 off the blade) each spacer floated 0.05 on both faces:
# 0.2 mm of axial rattle in the J5 stack. Line-to-line now; sand to fit.
SPACER_T = (J5.Z_IN + J5.SEAT_T) - BLADE_HALF          # 3.0
SPACER_OD, SPACER_ID = 32.0, 30.2


def j5_spacer():
    return (cq.Workplane("XY").circle(SPACER_OD / 2).circle(SPACER_ID / 2)
            .extrude(SPACER_T).translate((0, 0, BLADE_HALF)))


# ---------------- J6 (in the J1-like frame a, b, c) -----------------------
HUB_R = 18.1
X6_TIP = 30.0                           # plugs need ~11 mm off the hub (r 18.1)
X6_BACK_FULL = X6_TIP + 3.905
X6_CAP = X6_TIP + DC.CASE_ABOVE_CAP     # 64.589
X6_HORN = X6_CAP + DC.HORN_BELOW_CAP    # 67.600
LIP_T = 4.0
X6_LIP_TOP = X6_CAP + LIP_T             # 68.589
WALL_B0, WALL_B1 = DC.PINCH / 2, BLADE_HALF          # pinch wall 12.25..15.0
A0, A_OPEN, END_T = -10.112, 35.51, 3.8
SLOT_B = 10.0
# 21.6 (was 20.0): the M3 insert pockets at b +-17.5 left 0.44 mm of wall and
# the cap's head counterbores broke out of its side (audit, thin-wall rays)
BOSS_B0, BOSS_B1 = BLADE_HALF, 21.6     # cap bosses, outside the blade
BOSS_C0 = 50.0                          # > 39: clear of the cheeks at any J5 angle
# a = 14.5, not -6: at -6 the bolts were 18.5 from the J6 axis -- on the
# bearing's outer edge (the manual pocket check read O39.45 instead of O37.02)
CAP6_BOLTS = [(a, s * 17.5) for a in (14.5, 31.0) for s in (-1, 1)]
# Blade D sits only 0.05 beyond the shaft flat: at 0.2 the blade turned 2.4 deg
# on the shaft before the key bit (3.7 mm of slop at the tool). A radial M3 grub
# through the hub onto the flat then takes out what is left.
FLAT_A = -14.2 - 0.05
GRUB_PILOT_D = 2.6                      # M3 grub self-threads into the print
CAP6_T = 10.0
X6_BRG_TOP = X6_LIP_TOP + J4.BRG_W
X6_CAP_TOP = X6_LIP_TOP + CAP6_T
X6_FLANGE_BOT = X6_CAP_TOP + 0.5
X6_TOOL = X6_FLANGE_BOT + J4.FLANGE_T
TOOL_BCD = 30.0


def _box(a0, a1, b0, b1, c0, c1):
    return (cq.Workplane("XY").center((a0 + a1) / 2, (b0 + b1) / 2)
            .rect(a1 - a0, b1 - b0).extrude(c1 - c0).translate((0, 0, c0)))


def _to_j5(wp):
    return wp.rotate((0, 0, 0), (1, 1, 1), 120)


def j6_body_abc():
    s = (cq.Workplane("XZ").circle(HUB_R).extrude(BLADE_HALF)
         .union(cq.Workplane("XZ").circle(HUB_R).extrude(-BLADE_HALF)))   # hub disc along b
    for sb in (-1, 1):
        s = s.union(_box(A0, A_OPEN, *(sorted((sb * WALL_B0, sb * WALL_B1))), 0.0, X6_LIP_TOP))
        s = s.union(_box(A0, A_OPEN, *(sorted((sb * SLOT_B, sb * WALL_B0))), X6_CAP, X6_LIP_TOP))
        s = s.union(_box(-15.0, A_OPEN, *(sorted((sb * BOSS_B0, sb * BOSS_B1))), BOSS_C0, X6_LIP_TOP))
    s = s.union(_box(A0 - END_T, A0, -BLADE_HALF, BLADE_HALF, 0.0, X6_LIP_TOP))
    s = s.union(_box(A0, -3.4, -12.0, 12.0, 0.0, X6_BACK_FULL - DC.CLR))
    # D-bore along b for the J5 shaft
    bore = (cq.Workplane("XZ").circle(15.1).extrude(BLADE_HALF + 1)
            .union(cq.Workplane("XZ").circle(15.1).extrude(-(BLADE_HALF + 1))))
    key = _box(-20.0, FLAT_A, -BLADE_HALF - 2, BLADE_HALF + 2, -20.0, 20.0)
    s = s.cut(bore.cut(key))
    # Grub along -a (J5-local -y) at the blade's mid-plane, onto the D-flat.
    # Reached from the side between the cheeks: nothing on that line.
    s = s.cut(cq.Workplane("YZ").circle(GRUB_PILOT_D / 2).extrude(-(HUB_R + 2))
              .translate((0, 0, 0)))
    # SWING-SAFE WEDGE. Near the J5 axis the channel walls reached y = 35.5 and
    # swung into the fork bridge from +46.5 deg on (verify_wrist caught it).
    # Between the hub and the case back, keep only the hub disc and a +-45 deg
    # wedge pointing along the arm: at any J5 angle in +-93 that material cannot
    # reach the bridge (x < -20.28, |y| <= 25 in the fork frame).
    reach = _box(-60.0, 60.0, -30.0, 30.0, -30.0, X6_TIP - 0.5)
    # +-35 deg, not 45: the bridge's angular reach is widest at radius ~30,
    # where anything beyond +-39.5 deg meets it at a 93 deg swing (a 45 deg
    # wedge clipped the corner -- found by the sweep, not by this reasoning).
    t35 = np.tan(np.radians(35.0)) * (X6_TIP + 5)
    wedge = (cq.Workplane("XZ").polyline([(0, 0), (t35, X6_TIP + 5), (-t35, X6_TIP + 5)])
             .close().extrude(30.0).translate((0, 15.0, 0)))
    wedge = cq.Workplane("XY").add(wedge.val())
    hubc = (cq.Workplane("XZ").circle(HUB_R).extrude(30.0).translate((0, 15.0, 0)))
    s = s.cut(reach.cut(wedge).cut(hubc))
    # J6 hub journal + horn through the lips
    s = s.cut(cq.Workplane("XY").circle(DC.BORE_CLR_D / 2).extrude(LIP_T + 2)
              .translate((0, 0, X6_CAP - 1)))
    # Rule 4: lip tops off the 6706's turning inner ring (as J4)
    s = s.cut(cq.Workplane("XY").circle(J4.INNER_CLR_R).extrude(1.5).translate((0, 0, X6_LIP_TOP - 0.5)))
    for (a, b) in CAP6_BOLTS:
        s = s.cut(cq.Workplane("XY").center(a, b).circle(J4.M3_INS_D / 2)
                  .extrude(J4.M3_INS_L + 0.5).translate((0, 0, X6_LIP_TOP - J4.M3_INS_L)))
    # SERVO SCREWED BY ITS OWN BACK HOLES (audit M1): the far pair, on a
    # bridge between the side walls over the servo's far end (added after the
    # swing wedge: it lies in the servo's own shadow -- the 450-pose and sweep
    # checks judge it). Behind the near pair is the J5 hub: no screwdriver.
    # Heads on the bridge's outer face = the head seat.
    lo, hi = X6_CAP - DC.SSCR_HEAD, X6_CAP - DC.PLATEAU
    br = _box(DC.SCREW_FAR[0][0] - DC.PAD_D / 2 - 0.4, A_OPEN, -WALL_B1, WALL_B1, lo, hi)
    keep = _box(-20.0, 60.0, -DC.KEEP_Y, DC.KEEP_Y, hi - DC.KEEP_H, hi + 6.0)
    s = s.union(br.cut(keep))
    s = DC.screw_holes(s, X6_CAP, -1, DC.SCREW_FAR, DC.SSCR_HEAD + 1.0)
    # SEATED, NOT FLOATING (Rule 8): the near end rests on 2 pads from the side
    # walls onto the back plateau too (no screw: the J5 hub stands behind them)
    s = s.union(DC.screw_pads(X6_CAP, -1, DC.SCREW_NEAR, DC.SSCR_HEAD))
    # the J6 servo's rear IDLER horn (official ST3215 model) -- keep it clear
    return s.cut(DC.idler_clearance(X6_CAP, -1))


def j6_cap_abc():
    s = _box(A0 - END_T, A_OPEN, -BOSS_B1, BOSS_B1, X6_LIP_TOP, X6_CAP_TOP)
    s = s.union(cq.Workplane("XY").circle(J4.BRG_OD / 2 + 4.0).extrude(CAP6_T)
                .translate((0, 0, X6_LIP_TOP)))
    s = s.cut(cq.Workplane("XY").circle((J4.BRG_OD + 0.02) / 2).extrude(J4.BRG_W + 0.01)
              .translate((0, 0, X6_LIP_TOP - 0.01)))       # exactly BRG_W (was 0.01 short)
    s = s.cut(cq.Workplane("XY").circle(J4.SHOULDER_D / 2).extrude(CAP6_T + 2)
              .translate((0, 0, X6_LIP_TOP - 1)))
    for (a, b) in CAP6_BOLTS:
        s = s.cut(cq.Workplane("XY").center(a, b).circle(3.4 / 2).extrude(CAP6_T + 2)
                  .translate((0, 0, X6_LIP_TOP - 1)))
        s = s.cut(cq.Workplane("XY").center(a, b).circle(J4.CB_HEAD_D / 2)
                  .extrude(J4.CB_HEAD_T + 1).translate((0, 0, X6_CAP_TOP - J4.CB_HEAD_T)))
    return s


def j6_flange_abc():
    s = (cq.Workplane("XY").circle(DC.SHAFT_OD / 2).extrude(X6_BRG_TOP - X6_HORN)
         .translate((0, 0, X6_HORN)))
    s = s.union(cq.Workplane("XY").circle(J4.COLLAR_D / 2).extrude(X6_FLANGE_BOT - X6_BRG_TOP)
                .translate((0, 0, X6_BRG_TOP)))
    s = s.union(cq.Workplane("XY").circle(J4.FLANGE_D / 2).extrude(J4.FLANGE_T)
                .translate((0, 0, X6_FLANGE_BOT)))
    s = s.cut(cq.Workplane("XY").circle(J4.CENTRE_D / 2).extrude(X6_TOOL - X6_HORN + 2)
              .translate((0, 0, X6_HORN - 1)))
    for ang in (0, 90, 180, 270):
        x, y = DC.HORN_BCD / 2 * np.cos(np.radians(ang)), DC.HORN_BCD / 2 * np.sin(np.radians(ang))
        s = s.cut(cq.Workplane("XY").center(x, y).circle(DC.HORN_HOLE_D / 2)
                  .extrude(X6_TOOL - X6_HORN + 2).translate((0, 0, X6_HORN - 1)))
        zh = X6_HORN + J4.UNDER_HEAD
        s = s.cut(cq.Workplane("XY").center(x, y).circle(J4.CB_D / 2)
                  .extrude(X6_TOOL - zh + 1).translate((0, 0, zh)))
    for ang in (45, 135, 225, 315):
        x, y = TOOL_BCD / 2 * np.cos(np.radians(ang)), TOOL_BCD / 2 * np.sin(np.radians(ang))
        s = s.cut(cq.Workplane("XY").center(x, y).circle(J4.M3_INS_D / 2)
                  .extrude(J4.M3_INS_L + 0.5).translate((0, 0, X6_TOOL - J4.M3_INS_L)))
    return s


PARTS = [("J5_p1", j5_p1), ("J5_p2", j5_p2), ("J5_shaft", j5_shaft),
         ("J5_spacer", j5_spacer),
         ("j6_body", lambda: _to_j5(j6_body_abc())),
         ("j6_cap", lambda: _to_j5(j6_cap_abc())),
         ("j6_flange", lambda: _to_j5(j6_flange_abc()))]


def main():
    print("wrist rev I (J5 local):  J5_FACE %.2f  P5 %.2f  horn5 %.3f  Z_DRIVE %.2f  J5 axis world z %.3f"
          % (J5.J5_FACE, P5, Z5_HORN, J5.Z_DRIVE, Z_J5_WORLD))
    print("   J6: tip %.1f  cap face %.3f  horn %.3f  lips %.3f  bearing ..%.3f  tool face x %.3f  (from the J5 axis)"
          % (X6_TIP, X6_CAP, X6_HORN, X6_LIP_TOP, X6_BRG_TOP, X6_TOOL))
    ok = True
    for nm, fn in PARTS:
        p = fn()
        n = len(p.val().Solids())
        bb = p.val().BoundingBox()
        print("   %-10s %9.1f mm3  solids %d  x %7.2f..%7.2f  y %7.2f..%7.2f  z %7.2f..%7.2f"
              % (nm, p.val().Volume(), n, bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
        ok &= n == 1
        cq.exporters.export(p, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(p, os.path.join(HERE, nm + ".stl"), tolerance=0.01, angularTolerance=0.1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
