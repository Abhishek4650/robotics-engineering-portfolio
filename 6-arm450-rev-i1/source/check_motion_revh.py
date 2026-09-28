#!/usr/bin/env python3
"""
Joint motion clash test on the CURRENT parts.

`PRINT_GATE/check_motion.py` reads `ARM450_FINAL_ASSEMBLY.step` (11 Sep),
which predates every rev H part and contains a J5 that cannot hold a servo.
This runs the same sweep against the parts as they are now.

Two differences from the released check, both deliberate:

  * the five regenerated parts (J3_p1/p2, J4_module, J5_p1/p2) are swapped
    in at the transforms their predecessors occupied;
  * the SERVOS are in the model. A bay that clears the neighbouring
    structure can still be fouled by the motor sticking out of it, and the
    J3/J5 cheeks are 6.88 mm deeper than they were.

Overlap is counted by point containment here rather than boolean common
volume, so a seated fit reads as contact. To keep that from masking a real
clash the test is DIFFERENTIAL: the overlap at every swept angle is compared
against the overlap at the rest pose. Only a RISE above rest counts.
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asm_meshes as AM        # noqa: E402
import build_assembly as BA    # noqa: E402

REPLACED = {"J2_turret_p1", "J2_turret_p2", "J3_p1", "J3_p2",
            "J4_module", "J5_p1", "J5_p2"}

# axis point, axis direction, travel, downstream chain
JOINTS = [
    ("J1 yaw", (0, 0, 25.0), (0, 0, 1), 180,
     ["J2_turret_p1", "J2_turret_p2", "link_upper_groove",
      "link_upper_tongue", "J3_p1", "J3_p2", "link_fore_groove",
      "link_fore_tongue", "J4_module", "J5_p1", "J5_p2", "j6_body",
      "tool_flange", "joint_tube_1", "joint_tube_2", "shaft_clamp_1",
      "shaft_clamp_2", "shaft_clamp_3", "shaft_clamp_4"]),
    ("J2 shoulder", (0, 0, 90.0), (0, 1, 0), 108,
     ["link_upper_groove", "link_upper_tongue", "J3_p1", "J3_p2",
      "link_fore_groove", "link_fore_tongue", "J4_module", "J5_p1",
      "J5_p2", "j6_body", "tool_flange", "joint_tube_1", "joint_tube_2",
      "shaft_clamp_1", "shaft_clamp_2", "shaft_clamp_3", "shaft_clamp_4"]),
    ("J3 elbow", (0, 0, 209.0), (0, 1, 0), 144,
     ["link_fore_groove", "link_fore_tongue", "J4_module", "J5_p1",
      "J5_p2", "j6_body", "tool_flange", "joint_tube_2",
      "shaft_clamp_3", "shaft_clamp_4"]),
    ("J4 roll", (0, 0, 328.0), (0, 0, 1), 180,
     ["J5_p1", "J5_p2", "j6_body", "tool_flange"]),
    ("J5 pitch", (0, 0, 390.0), (0, 1, 0), 93,
     ["j6_body", "tool_flange"]),
    ("J6 roll", (0, 0, 420.0), (0, 0, 1), 180, ["tool_flange"]),
]


def scene():
    """Every part at its world placement, rev H parts substituted, servos in."""
    ms = AM.load(skip=REPLACED)
    for nm in REPLACED:
        ms[nm] = BA.placed(nm)
    # the servos, carried by the part whose bay holds them
    ms["servo_J3"] = BA.placed_servo("J3", 28.50)
    ms["servo_J5"] = BA.placed_servo("J5", 26.00)
    return ms


# a servo travels with the fork half that cradles it
CARRIED = {"servo_J3": "J3_p2", "servo_J5": "J5_p2"}


def rot(m, pt, ax, deg):
    T = trimesh.transformations.rotation_matrix(np.radians(deg), ax, pt)
    o = m.copy()
    o.apply_transform(T)
    return o


def overlap(moving, fixed, n=3000):
    """Total containment count of `moving` samples inside `fixed` parts."""
    tot = 0
    for mm in moving:
        P = mm.sample(n)
        for f in fixed:
            fb, mb = f.bounds, mm.bounds
            if (fb[1] < mb[0]).any() or (fb[0] > mb[1]).any():
                continue
            tot += int(f.contains(P).sum())
    return tot


def main():
    ms = scene()
    print("MOTION SWEEP -- rev H parts, servos included")
    print("differential: only a RISE above the rest-pose overlap counts")
    print()
    bad = 0
    for name, pt, ax, travel, chain in JOINTS:
        down = list(chain)
        for s, host in CARRIED.items():
            if host in down and s not in down:
                down.append(s)
        moving = [ms[k] for k in down if k in ms]
        fixed = [v for k, v in ms.items() if k not in down]
        if not moving:
            print("  %-13s no parts" % name)
            continue
        rest = overlap(moving, fixed)
        worst, worst_a = 0, 0
        for a in np.linspace(-travel / 2, travel / 2, 13):
            mv = [rot(m, pt, ax, a) for m in moving]
            o = overlap(mv, fixed)
            rise = o - rest
            if rise > worst:
                worst, worst_a = rise, a
        flag = ""
        if worst > 40:
            flag = "   <-- CLASH"
            bad += 1
        print("  %-13s travel %4d deg   rest %5d   worst rise %5d at %+6.1f deg%s"
              % (name, travel, rest, worst, worst_a, flag))
    print()
    print("joints with a real rise:", bad)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
