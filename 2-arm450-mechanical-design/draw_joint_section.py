"""ARM-450 — sectional drawing of a link-to-link joint."""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, FancyArrowPatch

INK, STEEL, ACC, SERVO = "#1b2733", "#6b7f95", "#2e7d9a", "#c8563c"
SHELL, SHELL_D, BRG, SHAFT = "#dfe6ee", "#c2cedb", "#2f3944", "#8f9aa6"
GOOD, BAD, DIM = "#1e7d3c", "#b03a2e", "#8a6d3b"

W = 29.0        # link boss width (= section width)
BW, BOD, BID = 7.0, 42.0, 30.0
SPAN = W - BW   # 22 mm bearing centre spacing
SEAT = 38.0

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(16.5, 8.4),
                              gridspec_kw=dict(width_ratios=[1.35, 1], wspace=0.14))
fig.patch.set_facecolor("white")

# ===================== SECTION ==========================================
def box(a, x, y, w, h, fc, ec=INK, lw=1.4, z=3, hatch=None):
    a.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                          linewidth=lw, zorder=z, hatch=hatch))

# --- link A boss (the bearing housing) : z from 0 to 29 -------------------
for sgn in (1, -1):
    # outer wall of the boss, top and bottom of the section
    box(ax, 0, sgn * 21, W, sgn * 4, SHELL)
    box(ax, 0, sgn * 25, W, sgn * 0.001, SHELL)
# the two shell halves meet at z = W/2
ax.plot([W / 2, W / 2], [-25, 25], color=BAD, lw=1.6, ls="--", zorder=9)
ax.text(W / 2, 27.5, "clamshell seam", ha="center", fontsize=9,
        color=BAD, fontweight="bold")

# --- the two bearings ----------------------------------------------------
for x0 in (0.0, W - BW):
    for sgn in (1, -1):
        box(ax, x0, sgn * (BID / 2), BW, sgn * ((BOD - BID) / 2), BRG, z=6)
    ax.text(x0 + BW / 2, 0, "", ha="center")
ax.text(BW / 2, 24.5, "6806", ha="center", fontsize=8.5, color=BRG, fontweight="bold")
ax.text(W - BW / 2, 24.5, "6806", ha="center", fontsize=8.5, color=BRG, fontweight="bold")

# --- seat shoulders (Ø38 lip the outer race lands on) --------------------
for sgn in (1, -1):
    box(ax, BW, sgn * (SEAT / 2), W - 2 * BW, sgn * ((BOD - SEAT) / 2), SHELL_D, z=4)

# --- shaft ---------------------------------------------------------------
box(ax, -26, -BID / 2, W + 46, BID, SHAFT, z=5)
ax.text(W / 2, 0, "Ø30 shaft", ha="center", va="center", fontsize=11,
        fontweight="bold", color="white", zorder=7)

# --- link B clamped to the shaft, outboard of the boss -------------------
for sgn in (1, -1):
    box(ax, -24, sgn * (BID / 2), 16, sgn * 13, ACC, z=6)
ax.text(-16, 30, "LINK B\nsplit clamp\non the shaft", ha="center", fontsize=9.5,
        color=ACC, fontweight="bold")

# --- preload screw + spacer ---------------------------------------------
box(ax, W + 6, -6, 5, 12, "#d8c078", z=7)
ax.text(W + 8.5, 15, "preload\nscrew", ha="center", fontsize=9, color=DIM,
        fontweight="bold")
ax.annotate("", (W + 6, 0), (W - 2, 0),
            arrowprops=dict(arrowstyle="->", color=DIM, lw=2.0), zorder=9)

# --- servo horn on the far shaft end -------------------------------------
for sgn in (1, -1):
    box(ax, -26, sgn * 8, 6, sgn * 12, SERVO, z=8)
ax.text(-32, 0, "servo\nhorn", ha="center", va="center", fontsize=9,
        color=SERVO, fontweight="bold")

# --- dimensions ----------------------------------------------------------
ax.annotate("", (BW / 2, -33), (W - BW / 2, -33),
            arrowprops=dict(arrowstyle="<->", color=DIM, lw=1.4))
ax.text(W / 2, -37.5, f"bearing spacing {SPAN:.0f} mm", ha="center",
        fontsize=10.5, color=DIM, fontweight="bold")
ax.annotate("", (0, -44), (W, -44),
            arrowprops=dict(arrowstyle="<->", color=DIM, lw=1.4))
ax.text(W / 2, -48.5, f"link boss width {W:.0f} mm", ha="center",
        fontsize=10, color=DIM)

ax.text(0, 40, "A   Section through a link-to-link joint",
        fontsize=13, fontweight="bold", color=INK)
ax.text(0, 35.5, "LINK A boss = the bearing housing.  Ø30 shaft turns inside it.\n"
        "LINK B clamps to the shaft.  Servo horn drives the shaft.",
        fontsize=10, color=STEEL)
ax.set_xlim(-40, W + 20)
ax.set_ylim(-56, 44)
ax.set_aspect("equal")
ax.axis("off")

# ===================== WOBBLE COMPARISON ================================
cases = [("single thrust washer\n(original, d≈5 mm, c=0.20)", 28.9, BAD),
         ("bearing pair, no preload\nd=22 mm, c=0.20", 6.55, BAD),
         ("bearing pair, light preload\nd=22 mm, c=0.05", 1.64, "#d09a2c"),
         ("bearing pair, PRELOADED\nd=22 mm, c=0.02", 0.65, GOOD)]
y = np.arange(len(cases))
ax2.barh(y, [c[1] for c in cases], color=[c[2] for c in cases],
         height=.6, edgecolor="white")
for i, c in enumerate(cases):
    ax2.text(c[1] * 1.08, i, f"{c[1]:.2f} mm", va="center",
             fontsize=10.5, fontweight="bold")
ax2.set_yticks(y)
ax2.set_yticklabels([c[0] for c in cases], fontsize=9.5)
ax2.set_xscale("log")
ax2.set_xlim(0.3, 90)
ax2.set_xlabel("TCP wobble (mm, log scale)")
ax2.set_title("B   What the joint is worth\nθ = 2c/d, projected over 360 mm reach",
              loc="left", fontsize=12.5, fontweight="bold", color=INK)
ax2.grid(axis="x", alpha=.25, ls=":")
ax2.set_axisbelow(True)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)
ax2.text(0.35, -0.85, "PRELOAD is the whole story: it converts clearance into\n"
         "contact. Without it the bearing pair buys only 4x; with it, 44x.",
         fontsize=9.6, color=STEEL, style="italic")

fig.suptitle("ARM-450 — the joint: how the links actually move",
             fontsize=15, fontweight="bold", color=INK, x=.02, ha="left", y=.97)
fig.tight_layout(rect=(0, 0, 1, .94))
fig.savefig("figures/joint_section.png", dpi=190, facecolor="white")
print("wrote figures/joint_section.png")
