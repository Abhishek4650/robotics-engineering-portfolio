#!/usr/bin/env python3
"""How J1 is connected, driven and aligned (the user's question on the J1
section, 2026-09-24). Exact section of the final assembly through the J1 axis
(plane y = 0), every part labelled, the torque path numbered."""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_rule5_views as R5        # noqa: E402
import build_final_assembly as BA    # noqa: E402
import verify_fasteners as VF        # noqa: E402

LABEL = {"servo_J1": "J1 servo (ST3215)", "j1_hub": "J1 hub", "J2_turret_p1": "turret (spigot)",
         "spigot_collar": "spigot collar", "collar_pinch": "collar pinch bolt", "base": "base",
         "brg_J1_z3": "6806 bearing (lower)", "brg_J1_z43": "6806 bearing (upper)", "j1_mount": "foot",
         "collar_ins": "insert"}
STEPS = [
    "1  The servo's horn turns. The servo is held",
    "   in the foot: pinch walls, lips, end wall,",
    "   and 4 posts with its own screws.",
    "2  4 x M2.5 bolt the J1 HUB's flange to the",
    "   horn face.",
    "3  The hub's plug has a D-flat; it sits in the",
    "   turret spigot's D-key: that turns the",
    "   turret (a key, not friction).",
    "4  The spigot's end is slit (a collet); the",
    "   SPIGOT COLLAR round it is pinched by one",
    "   M3 bolt and clamps it onto the plug:",
    "   no play.",
    "5  ALIGNMENT: the spigot runs in the base's",
    "   two 6806 bearings, 40 mm apart. They take",
    "   the arm's weight and tipping moment into",
    "   base -> 4 columns -> foot plate; the",
    "   servo only gives torque.",
    "6  Servo output axis = bearing axis",
    "   (measured both ways: 0.000 mm).",
]


def main():
    A, _ = BA.build()
    S = {c.name: VF.world(c) for c in A.children if VF.world(c) is not None}
    P = {}
    for nm, w in S.items():
        b = VF.bbox(w)
        if b[0][2] > 60 or b[1][2] < -60 or max(abs(b[0][0]), abs(b[1][0])) > 200:
            continue
        g = R5.section2d(w, (0, 0, 0), (0, 1, 0), 0, 2)
        if g is not None and not g.is_empty and g.area > 1e-3:
            P[nm] = g
    cols = R5.colours(S.keys())
    IF = R5.interfaces(P)
    fig = plt.figure(figsize=(16.5, 11.7))
    ax = fig.add_axes([0.03, 0.05, 0.60, 0.88])
    R5.draw_section(ax, P, cols, IF)
    for nm, g in P.items():
        lab = LABEL.get(nm) or (("horn screw" if nm.startswith("horn_screw") else None))
        if not lab:
            continue
        c = g.representative_point()
        ax.annotate(lab, (c.x, c.y), xytext=(40 if c.x > 0 else -40, 12), textcoords="offset points",
                    fontsize=8, ha="left" if c.x > 0 else "right",
                    arrowprops=dict(arrowstyle="-", lw=0.6, color="k"),
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="0.4", lw=0.4))
    ax.axvline(0, color="#0050ff", lw=0.8, ls="-.")
    ax.text(0.5, 58, "J1 axis", color="#0050ff", fontsize=9)
    ax.set_xlim(-60, 60); ax.set_ylim(-60, 60); ax.set_aspect("equal"); ax.grid(True, lw=0.3, alpha=0.4)
    ax.set_title("J1: exact section through the axis (plane y = 0), world mm", fontsize=11)
    fig.text(0.65, 0.92, "How J1 is connected, driven and aligned", fontsize=14, fontweight="bold", va="top")
    fig.text(0.65, 0.87, "\n".join(STEPS), fontsize=10, family="monospace", va="top")
    fig.text(0.65, 0.30, "green line = contact, blue = measured gap,\norange hatch = designed fit, red = overlap (none)",
             fontsize=9.5, va="top")
    out = os.path.join(HERE, "RULE6_VIEWS", "j1_drive_explained.png")
    fig.savefig(out, dpi=220); fig.savefig(out[:-4] + ".pdf"); plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
