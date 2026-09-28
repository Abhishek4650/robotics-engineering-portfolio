#!/usr/bin/env python3
"""
ARM-450 rev H -- J2 turret regenerated with the servo bay sized from the
MEASURED servo, the same correction applied to J3 and J5.

`turret_pro.py` inherits `BAY_T = SERVO_T + BAY_CLR + 1.5 = 26.62` from
fixparams, and cuts the bay `BAY_T` deep along the servo's OUTPUT axis.
Measured on the released `J2_turret_p2.stl`, the cavity is 27.11 mm deep
(y -55.11..-28.00) where the ST3215 needs 33.50 -- short by 6.39 mm, the
same swapped-axis error found at J3/J5.

The bay grows OUTWARD (away from the arm centreline). Verified free:
`base` is the only part in that region and it has NO material at y < -45
in the bay's z band (~30..55), so the turret can reach y = -63.90 without
touching anything.
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

_OLD = dict(BAY_L=FP.BAY_L, BAY_W=FP.BAY_W, BAY_T=FP.BAY_T,
            SERVO_BOLT_X=FP.SERVO_BOLT_X, SERVO_BOLT_Y=FP.SERVO_BOLT_Y)
FP.BAY_L = SG.BAY_L_Z
FP.BAY_W = SG.BAY_W_Z          # PINCH, 24.50 on the 24.72 case
FP.BAY_T = SG.BAY_T_Z          # 33.50 along the output axis
FP.SERVO_BOLT_X = 19.05
FP.SERVO_BOLT_Y = 20.29

import turret_pro as TP                     # noqa: E402
import cadquery as _cq                      # noqa: E402

# The released J2_turret_p1 starts at local z = -59.00, but the generator
# (with ORIGINAL parameters, checked) produces -72.00. The release was
# trimmed after generation: the spigot skirt below -59 runs straight through
# the spigot_collar, which occupies world z -7.00..3.00 = local -57..-47.
#
# This is pre-existing and not caused by the bay correction -- the same
# post-generation trim the released J5_p2 shows. Reapply it here so the
# rev H part matches the released envelope.
TRIM_Z = -59.00


def _trim(s):
    return s.cut(_cq.Workplane("XY").rect(400, 400).extrude(-400)
                 .translate((0, 0, TRIM_Z)))


def main():
    r = SG.measure()
    print("servo re-measured: below-face %.2f  above-face %.2f  %s"
          % (r["below"], r["above"], "AGREE" if r["ok"] else "DISAGREE"))
    if not r["ok"]:
        print("ABORT: servo_geom does not match the mesh")
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
    for nm, fn in (("J2_turret_p1", TP.turret_p1),
                   ("J2_turret_p2", TP.turret_p2)):
        try:
            s = fn()
            if nm == "J2_turret_p1":
                s = _trim(s)
        except Exception as e:
            print("   %-14s FAILED: %s" % (nm, e))
            ok = False
            continue
        sol = s.val()
        n = len(sol.Solids())
        bb = sol.BoundingBox()
        print("   %-14s %9.1f mm3  solids %d  y %7.2f..%7.2f  z %7.2f..%7.2f"
              % (nm, sol.Volume(), n, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
        if n != 1:
            print("                  ^^ NOT A SINGLE SOLID")
            ok = False
        cq.exporters.export(s, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(s, os.path.join(HERE, nm + ".stl"),
                            tolerance=0.01, angularTolerance=0.1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
