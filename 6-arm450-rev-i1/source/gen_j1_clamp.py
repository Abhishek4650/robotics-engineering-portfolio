#!/usr/bin/env python3
"""
ARM-450 rev H -- j1_clamp: a U-channel servo clamp for J1, ported from the
design that actually ran.

WHY THIS PART EXISTS
--------------------
`j1_pod` cannot hold the servo. Measured:

    servo case        45.22 long, output axis 12.50 off the case centre
    horn on J1 axis   -> case centre sits 12.50 off-axis
    far corner radius = sqrt((45.22/2 + 12.50)^2 + (24.72/2)^2) = 37.22 mm
    j1_pod inner bore radius (measured, z -30..-5)              = 35.70 mm
                                               INTERFERENCE     =  1.52 mm

An insertion sweep from z = -46 to -4 finds no height at which it clears, and
the bore is 35.65 mm in BOTH out_cad and REV_H -- a released-design defect.
Boring to O74.44 against a O76.0 outer leaves 0.78 mm of wall.

WHAT IS PORTED
--------------
From ~/roboARM/Robotic_arm_design/motor fixer.stl, which the user built and
ran. Measured from that file:

    overall        64.80 x 27.20 x 31.00
    channel gap    24.50 mm      grips the servo's 24.72 NARROW face
    interference   -0.22 mm      it pinches: that is the orientation lock
    back wall      a flat face the servo BEARS on
    ears           19.6 mm of overhang each end
    fixing         4 x O2.50 at x = +/-29.4, z = 2.02 / 8.52
                   -> 58.8 x 6.5 mm bolt spacing

The principle: the servo is gripped across its narrow dimension and bolted
down through overhanging ears. Orientation is locked by the pinch, not by a
pocket, and the horn points out of the open side on the joint axis.

WHAT IS ADAPTED FOR ARM-450
---------------------------
* the ears bolt UP into the base underside (z = 0), not sideways
* bolt circle r = 34.0 -- inside the base's solid annulus, measured solid
  from r = 20 to r = 28 and r = 40 to 58 at z = +0.5, and the pod already
  uses r = 34
* M3 clearance (O3.4), not M2.5: ARM-450 is M3 throughout
* the horn sits on the J1 axis, so the channel is offset by
  SERVO_AXIS_OFFSET = 12.50 mm
"""
import os
import sys

import cadquery as cq

PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
sys.path.insert(0, PARTS)
from fixparams import *          # noqa: F401,F403,E402

HERE = os.path.dirname(os.path.abspath(__file__))

# --- measured from the working `motor fixer` -------------------------------
GRIP = 24.50              # channel gap: 0.22 mm under the 24.72 case = pinch
WALL = 3.60               # side-wall thickness
BACK = 4.00               # back wall the servo bears on
HEIGHT = 31.00            # side-wall height, as the working part
EAR = 12.00               # ear length beyond the channel
EAR_T = 5.00              # ear thickness

# --- ARM-450 interface -----------------------------------------------------
# The base is NOT solid at r = 34. Measured at z = +2.0 it is solid only in
# an inner ring r = 20..28 and an outer rim r = 48..58, with a void between.
# Bolts at r = 34 (and my first attempt at r = 44) land in that void.
# r = 24.0 is the middle of the inner ring.
BOLT_R = 24.0
BOLT_D = M3_CLEAR         # 3.4
AXIS_OFF = SERVO_AXIS_OFFSET   # 12.50, horn to case centre
SERVO_L = 45.22


def j1_clamp():
    # channel runs along X, gap across Y, open at +Z.
    # The servo's case centre sits AXIS_OFF from the J1 axis so the horn
    # lands on x = y = 0.
    # Channel centre. The servo's horn sits toward one end of the case, so
    # with the horn on the J1 axis the CASE lands +AXIS_OFF away, not
    # -AXIS_OFF. Measured: placing the real mesh with its horn at x=0 puts
    # the case at x -10.10..+35.12, centre +12.51 -- matching +AXIS_OFF.
    # An earlier -AXIS_OFF put the channel on the opposite side entirely.
    cx = +AXIS_OFF
    L = SERVO_L + 2 * EAR
    outer_w = GRIP + 2 * WALL

    # back wall + two side walls
    s = (cq.Workplane("XY").center(cx, 0)
         .rect(L, outer_w).extrude(BACK))
    for sgn in (-1, 1):
        s = s.union(cq.Workplane("XY")
                    .center(cx, sgn * (GRIP / 2 + WALL / 2))
                    .rect(SERVO_L, WALL).extrude(HEIGHT))

    # ears: flat pads at each end, drilled to the base bolt circle
    for sgn in (-1, 1):
        s = s.union(cq.Workplane("XY")
                    .center(cx + sgn * (SERVO_L / 2 + EAR / 2), 0)
                    .rect(EAR, outer_w).extrude(EAR_T))

    # horn clearance through the back wall, on the J1 axis
    s = s.cut(cq.Workplane("XY").circle(HORN_CLEAR_D / 2)
              .extrude(BACK + 2).translate((0, 0, -1)))

    # Cable exit, carried over from j1_pod which this part replaces.
    # The pod's only remaining unique feature was its O8 cable bore; with
    # the servo held by this clamp the pod carries no load (no bolt holes
    # to the base, and nothing mates to its O32.00 or O71.20 registers).
    # Putting the exit here lets the pod be dropped: 44 g and 230 layers.
    s = s.cut(cq.Workplane("XZ").workplane(offset=-40.0)
              .center(cx + SERVO_L / 2 - 6.0, EAR_T + 8.0)
              .circle(SERVO_CABLE_D / 2).extrude(80.0))

    # 4 x M3 clearance on the BOLT_R circle, placed where the ears actually
    # are. An earlier version solved for y on the bolt circle at the ear's x
    # and produced only 2 holes at r = 44, both in the base's void ring.
    # Instead: put the four bolts at +/-45 degrees on the circle, then widen
    # the back plate so it reaches them.
    import numpy as np
    pts = []
    for a in (45.0, 135.0, 225.0, 315.0):
        t = np.radians(a)
        pts.append((BOLT_R * np.cos(t), BOLT_R * np.sin(t)))
    # a flange disc carrying the bolt circle, fused under the channel
    s = s.union(cq.Workplane("XY").circle(BOLT_R + 6.0).extrude(EAR_T))
    for x, y in pts:
        s = s.cut(cq.Workplane("XY").center(x, y)
                  .circle(BOLT_D / 2).extrude(EAR_T + BACK + 2)
                  .translate((0, 0, -1)))
    return s


if __name__ == "__main__":
    s = j1_clamp()
    bb = s.val().BoundingBox()
    print("j1_clamp  (ported from `motor fixer`)")
    print("   bbox     %.2f x %.2f x %.2f" % (bb.xlen, bb.ylen, bb.zlen))
    print("   channel  %.2f mm gap  (servo 24.72 -> %.2f mm pinch)"
          % (GRIP, 24.72 - GRIP))
    print("   volume   %.1f mm3   solids %d"
          % (s.val().Volume(), len(s.val().Solids())))
    cq.exporters.export(s, os.path.join(HERE, "j1_clamp.step"))
    cq.exporters.export(s, os.path.join(HERE, "j1_clamp.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    print("   written")
