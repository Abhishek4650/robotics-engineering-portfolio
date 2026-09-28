#!/usr/bin/env python3
"""
FINAL_PRINT/ -- the printable set, separated as a shipping design would be
(Rule 3 item 14 / user item 18). Each STL is rotated into its gated print
orientation (PRINT_ORIENTATION.json: 0 islands, least overhang), set on the
bed (z = 0) and centred, named <nn>_<part>_x<qty>.stl. The STEPs are copied in
their design frame for reference.
"""
import json
import cadquery as cq
import os
import shutil
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "PRINT_GATE"))
import orient_gate as OG          # noqa: E402

OUT = os.path.join(ROOT, "FINAL_PRINT")
REL = os.path.join(ROOT, "out_cad")

# (part, qty, source folder, note)
PARTS = [
    ("base", 1, HERE, "rev I: lower 6806 pocket opens from underneath"),
    ("spigot_collar", 1, HERE, "split clamp + J1 collet closer, slot 2.0, 1 x M3 pinch bolt"),
    ("j1_mount", 1, HERE, "J1 servo mount + the arm's foot"),
    ("j1_hub", 1, HERE, "J1 horn coupler, D-keys the turret"),
    ("J2_turret_p1", 1, HERE, "turret; spigot end slit as a collet (J1 zero play); land on the 6806 inner ring only"),
    ("J2_turret_p2", 1, HERE, "J2 servo pod (2.4 shell round the whole servo), 4 x M3x45 split bolts"),
    ("J2_shaft", 1, HERE, "printed J2 shaft, bolts to the horn; double-D flats for the M5 set screws"),
    ("shaft_clamp", 4, HERE, "link centring ring (0.025 fits); links locked by 2 x M5 set screws each"),
    ("link_upper_groove", 1, REL, "released, unchanged (reuse your printed one)"),
    ("link_upper_tongue", 1, HERE, "rev I: released + head counterbores (or drill yours: O6.0x3.2 seam, O5.0x2.7 ear)"),
    ("collar_upper", 2, HERE, "J2 spring collar, print 2 (same part)"),
    ("J3_p1", 1, HERE, "J3 fork; J3 spring lugs (both pockets)"),
    ("J3_p2", 1, HERE, "J3 servo cradle, bay 34.99 deep, 2.4 back wall"),
    ("J3_shaft", 1, HERE, "printed J3 shaft, double-D flats for the M5 set screws"),
    ("link_fore_tongue", 1, HERE, "rev I forearm: socket end, valid solid, flush seam-screw heads"),
    ("link_fore_groove", 1, HERE, "rev I forearm: socket end, valid solid"),
    ("collar_fore", 2, HERE, "J3 spring collar, print 2 (same part)"),
    ("j4_base", 1, HERE, "J4 servo base; lip tops relieved off the 6706 inner ring"),
    ("j4_cap", 1, HERE, "J4 cap, holds the 6706"),
    ("j4_hub", 1, HERE, "J4 hub, carries the J5 fork"),
    ("J5_p1", 1, HERE, "J5 fork"),
    ("J5_p2", 1, HERE, "J5 servo cradle, bay 34.99 deep, 2.4 back wall"),
    ("J5_shaft", 1, HERE, "printed J5 axle"),
    ("J5_spacer", 2, HERE, "blade spacers, exactly 3.0 (close the J5 stack), print 2"),
    ("j6_body", 1, HERE, "J5 blade + J6 servo housing"),
    ("j6_cap", 1, HERE, "J6 cap, holds the 6706"),
    ("j6_flange", 1, HERE, "tool flange, bolts to the J6 horn"),
]


def main():
    plan = json.load(open(os.path.join(HERE, "PRINT_ORIENTATION.json")))
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "STL_print_ready")); os.makedirs(os.path.join(OUT, "STEP_design_frame"))
    rows = []
    for i, (nm, q, src, note) in enumerate(PARTS, 1):
        p = plan.get(nm, {"orient": "+Z up", "supports": "see note"})
        key = p["orient"].split(" (")[0]
        m = trimesh.load(os.path.join(src, nm + ".stl"))
        m.apply_transform(OG.ORIENTS[key])
        m.apply_translation([-m.bounds[:, 0].mean(), -m.bounds[:, 1].mean(), -m.bounds[0][2]])
        fn = "%02d_%s_x%d.stl" % (i, nm, q)
        m.export(os.path.join(OUT, "STL_print_ready", fn))
        if os.path.exists(os.path.join(src, nm + ".step")):
            shutil.copy(os.path.join(src, nm + ".step"), os.path.join(OUT, "STEP_design_frame", nm + ".step"))
        ext = m.bounds[1] - m.bounds[0]
        rows.append((fn, q, p["orient"], p["supports"], "%.0f x %.0f x %.0f" % tuple(ext), note, m.is_watertight))
        print("  %-34s qty %d  %-8s supports %-22s %s  watertight %s" % (fn, q, key, p["supports"], "%.0fx%.0fx%.0f" % tuple(ext), m.is_watertight))
    with open(os.path.join(OUT, "_print_list.json"), "w") as f:
        json.dump(rows, f, indent=1)
    # Rule 5: the files to print, and nothing else, in their own folder
    pf = os.path.join(ROOT, "PRINTABLE_FILES")
    if os.path.isdir(pf):
        shutil.rmtree(pf)
    os.makedirs(pf)
    for fn, q, orient, sup, size, note, wt in rows:
        shutil.copy(os.path.join(OUT, "STL_print_ready", fn), os.path.join(pf, fn))
    with open(os.path.join(pf, "PRINT_LIST.txt"), "w") as f:
        f.write("ARM-450 rev I -- printable files. Each STL is already turned to its checked print\n"
                "orientation and sits on the bed. Print the quantity in the file name (_xN).\n\n")
        f.write("%-36s %3s  %-6s %-9s %s\n" % ("file", "qty", "orient", "supports", "size mm"))
        for fn, q, orient, sup, size, note, wt in rows:
            f.write("%-36s %3d  %-6s %-9s %s\n" % (fn, q, orient.split(" (")[0], sup, size))
        f.write("\n%d files, %d pieces. Hardware, springs and the build order: FINAL_PRINT/README.md\n"
                % (len(rows), sum(r[1] for r in rows)))
    # fit test first: the critical fits on the user's own printer (gen_fit_coupon.py)
    import gen_fit_coupon as FC
    ft = os.path.join(pf, "00_FIT_TEST_print_first")
    os.makedirs(ft)
    for nm_, sh_ in FC.parts().items():
        cq.exporters.export(sh_, os.path.join(ft, nm_ + ".stl"), tolerance=0.01, angularTolerance=0.1)
    open(os.path.join(ft, "README.txt"), "w").write(FC.__doc__)
    print("printable files ->", pf, "(+ %d fit-test coupons)" % len(FC.parts()))
    print("\n%d files, %d pieces to print" % (len(rows), sum(r[1] for r in rows)))


if __name__ == "__main__":
    main()
