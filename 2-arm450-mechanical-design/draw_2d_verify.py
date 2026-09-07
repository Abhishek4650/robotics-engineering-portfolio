"""
2-D VERIFICATION SECTIONS — cut through every joint interface so the bearing
seats can be checked by eye against the numbers.

One sheet per part: a true cross-section taken through the bearing axis, with
every diameter the section actually crosses measured off the STEP and labelled.
Nothing here is typed in by hand -- if the part does not contain a feature, no
label appears for it.

This exists because the pre-print gate checked the PARAMETER (BRG_OD + BRG_FIT
== 42.00) and never checked the GEOMETRY, so it passed 55/55 on parts whose
bearing pockets had been swallowed by an earlier cut.
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
import audit_parts as AP

CAD = "output/cad"
OUT = "figures/verify"
os.makedirs(OUT, exist_ok=True)
INK, DIM, BAD, GOOD = "#12202e", "#1b4f72", "#a4243b", "#1d6f42"

# part -> (section plane normal, plane origin, title, subtitle)
SECTIONS = {
    "link_half_tongue": ([1, 0, 0], [0, 0, 0], "LINK HALF (tongue) — section through the end boss",
                         "the J2/J3 bearing seat"),
    "link_half_groove": ([1, 0, 0], [0, 0, 0], "LINK HALF (groove) — section through the end boss",
                         "the J2/J3 bearing seat"),
    "base":             ([0, 1, 0], [0, 0, 0], "BASE — section through the J1 axis",
                         "the J1 turret bearing seat"),
    "turret_j1":        ([0, 0, 1], [0, 0, 40], "J1 TURRET — section through the bearing axis", ""),
    "wrist_j4_housing": ([1, 0, 0], [0, 0, 0], "J4 ROLL HOUSING — section through the bearing axis", ""),
    "wrist_j5_yoke":    ([0, 0, 1], [0, 0, 12], "J5 PITCH YOKE — section through the bearing axis",
                         "both cheeks"),
    "wrist_j6_output":  ([1, 0, 0], [0, 0, 0], "J6 OUTPUT — section through the bearing axis", ""),
    "shaft_clamp":      ([1, 0, 0], [0, 0, 0], "SHAFT CLAMP — section through the bore", ""),
    "shaft_tube":       ([1, 0, 0], [0, 0, 0], "JOINT SHAFT — section through the tube", ""),
    "horn_adapter":     ([0, 1, 0], [0, 0, 0], "SERVO HORN ADAPTER — section through the bore",
                         "closes the torque path: horn -> adapter -> roll pin -> tube"),
}


def section(mesh, normal, origin):
    """Project the section onto axes I choose, not the arbitrary frame
    to_planar() picks. Without this the view orientation changes part to part
    and the section can come out degenerate."""
    sec = mesh.section(plane_origin=origin, plane_normal=normal)
    if sec is None:
        return None
    n = np.array(normal, float)
    n = n / np.linalg.norm(n)
    # in-plane axes: prefer world +Z up whenever the cut is not perpendicular to it
    up = np.array([0, 0, 1.0])
    if abs(n @ up) > 0.9:
        up = np.array([0, 1.0, 0])
    v = up - n * (up @ n)
    v = v / np.linalg.norm(v)
    u = np.cross(v, n)
    segs = []
    for ent in sec.entities:
        p3 = sec.vertices[ent.points]
        segs.append(np.stack([p3 @ u, p3 @ v], axis=-1))
    return segs


def draw(name):
    normal, origin, title, sub = SECTIONS[name]
    m = trimesh.load(f"{CAD}/{name}.stl", force="mesh")
    P = section(m, normal, origin)
    if P is None:
        print(f"  {name}: no section"); return
    fig, ax = plt.subplots(figsize=(11.0, 6.8))
    for pts in P:
        ax.plot(pts[:, 0], pts[:, 1], color=INK, lw=1.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title + (f"\n{sub}" if sub else ""), fontsize=12.0,
                 color=INK, fontweight="bold", pad=10)
    return fig, ax, P


# what each part's bearing interface is SUPPOSED to be
EXPECT = {
    "link_half_tongue": (42.0, 38.0, "bearing pocket / shoulder"),
    "link_half_groove": (42.0, 38.0, "bearing pocket / shoulder"),
    "base": (42.0, None, "J1 bearing seat"),
    "turret_j1": (42.0, 38.0, "bearing pocket / shoulder"),
    # The wrist runs 6706 (Ø37 x 4), not the 6806 used at J1/J2/J3.
    "wrist_j4_housing": (37.0, 33.0, "6706 pocket / shoulder"),
    "wrist_j5_yoke": (37.0, 33.0, "6706 pocket / shoulder"),
    "wrist_j6_output": (37.0, 33.0, "6706 pocket / shoulder"),
    "shaft_clamp": (38.0, 30.2, "clamp OD / shaft bore"),
    "shaft_tube": (30.0, 26.0, "tube OD / bore"),
    "horn_adapter": (36.0, 30.2, "hub OD / tube bore"),
}


def annotate(ax, name, cyl):
    """Label the diameters this part really contains, near the bearing axis."""
    want_pocket, want_bore, label = EXPECT[name]
    dias = sorted({round(g["dia"], 2) for g in cyl if g["dia"] > 18.0},
                  reverse=True)
    got_pocket = any(abs(d - want_pocket) < 0.06 for d in dias)
    lines = [f"{label}", ""]
    lines.append(f"  intended pocket   Ø{want_pocket:.2f}")
    if want_bore:
        lines.append(f"  intended shoulder Ø{want_bore:.2f}")
    lines.append("")
    lines.append("  FOUND in the STEP (Ø > 18):")
    for d in dias[:7]:
        tag = ""
        if abs(d - want_pocket) < 0.06:
            tag = "   <- the pocket"
        elif want_bore and abs(d - want_bore) < 0.06:
            tag = "   <- the shoulder"
        lines.append(f"    Ø{d:7.2f}{tag}")
    col = GOOD if got_pocket else BAD
    verdict = ("POCKET PRESENT" if got_pocket else
               f"NO Ø{want_pocket:.2f} POCKET IN THIS PART")
    ax.text(0.015, 0.015, "\n".join(lines), transform=ax.transAxes,
            family="monospace", fontsize=8.0, va="bottom", ha="left",
            color="#33414f", zorder=8,
            bbox=dict(boxstyle="round,pad=0.5", fc="#f8fafb",
                      ec="#c8d2dc", lw=0.7))
    ax.text(0.985, 0.97, verdict, transform=ax.transAxes, ha="right",
            va="top", fontsize=11.5, fontweight="bold", color=col, zorder=9,
            bbox=dict(boxstyle="round,pad=0.42", fc="white", ec=col, lw=1.4))
    return got_pocket


def main():
    print("2-D VERIFICATION SECTIONS")
    bad = []
    for name in SECTIONS:
        r = draw(name)
        if r is None:
            continue
        fig, ax, _ = r
        ax.margins(0.28)
        cyl = AP.cylinders(f"{CAD}/{name}.step")
        ok = annotate(ax, name, cyl)
        if not ok:
            bad.append(name)
        fig.tight_layout()
        p = f"{OUT}/{name}.png"
        fig.savefig(p, dpi=140, facecolor="white")
        plt.close(fig)
        print(f"  {'ok  ' if ok else 'FAIL'}  {p}")
    print(f"\n  {len(SECTIONS)-len(bad)}/{len(SECTIONS)} parts have their intended seat")
    for b in bad:
        print(f"    NO SEAT: {b}")


if __name__ == "__main__":
    main()
