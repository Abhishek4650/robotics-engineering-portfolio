"""
ARM-450 rev B -- redrawn in the user's own design language (from their paper sketch):
round base with central bore + mounting ears, cylindrical barrel joint housings,
swept cast-style links, collar-stack wrist into a two-finger pincer.

Engineering change vs rev A: L2 == L3 == 145 mm, so the reachable annulus has no
inner dead zone. Panel C proves why that matters.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Wedge, Rectangle

import design_params as P

INK = "#1b2733"
STEEL = "#6b7f95"
SHELL = "#e3e9f0"
SHELL_D = "#c2cedb"
SERVO = "#c8563c"
ACC = "#2e7d9a"
DIM = "#8a6d3b"
GOOD = "#1e7d3c"
BAD = "#b03a2e"


def rot(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s], [s, c]])


def place(pts, o, a):
    return (np.asarray(pts) @ rot(a).T) + np.asarray(o)


def poly(ax, pts, fc, ec=INK, lw=1.4, z=2, alpha=1.0):
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=ec,
                         linewidth=lw, zorder=z, alpha=alpha, joinstyle="round"))


# ---------------------------------------------------------------------------
# components in the user's language
# ---------------------------------------------------------------------------
def barrel(ax, o, r, label=None, z=8):
    """Cylindrical joint housing seen end-on -- concentric rings, like the sketch."""
    ax.add_patch(Circle(o, r, facecolor=SHELL, edgecolor=INK, lw=1.6, zorder=z))
    ax.add_patch(Circle(o, r * 0.74, facecolor=SHELL_D, edgecolor=STEEL, lw=1.0, zorder=z + 1))
    ax.add_patch(Circle(o, r * 0.40, facecolor=SERVO, edgecolor=INK, lw=1.3, zorder=z + 2))
    ax.add_patch(Circle(o, r * 0.15, facecolor="white", edgecolor=INK, lw=1.0, zorder=z + 3))
    ax.plot(*o, marker="+", color=INK, ms=8, mew=1.5, zorder=z + 4)
    if label:
        ax.annotate(label, o, xytext=(0, r + 8), textcoords="offset points",
                    ha="center", fontsize=10, fontweight="bold", color=SERVO, zorder=z + 5)


def cast_link(ax, o, ang, length, r_root, r_tip, z=6):
    """Swept cast-style link blending two barrels -- waisted in the middle."""
    n = 40
    t = np.linspace(0, 1, n)
    # waist: pinch to 62 % at mid-span, blend out to each barrel
    w = (r_root + (r_tip - r_root) * t) * (1 - 0.38 * np.sin(np.pi * t))
    top = np.column_stack([t * length, w])
    bot = np.column_stack([t * length, -w])[::-1]
    poly(ax, place(np.vstack([top, bot]), o, ang), SHELL, lw=1.6, z=z)
    # rib line, reads as a casting parting line
    ax.plot(*place(np.column_stack([t * length, 0.30 * w]), o, ang).T,
            color=SHELL_D, lw=1.4, zorder=z + 1)
    ax.plot(*place(np.column_stack([t * length, -0.30 * w]), o, ang).T,
            color=SHELL_D, lw=1.4, zorder=z + 1)


def round_base(ax):
    """Side elevation: flared foot + 50 mm round base cylinder (user's dimension)."""
    h = P.L_BASE_HEIGHT
    poly(ax, [(-64, 0), (64, 0), (64, 7), (-64, 7)], STEEL, z=3)          # foot flange
    for x in (-50, -30, 30, 50):                                          # bolt holes
        ax.add_patch(Circle((x, 3.5), 2.6, facecolor="white", edgecolor=INK,
                            lw=0.8, zorder=4))
    poly(ax, [(-52, 7), (52, 7), (46, 18), (-46, 18)], SHELL_D, z=3)      # flare
    poly(ax, [(-46, 18), (46, 18), (46, h), (-46, h)], SHELL, z=3)        # barrel
    ax.plot([-46, 46], [h - 9, h - 9], color=SHELL_D, lw=1.3, zorder=4)   # slew brg split
    poly(ax, [(-40, h), (40, h), (40, h + 9), (-40, h + 9)], ACC, z=4)    # turret ring
    # shoulder pillar up to J2
    poly(ax, [(-30, h + 9), (30, h + 9), (26, h + P.L_SHOULDER_RISE),
              (-26, h + P.L_SHOULDER_RISE)], SHELL, z=4)


def wrist_stack(ax, o, ang, length):
    """Collar stack tapering into a two-finger pincer -- straight off the sketch."""
    n = 4
    for i in range(n):
        f0, f1 = i / n, (i + 1) / n
        r0 = 17 - 5 * f0
        r1 = 17 - 5 * f1
        poly(ax, place([(f0 * length * 0.62, -r0), (f1 * length * 0.62, -r1),
                        (f1 * length * 0.62, r1), (f0 * length * 0.62, r0)], o, ang),
             SHELL if i % 2 == 0 else SHELL_D, lw=1.2, z=9)
    x = length * 0.62
    poly(ax, place([(x, -12), (x + 10, -14), (x + 10, 14), (x, 12)], o, ang), ACC, z=10)
    # pincer fingers
    for s in (1, -1):
        poly(ax, place([(x + 10, s * 4), (length, s * 13), (length + 4, s * 10),
                        (x + 12, s * 1)], o, ang), STEEL, lw=1.2, z=10)


def draw_arm(ax, q2, q3, q5):
    round_base(ax)
    j2 = np.array([0.0, P.L_BASE_TO_J2])

    a2 = q2
    j3 = j2 + rot(a2) @ np.array([P.L_UPPER_ARM, 0])
    cast_link(ax, j2, a2, P.L_UPPER_ARM, 27, 23)
    barrel(ax, j2, 27, "J2")
    barrel(ax, j3, 23, "J3")

    a3 = a2 + q3
    j5 = j3 + rot(a3) @ np.array([P.L_FOREARM, 0])
    cast_link(ax, j3, a3, P.L_FOREARM, 23, 18)
    # J4 inline roll collar
    m4 = j3 + rot(a3) @ np.array([P.L_FOREARM * 0.58, 0])
    poly(ax, place([(-8, -17), (8, -17), (8, 17), (-8, 17)], m4, a3), SERVO, lw=1.3, z=8)
    ax.annotate("J4", m4, xytext=(0, 22), textcoords="offset points", ha="center",
                fontsize=10, fontweight="bold", color=SERVO, zorder=12)
    barrel(ax, j5, 18, "J5")

    a5 = a3 + q5
    wrist_stack(ax, j5, a5, P.L_WRIST_TCP)
    tcp = j5 + rot(a5) @ np.array([P.L_WRIST_TCP, 0])
    ax.plot(*tcp, marker="o", ms=8, mfc="none", mec=INK, mew=1.7, zorder=13)
    ax.plot(*tcp, marker="+", color=INK, ms=12, mew=1.5, zorder=13)
    return j2, j3, j5, tcp


def dim_h(ax, x0, x1, y, text, tick=6):
    ax.annotate("", (x0, y), (x1, y),
                arrowprops=dict(arrowstyle="<->", color=DIM, lw=1.2, shrinkA=0, shrinkB=0))
    for x in (x0, x1):
        ax.plot([x, x], [y - tick, y + tick], color=DIM, lw=1.0)
    ax.text((x0 + x1) / 2, y + 9, text, ha="center", va="bottom",
            fontsize=10, color=DIM, fontweight="bold")


def dim_v(ax, y0, y1, x, text):
    ax.annotate("", (x, y0), (x, y1),
                arrowprops=dict(arrowstyle="<->", color=DIM, lw=1.2, shrinkA=0, shrinkB=0))
    for y in (y0, y1):
        ax.plot([x - 6, x + 6], [y, y], color=DIM, lw=1.0)
    ax.text(x - 8, (y0 + y1) / 2, text, ha="right", va="center", fontsize=10,
            color=DIM, fontweight="bold", rotation=90)


def ext(ax, p, q):
    ax.plot([p[0], q[0]], [p[1], q[1]], color=DIM, lw=0.7, ls=(0, (4, 3)), zorder=1)


# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(17.5, 10.2))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(2, 3, width_ratios=[1.12, 0.72, 1.16], height_ratios=[1, 1],
                      hspace=0.14, wspace=0.16,
                      left=0.045, right=0.982, top=0.895, bottom=0.04)

