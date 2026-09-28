#!/usr/bin/env python3
"""
ARM-450 rev H -- J4_module rebuilt from source with the membrane defect fixed.

THE DEFECT, traced to its line
------------------------------
`arm450_design/verify_pro/parts/wrist_pro.py`, roll_j4_module():

    # O33 bearing seat + journal clearance
    s = s.cut(... .circle(WSEAT / 2).extrude(WB + 6.0 + 1)
              .translate((0, 0, -1)))          -> top at z = 10.000

    # O22 horn bore, stopping at the servo bay floor
    s = s.cut(... .circle(22.0 / 2).extrude(J4_MOD_H - BAY_T + 1)
              .translate((0, 0, -1)))          -> top at z = 10.100

Both cuts are meant to reach the bay floor. They differ by exactly 0.100 mm,
so the annulus between O22 and O33 keeps a 0.100 mm skin at z 10.000..10.100.

Measured in the released part: at (14, 0) the ONLY material in the whole
z column is z 10.002..10.100 = 0.098 mm. Below it is void.

WHY NOT FIX THE STEP FILE
-------------------------
Five boolean attempts on the output all failed, each caught by verification:
  O22 at origin        -> removed 0.213 mm3, skin untouched
  O33 at origin        -> left the skin at r > 16.5
  O37+O56 full height  -> removed 13918 mm3, split into 2 solids
  same, z-bounded      -> cut the real 10.096 mm flange ring, split the part
  415 per-column cuts  -> membrane gone, ring intact, but 44 solids
The skin and the legitimate flange share one z band and are topologically
interleaved. No boolean on the output separates them. The generator is the
only clean place to fix it.

THE FIX
-------
Drive BOTH cuts to a single shared plane, computed once, and overshoot it so
no two faces land coincident (coincident faces tessellate unpredictably --
that is what produced a 0.098 mm skin rather than a clean 0.000).
"""
import os
import sys

import cadquery as cq

PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
sys.path.insert(0, PARTS)
from fixparams import *      # noqa: F401,F403,E402

HERE = os.path.dirname(os.path.abspath(__file__))

WB, WOD = WRIST_BRG_W, WRIST_BRG_OD              # 4.0, 37.0
WSEAT = WRIST_BRG_OD - 2 * WRIST_BRG_SHOULDER    # 33.0
# ---- MODULE HEIGHT ----------------------------------------------------
# REVERTED to 36.72.
#
# I grew this to 45.90 on the belief that the ST3215's case body was
# 35.30 mm along its output axis. That was MY MISREADING of the mesh: the
# supplied ST3215.stl does not model the mounting tabs, and I took the
# 37.80 overall span as the output direction.
#
# The user confirmed with a caliper: the case is 24.72 along the output
# axis, and the four mounting holes are on a 19.05 x 20.29 pattern.
# So SERVO_T = 24.72 is correct and BAY_T = 26.62 gives 1.90 mm to spare.
# The original bay was right; the growth was not.
J4_MOD_H = 36.72
BAY_FLOOR_Z = J4_MOD_H - BAY_T                  # 10.100
D_OUT = 56.0
HORN_BORE_D = 22.0

# The one plane both cuts must reach: the servo bay floor.
BAY_FLOOR = BAY_FLOOR_Z                          # 10.100
# Overshoot so neither cut leaves a face coincident with the floor.
OVERSHOOT = 0.20

# --- SERVO BAY WIDTH: sized from the MEASURED moulding, not the datasheet --
# fixparams.py:69 computes
#     BAY_L, BAY_W = SERVO_L + 2*BAY_CLR, SERVO_W + 2*BAY_CLR
# using SERVO_W = 37.25, the DATASHEET width. The real moulding is
# SERVO_W_REAL = 37.80. So BAY_W came out 38.05 and the clearance is
# 0.125 mm per side, not the 0.400 the constant intends.
#
# Measured directly: your ST3215.stl is 45.22 x 37.80 x 24.72, and placing
# it in the rev-H bay gives x faces 0.398 mm (correct) but y faces 0.125 mm.
#
# params.py:29-34 records this exact mistake being made before:
#   "Cutting to SERVO_W + 2 x 0.20 gave 37.65 against a 37.80 moulding ...
#    The servo did not go in. Not tight -- did not go in."
# and defines SERVO_POCKET_W = SERVO_W_REAL + 2*SERVO_CLR_FIT = 38.80.
# fixparams.py does not use it. This rebuild does.
# BUT the module has no room for 38.80 at every x. Measured: at x = 30 the
# outer surface is at y = -19.49, so a bay wall at -19.40 leaves 0.090 mm of
# wall -- a new unprintable sliver, 27 confirmed thin columns. The old 38.05
# bay left 0.465 mm there.
#
# So the bay cannot simply be widened. Widen it only over the x range where
# the module is full width (the O56 lobes), and keep the narrow wall where
# the module necks down. Measured usable widths:
#     x  -10.5 .. 24.0   module full width, y +/-28  -> 38.80 fits
#     x   24.0 .. 35.6   module necks to y -19.49    -> 38.05 is the limit
BAY_L_FIX = SERVO_POCKET_L                       # 46.22
BAY_W_WIDE = SERVO_POCKET_W                      # 38.80, where there is room
BAY_W_NARROW = BAY_W                             # 38.05, at the necked end
BAY_X_SPLIT = 24.0                               # measured transition


