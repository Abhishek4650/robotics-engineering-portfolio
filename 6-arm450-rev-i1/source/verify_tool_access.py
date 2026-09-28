#!/usr/bin/env python3
"""
Rule 3 / thumb rule 5 -- a hex key reaches every screw AT THE STEP WHERE IT
IS TIGHTENED. The build sequence below (bench sub-assemblies and the steps
that join them) is the assembly procedure written into FINAL_PRINT/README.md.
For each screw: a O3.2 x 60 mm key path straight out of its socket along the
screw axis must be free of every part ALREADY IN PLACE at that step (exact
OCC booleans, parts at their final placement). Parts that go on later may
block it in the finished arm -- that is reported, not failed, and tells you
what to take off to service that screw.
"""
import os
import re
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import verify_fasteners as VF      # noqa: E402
import build_final_assembly as BA  # noqa: E402

# (step, group, regex of the components fitted / tightened in this step)
# a 'join' step merges groups: ('join', 'A+B', ...) -> B becomes part of A
SEQ = [
    ("foot: J1 servo into the foot, its 4 screws from under the foot plate", "main",
     r"^(j1_mount|foot_ins_\d|servo_J1|servo_scr_J1_\d)$"),
    ("J1 hub onto the horn", "main", r"^(j1_hub|horn_screw_J1_\d+)$"),
    ("base + J1 bearings onto the foot", "main", r"^(base|brg_J1_z\d+|m4_base_foot_\d)$"),
    ("turret p1 + J2 bearings, spigot collar", "main",
     r"^(J2_turret_p1|brg_J2_(drive|idle)|split_ins_J2_\d|pin_J2_turret_[+-]1_ins|spigot_collar|collar_ins|collar_pinch)$"),
    ("BENCH upper link", "ulink", r"^(shaft_clamp_[12]|link_upper_(groove|tongue)|seam_ins_upper_\d|seam_upper_\d|"
                                  r"ear_ins_upper|ear_bolt_upper|link_end_ins_\d)$"),
    ("BENCH J2 servo + shaft", "j2drv", r"^(servo_J2|J2_shaft|horn_screw_J2_\d+)$"),
    ("JOIN link into the J2 gap, servo+shaft down the axis", "main+ulink+j2drv", None),
    ("J2 pod on, servo screws, link set screws", "main", r"^(J2_turret_p2|split_J2_\d|servo_scr_J2_\d|link_set_[12]_\d+)$"),
    ("J3 fork p1 onto the upper link", "main",
     r"^(J3_p1|brg_J3_(drive|idle)|split_ins_J3_\d|pin_J3_fork_[+-]1_ins|j3fork_link_\d)$"),
    ("BENCH forearm", "fore", r"^(shaft_clamp_[34]|link_fore_(groove|tongue)|seam_ins_fore_\d|seam_fore_\d|"
                              r"ear_ins_fore|ear_bolt_fore|forearm_ins_\d)$"),
    ("BENCH J4 base on the forearm", "fore", r"^(j4_base|j4base_forearm_\d|cap_ins_J4_\d)$"),
    ("BENCH J4 servo (2 screws from under the plate), bearing, cap", "fore",
     r"^(servo_J4|servo_scr_J4_\d|brg_J4|j4_cap|cap_J4_\d)$"),
    ("BENCH J4 hub onto the horn", "fore", r"^(j4_hub|j4hub_ins_\d|horn_screw_J4_\d+)$"),
    ("BENCH J5 fork p1 onto the hub", "fore", r"^(J5_p1|brg_J5_(drive|idle)|split_ins_J5_\d|j5fork_j4hub_\d)$"),
    ("BENCH blade: J6 servo, bearing, cap", "blade",
     r"^(j6_body|servo_J6|servo_scr_J6_\d|brg_J6|cap_ins_J6_\d|j6_cap|cap_J6_\d)$"),
    ("BENCH blade: tool flange onto the J6 horn", "blade", r"^(j6_flange|tool_ins_\d+|horn_screw_J6_\d+)$"),
    ("BENCH J5 servo + axle", "j5drv", r"^(servo_J5|J5_shaft|horn_screw_J5_\d+)$"),
    ("JOIN blade into the J5 gap, spacers, axle down the axis", "fore+blade+j5drv", r"^(J5_spacer_[AB])$"),
    ("J5 cover, servo screws, axle grub", "fore", r"^(J5_p2|split_J5_\d|servo_scr_J5_\d|j5_grub)$"),
    ("BENCH J3 servo + shaft", "j3drv", r"^(servo_J3|J3_shaft|horn_screw_J3_\d+)$"),
    ("JOIN forearm into the J3 gap, servo+shaft down the axis", "main+fore+j3drv", None),
    ("J3 cover, servo screws, link set screws", "main", r"^(J3_p2|split_J3_\d|servo_scr_J3_\d|link_set_[34]_\d+)$"),
    ("spring collars", "main", r"^(collar_(upper|fore)_[+-]y|collar_clamp_\S+|collar_nut_\S+|pin_J\d_collar_[+-]1_ins)$"),
    ("spring pins + springs", "main", r"^(pin_J\d_(turret|fork|collar)_[+-]1|spring_J\d_[+-]1)$"),
]


