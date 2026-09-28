#!/usr/bin/env python3
"""Audit M1 picture (Rule 5): every servo screwed by its own back holes.
Exact OCC section of the final assembly through each servo's hole row
(y = +10.25 in the servo frame, the plane of the screw axes), servo back up.
Orange hatch = the designed self-tapping thread, green = contact (the pads on
the servo's back plateau, the heads on their seats), red hatch = overlap
nobody designed (must be none)."""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_rule5_views as R5        # noqa: E402
import make_audit_views as MV        # noqa: E402
import verify_official_servo as VO   # noqa: E402
import verify_fasteners as VF        # noqa: E402


def main():
    A, _ = VO.BA.build()
    S = {c.name: (VF.world(c), c) for c in A.children if VF.world(c) is not None}
    cols = R5.colours(S.keys())
    fig, axs = plt.subplots(3, 2, figsize=(11.7, 16.5))
    bad_all = 0
    for ax, k in zip(axs.ravel(), range(1, 7)):
        Ti = np.linalg.inv(MV.seat_T(S, k)); box = VF.bbox(S["servo_J%d" % k][0])
        P = {}
        for nm, (w, _) in S.items():
            if nm.startswith("spring") or not VF.overlap(box, VF.bbox(w), 25.0):
                continue
            g = R5.section2d(VO.place(w, Ti), (0, 10.25, 0), (0, 1, 0), 0, 2)
            if g is not None and not g.is_empty and g.area > 1e-3:
                P[nm] = g
        IF = R5.interfaces(P)
        R5.draw_section(ax, P, cols, IF)
        bad = [x for x in IF if x[2] == "OVERLAP"]
        bad_all += len(bad)
        n = len([x for x in S if x.startswith("servo_scr_J%d_" % k)])
        ax.set_xlim(-14, 42); ax.set_ylim(22, 58); ax.grid(True, lw=0.3, alpha=0.5)
        ax.set_title("J%d: %d screws into the servo's back holes  (overlaps not designed: %d)" % (k, n, len(bad)),
                     fontsize=10, color="#b00000" if bad else "#004000")
        for nm, g in P.items():
            if nm.startswith(("servo_scr", "servo_J")):
                continue
            c = g.representative_point()
            if 22 < c.y < 58 and -14 < c.x < 42:
                ax.annotate(nm, (c.x, c.y), fontsize=6.5, ha="center",
                            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7))
        ax.set_xlabel("x along the case from the output shaft (mm)", fontsize=8)
        ax.set_ylabel("height above the servo's seat face (mm)", fontsize=8)
    fig.text(0.5, 0.005, "Section through the screw axes. Dark grey = servo (back plateau at 32.0), steel = the "
             "self-tapping screws; orange hatch = thread formed in the servo's hole (designed), green = contact.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.015, 1, 1))
    out = os.path.join(HERE, "RULE6_VIEWS", "servo_screws.png")
    fig.savefig(out, dpi=250); fig.savefig(out[:-4] + ".pdf"); plt.close(fig)       # + vector copy for the PDFs
    print("wrote %s  undesigned overlaps %d" % (out, bad_all))


if __name__ == "__main__":
    main()
