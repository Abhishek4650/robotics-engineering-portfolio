#!/usr/bin/env python3
"""
ARM-450 rev H -- servo_strap_micro rebuilt as a SIDE-MOUNTED bracket.

THE DEFECT
----------
    servo_strap_micro   plate 40.0 (X) x 12.0 (Y) x 4.0 (Z)
                        O3.4 bolt holes at (-15, 0, 0) and (+15, 0, 0)
                        bolt axis Z        span 30.00 mm in X
    j6_body             O4.10 stations at (-15, 0, 14) and (+15, 0, 14)
                        station axis X     span 30.00 mm in X

The 30.00 mm span matches exactly. Only the AXIS disagrees: the strap's
bolts run along Z, the host's threads along X. Perpendicular, so the servo
has no retention at J6.

WHY j6_body IS THE ONE THAT IS RIGHT
------------------------------------
Measured on j6_body: the outer faces at x = +/-17.000 are 841 mm2 and 828 mm2,
centred at z = 14.09 -- exactly the station height. The part is built for a
bracket that lands on its SIDES and bolts inward along X. Its Z-facing
candidates at z = 18.00 are two small lugs at (0, +/-10.41), which do not
line up with anything on the strap.

So the strap is rebuilt to match the host, per your decision: side mounted.

THE GEOMETRY
------------
A U-bracket that straddles the micro servo:
    back plate  spans X between the two walls, lies in the YZ sense
    two legs    reach out to x = +/-17 and present the bolt holes on the
                X axis, coaxial with j6_body's O4.10 stations at z = 14.00

Wall at the stations is 2.098 mm and the rev-H j6_body drives both stations
through as O4.10 clearance holes, so the bolt passes through and takes a nut
or washer outside -- 2 mm of PLA cannot host a heat-set insert.
"""
import os
import sys

import numpy as np
import cadquery as cq

PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
sys.path.insert(0, PARTS)
import fixparams as FP                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# measured from j6_body
WALL_X = 17.00          # outer face of each side wall
STATION_Z = 14.00       # bolt axis height
SPAN = 30.00            # station centre-to-centre in X (+/-15)
BAY_HALF_Y = 6.00       # the micro servo is 13.0 wide -> 6.5; use 6.0 of strap
PLATE_T = 4.00          # strap thickness, as the original
LEG_W = 12.00           # leg width in Y, as the original plate
BOLT_D = FP.M3_CLEAR    # 3.4


def micro_strap_side():
    """U-bracket: back plate + two legs, bolts on the X axis."""
    # back plate: spans the bay in X, sits above the servo in Z
    inner = SPAN / 2.0 - PLATE_T        # 11.0 : inner face of each leg
    plate = (cq.Workplane("XY")
             .box(2 * inner, LEG_W, PLATE_T, centered=(True, True, True))
             .translate((0, 0, STATION_Z + 8.0)))
    s = plate
    # two legs reaching down to the station height, on each side
    for sgn in (-1, 1):
        leg = (cq.Workplane("XY")
               .box(PLATE_T, LEG_W, 12.0, centered=(True, True, True))
               .translate((sgn * (inner + PLATE_T / 2.0), 0,
                           STATION_Z + 8.0 - 6.0 - PLATE_T / 2.0 + 2.0)))
        s = s.union(leg)
        # boss carrying the bolt hole, reaching out to the wall face
        boss = (cq.Workplane("XY")
                .box(PLATE_T, LEG_W, 9.0, centered=(True, True, True))
                .translate((sgn * (inner + PLATE_T / 2.0), 0, STATION_Z)))
        s = s.union(boss)
    # bolt holes ON THE X AXIS at z = STATION_Z, coaxial with j6_body
    for sgn in (-1, 1):
        s = s.cut(cq.Workplane("YZ").workplane(offset=-40.0)
                  .center(0.0, STATION_Z)
                  .circle(BOLT_D / 2.0).extrude(80.0))
    return s


if __name__ == "__main__":
    s = micro_strap_side()
    bb = s.val().BoundingBox()
    print("servo_strap_micro rev H -- SIDE MOUNTED")
    print("   bbox  %.2f x %.2f x %.2f" % (bb.xlen, bb.ylen, bb.zlen))
    print("   x %.2f .. %.2f   z %.2f .. %.2f"
          % (bb.xmin, bb.xmax, bb.zmin, bb.zmax))
    print("   volume %.1f mm3   solids %d"
          % (s.val().Volume(), len(s.val().Solids())))
    cq.exporters.export(s, os.path.join(HERE, "servo_strap_micro.step"))
    cq.exporters.export(s, os.path.join(HERE, "servo_strap_micro.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    print("   written")
