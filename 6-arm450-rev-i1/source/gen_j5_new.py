#!/usr/bin/env python3
"""
ARM-450 — a NEW J5 wrist-pitch fork. Not a modification of the released
part; a fresh design on the arrangement that already works at J3.

WHY A NEW DESIGN
----------------
The released J5 ran the servo's 45.22 mm case LENGTH along the fork's local
x, between two faces that cannot move:

    mounting face  x = -25.28   (J5_FACE, set by the J4->J5 link spacing)
    clip plane     x = +11.00   (J5_CLIP, set by the J6 bearing and the
                                 O40 tool flange)
    usable                36.28 mm   -- the servo needs 46.02

That is 9.74 mm short, and no parameter fixes it. The released J5_p2 is an
open C-channel with no floor (probed at y=0: no material anywhere along x),
so it cannot retain a servo either. Modifying it would have to move J4->J5
spacing or the tool flange, which disturbs parts that are already correct.

THE FIX IS THE ORIENTATION, NOT THE SIZE
----------------------------------------
At J3 -- which works -- the case length runs ALONG the arm and the output
axis runs ACROSS it:

    J3 servo, world:  x 24.72   y 37.60 (output)   z 45.22 (length)

The released J5 put the 45.22 across the one direction that is boxed in.
Measured with J5 removed from the assembly, the only thing near the J5 axis
is `j6_body` at |y| <= 15.00; beyond that the space is open. So this design
uses J3's topology exactly:

    joint axis   world Y, through z = 390
    blade        j6_body, swinging in the fork slot
    servo        output on the joint axis, case length along the arm (Z),
                 case width across (X) -- both unobstructed

Stack outboard from the blade face, along the joint axis:
    fork gap        16.00   J5_GAP, 1.00 clearance on the O30 blade
    bearing seat     2.00   6706 outer race lands here
    bearing         4.00    6706, 30 x 37 x 4
    bay floor        4.00   carries the horn bore
    servo bay       33.50   measured: mounting face -> back of case + 0.40
    back wall        2.40
                   -----
                    61.90   total half-length, drive side

ORIENTATION LOCK
----------------
Same as J3 and as the user's own proven `motor fixer.stl`: the bay is a
24.50 mm channel on the servo's 24.72 mm face, a -0.22 mm PINCH, closed by
a strap on two M3 inserts. The four case screws cannot be used -- their
19.05 x 20.29 pattern puts the bolt circle at r = 13.92, inside the O37
bearing seat.
"""
import os
import sys

import cadquery as cq

PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARTS)
sys.path.insert(0, HERE)

import servo_geom as SG                      # noqa: E402
from fixparams import (WRIST_BRG_OD, WRIST_BRG_W, BRG_FIT, BRG_CHAMFER,
                       BRG_SHOULDER, M3_CLEAR, M3_INSERT_D, M3_INSERT_L,
                       END_BOLT_Y, END_BOLT_Z, WALL_MIN,
                       SERVO_CABLE_D)        # noqa: E402

# --- fixed by the rest of the machine -------------------------------------
J5_FACE = 25.28          # mounting face to bore, from J4->J5 spacing
J5_GAP = 16.00           # half the j6_body thickness + 1.00 clearance
BRG_OD = WRIST_BRG_OD    # 37.0
BRG_W = WRIST_BRG_W      # 4.0
SEAT_T = 2.00
FLOOR_T = 4.00
BACK_T = 2.40
HORN_CLEAR_D = 24.00     # horn boss clearance through the floor
CHEEK_R = 25.00          # outer radius of the cheeks
FORK_BACK = 8.00         # bridge thickness behind the swing circle

# --- derived --------------------------------------------------------------
Z_IN = J5_GAP                                   # inner face of both cheeks
Z_SEAT_TOP = Z_IN + SEAT_T + BRG_W              # 22.00
Z_BAY = Z_SEAT_TOP + FLOOR_T                    # 26.00  parting plane
Z_DRIVE = Z_BAY + SG.BAY_T_Z + BACK_T           # 61.90
Z_IDLE = Z_IN + SEAT_T + BRG_W                  # 22.00  idle outer face