# ---- A : extended side elevation, dimensioned ----------------------------
axA = fig.add_subplot(gs[:, 0])
j2, j3, j5, tcp = draw_arm(axA, 0.0, 0.0, 0.0)
yb = P.L_BASE_TO_J2
dim_h(axA, 0, P.L_UPPER_ARM, yb + 68, "145")
dim_h(axA, P.L_UPPER_ARM, P.L_UPPER_ARM + P.L_FOREARM, yb + 68, "145")
dim_h(axA, P.L_UPPER_ARM + P.L_FOREARM, P.REACH_HORIZ, yb + 68, "70")
dim_h(axA, 0, P.REACH_HORIZ, yb + 112, f"reach {P.REACH_HORIZ:.0f}")
for p in (j2, j3, j5, tcp):
    ext(axA, (p[0], p[1]), (p[0], yb + 116))
dim_v(axA, 0, P.L_BASE_HEIGHT, -95, "50")
dim_v(axA, P.L_BASE_HEIGHT, yb, -95, "40")
for yy in (0, P.L_BASE_HEIGHT, yb):
    ext(axA, (0, yy), (-99, yy))
axA.annotate("", (-72, -36), (P.REACH_HORIZ, -36),
             arrowprops=dict(arrowstyle="<->", color=BAD, lw=1.8))
