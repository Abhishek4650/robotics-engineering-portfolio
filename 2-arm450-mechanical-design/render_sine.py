"""
Render the ARM-450 tracing the sine, from the SOLVED trajectory.

Not a schematic: every frame is the real STL assembly placed by the same
`assemble.build()` the collision checker uses, so what you see is what was
verified. The traced path is drawn progressively as the tool reaches it.
"""
import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import assemble as A
import isodraw

TRAJ = os.path.expanduser("~/ros2_ws/src/arm450_sine/sine_traj.npz")
OUT = "figures/sine_frames"
INK, PATH, TCPC = "#12202e", "#c0392b", "#1b6f42"


def frame(ax, q, P, upto):
    parts, _ = A.build(*q)
    m = trimesh.util.concatenate([p[0] for p in parts])
    zb = isodraw.ZBuffer(m, px=800)
    ed, sil = isodraw.feature_edges(m, 26.0, want_flags=True)
    segs = isodraw.visible_segments(m, zb, ed, sil=sil, samples=8)
    ax.add_collection(LineCollection(
        [(isodraw.iso(a), isodraw.iso(b)) for a, b in segs],
        colors=INK, linewidths=0.55))
    p2 = isodraw.iso(P[:upto + 1] * 1000.0)
    if len(p2) > 1:
        ax.plot(p2[:, 0], p2[:, 1], color=PATH, lw=2.2, solid_capstyle="round")
    tip = isodraw.iso(P[upto] * 1000.0)
    ax.plot([tip[0]], [tip[1]], "o", color=TCPC, ms=5.5)


def main(n_frames=44):
    os.makedirs(OUT, exist_ok=True)
    d = np.load(TRAJ)
    Q, P = d["Q"], d["P"]
    # Follow the node's PING-PONG playback: forward along the path, then back
    # along the same waypoints. The old wrap-around jumped 43.3 deg on J4 and
    # teleported the tool 139.8 mm between the last waypoint and the first.
    fwd = np.linspace(0, len(Q) - 1, n_frames // 2).astype(int)
    idx = np.concatenate([fwd, fwd[::-1][1:-1]])
    # one fixed view box for every frame, so the arm does not jump around
    allp = []
    for k in idx[::6]:
        parts, _ = A.build(*Q[k])
        allp.append(isodraw.iso(trimesh.util.concatenate(
            [p[0] for p in parts]).vertices))
    allp = np.vstack(allp + [isodraw.iso(P * 1000.0)])
    lo, hi = allp.min(axis=0), allp.max(axis=0)
    pad = (hi - lo).max() * 0.06
    for i, k in enumerate(idx):
        fig, ax = plt.subplots(figsize=(7.2, 6.4))
        frame(ax, Q[k], P, k)
        ax.set_xlim(lo[0] - pad, hi[0] + pad)
        ax.set_ylim(lo[1] - pad, hi[1] + pad)
        ax.set_aspect("equal")
        ax.axis("off")
        arrow = "->" if (i < len(idx) // 2) else "<-"
        ax.set_title(f"ARM-450 — sine trace   waypoint {k+1}/{len(Q)}  {arrow}",
                     fontsize=10.5, color=INK)
        fig.tight_layout()
        fig.savefig(f"{OUT}/f{i:03d}.png", dpi=105, facecolor="white")
        plt.close(fig)
    print(f"  {n_frames} frames -> {OUT}/")


if __name__ == "__main__":
    main()