BAY_L = SG.BAY_L_Z       # 46.02  along local X (up the arm once placed)
BAY_W = SG.BAY_W_Z       # 24.50  PINCH, across
BAY_T = SG.BAY_T_Z       # 33.50  along the joint axis
BAY_OFF = 12.50          # horn is this far off the case centre (measured)

# tool_flange, measured in THIS part's local frame from the assembly
FLANGE_X = 24.00 - 1.00        # 1.00 mm clearance
FLANGE_Z_LO = -19.85 - 1.00
FLANGE_Z_HI = 19.85 + 1.00


# The bay runs from BAY_OFF-BAY_L/2 to BAY_OFF+BAY_L/2 = -10.51..35.51, but
# a plain O50 cheek stops at x=25.00, so the servo would hang out of the
# open end with no wall to pinch it. Extend the drive cheek as a racetrack
# (second disc + connecting rectangle) far enough to wrap the case.
X_EXT = BAY_OFF + BAY_L / 2 + WALL_MIN - CHEEK_R    # 12.91


def _stadium(z0, z1, r=CHEEK_R, ext=0.0):
    """The cheek outline: a disc round the bore, extended back to the
    mounting face so the J4 bolts have material to land in, and (on the
    drive side) forward by `ext` to wrap the servo case."""
    p = cq.Workplane("XY").circle(r).extrude(z1 - z0)
    if ext > 0.01:
        p = p.union(cq.Workplane("XY").center(ext / 2, 0)
                    .rect(ext, 2 * r).extrude(z1 - z0))
        p = p.union(cq.Workplane("XY").center(ext, 0)
                    .circle(r).extrude(z1 - z0))
    p = p.union(cq.Workplane("XY").center(-J5_FACE / 2, 0)
                .rect(J5_FACE, 2 * r).extrude(z1 - z0))
    return p.translate((0, 0, z0))


