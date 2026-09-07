"""Buy-this-not-that sheet: accurate scale drawings of every purchased part."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Wedge

INK, STEEL, GOOD, BAD, DIM = "#1b2733", "#8b96a3", "#1e7d3c", "#b03a2e", "#8a6d3b"
RACE, BALL = "#5b6673", "#c9d2dc"


def dim_h(ax, x0, x1, y, txt, c=DIM):
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", color=c, lw=1.1))
    ax.text((x0+x1)/2, y+1.4, txt, ha="center", fontsize=8.5, color=c, fontweight="bold")


def dim_v(ax, y0, y1, x, txt, c=DIM):
    ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", color=c, lw=1.1))
    ax.text(x+1.2, (y0+y1)/2, txt, va="center", fontsize=8.5, color=c,
            fontweight="bold", rotation=90)


def deep_groove(ax, cx=0, cy=0):
    """6806 half-section, both sides of the axis. 30 x 42 x 7.

    Outer race Ø42 down to Ø36.6, inner race Ø30 up to Ø35.4, a 3.2 mm ball
    running in the groove between them, seal lips closing the gap.
    """
    OD, ID, W = 42.0, 30.0, 7.0
    r_o_in, r_i_out, r_ball = 18.3, 17.7, 1.6      # radii, mm
    r_ball_c = (r_o_in + r_i_out) / 2
    for s in (1, -1):
        # outer race: from OD/2 inward
        ax.add_patch(Rectangle((cx - W/2, cy + s*r_o_in), W, s*(OD/2 - r_o_in),
                               fc=RACE, ec=INK, lw=1.3, zorder=3))
        # inner race: from bore outward
        ax.add_patch(Rectangle((cx - W/2, cy + s*ID/2), W, s*(r_i_out - ID/2),
                               fc=RACE, ec=INK, lw=1.3, zorder=3))
        # ball in the groove
        ax.add_patch(Circle((cx, cy + s*r_ball_c), r_ball,
                            fc=BALL, ec=INK, lw=1.2, zorder=6))
        # rubber seals both faces
        for xf in (cx - W/2 + 0.5, cx + W/2 - 0.5):
            ax.plot([xf, xf], [cy + s*(r_i_out), cy + s*(r_o_in)],
                    color="#3a4450", lw=2.6, zorder=7, solid_capstyle="butt")
    ax.plot([cx - W/2 - 4, cx + W/2 + 4], [cy, cy], color=INK, lw=0.8,
            ls=(0, (7, 3, 1, 3)))
    ax.text(cx + W/2 + 1.5, cy + r_ball_c, "ball", fontsize=7.5, color=INK, va="center")
    ax.text(cx - W/2 - 1.5, cy + (OD/2 + r_o_in)/2, "outer race", fontsize=7.5,
            color=INK, ha="right", va="center")
    ax.text(cx - W/2 - 1.5, cy - (ID/2 + r_i_out)/2, "inner race", fontsize=7.5,
            color=INK, ha="right", va="center")
    dim_v(ax, cy - OD/2, cy + OD/2, cx + W/2 + 12, "Ø42 OD")
    dim_v(ax, cy - ID/2, cy + ID/2, cx + W/2 + 24, "Ø30 bore")
    dim_h(ax, cx - W/2, cx + W/2, cy + OD/2 + 3, "7 wide")


def thrust_washer(ax, cx=0, cy=0):
    OD, W = 42.0, 3.7
    for s in (1, -1):
        ax.add_patch(Rectangle((cx-W/2, cy+s*8), W, s*(OD/2-8),
                               fc="#d8b4b0", ec=BAD, lw=1.2))
    ax.plot([cx-W/2-3, cx+W/2+3], [cy, cy], color=INK, lw=0.8, ls=(0, (6, 3, 1, 3)))
    dim_v(ax, cy-OD/2, cy+OD/2, cx+W/2+9, "Ø42 OD", BAD)
    dim_h(ax, cx-W/2, cx+W/2, cy+OD/2+3, "3.7 thin", BAD)
    ax.text(cx, cy, "no inner race\nnothing grips\nthe shaft", ha="center",
            va="center", fontsize=8, color=BAD, style="italic")


fig = plt.figure(figsize=(16.5, 9.6))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(2, 3, hspace=.30, wspace=.22, left=.04, right=.98, top=.88, bottom=.05)

# --- 1. the bearing you need
ax = fig.add_subplot(gs[0, 0]); ax.set_aspect("equal"); ax.axis("off")
deep_groove(ax)
ax.set_xlim(-34, 46); ax.set_ylim(-32, 30)
ax.set_title("BUY THIS\n6806-2RS deep-groove ball bearing",
             fontsize=12, fontweight="bold", color=GOOD, loc="left")
ax.text(-33, -25, "30 x 42 x 7 mm  ·  QTY 12\nalso sold as 61806-2RS / 6806ZZ\n"
        "specify C2 clearance if offered", fontsize=9, color=INK)

# --- 2. the one you have
ax = fig.add_subplot(gs[0, 1]); ax.set_aspect("equal"); ax.axis("off")
thrust_washer(ax)
ax.set_xlim(-34, 46); ax.set_ylim(-32, 30)
ax.set_title("NOT THIS\nthrust washer (what you already have)",
             fontsize=12, fontweight="bold", color=BAD, loc="left")
ax.text(-33, -25, "Ø42 x 3.7 mm\nSAME outer diameter, so it drops\n"
        "into the pocket and looks right", fontsize=9, color=BAD)

# --- 3. why
ax = fig.add_subplot(gs[0, 2]); ax.axis("off")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.set_title("WHY IT MATTERS", fontsize=12, fontweight="bold", color=INK, loc="left")
ax.text(0, .88, "A thrust washer takes load along the shaft ONLY.\n"
        "Balls run between two flat plates, so the joint is\n"
        "free to TILT. That tilt is your 28.9 mm wobble.\n\n"
        "A deep-groove bearing has a grooved raceway that\n"
        "captures the ball, so it resists radial load too.\n"
        "TWO of them, 22 mm apart, resist the tilting moment.\n\n"
        "One bearing cannot do it. Two touching cannot do it.\n"
        "It is the SPACING that carries the moment.",
        fontsize=9.6, color=INK, va="top", linespacing=1.55)
ax.text(0, .12, "28.9 mm  ->  0.65 mm", fontsize=15, fontweight="bold", color=GOOD)
ax.text(0, .04, "only with the preload screw fitted", fontsize=9, color=STEEL)

# --- 4. shaft
ax = fig.add_subplot(gs[1, 0]); ax.set_aspect("equal"); ax.axis("off")
ax.add_patch(Rectangle((0, -15), 72, 30, fc="#b9c2cc", ec=INK, lw=1.4))
ax.add_patch(Rectangle((0, -10), 72, 20, fc="white", ec=INK, lw=1.2))
dim_v(ax, -15, 15, 76, "Ø30")
dim_v(ax, 10, 15, 84, "5 wall")
dim_h(ax, 0, 72, 19, "72 long, x6")
ax.set_xlim(-8, 100); ax.set_ylim(-26, 26)
ax.set_title("Ø30 STEEL TUBE, 5 mm wall", fontsize=12, fontweight="bold",
             color=INK, loc="left")
ax.text(0, -23, "cut 6 x 72 mm  ·  DO NOT PRINT\n"
        "a printed shaft creeps under 2.9 N.m", fontsize=9, color=INK)

# --- 5. inserts
ax = fig.add_subplot(gs[1, 1]); ax.set_aspect("equal"); ax.axis("off")
for i, (d, l, lbl, n) in enumerate([(4.6, 5.8, "M3", 40), (3.6, 4.0, "M2.5", 12)]):
    x = i * 26
    ax.add_patch(Rectangle((x, 0), d, l, fc="#c9a227", ec=INK, lw=1.3))
    for k in range(4):
        ax.plot([x, x + d], [l * (k + .5) / 4, l * (k + .5) / 4], color="#8a6d1a", lw=.9)
    ax.text(x + d / 2, -1.6, f"{lbl}\nØ{d} x {l}\nqty {n}", ha="center", va="top",
            fontsize=9, color=INK)
ax.set_xlim(-6, 42); ax.set_ylim(-9, 10)
ax.set_title("BRASS HEAT-SET INSERTS", fontsize=12, fontweight="bold", color=INK, loc="left")
ax.text(-6, 9.4, "knurled, for melting into plastic", fontsize=9, color=STEEL)

# --- 6. screws
ax = fig.add_subplot(gs[1, 2]); ax.axis("off")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.set_title("FASTENERS", fontsize=12, fontweight="bold", color=INK, loc="left")
rows = [("M3 x 12 socket cap", "24", "link seams"),
        ("M3 x 16 socket cap", "12", "collars, wrist"),
        ("M3 x 20 socket cap", "6", "bearing PRELOAD"),
        ("M2.5 x 10", "12", "tip ears"),
        ("M2 x 6", "24", "servo horns"),
        ("M2.5 x 8", "24", "servo cases"),
        ("M4 x 16", "4", "base to bench"),
        ("M3 washers", "~30", "under every head")]
y = .88
ax.text(0, y + .06, f"{'item':22s}{'qty':>6s}   where", fontsize=9,
        color=STEEL, fontweight="bold", family="monospace")
for a, b, c in rows:
    ax.text(0, y, f"{a:22s}{b:>6s}   {c}", fontsize=9.2, color=INK, family="monospace")
    y -= .095

fig.suptitle("ARM-450 — parts to buy   (drawn to scale from the real dimensions)",
             fontsize=15.5, fontweight="bold", color=INK, x=.02, ha="left", y=.955)
fig.savefig("figures/bom_visual.png", dpi=175, facecolor="white")
print("wrote figures/bom_visual.png")
