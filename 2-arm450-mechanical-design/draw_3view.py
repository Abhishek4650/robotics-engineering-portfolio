"""
Three-view orthographic sheets for every ARM-450 part.

Each sheet: FRONT / TOP / RIGHT in third-angle layout, hidden detail dashed,
overall dimensions on each view, plus the diameters the STEP actually contains.
"""
import os
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad"))
from params import *          # noqa: F403,F401
import orthodraw as OD
import audit_parts as AP

CAD, OUT = "output/cad", "figures/3view"
os.makedirs(OUT, exist_ok=True)
DIMC, INK, BAD = "#1b4f72", "#12202e", "#a4243b"

PARTS = ["link_half_tongue", "link_half_groove", "shaft_clamp", "servo_collar",
         "wrist_j4_housing", "wrist_j5_yoke", "wrist_j6_output",
         "turret_j1", "base", "horn_adapter", "shaft_tube", "fit_coupon",
         # end effectors -- the arm side stays on, the tools come and go
         "tool_adapter", "tool_gripper", "gripper_jaw", "gripper_pinion",
         "tool_dock", "dock_target", "dock_target_sealed"]

TITLE = {
    "link_half_tongue": "LINK HALF — TONGUE SIDE",
    "link_half_groove": "LINK HALF — GROOVE SIDE",
    "shaft_clamp": "SHAFT CLAMP (SPLIT)",
    "servo_collar": "SERVO COLLAR",
    "wrist_j4_housing": "J4 ROLL HOUSING",
    "wrist_j5_yoke": "J5 PITCH YOKE",
    "wrist_j6_output": "J6 OUTPUT / TOOL FLANGE",
    "turret_j1": "J1 TURRET",
    "base": "BASE PEDESTAL",
    "horn_adapter": "SERVO HORN ADAPTER",
    "shaft_tube": "JOINT SHAFT — AL TUBE",
    "fit_coupon": "FIT-TEST COUPON",
    "tool_adapter": "TOOL ADAPTER — ARM SIDE OF THE BAYONET",
    "tool_gripper": "GRIPPER BODY — SG90 PARALLEL JAW",
    "gripper_jaw": "GRIPPER JAW (PRINT 2, ONE MIRRORED)",
    "gripper_pinion": "GRIPPER PINION",
    "tool_dock": "DOCKING PROBE",
    "dock_target": "DOCKING TARGET PORT (BENCH TEST)",
    "dock_target_sealed": "DOCKING TARGET PORT — SEALED, FOR FLUID",
}


def dim_h(ax, x0, x1, y, text, col=DIMC, fs=7.6, tick=1.6):
    ax.annotate("", (x0, y), (x1, y),
                arrowprops=dict(arrowstyle="<->", color=col, lw=0.7,
                                shrinkA=0, shrinkB=0))
    for x in (x0, x1):
        ax.plot([x, x], [y - tick, y + tick], color=col, lw=0.5)
    ax.text((x0 + x1) / 2, y + tick * 1.4, text, ha="center", va="bottom",
            fontsize=fs, color=col,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))


def dim_v(ax, y0, y1, x, text, col=DIMC, fs=7.6, tick=1.6):
    ax.annotate("", (x, y0), (x, y1),
                arrowprops=dict(arrowstyle="<->", color=col, lw=0.7,
                                shrinkA=0, shrinkB=0))
    for y in (y0, y1):
        ax.plot([x - tick, x + tick], [y, y], color=col, lw=0.5)
    ax.text(x + tick * 1.4, (y0 + y1) / 2, text, ha="left", va="center",
            rotation=90, fontsize=fs, color=col, rotation_mode="anchor",
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))


