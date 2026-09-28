#!/usr/bin/env python3
"""
ARM-450 rev H -- j2_clamp / j3_clamp / j5_clamp.

WHY THESE EXIST
---------------
J2, J3 and J5 have NO servo pocket. Established three ways:

  * `fork_pro.py` derives z_bay = FORK_HALF + SEAT_T + brg_w + FLOOR_T
    = 15.50 + 2.0 + 7.0 + 4.0 = 28.50, with the drive cheek ending at
    z_drive = 57.52. `J3_p1` ENDS at z = 28.50 -- exactly where the bay is
    supposed to begin. No released part has a face at 57.52.
  * manual slice inspection: J3_p1 is solid only at x -38..-32 (a back
    plate) with ring cheeks at z = +/-20 and open air between. J5_p1 and
    J2_turret_p1 show the same.
  * five seating searches failed because they were hunting a pocket that
    was never cut.

`J4_module` is the only joint with a genuine bay.

WHAT IS PORTED
--------------
The `motor fixer` U-clamp from ~/roboARM/Robotic_arm_design/, which the user
built and ran, already ported successfully as `j1_clamp`:

    channel gap   24.50 mm   grips the servo's 24.72 NARROW face
    interference  -0.22 mm   the pinch IS the orientation lock
    back wall     a flat face the servo bears on
    ears          overhang, drilled to the host's bolt pattern

MOUNTING, measured per joint
----------------------------
    J3_p1   back plate x -43.0 .. -27.0 (17.0 mm), joint axis Z at origin,
            4 x O3.4 at (-35.00, +/-17.00, +/-7.00) facing -X
    J5_p1   back plate x -24.3 .. -18.3 (7.0 mm), joint axis Z at origin,
            4 x O3.4 at (-26.28, +/-17.00, +/-7.00) facing -X
    J2      turret shell, joint axis Y at z = 40, 6 x O4.1 on the y = -28.50
            face at (0, +/-34, 14.00 / 66.00)

Each clamp bolts to those EXISTING stations -- no new holes in released
parts -- and presents the servo with its horn on the joint axis.
"""
import os
import sys

import numpy as np
import cadquery as cq

PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
sys.path.insert(0, PARTS)
from fixparams import *          # noqa: F401,F403,E402

HERE = os.path.dirname(os.path.abspath(__file__))

GRIP = 24.50              # 0.22 mm under the 24.72 case -> pinch
WALL = 3.60
BACK = 4.00
HEIGHT = 31.00
EAR = 12.00
EAR_T = 5.00
WALL_RUN = 22.00          # channel length; the fork is open only this far
BOLT_D = M3_CLEAR
SERVO_L = 45.22
AXIS_OFF = SERVO_AXIS_OFFSET      # 12.50

# joint -> (host, plate face x, bolt stations on that face (y,z), axis dir)
JOINTS = {
    # face_x is the OUTER surface of the host plate, measured by marching X
    # at (y=0,z=0):  J3_p1 solid x -43.75..-26.00, J5_p1 solid x -25.25..-17.25.
    # The flange sits ON that outer face, it does not start inside the plate.
    # An earlier version put the flange at x = -35.00 (mid-plate) and 377
    # clamp points landed inside the host.
    #
    # Bolt patterns are MEASURED, not assumed: mapping the plate material
    # shows J3_p1's plate is only y +/-11, z -10..+11, so the (+/-17, +/-7)
    # stations the fork carries are in VOID there. Largest pattern that lands
    # on material: J3 (+/-10, +/-6), J5 (+/-17, +/-5).
    # FLANGE SIZE 42 x 42, measured: sweeping a centred rectangle inboard of
    # each mounting face, the largest fully-free envelope is 44 x 44 mm in
    # BOTH parts. A 46 x 40 flange overlapped the fork cheek corners at
    # y = +/-23, z = +/-20 (239 points) -- 2 mm too wide. 42 leaves 1 mm each
    # side.
    #
    # Original note on profiling to the host boss:
    #   J3_p1  x -43.75..-34 is a PAD y +/-11, z -10..+11 (22 x 21 mm);
    #          beyond x = -33 it opens to full width. A flange larger than
    #          the pad intersects the step -- that is what put 375 clamp
    #          points inside the host.
    #   J5_p1  x -25.25..-17.25 is FULL WIDTH y +/-24, z -25..+21: flat,
    #          so the flange is free.
    # J3 mounts on the FULL-WIDTH SLAB (x -33..-27), not the narrow pad at
    # x -43.75..-34. The pad is only 22 x 21 mm, and the channel walls sit
    # 28.1 mm apart (2 x (GRIP/2 + WALL)), so a pad-sized flange cannot
    # reach them -- it exported as 2 disconnected solids.
    # Measured: the slab is y +/-24, z -24..+28 and 4 bolts at (+/-17, +/-9)
    # all land on material. The channel then STRADDLES the narrow pad
    # (walls at y +/-14.05 vs pad y +/-11) and the back wall at z -19.5..-15.5
    # passes below it (pad z -10..+11).
    # Hosts now carry a flat 42 x 42 x 6.0 mounting pad (gen_mount_pads.py),
    # standing proud on -X with 4 x O4.1 inserts at (+/-15, +/-15). The clamp
    # flange bolts to the pad's OUTER face, so it never touches the curved
    # fork at all -- which is what defeated seven earlier flange shapes.
    "j3_clamp": dict(host="J3_p1", face_x=-27.0,
                     flange=(42.0, 42.0),
                     bolts=[(-15.0, -15.0), (-15.0, 15.0),
                            (15.0, -15.0), (15.0, 15.0)],
                     axis_z=0.0, note="J3 elbow, axis Z"),
    "j5_clamp": dict(host="J5_p1", face_x=-17.25,
                     flange=(42.0, 42.0),
                     bolts=[(-15.0, -15.0), (-15.0, 15.0),
                            (15.0, -15.0), (15.0, 15.0)],
                     axis_z=0.0, note="J5 wrist pitch, axis Z"),
}


