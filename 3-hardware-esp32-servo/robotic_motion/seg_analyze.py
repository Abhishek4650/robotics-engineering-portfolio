#!/usr/bin/env python3
"""Segment the assembled arm mesh into rigid bodies, locate the servos/joints,
and render orthographic views. Output: printed body table + figure.

Bodies are connected components of the mesh (Fusion exports each solid as its
own shell, so components ~ parts). We match each body to the known part
library by sorted bounding-box dimensions, then the servo bodies give us the
joint-axis locations for the DH table."""
import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ASM = "/home/user/Desktop/Robotic_arm_design/Robo_2_assembled.stl"
FIGDIR = "/home/user/robotic_motion/figures"
os.makedirs(FIGDIR, exist_ok=True)

# known parts: name -> sorted (dim0,dim1,dim2) in mm (from stl_inspect)
LIB = {
    "ST3215_servo": (24.7, 37.8, 45.2),
    "link_base":    (29.0, 47.5, 147.5),
    "mount_J1":     (24.0, 40.0, 40.0),
    "mount_wrist":  (23.0, 40.0, 40.0),
    "mount_J2":     (38.2, 46.0, 46.0),
    "mount_base":   (33.0, 46.0, 46.0),
    "base_p1":      (43.0, 56.0, 72.9),
    "bearing":      (3.7, 42.0, 42.0),
    "J2_p1":        (64.8, 80.0, 85.5),
    "J4_p1":        (57.0, 63.8, 79.8),
    "wrist_p1":     (58.2, 62.7, 72.2),
}


def match(size):
    s = np.sort(size)
    best, bd = "?", 1e9
    for name, dims in LIB.items():
        d = np.abs(s - np.array(dims)).sum()
        if d < bd:
            bd, best = d, name
    return best if bd < 18 else f"?({best}?)"


print("loading", ASM)
mesh = trimesh.load(ASM, process=True)
print(f"  {len(mesh.faces)} faces, watertight={mesh.is_watertight}")
print("splitting into bodies ...")
parts = mesh.split(only_watertight=False)
print(f"  {len(parts)} connected components")

rows = []
for p in parts:
    ext = p.extents                      # bbox size
    ctr = p.bounds.mean(axis=0)
    vol = float(p.volume) if p.is_volume else 0.0
    # principal axis = eigenvector of inertia with SMALLEST moment = long axis
    try:
        pae = p.principal_inertia_vectors
    except Exception:
        pae = np.eye(3)
    rows.append(dict(size=ext, ctr=ctr, vol=abs(vol),
                     nface=len(p.faces), axis=pae[0], name=match(ext)))

# keep only reasonably-sized bodies (drop screws/tiny shells)
rows = [r for r in rows if max(r["size"]) > 20 and r["nface"] > 200]
rows.sort(key=lambda r: r["ctr"][2])     # sort up the Z (height) axis

print(f"\n{'idx':>3} {'part?':14s} {'size(sorted mm)':22s} "
      f"{'centre (x,y,z)':26s} {'longaxis':20s} {'nface':>6}")
print("-"*100)
for i, r in enumerate(rows):
    s = np.sort(r["size"])
    print(f"{i:3d} {r['name']:14s} "
          f"({s[0]:5.1f},{s[1]:5.1f},{s[2]:6.1f})     "
          f"({r['ctr'][0]:6.1f},{r['ctr'][1]:7.1f},{r['ctr'][2]:6.1f})   "
          f"({r['axis'][0]:5.2f},{r['axis'][1]:5.2f},{r['axis'][2]:5.2f})  "
          f"{r['nface']:6d}")

# ---- render orthographic silhouettes with body centroids ----
V = mesh.vertices
planes = [(0, 2, "FRONT  (X-Z)"), (1, 2, "SIDE  (Y-Z)"), (0, 1, "TOP  (X-Y)")]
fig, axes = plt.subplots(1, 3, figsize=(15, 6))
for ax, (a, b, title) in zip(axes, planes):
    ax.hexbin(V[:, a], V[:, b], gridsize=160, cmap="Blues", bins="log",
              linewidths=0)
    for i, r in enumerate(rows):
        ax.plot(r["ctr"][a], r["ctr"][b], "o", ms=5, color="red")
        ax.annotate(str(i), (r["ctr"][a], r["ctr"][b]), color="black",
                    fontsize=8, fontweight="bold",
                    xytext=(3, 3), textcoords="offset points")
    ax.set_title(title); ax.set_aspect("equal"); ax.set_xlabel("mm")
fig.suptitle("Assembled arm - orthographic silhouettes with body centroids (red)")
fig.tight_layout()
out = os.path.join(FIGDIR, "arm_segmentation.png")
fig.savefig(out, dpi=110)
print("\nsaved", out)
