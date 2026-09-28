#!/usr/bin/env python3
"""ARM-450 rev I -- final PDF: assembly with all hardware, per-joint views and
SECTION SLICES through each joint (the manual check), print list, BOM, specs.
Colours: RED fixed side, BLUE driven link, BLACK servo, GREY bearing,
STEEL screws/bolts, BRASS inserts, SILVER springs."""
import glob
import json
import os
import sys

import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                        # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages   # noqa: E402
from matplotlib.patches import Polygon as MPoly        # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_report_pdf as R      # noqa: E402  (projection helpers)
import gen_wrist as W            # noqa: E402

MD = os.path.join(HERE, "_asm_meshes")
COL = {"fixed": "#c0392b", "driven": "#2471a3", "servo": "#1b1b1b", "bearing": "#8e959c",
       "screw": "#5d6d7e", "insert": "#c9a227", "spring": "#b8c4d0", "other": "#cfcfcf"}

JOINTS = {
    "J1 base yaw": dict(fixed=["base", "j1_mount"], driven=["j1_hub", "J2_turret_p1", "spigot_collar"],
                        servo="servo_J1", plane=((0, 0, 0), (0, 1, 0)), box=((-70, -70, -72), (70, 70, 60)),
                        axes=("x", "z")),
    "J2 shoulder": dict(fixed=["J2_turret_p1", "J2_turret_p2"], driven=["J2_shaft", "shaft_clamp_1", "shaft_clamp_2",
                        "link_upper_groove", "link_upper_tongue"], servo="servo_J2",
                        plane=((0, 0, 90.0), (0, 0, 1)), box=((-50, -70, 40), (50, 50, 140)), axes=("x", "y")),
    "J3 elbow": dict(fixed=["J3_p1", "J3_p2", "link_upper_groove", "link_upper_tongue"],
                     driven=["J3_shaft", "shaft_clamp_3", "shaft_clamp_4", "link_fore_tongue", "link_fore_groove"],
                     servo="servo_J3", plane=((0, 0, 0), (1, 0, 0)), box=((-50, -40, 160), (50, 70, 270)), axes=("y", "z")),
    "J4 forearm roll": dict(fixed=["j4_base", "j4_cap", "link_fore_tongue", "link_fore_groove"],
                            driven=["j4_hub", "J5_p1", "J5_p2"], servo="servo_J4",
                            plane=((0, 0, 0), (0, 1, 0)), box=((-40, -40, 310), (45, 40, 415)), axes=("x", "z")),
    "J5 wrist pitch": dict(fixed=["J5_p1", "J5_p2", "j4_hub"], driven=["J5_shaft", "J5_spacer_A", "J5_spacer_B",
                           "j6_body", "j6_cap"], servo="servo_J5", plane=((0, 0, 0), (1, 0, 0)),
                           box=((-40, -40, 400), (40, 70, 475)), axes=("y", "z")),
    "J6 tool roll": dict(fixed=["j6_body", "j6_cap"], driven=["j6_flange"], servo="servo_J6",
                         plane=((0, 0, 0), (0, 1, 0)), box=((-30, -30, 440), (45, 30, 525)), axes=("x", "z")),
}


def category(name, jd):
    if name.startswith("servo"):
        return "servo"
    if name.startswith("brg"):
        return "bearing"
    if name.startswith("spring"):
        return "spring"
    if "_ins" in name or name.startswith("foot_ins") or name.startswith("tool_ins"):
        return "insert"
    if any(name.startswith(p) for p in ("horn_screw", "split_", "cap_", "j4base", "j5fork", "j3fork", "m4_",
                                        "collar_pinch", "j5_grub", "pin_", "collar_clamp", "collar_nut", "servo_scr")):
        return "screw"
    if name in jd["driven"]:
        return "driven"
    if name in jd["fixed"]:
        return "fixed"
    return "other"


def load_all():
    ms = {}
    for f in glob.glob(os.path.join(MD, "*.stl")):
        ms[os.path.basename(f)[:-4]] = trimesh.load(f)
    return ms


