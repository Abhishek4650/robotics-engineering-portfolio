#!/usr/bin/env python3
"""
ARM-450 rev I -- J3 elbow with a real drive train.

Rev H seated the servo against p2 only. Checked against p1 and the forearm,
two defects appeared: the servo's front cap sank 2.61 mm into p1's floor, and
the horn touched nothing -- it spun inside the Ø26 bore of the joint tube.
This version:

  * seats the servo on its CAP FACE on the parting plane (drive_common.py);
  * gives p1 a stepped floor: Ø38 x 0.6 recess (floor bears on the bearing's
    OUTER race only), Ø31 shaft bore, relief for the step and horn;
  * replaces the bought alu tube with a PRINTED SHAFT (user's choice) whose
    drive end bolts straight to the horn on the proven BCD-14 pattern;
  * opens a wiring window in p2's back wall over the two bus connectors;
  * drops the fork_pro strap inserts (p1 covers them; the strap cannot be
    fitted and is not needed -- the servo is captured on all six sides).
Mounting face, spigot, end bolts and the four split bolts are fork_pro's,
unchanged, so J3 still bolts to the upper link exactly as before.
"""
import os
import sys

import cadquery as cq

PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARTS)
sys.path.insert(0, HERE)
import fork_pro as FK                       # noqa: E402
import drive_common as DC                   # noqa: E402
from fixparams import BRG_OD, BRG_W         # noqa: E402

# fork() cuts the bay "st + 1" deep and puts the back face at z_bay + st +
# BACK_T, which left a 1.4 mm back wall and a bay 35.99 deep, not BAY_T
# (parameter audit). Pass st = BAY_T - 1 and BACK_T + 1: bay exactly BAY_T,
# back wall 2.4, back face (Z_DRIVE) unchanged.
BACK_T = FK.BACK_T                           # 2.4, the real back wall
FK.BAY_L, FK.BAY_W, FK.BAY_T = DC.BAY_L, DC.PINCH, DC.BAY_T - 1.0
FK.BACK_T = BACK_T + 1.0
FK.SERVO_BOLT_X = FK.SERVO_BOLT_Y = 0.0     # case screws not used (pinch lock)

KW = dict(brg_od=BRG_OD, brg_w=BRG_W)
Z_IN = FK.FORK_HALF                          # 15.5
Z_BRG_OUT = Z_IN + FK.SEAT_T + BRG_W         # 24.5  drive bearing outer face
P = FK.split_line(BRG_W)                     # 28.5  parting plane = cap face
Z_DRIVE = P + DC.BAY_T + BACK_T
Z_HORN = P - DC.HORN_BELOW_CAP               # 25.489
Z_IDLE_END = -(Z_IN + FK.SEAT_T + BRG_W) - 0.5   # -25.0, as the alu tube


def p1():
    s = FK.fork(**KW)
    s = s.cut(cq.Workplane("XY").rect(400, 400).extrude(400).translate((0, 0, P)))
    s = DC.split_bolts(s, P, Z_IN, Z_DRIVE, "p1")
    s = DC.p1_floor_cuts(s, Z_BRG_OUT, P)
    s = DC.open_drive_pocket(s, Z_IN, FK.SEAT_T, BRG_OD)
    # J3 gravity-spring lugs (spring_parts.py): world -> fork local is
    # "minus 209 in z, then +120 deg about (1,1,1)" (x->y, y->z, z->x)
    import spring_parts as SP
    to_local = lambda w: w.translate((0, 0, -209.0)).rotate((0, 0, 0), (1, 1, 1), 120)
    # rev I.1: the lugs are sunk into the round cheek tops and blended (SP.lug).
    # Proof the cheek arcs SP assumes are this fork's, and that the sunk part
    # of each lug only overlaps material (it must not fill a pocket or hole):
    body = s.val()
    for sy in (1, -1):
        zc, R, _ = SP.J3_CHEEK[sy]
        yw = sy * (SP.PIN_Y - 3.75)
        for dz, want in ((-0.05, True), (0.05, False)):
            pt = cq.Vector(zc + R + dz - 209.0, 0.0, yw)          # world (0, yw, z) in fork local
            assert body.isInside(pt) == want, "J3 cheek arc (side %+d) is not where spring_parts puts it" % sy
        lug = to_local(SP.lug(sy, None, SP.J3_AXIS_Z + SP.A3, cheek=SP.J3_CHEEK[sy])).val()
        disk = to_local(cq.Workplane().add(SP._cyl_y(0.0, zc, R))).val()
        sunk = lug.intersect(disk)
        gap = sunk.Volume() - sunk.intersect(body).Volume()
        assert gap < 1e-6, "sunk lug (side %+d) fills %.4f mm3 of a hole" % (sy, gap)
    lugs = to_local(SP.j3_lugs())
    s = s.union(lugs)
    # the 4 fork -> upper-link bolt heads sit on this floor (world z 183) right
    # under the swinging forearm: sunk 3.2 mm into it (M3 x 10 now)
    import gen_drive_j4 as J4
    return s.cut(DC.floor_head_counterbores(J4.BOLTS, 183.0, 209.0))


def p2():
    s = FK.fork(**KW)
    s = s.cut(cq.Workplane("XY").rect(400, 400).extrude(-400).translate((0, 0, P)))
    s = DC.split_bolts(s, P, Z_IN, Z_DRIVE, "p2")
    return DC.bay_shell(s, P, Z_DRIVE, BACK_T)


def shaft():
    return DC.shaft(Z_IDLE_END, Z_HORN, flat_half=Z_IN, double=True)   # two set-screw flats


def main():
    print("J3 rev I   P %.2f   horn face %.3f   z_drive %.2f   shaft %.2f..%.3f"
          % (P, Z_HORN, Z_DRIVE, Z_IDLE_END, Z_HORN))
    ok = True
    for nm, fn in (("J3_p1", p1), ("J3_p2", p2), ("J3_shaft", shaft)):
        s = fn()
        sol = s.val()
        n = len(sol.Solids())
        bb = sol.BoundingBox()
        print("   %-9s %9.1f mm3  solids %d  z %7.2f..%7.2f"
              % (nm, sol.Volume(), n, bb.zmin, bb.zmax))
        ok &= (n == 1)
        cq.exporters.export(s, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(s, os.path.join(HERE, nm + ".stl"),
                            tolerance=0.01, angularTolerance=0.1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
