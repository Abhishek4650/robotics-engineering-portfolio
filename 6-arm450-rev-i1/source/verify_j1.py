#!/usr/bin/env python3
"""J1 drive train, every part against every other, world frame."""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_common as DC        # noqa: E402
import gen_drive_j1 as G         # noqa: E402
import seat_servo as S           # noqa: E402
from verify_drive import contains  # noqa: E402

RES = []


def rec(label, ok, detail):
    print("   %-54s %s  %s" % (label, "PASS" if ok else "FAIL", detail))
    RES.append((label, ok, detail))


def load(f, dz=0.0):
    m = trimesh.load(os.path.join(HERE, f))
    if dz:
        m.apply_translation([0, 0, dz])
    return m


def servo_world():
    srv, z_step = S.servo_in_joint_frame()                  # output -Z
    srv.apply_translation([0, 0, -(z_step - DC.CAP_FACE_BELOW_STEP)])  # cap face at 0
    srv.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))  # output +Z
    srv.apply_translation([0, 0, G.Z_CAP])
    return srv


def main():
    print("=" * 78)
    print("J1 DRIVE TRAIN -- world frame, every part against every other")
    print("=" * 78)
    base = trimesh.load(os.path.join(HERE, "base.stl"))      # rev I base
    collar = load("spigot_collar.stl")
    turret = load("J2_turret_p1.stl", 50.0)
    hub, mount = load("j1_hub.stl"), load("j1_mount.stl")
    srv = servo_world()
    bb = srv.bounds
    top = bb[1][2]
    sl = srv.section(plane_origin=[0, 0, top - 0.8], plane_normal=[0, 0, 1])
    v = np.asarray(sl.vertices)
    off = np.hypot((v[:, 0].max() + v[:, 0].min()) / 2, (v[:, 1].max() + v[:, 1].min()) / 2)
    rec("A horn on the J1 axis", off < 0.02, "offset %.4f mm" % off)
    rec("A horn face at Z_HORN", abs(top - G.Z_HORN) < 0.02, "horn face %.3f, want %.3f" % (top, G.Z_HORN))
    Ps = srv.sample(60000)
    # mount: contacts allowed on the cap plane or on the pinch walls only
    ins = contains(mount, Ps)
    c = Ps[ins]
    on_plane = np.abs(c[:, 2] - G.Z_CAP) < 0.02
    on_pinch = np.abs(c[:, 1]) > DC.PINCH / 2 - 0.05
    on_end = np.abs(c[:, 0] - G.CASE_X0) < 0.02
    bad = int((~(on_plane | on_pinch | on_end)).sum())
    pen = (np.abs(c[on_pinch][:, 1]).max() - DC.PINCH / 2) if on_pinch.any() else 0
    rec("B servo vs mount: only lips + pinch walls + end stop", bad == 0,
        "%d contacts (%d lip, %d pinch %.3f/side, %d end), %d elsewhere"
        % (len(c), int(on_plane.sum()), int(on_pinch.sum()), pen, int(on_end.sum()), bad))
    # pedestals sit CLR under the case back: nothing touches them at rest
    ped = Ps[(Ps[:, 2] < G.Z_BACK_FULL + 0.5)]
    n = int(contains(mount, ped).sum())
    rec("B case back clears the pedestals (0.4 gap)", n == 0, "%d points" % n)
    ins = contains(hub, Ps)
    c = Ps[ins]
    bad = int((np.abs(c[:, 2] - G.Z_HORN) > 0.02).sum()) if len(c) else 0
    rec("B servo vs hub: only the horn face (bolted joint)", bad == 0 and len(c) > 0,
        "%d contacts on z %.3f, %d elsewhere" % (len(c), G.Z_HORN, bad))
    for nm, m in (("turret", turret), ("base", base), ("collar", collar)):
        n = int(contains(m, Ps).sum())
        rec("B servo vs %s" % nm, n == 0, "%d / 60000" % n)
    # INSERTION: slide the servo in along -X from outside the channel.
    # Allowed contact on the way: pinch walls and the lip plane only.
    worst = 0
    for dx in np.linspace(48.0, 0.5, 12):
        sv = srv.copy()
        sv.apply_translation([dx, 0, 0])
        Q = sv.sample(15000)
        c = Q[contains(mount, Q)]
        if len(c):
            ok = (np.abs(c[:, 1]) > DC.PINCH / 2 - 0.05) | (np.abs(c[:, 2] - G.Z_CAP) < 0.02)
            worst = max(worst, int((~ok).sum()))
    rec("B servo slides in along the channel (no snag)", worst == 0,
        "worst %d off-wall points over 12 stations" % worst)
    # hub vs everything
    Ph = hub.sample(60000)
    for nm, m in (("turret", turret), ("mount", mount), ("base", base), ("collar", collar)):
        n = int(contains(m, Ph).sum())
        rec("C hub vs %s" % nm, n == 0, "%d / 60000" % n)
    # the key transmits torque: turn the hub a little, it must hit the D
    for deg in (2.0, 4.0):
        h2 = hub.copy()
        h2.apply_transform(trimesh.transformations.rotation_matrix(np.radians(deg), [0, 0, 1]))
        n = int(contains(turret, h2.sample(60000)).sum())
        rec("D hub turned %.0f deg bears on the spigot D-key" % deg, n > 0, "%d points" % n)
    # mount vs the structure
    Pm = mount.sample(80000)
    for nm, m in (("turret", turret), ("collar", collar)):
        n = int(contains(m, Pm).sum())
        rec("E mount vs %s" % nm, n == 0, "%d / 80000" % n)
    c = Pm[contains(base, Pm)]
    bad = int((c[:, 2] < -0.02).sum() + (c[:, 2] > 0.15).sum()) if len(c) else 0
    rec("E mount vs base: posts meet the underside only", bad == 0,
        "%d contacts, z %s, %d off the face" % (len(c), ("%.3f..%.3f" % (c[:, 2].min(), c[:, 2].max())) if len(c) else "-", bad))
    # posts centred on the base foot holes
    ok = True
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * G.POST_XY, sy * G.POST_XY
            P = np.array([[x, y, z] for z in (0.5, 2.0, 4.0)])
            ok &= not base.contains(P).any()
    rec("E posts on the base foot-hole axes (holes open above)", ok, "4 of 4")
    # clearances that make it assemble
    rec("F hub flange clears the plate bore", DC.BORE_CLR_D / 2 - G.FLANGE_D / 2 >= 0.9,
        "radial %.2f mm" % (DC.BORE_CLR_D / 2 - G.FLANGE_D / 2))
    rec("F lip top under the spigot end", G.Z_SB - G.Z_LIP_TOP >= 1.0,
        "%.2f mm below the spigot" % (G.Z_SB - G.Z_LIP_TOP))
    rec("F lip top under the collar", -7.0 - G.Z_LIP_TOP >= 3.0,
        "%.2f mm below the collar" % (-7.0 - G.Z_LIP_TOP))
    # collar pinch bolts: along +X from the -X side, at the wall mid-radius
    import gen_base_collar as GB
    import math
    for z in GB.BOLT_Z:
        run = None
        for d in np.arange(0.5, 70, 0.5):
            x = -GB.X_WALL - d
            ring = np.array([[x, GB.Y_BOLT + 1.25 * math.cos(t), z + 1.25 * math.sin(t)]
                             for t in np.linspace(0, 2 * np.pi, 12, endpoint=False)])
            if any(m.contains(ring).any() for m in (base, mount, turret, srv)):
                run = d; break
        rec("G collar pinch bolt z %.1f: hex-key run from outside" % z, run is None,
            ">70 mm clear" if run is None else "blocked at %.1f mm" % run)
    fails = [r for r in RES if not r[1]]
    print("\nFAILURES: %d" % len(fails))
    for f in fails:
        print("  - %s | %s" % (f[0], f[2]))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
