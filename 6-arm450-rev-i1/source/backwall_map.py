#!/usr/bin/env python3
"""Back-wall map of each fork p2 vs the SEATED servo's back face (joint
frame). For every (x, y) over the bay: servo back-face height, p2 wall height
above P, and the axial gap. Answers: is the servo's back restrained, where is
the wall open, and is anything touching."""
import os, sys
import numpy as np
import trimesh
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_common as DC
import verify_drive as VD
import gen_drive_j3 as G3
import gen_wrist as W


def first_hit(m, xs, ys, z_from, direction):
    """Ray-cast (memory-safe): first surface hit from z_from along +-Z."""
    O = np.array([[x, y, z_from] for y in ys for x in xs], float)
    D = np.tile([0, 0, direction], (len(O), 1)).astype(float)
    loc, idx, _ = m.ray.intersects_location(O, D, multiple_hits=True)
    out = np.full(len(O), np.nan)
    for p, i in zip(loc, idx):
        d = (p[2] - z_from) * direction
        if d > 1e-6 and (np.isnan(out[i]) or d < abs(out[i] - z_from)):
            out[i] = p[2]
    return out.reshape(len(ys), len(xs))


def run(nm, p2, P):
    srv = VD.seated_servo(P)
    xs = np.arange(DC.SERVO_OFF - 22, DC.SERVO_OFF + 22.1, 2.0)
    ys = np.arange(-11, 11.1, 2.0)
    sb = first_hit(srv, xs, ys, P + 45, -1)       # servo back face, seen from above
    wl = first_hit(p2, xs, ys, P + 0.05, +1)      # p2 wall, seen from inside the bay
    print("\n%s  (P %.3f; servo cap face at P; want wall at P + %.3f; gap = wall - servo back)" % (nm, P, DC.BAY_T))
    print("   y\\x " + "".join("%6.0f" % x for x in xs))
    gmin = 99
    for j, y in enumerate(ys):
        s = []
        for i in range(len(xs)):
            if np.isnan(wl[j, i]):
                s.append("  OPEN" if not np.isnan(sb[j, i]) else "     .")
            elif np.isnan(sb[j, i]):
                s.append("  %4.1f" % (wl[j, i] - P))
            else:
                g = wl[j, i] - sb[j, i]; gmin = min(gmin, g)
                s.append(" g%4.2f" % g)
        print("  %4.0f " % y + "".join(s))
    print("   min axial gap servo back -> wall: %.2f mm" % gmin)


TU2J = trimesh.transformations.rotation_matrix(np.radians(-90), [1, 0, 0]); TU2J[:3, 3] = TU2J[:3, :3] @ np.array([0, 0, -40.0])

if __name__ == "__main__" and "--walls" not in sys.argv:
    import gen_drive_j2 as G2
    m = trimesh.load(os.path.join(HERE, "J2_turret_p2.stl")); m.apply_transform(TU2J)
    run("J2_p2", m, G2.P)
    run("J3_p2", trimesh.load(os.path.join(HERE, "J3_p2.stl")), G3.P)
    run("J5_p2", trimesh.load(os.path.join(HERE, "J5_p2.stl")), W.P5)


def side_walls(nm, p2, P):
    """Pinch walls: for each (x, depth) over the bay, the wall thickness on
    the +y and -y side (ray from the bay centre outward). 0 = no wall."""
    xs = np.arange(DC.SERVO_OFF - 22, DC.SERVO_OFF + 22.1, 2.0)
    zs = np.arange(P + 1.0, P + DC.BAY_T, 3.0)
    print("\n%s pinch walls: thickness of wall contact on +y | -y (mm), rows = depth above P" % nm)
    print("   dz\\x " + "".join("%8.0f" % x for x in xs))
    tot = cov = 0
    for z in zs:
        s = []
        for x in xs:
            th = []
            for sy in (1, -1):
                O = np.array([[x, 0.0, z]]); D = np.array([[0, sy, 0.0]])
                loc, idx, _ = p2.ray.intersects_location(O, D, multiple_hits=True)
                ds = sorted(abs(p[1]) for p in loc)
                if len(ds) >= 1 and abs(ds[0] - DC.PINCH / 2) < 0.3:
                    th.append(ds[1] - ds[0] if len(ds) >= 2 else 99)
                else:
                    th.append(0.0)
            tot += 2; cov += sum(t > 0.8 for t in th)
            s.append(" %3.1f|%3.1f" % (min(th[0], 9.9), min(th[1], 9.9)))
        print("  %5.1f " % (z - P) + "".join(s))
    print("   pinch-wall coverage over the bay sides: %.0f %%" % (100.0 * cov / tot))


if __name__ == "__main__" and "--walls" in sys.argv:
    import gen_drive_j2 as G2
    m = trimesh.load(os.path.join(HERE, "J2_turret_p2.stl")); m.apply_transform(TU2J)
    side_walls("J2_p2", m, G2.P)
    side_walls("J3_p2", trimesh.load(os.path.join(HERE, "J3_p2.stl")), G3.P)
