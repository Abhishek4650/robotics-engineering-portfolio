#!/usr/bin/env python3
"""
ARM-450 rev I -- gravity springs at J2 and J3 (user's choice: simple springs,
no payload). WORLD frame, arm straight up.

Each joint has two extension springs, one each side (|y| = PIN_Y), so the link
is not twisted. A spring runs from a pin a above the joint on the FIXED side
to a pin b along the MOVING link. With force proportional to length (F = k L)
it gives exactly K sin(angle): the gravity law. Specified by two force points,
lengths PIN CENTRE to PIN CENTRE (inside the hooks on O3 pins = + 3.0 mm):

  J2 spring x2:  7.4 N at 33.0 mm, 12.4 N at 55.2 mm (0.224 N/mm)
  J3 spring x2:  2.2 N at 40.0 mm,  5.0 N at 88.4 mm (0.056 N/mm)
(the old 9.56 N / 35.0 mm figures were for a2 = 30, before the anchors were
raised; superseded)

Pins are M3 shoulder screws in heat-set inserts facing outward (+-y).
The collars clamp the links, so the already-printed upper links need no holes.
"""
import numpy as np
import cadquery as cq

PIN_Y = 24.5             # lug / post outer face; spring loop sits at ~26.5
LUG_X = 5.0
INS_D, INS_L = 4.1, 6.5
J2_AXIS_Z, J3_AXIS_Z = 90.0, 209.0
# Raised after the posed spring sweep: at a2 = 30 the J2 spring's lower end
# grazed the turret's servo cover, and at a3 = 41 the J3 spring swung down onto
# the J3 servo housing at q3 = +72. b2 = 68 keeps the collar 2 mm under the fork.
A2, B2 = 35.0, 68.0      # J2: pin above the axis on the turret, pin along the upper link
A3, B3 = 50.0, 90.0      # J3: pin above the axis on the fork,   pin along the forearm
SPRING_Y = 30.0          # spring plane: a 5-mm spacer on each hook screw puts the
                         # loop here, so the Ø9 spring body clears its own anchor
LINK_HALF_X, LINK_HALF_Y = 25.0, 14.5
COLLAR_H, COLLAR_BACK, COLLAR_ARM = 10.0, 4.0, 7.0
CLR = 0.2
SPLIT_GAP = 0.5


def _box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY").center((x0 + x1) / 2, (y0 + y1) / 2)
            .rect(x1 - x0, y1 - y0).extrude(z1 - z0).translate((0, 0, z0)))


# rev I.1 (2026-09-27, user's slicer view of J3_p1: "joints at indicated areas
# need rectification"). The J3 lugs stood on the ROUND tops of the fork cheeks
# with their base at the arc's apex: joined by a 0.05-0.1 mm sliver (2.2 / 2.6
# mm3 of overlap), their corners 0.4 mm in the air, sharp notches both sides
# (verify_union_joints: joined over 0.47 of their own section). Now a lug on a
# round top is SUNK into the cheek -- EMBED below the arc at its edges, never
# into the bearing pocket -- and blended into the arc by R FILLET_R concave
# webs, drawn in the cheek's own plane (they print in-plane).
EMBED, FILLET_R = 1.5, 3.0


def _cyl_y(x, z, r):
    """cylinder along y through everything, centre (x, z)."""
    return cq.Solid.makeCylinder(r, 400.0, cq.Vector(x, -200.0, z), cq.Vector(0, 1, 0))


def lug(sy, z_base, z_pin, z_top=None, cheek=None):
    """Anchor lug on the side sy (+1/-1), from z_base up past the pin, with an
    outward M3 insert at z_pin. cheek = (zc, R, z_floor): the lug stands on a
    round cheek top (arc in the XZ plane, centre x = 0, z = zc, radius R);
    its base is then sunk EMBED below the arc at the lug's edges (not below
    z_floor) and R FILLET_R webs blend both sides into the arc."""
    z_top = z_top if z_top is not None else z_pin + 4.0
    y0, y1 = PIN_Y - 7.5, PIN_Y
    webs = []
    if cheek is not None:
        zc, R, z_floor = cheek
        z_edge = zc + np.sqrt(R ** 2 - LUG_X ** 2)          # arc under the lug's edges
        z_base = max(z_edge - EMBED, z_floor)
        assert z_base <= z_edge - 1.0, "lug cannot be sunk 1 mm without reaching z_floor"
        rf = FILLET_R
        zf = zc + np.sqrt((R + rf) ** 2 - (LUG_X + rf) ** 2)   # fillet centre height
        xt = R * (LUG_X + rf) / (R + rf)                       # where the fillet meets the arc
        for sx in (-1, 1):
            w = _box(*sorted((sx * LUG_X, sx * xt)), y0, y1, z_edge - 0.5, zf)
            w = w.cut(cq.Workplane().add(_cyl_y(sx * (LUG_X + rf), zf, rf)))
            w = w.cut(cq.Workplane().add(_cyl_y(0.0, zc, R)))
            webs.append(w)
    # built on +y, then mirrored whole. The old code translated the -y pocket
    # to y -25..-32 and THEN mirrored it to +25..+32: the -y lugs (turret p1,
    # J3 p1) had no insert pocket at all (section check: the -y pin screw
    # sat 3 mm inside solid J3_p1).
    s = _box(-LUG_X, LUG_X, y0, y1, z_base, z_top)
    for w in webs:
        s = s.union(w)
    ins = (cq.Workplane("XZ").center(0, z_pin).circle(INS_D / 2).extrude(INS_L + 0.5)
           .translate((0, PIN_Y + 0.5, 0)))
    s = s.cut(ins)
    return s.mirror("XZ") if sy < 0 else s


