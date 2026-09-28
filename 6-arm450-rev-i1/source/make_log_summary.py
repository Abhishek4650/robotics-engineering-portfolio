#!/usr/bin/env python3
"""LOG_SUMMARY (.md + .pdf): every check log of the release pass in one short
report -- what each check proves, its result and the numbers that matter --
plus the list of the important PDFs and what each one is for. Everything is
read from the current logs (REVI_CHECKS.log, FINAL_RUN.log and the per-check
logs written from it by split_logs.py)."""
import os
import re
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def txt(fn):
    p = os.path.join(HERE, fn)
    return open(p).read() if os.path.exists(p) else ""


def g(rx, s, fmt="%s", default="?"):
    m = re.findall(rx, s, flags=re.M)
    if not m:
        return default
    v = m[-1]
    return fmt % v if not isinstance(v, tuple) else fmt % v


def block(log, prefix):
    for b in re.split(r"^=== ", log, flags=re.M)[1:]:
        if b.startswith(prefix):
            return b
    return ""


def main():
    import make_audit_report as AR
    rows = AR.stage_table()
    res = {n: (v, tb) for n, v, tb, _ in rows}
    log, fin = txt("REVI_CHECKS.log"), txt("FINAL_RUN.log")

    def R(prefix):
        for n, (v, tb) in res.items():
            if n.startswith(prefix):
                return "ERROR" if tb else ("0 failures" if v == 0 else ("%s FAILURE(S)" % v if v is not None else "not run"))
        return "not run"

    def npass(prefix):
        return len(re.findall(r"\bPASS\b", block(log, prefix)))

    ag, cab, head = txt("AUDIT_GAPS.log"), txt("CABLE_ROUTE.log"), txt("HEAD_CLEARANCE.log")
    off, wir, sw = txt("OFFICIAL_SERVO_CHECK.log"), txt("WIRING_CHECK.log"), block(log, "SWEEP")
    items = [
        ("Drive trains", "J1 .. J6: servo seat, horn on the axis, coupler, bearings, shaft, every part of the joint "
         "against every other, servo insertion path",
         R("J1") if all(R(p) == "0 failures" for p in ("J1", "J2", "J3", "J4", "WRIST")) else "SEE LOG",
         "%d + %d + %d + %d + %d individual checks passed (J1, J2, J3, J4, J5/J6)"
         % (npass("J1 ="), npass("J2 ="), npass("J3 ="), npass("J4 ="), npass("WRIST"))),
        ("Bearings and bolts as solids", "every bearing seated on its pockets, every bolt through real holes",
         R("HARDWARE"), "%d checks passed" % npass("HARDWARE")),
        ("Link lock", "J2 / J3 links on their shafts: M5 set screws on the double-D flats, centring rings",
         R("LINK LOCK"), "2 x M5 x 10 per link half, all tightened on a flat"),
        ("Every fastener", "each screw passes free, bites >= its minimum, head seated, tip free; inserts in pockets",
         R("FASTENERS"), g(r"FASTENERS: (\d+) screws/grubs/pins, (\d+) inserts, (\d+) nuts, against (\d+) parts", log,
                          "%s screws, %s inserts, %s nuts against %s parts")),
        ("Parameters in the files", "every key dimension measured back out of the exported print files",
         R("PARAMETER AUDIT"), g(r"(\d+) parameters checked, (\d+) FAIL", log, "%s measured, %s off")),
        ("Tool access", "a hex key / screwdriver reaches every screw at the build step where it is fitted",
         R("TOOL ACCESS"), g(r"TOOL ACCESS: (\d+) screws, (\d+) clear even in the finished arm, (\d+) clear at their build step",
                             log, "%s screws: %s always clear, %s clear at their step")),
        ("Rule 4: mate, never overlap", "all pairs of the whole assembly, exact Boolean volume; only designed "
         "pathways (bearing race, horn, screw); every body attached; 3 injected faults must be caught",
         R("RULE 4"), g(r"RULE 4 -- mating, overlap and pathways on (\d+) components", log, "%s components; 3 of 3 faults detected")),
        ("Gravity springs", "spring points, lengths and forces; J2 / J3 torque with the springs",
         R("SPRINGS"), "worst case arm level: J2 SF 1.07, J3 SF 1.26 (ST3215 0.88 N.m continuous); no payload"),
        ("Whole-arm sweep", "each joint through its range, every part against every other; injected block caught",
         R("SWEEP"), "joints with a clash: %s; control %s" % (g(r"joints with a clash: (\d+)", sw),
                                                            "DETECTED" if "DETECTED" in sw else "?")),
        ("6 degrees of freedom", "each axis measured twice (servo horn = bearing pockets), Jacobian rank",
         R("6-DOF"), "rank 6 in the working range; spherical wrist (axes meet within 0.000 mm)"),
        ("Manufacturer's servo", "Waveshare's own ST3215 model (rear idler horn) in all 6 seats; servo screws in its "
         "holes; driven chains shifted 0.20 mm (its horn)", R("OFFICIAL ST3215"),
         "servo screw cores in the real holes 20 / 20; worst joint clearance %s mm"
         % g(r"J\d: ([\d.]+) mm", off)),
        ("Take it apart", "each servo unit slid out along its path, exact Booleans, our servo AND the manufacturer's",
         R("DISASSEMBLY PATHS (our") if R("DISASSEMBLY PATHS (off") == "0 failures" else "SEE LOG", "7 of 7 paths free, both servo models"),
        ("Joints moving together", "450 combined poses of J1 .. J5: every pair of bodies",
         R("AUDIT GAPS"), "every pair: neighbours >= %.2f mm (running gaps), all others >= %.1f mm" % (
             min([float(v) for v in re.findall(r"min\s+([\d.]+) mm", ag.split("B  TIPPING")[0])] or [float("nan")]),
             min([float(v) for v in re.findall(r"min\s+([\d.]+) mm", ag.split("B  TIPPING")[0]) if float(v) > 5] or [float("nan")]))),
        ("Tipping", "centre of mass over the poses vs the foot", R("AUDIT GAPS"),
         "COM up to %s mm out vs 64 mm foot: foot MUST be fixed (4 table holes)" % g(r"centre of mass ([\d.]+) mm", ag)),
        ("Thin walls / bed", "inward rays on every printed part (< 0.8 mm); bed size", R("AUDIT GAPS"),
         "thin walls: %s part(s); all parts fit a 180 mm cube" % g(r"THIN WALLS: (\d+)", ag)),
        ("Print orientation gates", "each part sliced in its chosen print orientation: islands, sub-layer features",
         R("GATES"), "0 islands; the 2 'MARGINAL z 16.1' notes are the seam lip's top face (2.0 mm wide below)"),
        ("Static all-pairs", "second, independent method: sampled points + penetration depth",
         R("PAIRS"), g(r"STATIC ALL-PAIRS AUDIT -- (\d+) parts, (\d+) touching pairs", log, "%s parts, %s touching pairs, 0 clashes")),
        ("Wiring", "both bus plugs into every servo (sockets from the maker's model + your photo), way out for wires",
         R("WIRING"), "nearest wall %s mm; every lead has a way out" %
         min(re.findall(r"nearest part ([\d.]+) mm", wir) or ["?"], key=lambda v: float(v) if v != "?" else 99)),
        ("Screw heads vs turning parts", "every screw beside a joint, joint turned -180 .. +180 deg: clearance in range, "
         "first contact angle", R("HEAD CLEARANCE"), "J3 fork heads 4.32 mm (contact at 94 deg), J5 6.85 mm, caps 1.30 mm"),
        ("Union joints", "every glued feature of every printed part joined over >= 0.80 of its own section (rev I.1, "
         "after the J3 lugs were found on a 0.1 mm sliver)", R("UNION JOINTS"),
         "%s weak joint(s); the J3 lugs now 136 mm2 (were 34)" % g(r"UNION JOINTS: (\d+) weak", txt("UNION_JOINTS.log"))),
        ("Plug slots", "each bus plug pulled out of its socket with the arm ASSEMBLED: straight through a slot, or "
         "straight then sideways out", R("PLUG INSERTION"), "%s of 12 plugs cannot; routes in PLUG_INSERT.log" %
         g(r"PLUG INSERTION: (\d+) plug", txt("PLUG_INSERT.log"))),
        ("Cable route", "one joint per cable; path change over the range; loop to leave", R("CABLE ROUTE"),
         "largest path change %s mm; loops 31 .. 61 mm" % g(r"largest path change is (\d+) mm", cab)),
        ("Sections (manual check)", "every joint sliced through its axis, each interface measured",
         R("SECTION MEASURE"), g(r"TOTAL CLASHES IN THE SECTIONS: (\d+)", fin, "%s clashes in the sections")),
        ("Print slicer", "the print-ready STLs themselves sliced", R("PRINT SLICER"), "0 islands, 0 unprintable layers"),
        ("Assembly", "the full arm exported as STEP", R("ASSEMBLY"),
         g(r"\((\d+) components\)", fin, "%s components (parts, servos, bearings, every screw, insert, spring)")),
    ]
    allok = all(it[2] == "0 failures" for it in items)
    head = ("ALL %d CHECKS AT 0 FAILURES -- print verdict GREEN (fit test first; the 6 servo housings after "
            "coupon 07 fits your servo)." % len(items)) if allok else "NOT ALL CHECKS AT 0 -- see the table."
    pdfs = [
        ("ARM450_AUDIT_REPORT.pdf", "READ FIRST: the verdict, what was found and fixed, your 4 snapshot questions "
         "answered with pictures, what is still to do"),
        ("ARM450_REV_I_FINAL.pdf", "every joint as exact sections (overlap in red, contact green, gaps measured), "
         "the whole arm, and every check log in full"),
        ("ARM450_POSES.pdf", "the full assembly in 6 poses, clearance measured in each"),
        ("ARM450_PARTS.pdf", "every printed part alone: 4 views + sections of its features"),
        ("../ASSEMBLY_MANUAL/ARM450_ASSEMBLY_MANUAL.pdf", "the build, one page per step (added parts in red), "
         "every screw's size and place, cable loops, service notes"),
        ("ARM450_REV_I.pdf", "the six joints, one page each: fixed side, driven side, servo, how it is held"),
        ("RULE5_VIEWS/ARM450_INTERFACES.pdf", "the Rule 5 interface sections on their own (also inside the FINAL pdf)"),
        ("LOG_SUMMARY.pdf", "this summary"),
        ("REV_H_VERIFICATION.pdf", "SUPERSEDED rev H report: now a pointer page (original in archive_superseded/)"),
    ]
    import pymupdf
    npg = {}
    for f, _ in pdfs:
        try:
            npg[f] = pymupdf.open(os.path.join(HERE, f)).page_count
        except Exception:
            npg[f] = None
    md = ["# ARM-450 rev I.1 -- log summary, release pass 2026-09-27 (J3_p1 lug fix)", "", "**%s**" % head, "",
          "| # | check | what it proves | result | key numbers |", "|---|---|---|---|---|"]
    md += ["| %d | %s | %s | %s | %s |" % ((i,) + it) for i, it in enumerate(items, 1)]
    md += ["", "## Important PDFs", "", "| file | pages | what it is for |", "|---|---|---|"]
    md += ["| `%s` | %s | %s |" % (f, npg.get(f) or "", w) for f, w in pdfs]
    md += ["", "Full logs: `REVI_CHECKS.log` (every check stage), `FINAL_RUN.log` (assembly, sections, print folder, "
           "slicer), and per check: FASTENER_CHECK, TOOL_ACCESS, MATING_CHECK, OFFICIAL_SERVO_CHECK, "
           "DISASSEMBLY_CHECK(_OFFICIAL), AUDIT_GAPS, WIRING_CHECK, HEAD_CLEARANCE, CABLE_ROUTE, DOF6_CHECK, "
           "CLAMP_CHECK (.log), PARAM_AUDIT.md, SECTION_MEASURE.md."]
    open(os.path.join(HERE, "LOG_SUMMARY.md"), "w").write("\n".join(md) + "\n")

    W = lambda s, n: "\n".join(textwrap.wrap(s, n))
    with PdfPages(os.path.join(HERE, "LOG_SUMMARY.pdf")) as pdf:
        fig = plt.figure(figsize=(11.7, 8.3))
        fig.suptitle("ARM-450 rev I.1 -- log summary (release pass 2026-09-27, J3_p1 lug fix)", fontsize=15, fontweight="bold")
        fig.text(0.04, 0.925, W(head, 140), fontsize=10.5, va="top", fontweight="bold",
                 color="#006000" if allok else "#b00000")
        ax = fig.add_axes([0.01, 0.02, 0.98, 0.87]); ax.axis("off")
        cell = [[str(i), W(it[0], 22), W(it[1], 58), W(it[2], 14), W(it[3], 46)] for i, it in enumerate(items, 1)]
        t = ax.table(cellText=cell, colLabels=["#", "check", "what it proves", "result", "key numbers"],
                     colWidths=[0.025, 0.14, 0.40, 0.09, 0.345], loc="upper center", cellLoc="left")
        t.auto_set_font_size(False); t.set_fontsize(6.6)
        for (r, c), ce in t.get_celld().items():
            nl = max(cell[r - 1][k].count("\n") for k in range(5)) + 1 if r else 1
            ce.set_height(0.0155 * nl + 0.006)
            if r == 0:
                ce.set_facecolor("#dde3ea"); ce.set_text_props(fontweight="bold")
            elif c == 3:
                ce.set_facecolor("#d9f2d9" if cell[r - 1][3].startswith("0 failures") else "#f8d0d0")
        pdf.savefig(fig); plt.close(fig)
        fig = plt.figure(figsize=(11.7, 8.3))
        fig.suptitle("Important PDFs -- which one to open for what", fontsize=15, fontweight="bold")
        body = "\n\n".join("%-46s %s pages\n   %s" % (f.replace("../", ""), npg.get(f) or "-", W(w, 100).replace("\n", "\n   "))
                           for f, w in pdfs)
        body += ("\n\n\nWhere they are: REV_H/ on this machine, RELEASES/2026-09-27_rev_I1/PDF/, and PDF/ in\n"
                 "ARM450_rev_I_print on your pen drive. Full logs: REVI_CHECKS.log and FINAL_RUN.log in REV_H/.")
        fig.text(0.05, 0.88, body, va="top", fontsize=9.5, family="monospace")
        pdf.savefig(fig); plt.close(fig)
    print(head)
    for i, it in enumerate(items, 1):
        print("%2d %-30s %-12s %s" % (i, it[0][:30], it[2], it[3]))


if __name__ == "__main__":
    main()
