#!/usr/bin/env python3
"""
Rule 5 picture of the rev I.1 J3 spring-lug fix (user's slicer view,
2026-09-27: "joints at indicated areas need rectification").

Sections through each lug in the cheek's own plane (world y = +-20.75), the
released rev-I part next to the new one, both zoomed on the joint, plus 3D
close-ups. Every number is measured here from the solids.

Out: RULE6_VIEWS/j3_lug_fix.png (300 dpi) + .pdf (vector)
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt            # noqa: E402
import cadquery as cq                      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import make_rule5_views as R5              # noqa: E402
import spring_parts as SP                  # noqa: E402

OLD = os.path.join(HERE, "..", "RELEASES", "2026-09-24_rev_I", "EDITABLE_CAD", "parts_step", "12_J3_p1_x1.step")
NEW = os.path.join(HERE, "J3_p1.step")
OUT = os.path.join(HERE, "RULE6_VIEWS", "j3_lug_fix")
YW = SP.PIN_Y - 3.75                        # lug mid-thickness, |world y|


def area(t):
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    g = GProp_GProps(); BRepGProp.SurfaceProperties_s(t, g)
    return g.Mass()


def joints():
    """joint area of the old and the new lug on the same cheek body."""
    import gen_drive_j3 as G
    import drive_common as DC
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
    FK = G.FK
    s = FK.fork(**G.KW)
    s = s.cut(cq.Workplane("XY").rect(400, 400).extrude(400).translate((0, 0, G.P)))
    s = DC.split_bolts(s, G.P, G.Z_IN, G.Z_DRIVE, "p1")
    s = DC.p1_floor_cuts(s, G.Z_BRG_OUT, G.P)
    body = DC.open_drive_pocket(s, G.Z_IN, FK.SEAT_T, G.BRG_OD).val().wrapped
    loc = lambda w: w.translate((0, 0, -209.0)).rotate((0, 0, 0), (1, 1, 1), 120).val().wrapped
    old_base = {1: 246.8, -1: 233.9}                     # rev I: base at the arc's apex
    out = {}
    for sy in (1, -1):
        o = SP._box(-SP.LUG_X, SP.LUG_X, SP.PIN_Y - 7.5, SP.PIN_Y, old_base[sy], 263.0)
        o = o.mirror("XZ") if sy < 0 else o
        n = SP.lug(sy, None, SP.J3_AXIS_Z + SP.A3, cheek=SP.J3_CHEEK[sy])
        for tag, w in (("old", o), ("new", n)):
            t = loc(w)
            out[(sy, tag)] = (area(body) + area(t) - area(BRepAlgoAPI_Fuse(body, t).Shape())) / 2
    return out


def section(path, sy):
    sh = cq.importers.importStep(path).val().wrapped
    # part frame = fork local: x = world z - 209, y = world x, z = world y
    g = R5.section2d(sh, (0, 0, sy * YW), (0, 0, 1), 1, 0)
    return g


def main():
    J = joints()
    fig = plt.figure(figsize=(16.5, 17.0))
    fig.suptitle("J3 fork p1 -- spring lugs on the round cheek tops: rev I (released) vs rev I.1 (fixed)\n"
                 "section in the cheek plane through each lug (world y = %+.2f / %+.2f), world x across, world z up"
                 % (YW, -YW), fontsize=14, fontweight="bold")
    for r, sy in enumerate((1, -1)):
        zc, R, zfloor = SP.J3_CHEEK[sy]
        apex = zc + R
        for c, (tag, path) in enumerate((("rev I (released)", OLD), ("rev I.1 (fixed)", NEW))):
            ax = fig.add_axes([0.06 + 0.48 * c, (0.60, 0.30)[r], 0.42, 0.28])
            g = section(path, sy)
            geoms = getattr(g, "geoms", [g])
            for p in geoms:
                x, z = p.exterior.xy
                ax.fill(x, np.array(z) + 209.0, color="#7fb3e6" if c else "#e6a07f", ec="k", lw=0.8)
                for h in p.interiors:
                    hx, hz = h.xy
                    ax.fill(hx, np.array(hz) + 209.0, color="white", ec="k", lw=0.6)
            t = np.linspace(np.radians(40), np.radians(140), 400)
            ax.plot(R * np.cos(t), zc + R * np.sin(t), color="#555555", lw=0.8, ls="--", label="cheek arc R %.0f" % R)
            ax.axvline(-SP.LUG_X, color="#999999", lw=0.5, ls=":"); ax.axvline(SP.LUG_X, color="#999999", lw=0.5, ls=":")
            z_edge = zc + np.sqrt(R ** 2 - SP.LUG_X ** 2)
            if c == 0:
                base = {1: 246.8, -1: 233.9}[sy]
                ax.annotate("lug base z %.2f\narc apex %.2f\njoined by a\n%.2f mm sliver" % (base, apex, apex - base),
                            (0, base), xytext=(-13.5, base + 2.0), fontsize=10, color="#b00000",
                            arrowprops=dict(arrowstyle="->", color="#b00000", lw=1.0))
                ax.annotate("corner\n%.2f mm\nin the air" % (base - z_edge), (SP.LUG_X, (base + z_edge) / 2),
                            xytext=(8.0, base + 1.5), fontsize=10, color="#b00000",
                            arrowprops=dict(arrowstyle="->", color="#b00000", lw=1.0))
            else:
                zb = max(z_edge - SP.EMBED, zfloor)
                ax.annotate("sunk %.1f mm below the arc\nat the lug edges (base z %.2f)" % (z_edge - zb, zb),
                            (-SP.LUG_X + 0.5, zb), xytext=(-13.5, zb - 5.0), fontsize=10, color="#004080",
                            arrowprops=dict(arrowstyle="->", color="#004080", lw=1.0))
                ax.annotate("R %.0f concave web" % SP.FILLET_R, (SP.LUG_X + 0.9, z_edge + 0.9), xytext=(7.0, z_edge + 6.0),
                            fontsize=10, color="#004080", arrowprops=dict(arrowstyle="->", color="#004080", lw=1.0))
            ax.set_xlim(-14, 14); ax.set_ylim(apex - 9, apex + 7)
            ax.set_aspect("equal"); ax.grid(True, lw=0.3)
            ax.set_xlabel("world x (mm)"); ax.set_ylabel("world z (mm)")
            ax.set_title("%s -- %s lug (%s cheek)\njoint area %.1f mm2 (lug section 10 x 7.5 = 75 mm2)"
                         % (tag, "+y" if sy > 0 else "-y", "drive" if sy > 0 else "idle", J[(sy, "old" if c == 0 else "new")]),
                         fontsize=11)
            ax.legend(fontsize=8, loc="lower right")
    # 3D close-ups
    for c, (tag, path) in enumerate((("rev I (released)", OLD), ("rev I.1 (fixed)", NEW))):
        sh = cq.importers.importStep(path).val().wrapped
        m = {"p": R5.tess(sh, 0.02, 0.1)}
        png = OUT + "_3d_%d.png" % c
        R5.vtk_render(m, {"p": "#e6a07f" if c == 0 else "#7fb3e6"}, png,
                      ((40.0, 0.0, 0.0), (0.5, 1.0, -0.9), (1, 0, 0)), size=(1400, 1000), scale=33.0)
        ax = fig.add_axes([0.06 + 0.48 * c, 0.01, 0.42, 0.24])
        ax.imshow(R5.trimmed(png), interpolation="none"); ax.axis("off")
        ax.set_title(tag + " -- both lugs, 3D", fontsize=11)
    fig.savefig(OUT + ".png", dpi=300); fig.savefig(OUT + ".pdf")
    print("wrote", OUT + ".png / .pdf")
    for k, v in sorted(J.items()):
        print("   lug %+d %s joint area %.1f mm2" % (k[0], k[1], v))


if __name__ == "__main__":
    main()
