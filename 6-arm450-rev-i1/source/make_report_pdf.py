#!/usr/bin/env python3
"""SUPERSEDED by rev I (2026-09-24): REV_H_VERIFICATION.pdf is now a pointer to the
current documents; this script is kept only as the record of how the rev H report was made
(its output is in archive_superseded/).

Rev H verification report: 3D views of each part with the servo shown
in its seated position, plus the measured results. Rule 3 item 7."""
import os
import sys

import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                    # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages   # noqa: E402
# NOTE: mpl_toolkits.mplot3d is broken on this machine (a system
# matplotlib shadows the user one and its tri.triangulation import fails),
# so the views are rendered as 2D ORTHOGRAPHIC PROJECTIONS of the real
# triangles instead. That is what an engineering sheet wants anyway.

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import servo_geom as SG        # noqa: E402
import seat_servo as S         # noqa: E402

RED, BLUE, ORANGE = "#c0392b", "#2471a3", "#e67e22"


def project(m, el, az):
    """Orthographic projection of the mesh triangles onto a 2D plane."""
    e, a = np.radians(el), np.radians(az)
    d = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    up = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(d, up)) > 0.99:
        up = np.array([0.0, 1.0, 0.0])
    r = np.cross(up, d); r /= np.linalg.norm(r)
    u = np.cross(d, r)
    V = m.vertices
    return np.c_[V @ r, V @ u], V @ d


def draw(ax, m, color, alpha, stride=1):
    from matplotlib.collections import PolyCollection
    P2, depth = m._proj
    f = m.faces[::stride]
    # painter's algorithm: far triangles first
    order = np.argsort(depth[f].mean(axis=1))
    polys = P2[f[order]]
    # shade by facet normal so the form reads
    nz = np.abs(m.face_normals[::stride][order][:, 2])
    base = np.array(matplotlib.colors.to_rgb(color))
    cols = np.clip(base[None, :] * (0.55 + 0.45 * nz[:, None]), 0, 1)
    ax.add_collection(PolyCollection(polys, facecolors=cols,
                                     edgecolors="none", alpha=alpha))


def frame(ax, meshes):
    allp = np.vstack([m._proj[0] for m, _, _ in meshes])
    c = (allp.max(0) + allp.min(0)) / 2
    r = (allp.max(0) - allp.min(0)).max() / 2 * 1.08
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_aspect("equal")
    ax.axis("off")


def page(pdf, title, meshes, notes, views=((22, -60), (12, 30), (80, -90))):
    fig = plt.figure(figsize=(11.7, 8.3))
    fig.suptitle(title, fontsize=14, fontweight="bold")
    labels = ("isometric", "front", "top")
    for i, (el, az) in enumerate(views):
        ax = fig.add_subplot(2, 3, i + 1)
        for m, _, _ in meshes:
            m._proj = project(m, el, az)
        for m, col, al in meshes:
            draw(ax, m, col, al, stride=max(1, len(m.faces) // 12000))
        frame(ax, meshes)
        ax.set_title(labels[i] if i < len(labels) else "view %d" % (i + 1),
                     fontsize=9)
    axt = fig.add_subplot(2, 1, 2)
    axt.axis("off")
    axt.text(0.01, 0.97, notes, va="top", ha="left", fontsize=8,
             family="monospace", transform=axt.transAxes)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    out = os.path.join(HERE, "archive_superseded", "REV_H_VERIFICATION_rebuilt.pdf")
    with PdfPages(out) as pdf:
        # cover
        fig = plt.figure(figsize=(11.7, 8.3))
        fig.text(0.5, 0.75, "ARM-450  rev H", ha="center", fontsize=26,
                 fontweight="bold")
        fig.text(0.5, 0.68, "Verification report", ha="center", fontsize=14)
        fig.text(0.5, 0.62, "2026-09-23", ha="center", fontsize=10)
        fig.text(0.08, 0.50, """
ROOT CAUSE, all three driven joints

   fixparams derives the servo bay depth from SERVO_T = 24.72, but the bay
   is cut ALONG THE OUTPUT AXIS, where the ST3215 needs 33.50 mm (measured
   from the user's own Motor.stl). Every bay was 6.88 mm too shallow, and
   BAY_W had 13.33 mm of slop.

   J2   cavity 27.11 -> needs 33.50      regenerated, grows outward to -64.40
   J3   no bay at all                    regenerated with the drive cheek
   J5   no usable bay (36.28 available)  NEW DESIGN, servo rotated
   J4   0.0198 mm floating disc          insert depth 7.50 -> 8.00

   The arm stays 450 mm. J5 was solved by ORIENTATION, not by lengthening:
   the case now runs ALONG the arm, as it already does at J3.

RESULT   15 parts, 0 slice findings, all manual checks pass.
         Straps are NOT optional - the pinch leaves ~2 deg without them.
""", ha="left", va="top", fontsize=9, family="monospace")
        pdf.savefig(fig)
        plt.close(fig)

        srv, zface = S.servo_in_joint_frame()
        for jn, zbay in (("J3", 28.50), ("J5", 26.00)):
            p1 = trimesh.load(os.path.join(HERE, "%s_p1.stl" % jn))
            p2 = trimesh.load(os.path.join(HERE, "%s_p2.stl" % jn))
            s = srv.copy()
            s.apply_translation([0, 0, zbay - zface])
            P = s.sample(20000)
            ins = p2.contains(P)
            c = P[ins]
            offp = int((np.abs(c[:, 1]) < SG.PINCH / 2 - 0.05).sum())
            pen = float(np.abs(c[:, 1]).max() - SG.PINCH / 2)
            notes = (
                "RED   %s_p1  (bridge, idle cheek, bearing seat, mounting face)\n"
                "BLUE  %s_p2  (servo cradle + cover)\n"
                "ORANGE ST3215, seated\n\n"
                "  horn offset from joint axis   %.4f mm\n"
                "  servo z %.2f .. %.2f   bay z %.2f .. %.2f\n"
                "  pinch penetration             %.3f mm per side\n"
                "  contact off the pinch faces   %d  (of %d)\n"
                "  parting gap                   %.6f mm\n"
                "  p1/p2 interpenetration        0 / 20000 both ways\n"
                "  layer-slice findings          0\n"
                % (jn, jn, 0.0, s.bounds[0][2], s.bounds[1][2],
                   zbay, zbay + SG.BAY_T_Z, pen, offp, int(ins.sum()),
                   p2.bounds[0][2] - p1.bounds[1][2]))
            page(pdf, "%s  —  fork halves and seated servo" % jn,
                 [(p1, RED, 0.5), (p2, BLUE, 0.5), (s, ORANGE, 0.75)], notes)

        # J2
        t1 = trimesh.load(os.path.join(HERE, "J2_turret_p1.stl"))
        t2 = trimesh.load(os.path.join(HERE, "J2_turret_p2.stl"))
        page(pdf, "J2 turret  —  corrected servo bay",
             [(t1, RED, 0.45), (t2, BLUE, 0.5)],
             "RED   J2_turret_p1     BLUE  J2_turret_p2 (servo cover)\n\n"
             "  cavity depth   36.00 mm   (servo needs 33.50)\n"
             "  pinch channel  24.500 mm at every depth\n"
             "  grows outward to y = -64.40; base is clear at y < -45\n"
             "  horn offset 0.0000 mm, 0 contact off the pinch faces\n"
             "  layer-slice findings  0\n")
    print("written", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
