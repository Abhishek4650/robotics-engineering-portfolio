"""
Headless orthographic render of the user's existing Fusion assembly + key parts.
No OpenGL here, so triangles are projected and painted back-to-front by depth
with a simple Lambert shade -- enough to actually SEE the design.
"""

import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

SRC = os.path.expanduser("~/Desktop/Robotic_arm_design")
LIGHT = np.array([0.35, -0.55, 0.75])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def view_matrix(az, el):
    a, e = np.radians(az), np.radians(el)
    ca, sa, ce, se = np.cos(a), np.sin(a), np.cos(e), np.sin(e)
    right = np.array([ca, -sa, 0.0])
    up = np.array([sa * se, ca * se, ce])
    fwd = np.cross(right, up)
    return np.vstack([right, up, fwd])


def paint(ax, mesh, az, el, base=(0.62, 0.70, 0.79), lw=0.0):
    """Paint EVERY face back-to-front. Dropping faces punches holes in the
    silhouette, so no decimation -- just accept the render cost."""
    m = mesh.copy()
    m.vertices -= m.bounds.mean(axis=0)

    R = view_matrix(az, el)
    V = m.vertices @ R.T
    tris = V[m.faces]

    # back-face cull first: halves the triangle count with no visual loss
    n = m.face_normals @ R.T
    vis = n[:, 2] > 0
    tris, n = tris[vis], n[vis]

    depth = tris[:, :, 2].mean(axis=1)
    order = np.argsort(depth)

    shade = np.clip(n @ np.array([0.3, 0.45, 0.84]), 0.0, 1.0) * 0.72 + 0.28
    cols = np.array(base)[None, :] * shade[:, None]
    cols = np.clip(cols, 0, 1)

    ax.add_collection(PolyCollection(tris[order][:, :, :2], facecolors=cols[order],
                                     edgecolors="none", linewidths=lw))
    lim = np.abs(V[:, :2]).max() * 1.06
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")
    return m


# ---------------------------------------------------------------------------
asm = trimesh.load(os.path.join(SRC, "Robo_2_assembled.stl"), force="mesh")
print(f"assembly: {len(asm.faces)} faces, bbox {asm.extents.round(1)}")

fig = plt.figure(figsize=(16, 6.4))
fig.patch.set_facecolor("white")
views = [(0, 0, "front"), (90, 0, "side"), (35, 22, "iso"), (0, 89, "top")]
for i, (az, el, name) in enumerate(views):
    ax = fig.add_subplot(1, 4, i + 1)
    paint(ax, asm, az, el)
    ax.set_title(name, fontsize=12, fontweight="bold", color="#1b2733")
fig.suptitle("Existing design — Robo_2_assembled.stl   "
             f"(envelope {asm.extents[0]:.0f} × {asm.extents[1]:.0f} × "
             f"{asm.extents[2]:.0f} mm, as-saved pose)",
             fontsize=14, fontweight="bold", color="#1b2733", y=0.97)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig("figures/existing_assembly.png", dpi=130, facecolor="white")
print("wrote figures/existing_assembly.png")

# ---- key parts gallery ----------------------------------------------------
PARTS = [("link1_base.stl", "link1_base"), ("link1_base_1.1.stl", "link1_base_1.1"),
         ("link2_base.stl", "link2_base"), ("J2_p1.stl", "J2_p1"),
         ("wrist_p1.stl", "wrist_p1"), ("base_p1.stl", "base_p1"),
         ("ST3215.stl", "ST3215 servo"), ("Motor_housing_new.stl", "motor housing")]

fig = plt.figure(figsize=(16, 8.2))
fig.patch.set_facecolor("white")
for i, (fn, label) in enumerate(PARTS):
    p = os.path.join(SRC, fn)
    ax = fig.add_subplot(2, 4, i + 1)
    if not os.path.exists(p):
        ax.axis("off")
        continue
    m = trimesh.load(p, force="mesh")
    paint(ax, m, 35, 22, base=(0.78, 0.55, 0.42) if "ST3215" in fn else (0.62, 0.70, 0.79))
    e = m.extents
    ax.set_title(f"{label}\n{e[0]:.1f} × {e[1]:.1f} × {e[2]:.1f} mm",
                 fontsize=10.5, fontweight="bold", color="#1b2733")
fig.suptitle("Existing parts — measured envelopes (mm)", fontsize=14,
             fontweight="bold", color="#1b2733", y=0.985)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig("figures/existing_parts.png", dpi=130, facecolor="white")
print("wrote figures/existing_parts.png")
