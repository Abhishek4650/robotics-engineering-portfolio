#!/usr/bin/env python3
"""
AUDIT of what the standing checks did not cover (Rule 3 / 4 / 6 re-run,
2026-09-24). On the exact-solid meshes of the final assembly:

  A  JOINTS TOGETHER: 450 combined poses (J1 x J2 x J3 x J4 x J5), minimum
     distance between every pair of rigid bodies (FCL). Neighbours are compared
     without the joint's own bearing / servo / horn screws. The single-joint
     sweep and the six drawn poses never moved joints together over a grid.
  B  TIPPING: centre of mass of the whole arm (printed parts at an effective
     fill, servos, bearings, steel, brass) over the same grid, against the
     foot's footprint.
  C  THINNEST WALL of every printed part: inward rays from 20 000 surface
     points; walls under 0.8 mm (two 0.4 mm lines) reported.
  D  BED: every print-ready part against 180^3 and 256^3 mm build volumes.
  (DISASSEMBLY is checked by verify_disassembly.py with exact OCC booleans and
  a baseline for the fit each unit starts in. An FCL depth sweep that stood
  here read the designed press fits and the servo pinch as obstructions.)
"""
import itertools
import json
import os
import re
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_rule6_pages as R6     # noqa: E402
import make_rule5_views as R5     # noqa: E402
import build_final_assembly as BA  # noqa: E402
import verify_fasteners as VF     # noqa: E402

PLA, STEEL, BRASS = 1.24e-3, 7.85e-3, 8.5e-3        # g / mm3
SERVO_G, B6806_G, B6706_G = 55.0, 20.0, 7.0          # ST3215 (Waveshare: ~55 g), bearings


def load():
    A, _ = BA.build()
    S, C = {}, {}
    for ch in A.children:
        w = VF.world(ch)
        if w is not None:
            S[ch.name] = w; C[ch.name] = ch
    return S, C


def mass_of(name, vol, fill):
    k = R5.kind(name)
    if k == "servo":
        return SERVO_G
    if k == "bearing":
        return B6806_G if "J1" in name or "J2" in name or "J3" in name else B6706_G
    if k in ("screw", "nut", "spring"):
        return vol * STEEL
    if k == "insert":
        return vol * BRASS
    return vol * PLA * fill


