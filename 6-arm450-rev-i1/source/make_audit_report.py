#!/usr/bin/env python3
"""ARM450_AUDIT_REPORT (.md + .pdf): the Rule 3 / 4 / 6 re-verification of
2026-09-24 -- what was missing, what was fixed, what is still open. Every
number in the rule table is read from the logs of the release pass that ran
after the fixes (REVI_CHECKS.log, FINAL_RUN.log, DOCS_RUN.log)."""
import os
import re
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VIEWS = os.path.join(HERE, "RULE6_VIEWS")
sys.path.insert(0, HERE)


def txt(fn):
    p = os.path.join(HERE, fn)
    return open(p).read() if os.path.exists(p) else ""


def stage_table():
    log = txt("REVI_CHECKS.log"); fin = txt("FINAL_RUN.log")
    rows = []
    for blk in re.split(r"^=== ", log, flags=re.M)[1:]:
        name = blk.split(" ===", 1)[0]
        if name == "DONE":
            continue
        f = [int(x) for x in re.findall(r"FAILURES: (\d+)", blk)]
        for rx in (r"FASTENER CHECK: (\d+) failure", r"CLAMP VERIFICATION: (\d+) failure", r"LINK LOCK VERIFICATION: (\d+) failure",
                   r"RULE 4: (\d+) failure", r"6-DOF CHECK: (\d+) failure", r"(\d+) BLOCKED at their step",
                   r"OFFICIAL-SERVO CHECK: (\d+) problem", r"DISASSEMBLY PATHS: (\d+) blocked",
                   r"(?:JOINTS TOGETHER|TIPPING|THIN WALLS|BED): (\d+)", r"WIRING CHECK: (\d+) problem", r"HEAD CLEARANCE: (\d+) screw", r"CABLE ROUTE: (\d+) problem", r"PLUG INSERTION: (\d+) plug", r"UNION JOINTS: (\d+) weak"):
            f += [int(x) for x in re.findall(rx, blk)]
        pa = re.findall(r"(\d+) parameters checked, (\d+) FAIL", blk)
        if pa:
            f.append(int(pa[0][1]))
        if name.startswith("GATES"):
            f.append(len(re.findall(r"^\s+(ISLAND|SUB-LAYER|UNPRINTABLE)", blk, flags=re.M)))
        if name.startswith("SWEEP"):
            f.append(len(re.findall(r"CLASH", blk)))
        if name.startswith("PAIRS"):
            cl = re.search(r"CLASHES \(penetration[^\n]*\n((?:   .*\n)*)", blk)
            f.append(len([ln for ln in (cl.group(1).splitlines() if cl else []) if ln.strip()]))
        if "CONTROLS" in blk:
            f.append(blk.split("CONTROLS")[-1].count("NOT DETECTED"))
        rows.append((name, sum(f) if f else None, "Traceback" in blk, blk))
    if "=== WIRING" not in log and txt("WIRING_CHECK.log"):          # run on its own this round
        w = txt("WIRING_CHECK.log"); m = re.findall(r"WIRING CHECK: (\d+) problem", w)
        rows.append(("WIRING (both bus plugs in every servo, way out)", int(m[-1]) if m else None, "Traceback" in w, w))
    for nm, rx in (("ASSEMBLY", None), ("SECTION MEASURE", r"TOTAL CLASHES IN THE SECTIONS: (\d+)")):
        part = [b for b in re.split(r"^=== ", fin, flags=re.M)[1:] if b.startswith(nm)]
        b = part[-1] if part else ""
        v = (int(re.findall(rx, b)[-1]) if rx and re.findall(rx, b) else (0 if b and "--- exit 0" in b else None))
        rows.append((b.split(" ===", 1)[0] if b else nm, v, "Traceback" in b, b))
    part = fin.split("=== PRINT SLICER")[-1] if "PRINT SLICER" in fin else ""
    rows.append(("PRINT SLICER on the print-ready files",
                 len(re.findall(r"^\s+(ISLAND|SUB-LAYER|UNPRINTABLE)", part, flags=re.M)) if part else None, False, part))
    doc = txt("DOCS_RUN.log")
    for b in re.split(r"^=== ", doc, flags=re.M)[1:]:
        n = b.split(" ===", 1)[0]
        # only the document builds that carry results; this report's own step is
        # still running when it reads the log (it counted itself as a failure once)
        if n.startswith(("FINAL PDF", "POSES + PARTS", "EDITABLE CAD")):
            rows.append((n, 0 if "--- exit 0" in b and "Traceback" not in b else 1, "Traceback" in b, b))
    return rows


def stage(rows, prefix):
    for n, v, tb, b in rows:
        if n.startswith(prefix):
            return v, tb, b
    return None, False, ""


def res(rows, *prefixes):
    vals = [stage(rows, p) for p in prefixes]
    if any(v is None for v, _, _ in vals):
        return "NOT RUN"
    if any(tb for _, tb, _ in vals):
        return "ERROR"
    s = sum(v for v, _, _ in vals)
    return "0 failures" if s == 0 else "%d FAILURE(S)" % s