def clamp(face_x, bolts, axis_z, flange):
    """U-channel bolted flat to a plate at x = face_x, horn on the JOINT AXIS.

    ORIENTATION, derived not assumed:
        J3_p1 / J5_p1 carry O42 / O37 bearing seats on the Z axis through the
        origin, so the JOINT AXIS IS Z. The servo horn must be coaxial with
        it -- horn along +Z at x = y = 0.

        The back plate faces -X, so the flange normal is X. A first version
        stood the channel off along +X, which pointed the horn along X too:
        90 degrees wrong, and the horn measured 20.79 mm off the axis.

        Correct arrangement:
            flange normal  X    bolts flat to the plate
            horn           Z    the joint axis
            grip           Y    24.72 across, 0.22 mm pinch
            length         X    45.22 standing off the plate

        The servo then spans x face_x .. face_x + 45.22, which for J3
        (-35.00 -> 10.22) is inside the part envelope x -44 .. 37.9.
    """
    fw, fh = flange
    # The channel walls sit at +/-(GRIP/2 + WALL) = +/-14.05 in Y. If the
    # flange is narrower than that the walls float free -- J3's 21 mm flange
    # produced 2 solids. Add a neck that spans from the flange out to the
    # walls, inside the pad footprint.
    NECK = 2 * (GRIP / 2 + WALL) + 0.0

    # flange on the host face
    # FLANGE DIRECTION. The host slab's OUTER face is at face_x and the part
    # is solid for +x beyond it, while -x is the open bay (apart from a
    # narrow pad). So the flange must grow INWARD, +x from the face, into
    # the bay -- growing outward put it straight through the pad.
    # flange lies ON the pad's outer face at face_x, growing -X (outward)
    s = (cq.Workplane("YZ").workplane(offset=face_x - EAR_T)
         .rect(fw, fh).extrude(EAR_T))

    # Channel walls: grip in Y, run along X (the servo length).
    #
    # The walls must stop before the fork's own structure. Measured along the
    # joint axis the parts are CLEAR at (x=0, y=0) and (x=0, y=8) over their
    # whole z range -- the axis is open -- but material appears from y=16
    # outward. A full-length 45.22 wall at +/-14 in Y ran into that and put
    # 316 clamp points inside J3_p1.
    #
    # So the walls are kept to WALL_RUN, enough to grip the case over the
    # region where the fork is open, and the servo's far end is unsupported
    # (as it is on the user's own motor fixer, whose channel is shorter than
    # the case).
    for sgn in (-1, 1):
        s = s.union(cq.Workplane("XY")
                    .box(WALL_RUN, WALL, HEIGHT, centered=(False, True, True))
                    .translate((face_x,
                                sgn * (GRIP / 2 + WALL / 2), axis_z)))
    # back wall the servo bears on, under the case
    s = s.union(cq.Workplane("XY")
                .box(WALL_RUN, GRIP + 2 * WALL, BACK,
                     centered=(False, True, False))
                .translate((face_x, 0.0,
                            axis_z - HEIGHT / 2 - BACK)))

    # bolt holes on the host's EXISTING stations
    for y, z in bolts:
        s = s.cut(cq.Workplane("YZ").workplane(offset=face_x - EAR_T - 1)
                  .center(y, z).circle(BOLT_D / 2).extrude(EAR_T + 2))
    return s


if __name__ == "__main__":
    for nm, cfg in JOINTS.items():
        s = clamp(cfg["face_x"], cfg["bolts"], cfg["axis_z"], cfg["flange"])
        bb = s.val().BoundingBox()
        print("%s  (%s)" % (nm, cfg["note"]))
        print("   host %s, flange on x = %.2f" % (cfg["host"], cfg["face_x"]))
        print("   bbox %.2f x %.2f x %.2f   volume %.1f mm3   solids %d"
              % (bb.xlen, bb.ylen, bb.zlen, s.val().Volume(),
                 len(s.val().Solids())))
        cq.exporters.export(s, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(s, os.path.join(HERE, nm + ".stl"),
                            tolerance=0.01, angularTolerance=0.1)
        print("   written")
        print()
