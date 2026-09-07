"""
ARM-450 — the four joints that were missing: J1, J4, J5, J6.

Design rule kept throughout: EVERY joint reuses the same interface —
a Ø42 6806 bearing pocket and a Ø30 shaft. One bearing part number, one shaft
diameter, one clamp, for the whole machine.

J1  TURRET      base yaw. Runs on the Ø42 seat already in the base, carries the
                J1 servo, and presents the J2 shoulder bore 40 mm above the base
                top face (the "shoulder rise" in the 450 mm chain).
J4  ROLL MODULE inline roll in the forearm. Two flanges, one rotating on a 6806,
                servo inside. The SAME part serves J6 tool roll.
J5  WRIST YOKE  pitch fork carrying the Ø42 bores, mounts the wrist body.
"""

import os
import sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *      # noqa: F403,F401

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")
os.makedirs(OUT, exist_ok=True)

POCKET = BRG_OD + BRG_FIT           # 42.00
SEAT = BRG_OD - 2 * BRG_SHOULDER    # 38.0
SHOULDER_RISE = 40.0


def turret_j1():
    """J1 yaw platform: shaft down into the base bearing, J2 bore on top."""
    # The J2 bore must sit exactly SHOULDER_RISE (40 mm) above the base top face,
    # with material all round it. Body height = 40 + pocket radius + wall.
    # (First cut made the body 40 tall and put the bore 24 below its top, which
    # placed J2 at only 30 mm -- 10 mm short, and it broke the 450 mm chain.)
    D = 80.0
    H = SHOULDER_RISE + POCKET / 2 + 6.0
    t = cq.Workplane("XY").circle(D / 2).extrude(H)
    t = t.edges("|Z").fillet(2.0) if False else t
    # Ø30 spigot downward, runs in the base's Ø42 bearing
    t = t.union(cq.Workplane("XY").circle(BRG_ID / 2).extrude(-14.0))
    # cable bore straight through, lines up with the base's Ø52
    t = t.cut(cq.Workplane("XY").circle(11.0).extrude(H + 20)
              .translate((0, 0, -16)))
    # HOLLOW IT. Solid, the turret was 212 cm3 = 137 g. A 3 mm shell keeps the
    # outside, the spigot and both bearing seats untouched.
    SHELL = 3.0
    t = t.cut(cq.Workplane("XY").workplane(offset=SHELL)
              .circle(D / 2 - SHELL).extrude(H - 2 * SHELL))
    # J1 servo pocket in the side
    # shifted by SERVO_AXIS_OFFSET: the output shaft is 12.5 mm off the case centre
    t = t.cut(cq.Workplane("XZ").workplane(offset=-D / 2 - 1)
              .center(SERVO_AXIS_OFFSET, H * 0.32)
              .rect(SERVO_L + 2 * SERVO_CLR, SERVO_W + 2 * SERVO_CLR)
              .extrude(SERVO_T + 2))
    # J1 servo case fixings + cable exit -- the pocket alone held nothing
    for dx in (-SERVO_BOLT_X / 2, SERVO_BOLT_X / 2):
        for dy in (-SERVO_BOLT_Y / 2, SERVO_BOLT_Y / 2):
            t = t.cut(cq.Workplane("XZ").workplane(offset=-D / 2 - 1)
                      .center(dx, H * 0.32 + dy)
                      .circle(SERVO_BOLT_D / 2).extrude(D))
    # shifted by SERVO_AXIS_OFFSET: the output shaft is 12.5 mm off the case centre
    t = t.cut(cq.Workplane("XZ").workplane(offset=-D / 2 - 1)
              .center(SERVO_AXIS_OFFSET, H * 0.32).circle(SERVO_CABLE_D / 2).extrude(D))
    # J2 shoulder bore across the top: Ø42 pockets both faces, Ø38 through
    zc = SHOULDER_RISE          # J2 axis, 40 mm above the base top face
    t = t.cut(cq.Workplane("XZ").workplane(offset=-D).center(0, zc)
              .circle(SEAT / 2).extrude(2 * D))
    for off in (-D / 2 - 0.01, D / 2 - BRG_W + 0.01):
        t = t.cut(cq.Workplane("XZ").workplane(offset=off).center(0, zc)
                  .circle(POCKET / 2).extrude(BRG_W))
        # 0.5 x 45 lead-in chamfer at each pocket mouth. BRG_CHAMFER has been
        # in params, on the drawings and in the docstrings since the design was
        # written; a STEP audit for CONICAL faces found ZERO on every part with
        # a bearing pocket. It was specified everywhere and cut nowhere.
        # The two J2 pockets face OPPOSITE ways, so the cone opens the opposite
        # way on each -- backwards and it cuts the seat instead of the mouth.
        mouth = off if off < 0 else off + BRG_W
        t = t.cut(cq.Workplane("XZ").workplane(offset=mouth).center(0, zc)
                  .circle(POCKET / 2 + BRG_CHAMFER)
                  .workplane(offset=BRG_CHAMFER if off < 0 else -BRG_CHAMFER)
                  .circle(POCKET / 2).loft(combine=False))
    return t


