#!/usr/bin/env python3
"""
Offline verification (no ROS): generate the vertical sine path, solve IK, run FK
on the solutions, and plot desired vs. achieved EE path in the X-Z plane.
Saves preview_path.png and prints the max/mean position error and joint ranges.

Run:  python scripts/preview_path.py
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

import kinematics as k

OUT_PNG = os.path.join(os.path.dirname(__file__), os.pardir, "preview_path.png")


def main():
    chain = k.build_chain()
    targets = k.make_sine_path()
    joints, full = k.solve_path(chain, targets)

    achieved = np.array([k.fk_position(chain, full[i]) for i in range(len(full))])
    errs = np.linalg.norm(achieved - targets, axis=1)

    print(f"waypoints           : {len(targets)}")
    print(f"max  position error : {errs.max()*1000:.3f} mm")
    print(f"mean position error : {errs.mean()*1000:.3f} mm")
    # Tightest joint limit on the M5 is joint3 at +/-2.4434 rad; use it as a
    # conservative reachability flag (all joints have >= this range).
    LIMIT = 2.4434
    print("joint ranges (rad):")
    for i, name in enumerate(k.JOINT_NAMES):
        lo, hi = joints[:, i].min(), joints[:, i].max()
        flag = "  <-- near/over limit!" if (lo < -LIMIT or hi > LIMIT) else ""
        print(f"  {name:24s} [{lo:+.3f}, {hi:+.3f}]{flag}")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.plot(targets[:, 0], targets[:, 2], "k--", lw=2, label="desired sine")
    ax1.plot(achieved[:, 0], achieved[:, 2], "r.", ms=4, label="achieved (FK of IK)")
    ax1.set_xlabel("X (m)"); ax1.set_ylabel("Z (m)")
    ax1.set_title("EE path in X-Z plane"); ax1.axis("equal"); ax1.legend(); ax1.grid(True)

    t = np.arange(len(joints))
    for i, name in enumerate(k.JOINT_NAMES):
        ax2.plot(t, joints[:, i], label=name)
    ax2.set_xlabel("waypoint"); ax2.set_ylabel("joint angle (rad)")
    ax2.set_title("Joint trajectories"); ax2.legend(fontsize=7); ax2.grid(True)

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=110)
    print(f"\nsaved plot -> {os.path.abspath(OUT_PNG)}")


if __name__ == "__main__":
    main()
