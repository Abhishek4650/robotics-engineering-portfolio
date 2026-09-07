"""
2-D orthographic drawing sheets from the exported STLs.

Each sheet: three true orthographic views (front / top / side) with the overall
dimensions, plus a title block carrying the material, mass and finish notes.
Silhouettes are the real geometry, projected and outlined -- not a sketch.
"""
import os, json, numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

CAD = "output/cad"
VOL = json.load(open(os.path.join(CAD, "volumes.json")))
INK, DIM, STEEL, LIGHT = "#1b2733", "#8a6d3b", "#6b7f95", "#e8edf2"


def views(m):
    """Orthographic silhouettes: (front XZ, top XY, side YZ)."""
    v = m.vertices - m.bounds.mean(axis=0)
    f = m.faces
    return [(v[:, [0, 2]], f, "FRONT"), (v[:, [0, 1]], f, "TOP"), (v[:, [1, 2]], f, "SIDE")]


def draw_view(ax, pts2, faces, label, title):
    tri = pts2[faces]
    ax.add_collection(PolyCollection(tri, facecolors=LIGHT, edgecolors="none"))
    # outline: draw all edges thinly, silhouette reads from density
    ax.add_collection(PolyCollection(tri, facecolors="none",
                                     edgecolors=STEEL, linewidths=0.12, alpha=0.55))
    w = pts2[:, 0].max() - pts2[:, 0].min()
    h = pts2[:, 1].max() - pts2[:, 1].min()
    x0, x1 = pts2[:, 0].min(), pts2[:, 0].max()
    y0, y1 = pts2[:, 1].min(), pts2[:, 1].max()
    pad = max(w, h) * 0.30
    # dimensions
    ax.annotate("", (x0, y0 - pad * 0.42), (x1, y0 - pad * 0.42),
                arrowprops=dict(arrowstyle="<->", color=DIM, lw=1.1))
    ax.text((x0 + x1) / 2, y0 - pad * 0.60, f"{w:.1f}", ha="center",
            fontsize=8.5, color=DIM, fontweight="bold")
    ax.annotate("", (x1 + pad * 0.42, y0), (x1 + pad * 0.42, y1),
                arrowprops=dict(arrowstyle="<->", color=DIM, lw=1.1))
    ax.text(x1 + pad * 0.56, (y0 + y1) / 2, f"{h:.1f}", va="center", rotation=90,
            fontsize=8.5, color=DIM, fontweight="bold")
    ax.set_xlim(x0 - pad, x1 + pad); ax.set_ylim(y0 - pad, y1 + pad)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(label, fontsize=9.5, fontweight="bold", color=INK, pad=3)


def sheet(name, qty, material, note, out):
    m = trimesh.load(os.path.join(CAD, name + ".stl"), force="mesh")
    e = m.extents
    vol = VOL.get(name, float("nan"))
    mass = vol * 1.29e-3 * 0.55
    fig = plt.figure(figsize=(11.7, 8.3))          # A4 landscape
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 0.30], hspace=0.14, wspace=0.10,
                          left=.04, right=.97, top=.90, bottom=.05)
    for i, (p2, f, lbl) in enumerate(views(m)):
        draw_view(fig.add_subplot(gs[0, i]), p2, f, lbl, name)
    ax = fig.add_subplot(gs[1, :]); ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                               fill=False, ec=INK, lw=1.4))
    rows = [("PART", name), ("QTY", str(qty)), ("MATERIAL", material),
            ("ENVELOPE", f"{e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm"),
            ("VOLUME", f"{vol/1000:.1f} cm3"), ("MASS", f"{mass:.1f} g each"),
            ("NOTE", note)]
    for k, (a, b) in enumerate(rows):
        x = 0.02 + 0.25 * (k % 4); y = 0.72 - 0.42 * (k // 4)
        ax.text(x, y, a, transform=ax.transAxes, fontsize=8, color=STEEL, fontweight="bold")
        ax.text(x, y - 0.20, b, transform=ax.transAxes, fontsize=9.5, color=INK)
    fig.suptitle(f"ARM-450   ·   {name}", fontsize=15, fontweight="bold",
                 color=INK, x=.04, ha="left", y=.965)
    fig.text(.97, .965, "all dimensions mm  ·  3rd angle", fontsize=8.5,
             color=STEEL, ha="right")
    fig.savefig(out, dpi=150, facecolor="white")
    plt.close(fig)
    return out


PARTS = [
    ("base", 1, "PLA+CF", "HOLLOW to a 3 mm shell — currently modelled solid, 166 g"),
    ("turret_j1", 1, "PLA+CF", "HOLLOW to a 3 mm shell — currently modelled solid, 151 g"),
    ("link_half_tongue", 2, "PLA+CF", "2.4 mm flange / 1.6 mm web. Print split-line down"),
    ("link_half_groove", 2, "PLA+CF", "Mates with tongue half. M3 inserts at <=25 mm pitch"),
    ("joint_shaft", 2, "STEEL — do not print", "Ø30 x 5 wall tube. Printed PLA creeps at 2.6 N.m"),
    ("shaft_clamp", 2, "PLA+CF", "Seats in the Ø38 through-bore between the bearings"),
    ("servo_collar", 2, "PLA+CF", "Split clamp, 2 x M3. Bore = servo +0.2 mm/side"),
    ("wrist_j4_housing", 1, "PLA+CF", "J4 roll. Ø56 to clear the ST3215"),
    ("wrist_j5_yoke", 1, "PLA+CF", "J5 pitch fork"),
    ("wrist_j6_output", 1, "PLA+CF", "J6 roll + integral tool flange, 4 x M3 on Ø30 BCD"),
]

if __name__ == "__main__":
    os.makedirs("figures/dwg", exist_ok=True)
    for n, q, mat, note in PARTS:
        p = sheet(n, q, mat, note, f"figures/dwg/{n}.png")
        print("  ", p)
