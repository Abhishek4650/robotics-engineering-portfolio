#!/usr/bin/env python3
"""Annotated kinematic skeleton over the assembled-arm side view (Y-Z),
with the 6 joint centres joined by link segments labelled with lengths."""
import numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ASM = "/home/user/Desktop/Robotic_arm_design/Robo_2_assembled.stl"
J = np.array([[-15.8, 0.1, 52.5],    # J1 base
              [14.9, 0.0, 108.4],    # J2 shoulder
              [30.7, -199.2, 113.9], # J3 elbow
              [24.0, -160.0, 150.0], # J4 (approx)
              [28.6, -126.3, 175.7], # J5 wrist
              [70.9, -67.9, 178.2]]) # J6 end
names = ["J1", "J2", "J3", "J4", "J5", "J6"]

m = trimesh.load(ASM, process=True)
V = m.vertices
fig, ax = plt.subplots(figsize=(9, 8))
ax.hexbin(V[:, 1], V[:, 2], gridsize=170, cmap="Blues", bins="log", linewidths=0)
ax.plot(J[:, 1], J[:, 2], "-o", color="crimson", ms=8, lw=2.2, zorder=5)
# base ground
ax.plot([J[0,1]], [0], "ks", ms=9); ax.annotate("base (z=0)", (J[0,1], 0),
        xytext=(6, -14), textcoords="offset points")
for i, n in enumerate(names):
    ax.annotate(n, (J[i,1], J[i,2]), color="black", fontsize=12,
                fontweight="bold", xytext=(6, 6), textcoords="offset points",
                zorder=6)
for i in range(5):
    mid = (J[i] + J[i+1]) / 2
    L = np.linalg.norm(J[i+1] - J[i])
    ax.annotate(f"{L:.0f} mm", (mid[1], mid[2]), color="darkgreen",
                fontsize=10, fontweight="bold",
                xytext=(4, 4), textcoords="offset points", zorder=6)
ax.set_xlabel("Y (mm)"); ax.set_ylabel("Z (mm)"); ax.set_aspect("equal")
ax.set_title("Assembled arm - kinematic skeleton (side view Y-Z)\n"
             "6-DOF, ST3215 joints; link lengths from mesh (uncertified)")
fig.tight_layout()
out = "/home/user/robotic_motion/figures/arm_skeleton.png"
fig.savefig(out, dpi=115); print("saved", out)

print("\nLink lengths (mm):")
for i in range(5):
    print(f"  {names[i]}->{names[i+1]}: {np.linalg.norm(J[i+1]-J[i]):6.1f}")
print(f"  base(z=0)->J1: {J[0,2]:.1f}")
