#!/usr/bin/env python3
"""
ARM-450 rev H -- J3 and J5 forks, drive cheek intact AND the servo bay
sized from the MEASURED servo in the orientation the joint axis forces.

TWO defects are fixed here.

1. No drive cheek.
   The released `J3_p1` / `J5_p1` stop at the parting plane (z=28.50 for
   J3), so there is no servo bay at all. `fork_pro.fork()` does build one;
   the released parts were cut from a different path. Calling fork_p1 /
   fork_p2 restores it.

2. BAY_W and BAY_T are swapped.
   `fork_pro.fork()` cuts the bay as rect(BAY_L, BAY_W) extruded BAY_T
   along +Z, and +Z IS the joint axis -- every bearing bore is a circle()
   on XY. So BAY_T is the dimension along the servo's OUTPUT axis.

   Measured from the user's own Motor.stl (see servo_geom.py, which
   re-derives every number from the mesh and self-checks):
       along the output axis, mounting face -> back of case = 33.10
       case cross-section normal to it                      = 45.22 x 24.72

   fixparams derives
       BAY_W = SERVO_W + 2*CLR = 38.05   but only 25.52 is needed -> 13.33 SLOP
       BAY_T = SERVO_T + CLR + 1.5 = 26.62 but 33.50 is needed    ->  6.88 SHORT

   13.33 mm of slop across the case means the servo can rattle and rotate
   in its own bay -- exactly the "floating servo" the user has said twice
   must not happen. 6.88 mm short means it does not go in at all.

   Corrected: BAY_W 25.52, BAY_T 33.50, both derived from the mesh.

   z_drive moves out by (33.50 - 26.62) = 6.88 mm per joint. That is a real
   change to the link geometry and is reported below.

Servo case screws: the supplied mesh does not model the mounting tabs, so
the pattern cannot be measured from it. The user supplied 19.05 x 20.29,
which is used here in place of fixparams' 35.0 x 20.0.
"""
import os
import sys

import cadquery as cq

PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARTS)
sys.path.insert(0, HERE)

import fixparams as FP                      # noqa: E402
import servo_geom as SG                     # noqa: E402

# --- correct the swapped bay BEFORE fork_pro binds them -------------------
_OLD = dict(BAY_L=FP.BAY_L, BAY_W=FP.BAY_W, BAY_T=FP.BAY_T,
            SERVO_BOLT_X=FP.SERVO_BOLT_X, SERVO_BOLT_Y=FP.SERVO_BOLT_Y)
FP.BAY_L = SG.BAY_L_Z
FP.BAY_W = SG.BAY_W_Z
FP.BAY_T = SG.BAY_T_Z
FP.SERVO_BOLT_X = 19.05      # user-supplied; not modelled in Motor.stl
FP.SERVO_BOLT_Y = 20.29

import fork_pro as FK                       # noqa: E402
import wrist_pro as WP                      # noqa: E402

from fixparams import BRG_OD, BRG_W          # noqa: E402

# J3 is a plain fork_pro fork. J5 IS NOT.
#
# `wrist_pro` builds J5 from the same fork_pro.fork_p1/p2 but with
# `mirror=True` and a `_clip_j5()` pass, and both are load-bearing:
#
#   mirror=True  puts the drive cheek on the far side of the blade from the
#                tool. Built the other way round the fork grows along +Z and
#                swallows the J6 bearing and the tool flange.
#   _clip_j5()   cuts the cheeks back J5_CLIP past the bore. Unclipped they
#                overhang the J6 axis ~30 mm and run straight through the
#                Ø40 flange (measured upstream: 0.39 cm3 into the flange,
#                0.10 into the bearing).
#
# Generating J5 with the plain J3 recipe -- which is what an earlier pass of
# this script did -- produces a part that is neither mirrored nor clipped and
# is NOT a drop-in replacement. It is also 6.88 mm longer now, so it would
# reach further into the flange than the upstream measurement.
JOINTS = {
    "J3": dict(kw=dict(brg_od=BRG_OD, brg_w=BRG_W),
               clip=None, note="elbow, 6806 30x42x7"),
    # J5 IS WITHDRAWN. With the correct wrist_pro recipe (mirror + clip)
    # the usable span is J5_FACE + J5_CLIP = 25.28 + 11.00 = 36.28 mm and
    # the ST3215 needs 46.02 -- short by 9.74 mm. The released J5_p2 is an
    # open C-channel with no floor and cannot hold a servo either. This
    # needs a design decision, not a parameter, so J5 is not generated.
}


def main():
    r = SG.measure()
    print("servo re-measured from mesh: below-face %.2f  above-face %.2f  %s"
          % (r["below"], r["above"], "AGREE" if r["ok"] else "DISAGREE"))
    if not r["ok"]:
        print("ABORT: servo_geom constants do not match the mesh")
        return 1
    print()
    print("bay corrected   L %.2f (was %.2f)   W %.2f (was %.2f)   T %.2f (was %.2f)"
          % (FP.BAY_L, _OLD["BAY_L"], FP.BAY_W, _OLD["BAY_W"],
             FP.BAY_T, _OLD["BAY_T"]))
    print("case screws     %.2f x %.2f (was %.2f x %.2f)"
          % (FP.SERVO_BOLT_X, FP.SERVO_BOLT_Y,
             _OLD["SERVO_BOLT_X"], _OLD["SERVO_BOLT_Y"]))
    print()
    ok = True
    for jn, cfg in JOINTS.items():
        kw = cfg["kw"]
        z = FK.split_line(kw.get("brg_w", BRG_W), kw.get("gap", FK.FORK_HALF))
        z_drive = z + FP.BAY_T + FK.BACK_T
        z_old = z + _OLD["BAY_T"] + FK.BACK_T
        print("%s  (%s)" % (jn, cfg["note"]))
        print("   parting plane z = %.2f   bay %.2f..%.2f"
              % (z, z, z + FP.BAY_T))
        print("   z_drive %.2f   (was %.2f, moved out %.2f mm)"
              % (z_drive, z_old, z_drive - z_old))
        for half, fn in (("p1", FK.fork_p1), ("p2", FK.fork_p2)):
            nm = "%s_%s" % (jn, half)
            try:
                s = fn(**dict(kw))
                if cfg["clip"] is not None:
                    s = cfg["clip"](s)
            except Exception as e:
                print("   %-8s FAILED: %s" % (nm, e))
                ok = False
                continue
            sol = s.val()
            v, n = sol.Volume(), len(sol.Solids())
            bb = sol.BoundingBox()
            print("   %-8s %9.1f mm3   solids %d   z %.2f..%.2f"
                  % (nm, v, n, bb.zmin, bb.zmax))
            if n != 1:
                print("            ^^ NOT A SINGLE SOLID")
                ok = False
            cq.exporters.export(s, os.path.join(HERE, nm + ".step"))
            cq.exporters.export(s, os.path.join(HERE, nm + ".stl"),
                                tolerance=0.01, angularTolerance=0.1)
        print()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