def in_box(m, box):
    lo, hi = np.array(box[0]), np.array(box[1])
    return not ((m.bounds[1] < lo).any() or (m.bounds[0] > hi).any())


def section_page(pdf, title, ms, jd):
    o, n = np.array(jd["plane"][0], float), np.array(jd["plane"][1], float)
    ax_idx = {"x": 0, "y": 1, "z": 2}
    i0, i1 = ax_idx[jd["axes"][0]], ax_idx[jd["axes"][1]]
    fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle(title + " -- SECTION (manual check by slicing)", fontsize=14, fontweight="bold")
    ax = fig.add_axes([0.05, 0.08, 0.62, 0.84])
    order = ["other", "fixed", "driven", "bearing", "servo", "spring", "insert", "screw"]
    items = sorted(((category(k, jd), k, m) for k, m in ms.items() if in_box(m, jd["box"])), key=lambda t: order.index(t[0]))
    shown = set()
    for cat, k, m in items:
        sl = m.section(plane_origin=o, plane_normal=n)
        if sl is None:
            continue
        for ent in sl.discrete:
            pts = np.asarray(ent)[:, [i0, i1]]
            if len(pts) < 3:
                continue
            ax.add_patch(MPoly(pts, closed=True, facecolor=COL[cat], edgecolor="k", lw=0.25,
                               alpha=0.35 if cat in ("fixed", "driven", "other") else 0.9))
        shown.add(cat)
    b = jd["box"]
    ax.set_xlim(b[0][i0], b[1][i0]); ax.set_ylim(b[0][i1], b[1][i1]); ax.set_aspect("equal")
    ax.set_xlabel("%s (mm)" % jd["axes"][0]); ax.set_ylabel("%s (mm)" % jd["axes"][1]); ax.grid(alpha=0.2)
    axl = fig.add_axes([0.70, 0.08, 0.28, 0.84]); axl.axis("off")
    from matplotlib.patches import Patch
    lab = {"fixed": "fixed side (previous link)", "driven": "driven link (next)", "servo": "ST3215",
           "bearing": "bearing", "screw": "screw / bolt / nut", "insert": "heat-set insert",
           "spring": "gravity spring", "other": "other"}
    axl.text(0.0, 1.0, "Cut plane: point (%g, %g, %g)\nnormal (%g, %g, %g)" % (*map(float, o), *map(float, n)),
             va="top", family="monospace", fontsize=9)
    axl.legend(handles=[Patch(facecolor=COL[c], edgecolor="k", label=lab[c]) for c in order if c in shown],
               loc="upper left", bbox_to_anchor=(0.0, 0.9), frameon=False, fontsize=9)
    pdf.savefig(fig); plt.close(fig)


