#!/usr/bin/env python3
"""
ARM-450 rev I -- is it really a 6-DOF arm?  (user request, thumb rules)

1. SIX joint axes, each measured TWO independent ways, which must agree:
   A  the servo that drives it: horn axis of the ST3215 as placed in the
      final assembly (build_final_assembly.SERVOS)
   B  the bearings that carry it: the axis of the bearing-pocket cylinders
      read off the printed part's own faces (OpenCascade), placed in the world
   agreement: angle < 0.05 deg, line-to-line distance < 0.05 mm, and the two
   pockets of a joint coaxial.
2. Each axis has its OWN servo (six distinct ST3215) and its own range
   (whole-arm sweep, SWEEP stage of REVI_CHECKS.log).
3. The six screws give a Jacobian of RANK 6 over the working range
   (product of exponentials on the measured axes; 3000 random poses inside
   the swept ranges), singular configurations named.
4. Controls: a deliberately degenerate arm (J5 axis moved onto J4) must read
   rank <= 5 everywhere -- else the rank test is blind.
"""
import os
import re
import sys

import numpy as np
import cadquery as cq
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_final_assembly as BA     # noqa: E402

RANGES = [90.0, 54.0, 72.0, 90.0, 46.5, 90.0]      # half travel, from the sweep
NAMES = ["J1 base yaw", "J2 shoulder", "J3 elbow", "J4 forearm roll", "J5 wrist pitch", "J6 tool roll"]


def cyl_axes(step, T, radius, tol=0.03):
    sh = cq.importers.importStep(os.path.join(HERE, step)).val().wrapped
    out = []
    e = TopExp_Explorer(sh, TopAbs_FACE)
    while e.More():
        s = BRepAdaptor_Surface(TopoDS.Face_s(e.Current()))
        if s.GetType() == GeomAbs_Cylinder:
            c = s.Cylinder()
            if abs(c.Radius() - radius) < tol:
                a = c.Axis(); p = a.Location(); d = a.Direction()
                P = T @ np.array([p.X(), p.Y(), p.Z(), 1.0]); D = T[:3, :3] @ np.array([d.X(), d.Y(), d.Z()])
                out.append((P[:3], D / np.linalg.norm(D)))
        e.Next()
    return out


def line_dist(p1, d1, p2, d2):
    n = np.cross(d1, d2)
    if np.linalg.norm(n) < 1e-9:
        v = p2 - p1
        return float(np.linalg.norm(v - (v @ d1) * d1))
    return float(abs((p2 - p1) @ n) / np.linalg.norm(n))


def ang(d1, d2):
    return float(np.degrees(np.arccos(min(1.0, abs(d1 @ d2)))))


def hat(w):
    return np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])


def expm_screw(w, v, th):
    W = hat(w)
    R = np.eye(3) + np.sin(th) * W + (1 - np.cos(th)) * W @ W
    p = (np.eye(3) * th + (1 - np.cos(th)) * W + (th - np.sin(th)) * W @ W) @ v
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = p
    return T


def jacobian(axes, th):
    """Spatial Jacobian (product of exponentials); twists ordered (w; v)."""
    J = np.zeros((6, 6)); G = np.eye(4)
    for i, (q, w) in enumerate(axes):
        v = -np.cross(w, q)
        J[:, i] = _adj_wv(G) @ np.r_[w, v]
        G = G @ expm_screw(w, v, th[i])
    return J


def _adj_wv(T):
    # adjoint for twists ordered (w; v)
    R, p = T[:3, :3], T[:3, 3]
    A = np.zeros((6, 6)); A[:3, :3] = R; A[3:, 3:] = R; A[3:, :3] = hat(p) @ R
    return A


L_CHAR = 430.0      # mm: scale the linear rows so rad and mm are comparable


def scaled(J):
    return np.r_[J[:3], J[3:] / L_CHAR]