axA.text((P.REACH_HORIZ - 72) / 2, -58,
         f"50 + 40 + 145 + 145 + 70  =  {P.L_TOTAL:.0f} mm  ✓",
         ha="center", fontsize=11.5, color=BAD, fontweight="bold")
ext(axA, (-72, 0), (-72, -40))
ext(axA, (P.REACH_HORIZ, tcp[1]), (P.REACH_HORIZ, -40))
axA.set_title("A   Extended — dimension chain", loc="left",
              fontsize=12.5, fontweight="bold", color=INK, pad=6)
axA.set_xlim(-150, 400)
axA.set_ylim(-80, 300)

# ---- B : working pose ----------------------------------------------------
axB = fig.add_subplot(gs[0, 1])
draw_arm(axB, np.radians(66), np.radians(-104), np.radians(-40))
axB.set_title("B   Working pose", loc="left", fontsize=12.5,
              fontweight="bold", color=INK, pad=6)
axB.set_xlim(-110, 300)
axB.set_ylim(-30, 340)

# ---- C : base plan view (the user's top-right detail) --------------------
axC = fig.add_subplot(gs[1, 1])
axC.add_patch(Circle((0, 0), 64, facecolor=SHELL_D, edgecolor=INK, lw=1.6, zorder=2))
axC.add_patch(Circle((0, 0), 46, facecolor=SHELL, edgecolor=INK, lw=1.5, zorder=3))
axC.add_patch(Circle((0, 0), 26, facecolor="white", edgecolor=INK, lw=1.5, zorder=4))
axC.text(0, 0, "Ø52\ncable\nbore", ha="center", va="center", fontsize=8.4,
         color=STEEL, zorder=5)
for k in range(4):                                        # mounting ears
    a = np.radians(45 + 90 * k)
    c = np.array([np.cos(a), np.sin(a)]) * 72
    poly(axC, [c + [-11, -11], c + [11, -11], c + [11, 11], c + [-11, 11]],
         SHELL_D, lw=1.3, z=1)
    axC.add_patch(Circle(c, 4.2, facecolor="white", edgecolor=INK, lw=1.0, zorder=6))
axC.add_patch(Circle((0, 0), 64, facecolor="none", edgecolor=STEEL, lw=0.8,
                     ls=(0, (5, 4)), zorder=7))
axC.annotate("slew bearing\n+ 4× M4 ears", (0, -78), (0, -108), ha="center",
             fontsize=9, color=ACC,
             arrowprops=dict(arrowstyle="-", color=ACC, lw=0.9))
axC.set_title("C   Base, plan", loc="left", fontsize=12.5,
              fontweight="bold", color=INK, pad=6)
axC.set_xlim(-115, 115)
axC.set_ylim(-125, 105)

# ---- D : why L2 == L3  ---------------------------------------------------
axD = fig.add_subplot(gs[0, 2])
S = P.L_UPPER_ARM + P.L_FOREARM
cases = [(145, 145, GOOD, "L2 = L3 = 145  ← rev B"),
         (190, 100, "#d09a2c", "L2 190 / L3 100"),
         (220, 70, BAD, "L2 220 / L3 70")]
