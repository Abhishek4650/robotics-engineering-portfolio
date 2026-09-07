"""Stress contour maps for the ARM-450 change schedule."""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import stress_analysis as S

INK, STEEL, GOOD, BAD, WARN = "#1b2733", "#6b7f95", "#1e7d3c", "#b03a2e", "#d09a2c"
G = 9.80665
L2 = L3 = 145.0
LW = 70.0
REACH = L2 + L3 + LW
t = 2.4
I = S.box_I(S.W_AXIS, S.H_BEND, t)
c = S.H_BEND / 2

fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.1], width_ratios=[1.5, 1],
                      hspace=0.32, wspace=0.22, left=.06, right=.98, top=.90, bottom=.07)

# ---------- A: bending stress contour along the arm -----------------------
axA = fig.add_subplot(gs[0, :])
x = np.linspace(0, REACH, 400)
P_tip = (0.150 + 0.300) * G
w = (0.145 + 0.130) * G / (L2 + L3)
M = np.where(x <= L2 + L3,
             P_tip * (REACH - x) + w * (L2 + L3 - x) ** 2 / 2,
             P_tip * (REACH - x))
sig = M * c / I

ny = 60
yy = np.linspace(-c, c, ny)
X, Y = np.meshgrid(x, yy)
SIG = (M[None, :] * Y[:, :] / I)
lim = np.abs(SIG).max()
im = axA.contourf(X, Y, SIG, levels=24, cmap="RdBu_r", vmin=-lim, vmax=lim)
axA.contour(X, Y, SIG, levels=[0], colors=[STEEL], linewidths=1.2, linestyles="--")
cb = fig.colorbar(im, ax=axA, pad=0.012, aspect=13)
cb.set_label("bending stress  σ = M·y/I   (MPa)", fontsize=10)

for xv, lbl in ((0, "J2"), (L2, "J3"), (L2 + L3, "J5"), (REACH, "TCP")):
    axA.axvline(xv, color=INK, lw=1.0, ls=":")
    axA.text(xv, c * 1.18, lbl, ha="center", fontsize=10.5, fontweight="bold", color=INK)
axA.text(6, -c * 0.72, f"peak |σ| = {sig.max():.2f} MPa at the J2 root\n"
                      f"derated allowable ≈ 9 MPa  →  SF ≈ {9/sig.max():.0f}",
         fontsize=10.5, color=GOOD, fontweight="bold")
axA.text(0.5 * REACH, 0, "neutral axis — zero stress", ha="center", va="center",
         fontsize=9, color=STEEL, style="italic")
axA.set_xlabel("distance from the shoulder axis (mm)")
axA.set_ylabel("section depth (mm)")
axA.set_title("A   Bending stress through the link — the shell is nowhere near its limit",
              loc="left", fontsize=12.5, fontweight="bold", color=INK)
axA.set_ylim(-c * 1.35, c * 1.35)

# ---------- B: the bracket that fails, same colour scale ------------------
axB = fig.add_subplot(gs[1, 0])
cases = [("link shell\n(t=2.4)", 0.13, GOOD),
         ("collar wall\n(NEW, 3 mm)", 0.25, GOOD),
         ("6 mm bracket\n(as printed)", 36.0, BAD),
         ("4 mm bracket\n(as printed)", 94.5, BAD)]
names = [c0[0] for c0 in cases]
vals = [c0[1] for c0 in cases]
cols = [c0[2] for c0 in cases]
b = axB.barh(range(len(cases)), vals, color=cols, height=.6, edgecolor="white")
axB.axvline(9.0, color=BAD, ls="--", lw=2.0)
axB.text(9.6, 3.35, "derated allowable\n≈ 9 MPa", fontsize=10, color=BAD, fontweight="bold")
for i, v in enumerate(vals):
    axB.text(v * 1.12, i, f"{v:.2f} MPa" if v < 1 else f"{v:.0f} MPa",
             va="center", fontsize=10.5, fontweight="bold")
axB.set_yticks(range(len(cases)))
axB.set_yticklabels(names, fontsize=10)
axB.set_xscale("log")
axB.set_xlim(0.05, 400)
axB.set_xlabel("peak stress (MPa, log scale)")
axB.set_title("B   Where the stress actually is", loc="left",
              fontsize=12.5, fontweight="bold", color=INK)
axB.grid(axis="x", alpha=.25, ls=":")
axB.set_axisbelow(True)
for s in ("top", "right"): axB.spines[s].set_visible(False)

# ---------- C: section map, where to put material -------------------------
axC = fig.add_subplot(gs[1, 1])
W, H = S.W_AXIS, S.H_BEND
axC.add_patch(Rectangle((-W/2, -H/2), W, H, fc="none", ec=INK, lw=2.0))
axC.add_patch(Rectangle((-W/2+2.4, -H/2+2.4), W-4.8, H-4.8, fc="none",
                        ec=STEEL, lw=1.4, ls="--"))
for sgn in (1, -1):
    axC.add_patch(Rectangle((-W/2, sgn*H/2 - (2.4 if sgn>0 else 0)), W, 2.4,
                            fc=BAD, alpha=.30, ec="none"))
axC.text(0, H/2-6.5, "2.4 mm  — flange, carries 87 % of the moment",
         ha="center", fontsize=9, color=BAD, fontweight="bold")
axC.text(0, -H/2+4.5, "2.4 mm  — flange", ha="center", fontsize=9,
         color=BAD, fontweight="bold")
axC.text(0, 0, "1.6 mm web\n(thin here — near\nthe neutral axis)", ha="center",
         va="center", fontsize=9.5, color=GOOD, fontweight="bold")
for sgn in (1, -1):
    axC.annotate("", (sgn*W/2+7, -H/2), (sgn*W/2+7, H/2),
                 arrowprops=dict(arrowstyle="<->", color=STEEL, lw=1.2))
axC.text(W/2+11, 0, "47.5", rotation=90, va="center", fontsize=10, color=STEEL)
axC.text(0, -H/2-7, "29.0", ha="center", fontsize=10, color=STEEL)
axC.set_xlim(-W, W); axC.set_ylim(-H/2-14, H/2+10)
axC.set_aspect("equal"); axC.axis("off")
axC.set_title("C   Variable wall — where to add and remove", loc="left",
              fontsize=12.5, fontweight="bold", color=INK)

fig.suptitle("ARM-450 — stress map and the change it implies",
             fontsize=15, fontweight="bold", color=INK, x=.02, ha="left", y=.97)
fig.savefig("figures/stress_map.png", dpi=200, facecolor="white",
            bbox_inches="tight")
print(f"peak shell stress {sig.max():.3f} MPa; wrote figures/stress_map.png")