def j2_lugs():
    z_pin = J2_AXIS_Z + A2
    return lug(+1, 116.9, z_pin).union(lug(-1, 116.9, z_pin))


# J3 fork cheek tops (world XZ plane, measured on the fork_pro geometry the
# J3 generator builds, asserted in gen_drive_j3.p1): +y = the drive cheek's
# racetrack end, arc centre z 221.91; -y = the idle cheek, centre on the J3
# axis. Both R 25. Floor = bearing pocket top (r 21.5 on the axis) + 1.0.
J3_CHEEK = {+1: (J3_AXIS_Z + 12.91, 25.0, J3_AXIS_Z + 21.5 + 1.0),
            -1: (J3_AXIS_Z, 25.0, J3_AXIS_Z + 21.5 + 1.0)}


def j3_lugs():
    z_pin = J3_AXIS_Z + A3
    return (lug(+1, None, z_pin, cheek=J3_CHEEK[+1])
            .union(lug(-1, None, z_pin, cheek=J3_CHEEK[-1])))       # posts up to z_pin + 4


def collar_half(sy, z_pin):
    """One U-half of a clamp collar around a 50 x 29 link, centred on z_pin."""
    z0, z1 = z_pin - COLLAR_H / 2, z_pin + COLLAR_H / 2
    yi = LINK_HALF_Y + CLR
    yb = yi + COLLAR_BACK
    xi = LINK_HALF_X + CLR
    xa = xi + COLLAR_ARM
    ys = sorted((sy * SPLIT_GAP / 2, sy * yb))
    s = _box(-xa, xa, *sorted((sy * yi, sy * yb)), z0, z1)                 # back plate
    for sx in (-1, 1):
        s = s.union(_box(*sorted((sx * xi, sx * xa)), *ys, z0, z1))       # arms
        # clamp bolt along y through both arms
        s = s.cut(cq.Workplane("XZ").center(sx * (xi + COLLAR_ARM / 2), z_pin)
                  .circle(3.4 / 2).extrude(-60).translate((0, -30, 0)))
    # spring post with the outward insert
    s = s.union(lug(sy, z0, z_pin, z1))
    return s


def springs_world(q2_deg=0.0, q3_deg=0.0):
    """Spring centre-lines as (p0, p1) pairs, for the clash sweep."""
    out = []
    t2, t3 = np.radians(q2_deg), np.radians(q2_deg + q3_deg)
    y = SPRING_Y
    for sy in (-1, 1):
        a = np.array([0, sy * y, J2_AXIS_Z + A2])
        b = np.array([B2 * np.sin(t2), sy * y, J2_AXIS_Z + B2 * np.cos(t2)])
        out.append(("J2", a, b))
        j3 = np.array([119.0 * np.sin(t2), 0, J2_AXIS_Z + 119.0 * np.cos(t2)])
        a3 = j3 + np.array([A3 * np.sin(t2), sy * y, A3 * np.cos(t2)])
        b3 = j3 + np.array([B3 * np.sin(t3), sy * y, B3 * np.cos(t3)])
        out.append(("J3", a3, b3))
    return out


if __name__ == "__main__":
    import os
    HERE = os.path.dirname(os.path.abspath(__file__))
    for nm, fn in (("collar_upper", lambda: collar_half(+1, J2_AXIS_Z + B2)),
                   ("collar_fore", lambda: collar_half(+1, J3_AXIS_Z + B3))):
        p = fn()
        n = len(p.val().Solids())
        print("%-13s %8.1f mm3  solids %d  (print 2: one each side)" % (nm, p.val().Volume(), n))
        cq.exporters.export(p, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(p, os.path.join(HERE, nm + ".stl"), tolerance=0.01, angularTolerance=0.1)
    for nm, fn in (("j2_lugs", j2_lugs), ("j3_lugs", j3_lugs)):
        print("%-13s solids %d" % (nm, len(fn().val().Solids())))
