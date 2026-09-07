#!/usr/bin/env python3
"""Step 1: sanity-check the physical myCobot 280 on /dev/ttyUSB0.

Connects, reads firmware/angles, then does one small, slow test move
(joint 1 +15 deg and back). Run with the robotic_arm venv python:

    /home/user/robotic_arm/venv/bin/python /home/user/arm_demo/check_arm.py
"""
import time
import sys

from pymycobot import MyCobot280

PORT = "/dev/ttyUSB0"
BAUD = 115200

print(f"Connecting to {PORT} @ {BAUD} ...")
mc = MyCobot280(PORT, BAUD)
time.sleep(0.5)

version = mc.get_system_version()
print(f"  firmware/system version : {version}")

mc.power_on()
time.sleep(1.0)
print(f"  powered on              : {mc.is_power_on() == 1}")

angles = mc.get_angles()
print(f"  current joint angles    : {angles}")
if not isinstance(angles, list) or len(angles) != 6:
    print("ERROR: could not read joint angles — check the arm is powered "
          "(DC barrel jack in, M5 screen on) and the USB cable is seated.")
    sys.exit(1)

print("\nSmall test move: joint 1 -> +15 deg and back (slow)...")
j1_start = angles[0]
mc.send_angle(1, j1_start + 15, 20)   # joint id 1, target deg, speed 20/100
time.sleep(3)
print(f"  after move  : {mc.get_angles()}")
mc.send_angle(1, j1_start, 20)
time.sleep(3)
print(f"  back to     : {mc.get_angles()}")

print("\nOK — the arm responds. Ready for the sine demo (sine_demo_hw.py).")