def fork():
    """The whole J5 fork before splitting. Local +Z is the joint axis."""
    s = _stadium(Z_IN, Z_DRIVE, ext=X_EXT)       # drive cheek
    s = s.union(_stadium(-Z_IDLE, -Z_IN))        # idle cheek
    # bridge joining the two, behind the swing circle
    s = s.union(cq.Workplane("XY")
                .center(-J5_FACE + FORK_BACK / 2, 0)
                .rect(FORK_BACK, 2 * CHEEK_R)
                .extrude(Z_DRIVE + Z_IDLE)
                .translate((0, 0, -Z_IDLE)))
    s = s.edges("|Z").fillet(2.0)

    seat_d = BRG_OD - 2 * BRG_SHOULDER

    # --- bearing pockets, fitted from the OUTSIDE of each cheek -----------
    # idle cheek
    s = s.cut(cq.Workplane("XY").circle((BRG_OD + BRG_FIT) / 2)
              .extrude(BRG_W + BRG_CHAMFER).translate((0, 0, -Z_IDLE)))
    s = s.cut(cq.Workplane("XY").circle((BRG_OD + BRG_FIT) / 2 + BRG_CHAMFER)
              .workplane(offset=BRG_CHAMFER).circle((BRG_OD + BRG_FIT) / 2)
              .loft(combine=False)
              .translate((0, 0, -Z_IDLE - BRG_CHAMFER)))
    # drive cheek: opens toward the servo, so the race seats on the shoulder
    # facing the blade
    s = s.cut(cq.Workplane("XY").circle((BRG_OD + BRG_FIT) / 2)
              .extrude(BRG_W + BRG_CHAMFER)
              .translate((0, 0, Z_IN + SEAT_T - BRG_CHAMFER)))
    s = s.cut(cq.Workplane("XY").circle((BRG_OD + BRG_FIT) / 2 + BRG_CHAMFER)
              .workplane(offset=-BRG_CHAMFER).circle((BRG_OD + BRG_FIT) / 2)
              .loft(combine=False)
              .translate((0, 0, Z_SEAT_TOP + BRG_CHAMFER)))

    # seat bore, only as far as the OUTER face of the drive bearing. Run it
    # through and it eats the floor the horn bore needs.
    s = s.cut(cq.Workplane("XY").circle(seat_d / 2)
              .extrude(Z_SEAT_TOP + Z_IDLE + 1)
              .translate((0, 0, -Z_IDLE - 1)))
    # horn passes the floor on a O24 clearance, into the bearing counterbore
    s = s.cut(cq.Workplane("XY").circle(HORN_CLEAR_D / 2)
              .extrude(Z_BAY - Z_SEAT_TOP + 2)
              .translate((0, 0, Z_SEAT_TOP - 1)))

    # --- the servo bay ----------------------------------------------------
    # The case is NOT symmetric about the output axis: the horn sits
    # SERVO_AXIS_OFFSET = 12.50 mm off the case centre (measured from the
    # mesh, not assumed). The shaft must land on the joint axis, so the BAY
    # is offset by that amount instead. Centring the bay on the bore leaves
    # the case hanging 12.10 mm past the +x wall.
    s = s.cut(cq.Workplane("XY").center(BAY_OFF, 0).rect(BAY_L, BAY_W)
              .extrude(BAY_T + 1).translate((0, 0, Z_BAY)))
    # cable exit through the back wall, at the far end of the case
    s = s.cut(cq.Workplane("XY").center(BAY_OFF + BAY_L / 2 - 6, 0)
              .circle(SERVO_CABLE_D / 2).extrude(BACK_T + 2)
              .translate((0, 0, Z_DRIVE - BACK_T - 1)))

    # --- lightening: keep a skin, a boss round each bore, bay walls -------
    def prof(o, h, ext=0.0):
        p = cq.Workplane("XY").circle(CHEEK_R - o).extrude(h)
        if ext > 0.01:
            p = p.union(cq.Workplane("XY").center(ext / 2, 0)
                        .rect(ext, 2 * (CHEEK_R - o)).extrude(h))
            p = p.union(cq.Workplane("XY").center(ext, 0)
                        .circle(CHEEK_R - o).extrude(h))
        p = p.union(cq.Workplane("XY").center(-J5_FACE / 2 + o / 2, 0)
                    .rect(J5_FACE - o, 2 * (CHEEK_R - o)).extrude(h))
        return p

    def boss(h):
        return cq.Workplane("XY").circle(BRG_OD / 2 + 5.0).extrude(h)

    # NOTE: this must be a function, not a stored Workplane. A Workplane's
    # pending wires are consumed by the first .extrude(), so reusing one
    # raises "No pending wires present" on the second call.
    def keep(h):
        return (cq.Workplane("XY").center(BAY_OFF, 0)
                .rect(BAY_L + 2 * WALL_MIN, BAY_W + 2 * WALL_MIN)
                .extrude(h))
    # behind the bay
    s = s.cut(prof(WALL_MIN, Z_DRIVE - Z_BAY, X_EXT).translate((0, 0, Z_BAY))
              .cut(keep(Z_DRIVE - Z_BAY + 2)
                   .translate((0, 0, Z_BAY - 1))))
    # between bearing and bay floor
    s = s.cut(prof(WALL_MIN, BRG_W + SEAT_T - WALL_MIN, X_EXT)
              .translate((0, 0, Z_IN + WALL_MIN))
              .cut(boss(BRG_W + SEAT_T + 2).translate((0, 0, Z_IN - 1)))
              .cut(keep(BRG_W + SEAT_T + 2)
                   .translate((0, 0, Z_IN - 1))))
    # idle cheek
    s = s.cut(prof(WALL_MIN, Z_IDLE - Z_IN - WALL_MIN)
              .translate((0, 0, -Z_IDLE + WALL_MIN))
              .cut(boss(Z_IDLE - Z_IN + 2).translate((0, 0, -Z_IDLE - 1))))

    # --- clear the tool flange --------------------------------------------
    # Measured with J5 removed from the assembly and mapped into this part's
    # local frame, the O40 tool_flange occupies x >= 24.00 with |z| <= 19.85.
    # The drive cheek's racetrack reaches x = 37.91, so the two overlap in a
    # corner near the parting plane. Cut ONLY that corner: clipping the whole
    # extension (what the released design did) is what left no room for the
    # servo in the first place.
    #
    # The servo case ends at x = 35.11 and the bay floor is at z = Z_BAY, so
    # the material removed here is outboard skin, not bay wall.
    s = s.cut(cq.Workplane("XY")
              .center((FLANGE_X + 60.0) / 2, 0)
              .rect(60.0 - FLANGE_X + 60.0, 2 * (CHEEK_R + X_EXT + 10))
              .extrude(FLANGE_Z_HI - FLANGE_Z_LO)
              .translate((0, 0, FLANGE_Z_LO)))

    # --- mounting face: 4 clearance holes through to J4 --------------------
    for sy in (-1, 1):
        for sz in (-1, 1):
            s = s.cut(cq.Workplane("YZ").workplane(offset=-J5_FACE - 1)
                      .center(sy * END_BOLT_Y / 2, sz * END_BOLT_Z / 2)
                      .circle(M3_CLEAR / 2).extrude(FORK_BACK + 2))
    return s


