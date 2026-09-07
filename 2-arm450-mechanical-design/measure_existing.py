"""
Measure the user's EXISTING Fusion 360 design (~/Desktop/Robotic_arm_design/*.stl).

STL carries no units; Fusion exports mm by default, so all numbers below are mm.
Goal: recover the real dimensions of the arm they already built, so rev C can be
their design corrected rather than my design imposed.
"""

import os
import glob
import numpy as np
import trimesh

SRC = os.path.expanduser("~/Desktop/Robotic_arm_design")

INTEREST = [
    "Robo_2_assembled.stl",
    "ST3215.stl",
    "base_p1.stl", "base_p2.stl",
    "link1_base.stl", "link1_cover.stl",
    "link2_base.stl", "link2_cover.stl",
    "J2_p1.stl", "J2_p2.stl",
    "J4_p1.stl", "J4_p2.stl",
    "wrist_p1.stl", "wrist_p2.stl",
    "Motor_mount_J1.stl", "Motor_mount_J2.stl", "Motor_mount_wrist.stl",
    "thrust ball bearing.stl",
    "pin.stl",
]

# rough print density: PLA/PETG solid ~1.24 g/cm3; at ~35 % infill call it 0.55
RHO_PRINT = 0.55e-3   # g/mm^3


def report(path):
    try:
        m = trimesh.load(path, force="mesh")
    except Exception as e:                                  # noqa: BLE001
        return f"{os.path.basename(path):32s}  <unreadable: {e}>"
    ext = m.extents
    name = os.path.basename(path)
    vol = m.volume if m.is_watertight else float("nan")
    line = (f"{name:32s} bbox {ext[0]:7.1f} x {ext[1]:7.1f} x {ext[2]:7.1f}"
            f"   Lmax {max(ext):7.1f}")
    if np.isfinite(vol) and vol > 0:
        line += f"   vol {vol/1000:8.1f} cm3   ~{vol*RHO_PRINT:6.1f} g @35% infill"
    else:
        line += "   (not watertight -> no volume)"
    return line


print(f"reading {SRC}\n")
print("--- parts of interest " + "-" * 74)
for n in INTEREST:
    p = os.path.join(SRC, n)
    if os.path.exists(p):
        print(report(p))

print("\n--- everything else " + "-" * 76)
seen = set(INTEREST)
for p in sorted(glob.glob(os.path.join(SRC, "*.stl"))):
    if os.path.basename(p) not in seen:
        print(report(p))