def verdict(v):
    """cell colour of a result: green clean, yellow unknown, red otherwise."""
    if "UNKNOWN" in v or "MODIFICATION" in v or "not modelled" in v:
        return "#fff2cc"
    if re.search(r"FAILURE|ERROR|NOT RUN|\?|\b[1-9]\d* (part|pair|problem)", v) or v.startswith("0 pages"):
        return "#f8d0d0"
    return "#d9f2d9"


def pdf_pages(fn):
    try:
        import fitz
        return fitz.open(os.path.join(HERE, fn)).page_count
    except Exception:
        return 0


def grab(block, rx):
    m = re.findall(rx, block)
    return m[-1] if m else "?"


def rule_matrix(rows):
    ag = stage(rows, "AUDIT GAPS")[2]
    walls = grab(ag, r"THIN WALLS: (\d+)"); tip = grab(ag, r"TIPPING: (\d+)"); bed = grab(ag, r"BED: (\d+)")
    jt = grab(ag, r"JOINTS TOGETHER: (\d+)")
    npar = grab(stage(rows, "PARAMETER AUDIT")[2], r"(\d+) parameters checked")
    pp, pa, fp = pdf_pages("ARM450_POSES.pdf"), pdf_pages("ARM450_PARTS.pdf"), pdf_pages("ARM450_REV_I_FINAL.pdf")
    return [
        ("3", "Manual verification by slicing", "every joint cut through its axis, exact solids, each interface measured",
         res(rows, "SECTION MEASURE")),
        ("3", "Pockets and holes on the right faces; parameters proven in the CAD",
         "%s parameters measured back out of the exported files" % npar, res(rows, "PARAMETER AUDIT")),
        ("3", "No thin walls", "inward rays on every printed part, walls < 0.8 mm (two lines)",
         "%s part(s) (upper GROOVE 0.5 mm skin accepted: already printed)" % walls),
        ("3", "Servo seated on the right face, locked, driving the next link",
         "J1..J6 drive trains part against part; link lock; YOUR servo model AND the manufacturer's STEP in all 6 seats",
         res(rows, "J1", "J2", "J3", "J4", "WRIST", "LINK LOCK", "OFFICIAL ST3215") +
         "; each servo SCREWED by its own back holes (M1: 20 screws, core in the manufacturer's holes)"),
        ("3", "Tool / hand reach", "hex key to every screw at its build step", res(rows, "TOOL ACCESS")),
        ("3", "Rigid, joints in sync", "450 combined poses of J1..J5 together; 6 DOF (axes two ways, Jacobian rank)",
         "%s pair(s) too close; 6-DOF %s" % (jt, res(rows, "6-DOF"))),
        ("3", "Stands up in use (new)", "centre of mass over the 450 poses vs the foot",
         "%s problem(s) with the foot fixed by its 4 new table holes" % tip),
        ("3", "Wiring clearance", "both bus plugs in all 6 servos (sockets from the manufacturer's STEP, plug from "
         "your photo), exact solids; free run for the wires from each lead",
         "%s problem(s); nearest wall %s mm; control detected. Route through the joints: see Rule 8 cables" % (grab(txt("WIRING_CHECK.log"), r"WIRING CHECK: (\d+)"),
                                          min(re.findall(r"nearest part ([\d.]+) mm", txt("WIRING_CHECK.log")) or ["?"],
                                              key=lambda v: float(v) if v != "?" else 99))),
        ("3", "Assemble / disassemble any time", "each unit slid out along its path, exact booleans, both servo models",
         res(rows, "DISASSEMBLY PATHS (our", "DISASSEMBLY PATHS (off")),
        ("3", "Bought hardware real", "every screw, insert, nut, bearing, spring as a solid",
         res(rows, "HARDWARE", "FASTENERS", "SPRINGS")),
        ("3", "Printable files, separate folder", "print orientation gates, slicer on the print-ready STLs, bed size",
         "%s; bed: %s part(s) too big" % (res(rows, "GATES", "PRINT SLICER"), bed)),
        ("4", "Mate on coincident planes, never overlap", "all pairs of solids, exact boolean volume; whole-arm sweep",
         res(rows, "PAIRS", "SWEEP")),
        ("4", "Touch only through designed pathways (bearing rings, horn, screws)",
         "every contact classified; a body may meet the next only at its bearing race / horn / screw; controls injected",
         res(rows, "RULE 4")),
        ("4", "Every part attached, nothing floating", "each body reached from its servo through touching contacts",
         res(rows, "RULE 4")),
        ("8", "Every servo seated, never floating", "each servo's back plateau on >= 4 supports near both ends "
         "(face measured in the STLs) + Rule 4 planar mates", res(rows, "PARAMETER AUDIT", "RULE 4")),
        ("8", "Screw heads beside a turning part", "every screw vs every joint turned -180..+180 deg: clearance in "
         "range >= 1.0 mm, contact angle reported", res(rows, "HEAD CLEARANCE")),
        ("8", "Cables cannot wind up", "one cable per joint; path change over the range measured; loops sized",
         res(rows, "CABLE ROUTE", "WIRING")),
        ("6", "Full assembly in different poses", "ARM450_POSES.pdf, clearance measured in each pose",
         "%d pages, %s" % (pp, res(rows, "POSES + PARTS"))),
        ("6", "Part by part, with details", "ARM450_PARTS.pdf: each part 4 views + axis sections of its features",
         "%d pages" % pa),
        ("6", "Sharp interface pictures (Rule 5)", "ARM450_REV_I_FINAL.pdf: exact sections per joint, overlap in red",
         "%d pages, %s" % (fp, res(rows, "FINAL PDF"))),
    ]


