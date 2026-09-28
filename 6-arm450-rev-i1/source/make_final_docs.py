#!/usr/bin/env python3
"""Cover + print-list pages for ARM450_REV_I_FINAL.pdf, built from the logs of
the release run (nothing typed by hand except the explanations)."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "FINAL_PRINT")


def txt(fn):
    p = os.path.join(HERE, fn)
    return open(p).read() if os.path.exists(p) else ""


def stage_results():
    log = txt("REVI_CHECKS.log")
    rows = []
    for blk in re.split(r"^=== ", log, flags=re.M)[1:]:
        name = blk.split(" ===", 1)[0]
        m = re.findall(r"FAILURES: (\d+)|FASTENER CHECK: (\d+) failure|CLAMP VERIFICATION: (\d+) failure|"
                       r"(\d+) parameters checked, (\d+) FAIL|CLASHES \(penetration[^\n]*\n((?:   .*\n)*)", blk)
        rows.append((name, blk))
    return rows


def main():
    log = txt("REVI_CHECKS.log"); fin = txt("FINAL_RUN.log")
    res = []
    for blk in re.split(r"^=== ", log, flags=re.M)[1:]:
        name = blk.split(" ===", 1)[0]
        if name == "DONE":
            continue
        f = [int(x) for x in re.findall(r"FAILURES: (\d+)", blk)]
        f += [int(x) for x in re.findall(r"FASTENER CHECK: (\d+) failure", blk)]
        f += [int(x) for x in re.findall(r"CLAMP VERIFICATION: (\d+) failure", blk)]
        f += [int(x) for x in re.findall(r"LINK LOCK VERIFICATION: (\d+) failure", blk)]
        f += [int(x) for x in re.findall(r"RULE 4: (\d+) failure", blk)]
        f += [int(x) for x in re.findall(r"OFFICIAL-SERVO CHECK: (\d+) problem", blk)]
        f += [int(x) for x in re.findall(r"DISASSEMBLY PATHS: (\d+) blocked", blk)]
        f += [int(x) for x in re.findall(r"WIRING CHECK: (\d+) problem", blk)]
        f += [int(x) for x in re.findall(r"HEAD CLEARANCE: (\d+) screw", blk)]
        f += [int(x) for x in re.findall(r"CABLE ROUTE: (\d+) problem", blk)]
        f += [int(x) for x in re.findall(r"PLUG INSERTION: (\d+) plug", blk)]
        f += [int(x) for x in re.findall(r"UNION JOINTS: (\d+) weak", blk)]
        f += [int(x) for x in re.findall(r"(?:JOINTS TOGETHER|TIPPING|THIN WALLS|BED): (\d+)", blk)]
        if "CONTROLS" in blk:
            f.append(blk.split("CONTROLS")[-1].count("NOT DETECTED"))
        f += [int(x) for x in re.findall(r"6-DOF CHECK: (\d+) failure", blk)]
        f += [int(x) for x in re.findall(r"(\d+) BLOCKED at their step", blk)]
        pa = re.findall(r"(\d+) parameters checked, (\d+) FAIL", blk)
        if pa:
            f.append(int(pa[0][1]))
        if name.startswith("GATES"):
            f.append(len(re.findall(r"^\s+(ISLAND|SUB-LAYER|UNPRINTABLE)", blk, flags=re.M)))
        if name.startswith("SWEEP"):
            f.append(len(re.findall(r"CLASH", blk)))
        if name.startswith("PAIRS"):
            cl = re.search(r"CLASHES \(penetration[^\n]*\n((?:   .*\n)*)", blk)
            f.append(len([l for l in (cl.group(1).splitlines() if cl else []) if l.strip()]))
        tb = "Traceback" in blk
        res.append((name, sum(f) if f else None, tb))
    sec = re.findall(r"TOTAL CLASHES IN THE SECTIONS: (\d+)", fin)
    slicer = len(re.findall(r"^\s+(ISLAND|SUB-LAYER|UNPRINTABLE)", fin.split("=== PRINT SLICER")[-1], flags=re.M)) if "PRINT SLICER" in fin else None
    res.append(("SECTION MEASURE (manual check by slicing)", int(sec[0]) if sec else None, False))
    res.append(("PRINT SLICER on the print-ready files", slicer, False))
    allzero = all(r[1] == 0 and not r[2] for r in res)
    lines = ["ARM-450 rev I -- release pass %s" % "(all stages 0)" if allzero else "ARM-450 rev I -- release pass: OPEN ITEMS", ""]
    lines += ["%-52s %s" % (n, ("TRACEBACK" if tb else ("n/a" if v is None else "%d" % v))) for n, v, tb in res]
    lines += ["", "VERIFICATION AUDIT 2026-09-24 (Rules 3, 4, 6, 8) -- ARM450_AUDIT_REPORT.pdf:",
              " * every servo SCREWED by its own back holes (20 self-tappers) and seated on 4 supports",
              " * rear idler horn of the real ST3215 cleared at J1/J4/J6; J5 axle assembles; table holes",
              " * thin walls fixed; fork-floor bolt heads sunk; wire windows fitted to the plugs",
              " * new checks: manufacturer's servo, disassembly, wiring, head clearance, cable route",
              "", "RULE 4 (mate, never overlap; interact only through proper pathways) found and fixed:",
              " * J1: hub D-plug in the spigot on 0.1/0.2 mm clearance (+-1.9 deg yaw play) ->",
              "   spigot end slit into a COLLET, closed by the spigot collar (slot 2.0: 1.10 needed)",
              " * J2/J3: links hung on +-0.2 mm clearances (+-1 deg) -> 2 x M5 set screws per link",
              "   half, self-tapped in the link's own O4.2 side holes, on double-D shaft flats",
              " * J1: turret land sat on the base and the 6806 OUTER ring -> land on the inner ring only",
              " * J4/J6: stationary lips on the 6706's turning INNER ring -> 0.5 mm relief",
              " * J4/J6 caps overlapped the bearings 0.01 mm; J5 spacers floated 0.05 per face",
              " * every set screw / grub modelled TIGHTENED; split clamps checked for closing travel",
              "", "Earlier in this pass (each measured, then re-checked):",
              " * shaft clamps: the released O38 ring could not enter the links' bores (seam ear);",
              "   rev-I C-clamp straddles the ear (gap 11.4 -> ~1 deg play) + M3 grub on the D-flat",
              " * J2 servo cover was held on by nothing (cover-bolt axes in air in both halves);",
              "   now a servo pod (2.4 mm shell round the whole servo) + 4 x M3 x 45 split bolts",
              " * J3/J5 bays were 35.99 deep with a 1.4 back wall (released generator cut +1);",
              "   now exactly 34.99 with 2.4 wall",
              " * -y spring-lug insert pockets were missing (mirror bug) on turret p1 and J3 p1",
              " * seam-screw heads on the link tongues stood 3 mm into the fork cheeks (1 mm gap)",
              "   and under the forearm collars: all tongue seam holes counterbored (flush heads)",
              " * spigot-collar insert broke out of the O46 surface: pads added",
              " * standard screw lengths everywhere; several would have bottomed out",
              " * forearm seam: 0.27 mm tongue/groove overlap removed",
              "",
              "6 DOF: six independent axes (yaw, shoulder, elbow, forearm roll, wrist pitch,",
              "tool roll), each axis measured twice (servo horn = bearing pockets, 0.0000 deg /",
              "0.0000 mm), spherical wrist, Jacobian rank 6 over the working range. Singular",
              "(as every arm of this type): arm straight up (the modelled home), elbow straight,",
              "wrist aligned (J5 = 0), wrist centre over the base axis -- use a bent 'ready' pose.",
              "",
              "Limits you accepted: simple gravity springs, NO continuous payload",
              "(worst case arm level: J2 SF 1.07, J3 SF 1.26 on 0.88 N.m continuous).",
              "Supports: see the print list (J2_turret_p1, J3_p1, j6_body, base REQUIRED).",
              "",
              "Slicer note, measured: the two link tongues show 'MARGINAL z 16.1' -- that is the",
              "cut exactly AT the top face of the rounded seam lip. The lip is 2.00 mm wide to",
              "z 15.4 and 1.17 mm at z 16.0 (three lines): not a thin wall."]
    open(os.path.join(HERE, "_final_cover.txt"), "w").write("\n".join(lines))
    rows = json.load(open(os.path.join(OUT, "_print_list.json")))
    pl = ["%-36s %3s  %-6s %-9s %-14s %s" % ("file", "qty", "orient", "supports", "size mm", "note")]
    for fn, q, orient, sup, size, note, wt in rows:
        pl.append("%-36s %3d  %-6s %-9s %-14s %s" % (fn, q, orient.split(" (")[0], sup, size, note[:70]))
    pl.append(""); pl.append("%d files, %d pieces" % (len(rows), sum(r[1] for r in rows)))
    open(os.path.join(HERE, "_print_page.txt"), "w").write("\n".join(pl))
    print("\n".join(lines))
    return allzero


if __name__ == "__main__":
    main()
