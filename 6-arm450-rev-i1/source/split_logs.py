#!/usr/bin/env python3
"""Write each stage of the release pass (REVI_CHECKS.log) back into the per-check
log that the documents quote, so no PDF page ever shows an older run."""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
MAP = [("LINK LOCK", "CLAMP_CHECK.log"), ("6-DOF", "DOF6_CHECK.log"), ("TOOL ACCESS", "TOOL_ACCESS.log"),
       ("FASTENERS", "FASTENER_CHECK.log"), ("RULE 4", "MATING_CHECK.log"), ("OFFICIAL ST3215", "OFFICIAL_SERVO_CHECK.log"),
       ("DISASSEMBLY PATHS (our", "DISASSEMBLY_CHECK.log"), ("DISASSEMBLY PATHS (official", "DISASSEMBLY_CHECK_OFFICIAL.log"),
       ("AUDIT GAPS", "AUDIT_GAPS.log"), ("WIRING", "WIRING_CHECK.log"), ("HEAD CLEARANCE", "HEAD_CLEARANCE.log"),
       ("CABLE ROUTE", "CABLE_ROUTE.log"), ("PLUG INSERTION", "PLUG_INSERT.log"),
       ("UNION JOINTS", "UNION_JOINTS.log")]


def main():
    log = open(os.path.join(HERE, "REVI_CHECKS.log")).read()
    blocks = {b.split(" ===", 1)[0]: b.split("\n", 1)[1] if "\n" in b else "" for b in re.split(r"^=== ", log, flags=re.M)[1:]}
    for prefix, fn in MAP:
        hit = [v for k, v in blocks.items() if k.startswith(prefix)]
        if hit:
            open(os.path.join(HERE, fn), "w").write(hit[0])
            print("%-32s <- %s" % (fn, prefix))
        else:
            print("%-32s NOT IN THE PASS" % fn)


if __name__ == "__main__":
    main()
