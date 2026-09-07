"""
Run the part-wise FEA and render von Mises maps.

Loads come from the assembly statics in joint_loads.py — worst case over the
whole configuration space, so every part is checked at its own worst pose.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

import fea

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "output", "cad")
INK, GOOD, BAD = "#1b2733", "#1e7d3c", "#b03a2e"

# --- loads from the assembly statics (joint_loads.py, 60k-pose sweep) -------
TAU_J2, TAU_J3 = 2.620, 1.271          # N.m worst case
TAU_STALL_3215 = 2.94                  # N.m — mounts are sized to STALL
ALLOWABLE = 9.0                        # MPa derated for PLA (report 5)


def view(az, el):
    a, e = np.radians(az), np.radians(el)
    ca, sa, ce, se = np.cos(a), np.sin(a), np.cos(e), np.sin(e)
    r = np.array([ca, -sa, 0.]); u = np.array([sa * se, ca * se, ce])
    return np.vstack([r, u, np.cross(r, u)])


def render(ax, quads, vals, az, el, vmax):
    R = view(az, el)
    Q = quads @ R.T
    depth = Q[:, :, 2].mean(axis=1)
    o = np.argsort(depth)
    cmap = plt.get_cmap("inferno")
    cols = cmap(np.clip(vals[o] / vmax, 0, 1))
    ax.add_collection(PolyCollection(Q[o][:, :, :2], facecolors=cols,
                                     edgecolors="none"))
    lim = np.abs(Q[:, :, :2]).max() * 1.06
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
    ax.set_aspect("equal"); ax.axis("off")


def study(name, stl, pitch, bc, load_fn, title, note):
    print(f"\n=== {name} ===")
    m, grid, h = fea.voxelise(os.path.join(CAD, stl), pitch)
    mdl = fea.Model(grid, h)
    print(f"  {len(mdl.els)} elements, {mdl.ndof} dof, pitch {h} mm")
    fixed = mdl.nodes_in(bc)
    loads = load_fn(mdl)
    print(f"  {len(fixed)} fixed nodes, {sum(len(n) for n, _ in loads)} loaded nodes")
    u = mdl.solve(fixed, loads)
    vm = mdl.von_mises(u)
    disp = np.linalg.norm(u.reshape(-1, 3), axis=1).max()
    p99 = np.percentile(vm, 99)
    print(f"  max |u| {disp:.4f} mm    von Mises: p50 {np.median(vm):.3f}  "
          f"p99 {p99:.2f}  max {vm.max():.2f} MPa")
    print(f"  SF on p99 vs {ALLOWABLE} MPa allowable: {ALLOWABLE/p99:.1f}")
    quads, vals = mdl.surface_quads(vm)
    return dict(name=name, quads=quads, vals=vals, vm=vm, disp=disp,
                p99=p99, title=title, note=note, nel=len(mdl.els))


# ===========================================================================
# 1. LINK HALF — cantilever: one bearing boss fixed, the other loaded with the
#    force the elbow actually transmits at the J2 worst-case pose.
# ===========================================================================
def link_bc(gx, gy, gz):
    return gx < 12.0                       # the whole first boss region


def link_load(mdl):
    L = mdl.dims[0] * mdl.h
    # force at the far boss = J3 torque / link length, acting transverse
    F = TAU_J3 * 1000.0 / 145.0            # N
    nds = mdl.nodes_in(lambda gx, gy, gz: gx > L - 12.0)
    return [(nds, np.array([0.0, -F, 0.0]))]


# ===========================================================================
# 2. BEARING YOKE — spine mount fixed, bearing bores loaded by the joint
#    reaction (shoulder torque reacted across the 40 mm bearing spacing).
# ===========================================================================
def yoke_bc(gx, gy, gz):
    return gy < 8.0                        # the spine face that bolts to the link


def yoke_load(mdl):
    X = mdl.dims[0] * mdl.h
    Z = mdl.dims[2] * mdl.h
    F = TAU_J2 * 1000.0 / 40.0             # couple across the bearing spacing
    left = mdl.nodes_in(lambda gx, gy, gz: (gx < 14.0) & (gz > Z * 0.35) & (gz < Z * 0.65))
    right = mdl.nodes_in(lambda gx, gy, gz: (gx > X - 14.0) & (gz > Z * 0.35) & (gz < Z * 0.65))
    return [(left, np.array([0.0, 0.0, +F])), (right, np.array([0.0, 0.0, -F]))]


# ===========================================================================
# 3. SERVO COLLAR — flange fixed, bore loaded by a torque couple at STALL.
# ===========================================================================
def collar_bc(gx, gy, gz):
    return gx < 7.0                        # the bolt flange


def collar_load(mdl):
    Y = mdl.dims[1] * mdl.h
    Z = mdl.dims[2] * mdl.h
    F = TAU_STALL_3215 * 1000.0 / (2 * 22.0)   # couple at the bore radius
    top = mdl.nodes_in(lambda gx, gy, gz: (gz > Z - 4.0) & (gy > Y * 0.25) & (gy < Y * 0.75))
    bot = mdl.nodes_in(lambda gx, gy, gz: (gz < 4.0) & (gy > Y * 0.25) & (gy < Y * 0.75))
    return [(top, np.array([0.0, +F, 0.0])), (bot, np.array([0.0, -F, 0.0]))]


if __name__ == "__main__":
    runs = [
        study("link half", "link_half_groove.stl", 2.0, link_bc, link_load,
              "Link half — cantilever, elbow load",
              f"{TAU_J3*1000/145:.1f} N at the far boss"),
        study("bearing yoke", "bearing_yoke.stl", 2.0, yoke_bc, yoke_load,
              "Bearing yoke — shoulder reaction",
              f"{TAU_J2*1000/40:.0f} N couple, 40 mm spacing"),
        study("servo collar", "servo_collar.stl", 2.0, collar_bc, collar_load,
              "Servo collar — ST3215 at STALL",
              f"{TAU_STALL_3215*1000/44:.0f} N couple at STALL"),
    ]

    vmax = max(r["p99"] for r in runs)
    fig, axes = plt.subplots(2, 3, figsize=(16.5, 7.6),
                             gridspec_kw=dict(hspace=0.02, wspace=0.02))
    fig.patch.set_facecolor("white")
    for j, r in enumerate(runs):
        for i, (az, el) in enumerate([(35, 22), (0, 89)]):
            ax = axes[i, j]
            render(ax, r["quads"], r["vals"], az, el, vmax)
            if i == 0:
                ax.set_title(f"{r['title']}\n{r['note']}\n"
                             f"peak p99 {r['p99']:.2f} MPa · SF {ALLOWABLE/r['p99']:.0f} "
                             f"· defl {r['disp']:.3f} mm",
                             fontsize=10.0, fontweight="bold", color=INK, pad=6)
    sm = plt.cm.ScalarMappable(cmap="inferno",
                               norm=plt.Normalize(0, vmax))
    cb = fig.colorbar(sm, ax=axes, fraction=0.028, pad=0.015)
    cb.set_label("von Mises stress (MPa)  —  derated allowable ≈ 9 MPa",
                 fontsize=11)
    fig.suptitle("ARM-450 — part-wise FEA on the printed geometry, "
                 "loads from the 6-DOF assembly statics",
                 fontsize=15, fontweight="bold", color=INK, x=0.02, ha="left", y=0.985)
    fig.savefig("figures/fea_parts.png", dpi=190, facecolor="white",
                bbox_inches="tight")
    print("\nwrote figures/fea_parts.png")