def roll_j4_module():
    x_srv = SERVO_AXIS_OFFSET + BAY_L / 2 + WALL_MIN - D_OUT / 2
    s = cq.Workplane("XY").circle(D_OUT / 2).extrude(J4_MOD_H)
    if x_srv > 0.01:
        s = s.union(cq.Workplane("XY").center(x_srv / 2, 0)
                    .rect(x_srv, D_OUT).extrude(J4_MOD_H))
        s = s.union(cq.Workplane("XY").center(x_srv, 0)
                    .circle(D_OUT / 2).extrude(J4_MOD_H))

    # 6706 seat in the inboard face
    s = s.cut(cq.Workplane("XY").circle((WOD + BRG_FIT) / 2).extrude(WB))
    # lead-in chamfer at the bearing mouth
    s = s.cut(cq.Workplane("XY").circle((WOD + BRG_FIT) / 2 + BRG_CHAMFER)
              .workplane(offset=BRG_CHAMFER).circle((WOD + BRG_FIT) / 2)
              .loft(combine=False).translate((0, 0, -BRG_CHAMFER)))

    # --- THE FIX -------------------------------------------------------
    # Both of these reach BAY_FLOOR. Previously the O33 stopped at 10.000
    # and the O22 at 10.100, leaving a 0.100 mm annular skin between them.
    # Cut from below the part (z = -1) to BAY_FLOOR + OVERSHOOT.
    depth = (BAY_FLOOR + OVERSHOOT) - (-1.0)
    s = s.cut(cq.Workplane("XY").circle(WSEAT / 2)
              .extrude(depth).translate((0, 0, -1.0)))
    s = s.cut(cq.Workplane("XY").circle(HORN_BORE_D / 2)
              .extrude(depth).translate((0, 0, -1.0)))
    # -------------------------------------------------------------------

    # servo bay, open at the top.
    #
    # SECOND COINCIDENT-PLANE FAULT, found after the first fix.
    # The bay floor and the O33 bore top were BOTH at z = BAY_FLOOR. Where
    # the rectangular bay reaches outside the O33 circle the floor is real
    # structure (2.1-4.0 mm), but exactly at the boundary the two cuts left
    # a 0.096 mm sliver -- measured at x 14.5..20.0, y +/-4..10, two
    # crescents where the bay corner overhangs the bore.
    #
    # Dropping the bay BELOW the bore top by one overshoot removes the
    # sliver without touching the floor further out, because the floor there
    # is bounded by the O56 lobe, not by this cut.
    # wide section, where the module is full width
    x0 = SERVO_AXIS_OFFSET - BAY_L_FIX / 2.0
    wide_l = BAY_X_SPLIT - x0
    s = s.cut(cq.Workplane("XY").center(x0 + wide_l / 2.0, 0)
              .rect(wide_l, BAY_W_WIDE).extrude(J4_MOD_H + OVERSHOOT)
              .translate((0, 0, BAY_FLOOR - OVERSHOOT)))
    # narrow section, out to the necked end
    x1 = SERVO_AXIS_OFFSET + BAY_L_FIX / 2.0
    narrow_l = x1 - BAY_X_SPLIT
    s = s.cut(cq.Workplane("XY").center(BAY_X_SPLIT + narrow_l / 2.0, 0)
              .rect(narrow_l, BAY_W_NARROW).extrude(J4_MOD_H + OVERSHOOT)
              .translate((0, 0, BAY_FLOOR - OVERSHOOT)))
    for dx in (-SERVO_BOLT_X / 2, SERVO_BOLT_X / 2):
        for dy in (-SERVO_BOLT_Y / 2, SERVO_BOLT_Y / 2):
            s = s.cut(cq.Workplane("XY").center(SERVO_AXIS_OFFSET + dx, dy)
                      .circle(SERVO_BOLT_D / 2).extrude(8.0)
                      .translate((0, 0, J4_MOD_H - BAY_T - 4.0)))

    # J5 fork inserts, blind from the top.
    #
    # DEPTH IS NOT M3_INSERT_L HERE. At 7.50 the blind floor lands at
    # J4_MOD_H - 7.50 = 29.220, and the bore ceiling beside it sits at
    # 29.200 -- a 0.020 mm disc of material between two planes, 7.75 mm2
    # of it. That is a tenth of a layer: the printer steps straight over
    # it and leaves a hole, and the insert bottoms out on nothing.
    #
    # Deepen to 8.00 so the floor lands at 28.720, clear of 29.200 by
    # 0.48 mm = more than two 0.20 mm layers. The heat-set insert is
    # 7.5 mm long, so 8.00 still bottoms it correctly with 0.5 mm of
    # swarf relief.
    INSERT_L_J4 = 8.00
    for sy in (-1, 1):
        for sz in (-1, 1):
            s = s.cut(cq.Workplane("XY").center(sy * END_BOLT_Y / 2,
                                                sz * END_BOLT_Z / 2)
                      .circle(M3_INSERT_D / 2).extrude(-INSERT_L_J4)
                      .translate((0, 0, J4_MOD_H)))

    # servo cable exit
    s = s.cut(cq.Workplane("XY").center(x_srv + D_OUT / 2 - 8, 0)
              .circle(SERVO_CABLE_D / 2).extrude(J4_MOD_H + 2)
              .translate((0, 0, -1)))
    return s


if __name__ == "__main__":
    print("ARM-450 rev H -- J4_module regenerated")
    print("   BAY_FLOOR  = J4_MOD_H - BAY_T = %.3f" % BAY_FLOOR)
    print("   both O%.0f and O%.0f now cut to %.3f (+%.2f overshoot)"
          % (WSEAT, HORN_BORE_D, BAY_FLOOR, OVERSHOOT))
    s = roll_j4_module()
    v = s.val().Volume()
    n = len(s.val().Solids())
    print("   volume %.3f mm3   solids %d" % (v, n))
    cq.exporters.export(s, os.path.join(HERE, "J4_module.step"))
    cq.exporters.export(s, os.path.join(HERE, "J4_module.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    print("   written to %s" % HERE)
