#!/usr/bin/env python3
"""
Generate result artifacts for the myCobot 280 M5 sine-path demo (offline, no ROS):
  * results/sine_path_results.png  -- X-Z path (desired vs achieved) + joint trajectories
  * results/ee_path_3d.png         -- 3D end-effector path
  * results/trajectory.csv         -- per-waypoint targets, achieved xyz, error, 6 joints
  * prints a summary table to stdout

Run:  python scripts/generate_results.py
"""

import os
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

import kinematics as k

RESULTS_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "results")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    chain = k.build_chain()
    targets = k.make_sine_path()
    joints, full = k.solve_path(chain, targets)
    achieved = np.array([k.fk_position(chain, full[i]) for i in range(len(full))])
    errs = np.linalg.norm(achieved - targets, axis=1)

    # ---- summary ----
    print("=" * 60)
    print(" myCobot 280 M5 - sinusoidal end-effector path : RESULTS")
    print("=" * 60)
    print(f" model            : official mycobot_280_m5 (EE = joint6_flange)")
    print(f" waypoints        : {len(targets)}")
    print(f" path             : vertical sine in X-Z plane")
    print(f"   X sweep        : {targets[:,0].min():.3f} -> {targets[:,0].max():.3f} m")
    print(f"   Z center / amp : {targets[:,2].mean():.3f} m / "
          f"{(targets[:,2].max()-targets[:,2].min())/2:.3f} m")
    print(f" IK max error     : {errs.max()*1000:.4f} mm")
    print(f" IK mean error    : {errs.mean()*1000:.4f} mm")
    print(" joint ranges (rad):")
    for i, name in enumerate(k.JOINT_NAMES):
        print(f"   {name:24s} [{joints[:,i].min():+.3f}, {joints[:,i].max():+.3f}]")
    print("=" * 60)

    # ---- CSV ----
    csv_path = os.path.join(RESULTS_DIR, "trajectory.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "tx", "ty", "tz", "ax", "ay", "az", "err_mm", *k.JOINT_NAMES])
        for i in range(len(targets)):
            w.writerow([i, *np.round(targets[i], 6), *np.round(achieved[i], 6),
                        round(errs[i] * 1000, 4), *np.round(joints[i], 6)])

    # ---- 2D plot ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    ax1.plot(targets[:, 0], targets[:, 2], "k--", lw=2, label="desired sine")
    ax1.plot(achieved[:, 0], achieved[:, 2], "r.", ms=4, label="achieved (FK of IK)")
    ax1.set_xlabel("X (m)"); ax1.set_ylabel("Z (m)")
    ax1.set_title("End-effector path in X-Z plane")
    ax1.axis("equal"); ax1.legend(); ax1.grid(True)
    t = np.arange(len(joints))
    for i, name in enumerate(k.JOINT_NAMES[:-1]):  # last joint is constant 0
        ax2.plot(t, joints[:, i], label=name)
    ax2.set_xlabel("waypoint"); ax2.set_ylabel("joint angle (rad)")
    ax2.set_title("Joint trajectories"); ax2.legend(fontsize=8); ax2.grid(True)
    fig.tight_layout()
    p2d = os.path.join(RESULTS_DIR, "sine_path_results.png")
    fig.savefig(p2d, dpi=120)

    # ---- 3D plot ----
    fig3 = plt.figure(figsize=(7, 6))
    ax = fig3.add_subplot(111, projection="3d")
    ax.plot(achieved[:, 0], achieved[:, 1], achieved[:, 2], "r-", lw=2, label="EE path")
    ax.scatter([0], [0], [0], c="k", s=40, label="base (g_base)")
    ax.set_xlabel("X (m)"); ax.set_ylabel("Y (m)"); ax.set_zlabel("Z (m)")
    ax.set_ylim(-0.05, 0.05)  # path is planar (Y const); fix range so it reads as a wave
    ax.set_zlim(0.10, 0.25)
    ax.view_init(elev=18, azim=-72)
    ax.set_title("End-effector sinusoidal path (3D)")
    ax.legend()
    p3d = os.path.join(RESULTS_DIR, "ee_path_3d.png")
    fig3.savefig(p3d, dpi=120)

    print(f"\n wrote:\n   {os.path.abspath(p2d)}\n   {os.path.abspath(p3d)}"
          f"\n   {os.path.abspath(csv_path)}")


if __name__ == "__main__":
    main()
