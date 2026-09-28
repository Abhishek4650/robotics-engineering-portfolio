#!/usr/bin/env python3
"""
ARM-450 rev I -- J2 shoulder with a real drive train, in the turret.

Same design as J3 (see gen_drive_j3.py / drive_common.py): servo seated on
its CAP FACE on the parting plane, stepped p1 floor, printed drive shaft
bolted to the horn, wiring window, no strap inserts.

Frames. turret_pro cuts the J2 bay on an XZ workplane, so in the turret the
joint axis runs along -Y (servo side) and the horn sits at (x=0, z=SHOULDER).
Joint frame -> turret frame is a +90 deg rotation about X, then +SHOULDER in
Z. The floor cuts and the shaft are built in the joint frame and moved over.

turret_p1 keeps the released trim at local z = -59.00 (the generator makes
-72.00; the skirt below -59 runs through spigot_collar -- checked earlier).
"""
import os
import sys

import cadquery as cq

PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARTS)
sys.path.insert(0, HERE)
import drive_common as DC                   # noqa: E402
import fixparams as FP                      # noqa: E402
# turret_pro binds Z_DRIVE from BAY_T at import, so set these FIRST
FP.BAY_L, FP.BAY_W, FP.BAY_T = DC.BAY_L, DC.PINCH, DC.BAY_T
FP.SERVO_BOLT_X = FP.SERVO_BOLT_Y = 0.0
import turret_pro as TP                     # noqa: E402
import gen_drive_j1 as J1                   # noqa: E402

P = TP.Z_BAY                    # 28.5, parting plane = cap face
Z_BRG_OUT = TP.Z_IDLE           # 24.5, drive bearing outer face
Z_HORN = P - DC.HORN_BELOW_CAP
Z_IDLE_END = -25.0
SH = TP.SHOULDER
TRIM_Z = -59.00
LAND_R = 16.75          # turret underside bears on the upper 6806's INNER ring only
COLLET_SLIT = 1.0       # two axial slits (x = +-13) in the spigot end ...
COLLET_TOP = -1.5       # ... from its end (world z -9) up to here, inside the collar


def to_turret(wp):
    return wp.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, 0, SH))


def to_joint(wp):
    return wp.translate((0, 0, -SH)).rotate((0, 0, 0), (1, 0, 0), -90)


def p1():
    s = TP.turret()
    s = s.cut(cq.Workplane("XY").center(0, -(P + 200)).rect(400, 400)
              .extrude(400).translate((0, 0, -200)))
    # turret_pro's 4 cover bolts sit at x +-34, where NEITHER half has any
    # material on the bolt axis (probed: p1 only at y -20.9..-15.6, p2 none):
    # the released p2 was held on by nothing. Rev I uses the fork split bolts.
    s = DC.p1_floor_cuts(to_joint(s), Z_BRG_OUT, P)
    s = DC.open_drive_pocket(s, TP.GAP, TP.SEAT_T, FP.BRG_OD)
    s = DC.split_bolts(s, P, TP.GAP, TP.Z_DRIVE, "p1")
    # IDLE bearing, J2 only: its pocket opened into the TURRET'S INTERIOR, and
    # a bearing slid out that way hits turret structure after 8.5 mm -- no
    # straight path to fit it (the installation sweep caught this). So the
    # idle bearing also presses in from the fork gap: drop its gap-side
    # shoulder (mirror of the drive side) and give it a Ø38 retention ring on
    # the turret side that touches the OUTER race only.
    s = s.cut(cq.Workplane("XY").circle((FP.BRG_OD + 0.02) / 2).extrude(TP.SEAT_T + 1.0)
              .translate((0, 0, -(TP.GAP + TP.SEAT_T) - 0.001)))
    s = s.cut(cq.Workplane("XY").circle((FP.BRG_OD + 0.02) / 2 + 0.5).workplane(offset=-0.5)
              .circle((FP.BRG_OD + 0.02) / 2).loft(combine=True).translate((0, 0, -TP.GAP + 0.001)))
    s = s.union(cq.Workplane("XY").circle(23.0).circle(19.0).extrude(1.5)
                .translate((0, 0, -TP.Z_IDLE - 1.5)))
    s = to_turret(s)
    # J2 gravity-spring lugs on the turret top (spring_parts.py, world -> turret: z - 50)
    import spring_parts as SP
    s = s.union(SP.j2_lugs().translate((0, 0, -50.0)))
    s = s.cut(cq.Workplane("XY").rect(400, 400).extrude(-400)
              .translate((0, 0, TRIM_Z)))
    # J1 drive key: a D inside the Ø22 spigot bore, over the hub plug's
    # length (world z -9..6 = turret z -59..-44). The keyed j1_hub drives the
    # turret through this flat; the released grubs could never be tightened.
    s = s.union(J1.spigot_key(J1.Z_SB, J1.Z_FLANGE_TOP + J1.PLUG_L + 1.5)
                .translate((0, 0, -50.0)))
    # Rule 4, J1 bearing path: the released underside land (r < 26) sat on the
    # base top AND the upper 6806's outer ring -- the turret rubbed the base.
    # Keep the land only inside the inner ring (d1/2 = 16.85, SKF 61806).
    s = s.cut(cq.Workplane("XY").circle(27.0).circle(LAND_R).extrude(0.6).translate((0, 0, -0.1)))
    # Rule 4, J1 torque path: the hub's D-plug sat in the spigot with 0.1 mm
    # radial / 0.2 mm key clearance (about +-1.9 deg of yaw play). Two axial
    # slits make the spigot end a COLLET: the spigot collar's pinch bolt now
    # squeezes the spigot onto the plug -- zero play, no new screw.
    for sx in (-1, 1):
        s = s.cut(cq.Workplane("XY").center(sx * 13.0, 0).rect(6.0, COLLET_SLIT)
                  .extrude(COLLET_TOP - (J1.Z_SB - 1.0)).translate((0, 0, J1.Z_SB - 1.0 - 50.0)))
    return s


