#!/usr/bin/env python3
"""J4 drive train, every part against every other, world frame."""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_common as DC        # noqa: E402
import gen_drive_j4 as G         # noqa: E402
import seat_servo as S           # noqa: E402
import asm_xforms as AX          # noqa: E402
from verify_drive import contains  # noqa: E402

RES = []


def rec(label, ok, detail):
    print("   %-56s %s  %s" % (label, "PASS" if ok else "FAIL", detail))
    RES.append((label, ok, detail))


def servo_up(z_cap):
    srv, z_step = S.servo_in_joint_frame()
    srv.apply_translation([0, 0, -(z_step - DC.CAP_FACE_BELOW_STEP)])
    srv.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    srv.apply_translation([0, 0, z_cap])
    return srv


def main():
    print("=" * 80)
    print("J4 DRIVE TRAIN -- world frame, every part against every other")
    print("=" * 80)
    X = AX.xforms()
    fore = {}
    for k in ("link_fore_tongue", "link_fore_groove"):
        m = trimesh.load(os.path.join(HERE, k + ".stl")); m.apply_transform(X[k])
        from verify_drive import attach_occ
        fore[k] = attach_occ(m, os.path.join(HERE, k + ".step"), X[k])
    base = trimesh.load(os.path.join(HERE, "j4_base.stl"))
    cap = trimesh.load(os.path.join(HERE, "j4_cap.stl"))
    hub = trimesh.load(os.path.join(HERE, "j4_hub.stl"))
    srv = servo_up(G.Z_CAP)
    top = srv.bounds[1][2]
    sl = srv.section(plane_origin=[0, 0, top - 0.8], plane_normal=[0, 0, 1])
    v = np.asarray(sl.vertices)
    off = np.hypot((v[:, 0].max() + v[:, 0].min()) / 2, (v[:, 1].max() + v[:, 1].min()) / 2)
    rec("A horn on the J4 axis", off < 0.02, "offset %.4f mm" % off)
    rec("A horn face at Z_HORN", abs(top - G.Z_HORN) < 0.02, "%.3f vs %.3f" % (top, G.Z_HORN))
    Ps = srv.sample(60000)
    c = Ps[contains(base, Ps)]
    ok_ = (np.abs(c[:, 2] - G.Z_CAP) < 0.02) | (np.abs(c[:, 1]) > DC.PINCH / 2 - 0.05) | (np.abs(c[:, 0] - G.CASE_X0) < 0.02)
    rec("B servo vs base: only lips + pinch walls + end stop", (~ok_).sum() == 0,
        "%d contacts, %d elsewhere" % (len(c), int((~ok_).sum())))
    c = Ps[contains(hub, Ps)]
    bad = int((np.abs(c[:, 2] - G.Z_HORN) > 0.02).sum()) if len(c) else 0
    rec("B servo vs hub: only the horn face", bad == 0 and len(c) > 0, "%d contacts, %d elsewhere" % (len(c), bad))
    for nm, m in [("cap", cap)] + list(fore.items()):
        n = int(contains(m, Ps).sum())
        rec("B servo vs %s" % nm, n == 0, "%d / 60000" % n)
    worst = 0
    for dx in np.linspace(48.0, 0.5, 12):
        sv = srv.copy(); sv.apply_translation([dx, 0, 0])
        Q = sv.sample(15000); c = Q[contains(base, Q)]
        if len(c):
            ok_ = (np.abs(c[:, 1]) > DC.PINCH / 2 - 0.05) | (np.abs(c[:, 2] - G.Z_CAP) < 0.02)
            worst = max(worst, int((~ok_).sum()))
    rec("B servo slides in along the channel (no snag)", worst == 0, "worst %d" % worst)
    # base on the forearm face
    Pb = base.sample(80000)
    for k, m in fore.items():
        c = Pb[contains(m, Pb)]
        bad = int((np.abs(c[:, 2] - G.Z_FACE) > 0.02).sum()) if len(c) else 0
        rec("C base vs %s: contact only on the face" % k, bad == 0, "%d contacts, %d off the face" % (len(c), bad))
    ok = True
    for (x, y) in G.BOLTS:
        P = np.array([[x, y, z] for z in (G.Z_FACE - 1.0, G.Z_FACE - 4.0, G.Z_FACE - 7.0)])
        solid = any(m.contains(P).any() for m in fore.values())
        ok &= not solid
    rec("C base bolt holes over the forearm inserts", ok, "4 of 4")
    Pc = cap.sample(60000)
    c = Pc[contains(base, Pc)]
    bad = int((np.abs(c[:, 2] - G.Z_LIP_TOP) > 0.02).sum()) if len(c) else 0
    rec("C cap vs base: contact only on the wall tops", bad == 0, "%d contacts, %d elsewhere" % (len(c), bad))
    # hub runs free through a full turn
    worst = 0
    for a in np.linspace(0, 360, 13)[:-1]:
        h2 = hub.copy(); h2.apply_transform(trimesh.transformations.rotation_matrix(np.radians(a), [0, 0, 1]))
        Q = h2.sample(20000)
        for m in [base, cap] + list(fore.values()):
            worst = max(worst, int(contains(m, Q).sum()))
    rec("D hub turns a full revolution clear of base/cap/forearm", worst == 0, "worst %d points" % worst)
    rec("D hub flange clears the cap top", G.Z_FLANGE_BOT - G.Z_CAP_TOP >= 0.4,
        "%.2f mm" % (G.Z_FLANGE_BOT - G.Z_CAP_TOP))
    rec("D collar on the inner race, inside the outer-race shoulder", G.COLLAR_D / 2 < G.SHOULDER_D / 2, "collar r %.1f < shoulder r %.1f" % (G.COLLAR_D / 2, G.SHOULDER_D / 2))
    rec("E forearm bolt heads (-17,+-7) clear the end wall", -17.0 + 2.75 <= G.CASE_X0 - G.END_T - 0.2,
        "head edge x %.2f, wall face %.2f" % (-17.0 + 2.75, G.CASE_X0 - G.END_T))
    fails = [r for r in RES if not r[1]]
    print("\nFAILURES: %d" % len(fails))
    for f in fails:
        print("  - %s | %s" % (f[0], f[2]))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
