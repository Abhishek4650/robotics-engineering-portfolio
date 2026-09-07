"""
FEA on the parts that had never been analysed: turret J1 and the integrated wrist.

Loads come from joint_loads.py (60k-pose worst case) and the payload, applied at
the real mating faces. Same voxel-hex solver as run_fea.py; the limitations
stated there apply here too (stair-stepped curves, linear elastic, isotropic).
"""
import os, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import fea

CAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "cad")
INK, STEEL = "#1b2733", "#6b7f95"
ALLOW = 9.0                      # derated PLA allowable, report §5
G = 9.80665

# worst-case joint torques (N.m) and the masses each part carries
TAU_J2, TAU_J5, TAU_J6 = 2.620, 0.297, 0.088
M_ARM_ABOVE_J2 = 1.025           # kg, everything the turret holds up
M_OUTBOARD_J4 = 0.45             # wrist + payload beyond J4
PAYLOAD = 0.300


def run(name, stl, pitch, bc, loadf, note):
    m, grid, h = fea.voxelise(os.path.join(CAD, stl), pitch)
    mdl = fea.Model(grid, h)
    fixed = mdl.nodes_in(bc)
    loads = loadf(mdl)
    u = mdl.solve(fixed, loads)
    vm = mdl.von_mises(u)
    p99 = np.percentile(vm, 99)
    disp = np.linalg.norm(u.reshape(-1, 3), axis=1).max()
    print(f"  {name:20s} {len(mdl.els):6d} el   p99 {p99:7.3f} MPa   "
          f"SF {ALLOW/p99:6.1f}   defl {disp:.4f} mm")
    q, v = mdl.surface_quads(vm)
    return dict(name=name, quads=q, vals=v, p99=p99, disp=disp, note=note)


# --- turret J1: spigot fixed, J2 bore carries the whole arm ----------------
def turret_bc(gx, gy, gz):
    return gz < 14.0                                   # the Ø30 spigot in the base
def turret_load(mdl):
    X, Z = mdl.dims[0]*mdl.h, mdl.dims[2]*mdl.h
    W = M_ARM_ABOVE_J2 * G                             # 10.1 N down
    F = TAU_J2 * 1000.0 / 60.0                         # couple across the J2 bore
    top = mdl.nodes_in(lambda gx,gy,gz: (gz > Z-46) & (gz < Z-24) & (gx < X*0.5))
    bot = mdl.nodes_in(lambda gx,gy,gz: (gz > Z-46) & (gz < Z-24) & (gx >= X*0.5))
    return [(top, np.array([0.0, 0.0, -W/2 + F])), (bot, np.array([0.0, 0.0, -W/2 - F]))]

# --- J4 housing: forearm bolt face fixed, yoke face loaded ----------------
def j4_bc(gx, gy, gz):  return gz < 5.0
def j4_load(mdl):
    """J4 is a ROLL joint: its housing carries the joint torque as TORSION about
    its own axis. The first version applied only a lateral force, which misses
    the one load case an open C-section is actually weak in."""
    X, Y, Z = [mdl.dims[i]*mdl.h for i in range(3)]
    W = M_OUTBOARD_J4 * G
    TAU_J4 = 0.296                                     # N.m, 60k-pose worst case
    F = TAU_J4 * 1000.0 / (0.056)                      # couple across the Ø56 housing
    F = TAU_J4 * 1000.0 / 56.0                         # N, at the housing radius
    top = mdl.nodes_in(lambda gx,gy,gz: (gz > Z-5.0) & (gx < X*0.5))
    bot = mdl.nodes_in(lambda gx,gy,gz: (gz > Z-5.0) & (gx >= X*0.5))
    # equal and opposite tangential forces = a pure torsional couple, plus weight
    return [(top, np.array([0.0, +F, -W/2])), (bot, np.array([0.0, -F, -W/2]))]

