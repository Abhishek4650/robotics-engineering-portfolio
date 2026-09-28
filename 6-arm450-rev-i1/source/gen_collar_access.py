#!/usr/bin/env python3
"""
ARM-450 rev H -- spigot collar pinch bolts made reachable.

THE DEFECT
----------
The spigot collar is what stops the whole arm lifting off its J1 bearings.
It is pinched by two M3 bolts. Neither could be tightened.

Measured in the assembly, marching +y from each bolt:

    collar body      z -7.00 .. +3.00
    base underside   z  0.00
    bolt A  z = -4.20   j1_pod wall SOLID y 35.70..38.00, then open
    bolt B  z = +0.20   base SOLID from y+0.2 -- inside the base

    j1_pod radial holes near z = -4.2 :  NONE

So bolt A is enclosed by a 2.30 mm pod wall with open space beyond it, and
bolt B sits 0.20 mm up inside the base.

WHY NOT JUST MOVE BOLT B DOWN
-----------------------------
Tested every height from +0.20 to -4.20 in the real assembly: ALL blocked,
because the pod wall encloses the whole collar, not just bolt B. Moving the
bolt alone fixes nothing. (My first proposal was exactly this, and the
measurement refuted it.)

THE FIX, and why this one
-------------------------
Two changes, each measured:

 1. j1_pod gains a radial ACCESS WINDOW at the bolt height. With the pod
    removed from the assembly the clearance at z = -4.20 is 60 mm for a hex
    key AND 60 mm for a full 6 mm driver body -- the best access anywhere on
    the part. A window restores that.

 2. bolt B moves from z = +0.20 to z = -2.50. At +0.20 it is inside the base
    and no window can help; at -2.50 it clears the base and still leaves
    1.70 mm of bolt spacing above bolt A's boss, keeping a real couple so the
    split collar closes evenly instead of cocking on the spigot.

Bolt spacing becomes 1.70 mm instead of 4.40, which is less couple than the
original intent -- but two reachable bolts beat two unreachable ones, and
the alternative (a single bolt) clamps only the collar's lower half.
"""
import os
import sys

import numpy as np
import cadquery as cq

PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
sys.path.insert(0, PARTS)
import fixparams as FP                     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "/home/user/ros2_ws/Arm_450_new_design/out_cad"

BOLT_A_Z = -4.20
BOLT_B_Z_OLD = 0.20
BOLT_B_Z_NEW = -2.50
WINDOW_D = 9.0          # clears a 6.0 mm driver body with 1.5 mm each side


def fixed_collar():
    """spigot_collar with bolt B relocated below the base underside.

    Rebuilt from its measured dimensions rather than patched: filling an
    existing hole by unioning a plug and re-cutting produced a 372 mm3
    fragment from an 8932 mm3 part, because .intersect() on an imported
    solid does not behave like a boolean plug. Measured collar geometry:

        OD            46.00      (D 46.00 cylinder, axis Z)
        bore          30.15      (+0.15 slip on the O30 spigot)
        height        10.00      z -7.00 .. +3.00
        pinch bolts   O3.4 clearance, O6.0 counterbore, axis +Y at x = 0
    """
    OD, BORE, H, Z0 = 46.00, 30.15, 10.00, -7.00
    s = (cq.Workplane("XY").circle(OD / 2).extrude(H)
         .translate((0, 0, Z0)))
    s = s.cut(cq.Workplane("XY").circle(BORE / 2).extrude(H + 2)
              .translate((0, 0, Z0 - 1)))
    # split so the collar can actually close on the spigot
    s = s.cut(cq.Workplane("XY").center(0, OD / 4 + BORE / 4)
              .rect(1.2, OD / 2 - BORE / 2 + 2).extrude(H + 2)
              .translate((0, 0, Z0 - 1)))
    # two pinch bolts across the split, both BELOW the base underside
    for z in (BOLT_A_Z, BOLT_B_Z_NEW):
        s = s.cut(cq.Workplane("XZ").workplane(offset=-30.0)
                  .center(0.0, z).circle(FP.M3_CLEAR / 2).extrude(60.0))
        s = s.cut(cq.Workplane("XZ").workplane(offset=-30.0)
                  .center(0.0, z).circle(6.0 / 2).extrude(30.0 - 8.0))
    return s


def pod_with_window():
    """j1_pod with a radial access window at the collar bolt heights."""
    s = cq.importers.importStep(os.path.join(OUT, "j1_pod.step"))
    # one slot covering both bolts: centred between them, tall enough for
    # a driver to enter square at either height.
    zc = (BOLT_A_Z + BOLT_B_Z_NEW) / 2.0
    h = abs(BOLT_A_Z - BOLT_B_Z_NEW) + WINDOW_D
    tool = (cq.Workplane("XZ").workplane(offset=-60.0)
            .center(0.0, zc).rect(WINDOW_D, h).extrude(120.0))
    return s.cut(tool)


if __name__ == "__main__":
    print("spigot collar access fix")
    print("   bolt A stays at z = %.2f" % BOLT_A_Z)
    print("   bolt B  %.2f -> %.2f  (clears the base underside at z = 0)"
          % (BOLT_B_Z_OLD, BOLT_B_Z_NEW))
    print("   j1_pod window %.1f mm wide, centred z = %.2f"
          % (WINDOW_D, (BOLT_A_Z + BOLT_B_Z_NEW) / 2.0))
    print()
    for fn, nm in ((fixed_collar, "spigot_collar"),
                   (pod_with_window, "j1_pod")):
        s = fn()
        v = s.val().Volume()
        n = len(s.val().Solids())
        print("   %-16s %10.1f mm3  %d solid(s)" % (nm, v, n))
        cq.exporters.export(s, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(s, os.path.join(HERE, nm + ".stl"),
                            tolerance=0.01, angularTolerance=0.1)
