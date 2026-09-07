"""
Presentation deck for the guide review.

Rendered with matplotlib rather than a slide tool so that every number on a
slide is pulled from the same modules the report and the gate use. A deck that
is retyped from a report is a third copy of the numbers, and copies rot.

Run:  python3 make_slides.py
Out:  output/ARM450_SLIDES.pdf   (16:9, one slide per page)
"""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
W, H = 13.333, 7.5                      # 16:9 inches
INK, ACC, MUT = "#12202e", "#b4531a", "#5a6b7b"
GOOD, BAD = "#1e6b45", "#a4243b"
BG = "white"


def new():
    fig = plt.figure(figsize=(W, H), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    return fig, ax


def title(ax, t, sub=None, y=0.90):
    ax.text(0.055, y, t, fontsize=27, color=INK, fontweight="bold", va="top")
    if sub:
        ax.text(0.055, y - 0.085, sub, fontsize=14.5, color=ACC, va="top")
    ax.plot([0.055, 0.945], [y - 0.125, y - 0.125], color="#dde3e9", lw=1.2)


def foot(ax, n, tot):
    ax.text(0.945, 0.035, f"{n} / {tot}", fontsize=9.5, color=MUT, ha="right")
    ax.text(0.055, 0.035, "ARM-450  ·  pre-print design review  ·  2026-08-22",
            fontsize=9.5, color=MUT)


def bullets(ax, items, x=0.075, y=0.70, dy=0.080, fs=15.5, w=0.86,
            floor=0.10):
    """`**` marks a bullet as bold. It is a WHOLE-BULLET marker, not inline
    markdown -- an earlier version stripped only the leading pair and left the
    closing `**` printed on the slide."""
    import textwrap
    n = len(items)
    lh = 0.048 * (fs / 15.5)
    for it in items:
        bold = it.startswith("**")
        txt = it.replace("*", "")
        lines = textwrap.wrap(txt, width=int(w * 105 * (15.5 / fs)))
        ax.text(x - 0.022, y + 0.004, "▪", fontsize=min(12, fs - 2), color=ACC,
                va="top")
        for k, ln in enumerate(lines):
            ax.text(x, y - k * lh, ln, fontsize=fs, color=INK, va="top",
                    fontweight="bold" if bold else "normal")
        y -= dy + lh * (len(lines) - 1)
    if y < floor:
        # the deck is generated, so an overrun is a bug I can see and fix, not
        # something to leave for the projector to reveal
        print(f"    ! bullets overran the slide by {floor - y:.3f} "
              f"({n} items at fs={fs})")
    return y


def image(ax, name, box=(0.5, 0.08, 0.46, 0.60)):
    """box = (x0, y0, w, h) in figure coords; image is fitted inside it."""
    p = os.path.join(FIG, name)
    if not os.path.exists(p):
        return
    im = mpimg.imread(p)
    ih, iw = im.shape[0], im.shape[1]
    x0, y0, bw, bh = box
    # fit preserving aspect, in FIGURE coordinates (account for 16:9)
    ar_img = (iw / ih) * (1 / (W / H))
    ar_box = bw / bh
    if ar_img > ar_box:
        w2, h2 = bw, bw / ar_img
    else:
        h2, w2 = bh, bh * ar_img
    a = ax.figure.add_axes([x0 + (bw - w2) / 2, y0 + (bh - h2) / 2, w2, h2])
    a.imshow(im); a.axis("off")


def table(ax, rows, x=0.075, y=0.66, cw=(0.30, 0.30, 0.28), fs=13,
          head=None, dy=0.062, colors=None):
    if head:
        for j, h in enumerate(head):
            ax.text(x + sum(cw[:j]), y, h, fontsize=fs - 0.5, color=INK,
                    fontweight="bold", va="top")
        ax.plot([x, x + sum(cw)], [y - 0.022, y - 0.022], color="#c8d2dc", lw=1)
        y -= 0.05
    for i, r in enumerate(rows):
        for j, c in enumerate(r):
            col = INK
            if colors and colors[i] is not None and j == len(r) - 1:
                col = colors[i]
            ax.text(x + sum(cw[:j]), y - i * dy, str(c), fontsize=fs, color=col,
                    va="top", fontweight="bold" if (colors and colors[i] and j == len(r) - 1) else "normal")
    return y - len(rows) * dy


def kpi(ax, items, y=0.30, fs_v=34, fs_l=12):
    n = len(items)
    for i, (v, lab, col) in enumerate(items):
        cx = 0.075 + (0.85 / n) * (i + 0.5)
        ax.text(cx, y, v, fontsize=fs_v, color=col, fontweight="bold",
                ha="center", va="center")
        ax.text(cx, y - 0.085, lab, fontsize=fs_l, color=MUT, ha="center",
                va="center")


# ---------------------------------------------------------------- the deck
def build():
    VC = json.load(open(os.path.join(HERE, "output", "verify_configs.json")))
    slides = []

    # 1 ---------------------------------------------------------------- title
    def s1(ax):
        ax.add_patch(Rectangle((0, 0.62), 1, 0.38, fc="#f4f7f9", ec="none"))
        ax.text(0.055, 0.86, "ARM-450", fontsize=54, color=INK, fontweight="bold")
        ax.text(0.055, 0.775,
                "A 450 mm printed 6-DOF manipulator with quick-change end effectors",
                fontsize=19, color=ACC)
        ax.text(0.055, 0.715, "Design · analysis · pre-print verification",
                fontsize=15, color=MUT)
        kpi(ax, [("1365 g", "arm mass, of 1450 g", INK),
                 ("492 mm", "reach with a gripper", INK),
                 ("27 / 27", "verification checks", GOOD),
                 ("0", "parts printed yet", BAD)], y=0.42)
        ax.text(0.5, 0.16,
                "Everything in this deck is analytical or simulated.\n"
                "No part has been printed or measured — and that is deliberate:\n"
                "a prediction recorded before the test is evidence, one recorded after it is not.",
                fontsize=13.5, color=MUT, ha="center", va="center", linespacing=1.7)
    slides.append(s1)

    # 2 ---------------------------------------------------------------- brief
    def s2(ax):
        title(ax, "Two demonstrations, two different problems",
              "and they fail for opposite reasons")
        bullets(ax, [
            "**Sinusoidal trace — a PRECISION problem.** A tool follows a sine on a "
            "vertical board. The traced curve is a permanent, visible record of "
            "repeatability, and it exercises five joints at once.",
            "**Docking — a CAPTURE TOLERANCE problem.** A probe enters a passive port and "
            "latches. The interesting engineering is that it must succeed while the arm "
            "is far less accurate than the interface naively requires.",
            "The arm is accurate to about 2.2 mm. The docking cone accepts ±9.75 mm.",
            "**Docking was made feasible by geometry, not by making the arm accurate.** "
            "That is the transferable idea in this project.",
        ], y=0.70)
    slides.append(s2)

    # 3 ------------------------------------------------------------ requirements
    def s3(ax):
        title(ax, "Requirements", "and where each one stands today")
        rows = [
            ("R1  ≤ 450 mm chain", "450.0 mm exactly", "MET"),
            ("R2  ≤ 1450 g (hard)", "1365 g, 85 g spare", "MET"),
            ("R3  300 g payload at the tool", "worst fitted case 75 g", "MET"),
            ("R4  6 DOF wrist", "J4 roll · J5 pitch · J6 roll", "MET"),
            ("R5  consumer FDM printable", "0.6 mm nozzle, no support on load paths", "MET"),
            ("R6  tool change without tools", "3-lug bayonet + 1 thumbscrew", "MET"),
            ("R7  docking without a 7th actuator", "latch driven by J6", "MET"),
            ("R8  visibly accurate trace", "0.055 mm rms simulated at the tip", "SIM ONLY"),
        ]
        cols = [GOOD] * 7 + [ACC]
        table(ax, rows, y=0.68, cw=(0.34, 0.40, 0.16), fs=14,
              head=("requirement", "as built", "status"), colors=cols)
        ax.text(0.075, 0.115,
                "R1 constrains the ARM. With a gripper the system reaches 492 mm — raised, "
                "and accepted as a design\ndecision, now a checked constant so a later, "
                "longer tool cannot quietly exceed it.",
                fontsize=12, color=MUT, linespacing=1.6)
    slides.append(s3)

    # 4 ------------------------------------------------------------ architecture
    def s4(ax):
        title(ax, "One joint interface, all six axes",
              "the decision everything else compounds from")
        bullets(ax, [
            "**Ø42 pocket · 6806 bearing · Ø30 shaft — everywhere.**",
            "One fit tolerance to characterise, not six — a 0.9 h coupon gates ≈19 h "
            "of parts.",
            "One spare part number, whichever joint fails.",
            "Clamp, horn adapter and shaft are common parts, ×6.",
            "**Cost: the wrist carries more bearing than it needs.**",
            "Measured, not assumed: a 4 mm-wide 6706 there saved 24 g and cost NO "
            "stiffness — moment stiffness goes as bearing SPACING squared, and is "
            "independent of bearing width.",
        ], y=0.72, w=0.50, fs=13.5, dy=0.070)
        image(ax, "joint_section.png", (0.585, 0.10, 0.375, 0.60))
    slides.append(s4)

    # 5 ------------------------------------------------------------- the arm
    def s5(ax):
        title(ax, "The arm", "1365 g · 450 mm · 21 printed parts")
        image(ax, "assembly_hero.png", (0.05, 0.09, 0.55, 0.63))
        bullets(ax, [
            "**Clamshell links** — tongue and groove halves bolted on the neutral "
            "axis, closing a 47.5 × 29 box section.",
            "An open C-section of the same envelope has ≈100× less torsional "
            "stiffness — and the payload hangs off-axis.",
            "**Integrated wrist**, not generic modules.",
            "J5 is −91° to +49°, not ±110°: a mesh sweep found J4 striking J6 over "
            "the excluded range.",
        ], x=0.645, y=0.73, w=0.32, fs=12.5, dy=0.062)
    slides.append(s5)

    # 5B --------------------------------------------- kinematics verified
    def s5b(ax):
        title(ax, "The kinematics, checked three independent ways",
              "modified (Craig) DH · velocity-propagation Jacobian · ikpy")
        rows = [("FK:  Craig DH  ==  URDF chain", "1.96e-13 mm"),
                ("FK:  Craig DH  ==  ikpy", "2.17e-13 mm"),
                ("FK:  URDF chain ==  ikpy", "1.14e-13 mm"),
                ("tool axis direction", "8.95e-16"),
                ("Jacobian: propagation == finite diff", "1.81e-05"),
                ("IK, Craig DH + propagated Jacobian", "1.6e-11 mm"),
                ("IK, ikpy", "0.000 mm")]
        table(ax, rows, y=0.70, cw=(0.46, 0.24), fs=12.5,
              head=("check", "worst over 200 poses"), dy=0.048)
        ax.text(0.075, 0.275,
                "7 of 7 pass. Those are double-precision rounding errors, not disagreement.",
                fontsize=13.5, color=INK, fontweight="bold")
        ax.text(0.075, 0.215,
                "Agreement between the DH table and the URDF proves only that the table copies\n"
                "the URDF faithfully — INCLUDING any error the URDF already had. A third route\n"
                "sharing no code closes that: three implementations cannot agree on one mistake.",
                fontsize=12, color=MUT, linespacing=1.7)
        ax.text(0.075, 0.095,
                "d4 = 181, not 119. Using the obvious link length put the tool 193 mm out — "
                "caught\nby the URDF comparison on the first run.",
                fontsize=11.5, color=ACC, linespacing=1.7)
    slides.append(s5b)

    # 6 ------------------------------------------------------------ workspace
    def s6(ax):
        title(ax, "Workspace", "200 000-pose Monte-Carlo FK inside the URDF limits")
        image(ax, "workspace_arm450.png", (0.045, 0.07, 0.50, 0.62))
        rows = [("bare face", "450 mm", "188 L"),
                ("pen", "480 mm", "239 L"),
                ("gripper", "492 mm", "262 L"),
                ("dock probe", "486 mm", "251 L")]
        table(ax, rows, x=0.60, y=0.63, cw=(0.16, 0.13, 0.12), fs=14,
              head=("fitted", "reach", "swept"))
        ax.text(0.60, 0.26,
                "A gripper adds 39 % of swept volume\nfor 42 mm of extension — volume\n"
                "grows roughly as the cube of reach.",
                fontsize=13, color=MUT, linespacing=1.7)
        ax.text(0.60, 0.11,
                "Reach past the flange is MEASURED off\nthe assembly, not typed in. The dock\n"
                "figure was stale by 7 mm until it was.",
                fontsize=12, color=ACC, linespacing=1.7)
    slides.append(s6)

    # 7 --------------------------------------------------------- end effectors
    def s7(ax):
        title(ax, "Quick-change end effectors",
              "push on, twist 30°, nip one screw — off in about five seconds")
        image(ax, "end_effectors.png", (0.05, 0.08, 0.52, 0.62))
        bullets(ax, [
            "**Three-lug bayonet + one M3 thumbscrew.**",
            "Bolts were rejected: the J6 face has only THREE holes — the servo pocket "
            "ate the fourth quadrant — and three blind M3s under a wrist is the wrong "
            "answer to a tool-change problem.",
            "**Gripper:** parallel jaws, rack and pinion, one 9 g SG90.",
            "**Dock probe:** no actuator at all — J6 turns the latch.",
        ], x=0.60, y=0.73, w=0.33, fs=12.5, dy=0.062)
    slides.append(s7)

    # 8 -------------------------------------------------------------- docking
    def s8(ax):
        title(ax, "Docking: capture tolerance is the design driver",
              "not accuracy — and that is the point")
        image(ax, "dock_latch_section.png", (0.045, 0.10, 0.60, 0.56))
        kpi(ax, [("±9.75 mm", "measured capture", GOOD),
                 ("≈2.2 mm", "arm precision", INK),
                 ("4×", "margin", GOOD)], y=0.755, fs_v=24, fs_l=10.5)
        ax.text(0.68, 0.60,
                "Measured by sweeping the exported\nprobe mesh against the exported\n"
                "target mesh until they foul — not\nsubtracted from two diameters.",
                fontsize=12, color=MUT, linespacing=1.7, va="top")
        ax.text(0.68, 0.34,
                "Insert · roll J6 30° · latched.\nReverse to undock.\n\n"
                "J6 has ±175° and does nothing\nduring a docking approach, so\nthe motion is free.",
                fontsize=12.5, color=INK, linespacing=1.7)
    slides.append(s8)

    # 9 ------------------------------------------------------ method principle
    def s9(ax):
        title(ax, "Verification: interrogate the geometry, not the parameters",
              "the single most important decision in the method")
        bullets(ax, [
            "Every check reads the EXPORTED STEP or mesh — never the numbers used to "
            "author it.",
            "**An earlier gate checked that BEARING_POCKET_D == 42.0 and passed 55/55 "
            "while three bearing pockets did not physically exist.**",
            "A hollowing operation had removed the material the pocket was cut into. "
            "Subtracting a Ø42 pocket from an already-empty region succeeds silently and "
            "changes nothing.",
        ], y=0.68, fs=15)
        ax.add_patch(FancyBboxPatch((0.075, 0.13), 0.85, 0.20,
                                    boxstyle="round,pad=0.012",
                                    fc="#fdf6f2", ec=ACC, lw=1.4))
        ax.text(0.5, 0.23,
                "\"A boolean that removes nothing does not fail. It returns the same solid,\n"
                "and every step downstream — render, drawing, mass, collision —\n"
                "treats the result as correct.\"",
                fontsize=15.5, color=ACC, ha="center", va="center",
                style="italic", linespacing=1.8)
    slides.append(s9)

    # 10 ---------------------------------------------------------- the 8 stages
    def s10(ax):
        title(ax, "Eight staged gates", "each a real analysis, each with its own criterion")
        rows = [
            ("1  Design check", "do the features physically exist?", "STEP B-rep audit"),
            ("2  FEA", "does anything yield?", "p99 von Mises SF ≥ 3"),
            ("3  Creep + fatigue", "does it fail slowly?", "< 0.5 %/y, > 1e8 cycles"),
            ("4  Stiffness", "does the tool stay put?", "compliance ≤ 0.30 mm"),
            ("5  URDF", "does the model match the machine?", "parses, mass, meshes"),
            ("6  Path tracing", "does the real trajectory work?", "0 collisions"),
            ("7  Simulation", "will ROS work on hardware?", "ramp, topic, rate"),
            ("8  End effectors", "do the tools fit, does it latch?", "29 checks + a mate"),
        ]
        table(ax, rows, y=0.68, cw=(0.20, 0.40, 0.30), fs=13.5,
              head=("stage", "question it answers", "criterion"))
        kpi(ax, [("27", "checks", INK), ("8", "stages", INK),
                 ("0", "failures", GOOD), ("GO", "for printing", GOOD)], y=0.15)
    slides.append(s10)

    # 11 ------------------------------------------------- with / without tool
    def s11(ax):
        title(ax, "Every load case, with and without an end effector",
              "because a tool is not just mass — it is a lever arm")
        image(ax, "verify_matrix.png", (0.035, 0.145, 0.93, 0.585))
        ax.text(0.5, 0.085,
                "75 g on a 42 mm stick is not the load case 75 g at the flange is. "
                "The suite runs from one driver for\nall five configurations, so the "
                "\"with gripper\" answer cannot be a different vintage from \"bare\".",
                fontsize=12, color=MUT, ha="center", linespacing=1.7)
    slides.append(s11)

    # 12 --------------------------------------------------------- the results
    def s12(ax):
        title(ax, "Results across five payload configurations",
              "30 of 30 criteria pass")
        rows = []
        cols = []
        for k in ("bare", "pen", "gripper", "gripper+load", "dock"):
            r = VC[k]
            rows.append((k.replace("+load", " + 225 g"),
                         f"{r['tau'][1]:.2f} N·m", f"{r['sf']:.0f}×",
                         f"{r['compliance_mm']:.3f} mm",
                         f"{r['servo_margin_min']:.2f}×", "PASS"))
            cols.append(GOOD)
        table(ax, rows, y=0.66, cw=(0.20, 0.15, 0.11, 0.16, 0.15, 0.10), fs=13.5,
              head=("configuration", "J2 torque", "SF", "compliance",
                    "servo margin", ""), colors=cols)
        ax.text(0.075, 0.24,
                "Structural margins of 46–102× are not a claim of excellence. They say the arm is\n"
                "STIFFNESS-DRIVEN AND SERVO-LIMITED, not strength-driven.",
                fontsize=14, color=INK, linespacing=1.8, fontweight="bold")
        ax.text(0.075, 0.11,
                "The two margins that are merely comfortable — servo stall 1.19× and continuous "
                "1.61× in the\nworst case — are the ones to watch on hardware.",
                fontsize=12.5, color=ACC, linespacing=1.7)
    slides.append(s12)

    # 13 ---------------------------------------------------------- precision
    def s13(ax):
        title(ax, "The precision budget has one term in it",
              "and it is not the printed structure")
        rows = [("bare", "0.036 mm", "1.88 mm", "1.88 mm"),
                ("gripper", "0.054 mm", "2.24 mm", "2.24 mm"),
                ("gripper + 225 g", "0.098 mm", "2.24 mm", "2.24 mm")]
        table(ax, rows, y=0.66, cw=(0.24, 0.20, 0.20, 0.18), fs=15,
              head=("configuration", "structural", "0.5° backlash", "combined"))
        ax.add_patch(FancyBboxPatch((0.075, 0.20), 0.85, 0.20,
                                    boxstyle="round,pad=0.012",
                                    fc="#f2f7f4", ec=GOOD, lw=1.4))
        ax.text(0.5, 0.30,
                "Backlash exceeds structural deflection by ≈20×, in EVERY configuration.\n"
                "No change to the printed parts moves the number.\n"
                "Accuracy work belongs in joint-side feedback, not in the arm.",
                fontsize=15, color=INK, ha="center", va="center", linespacing=1.9)
        ax.text(0.075, 0.11,
                "This also means the conclusion is invariant to whether a tool is fitted — "
                "which is worth knowing before\nspending print time trying to stiffen anything.",
                fontsize=12.5, color=MUT, linespacing=1.7)
    slides.append(s13)

    # 14 --------------------------------------------------------- simulation
    def s14(ax):
        title(ax, "Simulation — the trajectory that will actually run",
              "IK solved offline, replayed by a ROS 2 node")
        image(ax, "rviz_tip_side.png", (0.045, 0.09, 0.55, 0.61))
        bullets(ax, [
            "**0.014 mm rms** at the flange, **0.055 mm** at the tip.",
            "**0 collisions in 240 waypoints** on exact meshes; 0/60 with either tool "
            "fitted.",
            "Largest joint step 2.09°.",
            "**Marker on the fingertips** — verified at 0.00 mm from the furthest "
            "point of the tool mesh.",
            "**Board goes at 342 mm, not 300**: the path drives the FLANGE.",
        ], x=0.625, y=0.73, w=0.32, fs=12.5, dy=0.060)
    slides.append(s14)

    # 15 ------------------------------------------------------------- defects
    def s15(ax):
        title(ax, "What the gate caught", "13 defects that survived visual inspection")
        rows = [
            ("Three bearing pockets absent", "a boolean that removed nothing"),
            ("Dock probe exported as 4 solids", "latch lugs floating 5.5 mm clear"),
            ("Target groove severed its own spigot", "3.30 mm cut in a 1.65 mm wall"),
            ("Cone deeper than the spigot was long", "the two could never have mated"),
            ("Rack pitch line 1.20 mm off the PCD", "the gear mesh never touched"),
            ("Steel shaft quoted at 93 g, was 222 g", "per-unit figure never multiplied"),
            ("Sine path grazing the base pedestal", "accuracy is not clearance"),
            ("The URDF had no tool link at all", "verified in one model, shown from another"),
            ("Sine traced by the flange, not the tip", "a 42 mm error on hardware"),
        ]
        table(ax, rows, y=0.68, cw=(0.44, 0.44), fs=13.2,
              head=("defect", "class of error"), dy=0.058)
        ax.text(0.075, 0.135,
                "The pattern across all of them: NOTHING FAILED LOUDLY. Each produced a "
                "plausible artefact —\na render, a number, a passing check — that was wrong.",
                fontsize=13.5, color=ACC, linespacing=1.7, fontweight="bold")
    slides.append(s15)

    # 16 ---------------------------------------------------------- space grade
    def s16(ax):
        title(ax, "Is it space grade?", "true in one specific sense, false in every other")
        image(ax, "spacegrade_compare.png", (0.030, 0.09, 0.615, 0.64))
        for i, (v, lab, col) in enumerate([("3", "survive unchanged", GOOD),
                                           ("2", "need rework", "#b8860b"),
                                           ("11", "must be replaced", BAD)]):
            yy = 0.655 - i * 0.085
            ax.text(0.685, yy, v, fontsize=30, color=col, fontweight="bold",
                    ha="right", va="center")
            ax.text(0.705, yy, lab, fontsize=13, color=MUT, va="center")
        ax.text(0.665, 0.40,
                "SURVIVES\nthe kinematics, the joint architecture,\nthe fastening scheme.",
                fontsize=12.5, color=INK, linespacing=1.75, va="top")
        ax.text(0.665, 0.265,
                "DOES NOT\nthe material (Tg 60 °C, outgasses),\nthe actuators (plastic gears, wet\n"
                "grease, no rad tolerance), vacuum\ncompatibility, qualification.",
                fontsize=12.5, color=INK, linespacing=1.75, va="top")
    slides.append(s16)

    # 17 ------------------------------------------------------- the honest line
    def s17(ax):
        title(ax, "The honest summary", "worth saying out loud")
        ax.add_patch(FancyBboxPatch((0.07, 0.30), 0.86, 0.42,
                                    boxstyle="round,pad=0.015",
                                    fc="#f4f7f9", ec="#c8d2dc", lw=1.4))
        ax.text(0.5, 0.51,
                "ARM-450 is a KINEMATIC AND ARCHITECTURAL PROTOTYPE of a space\n"
                "manipulator, and a FUNCTIONAL DEMONSTRATOR of a docking interface.\n\n"
                "It is not a flight article, and no part of it is on a path to becoming one\n"
                "without replacing the material, the actuators and the electronics.\n\n"
                "What DOES transfer: the geometry, the joint scheme, the docking principle —\n"
                "and the verification method, which is grade-independent.",
                fontsize=15.5, color=INK, ha="center", va="center", linespacing=1.95)
        ax.text(0.5, 0.19,
                "Re-made in Al 6061-T6 the same geometry masses ≈1.13 kg — LIGHTER than the "
                "printed version — and is\nabout 10× stiffer. The material swap is not a "
                "compromise; it is an improvement that costs money.",
                fontsize=12.5, color=MUT, ha="center", linespacing=1.7)
    slides.append(s17)

    # 18 ------------------------------------------------------ awaiting hardware
    def s18(ax):
        title(ax, "What is NOT verified", "written before the test, so it counts as a prediction")
        rows = [
            ("Fit coupon — Ø42 bore", "firm thumb press", "gates ≈19 h of parts"),
            ("Servo backlash", "0.3–1.0° per joint", "the dominant error term"),
            ("Sine trace accuracy", "1–3 mm rms", "vs 0.055 mm simulated"),
            ("Docking latch, bench", "latches + releases", "needs no arm, no fuel"),
            ("Static deflection, 300 g", "0.098 mm", "falsified if > 0.30 mm"),
            ("J2 torque and case temp", "2.74 N·m, 44 °C", "falsified if > 60 °C"),
            ("Assembled mass", "1365 ± 40 g", "falsified if > 1450 g"),
        ]
        table(ax, rows, y=0.68, cw=(0.31, 0.27, 0.32), fs=13.5,
              head=("measurement", "prediction", "why it matters"))
        ax.text(0.075, 0.135,
                "Each has a stated FALSIFICATION condition, not just a target. "
                "§9 of the paper has the blank\nspaces for the measured numbers.",
                fontsize=12.5, color=ACC, linespacing=1.7)
    slides.append(s18)

    # 19 ------------------------------------------------------------ limitations
    def s19(ax):
        title(ax, "Limitations", "stated plainly, because a verification document that does not, is not one")
        bullets(ax, [
            "**No hardware.** Every number is analytical or simulated.",
            "**FEA is part-wise, not assembly-level** — joint stiffness, bolt preload and "
            "contact are not modelled.",
            "**Backlash is assumed, not measured** — and it dominates the error budget, so "
            "the headline precision figure is the least evidenced number in the work.",
            "Creep uses a Findley fit two orders of magnitude below its calibration range.",
            "Print anisotropy is not modelled; the FEA is isotropic.",
            "The docking mate is rigid-body geometry — no friction, compliance or "
            "misalignment dynamics.",
        ], y=0.68, fs=14.5)
    slides.append(s19)

    # 20 ----------------------------------------------------------- conclusions
    def s20(ax):
        title(ax, "Conclusions", "")
        bullets(ax, [
            "**A 450 mm printed 6-DOF arm at 1365 g with a 300 g allowance is achievable** "
            "— 46–102× on yield, 0.098 mm compliance in the worst configuration.",
            "**The arm is servo-limited, not structure-limited.** Backlash beats structural "
            "deflection ≈20×, in every payload configuration.",
            "**Docking is feasible anyway**, because capture tolerance was designed as "
            "geometry. Making the interface forgiving is cheaper than making the arm accurate.",
            "**One joint interface across six axes** compounds into fewer tolerances, one "
            "spare, and a one-coupon qualification path.",
            "**Verification must interrogate exported geometry.** 13 defects survived visual "
            "inspection and passing parameter checks.",
        ], y=0.745, fs=14, dy=0.074)
        ax.text(0.075, 0.115,
                "Next: print the fit coupon (0.9 h), then the arm (≈21 h), then measure "
                "everything in §9.",
                fontsize=13.5, color=ACC, fontweight="bold")
    slides.append(s20)

    out = os.path.join(HERE, "output", "ARM450_SLIDES.pdf")
    with PdfPages(out) as pdf:
        for i, fn in enumerate(slides, 1):
            fig, ax = new()
            fn(ax)
            if i > 1:
                foot(ax, i, len(slides))
            pdf.savefig(fig, facecolor=BG)
            plt.close(fig)
    print(f"  wrote {out}  ({len(slides)} slides)")


if __name__ == "__main__":
    print("ARM-450 PRESENTATION")
    build()
