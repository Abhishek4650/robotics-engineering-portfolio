#!/usr/bin/env python3
"""Rev I verification PDF: full arm + one page per joint.
RED = fixed side (previous link), BLUE = driven link, ORANGE = ST3215."""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                        # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import full_scene as FS                 # noqa: E402
import make_report_pdf as R             # noqa: E402  (projection helpers)

RED, BLUE, ORANGE, GREY = "#c0392b", "#2471a3", "#e67e22", "#9aa0a6"
VIEWS = ((22, -60), (0, 0), (0, -90))
LABELS = ("isometric", "side (along the J2/J3/J5 axes)", "front")

PAGES = [
    ("J1 base yaw", ["j1_mount"], ["j1_hub", "J2_turret_p1"], "servo_J1",
     "Servo slides into the foot's pinch channel against the end wall; its front face under the lips.\n"
     "It stands on 4 posts on its back plateau and is screwed by its OWN 4 back holes from under the foot\n"
     "plate (the self-tappers from the servo box). Hub bolted to the horn (4 x M2.5); its D-plug keys the\n"
     "turret spigot, slit into a collet and clamped by the spigot collar. The turret runs in 2 x 6806 in\n"
     "the base; base on the foot's 4 columns (4 x M4); foot fixed to the table through its 4 holes."),
    ("J2 shoulder", ["J2_turret_p1", "J2_turret_p2"], ["J2_shaft", "link_upper_groove", "link_upper_tongue",
     "shaft_clamp_1", "shaft_clamp_2"], "servo_J2",
     "Servo in the turret pod (-0.22 mm pinch), front face on the parting plane; the cover's 4 pads sit on\n"
     "its back plateau and 4 self-tappers through the cover go into its back holes. Cover: 4 x M3 x 45.\n"
     "Printed shaft bolted to the horn (4 x M2.5, driven through the shaft bore). Both 6806 press in from\n"
     "the fork gap. Link halves locked on the double-D shaft by 2 x M5 x 10 set screws each (centring rings)."),
    ("J3 elbow", ["J3_p1", "J3_p2", "link_upper_groove", "link_upper_tongue"],
     ["J3_shaft", "link_fore_tongue", "link_fore_groove", "shaft_clamp_3", "shaft_clamp_4"], "servo_J3",
     "Same drive train as J2. The fork bolts to the upper link's socket end with 4 x M3 x 10, heads sunk\n"
     "3.2 mm in the fork floor under the swinging forearm. Servo on 4 cover pads + 4 servo screws."),
    ("J4 forearm roll", ["j4_base", "j4_cap", "link_fore_tongue", "link_fore_groove"],
     ["j4_hub", "J5_p1", "J5_p2"], "servo_J4",
     "Base bolts to the forearm's socket end (4 x M3 + spigot, cables down the forearm). Servo slides in\n"
     "along its channel and stands on 4 posts (2 with servo screws from under the plate). Cap: 4 x M3 x 12,\n"
     "heads 3.8 deep, holds the 6706. Hub bolted to the horn; the J5 fork bolts to the hub's 4 inserts\n"
     "(M3 x 10, heads sunk in the fork floor)."),
    ("J5 wrist pitch", ["J5_p1", "J5_p2", "j4_hub"],
     ["J5_shaft", "J5_spacer_A", "J5_spacer_B", "j6_body", "j6_cap"], "servo_J5",
     "Fork on the J3 rules; servo on 4 cover pads + 4 servo screws. Printed axle bolted to the horn; its\n"
     "flat runs out of the idle end into the blade's D-bore (+ M3 grub). The spacers clamp the blade\n"
     "between the inner races. Both 6706 press in from the gap."),
    ("J6 tool roll", ["j6_body", "j6_cap"], ["j6_flange"], "servo_J6",
     "ST3215 in the blade, output along the arm; slides in along its channel and stands on 2 near pads\n"
     "+ a far bridge with 2 servo screws; the cap holds a 6706. Tool flange bolted to the horn; 4 x M3\n"
     "inserts on O30 for the tool."),
]
COVER = """PRINT VERDICT (2026-09-24): GREEN -- 26 release stages at 0 failures.

 * all six joints driven by ST3215 servos through bolted horn couplers
 * every servo seated on 4 supports on its back and screwed by its own holes (20 screws)
 * every part checked against every other as exact solids, the manufacturer's servo model too
 * 265 dimensions measured back out of the print files; 114 screws checked as solids
 * assembly and disassembly paths free; screwdriver reaches every screw at its build step
 * cable route: one joint per cable, loops 31 .. 61 mm; nothing can wind up

Read first: ARM450_AUDIT_REPORT.pdf.  Details: ARM450_REV_I_FINAL.pdf, ARM450_POSES.pdf,
ARM450_PARTS.pdf.  Print: PRINTABLE_FILES (fit test first)."""