def _split_bolts(s, through):
    """4 x M3 across the parting plane, clear of the bay and the bore."""
    import math
    for ang in (35, 145, 215, 325):
        x = (CHEEK_R - 5.0) * math.cos(math.radians(ang))
        y = (CHEEK_R - 5.0) * math.sin(math.radians(ang))
        if through:
            s = s.cut(cq.Workplane("XY").center(x, y).circle(M3_CLEAR / 2)
                      .extrude(60.0).translate((0, 0, Z_BAY)))
        else:
            s = s.cut(cq.Workplane("XY").center(x, y)
                      .circle(M3_INSERT_D / 2).extrude(-M3_INSERT_L)
                      .translate((0, 0, Z_BAY)))
    return s


def j5_p1():
    """Bridge, idle cheek, drive bearing seat, mounting face."""
    s = fork()
    s = s.cut(cq.Workplane("XY").rect(400, 400).extrude(400)
              .translate((0, 0, Z_BAY)))
    return _split_bolts(s, through=False)


def j5_p2():
    """Servo cradle and cover. The servo drops in from the parting face."""
    s = fork()
    s = s.cut(cq.Workplane("XY").rect(400, 400).extrude(-400)
              .translate((0, 0, Z_BAY)))
    s = _split_bolts(s, through=True)
    # two M3 inserts for the strap, across the open face
    for sy in (-1, 1):
        s = s.cut(cq.Workplane("XY").center(BAY_OFF, sy * (BAY_W / 2 + 5.0))
                  .circle(M3_INSERT_D / 2).extrude(M3_INSERT_L)
                  .translate((0, 0, Z_BAY)))
    return s


def strap():
    """Presses the case into the cradle so joint torque is carried by the
    pocket walls in bearing, not by the strap bolts."""
    w = BAY_W + 22.0
    s = cq.Workplane("XY").box(14.0, w, 5.0, centered=(True, True, False))
    s = s.edges("|Z").fillet(2.0)
    for sy in (-1, 1):
        s = s.cut(cq.Workplane("XY").center(0, sy * (BAY_W / 2 + 5.0))
                  .circle(M3_CLEAR / 2).extrude(6.0))
    return s


def main():
    print("NEW J5 wrist fork -- J3 topology, servo along the arm")
    print()
    print("   joint axis   local +Z")
    print("   fork gap     %.2f   blade clearance 1.00/side" % J5_GAP)
    print("   bearing      6706 %.1f x %.1f  seat %.2f..%.2f"
          % (BRG_OD, BRG_W, Z_IN + SEAT_T, Z_SEAT_TOP))
    print("   bay          %.2f x %.2f x %.2f   (L x W-PINCH x T)"
          % (BAY_L, BAY_W, BAY_T))
    print("   parting      z = %.2f" % Z_BAY)
    print("   z_drive      z = %.2f" % Z_DRIVE)
    print()
    ok = True
    for nm, fn in (("J5_p1", j5_p1), ("J5_p2", j5_p2),
                   ("J5_strap", strap)):
        try:
            s = fn()
        except Exception as e:
            print("   %-10s FAILED: %s" % (nm, e))
            ok = False
            continue
        sol = s.val()
        n = len(sol.Solids())
        bb = sol.BoundingBox()
        print("   %-10s %9.1f mm3   solids %d   x %7.2f..%7.2f  z %7.2f..%7.2f"
              % (nm, sol.Volume(), n, bb.xmin, bb.xmax, bb.zmin, bb.zmax))
        if n != 1:
            print("              ^^ NOT A SINGLE SOLID")
            ok = False
        cq.exporters.export(s, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(s, os.path.join(HERE, nm + ".stl"),
                            tolerance=0.01, angularTolerance=0.1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
