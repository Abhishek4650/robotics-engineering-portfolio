#!/usr/bin/env python3
"""Sine-wave demo on the PHYSICAL myCobot 280.

Reuses the senior's kinematics (ikpy IK over the official M5 URDF in
/home/user/robotic_arm) to compute the same vertical X-Z sine path shown
in the RViz demo, then streams the joint solutions to the real arm.

    /home/user/robotic_arm/venv/bin/python /home/user/arm_demo/sine_demo_hw.py [n_loops]

Press Ctrl-C to stop; the arm is released (torque off) on exit only if
RELEASE_ON_EXIT is True.
"""
import sys
import time

import numpy as np

sys.path.insert(0, "/home/user/robotic_arm/scripts")
from kinematics import build_chain, make_sine_path, solve_path  # noqa: E402

from pymycobot import MyCobot280  # noqa: E402

PORT = "/dev/ttyUSB0"
BAUD = 115200
N_WAYPOINTS = 40        # fewer than RViz's 120: real servos need coarser steps
MOVE_SPEED = 40         # 1-100; speed for waypoint moves
DWELL = 0.25            # s between waypoints
RELEASE_ON_EXIT = False # True -> torque off when done (arm goes limp!)

n_loops = int(sys.argv[1]) if len(sys.argv) > 1 else 2

print("Computing sine path + IK (senior's kinematics)...")
chain = build_chain()
path = make_sine_path(n_points=N_WAYPOINTS)
q_rad, _ = solve_path(chain, path)
q_deg = np.degrees(q_rad)

# Basic sanity: myCobot 280 joints are all within +/-165..175 deg.
if np.abs(q_deg).max() > 170:
    print(f"ERROR: IK produced angle {np.abs(q_deg).max():.1f} deg — refusing to send.")
    sys.exit(1)
print(f"  {len(q_deg)} waypoints, joint range "
      f"[{q_deg.min():.1f}, {q_deg.max():.1f}] deg — OK")

print(f"Connecting to {PORT} ...")
mc = MyCobot280(PORT, BAUD)
time.sleep(0.5)
mc.power_on()
time.sleep(1.0)

try:
    print("Moving slowly to path start...")
    mc.send_angles(list(q_deg[0]), 20)
    time.sleep(4)

    for loop in range(n_loops):
        print(f"Tracing sine wave, pass {loop + 1}/{n_loops} ...")
        # forward sweep, then reverse so the motion loops smoothly
        for row in list(q_deg) + list(q_deg[::-1]):
            mc.send_angles(list(row), MOVE_SPEED)
            time.sleep(DWELL)

    print("Returning to path start...")
    mc.send_angles(list(q_deg[0]), 20)
    time.sleep(3)
except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    if RELEASE_ON_EXIT:
        mc.release_all_servos()
print("Done.")