FOUND = [
    ("rev I.1 -- J3 fork p1: both spring lugs joined to the cheeks by a 0.1 mm sliver (your slicer view, 2026-09-27)",
     "The J3 spring lugs stood on the ROUND tops of the fork cheeks with their base at the arc's apex: +y lug base "
     "z 246.80 on an apex of 246.91, -y lug 233.90 on 234.00. Joined by a 0.10-0.11 mm sliver (2.2 / 2.6 mm3 of "
     "overlap), corners 0.40 mm in the air, sharp notches on both sides; joint area 34-35 mm2 against the lug's own "
     "75 mm2 section. The part was still ONE solid in the STEP, so no check saw it.",
     "Each lug is now SUNK 1.5 mm into its cheek below the arc at its edges (the generator asserts it never reaches the "
     "bearing pocket or any hole) and blended into the arc by R3 concave webs drawn in the cheek's plane: joint area "
     "136 mm2. Spring pin position unchanged. New permanent check verify_union_joints.py: every glued feature of every "
     "printed part must be joined over at least 0.80 of its own section (all others read 1.00 or more).",
     ["j3_lug_fix.png"]),
    ("The real ST3215 has a REAR IDLER HORN (O19.2, turns with the output)",
     "Manufacturer's model (Waveshare ST3215-3D.zip) vs your Motor.stl: same case, but Motor.stl has no idler horn. "
     "Seated in the arm, the idler cut 169 mm3 into the back of the J1 foot, the J4 base and the J6 body -- all three "
     "would have jammed their servo.",
     "O20.4 x 4.35 pocket round the output axis in j1_mount, j4_base, j6_body (0.6 mm radial and axial). The fork bays "
     "J2/J3/J5 already clear it by 0.95 mm. New permanent check: verify_official_servo.py.",
     ["idler_compare.png", "idler_cut_J1.png", "idler_cut_J4.png", "idler_cut_J6.png"]),
    ("The real drive horn stands 0.20 mm further out than in Motor.stl",
     "Every shaft, hub and flange bolted to a horn therefore sits 0.20 mm further along its axis.",
     "Checked, no change needed: with each driven chain shifted 0.20 mm, every joint keeps >= 0.30 mm running clearance.",
     []),
    ("The J5 wrist could not be assembled or taken apart",
     "The J5 axle's flat covered only its middle 31 mm; the round idle end jammed in the blade's D-bore (exact solids: "
     "30 mm3) whichever way it was pushed. Only the final position had ever been checked.",
     "The flat now runs out of the axle's idle end. All 7 assembly / disassembly paths are free with our servo model AND "
     "the manufacturer's. New permanent check: verify_disassembly.py.", []),
    ("The arm falls over unless the foot is fixed down",
     "At full reach the centre of mass (~1.5 kg arm) is 118 mm from the J1 axis; the foot's radius is 64 mm.",
     "4 x O5.5 table holes in the foot plate (r 58, between the columns): M5 bolts or #10 wood screws, driven before "
     "the base goes on. Or clamp the foot.", []),
    ("Thin walls a slicer would drop or print as one fragile line",
     "Inward rays on every part: base foot floor 0.5 mm over ~5100 mm2 (the released recess was written for a 7.0 mm "
     "foot; the foot became 5.5); J3/J5 servo-cover walls 0.06-0.5 mm at the far end of the bay; J4 cap 0.15 mm beside "
     "the bolt counterbores; J6 bosses 0.44 mm round the inserts; spigot-collar pad 0.5 mm over the head counterbore; "
     "centring-ring gap corners a 17 deg knife edge; forearm / tongue cable-bore skin 0.5 mm.",
     "Base floor 3.0; 2.4 mm shell round the J3 / J5 bays; J4 cap sides +1.45; J6 bosses O21.6; collar pad +0.8; ring "
     "corners squared; cable skin 1.2 (forearm, upper tongue). Accepted: your already-printed upper GROOVE keeps its "
     "0.5 mm cable skin (bottom layers on the bed, carries no load).", []),
    ("Printer tolerance vs the tight fits",
     "The key fits are finer than FDM accuracy (+-0.1..0.2 mm): bearing seats O42.00 / O37.02, printed shafts O29.95 "
     "in 30 mm bores, the -0.22 servo pinch, the 0.025 mm centring-ring fit.",
     "PRINTABLE_FILES/00_FIT_TEST_print_first: 6 small coupons (~1.5 h) with exactly those fits. Print them first and "
     "tune the slicer's XY hole / contour compensation before the big parts.", []),
    ("A checker reported disassembly paths as BLOCKED that are free",
     "audit_gaps.py section E swept the units with FCL mesh depth: it read the designed press fits (bearings) and the "
     "-0.22 servo pinch as obstructions (J4/J6 'deepest contact 25.6 mm', J1 1.7 mm on a pressed bearing).",
     "Removed; disassembly is judged only by verify_disassembly.py (exact OCC booleans, with a baseline for the fit "
     "each unit starts in, both servo models).", []),
    ("One of my own audit fixes broke Rule 4 -- caught by the re-run",
     "The 1.2 mm cable-skin fill added to the upper tongue ran 0.5 mm past the link's end face into the J3 fork "
     "(exact solids: 1.2 mm3 overlap; the part grew from x 85.0 to 85.5). The Rule 4 check flagged it as the only failure.",
     "The fill now ends exactly at the end face, and the generator refuses to export if the tongue runs past it. "
     "Whole release pass run again on the corrected part.", []),
    ("J1 foot: the locating end wall was 0.6 mm thin over the lip height",
     "The O31 clearance bore for the hub flange cut the 6.0 mm end wall down to a 0.6 mm crescent (44 mm2) from the "
     "cap face to the lip top -- found by the thin-wall check once it judged areas instead of single points.",
     "End wall 7.0 mm (outward only; the servo seat is unchanged): 1.6 mm at its thinnest.", []),
    ("A checker's mesh was coarser than its own threshold",
     "The static all-pairs check (PAIRS) meshed the released upper groove at 0.4 mm deflection and judged clashes at "
     "0.15 mm: it reported the 0.025 mm centring-ring fit as a 0.15 mm clash, and it MISSED the real 1.2 mm3 tongue "
     "overlap (too few sample points in so small a volume). Both exact checks (Rule 4 booleans, joint sections) "
     "measured the ring fit as 0.025 mm clear and caught the tongue.",
     "PAIRS now uses the groove's own fine STL (115 756 faces) and its exact solid for containment. The exact Boolean "
     "checks remain the authority; PAIRS is the independent second method.", []),
    ("The J6 servo's rear boss snagged the new screw bridge -- and a checker hid it",
     "The pads keep a channel clear over the servo's raised back features so the servo can slide in; it was 2.35 mm "
     "deep, sized for the idler horn (2.04 above the plateau) -- but the bare rear boss (as on your servo) stands "
     "2.589 above it: the J6 servo would catch 0.24 mm on the bridge while sliding in. The insertion check "
     "(verify_wrist) caught it; the exact disassembly sweep did not, because it compared the total overlap with the "
     "housing against the starting pinch -- and the pinch overlap SHRINKS as the servo slides out, hiding the 6.5 mm3.",
     "Channel 2.9 deep on every pad (0.31 over the boss). The disassembly sweep now judges each servo by its core "
     "(everything but its two pinched side strips): shown to report the snag (+6.53 mm3 at 32 mm) before the fix, "
     "free after it.", []),
]

