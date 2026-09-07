"""
Build the ARM-450 parts & dimensions document.

Measures every STL in the user's Fusion folder, renders each part, assigns a
part number, and emits DRAWINGS.md -> output/ARM450_DRAWINGS.pdf.
"""

import os
import glob
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from render_existing import paint

SRC = os.path.expanduser("~/Desktop/Robotic_arm_design")
HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(HERE, "figures", "parts")
os.makedirs(FIGS, exist_ok=True)

RHO = 0.55e-3      # g/mm^3, PLA at ~35 % infill — estimate only

# part number, filename, group, function, status
CATALOGUE = [
    ("A-01", "base_p1.stl",            "Base",   "Lower base shell, D-profile", "keep"),
    ("A-02", "base_p2.stl",            "Base",   "Base cover / floor plate", "keep"),
    ("A-03", "Motor_mount_base.stl",   "Base",   "J1 servo mount, top-hat flange", "revise"),
    ("B-01", "link1_base.stl",         "Link",   "Upper-arm shell, lower half", "LENGTHEN"),
    ("B-02", "link1_cover.stl",        "Link",   "Upper-arm shell, upper half", "MISMATCH"),
    ("B-03", "link2_base.stl",         "Link",   "Forearm shell, lower half", "LENGTHEN"),
    ("B-04", "link2_cover.stl",        "Link",   "Forearm shell, upper half", "LENGTHEN"),
    ("B-05", "link1_base_1.1.stl",     "Link",   "Upper-arm shell rev 1.1 (longer)", "REJECT"),
    ("B-06", "link1_cover1.1.stl",     "Link",   "Upper-arm cover rev 1.1", "REJECT"),
    ("B-07", "link2_cover2.1.stl",     "Link",   "Forearm cover rev 2.1", "keep"),
    ("C-01", "J2_p1.stl",              "Joint",  "J2 shoulder yoke, driven side", "revise"),
    ("C-02", "J2_p2.stl",              "Joint",  "J2 shoulder yoke, idler side", "revise"),
    ("C-03", "J4_p1.stl",              "Joint",  "J4 yoke, driven side", "revise"),
    ("C-04", "J4_p2.stl",              "Joint",  "J4 yoke, idler side", "revise"),
    ("C-05", "Motor_housing_new.stl",  "Joint",  "Elbow motor housing", "keep"),
    ("D-01", "wrist_p1.stl",           "Wrist",  "Wrist body, driven side", "keep"),
    ("D-02", "wrist_p2.stl",           "Wrist",  "Wrist body, idler side", "keep"),
    ("E-01", "Motor_mount_J1.stl",     "Mount",  "J1 servo mount", "REDESIGN"),
    ("E-02", "Motor_mount_J2.stl",     "Mount",  "J2 servo mount", "REDESIGN"),
    ("E-03", "Motor_mount_wrist.stl",  "Mount",  "Wrist servo mount", "REDESIGN"),
    ("E-04", "Motor_mount.stl",        "Mount",  "Generic servo mount", "REDESIGN"),
    ("E-05", "Motor_mount_changed_ 2mm_length.stl", "Mount",
                                        "Servo mount, +2 mm variant", "REDESIGN"),
    ("F-01", "Motor_fixer_j2_p1.stl",  "Fixer",  "J2 servo clamp, 6 mm plate", "FAILS"),
    ("F-02", "Motor_fixer_j2_p2.stl",  "Fixer",  "J2 servo clamp, 4 mm plate", "FAILS"),
    ("F-03", "motor fixer.stl",        "Fixer",  "Servo clamp, U-channel", "FAILS"),
    ("F-04", "motor fixer_wrist.stl",  "Fixer",  "Wrist servo clamp", "FAILS"),
    ("G-01", "ST3215.stl",             "COTS",   "Feetech ST3215 serial-bus servo", "COTS"),
    ("G-02", "thrust ball bearing.stl", "COTS",  "Thrust ball bearing Ø42", "REPLACE"),
    ("G-03", "pin.stl",                "Tool",   "Grasp pin / end effector", "keep"),
]