def main():
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    S, C = load()
    meshes = {k: R5.tess(v, 0.06, 0.25) for k, v in S.items()}
    axes = R6.joint_axes()
    report = {}
    # ------------------------------------------------------------------ A
    print("A  JOINTS TOGETHER -- 450 combined poses")
    mgr = {}
    for b in range(7):
        mgr[b] = trimesh.collision.CollisionManager()
    names_in = {b: [] for b in range(7)}
    for nm, (V, F) in meshes.items():
        b = R6.body(nm)
        if b is None or nm.startswith("spring_"):
            continue
        mgr[b].add_object(nm, trimesh.Trimesh(V, F, process=False)); names_in[b].append(nm)
    # neighbour managers without the joint's own hardware
    joint_hw = lambda k, nm: nm.startswith("brg_J%d" % k) or nm == "servo_J%d" % k or nm.startswith("horn_screw_J%d" % k)
    nb = {}
    for k in range(1, 7):
        for side, b in (("lo", k - 1), ("hi", k)):
            m = trimesh.collision.CollisionManager()
            for nm in names_in[b]:
                if not joint_hw(k, nm):
                    V, F = meshes[nm]; m.add_object(nm, trimesh.Trimesh(V, F, process=False))
            nb[(k, side)] = (m, [n for n in names_in[b] if not joint_hw(k, n)])
    grid = list(itertools.product((0, 45), (-54, -27, 0, 27, 54), (-72, -36, 0, 36, 72), (-90, 0, 90), (-46.5, 0, 46.5)))
    worst = {}
    com_worst = (0, None, None)
    # masses
    vol = {}
    for nm, sh in S.items():
        g = GProp_GProps(); BRepGProp.VolumeProperties_s(sh, g); vol[nm] = (g.Mass(), np.array([g.CentreOfMass().X(), g.CentreOfMass().Y(), g.CentreOfMass().Z()]))
    fill = 0.65          # 4 perimeters + 40 % gyroid on these wall thicknesses, conservative (heavy)
    for th5 in grid:
        th = list(th5) + [0.0]
        G = R6.body_frames(axes, th)
        for b in range(7):
            for nm in names_in[b]:
                mgr[b].set_transform(nm, G[b])
        for k in range(1, 7):
            for side, b in (("lo", k - 1), ("hi", k)):
                m, ns = nb[(k, side)]
                for nm in ns:
                    m.set_transform(nm, G[b])
        for i in range(7):
            for j in range(i + 1, 7):
                if j == i + 1:
                    d, nn = nb[(j, "lo")][0].min_distance_other(nb[(j, "hi")][0], return_names=True)
                else:
                    d, nn = mgr[i].min_distance_other(mgr[j], return_names=True)
                if (i, j) not in worst or d < worst[(i, j)][0]:
                    worst[(i, j)] = (d, th5, nn)
        # centre of mass
        M, Mx = 0.0, np.zeros(3)
        for nm, (v, c) in vol.items():
            b = R6.body(nm)
            if b is None:
                b = 1 if nm.startswith("spring_J2") else 2
            m_ = mass_of(nm, v, fill)
            M += m_; Mx += m_ * (G[b] @ np.r_[c, 1])[:3]
        com = Mx / M
        r = np.hypot(com[0], com[1])
        if r > com_worst[0]:
            com_worst = (r, th5, com)
    body_n = ["ground", "turret", "upper link", "forearm", "J4 hub", "blade", "flange"]
    rowsA = []
    for (i, j), (d, th5, nn) in sorted(worst.items(), key=lambda kv: kv[1][0]):
        lim = 0.1 if j == i + 1 else 0.5
        ok = d > lim
        rowsA.append(dict(pair="%s-%s" % (body_n[i], body_n[j]), min=round(float(d), 3), pose=th5, parts=nn, ok=ok))
        print("   %-22s min %7.3f mm at J1..J5 %s  (%s | %s)  %s" % ("%s - %s" % (body_n[i], body_n[j]), d, th5, nn[0], nn[1],
              "ok" if ok else "TOO CLOSE / COLLISION"))
    report["A"] = rowsA
    print("JOINTS TOGETHER: %d pair(s) too close" % sum(1 for r_ in rowsA if not r_["ok"]))
    # ------------------------------------------------------------------ B
    print("\nB  TIPPING -- centre of mass vs the foot")
    import gen_drive_j1 as G1
    Mtot = sum(mass_of(n, v, fill) for n, (v, c) in vol.items())
    foot_r = G1.BASE_R
    r, th5, com = com_worst
    print("   total mass %.0f g (printed parts at %.0f %% fill, 6 x ST3215 %.0f g)" % (Mtot, 100 * fill, SERVO_G))
    print("   worst pose J1..J5 %s: centre of mass %.1f mm from the J1 axis, %.1f mm high; foot radius %.1f mm -> %s"
          % (th5, r, com[2], foot_r, "STANDS (%.1f mm inside the edge)" % (foot_r - r) if r < foot_r else "TIPS unless the foot is fixed down"))
    fixed = getattr(G1, "TABLE_HOLE", 0) > 0
    print("   -> %s" % ("stands on its own" if r < foot_r else
          "the foot MUST be fixed down: 4 x O%.1f table holes at r %.0f are in the foot -> ok" % (G1.TABLE_HOLE, G1.TABLE_R)
          if fixed else "NO MEANS TO FIX THE FOOT DOWN -> FAIL"))
    print("TIPPING: %d problem(s)" % (0 if (r < foot_r or fixed) else 1))
    report["B"] = dict(mass_g=round(Mtot), worst_pose=th5, com_r=round(float(r), 1), foot_r=foot_r, stands=bool(r < foot_r), fixed_down=fixed)
    # ------------------------------------------------------------------ C
    print("\nC  THINNEST WALLS of the printed parts (inward rays, 20 000 points each)")
    import make_final_print as MF
    rowsC = []
    for nm, q, src, note in MF.PARTS:
        m = trimesh.load(os.path.join(src, nm + ".stl")); m.merge_vertices()
        P, fi = trimesh.sample.sample_surface_even(m, 20000, seed=1)
        N = m.face_normals[fi]
        O = P - N * 0.01
        loc, idx, _ = m.ray.intersects_location(O, -N, multiple_hits=False)
        t = np.full(len(P), np.inf)
        t[idx] = np.linalg.norm(loc - O[idx], axis=1)
        t = t[np.isfinite(t) & (t > 0.05)]
        # cluster the thin points: a WALL is a patch >= 15 mm2 thinner than 0.8;
        # a few mm2 where a flat meets a curve is an edge sliver
        from scipy.cluster.hierarchy import fcluster, linkage
        tt = np.full(len(P), np.inf); tt[idx] = np.linalg.norm(loc - O[idx], axis=1)
        sel = np.where((tt < 0.8) & (tt > 0.05))[0]
        walls = []
        if len(sel) >= 3:
            Z = fcluster(linkage(P[sel], "single"), 2.0, "distance")
            for c in np.unique(Z):
                q = sel[Z == c]
                area = len(q) / len(P) * m.area
                if area >= 15.0 and np.median(tt[q]) < 0.8:
                    walls.append((round(area, 1), [round(float(v), 1) for v in P[q].mean(0)], round(float(np.median(tt[q])), 2)))
        p1 = float(np.percentile(t, 1))
        rowsC.append(dict(part=nm, p1=round(p1, 2), thin_walls=walls))
        print("   %-20s 1st percentile %5.2f mm   thin WALLS (>= 15 mm2 under 0.8 mm): %s" % (nm, p1,
              "none" if not walls else "; ".join("%.0f mm2 at %s, %.2f mm" % w for w in walls)))
    ACCEPTED = {"link_upper_groove": "released part the user already printed: 0.5 mm skin under its "
                                     "cable bore = the first bottom layers on the bed, not load-bearing"}
    bad = [r_ for r_ in rowsC if r_["thin_walls"] and r_["part"] not in ACCEPTED]
    for k_, why in ACCEPTED.items():
        print("   accepted: %s -- %s" % (k_, why))
    print("THIN WALLS: %d part(s) with a thin wall" % len(bad))
    report["C"] = rowsC
    # ------------------------------------------------------------------ D
    print("\nD  BED FIT (print-ready orientation)")
    rowsD = []
    for fn, qq, orient, sup, size, note, wt in json.load(open(os.path.join(ROOT, "FINAL_PRINT", "_print_list.json"))):
        e = [float(x) for x in size.split(" x ")]
        rowsD.append(dict(file=fn, size=e, fits180=max(e) <= 180, fits256=max(e) <= 256))
    print("BED: %d part(s) too big for a 180 mm cube" % sum(1 for r_ in rowsD if not r_["fits180"]))
    print("   largest: %s  -> all fit 180 mm cube: %s, 256 mm cube: %s" % (
        max(rowsD, key=lambda r: max(r["size"]))["file"], all(r["fits180"] for r in rowsD), all(r["fits256"] for r in rowsD)))
    report["D"] = rowsD
    json.dump(report, open(os.path.join(HERE, "AUDIT_GAPS.json"), "w"), indent=1, default=str)
    print("\nwritten AUDIT_GAPS.json")


if __name__ == "__main__":
    main()