def sheet(name):
    m = trimesh.load(f"{CAD}/{name}.stl", force="mesh")
    m.vertices = m.vertices - m.bounds.mean(axis=0)
    ex = m.extents
    gap = max(ex) * 0.30 + 12.0
    fig, ax = plt.subplots(figsize=(13.0, 9.6))

    # third angle:  TOP above FRONT,  RIGHT to the right of FRONT
    fw, fh = ex[0], ex[2]            # FRONT  = X x Z
    tw, th = ex[0], ex[1]            # TOP    = X x Y
    rw, rh = ex[1], ex[2]            # RIGHT  = Y x Z
    o_front = (0.0, 0.0)
    o_top = (0.0, fh / 2 + gap + th / 2)
    o_right = (fw / 2 + gap + rw / 2, 0.0)

    boxes = {}
    for vname, org in (("FRONT", o_front), ("TOP", o_top), ("RIGHT", o_right)):
        boxes[vname] = OD.draw_view(ax, m, vname, origin=org)

    for vname, org, w, h in (("FRONT", o_front, fw, fh),
                             ("TOP", o_top, tw, th),
                             ("RIGHT", o_right, rw, rh)):
        lo, hi = boxes[vname]
        ax.text((lo[0] + hi[0]) / 2, lo[1] - max(ex) * 0.16, vname,
                ha="center", va="top", fontsize=9.5, color=INK,
                fontweight="bold")
        dim_h(ax, lo[0], hi[0], hi[1] + max(ex) * 0.055, f"{w:.2f}",
              tick=max(ex) * 0.012)
        dim_v(ax, lo[1], hi[1], hi[0] + max(ex) * 0.055, f"{h:.2f}",
              tick=max(ex) * 0.012)

    # centre lines through the FRONT view
    lo, hi = boxes["FRONT"]
    ax.plot([lo[0] - 6, hi[0] + 6], [0, 0], color=DIMC, lw=0.45,
            ls=(0, (9, 3, 1.5, 3)), alpha=0.8)
    ax.plot([0, 0], [lo[1] - 6, hi[1] + 6], color=DIMC, lw=0.45,
            ls=(0, (9, 3, 1.5, 3)), alpha=0.8)

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"{TITLE[name]}   —   third-angle projection",
                 fontsize=13, color=INK, fontweight="bold", pad=12)
    return fig, ax, m


def table(ax, name, m):
    """Everything the STEP actually contains, so the sheet cannot overstate it."""
    cyl = AP.cylinders(f"{CAD}/{name}.step")
    seen, rows = set(), []
    for g in sorted(cyl, key=lambda g: -g["dia"]):
        d = round(g["dia"], 2)
        if d in seen or d < 2.0:
            continue
        seen.add(d)
        n = sum(1 for h in cyl if abs(h["dia"] - d) < 0.02)
        ax_l = "XYZ"[int(np.argmax(np.abs(g["d"])))]
        rows.append(f"  Ø{d:7.2f} × {n:<2d} axis {ax_l}   depth {g['depth']:6.2f}")
    ex = m.extents
    txt = (f"{name}.stl\n"
           f"  envelope {ex[0]:.2f} × {ex[1]:.2f} × {ex[2]:.2f}\n\n"
           f"  CYLINDRICAL FEATURES IN THE STEP:\n" + "\n".join(rows[:11]))
    ax.text(0.008, 0.008, txt, transform=ax.transAxes, family="monospace",
            fontsize=7.0, va="bottom", ha="left", color="#33414f", zorder=9,
            bbox=dict(boxstyle="round,pad=0.45", fc="#f8fafb", ec="#c8d2dc", lw=0.7))
    # Bearing-pocket stamp, read from the STEP -- NOT from a hardcoded list.
    # This banner used to name link_half_tongue / link_half_groove / base
    # unconditionally, from the audit that first found the pockets missing.
    # They were fixed on 2026-08-21 and the banner went on claiming the defect,
    # in bold red, on the very sheets someone prints from. A drawing that
    # asserts a feature the part does not have is the defect the J6 pilot
    # taught us to fear; a drawing that asserts a DEFECT the part no longer has
    # is the same error pointing the other way. Ask the geometry instead.
    if name in ("link_half_tongue", "link_half_groove", "base",
                "turret_j1", "wrist_j4_housing", "wrist_j5_yoke",
                "wrist_j6_output"):
        pk = [g for g in cyl if abs(g["dia"] - BRG_OD) < 0.30
              and abs(g["depth"] - BRG_W) < 1.5]
        ok = len(pk) > 0
        ax.text(0.99, 0.99,
                (f"Ø{BRG_OD:.2f} × {BRG_W:.2f} BEARING POCKET — {len(pk)} PRESENT"
                 if ok else f"NO Ø{BRG_OD:.2f} BEARING POCKET — see ARM450_AUDIT.pdf"),
                transform=ax.transAxes, ha="right", va="top", fontsize=10.5,
                fontweight="bold", color=("#1e6b45" if ok else BAD), zorder=10,
                bbox=dict(boxstyle="round,pad=0.4", fc="white",
                          ec=("#1e6b45" if ok else BAD), lw=1.4))


def main():
    print("THREE-VIEW ORTHOGRAPHIC SHEETS  (third angle, hidden detail dashed)")
    for n in PARTS:
        fig, ax, m = sheet(n)
        table(ax, n, m)
        ax.autoscale()
        ax.margins(0.06)
        y0, y1 = ax.get_ylim()
        ax.set_ylim(y0 - (y1 - y0) * 0.30, y1)          # band for the table
        fig.tight_layout()
        p = f"{OUT}/{n}.png"
        fig.savefig(p, dpi=135, facecolor="white")
        plt.close(fig)
        print(f"  wrote {p}")


if __name__ == "__main__":
    main()