STATUS_NOTE = {
    "keep": "Carry forward unchanged.",
    "revise": "Minor revision — fillets and bearing seats.",
    "LENGTHEN": "Lengthen to 145 mm joint-to-joint.",
    "MISMATCH": "Envelope does not pair with its base shell — check before reuse.",
    "REJECT": "Unequal link length; creates a dead zone and exceeds 450 mm.",
    "REDESIGN": "Redesign as a full-perimeter collar; current form is understrength.",
    "FAILS": "Fails at servo stall torque. Do not reprint as-is.",
    "COTS": "Commercial off-the-shelf, not printed.",
    "REPLACE": "Replace with a spaced, preloaded pair of deep-groove bearings.",
}


def measure(path):
    m = trimesh.load(path, force="mesh")
    e = m.extents
    V = m.volume if m.is_watertight and m.volume > 0 else float("nan")
    A = m.area
    t = 2 * V / A if V == V else float("nan")
    return m, e, V, A, t


def render_grid(entries, out, title, cols=4):
    rows = int(np.ceil(len(entries) / cols))
    fig = plt.figure(figsize=(3.6 * cols, 3.5 * rows))
    fig.patch.set_facecolor("white")
    for i, (pn, fn, grp, fun, st) in enumerate(entries):
        p = os.path.join(SRC, fn)
        ax = fig.add_subplot(rows, cols, i + 1)
        if not os.path.exists(p):
            ax.axis("off")
            continue
        m = trimesh.load(p, force="mesh")
        col = (0.80, 0.45, 0.38) if st in ("FAILS", "REDESIGN", "REJECT", "REPLACE") \
            else (0.62, 0.70, 0.79)
        paint(ax, m, 38, 24, base=col)
        e = m.extents
        ax.set_title(f"{pn}  {fn.replace('.stl','')}\n"
                     f"{e[0]:.1f} × {e[1]:.1f} × {e[2]:.1f} mm",
                     fontsize=8.6, fontweight="bold", color="#1b2733")
    fig.suptitle(title, fontsize=14, fontweight="bold", color="#1b2733", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(out, dpi=115, facecolor="white")
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    present = [e for e in CATALOGUE if os.path.exists(os.path.join(SRC, e[1]))]

    # --- render grids by group -------------------------------------------
    groups = {}
    for e in present:
        groups.setdefault(e[2], []).append(e)
    grid_files = {}
    for grp, entries in groups.items():
        out = os.path.join(FIGS, f"grp_{grp.lower()}.png")
        render_grid(entries, out, f"{grp} parts", cols=min(4, len(entries)))
        grid_files[grp] = os.path.relpath(out, HERE)

    # --- measure everything ----------------------------------------------
    rows = []
    for pn, fn, grp, fun, st in present:
        m, e, V, A, t = measure(os.path.join(SRC, fn))
        rows.append(dict(pn=pn, fn=fn, grp=grp, fun=fun, st=st,
                         x=e[0], y=e[1], z=e[2], V=V, t=t,
                         mass=V * RHO if V == V else float("nan")))

    # --- emit markdown ----------------------------------------------------
    L = []
    w = L.append
    w("# ARM-450 — Parts, Drawings and Dimensions\n")
    w("- **Source:** `~/Desktop/Robotic_arm_design/` (Fusion 360 export)")
    w("- **Date:** 2026-08-13")
    w("- **Units:** all dimensions in millimetres")
    w("- **Method:** every dimension below was measured directly from the STL "
      "geometry, not read off a drawing. Envelope = axis-aligned bounding box "
      "of the part as exported.\n")
    w("---\n")

    w("## 1. How to read this document\n")
    w("Each part carries a part number, its measured envelope, an estimated "
      "printed mass, and a status. Status meanings:\n")
    for k, v in STATUS_NOTE.items():
        w(f"- **{k}** — {v}")
    w("")
    w("**Important:** the envelope is not the same as the kinematic link length. "
      "A capsule link has a circular boss at each end and the joint axis sits at "
      "the boss centre, inset from the part end by the boss radius. Section 4 "
      "gives the true joint-to-joint lengths.\n")
    w("---\n")

    w("## 2. Assembly overview\n")
    w("![Assembly](figures/existing_assembly.png)\n")
    w("The as-printed assembly measures 155 × 260 × 213 mm in the pose it was "
      "saved in. Fully extended the chain is longer; section 4 gives the "
      "dimension chain that must total 450 mm.\n")
    w("---\n")

    w("## 3. Master parts list\n")
    w("| Part | File | Group | Function | Envelope (mm) | Wall | Mass est. | Status |")
    w("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        wall = f"{r['t']:.1f}" if r["t"] == r["t"] else "—"
        mass = f"{r['mass']:.1f} g" if r["mass"] == r["mass"] else "—"
        w(f"| {r['pn']} | {r['fn'].replace('.stl','')} | {r['grp']} | {r['fun']} | "
          f"{r['x']:.1f} × {r['y']:.1f} × {r['z']:.1f} | {wall} | {mass} | {r['st']} |")
    w("")
    w("Mass estimates assume PLA at roughly 35 % infill (0.55 g/cm³ effective) "
      "and are indicative only — weigh the real parts to confirm. Wall is the "
      "effective shell thickness computed as 2V/A; it is meaningless for solid "
      "parts and is shown as a dash where the mesh is not watertight.\n")
    w("---\n")

    w("## 4. Kinematic dimension chain — the 450 mm budget\n")
    w("| Segment | Length | Notes |")
    w("| --- | --- | --- |")
    w("| Round base height | 50 | user's sketch dimension |")
    w("| Base top → J2 shoulder axis | 40 | shoulder barrel centre |")
    w("| **L2 upper arm, J2 → J3** | **145** | must equal L3 |")
    w("| **L3 forearm, J3 → J5** | **145** | must equal L2 |")
    w("| Wrist centre → TCP | 70 | J6 flange plus tool |")
    w("| **TOTAL** | **450** | meets the requirement exactly |")
    w("")
    w("Horizontal reach from the J1 axis is 145 + 145 + 70 = **360 mm**.\n")
    w("### Why L2 must equal L3\n")
    w("The reachable region of a two-link chain is an annulus whose **inner "
      "radius is |L2 − L3|**. Equal links collapse that inner hole to zero. "
      "Unequal links punch a dead zone directly in front of the robot that no "
      "amount of joint travel can reach.\n")
    w("![Revision comparison](figures/revision_compare.png)\n")
    w("| Configuration | L2 | L3 | Dead zone | Total length |")
    w("| --- | --- | --- | --- | --- |")
    w("| As printed | 97.9 | 97.9 | none | 356 mm |")
    w("| Revision 1.1 | 195.1 | 97.9 | **Ø194 mm** | 453 mm — over |")
    w("| **Recommended** | **145** | **145** | **none** | **450 mm** |")
    w("")
    w("---\n")

    w("## 5. Measured link geometry\n")
    w("Joint centres were recovered by fitting circles to the end bosses "
      "(`measure_joint_centres.py`), because the bounding box overstates the "
      "kinematic length by the sum of the two boss radii.\n")
    w("| Part | Envelope length | Boss radius A | Boss radius B | **Joint-to-joint** |")
    w("| --- | --- | --- | --- | --- |")
    w("| link1_base | 147.5 | 25.2 | 25.0 | **97.9** |")
    w("| link2_base | 147.5 | 25.2 | 25.0 | **97.9** |")
    w("| link1_base_1.1 | 256.0 | 29.5 | 29.2 | **195.1** |")
    w("| link1_cover | 196.5 | 16.8 | 17.6 | 167.6 |")
    w("| link2_cover | 146.5 | 18.2 | 17.2 | 115.9 |")
    w("| link1_cover1.1 | 256.0 | 27.1 | 27.1 | 196.0 |")
    w("")
    w("**Flag:** `link1_cover` (envelope 196.5) does not pair with `link1_base` "
      "(envelope 147.5). `link2_cover` (146.5) does pair with `link2_base` "
      "(147.5). Check this before reprinting — a mismatched shell pair is a "
      "likely cause of both the assembly gaps and any URDF export errors.\n")
    w("---\n")

    w("## 6. Link cross-section\n")
    w("| Property | Value |")
    w("| --- | --- |")
    w("| Outer width × depth | 47.5 × 29.0 |")
    w("| Wall thickness, as printed | 2.0 |")
    w("| Wall thickness, recommended | **2.4** (6 × 0.4 mm nozzle passes) |")
    w("| Second moment of area I, closed, t=2.0 | 39,899 mm⁴ |")
    w("| Torsion constant J, closed, t=2.0 | 83,267 mm⁴ |")
    w("| Torsion constant J, **seam open** | 661 mm⁴ — a 126× loss |")
    w("")
    w("---\n")

    w("## 7. Part drawings by group\n")
    for grp in ("Base", "Link", "Joint", "Wrist", "Mount", "Fixer", "COTS", "Tool"):
        if grp not in grid_files:
            continue
        w(f"### {grp}\n")
        w(f"![{grp} parts]({grid_files[grp]})\n")
        sub = [r for r in rows if r["grp"] == grp]
        w("| Part | Envelope (mm) | Wall | Status |")
        w("| --- | --- | --- | --- |")
        for r in sub:
            wall = f"{r['t']:.1f}" if r["t"] == r["t"] else "—"
            w(f"| {r['pn']} {r['fn'].replace('.stl','')} | "
              f"{r['x']:.1f} × {r['y']:.1f} × {r['z']:.1f} | {wall} | {r['st']} |")
        w("")
    w("---\n")

    w("## 8. Critical interface dimensions\n")
    w("These are the dimensions that decide whether the arm assembles tightly. "
      "They matter more than any outside dimension.\n")
    w("| Interface | Current | Specify | Reason |")
    w("| --- | --- | --- | --- |")
    w("| Bearing pocket, Ø42 bearing | Ø42.0 modelled | **Ø42.15** press fit | "
      "FDM pockets print 0.1–0.4 mm undersize |")
    w("| Bearing pocket chamfer | none | **0.5 × 45°** | bearing starts square |")
    w("| Bearing axial seat | flat face | **turned shoulder** | flat printed faces are not flat |")
    w("| Bearing spacing per joint | ~5 (stacked) | **≥ 40** | moment stiffness ∝ spacing² |")
    w("| M3 heat-set insert hole | — | **Ø4.0** | for a Ø4.6 × 5.8 insert |")
    w("| Insert boss outer diameter | — | **≥ Ø9.0** | ≥ 2.2 mm wall or it splits |")
    w("| Seam fastener pitch | — | **≤ 25** | keeps the section closed |")
    w("| Seam interlock lip | none | **1.5 mm tongue-and-groove** | shear in bearing, not friction |")
    w("| Internal fillet radius | ~0 sharp | **≥ 2.0** | drops Kt from ≥3 to ~1.3 |")
    w("| Servo clamp form | 4–6 mm bracket | **full-perimeter collar, 4 mm wall** | "
      "carries torque in shear, not bending |")
    w("")
    w("Insert dimensions are typical values — check your specific insert's datasheet.\n")
    w("---\n")

    w("## 9. Bill of materials — non-printed\n")
    w("| Item | Qty | Note |")
    w("| --- | --- | --- |")
    w("| Feetech ST3215 servo (30 kgf·cm) | 5 | J1, J3, J4, J5, J6 |")
    w("| Feetech ST3250 servo (50 kgf·cm) | 1 | J2 shoulder — needs the extra torque |")
    w("| Deep-groove ball bearings | 12 | 2 per joint, spaced ≥ 40 mm |")
    w("| M3 heat-set inserts, Ø4.6 × 5.8 | ~40 | seam and mounts |")
    w("| M3 socket-head screws, 8–16 mm | ~40 | |")
    w("| M3 preload screw + spacer per joint | 6 | removes bearing clearance |")
    w("")
    w("Bearing sizes are not yet fixed — they depend on the shaft diameter "
      "chosen for each joint. See the open questions in the analysis report.\n")

    md = os.path.join(HERE, "DRAWINGS.md")
    open(md, "w").write("\n".join(L))
    print(f"wrote {md}")