def main():
    A, _ = BA.build()
    S = {}
    for ch in A.children:
        w = VF.world(ch)
        if w is not None:
            S[ch.name] = (w, ch)
    # step and group of every component
    step, grp = {}, {}
    for i, (nm, g, rx) in enumerate(SEQ):
        if rx is None:
            continue
        for k in S:
            if re.match(rx, k):
                step[k] = i; grp[k] = g.split("+")[0]
    missing = sorted(set(S) - set(step))
    if missing:
        print("NOT IN THE BUILD SEQUENCE:", ", ".join(missing))
    # group membership over time: owner[i][g] = root group g belongs to after step i
    owner, cur = [], {}
    for nm, g, rx in SEQ:
        parts = g.split("+")
        for p in parts:
            cur.setdefault(p, p)
        if len(parts) > 1:
            for p in parts[1:]:
                for q, r in list(cur.items()):
                    if r == p:
                        cur[q] = parts[0]
        owner.append(dict(cur))
    screws = [k for k in S if re.match(r"^(split_J\d_\d|cap_J\d_\d|j4base_forearm_\d|j5fork_j4hub_\d|j3fork_link_\d|"
                                        r"m4_base_foot_\d|collar_pinch|j5_grub|pin_J\d_\w+_[+-]\d|collar_clamp_\S+|"
                                        r"seam_(upper|fore)_\d+|ear_bolt_\w+|link_set_\d_\d+|horn_screw_J\d_\d+|servo_scr_J\d_\d)$", k)]
    B = {k: VF.bbox(v[0]) for k, v in S.items()}
    fails, later_only, clear = [], [], 0
    for s in sorted(screws, key=lambda k: (step[k], k)):
        sh, ch = S[s]
        i = step[s]; own = owner[i]
        bb = ch.obj.val().BoundingBox() if isinstance(ch.obj, cq.Workplane) else ch.obj.BoundingBox()
        key = cq.Solid.makeCylinder(1.6, 60.0, cq.Vector(0, 0, bb.zmax + 0.1), cq.Vector(0, 0, 1)).moved(ch.loc).wrapped
        kb = VF.bbox(key)
        hits = [k for k, (w, _) in S.items() if k != s and VF.overlap(kb, B[k]) and VF.common(key, w) > 1e-3]
        present = [h for h in hits if step[h] <= i and own.get(grp[h]) == own.get(grp[s])]
        if present:
            fails.append((s, present))
            print("  FAIL %-22s step %2d (%s): key blocked by %s, already in place" % (s, i + 1, SEQ[i][0], ", ".join(present)))
        elif hits:
            later_only.append((s, hits))
            print("  ok   %-22s step %2d (%s): clear then; in the finished arm %s cover(s) it" % (s, i + 1, SEQ[i][0], ", ".join(hits)))
        else:
            clear += 1
    print("\nTOOL ACCESS: %d screws, %d clear even in the finished arm, %d clear at their build step "
          "(covered later), %d BLOCKED at their step; %d components outside the sequence"
          % (len(screws), clear, len(later_only), len(fails), len(missing)))
    return len(fails) + len(missing)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
