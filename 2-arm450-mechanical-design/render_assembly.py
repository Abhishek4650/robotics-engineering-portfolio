#!/usr/bin/env python3
"""
ARM-450 — detailed assembly render, from the STEP assembly.

`assemble.py` renders the MESH assembly, which has no bearings in it: the mesh
model exists for collision work and the bought hardware was never part of it.
This renders the STEP assembly instead, so what is drawn is what an inspector
opens -- all 34 components, bearings included, in the colours that separate
printed structure from bought items.

It also fixes a scaling fault in the older figure. That sheet computed ONE
scale from the working pose and reused it for the home and extended poses,
which are taller and wider, so those two panels were drawn cropped and the arm
appeared to be missing parts. Every panel here is scaled from its own geometry.

    python3 render_assembly.py            -> figures/assembly_detail.png
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch

import assemble_step as S

HERE = os.path.dirname(os.path.abspath(__file__))
INK, MUT, ACC = "#1b2733", "#5a6478", "#c9560f"
TESS = 0.08                     # mm chord tolerance; 0.3 is visibly faceted

# light rig: a key from over the left shoulder, a cool fill, a rim from behind
KEY = np.array([0.38, 0.30, 0.87]); KEY /= np.linalg.norm(KEY)
FILL = np.array([-0.65, 0.15, 0.35]); FILL /= np.linalg.norm(FILL)
RIM = np.array([-0.2, -0.8, 0.25]); RIM /= np.linalg.norm(RIM)


def tessellate(assy):
    """Every component as (vertices, faces, rgb), in assembly coordinates."""
    out = []
    for ch in assy.children:
        shp = ch.obj.val() if hasattr(ch.obj, "val") else ch.obj
        vs, ts = shp.located(ch.loc).tessellate(TESS)
        V = np.array([[v.x, v.y, v.z] for v in vs])
        F = np.array(ts, dtype=int)
        if len(F) == 0:
            continue
        c = ch.color.toTuple()[:3] if ch.color else (0.7, 0.7, 0.7)
        out.append((V, F, np.array(c), ch.name))
    return out


def view(az, el):
    a, e = np.radians(az), np.radians(el)
    ca, sa, ce, se = np.cos(a), np.sin(a), np.cos(e), np.sin(e)
    r = np.array([ca, -sa, 0.0])
    u = np.array([sa * se, ca * se, ce])
    return np.vstack([r, u, np.cross(r, u)])


def render(ax, parts, az, el, pad=1.06, centre=None, scale=None, edges=True):
    R = view(az, el)
    allv = np.vstack([V for V, _, _, _ in parts])
    C0 = centre if centre is not None else (allv.min(0) + allv.max(0)) / 2
    T, C, Z = [], [], []
    for V, F, base, _name in parts:
        P = (V - C0) @ R.T
        tri = P[F]
        e1 = tri[:, 1] - tri[:, 0]
        e2 = tri[:, 2] - tri[:, 0]
        n = np.cross(e1, e2)
        ln = np.linalg.norm(n, axis=1)
        keep = ln > 1e-12
        n[keep] /= ln[keep][:, None]
        vis = n[:, 2] > 0
        if vis.sum() == 0:
            continue
        nv = n[vis]
        lam = (np.clip(nv @ KEY, 0, 1) * 0.58
               + np.clip(nv @ FILL, 0, 1) * 0.20
               + np.clip(nv @ RIM, 0, 1) * 0.12 + 0.26)
        # Specular was 0.30 at exponent 18. A face pointing straight at the
        # camera then took the full highlight, so in the orthographic views --
        # where whole flat faces point straight at the camera -- entire link
        # halves washed out to near white and the arm read as translucent.
        # A tighter, weaker highlight keeps the shape and loses the glare.
        spec = np.clip(nv[:, 2], 0, 1) ** 40 * 0.10
        col = base[None, :] * lam[:, None] + spec[:, None]
        T.append(tri[vis][:, :, :2])
        C.append(col)
        Z.append(tri[vis][:, :, 2].mean(1))
    T = np.concatenate(T)
    C = np.clip(np.concatenate(C), 0, 1)
    o = np.argsort(np.concatenate(Z))            # painter's algorithm
    ax.add_collection(PolyCollection(
        T[o], facecolors=C[o],
        edgecolors=(C[o] * 0.72 if edges else "none"), linewidths=0.06))
    P2 = (allv - C0) @ R.T
    lim = scale if scale else np.abs(P2[:, :2]).max() * pad
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")
    return lim, C0


def tag(ax, text, xy, xytext, color=ACC, fs=8.6):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=fs, color=color,
                fontweight="bold", ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=color, lw=0.8,
                                shrinkA=0, shrinkB=2))


def main():
    POSE = (np.radians(25), np.radians(58), np.radians(-96),
            np.radians(40), np.radians(-38), np.radians(60))

    print("  tessellating ...")
    work, _ = S.build_step(POSE)
    home, _ = S.build_step()
    expl, _ = S.build_step(explode=16.0)
    Pw, Ph, Px = tessellate(work), tessellate(home), tessellate(expl)
    n = len(Pw)

    fig = plt.figure(figsize=(19.5, 11.6))
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(2, 4, width_ratios=[1.55, 1.0, 1.0, 1.35],
                          height_ratios=[1.0, 1.0], wspace=0.03, hspace=0.10,
                          left=0.015, right=0.985, top=0.885, bottom=0.055)

    fig.text(0.015, 0.955, "ARM-450", fontsize=25, fontweight="bold", color=INK)
    fig.text(0.115, 0.958, "· detailed assembly · 6-DOF · 450 mm to the tool face",
             fontsize=15, color=INK)
    fig.text(0.015, 0.925,
             f"{n} components from arm450_assembly_*.step — printed structure, "
             "bearings, joint shafts, servo collars and the quick-change gripper",
             fontsize=10.4, color=MUT)

    # --- hero -----------------------------------------------------------
    ax = fig.add_subplot(gs[:, 0])
    lim, C0 = render(ax, Pw, 34, 18)
    ax.set_title("working pose", fontsize=13, fontweight="bold", color=INK)
    for txt, xy, xyt in [
            ("J1 turret", (-0.10, -0.62), (-0.92, -0.50)),
            ("J2 shoulder", (-0.02, -0.42), (-0.95, -0.24)),
            ("L2 link — two printed halves", (0.10, -0.16), (-0.99, 0.02)),
            ("J3 elbow", (0.20, 0.10), (-0.95, 0.26)),
            ("J4 / J5 / J6 wrist", (0.13, 0.44), (-0.90, 0.52)),
            ("gripper", (0.05, 0.60), (-0.80, 0.70))]:
        tag(ax, txt, (xy[0] * lim, xy[1] * lim), (xyt[0] * lim, xyt[1] * lim))

    # --- orthographic views ---------------------------------------------
    for k, (az, el, lbl) in enumerate([(0, 0, "front"), (90, 0, "side")]):
        a = fig.add_subplot(gs[0, 1 + k])
        render(a, Pw, az, el)
        a.set_title(lbl, fontsize=11.5, fontweight="bold", color=INK)

    a = fig.add_subplot(gs[1, 1])
    # Not a straight front elevation. Dead-on, the link halves are seen almost
    # edge-on across the seam and the whole column reads as translucent; a few
    # degrees of rotation puts light on the outer faces and it reads as a solid
    # arm again.
    render(a, Ph, 22, 12)
    a.set_title("home — TCP at 450 mm", fontsize=11.5, fontweight="bold", color=INK)

    a = fig.add_subplot(gs[1, 2])
    render(a, Ph, 0, 90)
    a.set_title("plan", fontsize=11.5, fontweight="bold", color=INK)

    # --- exploded --------------------------------------------------------
    a = fig.add_subplot(gs[:, 3])
    render(a, Px, 34, 18)
    a.set_title("exploded on the mating axes", fontsize=13,
                fontweight="bold", color=INK)

    # --- legend ----------------------------------------------------------
    keys = [("printed shell", S.COL["shell"]), ("joint housing", S.COL["joint"]),
            ("servo collar", S.COL["servo"]), ("shaft / clamp", S.COL["steel"]),
            ("bearing (bought)", S.COL["brg"]), ("tool", S.COL["tool"])]
    fig.legend(handles=[Patch(facecolor=c.toTuple()[:3], edgecolor="none", label=l)
                        for l, c in keys],
               loc="lower center", ncol=6, frameon=False, fontsize=10.2,
               bbox_to_anchor=(0.5, 0.005))

    out = os.path.join(HERE, "figures", "assembly_detail.png")
    fig.savefig(out, dpi=190, facecolor="white", bbox_inches="tight")
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()