def rank_stats(axes, poses, tol=1e-6):
    ranks, smin = [], []
    for th in poses:
        s = np.linalg.svd(scaled(jacobian(axes, th)), compute_uv=False)
        ranks.append(int((s > tol * s[0]).sum())); smin.append(s[-1] / s[0])
    return np.array(ranks), np.array(smin)


def main():
    fails = []
    M, TURW, J2J, J3W, J5W, ABC = BA.M, BA.TURW, BA.J2J, BA.J3W, BA.J5W, BA.ABC
    flipZ = BA.rot([1, 0, 0], 180)
    G1, G4, W, G3, TP = BA.G1, BA.G4, BA.W, BA.G3, BA.TP
    servoT = [M(t=(0, 0, G1.Z_CAP)) @ flipZ, TURW @ J2J @ M(t=(0, 0, TP.Z_BAY)), J3W @ M(t=(0, 0, G3.P)),
              M(t=(0, 0, G4.Z_CAP)) @ flipZ, J5W @ M(t=(0, 0, W.P5)), J5W @ ABC @ M(t=(0, 0, W.X6_CAP)) @ flipZ]
    # A: servo horn axes (horn at local (0,0) on the local Z axis)
    A = [(T[:3, 3].copy(), T[:3, 2] / np.linalg.norm(T[:3, 2])) for T in servoT]
    # B: bearing-pocket cylinders on the printed parts (6806 O42.02 / 6706 O37.02)
    r68, r67 = 42.02 / 2, 37.02 / 2
    B_src = [("base.step", np.eye(4), r68), ("J2_turret_p1.step", TURW, r68), ("J3_p1.step", J3W, r68),
             ("j4_cap.step", np.eye(4), r67), ("J5_p1.step", J5W, r67),
             # j6_cap.step is exported ALREADY in the J5 frame (the assembly places
             # it with J5W alone); adding ABC here turned it 90 deg (first run)
             ("j6_cap.step", J5W, r67)]
    print("1  JOINT AXES -- A: servo horn   B: bearing pockets on the printed part\n")
    B = []
    for i, (st, T, r) in enumerate(B_src):
        cyl = cyl_axes(st, T, r)
        if not cyl:
            fails.append("%s: no bearing pocket found in %s" % (NAMES[i], st)); B.append(None); continue
        p0, d0 = cyl[0]
        coax = max(max(ang(d0, d), line_dist(p0, d0, p, d)) for p, d in cyl)
        B.append((p0, d0))
        pa, da = A[i]
        a_ab, d_ab = ang(da, d0), line_dist(pa, da, p0, d0)
        ok = a_ab < 0.05 and d_ab < 0.05 and coax < 0.05
        if not ok:
            fails.append("%s: servo axis vs bearing axis %.3f deg / %.3f mm (pockets coaxial to %.3f)" % (NAMES[i], a_ab, d_ab, coax))
        print("   %-16s axis %s through %s | %d pocket faces (%s), coaxial to %.4f | servo vs bearings: %.4f deg, %.4f mm  %s"
              % (NAMES[i], np.round(da, 4), np.round(pa, 2), len(cyl), st, coax, a_ab, d_ab, "ok" if ok else "FAIL"))
    # 2: six distinct servos + ranges from the sweep log
    log = open(os.path.join(HERE, "REVI_CHECKS.log")).read() if os.path.exists(os.path.join(HERE, "REVI_CHECKS.log")) else ""
    sw = re.findall(r"^\s+(J\d \w+)\s+\+-\s*([\d.]+) deg.*worst rise\s+(\d+)", log, flags=re.M)
    distinct = len({tuple(np.round(T[:3, 3], 3)) for T in servoT}) == 6
    print("\n2  six distinct ST3215 (one per joint): %s;  swept ranges without a clash: %s"
          % (distinct, ", ".join("%s +-%s" % (n, h) for n, h, _ in sw) or "(sweep log missing)"))
    if not distinct or len(sw) != 6:
        fails.append("servo count / sweep ranges")
    # 3: rank of the Jacobian on the MEASURED axes (B; A agrees above)
    axes = [(p, d) for p, d in B]
    rng = np.random.default_rng(7)
    poses = rng.uniform(-1, 1, (3000, 6)) * np.radians(RANGES)
    ranks, smin = rank_stats(axes, poses)
    frac6 = float((ranks == 6).mean())
    print("\n3  Jacobian rank over 3000 random poses inside the swept ranges (linear rows / %.0f mm): rank 6 at %.1f %%; "
          "sigma_min/sigma_max min %.2e, median %.3f" % (L_CHAR, 100 * frac6, smin.min(), np.median(smin)))
    near = poses[smin < 1e-3]
    if len(near):
        # classify: elbow straight (J3 ~ 0), wrist aligned (J5 ~ 0), or the
        # shoulder singularity (wrist centre over the J1 axis) -- all three are
        # the textbook singularities of an elbow arm with a spherical wrist
        wc0 = np.r_[axes[4][0][:2] * 0 + axes[3][0][:2], axes[4][0][2], 1.0]
        kinds = {"elbow straight (|J3| < 8 deg)": 0, "wrist aligned (|J5| < 8 deg)": 0,
                 "wrist centre within 25 mm of the J1 axis": 0, "other": 0}
        for th in near:
            G = np.eye(4)
            for (q, w), t in list(zip(axes, th))[:3]:
                G = G @ expm_screw(w, -np.cross(w, q), t)
            wc = G @ wc0
            if abs(np.degrees(th[2])) < 8:
                kinds["elbow straight (|J3| < 8 deg)"] += 1
            elif abs(np.degrees(th[4])) < 8:
                kinds["wrist aligned (|J5| < 8 deg)"] += 1
            elif np.hypot(wc[0], wc[1]) < 25:
                kinds["wrist centre within 25 mm of the J1 axis"] += 1
            else:
                kinds["other"] += 1
        print("   %d near-singular poses (sigma ratio < 1e-3): %s" % (len(near), "; ".join("%s %d" % kv for kv in kinds.items())))
        if kinds["other"]:
            fails.append("%d near-singular poses not explained by the three textbook singularities" % kinds["other"])
    named = {"home (all 0: arm straight up)": np.zeros(6),
             "working pose (30,40,-70,20,35,10)": np.radians([30, 40, -70, 20, 35, 10]),
             "J5 = 0 only (wrist aligned)": np.radians([30, 40, -70, 20, 0, 10]),
             "J3 = 0 only (elbow straight)": np.radians([30, 40, 0, 20, 35, 10])}
    for k, th in named.items():
        s = np.linalg.svd(scaled(jacobian(axes, th)), compute_uv=False)
        print("   %-36s rank %d   sigma_min/sigma_max %.2e" % (k, int((s > 1e-6 * s[0]).sum()), s[-1] / s[0]))
    if frac6 < 0.99:
        fails.append("rank 6 at only %.1f %% of poses" % (100 * frac6))
    # wrist geometry
    d45 = line_dist(*axes[3], *axes[4]); d56 = line_dist(*axes[4], *axes[5]); d46 = line_dist(*axes[3], *axes[5])
    print("   wrist: J4-J5 %.3f mm, J5-J6 %.3f mm, J4-J6 %.3f mm apart -> %s"
          % (d45, d56, d46, "spherical wrist (axes meet in one point)" if max(d45, d56) < 0.05 else "offset wrist"))
    # 4: control -- a degenerate arm must be caught
    bad = list(axes); bad[4] = axes[3]
    rb, _ = rank_stats(bad, poses[:300])
    ctrl = int(rb.max()) <= 5
    print("\n4  CONTROL: J5 axis moved onto J4 -> max rank %d over 300 poses -> %s" % (rb.max(), "DETECTED" if ctrl else "NOT DETECTED (test blind)"))
    if not ctrl:
        fails.append("control not detected")
    print("\n6-DOF CHECK: %d failure(s)" % len(fails))
    for f in fails:
        print("   FAIL", f)
    return len(fails)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