CLEAN = [
    "Joints moving TOGETHER: 450 combined poses (J1 x J2 x J3 x J4 x J5): every pair of neighbouring bodies keeps "
    ">= 0.47 mm (running gaps), every other pair >= 15 mm.",
    "Bed: every part fits a 180 mm cube (the largest, the forearm tongue, is 144 mm).",
    "Wiring (new check, verify_wiring.py): both bus plugs fit in all 6 servos -- sockets from the manufacturer's STEP "
    "at the place your photo shows, plug as wide as its socket -- nearest wall 1.0 mm (J2/J3/J5 cover windows) to "
    "2.45 mm; the wires leave straight out through the J2/J3/J5 windows, along the channel at J1/J4, and at J6 "
    "2 mm further out, then over the new screw bridge. Your photo "
    "shows the rear boss without an idler horn; the seats clear the idler horn either way.",
    "Every earlier check re-run on the fixed geometry, see the stage table.",
]

MODIFY = [
    ("M1 (done). Every servo screwed into its own back-face holes -- your requirement",
     "Before: each servo was captured, not fastened (pinch walls, lips, end wall; the J1 pedestal stood 0.6 mm clear "
     "of its back) -- along its axis only friction held it, and the press depends on printer accuracy. "
     "Hole pattern: the Waveshare 2D drawing (DXF, exact) -- back face x 8.30 / 32.75 from the output shaft, y +-10.25 "
     "(24.45 x 20.5). Your photo of the back face gives ratio 1.14 (drawing 1.19; 19.05 x 20.29 would be 0.94) and your "
     "37.24 mm horn-to-horn and O5.95 boss match the drawing (37.25, O6.0), so the drawing describes your servo. "
     "Now: pads / posts touch the servo's back plateau (32.0 above its seat face, both servo models) round each hole "
     "and the servo's own self-tapping screws (~8 mm, from the box) pull it down: J2, J3, J5 through the cover (heads on "
     "its outer face), J1 from under the foot plate (4 posts, O5.6 counterbores), J4 from under its base plate and J6 "
     "through a bridge over the servo's far end -- the far pair only there: behind the near pair sit the forearm (J4) "
     "and the J5 hub (J6), no screwdriver reaches. 20 screws, 2.6 mm into the servo (holes 3.0 deep). The pads keep "
     "|y| < 9.9 clear for 2.35 mm, so the servos still slide in and out (checked, both servo models). Checked: every "
     "screw passes free, bites, head seated, tip free; the screw's core runs down the MANUFACTURER'S hole at all 20; "
     "each screw clamps the housing to the servo on a face along its axis (Rule 4); tool access at its build step.",
     ["j1_servo_hold.png", "servo_screws.png"]),
    ("M2 (done). Cover wire windows fitted to the plugs",
     "The J2 / J3 / J5 cover windows were 12 x 20 centred on the case; the two plugs' footprint reached 0.2 past the "
     "edge. Now x 12.2..18.5 from the output shaft (the wires leave at 13.2..15.2), 22 wide: both plugs fit, wires "
     "1.0 mm clear, and the window stops short of the new near screw pads.", ["sockets_photo.png"]),
    ("M3 (done). Rule 8 from your Fusion snapshots: seated servos, sunk heads, cable route",
     "J4 and J6 servos now stand on 4 back supports like the others; the 8 fork-floor bolt heads are sunk 3.2 mm "
     "(M3 x 10), the J4 / J6 cap counterbores deepened to 3.8; new permanent checks: verify_head_clearance.py "
     "(every screw vs every joint, -180..+180 deg) and cable_route.py (path change per joint, loops).",
     ["head_clearance.png"]),
]