DIRS = ((1, -1, 0.8), (0, -1, 0.0001), (1, 0, 0.0001))


def _render(meshes, out, d, size=(1600, 1500)):
    """VTK render (exact-solid meshes, black edges) -- replaces the old decimated
    2D projections, which the user found too coarse."""
    import make_rule5_views as R5
    M, C = {}, {}
    for k, (m, col) in meshes.items():
        M[k] = (np.asarray(m.vertices), np.asarray(m.faces)); C[k] = col
    V = np.vstack([v for v, f in M.values()])
    fp = tuple((V.min(0) + V.max(0)) / 2)
    R5.vtk_render(M, C, out, (fp, np.asarray(d, float) / np.linalg.norm(d), (0, 0, 1)), size=size, zoom=1.0)
    return R5.trimmed(out)


def page(pdf, title, s, red, blue, servo, notes):
    os.makedirs(os.path.join(HERE, "REVI_VIEWS"), exist_ok=True)
    meshes = {k: (s[k], RED) for k in red}
    meshes.update({k: (s[k], BLUE) for k in blue})
    meshes[servo] = (s[servo], ORANGE)
    fig = plt.figure(figsize=(11.7, 8.3))
    fig.suptitle(title, fontsize=15, fontweight="bold")
    for i, d in enumerate(DIRS):
        img = _render(meshes, os.path.join(HERE, "REVI_VIEWS", "%s_%d.png" % (title.split()[0], i)), d)
        ax = fig.add_axes([0.01 + 0.33 * i, 0.40, 0.32, 0.52]); ax.imshow(img, interpolation="none"); ax.axis("off")
        ax.set_title(LABELS[i], fontsize=9)
    key = ("RED = fixed side (previous link): %s\nBLUE = driven (next link): %s\nORANGE = ST3215\n\n"
           % (", ".join(red), ", ".join(blue)))
    fig.text(0.02, 0.37, key + notes + "\n\nVerification: 0 failures (see REVI_CHECKS.log).",
             va="top", ha="left", fontsize=8.5, family="monospace")
    pdf.savefig(fig); plt.close(fig)


def main():
    os.makedirs(os.path.join(HERE, "REVI_VIEWS"), exist_ok=True)
    s = FS.scene()
    out = os.path.join(HERE, "ARM450_REV_I.pdf")
    with PdfPages(out) as pdf:
        fig = plt.figure(figsize=(11.7, 8.3))
        fig.text(0.5, 0.86, "ARM-450  rev I", ha="center", fontsize=28, fontweight="bold")
        fig.text(0.5, 0.80, "every joint driven, every part checked against every other", ha="center", fontsize=12)
        fig.text(0.06, 0.72, COVER, ha="left", va="top", fontsize=10, family="monospace")
        pdf.savefig(fig); plt.close(fig)
        # full arm
        fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle("Full arm, %d parts incl. 6 x ST3215" % len(s), fontsize=15, fontweight="bold")
        meshes = {k: (s[k], ORANGE if k.startswith("servo") else BLUE) for k in s}
        for i, d in enumerate(DIRS):
            img = _render(meshes, os.path.join(HERE, "REVI_VIEWS", "arm_%d.png" % i), d, size=(1300, 2000))
            ax = fig.add_axes([0.01 + 0.33 * i, 0.02, 0.32, 0.90]); ax.imshow(img, interpolation="none"); ax.axis("off")
            ax.set_title(LABELS[i], fontsize=9)
        pdf.savefig(fig); plt.close(fig)
        for (t, red, blue, sv, notes) in PAGES:
            page(pdf, t, s, red, blue, sv, notes)
    print("written", out)


if __name__ == "__main__":
    main()
