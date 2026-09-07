"""
Recover the TRUE joint-to-joint link lengths from the capsule links.

A bounding box is not a link length: each capsule has a circular boss at both
ends, and the joint axis sits at the boss CENTRE, inset from the part end by the
boss radius. So bbox length = L_joint_to_joint + r_boss_A + r_boss_B.

Method: project the shell onto its own principal plane, walk along the long
axis, and fit a circle to the boundary at each end. The fitted centres are the
joint axes.
"""

import os
import numpy as np
import trimesh

SRC = os.path.expanduser("~/Desktop/Robotic_arm_design")
PARTS = ["link1_base.stl", "link2_base.stl", "link1_base_1.1.stl",
         "link1_cover.stl", "link2_cover.stl", "link1_cover1.1.stl"]


def fit_circle(pts):
    """Algebraic (Kasa) circle fit -> centre, radius."""
    x, y = pts[:, 0], pts[:, 1]
    A = np.column_stack([2 * x, 2 * y, np.ones(len(x))])
    b = x ** 2 + y ** 2
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy, c = sol
    return np.array([cx, cy]), np.sqrt(c + cx ** 2 + cy ** 2)


def analyse(path):
    m = trimesh.load(path, force="mesh")
    V = m.vertices - m.vertices.mean(axis=0)

    # principal axes: long axis = largest spread, plane normal = smallest
    _, _, W = np.linalg.svd(V - V.mean(axis=0), full_matrices=False)
    P = V @ W.T                     # cols: long, width, thickness
    x, y = P[:, 0], P[:, 1]

    # half-width profile along the long axis
    nb = 160
    edges = np.linspace(x.min(), x.max(), nb + 1)
    ctr = 0.5 * (edges[:-1] + edges[1:])
    hw = np.array([np.abs(y[(x >= edges[i]) & (x < edges[i + 1])]).max()
                   if ((x >= edges[i]) & (x < edges[i + 1])).any() else 0.0
                   for i in range(nb)])

    res = {}
    for side, sl in (("A", slice(0, nb // 3)), ("B", slice(2 * nb // 3, nb))):
        seg = hw[sl]
        segc = ctr[sl]
        rmax = seg.max()
        # boss region = where the profile is within 3 % of that end's max width
        sel = seg >= 0.97 * rmax
        xc_guess = segc[sel].mean()
        # gather boundary points near this end and circle-fit them
        near = np.abs(x - xc_guess) < rmax * 1.15
        pts = P[near][:, :2]
        # keep outer boundary only: farthest point per angle bin about the guess
        ang = np.arctan2(pts[:, 1] - 0.0, pts[:, 0] - xc_guess)
        bins = np.digitize(ang, np.linspace(-np.pi, np.pi, 73))
        keep = []
        for bnum in np.unique(bins):
            grp = pts[bins == bnum]
            d = np.linalg.norm(grp - [xc_guess, 0], axis=1)
            keep.append(grp[d.argmax()])
        c, r = fit_circle(np.array(keep))
        res[side] = (c, r)

    L = np.linalg.norm(res["A"][0] - res["B"][0])
    return dict(bbox=m.extents, L=L,
                rA=res["A"][1], rB=res["B"][1],
                name=os.path.basename(path))


print(f"{'part':22s} {'bbox long':>10s} {'joint-to-joint':>15s} {'rA':>7s} {'rB':>7s}")
print("-" * 68)
out = {}
for p in PARTS:
    f = os.path.join(SRC, p)
    if not os.path.exists(f):
        continue
    r = analyse(f)
    out[p] = r
    print(f"{r['name']:22s} {max(r['bbox']):10.1f} {r['L']:15.1f} "
          f"{r['rA']:7.1f} {r['rB']:7.1f}")

print("\n--- what this means for the 450 mm / dead-zone budget ---")
if "link1_base.stl" in out and "link2_base.stl" in out:
    l1 = out["link1_base.stl"]["L"]
    l2 = out["link2_base.stl"]["L"]
    print(f"current pair   L2 = {l1:.1f}, L3 = {l2:.1f}  ->  "
          f"dead zone Ø{2*abs(l1-l2):.0f} mm")
if "link1_base_1.1.stl" in out and "link2_base.stl" in out:
    l1 = out["link1_base_1.1.stl"]["L"]
    l2 = out["link2_base.stl"]["L"]
    print(f"'1.1' revision L2 = {l1:.1f}, L3 = {l2:.1f}  ->  "
          f"dead zone Ø{2*abs(l1-l2):.0f} mm   <-- unequal!")
