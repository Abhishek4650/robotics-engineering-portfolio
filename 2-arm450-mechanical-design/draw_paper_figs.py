"""
Figures for the paper and the presentation.

  verify_matrix.png     6 criteria x 5 configurations, with the MARGIN shown,
                        not just a tick. A pass with 1.06x of margin and a pass
                        with 300x are different facts and a tick hides that.
  spacegrade_compare.png  what survives a move to flight hardware and what does
                        not, scored per subsystem.
"""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
INK, ACC, MUT = "#12202e", "#b4531a", "#5a6b7b"
GOOD, WARN, BAD = "#1e6b45", "#b8860b", "#a4243b"


def verify_matrix():
    import verify_configs as VC
    res = {n: VC.run(n) for n in VC.CONFIGS}
    crit = VC.CRIT
    names = list(VC.CONFIGS)

    # margin = how many times better than the limit, always "bigger is safer"
    def margin(key, v):
        lim = {"sf": 3.0, "compliance_mm": 0.30, "creep_1y_pct": 0.5,
               "fatigue_cycles": 1e8, "servo_margin_min": 1.5,
               "cont_ratio_max": 3.0}[key]
        return (v / lim) if key in ("sf", "fatigue_cycles", "servo_margin_min") \
            else (lim / v)

    M = np.array([[margin(k, res[n][k]) for n in names] for _l, k, _o, _x in crit])
    fig, ax = plt.subplots(figsize=(11.6, 5.4))
    L = np.log10(M)
    L = np.clip(L, 0, 8)
    im = ax.imshow(L, cmap="YlGn", vmin=0, vmax=8, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            # fatigue margins run to 1e28. Printed in full they overflow the
            # cell and wipe out the row label next to them, which is how a
            # figure ends up hiding the very numbers it exists to show.
            if v >= 1e4:
                m, e = f"{v:.0e}".split("e")
                txt = f"{m}×10^{int(e)}"
            elif v >= 10:
                txt = f"{v:,.0f}×"
            else:
                txt = f"{v:.2f}×"
            ax.text(j, i, txt, ha="center", va="center", fontsize=9.6,
                    color=INK if L[i, j] < 4.2 else "white", fontweight="bold")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n.replace("+load", "\n+225 g") for n in names],
                       fontsize=10)
    ax.set_yticks(range(len(crit)))
    ax.set_yticklabels([f"{l}\n({lim})" for l, _k, _o, lim in crit], fontsize=9)
    ax.set_title("ARM-450 — margin against every limit, with and without an end effector\n"
                 "the number is how many times better than the criterion, so 1.00× "
                 "is exactly at the limit",
                 fontsize=12.5, color=INK, fontweight="bold", pad=14)
    cb = fig.colorbar(im, ax=ax, pad=0.015)
    cb.set_label("orders of magnitude of margin (log₁₀, clipped at 8)",
                 fontsize=9, color=MUT)
    ax.text(0.0, -0.20,
            "Every cell passes. The two that are merely comfortable rather than "
            "enormous — servo stall margin and\ncontinuous rating in the "
            "gripper+225 g case — are the ones worth watching on hardware; "
            "the structural\nmargins are so large because this arm is "
            "stiffness-driven and servo-limited, not strength-driven.",
            transform=ax.transAxes, fontsize=8.8, color=MUT, va="top")
    fig.tight_layout()
    p = os.path.join(OUT, "verify_matrix.png")
    fig.savefig(p, dpi=155, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {p}")


ROWS = [
    # subsystem, this build, flight build, survives? (0 no, 1 partly, 2 yes)
    ("Kinematics & DOF layout", "6R, 450 mm, offset-free wrist",
     "identical", 2),
    ("Joint architecture", "Ø42 pocket · 6806 · Ø30 shaft,\none part number throughout",
     "same scheme, flight bearings", 2),
    ("Fastening scheme", "M3 steel, heat-set brass inserts",
     "same layout; locked, staked, vented", 2),
    ("Structural material", "plain PLA, E = 3.5 GPa, Tg 60 °C",
     "Al 6061-T6 or CFRP, E 70 GPa", 0),
    ("Mass", "1.584 kg assembled (1.34 structure + 0.24 fasteners)",
     "≈1.13 kg in Al 6061, ~10× stiffer", 1),
    ("Actuators", "ST3215/3250 hobby serial servos,\nplastic gear train",
     "BLDC + harmonic drive,\nvacuum-rated, rad-tolerant", 0),
    ("Feedback", "servo-internal pot, no joint encoder",
     "joint-side resolver / optical encoder", 0),
    ("Precision", "≈2.2 mm, backlash-dominated",
     "< 50 µm, encoder-closed", 0),
    ("Lubrication", "wet lithium grease in 6806",
     "dry film MoS₂ / PFPE, vacuum-stable", 0),
    ("Thermal range", "0–50 °C; Tg 60 °C is the wall",
     "−120 to +120 °C cycling, CTE-matched", 0),
    ("Vacuum compatibility", "none — PLA outgasses,\ntrapped volumes unvented",
     "TML < 1 %, CVCM < 0.1 %, vented", 0),
    ("Radiation", "none",
     "TID-rated parts, latch-up immune", 0),
    ("Qualification", "analysis + bench only",
     "vibration, shock, thermal-vac, EMC", 0),
    ("Redundancy", "single string",
     "dual-wound motors, redundant sensing", 0),
    ("Docking interface", "3-lug bayonet, J6-driven,\n±9.75 mm capture",
     "same principle; softer capture,\nlatch preload, fluid seal", 1),
    ("Cost", "consumer printer + hobby servos",
     "3–4 orders of magnitude higher", 0),
]


def spacegrade():
    fig, ax = plt.subplots(figsize=(12.6, 8.8))
    ax.axis("off")
    n = len(ROWS)
    ax.set_xlim(0, 10); ax.set_ylim(-1, n + 1.4)
    cols = (0.02, 3.05, 6.55, 9.55)
    ax.text(cols[0], n + 0.75, "SUBSYSTEM", fontsize=10, fontweight="bold", color=INK)
    ax.text(cols[1], n + 0.75, "ARM-450 (this build)", fontsize=10, fontweight="bold", color=INK)
    ax.text(cols[2], n + 0.75, "SPACE-GRADE EQUIVALENT", fontsize=10, fontweight="bold", color=INK)
    ax.plot([0, 10], [n + 0.5, n + 0.5], color=INK, lw=1.1)
    for i, (sub, mine, flight, ok) in enumerate(ROWS):
        y = n - i - 0.5
        if i % 2 == 0:
            ax.add_patch(Rectangle((0, y - 0.44), 10, 0.88, fc="#f6f8fa", ec="none", zorder=0))
        c = (BAD, WARN, GOOD)[ok]
        ax.add_patch(Rectangle((cols[3] - 0.06, y - 0.30), 0.34, 0.60,
                               fc=c, ec="none", zorder=2))
        ax.text(cols[0], y, sub, fontsize=8.8, va="center", color=INK, zorder=3)
        ax.text(cols[1], y, mine, fontsize=8.2, va="center", color="#33414f", zorder=3)
        ax.text(cols[2], y, flight, fontsize=8.2, va="center", color="#33414f", zorder=3)
    ax.plot([0, 10], [-0.05, -0.05], color=INK, lw=1.1)
    key = [("survives the transition unchanged", GOOD),
           ("survives in principle, needs rework", WARN),
           ("does not survive — must be replaced", BAD)]
    for k, (lab, c) in enumerate(key):
        ax.add_patch(Rectangle((0.02 + k * 3.4, -0.75), 0.28, 0.34, fc=c, ec="none"))
        ax.text(0.40 + k * 3.4, -0.58, lab, fontsize=8.6, va="center", color=MUT)
    ax.set_title("What survives a move to flight hardware, and what does not",
                 fontsize=13.5, color=INK, fontweight="bold", pad=16)
    fig.tight_layout()
    p = os.path.join(OUT, "spacegrade_compare.png")
    fig.savefig(p, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {p}")
    return sum(1 for r in ROWS if r[3] == 2), sum(1 for r in ROWS if r[3] == 1), \
        sum(1 for r in ROWS if r[3] == 0)


if __name__ == "__main__":
    print("PAPER FIGURES")
    verify_matrix()
    g, w, b = spacegrade()
    print(f"  space-grade: {g} survive, {w} need rework, {b} must be replaced")