def _cable_table():
    t = txt("CABLE_ROUTE.log")
    return "\n".join(ln for ln in t.splitlines() if ln.strip().startswith(("J", "cable"))) or "(see CABLE_ROUTE.log)"


QA = [
    ("Q1. How is J1 connected, how does it drive the turret, how is it aligned?",
     "Servo horn -> 4 x M2.5 -> J1 hub. The hub's plug has a D-flat that sits in the turret spigot's D-key: that "
     "turns the turret. The spigot's end is slit into a collet; the spigot collar round it is pinched by one M3 bolt "
     "and clamps it onto the plug (no play). Alignment: the turret's spigot runs in the base's two 6806 bearings, "
     "40 mm apart; they carry the arm's weight and tipping moment into the base, the columns and the foot, so the "
     "servo gives torque only. Servo axis = bearing axis (measured, 0.000 mm).", ["j1_drive_explained.png"]),
    ("Q2. Won't the cables wind up during joint motion?",
     "No. The bus is a daisy chain; each cable joins servo k to servo k+1 and so crosses ONE joint -- joint k, whose "
     "axis is servo k's own output axis. No joint turns more than 180 deg in total (the ST3215 is not continuous), "
     "so a cable only flexes back and forth; it can never wind turn after turn. The change of each cable's path over "
     "its joint's range is measured below; leave that + 20 mm as a loop at the joint and tie the cable down on both "
     "sides. " + _cable_table(), ["cable_schematic.png"]),
    ("Q3. Servos floating (your J4 and J6 snapshots)",
     "They were: the J4 and J6 servos hung from their front lips with only friction at the back (J4: a 12 mm cable "
     "space under it). Now every servo stands on 4 supports on its back plateau near both ends -- J1: 4 posts, J2/J3/J5: "
     "4 pads in the cover, J4: 4 posts, J6: 2 far pads (bridge) + 2 near pads -- and is screwed by its own holes where "
     "a screwdriver reaches (20 screws). The middle of the servo's back carries the label block, the rear idler horn "
     "and the bus sockets, so the supports sit on the flat plateau along both long edges: a cut at y = 0 still shows "
     "the gap there; the cut through the hole rows shows the contact.", ["servo_screws.png"]),
    ("Q4. The screw heads under the swinging links -- collision, and at what angle?",
     "Measured for every screw beside a turning part (-180..+180 deg). The J3 fork floor heads came within 1.28 mm of "
     "the forearm at +-72 deg and would touch at 81 deg -- only 9 deg of margin. All fork-floor heads are now sunk "
     "3.2 mm into O6.2 counterbores (M3 x 10 instead of x 14): J3 4.32 mm in range, first contact 94 deg; J5 6.85 mm, "
     "first contact 107 deg; the J4 / J6 cap heads went 0.80 -> 1.30 mm (counterbore 3.3 -> 3.8).",
     ["head_clearance.png"]),
]

QA.append(
    ("Q5. Slots to plug the servo cables in -- is there clearance?",
     "Plugged in: yes, both plugs in every servo with >= 1.0 mm to spare (verify_wiring). Plugging IN or OUT with the "
     "arm assembled: not before -- the new screw pads / posts near the horn end and the cover window's edge stood 0.5 "
     "to 1 mm in the plug's way. Now a clear passage above both sockets (their footprint + margin) is cut through "
     "every pad, post and cover (J2/J3/J5 window 7.5 x 22 mm). New check verify_plug_insert.py pulls each of the 12 "
     "plugs out of its socket with the arm assembled: J2/J3/J5 straight out through the cover; J1/J4 10 mm straight "
     "out, a few mm sideways, then out along the channel; J6 14 mm straight out, then sideways -- all 12 free.", []))