# --- J5 yoke: bottom bolt face fixed, bores loaded ------------------------
def j5_bc(gx, gy, gz):  return gz < 5.0
def j5_load(mdl):
    X, Y, Z = [mdl.dims[i]*mdl.h for i in range(3)]
    F = TAU_J5 * 1000.0 / 30.0 + PAYLOAD*G
    a = mdl.nodes_in(lambda gx,gy,gz: (gy < 14.0) & (gz > 6.0) & (gz < 20.0))
    b = mdl.nodes_in(lambda gx,gy,gz: (gy > Y-14.0) & (gz > 6.0) & (gz < 20.0))
    return [(a, np.array([F/2, 0, -F/2])), (b, np.array([F/2, 0, -F/2]))]

# --- J6 output: bearing pocket fixed, flange loaded -----------------------
def j6_bc(gx, gy, gz):  return gz < 8.0
def j6_load(mdl):
    Z = mdl.dims[2]*mdl.h
    F = PAYLOAD * G
    M = TAU_J6 * 1000.0 / 15.0
    n = mdl.nodes_in(lambda gx,gy,gz: gz > Z-6.0)
    return [(n, np.array([M, 0.0, -F]))]


if __name__ == "__main__":
    print("FEA — turret and integrated wrist (loads from the 60k-pose sweep)\n")
    runs = [
        run("turret_j1", "turret_j1.stl", 2.5, turret_bc, turret_load,
            f"whole arm {M_ARM_ABOVE_J2*G:.1f} N + J2 {TAU_J2:.2f} N·m"),
        run("wrist_j4_housing", "wrist_j4_housing.stl", 1.5, j4_bc, j4_load,
            f"TORSION 0.296 N·m about the roll axis + {M_OUTBOARD_J4*G:.1f} N"),
        run("wrist_j5_yoke", "wrist_j5_yoke.stl", 1.8, j5_bc, j5_load,
            f"J5 {TAU_J5:.2f} N·m + payload"),
        run("wrist_j6_output", "wrist_j6_output.stl", 1.2, j6_bc, j6_load,
            f"payload {PAYLOAD*G:.1f} N + J6 {TAU_J6:.2f} N·m"),
    ]
    vmax = max(r["p99"] for r in runs)
    fig, axes = plt.subplots(1, 4, figsize=(17, 5.4))
    fig.patch.set_facecolor("white")
    def view(az,el):
        a,e=np.radians(az),np.radians(el); ca,sa,ce,se=np.cos(a),np.sin(a),np.cos(e),np.sin(e)
        r=np.array([ca,-sa,0.]); u=np.array([sa*se,ca*se,ce]); return np.vstack([r,u,np.cross(r,u)])
    for ax, r in zip(axes, runs):
        R = view(35, 22); Q = r["quads"] @ R.T
        o = np.argsort(Q[:,:,2].mean(1))
        cols = plt.get_cmap("inferno")(np.clip(r["vals"][o]/vmax, 0, 1))
        ax.add_collection(PolyCollection(Q[o][:,:,:2], facecolors=cols, edgecolors="none"))
        lim = np.abs(Q[:,:,:2]).max()*1.06
        ax.set_xlim(-lim,lim); ax.set_ylim(-lim,lim); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"{r['name']}\n{r['note']}\np99 {r['p99']:.2f} MPa · SF {ALLOW/r['p99']:.0f}",
                     fontsize=10, fontweight="bold", color=INK, pad=8)
    sm = plt.cm.ScalarMappable(cmap="inferno", norm=plt.Normalize(0, vmax))
    cb = fig.colorbar(sm, ax=axes, fraction=0.022, pad=0.012)
    cb.set_label("von Mises (MPa) — derated allowable 9 MPa", fontsize=10)
    fig.suptitle("ARM-450 — FEA on the turret and integrated wrist",
                 fontsize=15, fontweight="bold", color=INK, x=.02, ha="left", y=.99)
    fig.savefig("figures/fea_wrist.png", dpi=180, facecolor="white", bbox_inches="tight")
    print("\nwrote figures/fea_wrist.png")
