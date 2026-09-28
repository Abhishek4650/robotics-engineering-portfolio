#!/usr/bin/env python3
"""Wrist drive trains (J5, J6): every part against every other."""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_common as DC        # noqa: E402
import gen_wrist as W            # noqa: E402
import gen_drive_j4 as J4        # noqa: E402
import verify_drive as VD        # noqa: E402
from verify_drive import contains  # noqa: E402
from verify_j4 import servo_up   # noqa: E402

RES = []


def rec(label, ok, detail):
    print("   %-58s %s  %s" % (label, "PASS" if ok else "FAIL", detail))
    RES.append((label, ok, detail))


def L(nm):
    return trimesh.load(os.path.join(HERE, nm + ".stl"))


FORK_R = np.array([[0., 1., 0.], [0., 0., 1.], [1., 0., 0.]])
J5W = np.eye(4); J5W[:3, :3] = FORK_R; J5W[:3, 3] = [0, 0, W.Z_J5_WORLD]   # J5 local -> world
W2J5 = np.linalg.inv(J5W)
ABC2J5 = trimesh.transformations.rotation_matrix(np.radians(120), [1, 1, 1])
J52ABC = np.linalg.inv(ABC2J5)


def main():
    p1, p2, sh, body, cap6, fl6 = (L(n) for n in ("J5_p1", "J5_p2", "J5_shaft", "j6_body", "j6_cap", "j6_flange"))
    spA = L("J5_spacer")
    spB = spA.copy(); spB.apply_translation([0, 0, -(2 * W.BLADE_HALF + W.SPACER_T)])
    hub4 = L("j4_hub"); hub4.apply_transform(W2J5)
    cap4 = L("j4_cap"); cap4.apply_transform(W2J5)

    print("=" * 84); print("J5 DRIVE TRAIN -- J5 fork frame"); print("=" * 84)
    nb = {"link_j6_body (D-bore grip)": body, "spacer_A": spA, "spacer_B": spB,
          "j6_cap": cap6, "j6_flange": fl6, "j4_hub": hub4, "j4_cap": cap4}
    VD.RES.clear()
    srv5 = VD.verify("J5", p1, p2, sh, W.P5, nb, W.Z5_IDLE_END)
    RES.extend(VD.RES)
    # blade + spacers vs the fork, and the blade's J5 swing
    worst = 0
    for a in np.linspace(-93, 93, 13):
        R = trimesh.transformations.rotation_matrix(np.radians(a), [0, 0, 1])
        for m in (body, cap6, fl6, spA, spB):
            m2 = m.copy(); m2.apply_transform(R); Q = m2.sample(12000)
            for f in (p1, p2, srv5, hub4, cap4):
                worst = max(worst, int(contains(f, Q).sum()))
    rec("J5 blade + J6 stack swings +-93 deg clear of fork/servo/J4", worst == 0, "worst %d points" % worst)
    # D-key: turn the blade 2 deg on the shaft, it must bear on the flat
    b2 = body.copy(); b2.apply_transform(trimesh.transformations.rotation_matrix(np.radians(2), [0, 0, 1]))
    n = int(contains(b2, sh.sample(60000)).sum())
    rec("J5 blade D-bore bears on the shaft flat at 2 deg", n > 0, "%d points" % n)
    # spacers on the inner races: faces at |z| = Z_IN + SEAT_T, blade faces at +-BLADE_HALF
    # measured on the placed parts: spacer A's faces against the blade face and the inner ring
    zA = spA.bounds[:, 2]
    rec("J5 spacers close the stack: blade face -> spacer -> inner ring, 0 play",
        abs(zA[0] - W.BLADE_HALF) < 1e-3 and abs(zA[1] - (W.J5.Z_IN + W.J5.SEAT_T)) < 1e-3,
        "spacer z %.3f..%.3f, blade face %.3f, inner ring %.3f" % (zA[0], zA[1], W.BLADE_HALF, W.J5.Z_IN + W.J5.SEAT_T))
    rec("J5 spacer OD clears the cheek seat bore", W.SPACER_OD / 2 < (W.J5.BRG_OD - 4) / 2,
        "r %.1f < r %.1f" % (W.SPACER_OD / 2, (W.J5.BRG_OD - 4) / 2))
    # fork mounting face on the J4 hub top
    c = p1.sample(80000); c = c[contains(hub4, c)]
    bad = int((np.abs(c[:, 0] + W.J5.J5_FACE) > 0.02).sum()) if len(c) else 0
    rec("J5 fork sits on the J4 hub top face only", bad == 0, "%d contacts, %d off the face" % (len(c), bad))
    ok = True
    for (x, y) in J4.BOLTS:                         # world (x, y) -> J5 local (y, z)
        P = np.array([[-W.J5.J5_FACE - d, x, y] for d in (1.0, 4.0, 7.0)])
        ok &= not hub4.contains(P).any()
    rec("J5 fork bolts land on the J4 hub inserts", ok, "4 of 4")

    print("\n" + "=" * 84); print("J6 DRIVE TRAIN -- J6 frame (a channel, b pinch, c output)"); print("=" * 84)
    def to_abc(m):
        m = m.copy(); m.apply_transform(J52ABC); return m
    B, C, F = to_abc(body), to_abc(cap6), to_abc(fl6)
    others = {"J5_shaft": to_abc(sh), "spacer_A": to_abc(spA), "spacer_B": to_abc(spB),
              "J5_p1": to_abc(p1), "J5_p2": to_abc(p2)}
    srv = servo_up(W.X6_CAP)
    top = srv.bounds[1][2]
    sl = srv.section(plane_origin=[0, 0, top - 0.8], plane_normal=[0, 0, 1]); v = np.asarray(sl.vertices)
    off = np.hypot((v[:, 0].max() + v[:, 0].min()) / 2, (v[:, 1].max() + v[:, 1].min()) / 2)
    rec("J6 horn on the J6 axis", off < 0.02, "offset %.4f" % off)
    rec("J6 horn face at X6_HORN", abs(top - W.X6_HORN) < 0.02, "%.3f vs %.3f" % (top, W.X6_HORN))
    Ps = srv.sample(60000)
    c = Ps[contains(B, Ps)]
    ok_ = (np.abs(c[:, 2] - W.X6_CAP) < 0.02) | (np.abs(c[:, 1]) > DC.PINCH / 2 - 0.05) | (np.abs(c[:, 0] - W.A0) < 0.02)
    rec("J6 servo vs body: only lips + pinch walls + end stop", (~ok_).sum() == 0, "%d contacts, %d elsewhere" % (len(c), int((~ok_).sum())))
    c = Ps[contains(F, Ps)]
    bad = int((np.abs(c[:, 2] - W.X6_HORN) > 0.02).sum()) if len(c) else 0
    rec("J6 servo vs flange: only the horn face", bad == 0 and len(c) > 0, "%d contacts, %d elsewhere" % (len(c), bad))
    for nm, m in [("j6_cap", C)] + list(others.items()):
        n = int(contains(m, Ps).sum())
        rec("J6 servo vs %s" % nm, n == 0, "%d / 60000" % n)
    worst = 0
    for dx in np.linspace(48.0, 0.5, 12):
        sv = srv.copy(); sv.apply_translation([dx, 0, 0]); Q = sv.sample(15000); c = Q[contains(B, Q)]
        if len(c):
            ok_ = (np.abs(c[:, 1]) > DC.PINCH / 2 - 0.05) | (np.abs(c[:, 2] - W.X6_CAP) < 0.02)
            worst = max(worst, int((~ok_).sum()))
    rec("J6 servo slides into the body channel (no snag)", worst == 0, "worst %d" % worst)
    c = C.sample(60000); c = c[contains(B, c)]
    bad = int((np.abs(c[:, 2] - W.X6_LIP_TOP) > 0.02).sum()) if len(c) else 0
    rec("J6 cap vs body: only on the lip/boss tops", bad == 0, "%d contacts, %d elsewhere" % (len(c), bad))
    worst = 0
    for a in np.linspace(0, 360, 13)[:-1]:
        f2 = F.copy(); f2.apply_transform(trimesh.transformations.rotation_matrix(np.radians(a), [0, 0, 1]))
        Q = f2.sample(20000)
        for m in (B, C):
            worst = max(worst, int(contains(m, Q).sum()))
    rec("J6 flange turns a full revolution clear of body/cap", worst == 0, "worst %d" % worst)
    rec("J6 flange clears the cap top", W.X6_FLANGE_BOT - W.X6_CAP_TOP >= 0.4, "%.2f mm" % (W.X6_FLANGE_BOT - W.X6_CAP_TOP))
    # plug room behind the J6 servo
    rec("J6 plug room between hub and case back", W.X6_TIP - W.HUB_R >= 10.0, "%.1f mm" % (W.X6_TIP - W.HUB_R))
    fails = [r for r in RES if not r[1]]
    print("\nFAILURES: %d" % len(fails))
    for f in fails:
        print("  - %s | %s" % (f[0], f[2]))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
