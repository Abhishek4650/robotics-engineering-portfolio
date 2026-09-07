"""
The finding that matters: comparing the user's OWN two link generations against
the proposed rev C, using the joint centres measured out of their STLs.

  current   L2 = L3 = 97.9   -> zero dead zone, but only ~196 mm of link reach
  rev '1.1' L2 = 195.1, L3 = 97.9 -> same total link length, Ø194 dead zone
  rev C     L2 = L3 = 145   -> same total link length again, dead zone gone,
                               and the chain finally adds up to 450 mm
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

INK, STEEL, GOOD, BAD, WARN, ACC = "#1b2733", "#6b7f95", "#1e7d3c", "#b03a2e", "#d09a2c", "#2e7d9a"

CASES = [
    dict(l2=97.9, l3=97.9, col=ACC, tag="CURRENT  (link1_base / link2_base)",
         sub="measured from your STLs"),
    dict(l2=195.1, l3=97.9, col=BAD, tag="YOUR '1.1' REVISION",
         sub="link1 lengthened, link2 left alone"),
    dict(l2=145.0, l3=145.0, col=GOOD, tag="PROPOSED  rev C",
         sub="same total link length, split evenly"),
]

fig, axes = plt.subplots(2, 3, figsize=(15.5, 9.4),
                         gridspec_kw=dict(height_ratios=[1.35, 1], hspace=0.22, wspace=0.12))
fig.patch.set_facecolor("white")

RMAX = 300
for k, c in enumerate(CASES):
    l2, l3, col = c["l2"], c["l3"], c["col"]
    outer, hole = l2 + l3, abs(l2 - l3)

    # ---- top row: workspace annulus -------------------------------------
    ax = axes[0, k]
    ax.add_patch(Circle((0, 0), outer, facecolor=col, alpha=0.20, edgecolor=col, lw=1.8))
    if hole > 0:
        ax.add_patch(Circle((0, 0), hole, facecolor="white", edgecolor=BAD,
                            lw=1.8, hatch="///", zorder=3))
        ax.annotate(f"dead zone\nØ{2*hole:.0f} mm", (0, 0), (0, -outer - 62),
                    ha="center", fontsize=10.5, color=BAD, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=BAD, lw=1.3), zorder=6)
    else:
        ax.text(0, -outer - 62, "no dead zone", ha="center", fontsize=10.5,
                color=GOOD, fontweight="bold")

    # the arm at a mid pose, to scale
    q2, q3 = np.radians(38), np.radians(-88)
    e = np.array([l2 * np.cos(q2), l2 * np.sin(q2)])
    t = e + np.array([l3 * np.cos(q2 + q3), l3 * np.sin(q2 + q3)])
    ax.plot([0, e[0], t[0]], [0, e[1], t[1]], color=INK, lw=4.5,
            solid_capstyle="round", zorder=7)
    for p, r in ((np.zeros(2), 8), (e, 7), (t, 5)):
        ax.add_patch(Circle(p, r, facecolor="white", edgecolor=INK, lw=1.8, zorder=8))

    ax.set_title(c["tag"], fontsize=11.6, fontweight="bold", color=col, pad=8)
    ax.text(0.5, 1.005, c["sub"], transform=ax.transAxes, ha="center",
            fontsize=9, color=STEEL, style="italic")
    ax.set_xlim(-RMAX, RMAX)
    ax.set_ylim(-RMAX - 40, RMAX)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- bottom row: length stack vs the 450 budget ----------------------
    ax = axes[1, k]
    BASE, SHOULDER, WRIST = 50, 40, 70
    segs = [("base", BASE, "#9fb0c2"), ("shoulder", SHOULDER, "#8195aa"),
            ("L2", l2, col), ("L3", l3, col), ("wrist→TCP", WRIST, "#8195aa")]
    x = 0
    for name, L, cc in segs:
        ax.add_patch(Rectangle((x, 0), L, 1, facecolor=cc, edgecolor="white", lw=1.6))
        if L > 42:
            ax.text(x + L / 2, 0.5, f"{name}\n{L:.0f}", ha="center", va="center",
                    fontsize=8.8, color="white", fontweight="bold")
        x += L
    total = x
    ax.axvline(450, color=BAD, lw=2.0, ls="--")
    ax.text(450, 1.30, "450 limit", ha="center", fontsize=9.6, color=BAD, fontweight="bold")
    ok = total <= 450
    ax.text(total / 2, -0.42, f"total {total:.0f} mm  " + ("✓" if ok else "✗ OVER"),
            ha="center", fontsize=11.5, fontweight="bold", color=GOOD if ok else BAD)
    if total < 440:
        ax.annotate("", (total, 1.12), (450, 1.12),
                    arrowprops=dict(arrowstyle="<->", color=STEEL, lw=1.2))
        ax.text((total + 450) / 2, 1.20, f"{450-total:.0f} unused",
                ha="center", fontsize=9, color=STEEL)
    ax.set_xlim(-10, 560)
    ax.set_ylim(-0.75, 1.55)
    ax.axis("off")

fig.suptitle("Your two link generations vs the fix — measured from "
             "~/Desktop/Robotic_arm_design/*.stl",
             fontsize=14.5, fontweight="bold", color=INK, y=0.975)
fig.text(0.5, 0.925,
         "L2+L3 is essentially identical in all three (196 / 293 / 290 mm). "
         "Only the SPLIT changes — and the split is what creates the dead zone.",
         ha="center", fontsize=10.4, color=STEEL)
fig.savefig("figures/revision_compare.png", dpi=200, facecolor="white",
            bbox_inches="tight")
print("wrote figures/revision_compare.png")
