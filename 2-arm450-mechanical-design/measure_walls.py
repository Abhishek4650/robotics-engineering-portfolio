"""
Estimate the shell wall thickness of the existing clamshell links, and compute
what the section actually looks like structurally.

For a thin closed-ish shell the mesh surface area counts BOTH faces, so
    t ~= 2 * V / A
is a decent first estimate. Cross-check with a ray-cast thickness sample.
"""

import os
import numpy as np
import trimesh

SRC = os.path.expanduser("~/Desktop/Robotic_arm_design")
PARTS = ["link1_base.stl", "link2_base.stl", "link1_base_1.1.stl",
         "link2_cover.stl", "J2_p2.stl", "wrist_p2.stl"]


def sample_thickness(m, n=4000, seed=0):
    """Cast rays inward from random surface points; first re-hit ~ wall thickness."""
    rng = np.random.default_rng(seed)
    pts, fidx = trimesh.sample.sample_surface(m, n)
    nrm = m.face_normals[fidx]
    origins = pts - nrm * 1e-3
    try:
        loc, ray_idx, _ = m.ray.intersects_location(
            ray_origins=origins, ray_directions=-nrm, multiple_hits=False)
    except Exception:                                          # noqa: BLE001
        return np.nan, np.nan
    if len(loc) == 0:
        return np.nan, np.nan
    d = np.linalg.norm(loc - origins[ray_idx], axis=1)
    d = d[(d > 0.15) & (d < 25)]          # discard grazing + through-bore hits
    if d.size < 20:
        return np.nan, np.nan
    return np.median(d), np.percentile(d, 15)


print(f"{'part':22s} {'vol cm3':>9s} {'area cm2':>9s} {'t=2V/A':>8s} "
      f"{'t_median':>9s} {'t_p15':>7s}")
print("-" * 72)
for p in PARTS:
    f = os.path.join(SRC, p)
    if not os.path.exists(f):
        continue
    m = trimesh.load(f, force="mesh")
    V, A = m.volume, m.area
    t_va = 2 * V / A if (m.is_watertight and V > 0) else np.nan
    t_med, t_p15 = sample_thickness(m)
    print(f"{p:22s} {V/1000:9.1f} {A/100:9.1f} {t_va:8.2f} "
          f"{t_med:9.2f} {t_p15:7.2f}")

# --- what the section is worth, open vs closed -----------------------------
print("\n--- clamshell section, open (two loose halves) vs closed (bolted) ---")
b, h = 47.5, 29.0          # link outer width x depth, from the STLs
for t in (2.0, 2.4, 3.0):
    bi, hi = b - 2 * t, h - 2 * t
    I_closed = (b * h ** 3 - bi * hi ** 3) / 12.0

    # one open half-shell = a C channel, half the depth
    hh = h / 2
    I_half = (b * hh ** 3 - bi * (hh - t) ** 3) / 12.0
    I_open = 2 * I_half        # two halves bending independently about their OWN axes

    # torsion: closed thin tube (Bredt) vs open strip (sum b*t^3/3)
    Am = (b - t) * (h - t)
    peri = 2 * ((b - t) + (h - t))
    J_closed = 4 * Am ** 2 * t / peri
    J_open = 2 * ((2 * b + 2 * hh) * t ** 3 / 3.0)

    print(f"t={t:.1f} mm   I_closed {I_closed:9.0f}  I_open {I_open:9.0f}  "
          f"ratio {I_closed/I_open:5.2f}x   |   "
          f"J_closed {J_closed:10.0f}  J_open {J_open:8.0f}  "
          f"ratio {J_closed/J_open:7.1f}x")
