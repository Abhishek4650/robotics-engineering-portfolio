#!/usr/bin/env python3
"""
MANUAL VERIFICATION -- Rule 3's most important check.

Not a gate. This slices each part by hand and reads the geometry directly,
feature by feature, the way you would inspect a printed part on the bench.
Every number is measured from the solid; nothing is taken from a parameter.

Covers Rule 3 items 3 (features on the right face/plane), 4 (servo seats
correctly and drives the next link), 5 (no floating servo) and 10 (no face
overlap, real clearance).
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import servo_geom as SG        # noqa: E402
import seat_servo as S         # noqa: E402

FAIL = []


def check(label, ok, detail=""):
    print("   %-52s %s %s" % (label, "PASS" if ok else "FAIL", detail))
    if not ok:
        FAIL.append(label)
    return ok


def void_runs(m, p0, p1, n=2000):
    """Contiguous VOID intervals along a segment, as (start, end, length)."""
    t = np.linspace(0, 1, n)
    P = np.outer(1 - t, p0) + np.outer(t, p1)
    ins = m.contains(P)
    L = np.linalg.norm(np.asarray(p1) - np.asarray(p0))
    out, i = [], 0
    while i < n:
        if not ins[i]:
            j = i
            while j + 1 < n and not ins[j + 1]:
                j += 1
            out.append((t[i] * L, t[j] * L, (t[j] - t[i]) * L))
            i = j + 1
        else:
            i += 1
    return out


def bore(m, cx, cy, z0, z1, want_d, label, tol=0.6):
    """A bore on the joint axis: measure its diameter by radial probing."""
    # Vectorised: build the whole (z, r, theta) lattice and call contains()
    # once. Probing r in a Python loop calls contains() ~800 times per z and
    # takes minutes per bore.
    zs = np.linspace(z0, z1, 7)
    rs = np.linspace(0.2, want_d * 0.75, 160)
    ang = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    Z, Rr, A = np.meshgrid(zs, rs, ang, indexing="ij")
    P = np.c_[(cx + Rr * np.cos(A)).ravel(),
              (cy + Rr * np.sin(A)).ravel(), Z.ravel()]
    ins = m.contains(P).reshape(len(zs), len(rs), len(ang))
    solid_ring = ins.all(axis=2)          # this radius is fully in material
    ds = []
    for i in range(len(zs)):
        w = np.where(solid_ring[i])[0]
        if len(w):
            ds.append(2 * rs[w[0]])
    if not ds:
        return check(label, False, "no wall found")
    d = float(np.median(ds))
    return check(label, abs(d - want_d) <= tol,
                 "measured O%.2f, want O%.2f" % (d, want_d))


def verify_fork(jn, stl_p1, stl_p2, z_in, z_seat_top, z_bay, z_drive,
                brg_od, bay_off):
    print("\n%s" % ("=" * 74))
    print("MANUAL VERIFICATION -- %s" % jn)
    print("=" * 74)
    p1 = trimesh.load(os.path.join(HERE, stl_p1))
    p2 = trimesh.load(os.path.join(HERE, stl_p2))

    print("\n  [1] bores and pockets on the right plane")
    # bearing bore through the idle cheek
    bore(p1, 0, 0, -z_seat_top + 0.5, -z_in - 0.5, brg_od + 0.02,
         "idle bearing pocket O%.2f" % (brg_od + 0.02))
    # drive-side bearing pocket
    bore(p1, 0, 0, z_in + 2.2, z_seat_top - 0.2, brg_od + 0.02,
         "drive bearing pocket O%.2f" % (brg_od + 0.02))
    # horn clearance through the bay floor
    bore(p1, 0, 0, z_seat_top + 0.5, z_bay - 0.5, 24.0,
         "horn clearance bore O24.00")

    print("\n  [2] the bay is a pinch channel, at the right width")
    for x in (bay_off - 15, bay_off, bay_off + 15):
        runs = void_runs(p2, (x, -20, (z_bay + z_drive) / 2),
                         (x, 20, (z_bay + z_drive) / 2))
        w = max((r[2] for r in runs), default=0.0)
        check("channel at x=%+6.1f" % x, abs(w - SG.PINCH) < 0.05,
              "measured %.3f, want %.3f (-%.2f pinch on the %.2f case)"
              % (w, SG.PINCH, SG.PINCH_INTERF, SG.CASE_W))

    print("\n  [3] no thin surfaces (Rule 3 item 2)")
    n = p2.face_normals
    c = p2.triangles_center
    thin = 0
    for ax in range(3):
        sel = np.abs(n[:, ax]) > 0.999
        if not sel.any():
            continue
        u = np.unique(np.round(c[sel][:, ax], 3))
        for a, b in zip(u, u[1:]):
            if 1e-4 < b - a < 0.20:
                sa = sel & (np.abs(c[:, ax] - a) < 1e-3)
                sb = sel & (np.abs(c[:, ax] - b) < 1e-3)
                if (n[sa][:, ax] < 0).any() and (n[sb][:, ax] > 0).any():
                    thin += 1
    check("sub-layer bands in p2", thin == 0, "%d found" % thin)

    print("\n  [4] the servo seats, on axis, not floating")
    srv, zface = S.servo_in_joint_frame()
    s = srv.copy()
    s.apply_translation([0, 0, z_bay - zface])
    bb = s.bounds
    sl = s.section(plane_origin=[0, 0, bb[0][2] + 0.8],
                   plane_normal=[0, 0, 1])
    v = np.asarray(sl.vertices)
    hx = (v[:, 0].max() + v[:, 0].min()) / 2
    hy = (v[:, 1].max() + v[:, 1].min()) / 2
    check("horn on the joint axis", np.hypot(hx, hy) < 0.02,
          "offset %.4f mm" % np.hypot(hx, hy))
    check("horn passes through the floor into the bore", bb[0][2] < z_bay,
          "horn tip z %.2f, floor z %.2f" % (bb[0][2], z_bay))
    check("case fully inside the bay", bb[1][2] <= z_bay + SG.BAY_T_Z + 0.01,
          "case back z %.2f, bay top %.2f" % (bb[1][2], z_bay + SG.BAY_T_Z))
    P = s.sample(40000)
    ins = p2.contains(P)
    cc = P[ins]
    off = int((np.abs(cc[:, 1]) < SG.PINCH / 2 - 0.05).sum()) if len(cc) else 0
    check("contact ONLY on the pinch faces", off == 0,
          "%d of %d contacts off-pinch" % (off, int(ins.sum())))
    if len(cc):
        pen = np.abs(cc[:, 1]).max() - SG.PINCH / 2
        check("pinch grips the case", 0.05 < pen < 0.20,
              "%.3f mm per side" % pen)
    # floating test: does rotation bite?
    r5 = srv.copy()
    r5.apply_transform(trimesh.transformations.rotation_matrix(
        np.radians(5), [0, 0, 1]))
    r5.apply_translation([0, 0, z_bay - zface])
    P5 = r5.sample(12000)
    c5 = P5[p2.contains(P5)]
    o5 = int((np.abs(c5[:, 1]) < SG.PINCH / 2 - 0.05).sum()) if len(c5) else 0
    check("5 deg rotation is resisted by the bay", o5 > 0,
          "%d off-pinch points at 5 deg (strap closes the last ~2 deg)" % o5)

    print("\n  [5] p1/p2 mate as adjacent faces (Rule 3 item 10)")
    gap = p2.bounds[0][2] - p1.bounds[1][2]
    check("parting plane coincident", abs(gap) < 1e-6, "gap %.6f mm" % gap)
    n1 = int(p1.contains(p2.sample(20000)).sum())
    n2 = int(p2.contains(p1.sample(20000)).sum())
    check("no interpenetration", n1 == 0 and n2 == 0,
          "p2-in-p1 %d, p1-in-p2 %d" % (n1, n2))
    return s


def main():
    print("MANUAL VERIFICATION -- reading the geometry directly")
    print("Rule 3: manual inspection is the most important check.")
    verify_fork("J3", "J3_p1.stl", "J3_p2.stl",
                z_in=15.5, z_seat_top=24.5, z_bay=28.5, z_drive=64.40,
                brg_od=42.0, bay_off=12.5)
    verify_fork("J5", "J5_p1.stl", "J5_p2.stl",
                z_in=16.0, z_seat_top=22.0, z_bay=26.0, z_drive=61.90,
                brg_od=37.0, bay_off=12.5)
    print("\n%s" % ("=" * 74))
    if FAIL:
        print("FAILURES (%d):" % len(FAIL))
        for f in FAIL:
            print("   - %s" % f)
    else:
        print("ALL MANUAL CHECKS PASS")
    print("=" * 74)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
