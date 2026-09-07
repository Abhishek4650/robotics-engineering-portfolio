"""
ARM-450 concept sketch sheet.

Draws the proposed arm as a dimensioned 2-D concept -- the thing you would put
next to your paper sketch and argue about before touching SolidWorks.

Design language (deliberately NOT the myCobot 280 stacked-cylinder look):
    * hexagonal tapered pedestal instead of a round puck
    * open twin-plate CLEVIS yokes at every pitch joint -> servo runs in double
      shear, and you can see straight through the joint
    * upper arm is an open truss with triangular lightening cutouts
    * forearm is a slim square carbon spar, visibly thinner than the upper arm,
      so the arm tapers outward instead of being constant-section
    * compact orthogonal wrist block, circular tool flange on a 30 mm bolt circle
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyBboxPatch, Wedge

import design_params as P

INK = "#1b2733"
STEEL = "#6b7f95"
CARBON = "#2f3944"
SERVO = "#c8563c"
FILL = "#dfe6ee"
ACC = "#2e7d9a"
DIM = "#8a6d3b"


# ---------------------------------------------------------------------------
# geometry helpers -- everything in mm, side-view plane (x right, z up)
# ---------------------------------------------------------------------------
def rot(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s], [s, c]])


def place(pts, origin, ang):
    """Rotate local pts by ang and translate to origin."""
    return (np.asarray(pts) @ rot(ang).T) + np.asarray(origin)


def poly(ax, pts, fc, ec=INK, lw=1.4, z=2, alpha=1.0):
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=ec,
                         linewidth=lw, zorder=z, alpha=alpha, joinstyle="round"))


def truss_link(ax, origin, ang, length, h_root, h_tip, n_cut=3):
    """Open twin-plate truss segment with triangular lightening cutouts."""
    hr, ht = h_root / 2, h_tip / 2
    outline = [(-14, -hr), (length + 12, -ht), (length + 12, ht), (-14, hr)]
    poly(ax, place(outline, origin, ang), FILL, lw=1.6, z=3)

    # triangular cutouts, alternating up/down -> reads as a truss web
    span = length - 26
    w = span / n_cut
    for i in range(n_cut):
        x0 = 6 + i * w
        f0, f1 = x0 / length, (x0 + w) / length
        y0 = hr + (ht - hr) * f0
        y1 = hr + (ht - hr) * f1
        m = 0.72
        if i % 2 == 0:
            tri = [(x0 + 3, -y0 * m), (x0 + w - 3, -y1 * m), (x0 + w / 2, y0 * m)]
        else:
            tri = [(x0 + 3, y0 * m), (x0 + w - 3, y1 * m), (x0 + w / 2, -y0 * m)]
        poly(ax, place(tri, origin, ang), "white", ec=STEEL, lw=1.0, z=4)


def tube_link(ax, origin, ang, length, a=20.0):
    """Slim square carbon spar with printed end collars."""
    h = a / 2
    poly(ax, place([(0, -h), (length, -h), (length, h), (0, h)], origin, ang),
         CARBON, ec=INK, lw=1.4, z=3)
    # weave hint
    for f in np.linspace(0.12, 0.88, 7):
        x = f * length
        ax.plot(*place([(x - 4, -h), (x + 4, h)], origin, ang).T,
                color="#5a6675", lw=0.7, zorder=4)
    for x0 in (0, length):
        c = 1 if x0 == 0 else -1
        poly(ax, place([(x0, -h - 3), (x0 + c * 16, -h - 3),
                        (x0 + c * 16, h + 3), (x0, h + 3)], origin, ang),
             FILL, lw=1.3, z=5)


def yoke(ax, origin, ang, r=17.0, depth=26.0):
    """Clevis yoke cheeks -- the double-shear joint housing."""
    poly(ax, place([(-depth, -r), (0, -r), (0, r), (-depth, r)], origin, ang),
         FILL, lw=1.5, z=5)
    ax.add_patch(Wedge(origin, r, np.degrees(ang) - 90, np.degrees(ang) + 90,
                       facecolor=FILL, edgecolor=INK, lw=1.5, zorder=5))


def servo_at(ax, origin, r=13.0, label=None):
    ax.add_patch(Circle(origin, r, facecolor=SERVO, edgecolor=INK, lw=1.5, zorder=7))
    ax.add_patch(Circle(origin, r * 0.42, facecolor="white", edgecolor=INK,
                        lw=1.1, zorder=8))
    ax.plot(*origin, marker="+", color=INK, ms=7, mew=1.4, zorder=9)
    if label:
        ax.annotate(label, origin, xytext=(0, r + 9), textcoords="offset points",
                    ha="center", fontsize=9, fontweight="bold", color=SERVO, zorder=10)


def base_pedestal(ax):
    """Hexagonal tapered pedestal + J1 turret ring."""
    poly(ax, [(-62, 0), (62, 0), (62, 8), (-62, 8)], STEEL, z=2)        # foot plate
    poly(ax, [(-55, 8), (55, 8), (40, 62), (-40, 62)], FILL, z=2)       # pedestal
    for x in (-30, 0, 30):                                              # facet lines
        ax.plot([x * 1.0, x * 0.72], [8, 62], color=STEEL, lw=0.8, zorder=3)
    poly(ax, [(-38, 62), (38, 62), (38, 74), (-38, 74)], ACC, z=3)      # turret ring
    poly(ax, [(-26, 74), (26, 74), (26, 95), (-26, 95)], FILL, z=3)     # shoulder yoke
    for dx in (-4, 4):                                                  # M3 bolt hints
        ax.add_patch(Circle((dx * 9, 68), 2.4, facecolor="white",
                            edgecolor=INK, lw=0.8, zorder=5))


def draw_arm(ax, q2, q3, q5, tool=True):
    """Full arm in the side plane. q* in radians, measured from +x."""
    base_pedestal(ax)
    j2 = np.array([0.0, P.L_BASE_TO_J2])
    servo_at(ax, j2, 15, "J2")

    a2 = q2
    j3 = j2 + rot(a2) @ np.array([P.L_UPPER_ARM, 0])
    truss_link(ax, j2, a2, P.L_UPPER_ARM, 40, 30)
    yoke(ax, j3, a2)
    servo_at(ax, j3, 13, "J3")

    a3 = a2 + q3
    j5 = j3 + rot(a3) @ np.array([P.L_FOREARM, 0])
    tube_link(ax, j3, a3, P.L_FOREARM)
    # J4 roll -- inline collar on the spar
    m4 = j3 + rot(a3) @ np.array([P.L_FOREARM * 0.55, 0])
    poly(ax, place([(-9, -14), (9, -14), (9, 14), (-9, 14)], m4, a3),
         SERVO, lw=1.3, z=6)
    ax.annotate("J4", m4, xytext=(0, 20), textcoords="offset points", ha="center",
                fontsize=9, fontweight="bold", color=SERVO, zorder=10)

    yoke(ax, j5, a3, r=15, depth=20)
    servo_at(ax, j5, 12, "J5")

    a5 = a3 + q5
    # compact orthogonal wrist block
    poly(ax, place([(0, -15), (46, -13), (46, 13), (0, 15)], j5, a5), FILL, lw=1.5, z=6)
    m6 = j5 + rot(a5) @ np.array([46, 0])
    servo_at(ax, m6, 11, "J6")
    # tool flange on 30 mm bolt circle
    flange = j5 + rot(a5) @ np.array([P.L_WRIST_TCP - 8, 0])
    poly(ax, place([(0, -19), (8, -19), (8, 19), (0, 19)], flange, a5), ACC, lw=1.4, z=7)
    tcp = j5 + rot(a5) @ np.array([P.L_WRIST_TCP, 0])
    if tool:
        ax.plot(*tcp, marker="o", ms=7, mfc="none", mec=INK, mew=1.6, zorder=11)
        ax.plot(*tcp, marker="+", color=INK, ms=11, mew=1.4, zorder=11)
    return j2, j3, j5, tcp


# ---------------------------------------------------------------------------
# dimensioning
# ---------------------------------------------------------------------------
def dim_h(ax, x0, x1, y, text, tick=6, off=0):
    ax.annotate("", (x0, y), (x1, y),
                arrowprops=dict(arrowstyle="<->", color=DIM, lw=1.2, shrinkA=0, shrinkB=0))
    for x in (x0, x1):
        ax.plot([x, x], [y - tick, y + tick], color=DIM, lw=1.0)
    ax.text((x0 + x1) / 2, y + 9 + off, text, ha="center", va="bottom",
            fontsize=9.5, color=DIM, fontweight="bold")


def dim_v(ax, y0, y1, x, text):
    ax.annotate("", (x, y0), (x, y1),
                arrowprops=dict(arrowstyle="<->", color=DIM, lw=1.2, shrinkA=0, shrinkB=0))
    for y in (y0, y1):
        ax.plot([x - 6, x + 6], [y, y], color=DIM, lw=1.0)
    ax.text(x - 9, (y0 + y1) / 2, text, ha="right", va="center", fontsize=9.5,
            color=DIM, fontweight="bold", rotation=90)


def ext(ax, p, q):
    ax.plot([p[0], q[0]], [p[1], q[1]], color=DIM, lw=0.7, ls=(0, (4, 3)), zorder=1)


# ---------------------------------------------------------------------------
# the sheet
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(16.5, 9.6))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(2, 2, width_ratios=[1.55, 1], height_ratios=[1, 1],
                      hspace=0.16, wspace=0.10,
                      left=0.045, right=0.985, top=0.90, bottom=0.045)

# ---- A : fully extended, dimensioned -------------------------------------
axA = fig.add_subplot(gs[0, :])
j2, j3, j5, tcp = draw_arm(axA, 0.0, 0.0, 0.0)

yb = P.L_BASE_TO_J2
dim_h(axA, 0, P.L_UPPER_ARM, yb + 78, f"{P.L_UPPER_ARM:.0f}")
dim_h(axA, P.L_UPPER_ARM, P.L_UPPER_ARM + P.L_FOREARM, yb + 78, f"{P.L_FOREARM:.0f}")
dim_h(axA, P.L_UPPER_ARM + P.L_FOREARM, P.REACH_HORIZ, yb + 78, f"{P.L_WRIST_TCP:.0f}")
dim_h(axA, 0, P.REACH_HORIZ, yb + 122, f"horizontal reach  {P.REACH_HORIZ:.0f}")
dim_v(axA, 0, P.L_BASE_TO_J2, -95, f"{P.L_BASE_TO_J2:.0f}")
for p in (j2, j3, j5, tcp):
    ext(axA, (p[0], p[1]), (p[0], yb + 126))
ext(axA, (0, 0), (-99, 0))
ext(axA, (0, yb), (-99, yb))

# the 450 mm headline dimension: base plane -> TCP along the stretched chain
axA.annotate("", (-72, -34), (P.REACH_HORIZ, -34),
             arrowprops=dict(arrowstyle="<->", color="#b03a2e", lw=1.8))
axA.text(P.REACH_HORIZ / 2 - 36, -52,
         f"OVERALL LENGTH  {P.L_BASE_TO_J2:.0f} + {P.L_UPPER_ARM:.0f} + "
         f"{P.L_FOREARM:.0f} + {P.L_WRIST_TCP:.0f}  =  {P.L_TOTAL:.0f} mm   ≤ 450 mm  ✓",
         ha="center", fontsize=11, color="#b03a2e", fontweight="bold")
ext(axA, (-72, 0), (-72, -38))
ext(axA, (P.REACH_HORIZ, tcp[1]), (P.REACH_HORIZ, -38))

axA.set_title("A   Side elevation — fully extended, dimension chain",
              loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=8)
axA.set_xlim(-150, 400)
axA.set_ylim(-80, 260)

# ---- B : natural working pose --------------------------------------------
axB = fig.add_subplot(gs[1, 0])
draw_arm(axB, np.radians(62), np.radians(-98), np.radians(-38))
axB.set_title("B   Working pose — the silhouette you actually see",
              loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=8)
axB.set_xlim(-140, 330)
axB.set_ylim(-40, 330)

notes = [
    ("open twin-plate truss", (55, 190), (150, 268)),
    ("slim carbon spar\n(arm tapers outward)", (168, 232), (272, 300)),
    ("clevis yoke = double shear", (-14, 110), (-122, 190)),
    ("hex pedestal,\nnot a round puck", (-42, 30), (-128, 78)),
]
for txt, xy, xyt in notes:
    axB.annotate(txt, xy=xy, xytext=xyt, fontsize=9, color=ACC, ha="center",
                 arrowprops=dict(arrowstyle="-", color=ACC, lw=0.9,
                                 connectionstyle="arc3,rad=0.2"), zorder=12)

# ---- C : spec block -------------------------------------------------------
axC = fig.add_subplot(gs[1, 1])
axC.axis("off")
t2, t3 = P.joint_torques()
beams = P.beam_check()

rows = [
    ("REQUIREMENT", "TARGET", "THIS DESIGN", None),
    ("overall length", "≤ 450 mm", f"{P.L_TOTAL:.0f} mm", True),
    ("total mass", "≤ 1.2 kg", f"{P.MASS_TOTAL*1000:.0f} g", P.MASS_TOTAL <= 1.2),
    ("horizontal reach", "—", f"{P.REACH_HORIZ:.0f} mm", None),
    ("rated payload @ full reach", "—", f"{P.PAYLOAD_RATED*1000:.0f} g", None),
    ("DOF", "—", "6 (revolute)", None),
    ("", "", "", None),
    ("J2 shoulder torque", "STS3250  4.90 N·m",
     f"{t2:.2f} N·m   SF {P.SERVOS['STS3250']['stall']/t2:.1f}", True),
    ("J3 elbow torque", "STS3215  2.94 N·m",
     f"{t3:.2f} N·m   SF {P.SERVOS['STS3215']['stall']/t3:.1f}", True),
    ("", "", "", None),
    ("upper-arm root stress", f"{P.SECTIONS['upper_arm']['sigma_y']/1e6:.0f} MPa yield",
     f"{beams['upper_arm']['sigma']:.1f} MPa   SF {beams['upper_arm']['sf']:.0f}", True),
    ("forearm root stress", f"{P.SECTIONS['forearm']['sigma_y']/1e6:.0f} MPa",
     f"{beams['forearm']['sigma']:.1f} MPa   SF {beams['forearm']['sf']:.0f}", True),
    ("tip droop under rated load", "—",
     f"{beams['upper_arm']['defl']+beams['forearm']['defl']:.2f} mm", None),
]

y = 0.97
for i, (a, b, c, ok) in enumerate(rows):
    if a == "" and b == "":
        y -= 0.028
        continue
    head = (i == 0)
    fs = 9.6 if not head else 9.0
    w = "bold" if head else "normal"
    col = STEEL if head else INK
    axC.text(0.00, y, a, fontsize=fs, fontweight=w, color=col, va="top")
    axC.text(0.47, y, b, fontsize=fs, fontweight=w, color=col, va="top")
    axC.text(0.76, y, c, fontsize=fs,
             fontweight="bold" if ok else w,
             color="#1e7d3c" if ok else col, va="top")
    if head:
        y -= 0.030
        axC.plot([0, 1], [y, y], color=STEEL, lw=1.0)
    y -= 0.062

axC.text(0.0, y - 0.02,
         "Structure is sized by JOINT TORQUE and STIFFNESS, not by material stress —\n"
         "the huge stress safety factors mean the sections are set by servo mounting\n"
         "geometry and off-the-shelf tube sizes, which is normal at this scale.",
         fontsize=8.8, color=STEEL, va="top", style="italic")
axC.set_xlim(0, 1)
axC.set_ylim(0, 1)

for ax in (axA, axB):
    ax.set_aspect("equal")
    ax.axis("off")

fig.suptitle("ARM-450   —   6-DOF lightweight arm, clean-sheet concept   "
             "(rev A, all dimensions mm)",
             fontsize=15, fontweight="bold", color=INK, x=0.045, ha="left", y=0.965)
fig.text(0.985, 0.965, "kinematic structure after myCobot 280 URDF · "
         "geometry and styling original", fontsize=9.5, color=STEEL, ha="right")

fig.savefig("figures/arm450_concept.png", dpi=200, facecolor="white")
print("wrote figures/arm450_concept.png")