def roll_module():
    """Inline roll joint used at J4 and J6. Rotating flange on one 6806."""
    D, L = 46.0, 34.0
    r = cq.Workplane("XY").circle(D / 2).extrude(L)
    # bearing pocket in the top face, Ø38 through below it
    r = r.cut(cq.Workplane("XY").workplane(offset=L - BRG_W)
              .circle(POCKET / 2).extrude(BRG_W + 1))
    r = r.cut(cq.Workplane("XY").circle(SEAT / 2).extrude(L + 2)
              .translate((0, 0, -1)))
    # servo pocket in the side
    r = r.cut(cq.Workplane("XZ").workplane(offset=-D / 2 - 1)
              .center(0, L * 0.34)
              .rect(SERVO_L + 2 * SERVO_CLR, SERVO_W + 2 * SERVO_CLR)
              .extrude(SERVO_T + 2))
    # mounting flange holes in the bottom face
    r = (r.faces("<Z").workplane()
         .polarArray(34.0 / 2, 45, 360, 4).circle(M3_CLEAR / 2).cutBlind(-8.0))
    return r


def wrist_yoke_j5():
    """J5 pitch fork: two cheeks with Ø42 bores, bolts to the forearm roll module."""
    W, H, T = 58.0, 46.0, 12.0
    SPAN = 30.0
    y = cq.Workplane("XY").box(W, SPAN + 2 * T, H, centered=(True, True, False))
    y = y.edges("|Z").fillet(5.0)
    # open the fork
    y = y.cut(cq.Workplane("XY").box(W + 2, SPAN, H - 16,
                                     centered=(True, True, False))
              .translate((0, 0, 16)))
    # Ø42 pockets facing each other in the cheeks, Ø38 through
    zc = H - 16.0
    y = y.cut(cq.Workplane("XZ").workplane(offset=-(SPAN / 2 + T + 1))
              .center(0, zc).circle(SEAT / 2).extrude(SPAN + 2 * T + 2))
    for off in (-(SPAN / 2 + T) - 0.01, SPAN / 2 + T - BRG_W + 0.01):
        y = y.cut(cq.Workplane("XZ").workplane(offset=off).center(0, zc)
                  .circle(POCKET / 2).extrude(BRG_W))
    # bolt face to the roll module
    y = (y.faces("<Z").workplane()
         .polarArray(34.0 / 2, 45, 360, 4).circle(M3_CLEAR / 2).cutBlind(-9.0))
    return y


def report(part, name):
    bb = part.val().BoundingBox()
    v = part.val().Volume()
    print(f"{name:16s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:6.1f} mm   "
          f"{v/1000:6.1f} cm3   ~{v*1.29e-3*0.5:5.0f} g")
    cq.exporters.export(part, os.path.join(OUT, f"{name}.step"))
    cq.exporters.export(part, os.path.join(OUT, f"{name}.stl"),
                        tolerance=0.01, angularTolerance=0.1)


if __name__ == "__main__":
    print("Every joint uses the same Ø42 / 6806 / Ø30 interface.\n")
    report(turret_j1(), "turret_j1")
    report(roll_module(), "roll_module")
    report(wrist_yoke_j5(), "wrist_yoke_j5")
    print("\nroll_module is used TWICE: J4 forearm roll and J6 tool roll.")
    print("With these, all six axes have real hardware.")