HOUSINGS = ["03_j1_mount", "06_J2_turret_p2", "13_J3_p2", "18_j4_base", "22_J5_p2", "25_j6_body"]
HOLD = []
GREEN = ["00_FIT_TEST_print_first -- FIRST, all 7 coupons (07 = the servo-screw plate)",
         "then all 27 files in PRINTABLE_FILES (33 pieces); the 6 servo housings (%s) once coupon 07 "
         "has screwed onto your servo's back" % ", ".join(HOUSINGS)]

OPEN = [
    ("Servo screws", "Use the self-tapping screws from the servo box (~8 mm under the head): 2.6 mm go into the "
     "servo. A longer screw needs a washer under its head so that no more than 2.6 mm go in. J1: drive the 4 from "
     "under the foot plate BEFORE the foot is fixed to the table. J4: from under its base plate -- in the finished arm "
     "the forearm spring collars cover them (take the collars off to service J4)."),
    ("Print the fit test first", "About 1.5 h. If a coupon is tight or loose, tell me the numbers or set hole "
     "compensation before the big parts."),
    ("Fix the foot to the table", "4 screws through the new holes (or a clamp); otherwise the arm tips at reach."),
    ("Cable loops", "Leave the loop listed for each joint (31-61 mm) and tie each cable down on both sides of "
     "its joint; move every joint through its full range once by hand before powering up."),
    ("Watch the servo temperature", "The J2 servo works near its continuous rating (SF 1.07 with the springs) in a "
     "closed pod. The ST3215 reports its temperature over the bus: watch it in your control code."),
]

CHANGED = ["rev I.1 (2026-09-27): J3_p1 -- spring lugs sunk 1.5 mm into the cheeks + R3 blend webs (reprint J3_p1 only)",
           "j1_mount (idler pocket, table holes, end wall 7.0, 4 servo-screw posts, plug slot)", "base (foot floor 3.0)",
           "J3_p1, J5_p1 (floor bolt heads sunk 3.2 mm; bolts now M3 x 10)", "j4_cap, j6_cap (cap bolt counterbores 3.8)",
           "spigot_collar (pad)", "J2_turret_p2 (servo-screw pads, wire window + plug slot 7.5 x 22)",
           "J3_p2, J5_p2 (bay shell, servo-screw pads, wire window + plug slot 7.5 x 22)", "J5_shaft (flat to the idle end)", "j4_base (idler pocket, 4 support posts, 2 with servo screws)",
           "j4_cap (wider sides)", "j6_body (idler pocket, bosses O21.6, servo-screw bridge + 2 near pads)", "j6_cap (bosses O21.6)",
           "shaft_clamp (corners)", "link_fore_tongue, link_fore_groove (cable skin)", "link_upper_tongue (cable skin)",
           "NEW: 00_FIT_TEST_print_first (7 coupons; 07 = servo-screw plate)"]

SOURCES = [
    ("Waveshare ST3215 servo wiki (3D model ST3215-3D.zip, specifications)", "https://www.waveshare.com/wiki/ST3215_Servo"),
    ("SKF 61806-2RS1 (drive bearings J1/J2/J3/J5)",
     "https://www.skf.com/us/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-61806-2RS1"),
    ("61706 dimensions (J4/J6 bearings)", "https://www.123bearing.com/bearing-housing/deep-groove-bearing/single-row/61706"),
    ("Waveshare ST3215 2D drawing (face-hole positions)", "https://files.waveshare.com/upload/0/08/ST3215-2D.zip"),
    ("ST3215 pinout / 5264 connector", "https://docs.cirkitdesigner.com/component/20f64312-8ca7-4cd1-86c1-882fd984ad37/st3215-servo"),
]


VECTOR = []     # (page index, vector pdf) -- placed after the matplotlib pages are written


def pic_page(pdf, title, png, port=None, fs=12):
    """A picture page. If the view script also wrote a VECTOR copy (.pdf next to the
    .png: sections, charts, schematics), that is placed instead -- sharp at any zoom;
    otherwise the picture is embedded at its native resolution."""
    vec = png[:-4] + ".pdf"
    im = None if os.path.exists(vec) else plt.imread(png)
    if port is None:
        if im is not None:
            port = im.shape[0] > im.shape[1]
        else:
            import pymupdf
            r = pymupdf.open(vec)[0].rect; port = r.height > r.width
    fig = plt.figure(figsize=(8.3, 11.7) if port else (11.7, 8.3))
    fig.suptitle(title, fontsize=fs, fontweight="bold")
    if im is not None:
        ax = fig.add_axes([0.01, 0.01, 0.98, 0.92]); ax.imshow(im, interpolation="none"); ax.axis("off")
    else:
        VECTOR.append((pdf.get_pagecount(), vec))
    pdf.savefig(fig); plt.close(fig)


def place_vectors(path):
    import pymupdf
    doc = pymupdf.open(path)
    for i, vec in VECTOR:
        page = doc[i]; r = page.rect
        page.show_pdf_page(pymupdf.Rect(r.x0 + 0.01 * r.width, r.y0 + 0.07 * r.height, r.x1 - 0.01 * r.width,
                                        r.y1 - 0.01 * r.height), pymupdf.open(vec), 0, keep_proportion=True)
    tmp = path + ".tmp"
    doc.save(tmp, garbage=3, deflate=True); doc.close()
    os.replace(tmp, path)


