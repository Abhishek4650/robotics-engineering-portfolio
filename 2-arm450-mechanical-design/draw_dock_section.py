"""
Section through the docking latch — insert, then latched.

The latch is the one feature of this design that cannot be shown in an
isometric: it is inside a bore. It is also the feature that was WRONG — the
lugs floated 5.5 mm clear of the wall, the target's groove had severed its own
spigot tip, and the cone was deeper than the spigot was long. A section is the
only view in which any of that is visible, which is a large part of why none of
it was caught by looking.

Both states are cut through a lug centre: the probe's three lugs sit at 0/120/
240 deg, so the LATCHED state is drawn with the whole scene rolled back 30 deg
to keep the same lug in the cutting plane.
"""
import os
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad"))
import end_effector as EE

CAD, OUT = "output/cad", "figures"
INK, DIMC, PROBE_C, TARG_C = "#12202e", "#1b4f72", "#8fa9c2", "#c9a227"


def section(mesh):
    """Section in the X-Z plane.

    ALWAYS cut at 0 deg, never at the roll angle. The probe's three lugs are
    fixed at 0/120/240; rolling the CUTTING PLANE with the target takes the lug
    out of the section, and the latched panel then draws identically to the
    seated one -- which is exactly the picture that would have let the original
    floating-lug defect through again.
    """
    m = mesh.copy()
    sec = m.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
    if sec is None:
        return []
    p2, T = sec.to_2D()
    out = []
    for e in p2.entities:
        v = np.asarray(e.discrete(p2.vertices))
        # to_2D puts the plane's own axes in (u, v); recover world (x, z)
        w = trimesh.transform_points(np.column_stack([v, np.zeros(len(v))]), T)
        out.append(w[:, [0, 2]])
    return out


def draw(ax, loops, fc, ec, label=None):
    for k, w in enumerate(loops):
        ax.add_patch(Polygon(w, closed=True, facecolor=fc, edgecolor=ec,
                             lw=1.1, alpha=0.92, zorder=2,
                             label=label if k == 0 else None))


def panel(ax, roll, gap, title, sub, note=None):
    P = trimesh.load(f"{CAD}/tool_dock.stl", force="mesh")
    T = trimesh.load(f"{CAD}/dock_target.stl", force="mesh")
    T.apply_transform(trimesh.transformations.rotation_matrix(
        np.radians(roll), [0, 0, 1]))
    T.apply_translation([0, 0, EE.SEAT_DZ - EE.FLANGE_H - gap])
    draw(ax, section(T), TARG_C, "#7d6416", "target")
    draw(ax, section(P), PROBE_C, "#31506e", "probe")
    ax.axhline(0, color=DIMC, lw=0.45, ls=(0, (9, 3, 1.5, 3)), alpha=0.5)
    ax.axvline(0, color=DIMC, lw=0.45, ls=(0, (9, 3, 1.5, 3)), alpha=0.5)
    if note is not None:
        txt, xy, xyt = note
        ax.annotate(txt, xy=xy, xytext=xyt, fontsize=8.2, color="#8a5a12",
                    ha="left", va="center", zorder=6,
                    arrowprops=dict(arrowstyle="-", color="#8a5a12", lw=0.9))
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"{title}\n{sub}", fontsize=10.5, color=INK,
                 fontweight="bold", pad=8, linespacing=1.9)
    ax.set_xlim(-27, 27); ax.set_ylim(-36, 26)


def main():
    os.makedirs(OUT, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 7.2))
    lugz = (EE.LATCH_Z0 + EE.LATCH_Z1) / 2
    panel(axes[0], 0.0, 12.0, "1 — APPROACH",
          f"the Ø{EE.DOCK_MOUTH:.0f} mouth catches a Ø{2*EE.SPG_R:.2f} spigot\n"
          f"anywhere within ±9.75 mm")
    panel(axes[1], 0.0, 0.0, "2 — SEATED",
          f"lugs have passed the entry slots;\n"
          f"{-EE.SEAT_DZ - EE.DOCK_CONE_L:.0f} mm standoff at the flange",
          ("entry slot", (EE.SPG_R, lugz), (11.0, lugz + 9.0)))
    panel(axes[2], EE.DOCK_TWIST, 0.0,
          f"3 — LATCHED   J6 rolled {EE.DOCK_TWIST:.0f}°",
          "the lug is under the groove shoulder;\n"
          "pulling now catches",
          ("lug under\nthe shoulder", (EE.GRV_R, lugz), (11.0, lugz + 9.0)))
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower left", bbox_to_anchor=(0.012, 0.045),
               fontsize=8.6, frameon=True, framealpha=0.95)
    fig.suptitle("the capture project DOCKING LATCH — section through a lug centre",
                 fontsize=14, color=INK, fontweight="bold", y=0.995)
    fig.text(0.5, 0.022,
             f"Ø{EE.DOCK_MOUTH:.0f} mouth · Ø{EE.DOCK_THROAT:.0f} throat · "
             f"cone {EE.DOCK_CONE_L:.0f} deep · spigot {EE.SPG_H:.0f} · "
             f"groove {EE.GRV_DEPTH:.2f} deep leaving "
             f"{EE.GRV_R - EE.FLUID_BORE/2:.2f} mm of wall · "
             f"measured capture ±9.75 mm · no seventh actuator",
             ha="center", fontsize=8.6, color="#5a6b7b")
    fig.tight_layout(rect=(0, 0.055, 1, 0.905))
    p = os.path.join(OUT, "dock_latch_section.png")
    fig.savefig(p, dpi=155, facecolor="white")
    plt.close(fig)
    print(f"  wrote {p}")


if __name__ == "__main__":
    main()