def view_page(pdf, title, ms, jd, notes):
    fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle(title, fontsize=15, fontweight="bold")
    meshes = [(m, COL[category(k, jd)], 0.85 if category(k, jd) in ("servo", "screw", "bearing", "insert", "spring") else 0.4)
              for k, m in ms.items() if in_box(m, jd["box"])]
    for i, (el, az, lb) in enumerate(((22, -60, "isometric"), (0, 0, "side"), (0, -90, "front"))):
        ax = fig.add_subplot(2, 3, i + 1)
        for m, _, _ in meshes:
            m._proj = R.project(m, el, az)
        for m, c, a in meshes:
            R.draw(ax, m, c, a, stride=max(1, len(m.faces) // 6000))
        R.frame(ax, meshes); ax.set_title(lb, fontsize=9)
    axt = fig.add_subplot(2, 1, 2); axt.axis("off")
    axt.text(0.01, 0.97, notes, va="top", fontsize=9, family="monospace", transform=axt.transAxes)
    pdf.savefig(fig); plt.close(fig)


def text_page(pdf, title, body, fs=8.5):
    fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle(title, fontsize=15, fontweight="bold")
    fig.text(0.05, 0.92, body, va="top", family="monospace", fontsize=fs)
    pdf.savefig(fig); plt.close(fig)


NOTES = {
    "J1 base yaw": "Servo slides into the foot's -0.22 mm pinch channel against a locating wall; cap face under the lips.\n"
                   "Hub bolted to the horn (4 x M2.5, BCD 14, from above), D-plug keys the turret spigot. No grubs.\n"
                   "Base: lower 6806 presses up from underneath; collar (1 x M3 pinch) preloads its INNER race only.",
    "J2 shoulder": "Servo in the turret's servo POD (2.4 mm shell all round), cap face on the parting plane; the pod\n"
                   "bolts to the turret with 4 x M3 x 45 into inserts. Printed shaft bolted to the horn (screws through\n"
                   "the shaft bore). Both 6806 press in from the fork gap. Each link half: C-clamp keyed by the seam ear,\n"
                   "M3 grub onto the shaft's D-flat. Springs: turret lugs -> upper-link collar (7.4 N / 12.4 N, x2).",
    "J3 elbow": "Same drive train as J2 (bay 34.99 deep, 2.4 back wall, 4 x M3 x 45); fork bolts to the upper\n"
                "link's socket end. Springs: fork lugs -> forearm collar (2.2 N / 5.0 N, x2).",
    "J4 forearm roll": "Base bolts to the forearm's socket end (4 x M3 + spigot, cables down the forearm).\n"
                       "Servo slides in; cap (counterbored bolts) holds the 6706; hub bolted to the horn from above;\n"
                       "the J5 fork bolts to the hub's inserts. Hub turns a full revolution clear.",
    "J5 wrist pitch": "Axle bolted to the horn, D-keys the blade + M3 grub (zero backlash). Spacers clamp the blade\n"
                      "between the inner races. Both 6706 press in from the gap. Blade swings +-93 deg clear.",
    "J6 tool roll": "ST3215 in the blade, output along the arm; slides in; cap holds a 6706.\n"
                    "Tool flange bolted to the horn from the tool side; standard 4 x M3 on O30 tool face.",
}


def main():
    import make_rule5_views as R5
    S = R5.load(); cols = R5.colours(S); cache = {}
    out = os.path.join(HERE, "ARM450_REV_I_FINAL.pdf")
    with PdfPages(out) as pdf:
        text_page(pdf, "ARM-450 rev I -- final design", open(os.path.join(HERE, "_final_cover.txt")).read(), 9.5)
        # Rule 5: exact solids, every part opaque in its own colour; exact
        # sections with overlaps red, contacts green, gaps measured
        R5.full_arm_page(pdf, S, cols, cache)
        for t, jd in JOINTS.items():
            R5.joint_pages(pdf, t, jd, S, cols, cache, NOTES[t])
        for fn, title in (("MATING_CHECK.log", "RULE 4 -- mate, never overlap: contacts, pathways, attachment (exact solids)"),
                          ("SECTION_MEASURE.md", "Manual check by slicing -- every pair measured in each joint's cut"),
                          ("CLAMP_CHECK.log", "Link lock J2/J3 -- M5 set screws on the double-D flats, centring rings, key access"),
                          ("DOF6_CHECK.log", "6 DOF -- axes measured twice, Jacobian rank"),
                          ("TOOL_ACCESS.log", "Tool access -- a hex key reaches every screw at its build step"),
                          ("FASTENER_CHECK.log", "Every fastener as a solid: free, engaged, seated, tip clear"),
                          ("PARAM_AUDIT.md", "Parameter -> CAD audit (generator value vs measured file)"),
                          ("HARDWARE_BOM.md", "Bought hardware (counted from the placed assembly)"),
                          ("_print_page.txt", "Print list (FINAL_PRINT/STL_print_ready)")):
            p = os.path.join(HERE, fn)
            if os.path.exists(p):
                body = open(p).read()
                lines = body.splitlines()
                for k in range(0, len(lines), 62):
                    text_page(pdf, title + ("" if k == 0 else " (cont.)"), "\n".join(lines[k:k + 62]), 7.5)
    print("written", out)


if __name__ == "__main__":
    main()