def main():
    VECTOR.clear()
    rows = stage_table()
    M = rule_matrix(rows)
    stages_ok = all(v == 0 and not tb for _, v, tb, _ in rows)
    head = ("PRINT VERDICT: GREEN. Print the fit test first (7 coupons, about 2 h); when coupon 07 screws onto the back "
            "of your servo, print all 27 files. Every check is at 0 after M1 (servos screwed by their own holes), "
            "M2 (wire windows) and M3 (Rule 8: every servo seated on 4 supports, heads beside turning links sunk, "
            "cable route proven); wiring verified against your photo."
            if stages_ok else "NO GREEN: not all checks are at 0 -- see the stage table.")
    md = ["# ARM-450 rev I.1 -- verification audit (Rules 3, 4, 6, 8), 2026-09-24, J3 lug fix 2026-09-27", "", "**" + head + "**", "",
          "## The three rules, clause by clause", "", "| rule | what it asks | how it was checked | result |",
          "|---|---|---|---|"]
    md += ["| %s | %s | %s | %s |" % r for r in M]
    md += ["", "## What was missing -- found and fixed", ""]
    for i, (t, found, fix, pics) in enumerate(FOUND, 1):
        md += ["### %d. %s" % (i, t), "", "*Found:* " + found, "", "*Fixed:* " + fix, ""]
        md += ["![%s](RULE6_VIEWS/%s)" % (p, p) for p in pics if os.path.exists(os.path.join(VIEWS, p))]
        md += [""] if pics else []
    md += ["## Checked and clean", ""] + ["* " + c for c in CLEAN]
    md += ["", "## Modifications made in this audit (your go-ahead: \"do it on the spot\")", ""]
    for t, body, pics in MODIFY:
        md += ["### " + t, "", body, ""] + ["![%s](RULE6_VIEWS/%s)" % (p, p) for p in pics
                                            if os.path.exists(os.path.join(VIEWS, p))] + [""]
    md += ["## Your questions on the Fusion snapshots", ""]
    for t, body, pics in QA:
        md += ["### " + t, "", body, ""] + ["![%s](RULE6_VIEWS/%s)" % (p, p) for p in pics
                                            if os.path.exists(os.path.join(VIEWS, p))] + [""]
    md += ["## Print order (GREEN)", ""] + ["%d. %s" % (i, g) for i, g in enumerate(GREEN, 1)]
    md += ["", "## Before and while building", ""] + ["* **%s** -- %s" % o for o in OPEN]
    md += ["", "## Every stage of the re-verification", "", "| stage | failures |", "|---|---|"]
    md += ["| %s | %s |" % (n, "ERROR" if tb else ("not run" if v is None else v)) for n, v, tb, _ in rows]
    md += ["", "## Files changed by this audit (reprint these)", ""] + ["* " + c for c in CHANGED]
    md += ["", "## Outside references", ""] + ["* [%s](%s)" % s for s in SOURCES]
    md += ["", "Logs: REVI_CHECKS.log, FINAL_RUN.log, DOCS_RUN.log, OFFICIAL_SERVO_CHECK.log, DISASSEMBLY_CHECK*.log, "
           "AUDIT_GAPS.json, PARAM_AUDIT.md, MATING_CHECK.log, WIRING_CHECK.log"]
    open(os.path.join(HERE, "ARM450_AUDIT_REPORT.md"), "w").write("\n".join(md) + "\n")

    W = lambda s_, n=112: "\n".join(textwrap.wrap(s_, n))
    with PdfPages(os.path.join(HERE, "ARM450_AUDIT_REPORT.pdf")) as pdf:
        # page 1: the rules, clause by clause
        fig = plt.figure(figsize=(11.7, 8.3))
        fig.suptitle("ARM-450 rev I.1 -- verification audit, Rules 3 / 4 / 6 / 8 (2026-09-24; J3 lugs 2026-09-27)", fontsize=15, fontweight="bold")
        fig.text(0.04, 0.925, W(head, 128), fontsize=10, va="top", fontweight="bold",
                 color="#006000" if stages_ok else "#b00000")
        ax = fig.add_axes([0.02, 0.02, 0.96, 0.86]); ax.axis("off")
        cell = [[r[0], W(r[1], 40), W(r[2], 66), W(r[3], 42)] for r in M]
        t = ax.table(cellText=cell, colLabels=["rule", "what it asks", "how it was checked", "result"],
                     colWidths=[0.04, 0.25, 0.43, 0.28], loc="upper center", cellLoc="left")
        t.auto_set_font_size(False); t.set_fontsize(7.2)
        for (r, c), ce in t.get_celld().items():
            nl = max(cell[r - 1][k].count("\n") for k in range(4)) + 1 if r else 1
            ce.set_height(0.02 * nl + 0.01)
            if r == 0:
                ce.set_facecolor("#dde3ea"); ce.set_text_props(fontweight="bold")
            elif c == 3:
                ce.set_facecolor(verdict(M[r - 1][3]))
        pdf.savefig(fig); plt.close(fig)
        # page 2: the print verdict
        fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle("Print verdict", fontsize=15, fontweight="bold")
        fig.text(0.05, 0.90, W(head, 100) + "\n\nPRINT ORDER\n" + "\n".join(W("%d. %s" % (i, g), 100)
                                                                            for i, g in enumerate(GREEN, 1)) +
                 "\n\nMODIFICATIONS MADE\n" + "\n".join("   " + t_ for t_, _, _ in MODIFY),
                 va="top", fontsize=11, family="monospace", color="#006000" if stages_ok else "#b00000")
        pdf.savefig(fig); plt.close(fig)
        for t_, body, pics in MODIFY:
            fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle(t_, fontsize=13, fontweight="bold")
            fig.text(0.05, 0.90, W(body), va="top", fontsize=10.5, family="monospace")
            pdf.savefig(fig); plt.close(fig)
            for p in pics:
                fp = os.path.join(VIEWS, p)
                if not os.path.exists(fp):
                    continue
                pic_page(pdf, {"head_clearance.png": "M3: screw heads beside turning parts, clearance vs angle",
                               "j1_servo_hold.png": "M1 BEFORE: the J1 servo was captured only; its own holes unused",
                               "servo_screws.png": "M1 AFTER: every servo screwed by its own back holes (exact sections)",
                               "sockets_photo.png": "Your servo's back face: sockets, plug, and the 4 back-face holes"}[p], fp)
        for t_, body, pics in QA:
            fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle(t_, fontsize=13, fontweight="bold")
            fig.text(0.05, 0.90, "\n".join(W(par) if not par.startswith(("  J", "  cable")) else par
                                            for par in body.split("\n")), va="top", fontsize=9.5, family="monospace")
            pdf.savefig(fig); plt.close(fig)
            for p in pics:
                fp = os.path.join(VIEWS, p)
                if os.path.exists(fp):
                    pic_page(pdf, t_, fp, fs=11)
        for i, (t_, found, fix, pics) in enumerate(FOUND, 1):
            fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle("%d. %s" % (i, t_), fontsize=14, fontweight="bold")
            fig.text(0.05, 0.90, "FOUND\n" + W(found) + "\n\nFIXED\n" + W(fix), va="top", fontsize=10.5, family="monospace")
            pdf.savefig(fig); plt.close(fig)
            for p in pics:
                fp = os.path.join(VIEWS, p)
                if not os.path.exists(fp):
                    continue
                ttl = ("Manufacturer's ST3215 (left: idler horn red, drive horn orange) vs your Motor.stl model (right)"
                       if p == "idler_compare.png" else
                       "J3 fork p1 spring lugs: rev I (released) vs rev I.1 -- sections in the cheek plane + 3D"
                       if p == "j3_lug_fix.png" else
                       "%s seat, manufacturer's servo in place: exact section through the servo axis" % p[10:12])
                pic_page(pdf, ttl, fp, port=False)
        fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle("Still to do -- before and while building", fontsize=15,
                                                            fontweight="bold")
        fig.text(0.05, 0.90, "\n\n".join(W("%s -- %s" % o) for o in OPEN) + "\n\n\nCHECKED AND CLEAN\n\n" +
                 "\n\n".join(W("* " + c) for c in CLEAN), va="top", fontsize=10.5, family="monospace")
        pdf.savefig(fig); plt.close(fig)
        fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle("Every stage of the re-verification", fontsize=15, fontweight="bold")
        body = "\n".join("%-68s %s" % (n[:68], "ERROR" if tb else ("not run" if v is None else v)) for n, v, tb, _ in rows)
        fig.text(0.05, 0.92, body, va="top", fontsize=9, family="monospace")
        pdf.savefig(fig); plt.close(fig)
        fig = plt.figure(figsize=(11.7, 8.3))
        fig.suptitle("Files changed by this audit -- reprint these", fontsize=15, fontweight="bold")
        fig.text(0.05, 0.90, "\n".join("* " + c for c in CHANGED) + "\n\n\nOUTSIDE REFERENCES\n\n" +
                 "\n".join("* %s\n  %s" % s for s in SOURCES), va="top", fontsize=10.5, family="monospace")
        pdf.savefig(fig); plt.close(fig)
    place_vectors(os.path.join(HERE, "ARM450_AUDIT_REPORT.pdf"))
    st = ["ARM-450 rev I.1 -- PRINT STATUS (verification audit 2026-09-24, J3_p1 lug fix re-verified 2026-09-27)", "", head, "", "PRINT ORDER:"] + \
         ["  %d. %s" % (i, g) for i, g in enumerate(GREEN, 1)] + ["", "Why and what changed: ARM450_AUDIT_REPORT.pdf"]
    pf = os.path.join(ROOT, "PRINTABLE_FILES")
    if os.path.isdir(pf):
        open(os.path.join(pf, "PRINT_STATUS.txt"), "w").write("\n".join(st) + "\n")
    print("written ARM450_AUDIT_REPORT.md / .pdf  (all stages 0: %s)" % stages_ok)
    for r in M:
        print("  R%s  %-60s %s" % (r[0], r[1][:60], r[3]))


if __name__ == "__main__":
    main()
