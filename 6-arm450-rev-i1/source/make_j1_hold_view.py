#!/usr/bin/env python3
"""How the J1 servo is held today, and where the manufacturer's face holes
are. Three exact sections in the servo frame (horn drawn UP, as in the Rule 5
page): the y = 0 cut the user asked about, a cut along the hole row
(y = +10.25), and a plan cut through the case. The manufacturer's 8 face
holes (Waveshare ST3215 2D drawing + STEP) are drawn over the sections."""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                 # noqa: E402
from matplotlib.patches import Circle           # noqa: E402
from shapely import affinity                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_rule5_views as R5        # noqa: E402
import make_audit_views as MV        # noqa: E402
import verify_official_servo as VO   # noqa: E402
import verify_fasteners as VF        # noqa: E402

# manufacturer's face holes in the servo frame (x from the output axis along
# the case, y across): drawing 18.41 / 20.7 / 24.45 / 20.5 minus 10.11
FRONT_HOLES = [(8.30, -10.25), (8.30, 10.25), (29.00, -10.25), (29.00, 10.25)]
BACK_HOLES = [(8.30, -10.25), (8.30, 10.25), (32.75, -10.25), (32.75, 10.25)]


def main():
    A, _ = VO.BA.build()
    S = {c.name: (VF.world(c), c) for c in A.children if VF.world(c) is not None}
    Ti = np.linalg.inv(MV.seat_T(S, 1))
    sv = VO.place(S["servo_J1"][0], Ti)
    box = VF.bbox(S["servo_J1"][0])
    parts = {"servo_J1": sv}
    for nm, (w, _) in S.items():
        if nm != "servo_J1" and not nm.startswith("spring") and VF.overlap(box, VF.bbox(w), 8.0):
            parts[nm] = VO.place(w, Ti)
    cols = R5.colours(S.keys())
    flip = lambda g: affinity.scale(g, 1.0, -1.0, origin=(0, 0))     # servo -z (horn) drawn up
    cuts = []
    for ttl, o, n, i0, i1, fl in (("A  cut at y = 0 (your picture): only the end wall and the pedestal are in this plane",
                                   (0, 0, 0), (0, 1, 0), 0, 2, True),
                                  ("B  cut at y = +10.25, along the servo's own hole row: the LIP over the front face",
                                   (0, 10.25, 0), (0, 1, 0), 0, 2, True),
                                  ("C  plan cut half-way up the case: the two PINCH walls grip both long sides",
                                   (0, 0, 16.0), (0, 0, 1), 0, 1, False)):
        P = {}
        for nm, sh in parts.items():
            g = R5.section2d(sh, o, n, i0, i1)
            if g is not None and not g.is_empty and g.area > 1e-3:
                P[nm] = flip(g) if fl else g
        cuts.append((ttl, P, fl))
    fig, axs = plt.subplots(3, 1, figsize=(11.7, 16.5))
    for ax, (ttl, P, fl) in zip(axs, cuts):
        IF = R5.interfaces(P)
        R5.draw_section(ax, P, cols, IF)
        ax.set_title(ttl, fontsize=11, loc="left")
        ax.grid(True, lw=0.3, alpha=0.5)
        if fl:          # hole columns in the side cuts: front face z 0..1.65, back face 2.85 deep
            for x, y in FRONT_HOLES:
                if y > 0 and "10.25" in ttl:
                    ax.add_patch(plt.Rectangle((x - 0.8, -1.65), 1.6, 1.65, fc="none", ec="#0050ff", lw=1.2, zorder=7))
            for x, y in BACK_HOLES:
                if y > 0 and "10.25" in ttl:
                    ax.add_patch(plt.Rectangle((x - 0.8, -31.8), 1.6, 2.85, fc="none", ec="#d00000", lw=1.2, zorder=7))
            ax.set_xlim(-24, 42); ax.set_ylim(-60, 18)
        else:
            for x, y in FRONT_HOLES:
                ax.add_patch(Circle((x, y), 0.8, fc="none", ec="#0050ff", lw=1.4, zorder=7))
            for x, y in BACK_HOLES:
                ax.plot([x - 0.9, x + 0.9], [y - 0.9, y + 0.9], color="#d00000", lw=1.4, zorder=7)
                ax.plot([x - 0.9, x + 0.9], [y + 0.9, y - 0.9], color="#d00000", lw=1.4, zorder=7)
            ax.set_xlim(-24, 42); ax.set_ylim(-24, 24)
        ax.set_aspect("equal")
    fig.text(0.5, 0.005, "servo frame, mm (x along the case from the output axis). Blue = the servo's FRONT-face holes, "
             "red = its BACK-face holes (manufacturer's drawing). No screw goes into any of them today.",
             ha="center", fontsize=9.5)
    out = os.path.join(HERE, "RULE6_VIEWS", "j1_servo_hold.png")
    fig.tight_layout(rect=(0, 0.015, 1, 1)); fig.savefig(out, dpi=220); fig.savefig(out[:-4] + ".pdf"); plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