for i, (l2, l3, col, lbl) in enumerate(cases):
    cx = i * 700
    hole = abs(l2 - l3)
    axD.add_patch(Circle((cx, 0), S, facecolor=col, edgecolor=col, lw=1.4, alpha=0.20))
    axD.add_patch(Circle((cx, 0), S, facecolor="none", edgecolor=col, lw=1.6))
    if hole > 0:
        axD.add_patch(Circle((cx, 0), hole, facecolor="white", edgecolor=BAD,
                             lw=1.6, hatch="///", zorder=3))
        axD.text(cx, hole + 30, f"dead zone Ø{2*hole:.0f}", ha="center", va="bottom",
                 fontsize=9.2, color=BAD, fontweight="bold", zorder=6)
    else:
        axD.text(cx, 40, "no dead zone", ha="center", va="bottom", fontsize=9.6,
                 color=GOOD, fontweight="bold", zorder=6)
    axD.text(cx, -S - 46, lbl, ha="center", fontsize=9.6, color=col, fontweight="bold")
    axD.plot(cx, 0, marker="+", color=INK, ms=9, mew=1.4, zorder=5)
axD.set_title("D   Fixed L2+L3 = 290 mm — unequal links = dead zone",
              loc="left", fontsize=11.8, fontweight="bold", color=INK, pad=6)
axD.set_xlim(-S - 60, 2 * 700 + S + 60)
axD.set_ylim(-S - 78, S + 30)

# ---- E : spec table ------------------------------------------------------
axE = fig.add_subplot(gs[1, 2])
axE.axis("off")
t2, t3 = P.joint_torques()
beams = P.beam_check()
rows = [
    ("REQUIREMENT", "TARGET", "REV B", None),
    ("overall length", "≤ 450 mm", f"{P.L_TOTAL:.0f} mm", True),
    ("total mass", "≤ 1.2 kg", f"{P.MASS_TOTAL*1000:.0f} g", P.MASS_TOTAL <= 1.2),
    ("horizontal reach", "—", f"{P.REACH_HORIZ:.0f} mm", None),
    ("workspace dead zone", "none", f"Ø{2*abs(P.L_UPPER_ARM-P.L_FOREARM):.0f} mm", True),
    ("rated payload @ full reach", "—", f"{P.PAYLOAD_RATED*1000:.0f} g", None),
    ("", "", "", None),
    ("J2 shoulder  (50 kgf·cm)", "4.90 N·m stall",
     f"{t2:.2f} N·m   SF {P.SERVOS['STS3250']['stall']/t2:.1f}", True),
    ("J3 elbow  (30 kgf·cm)", "2.94 N·m stall",
     f"{t3:.2f} N·m   SF {P.SERVOS['STS3215']['stall']/t3:.1f}", True),
    ("", "", "", None),
    ("upper-arm root stress", "55 MPa yield",
     f"{beams['upper_arm']['sigma']:.1f} MPa  SF {beams['upper_arm']['sf']:.0f}", True),
    ("tip droop, rated load", "—",
     f"{beams['upper_arm']['defl']+beams['forearm']['defl']:.2f} mm", None),
]
y = 0.97
for i, (a, b, c, ok) in enumerate(rows):
    if not a and not b:
        y -= 0.030
        continue
    head = (i == 0)
    axE.text(0.00, y, a, fontsize=9.8, fontweight="bold" if head else "normal",
             color=STEEL if head else INK, va="top")
    axE.text(0.48, y, b, fontsize=9.8, fontweight="bold" if head else "normal",
             color=STEEL if head else INK, va="top")
    axE.text(0.76, y, c, fontsize=9.8, fontweight="bold" if ok else "normal",
             color=GOOD if ok else (STEEL if head else INK), va="top")
    if head:
        y -= 0.032
        axE.plot([0, 1], [y, y], color=STEEL, lw=1.0)
    y -= 0.072
axE.set_xlim(0, 1)
axE.set_ylim(0, 1)

for ax in (axA, axB, axC, axD):
    ax.set_aspect("equal")
    ax.axis("off")

fig.suptitle("ARM-450  rev B  —  redrawn to the paper sketch  "
             "(round base · barrel joints · cast links · collar wrist)",
             fontsize=15, fontweight="bold", color=INK, x=0.045, ha="left", y=0.962)
fig.text(0.982, 0.962, "all dimensions mm", fontsize=9.5, color=STEEL, ha="right")

fig.savefig("figures/arm450_revb.png", dpi=200, facecolor="white")
print("wrote figures/arm450_revb.png")