def p2():
    s = TP.turret()
    keep = (cq.Workplane("XY").center(0, -(P + 200)).rect(400, 400)
            .extrude(400).translate((0, 0, -200)))
    s = to_joint(s.intersect(keep))
    # SERVO POD. The correct-depth bay (34.99) runs out through the turret's
    # rounded outline: the back wall was missing over x 7..35 and both pinch
    # walls over the deep rear corner (backwall_map.py). Close it with a
    # 2.4 mm shell round the bay -- the fork housings' wall -- so the pinch
    # grips the full case and the back is a real wall.
    x0, x1 = DC.SERVO_OFF - DC.BAY_L / 2, DC.SERVO_OFF + DC.BAY_L / 2
    w, hy = TP.BACK_T, DC.PINCH / 2
    s = s.union(cq.Workplane("XY").center((x0 + x1) / 2, 0)
                .rect(x1 - x0 + 2 * w, 2 * (hy + w)).extrude(TP.Z_DRIVE - P)
                .translate((0, 0, P)))
    s = s.cut(cq.Workplane("XY").center((x0 + x1) / 2, 0)
              .rect(x1 - x0, 2 * hy).extrude(DC.BAY_T + 1.0).translate((0, 0, P - 1.0)))
    s = DC.split_bolts(s, P, TP.GAP, TP.Z_DRIVE, "p2")
    s = DC.p2_servo_screws(s, P, TP.Z_DRIVE, TP.BACK_T)     # servo screwed by its own back holes
    s = DC.p2_wire_window(s, TP.Z_DRIVE, TP.BACK_T)
    # cable exit, as in the forks (fork_pro: off + BAY_L/2 - 6, O8)
    s = s.cut(cq.Workplane("XY").center(x1 - 6.0, 0).circle(8.0 / 2)
              .extrude(TP.BACK_T + 2).translate((0, 0, TP.Z_DRIVE - TP.BACK_T - 1)))
    return to_turret(s)


def shaft():
    # the upper link hangs along world Z, so its clamp grubs (link +-y) point
    # along world +-X = joint +-X: the flat faces +X (verify_clamp, step 4)
    # DOUBLE-D (Rule 4): each link half is locked by two M5 set screws, one on
    # each flat, threaded into the link's own O4.2 side holes -- zero play
    return to_turret(DC.shaft(Z_IDLE_END, Z_HORN, flat_half=TP.GAP, flat_ang=0.0, double=True))


def main():
    print("J2 rev I   P %.2f  horn face %.3f  Z_DRIVE %.2f  (turret frame, axis -Y)"
          % (P, Z_HORN, TP.Z_DRIVE))
    ok = True
    for nm, fn in (("J2_turret_p1", p1), ("J2_turret_p2", p2),
                   ("J2_shaft", shaft)):
        s = fn()
        sol = s.val()
        n = len(sol.Solids())
        bb = sol.BoundingBox()
        print("   %-13s %9.1f mm3  solids %d  y %7.2f..%7.2f  z %7.2f..%7.2f"
              % (nm, sol.Volume(), n, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
        ok &= (n == 1)
        cq.exporters.export(s, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(s, os.path.join(HERE, nm + ".stl"),
                            tolerance=0.01, angularTolerance=0.1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
