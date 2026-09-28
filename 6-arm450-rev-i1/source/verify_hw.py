#!/usr/bin/env python3
"""Bearings and bolts as REAL solids, against every part.

The drive-train checks modelled servos and printed parts only. With no
bearings and no bolts in the model, a cap bolt ran straight through the J4
bearing and the fork split-bolt inserts broke into the bearing pockets
(two of those bolts also ran through the servo bay) -- all invisible.
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_common as DC          # noqa: E402
import verify_drive as VD          # noqa: E402
from verify_drive import contains  # noqa: E402
from verify_j4 import servo_up     # noqa: E402
import gen_drive_j4 as J4          # noqa: E402
import gen_wrist as W              # noqa: E402

RES = []


def rec(label, ok, detail):
    print("   %-60s %s  %s" % (label, "PASS" if ok else "FAIL", detail))
    RES.append((label, ok, detail))


def bearing(od, w, z0, idd=30.0):
    # 256 sections: at the default resolution the bore's flat facets sit at
    # r = 14.93, inside a 29.95 shaft, and every bore point read as a clash
    b = trimesh.creation.annulus(r_min=idd / 2, r_max=od / 2, height=w, sections=256)
    b.apply_translation([0, 0, z0 + w / 2]); return b


def bolt(x, y, z0, z1, d=3.0, head=True, head_up=True):
    c = trimesh.creation.cylinder(radius=d / 2, height=z1 - z0)
    c.apply_translation([x, y, (z0 + z1) / 2])
    if head:
        zh = z1 if head_up else z0 - 3.0
        h = trimesh.creation.cylinder(radius=2.75, height=3.0); h.apply_translation([x, y, zh + 1.5])
        c = trimesh.util.concatenate([c, h])
    return c


def seated(b, part, od, faces):
    """bearing vs the part that holds it: contact only on the OD or a seat face."""
    P = b.sample(30000); c = P[contains(part, P)]
    if not len(c):
        return 0, 0
    r = np.hypot(c[:, 0], c[:, 1])
    ok = (r > od / 2 - 0.06) | np.any([np.abs(c[:, 2] - f) < 0.06 for f in faces], axis=0)
    return len(c), int((~ok).sum())


def fork(jn, p1, p2, sh, srv, od, w, z_in, seat, P, z_drive, others):
    print("\n%s  (joint frame, axis Z)" % jn)
    zd0 = z_in + seat; zi0 = -(z_in + seat + w)
    bd, bi = bearing(od, w, zd0), bearing(od, w, zi0)
    for nm, b, faces in (("drive", bd, (zd0, zd0 + w)), ("idle", bi, (zi0, zi0 + w))):
        n, bad = seated(b, p1, od, faces)
        rec("%s %s bearing seats only on its OD / faces in p1" % (jn, nm), bad == 0, "%d contacts, %d elsewhere" % (n, bad))
        for onm, m in [("p2", p2), ("servo", srv), ("shaft", sh)] + list(others.items()):
            k = int(contains(m, b.sample(20000)).sum())
            rec("%s %s bearing vs %s" % (jn, nm, onm), k == 0, "%d" % k)
    for (x, y) in DC.SPLIT_BOLTS:
        bl = bolt(x, y, P - DC.M3_INSERT_L + 0.5, z_drive)     # screw shorter than its insert
        Q = bl.sample(8000)
        hits = {nm: int(contains(m, Q).sum()) for nm, m in [("servo", srv), ("drive brg", bd), ("idle brg", bi), ("shaft", sh), ("p1", p1), ("p2", p2)] + list(others.items())}
        bad = {k: v for k, v in hits.items() if v}
        rec("%s split bolt (%+.0f,%+.0f) clear of everything" % (jn, x, y), not bad, str(bad) if bad else "clear")


def roll(jn, base, cap, hub, srv, z_lip_top, z_cap_top, bolts, others):
    print("\n%s  (roll frame, axis Z)" % jn)
    b = bearing(J4.BRG_OD, J4.BRG_W, z_lip_top)
    n, bad = seated(b, cap, J4.BRG_OD, (z_lip_top, z_lip_top + J4.BRG_W))
    rec("%s bearing seats only on its OD / faces in the cap" % jn, bad == 0, "%d contacts, %d elsewhere" % (n, bad))
    for onm, m, face in (("base", base, z_lip_top), ("hub", hub, z_lip_top + J4.BRG_W)):
        P = b.sample(20000); c = P[contains(m, P)]
        badc = int((np.abs(c[:, 2] - face) > 0.06).sum()) if len(c) else 0
        rec("%s bearing vs %s: only the seated face z=%.2f" % (jn, onm, face), badc == 0, "%d contacts, %d elsewhere" % (len(c), badc))
    k = int(contains(srv, b.sample(20000)).sum())
    rec("%s bearing vs servo" % jn, k == 0, "%d" % k)
    for (x, y) in bolts:
        z_seat = z_cap_top - J4.CB_HEAD_T
        bl = bolt(x, y, z_lip_top - J4.M3_INS_L + 0.5, z_seat)     # head in its counterbore
        Q = bl.sample(8000)
        hits = {}
        for nm, m in [("servo", srv), ("bearing", b), ("hub", hub), ("base", base), ("cap", cap)] + list(others.items()):
            c = Q[contains(m, Q)]
            if nm == "cap" and len(c):
                c = c[np.abs(c[:, 2] - z_seat) > 0.06]     # the head's seat is a designed face
            hits[nm] = len(c)
        bad = {k: v for k, v in hits.items() if v}
        rec("%s cap bolt (%+.1f,%+.1f) clear of everything" % (jn, x, y), not bad, str(bad) if bad else "clear")


def L(nm, T=None):
    m = trimesh.load(os.path.join(HERE, nm + ".stl"))
    if T is not None:
        m.apply_transform(T)
    return m


if __name__ == "__main__":
    print("=" * 90); print("BEARINGS + BOLTS as solids, against every part"); print("=" * 90)
    import gen_drive_j3 as G3
    fork("J3", L("J3_p1"), L("J3_p2"), L("J3_shaft"), VD.seated_servo(G3.P), 42.0, 7.0, 15.5, 2.0, G3.P, G3.Z_DRIVE, {})
    body = L("j6_body"); sa = L("J5_spacer")
    sb = sa.copy(); sb.apply_translation([0, 0, -(2 * W.BLADE_HALF + W.SPACER_T)])
    fork("J5", L("J5_p1"), L("J5_p2"), L("J5_shaft"), VD.seated_servo(W.P5), 37.0, 4.0, W.J5.Z_IN, W.J5.SEAT_T, W.P5, W.J5.Z_DRIVE,
         {"j6_body": body, "spacer_A": sa, "spacer_B": sb})
    # J2: turret -> joint frame (bearings only; its cover bolts sit at r 43, far outside)
    TU2J = trimesh.transformations.rotation_matrix(np.radians(-90), [1, 0, 0]); TU2J[:3, 3] = TU2J[:3, :3] @ np.array([0, 0, -40.0])
    t1, t2, s2 = L("J2_turret_p1", TU2J), L("J2_turret_p2", TU2J), L("J2_shaft", TU2J)
    srv2 = VD.seated_servo(28.5)
    print("\nJ2  (joint frame, axis Z)")
    for nm, z0 in (("drive", 17.5), ("idle", -24.5)):
        b = bearing(42.0, 7.0, z0)
        n, bad = seated(b, t1, 42.0, (z0, z0 + 7.0))
        rec("J2 %s bearing seats only on its OD / faces" % nm, bad == 0, "%d contacts, %d elsewhere" % (n, bad))
        for onm, m in (("turret_p2", t2), ("servo", srv2), ("shaft", s2)):
            k = int(contains(m, b.sample(20000)).sum()); rec("J2 %s bearing vs %s" % (nm, onm), k == 0, "%d" % k)
    roll("J4", L("j4_base"), L("j4_cap"), L("j4_hub"), servo_up(J4.Z_CAP), J4.Z_LIP_TOP, J4.Z_CAP_TOP, J4.CAP_BOLTS, {})
    J52ABC = np.linalg.inv(trimesh.transformations.rotation_matrix(np.radians(120), [1, 1, 1]))
    roll("J6", L("j6_body", J52ABC), L("j6_cap", J52ABC), L("j6_flange", J52ABC), servo_up(W.X6_CAP),
         W.X6_LIP_TOP, W.X6_CAP_TOP, W.CAP6_BOLTS, {})
    fails = [r for r in RES if not r[1]]
    print("\nFAILURES: %d" % len(fails))
    for f in fails:
        print("  - %s | %s" % (f[0], f[2]))
