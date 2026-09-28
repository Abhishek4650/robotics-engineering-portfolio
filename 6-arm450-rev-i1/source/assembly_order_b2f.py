#!/usr/bin/env python3
"""
BASE-TO-FLANGE build order (user, 2026-09-26: "assembly guide step by step to
the full 6-DOF arm from base to flange"). The arm is built up joint by joint
from the foot to the tool flange; a link half, a servo on its shaft or the
wrist blade is put together on the bench right before its joint is closed.

Run as a script it PROVES the order: verify_tool_access.py's check (a O3.2 x
60 mm key straight out of every screw, against every part already in place at
that step, exact solids) with this sequence instead of the manual's.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

B2F = [
    ("Foot: J1 servo into the foot, its 4 screws from under the foot plate", "main",
     r"^(j1_mount|foot_ins_\d|servo_J1|servo_scr_J1_\d)$"),
    ("J1 hub onto the J1 servo horn", "main", r"^(j1_hub|horn_screw_J1_\d+)$"),
    ("Base with the two J1 bearings onto the foot", "main", r"^(base|brg_J1_z\d+|m4_base_foot_\d)$"),
    ("Turret onto the J1 hub, spigot collar", "main",
     r"^(J2_turret_p1|brg_J2_(drive|idle)|split_ins_J2_\d|pin_J2_turret_[+-]1_ins|spigot_collar|collar_ins|collar_pinch)$"),
    ("BENCH: upper link halves round their centring rings", "ulink",
     r"^(shaft_clamp_[12]|link_upper_(groove|tongue)|seam_ins_upper_\d|seam_upper_\d|ear_ins_upper|ear_bolt_upper|link_end_ins_\d)$"),
    ("BENCH: J2 servo onto its printed shaft", "j2drv", r"^(servo_J2|J2_shaft|horn_screw_J2_\d+)$"),
    ("J2: upper link into the turret, servo + shaft down the axis", "main+ulink+j2drv", None),
    ("J2: servo pod closed, servo screws, link set screws", "main",
     r"^(J2_turret_p2|split_J2_\d|servo_scr_J2_\d|link_set_[12]_\d+)$"),
    ("J3 fork onto the top of the upper link", "main",
     r"^(J3_p1|brg_J3_(drive|idle)|split_ins_J3_\d|pin_J3_fork_[+-]1_ins|j3fork_link_\d)$"),
    ("BENCH: forearm halves round their centring rings", "fore",
     r"^(shaft_clamp_[34]|link_fore_(groove|tongue)|seam_ins_fore_\d|seam_fore_\d|ear_ins_fore|ear_bolt_fore|forearm_ins_\d)$"),
    ("BENCH: J3 servo onto its printed shaft", "j3drv", r"^(servo_J3|J3_shaft|horn_screw_J3_\d+)$"),
    ("J3: forearm into the fork, servo + shaft down the axis", "main+fore+j3drv", None),
    ("J3: cover closed, servo screws, forearm set screws", "main",
     r"^(J3_p2|split_J3_\d|servo_scr_J3_\d|link_set_[34]_\d+)$"),
    ("J4 base onto the top of the forearm", "main", r"^(j4_base|j4base_forearm_\d|cap_ins_J4_\d)$"),
    ("J4 servo in (2 screws from under the plate), bearing, cap", "main",
     r"^(servo_J4|servo_scr_J4_\d|brg_J4|j4_cap|cap_J4_\d)$"),
    ("J4 hub onto the J4 servo horn", "main", r"^(j4_hub|j4hub_ins_\d|horn_screw_J4_\d+)$"),
    ("J5 fork onto the J4 hub", "main", r"^(J5_p1|brg_J5_(drive|idle)|split_ins_J5_\d|j5fork_j4hub_\d)$"),
    ("BENCH: wrist blade -- J6 servo in, bearing, cap", "blade",
     r"^(j6_body|servo_J6|servo_scr_J6_\d|brg_J6|cap_ins_J6_\d|j6_cap|cap_J6_\d)$"),
    ("BENCH: J5 servo onto its printed axle", "j5drv", r"^(servo_J5|J5_shaft|horn_screw_J5_\d+)$"),
    ("J5: blade into the fork with its spacers, axle in from the idle side", "main+blade+j5drv", r"^(J5_spacer_[AB])$"),
    ("J5: cover closed, servo screws, axle grub", "main", r"^(J5_p2|split_J5_\d|servo_scr_J5_\d|j5_grub)$"),
    ("J6: tool flange onto the J6 servo horn", "main", r"^(j6_flange|tool_ins_\d+|horn_screw_J6_\d+)$"),
    ("Spring collars on the upper link and the forearm", "main",
     r"^(collar_(upper|fore)_[+-]y|collar_clamp_\S+|collar_nut_\S+|pin_J\d_collar_[+-]1_ins)$"),
    ("Spring pins and the four gravity springs", "main", r"^(pin_J\d_(turret|fork|collar)_[+-]1|spring_J\d_[+-]1)$"),
]


if __name__ == "__main__":
    import verify_tool_access as TA
    TA.SEQ = B2F
    print("BASE-TO-FLANGE ORDER -- tool access at every step\n")
    sys.exit(1 if TA.main() else 0)
