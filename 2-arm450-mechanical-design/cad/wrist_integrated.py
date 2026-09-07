"""
ARM-450 — integrated 3-axis wrist (J4 roll, J5 pitch, J6 roll).

WHY THIS EXISTS
The first wrist was three stacked modules: a 34 mm roll module, a 46 mm yoke,
a second 34 mm roll module. Measured axis-to-axis that forced 152 mm from J4 to
the TCP, against a 70 mm allowance -- so the interference sweep found a collision
in 100 % of sampled poses. Stacking wastes length; a real wrist NESTS.

BUDGET (after shortening the links to 119 mm, which costs nothing in reach)
    J4 -> J5   62 mm   (32 forearm boss overhang + 30 housing)
    J5 -> J6   34 mm
    J6 -> TCP  26 mm
               122 mm total, which is what the 450 mm chain now leaves.

Every joint still uses the house interface: Ø42 pocket, 6806, Ø30 shaft.
"""
import os, sys
import math
import cadquery as cq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")
# Wrist runs 6706 (Ø37 x 4), not the 6806 used at J1/J2/J3 — see params.py.
POCKET = WRIST_BRG_OD + BRG_FIT
SEAT = WRIST_BRG_OD - 2 * WRIST_BRG_SHOULDER
BRG_W = WRIST_BRG_W

# 2026-08-19: rebalanced so J6 can take a FULL-SIZE ST3215 like every other
# joint. J5->J6 34->30 and J6->TCP 26->30 keeps the 60 mm J5->TCP total, and the
# extra 4 mm of thickness is exactly what the 25.1 mm servo cavity needed.
J4_J5, J5_J6, J6_TCP = 62.0, 30.0, 30.0
# Standard tool interface, shared with cad/base_wrist.py tool_flange()
FLANGE_BCD, FLANGE_PILOT = 30.0, 10.0
# Servo pocket occupies y +1.88..+27 (the XZ workplane's normal is -Y, so
# offset=-D/2-1 puts the plane at y=+27 and the extrude runs back to +1.88).
# Usable arc on the Ø30 circle is therefore ~133..353 deg. These three sit in
# material with >2 mm of wall to the pocket, at 90 deg spacing -- so a tool
# drilled 4 x 90 deg still bolts on with three.
TOOL_BOLT_ANGLES = (160.0, 250.0, 340.0)


# 0.5 x 45 LEAD-IN CHAMFER at every bearing-pocket mouth.
# BRG_CHAMFER has been in params.py, on the drawings and in the docstrings since
# the design was written, and a STEP audit for CONICAL faces found ZERO in every
# part carrying a pocket -- the feature was specified everywhere and cut nowhere.
# It is what lets a Ø42 bearing start square in a Ø42 hole.
# Cut as a CONE rather than with .chamfer(): the edge selector throws whenever a
# boss blend is awkward, and the try/except that catches it is exactly how a
# feature disappears in silence.
def _chamfer_mouth(solid, cx, cy, z_mouth, pocket_d, cham, down=True):
    import cadquery as _cq
    d = -1.0 if down else 1.0
    return solid.cut(_cq.Workplane("XY").center(cx, cy)
                     .circle(pocket_d / 2 + cham)
                     .workplane(offset=cham * d)
                     .circle(pocket_d / 2)
                     .loft(combine=False)
                     .translate((0, 0, z_mouth if down else z_mouth)))


def servo_fixings(part, plane, offset, cx, cy, bx=None, by=None, depth=30.0):
    """NOTE: cx/cy must already include SERVO_AXIS_OFFSET -- the ST3215 output
    shaft is 10.11 mm from one end of a 45.22 mm case, not on its centre."""
    """4 case-mounting holes + a cable exit for a servo pocket.
    Without these the servo sits in its pocket with nothing holding it."""
    bx = bx or SERVO_BOLT_X
    by = by or SERVO_BOLT_Y
    for dx in (-bx / 2, bx / 2):
        for dy in (-by / 2, by / 2):
            part = part.cut(cq.Workplane(plane).workplane(offset=offset)
                            .center(cx + dx, cy + dy)
                            .circle(SERVO_BOLT_D / 2).extrude(depth))
    part = part.cut(cq.Workplane(plane).workplane(offset=offset)
                    .center(cx, cy).circle(SERVO_CABLE_D / 2).extrude(depth))
    return part


def horn_pattern(part, plane, offset, depth=9.0):
    """Servo-horn bolt circle on the DRIVEN side of a joint."""
    return (part.cut(cq.Workplane(plane).workplane(offset=offset)
                     .polarArray(HORN_BCD / 2, 0, 360, HORN_N)
                     .circle(HORN_SCREW_D / 2).extrude(depth)))
BOSS_OH = 32.0                      # forearm end-boss overhang past J4


def _racetrack(D, x_to, depth):
    """Circle at the bearing axis, extended along +X to swallow the servo.

    A plain Ø56 circle could not contain the servo once the pocket was shifted
    by the 12.5 mm output-axis offset -- the pocket overhung by 7.3 mm and was
    clipped. Growing the circle to Ø75 would be wasteful; extending it in ONE
    direction costs nothing in the chain, being perpendicular to it.
    """
    body = cq.Workplane("XY").circle(D / 2).extrude(depth)
    if x_to > 0.01:
        body = body.union(cq.Workplane("XY")
                          .center(x_to / 2, 0).rect(x_to, D).extrude(depth))
        body = body.union(cq.Workplane("XY").center(x_to, 0)
                          .circle(D / 2).extrude(depth))
    return body


def wrist_j4_housing():
    """Bolts to the forearm end. Carries the J4 roll bearing; its far face is
    the J5 yoke mount. Length = J4_J5 - BOSS_OH so the yoke bore lands on J5."""
    L = J4_J5 - BOSS_OH             # 30
    # Ø46 left only a 41.2 mm cavity and the ST3215 needs 45.6. Growing the
    # diameter costs NOTHING in chain length -- it is perpendicular to the chain.
    D = 56.0
    x_to = SERVO_AXIS_OFFSET + (SERVO_L + 2 * SERVO_CLR) / 2 + 2.4 - D / 2
    h = _racetrack(D, max(0.0, x_to), L)
    # J4 roll bearing in the inboard face, Ø38 through
    h = h.cut(cq.Workplane("XY").circle(POCKET / 2).extrude(BRG_W))
    h = _chamfer_mouth(h, 0, 0, BRG_W - BRG_CHAMFER, POCKET, BRG_CHAMFER, down=False)
    h = h.cut(cq.Workplane("XY").circle(SEAT / 2).extrude(L + 2).translate((0, 0, -1)))
    # yoke bolt pattern on the outboard face
    # pocket shifted so the servo's OUTPUT AXIS lands on the joint axis
    h = h.cut(cq.Workplane("XZ").workplane(offset=-D / 2 - 1)
              .center(SERVO_AXIS_OFFSET, L / 2)
              .rect(SERVO_L + 2 * SERVO_CLR, SERVO_W + 2 * SERVO_CLR)
              .extrude(SERVO_T + 2 * SERVO_CLR + 1))
    h = servo_fixings(h, "XZ", -D / 2 - 1, SERVO_AXIS_OFFSET, L / 2, depth=D)
    # the J4 output drives the yoke above it -> horn pattern in that face
    h = horn_pattern(h, "XY", L - 9.0)
    h = (h.faces(">Z").workplane().polarArray(34.0 / 2, 45, 360, 4)
         .circle(M3_INSERT_D / 2).cutBlind(-M3_INSERT_L))
    return h


def wrist_j5_yoke():
    """Compact pitch fork. Bore sits low so J5->J6 is only 34 mm."""
    # 2026-08-21 AUDIT FIX. SPAN was 30.0, giving an outer width of 52 and a
    # bearing-face spacing of 52 - 2*7 = 38.02 -- while BRG_SPACING (and every
    # drawing) said 40.00. Moment stiffness goes as spacing squared, so that was
    # a quiet 9.6 % loss. Derive SPAN from BRG_SPACING so the two cannot drift
    # apart again. The extra 2 mm is across the wrist, perpendicular to the
    # chain, so it costs nothing in the 450 mm budget.
    W, T = 54.0, 11.0
    SPAN = BRG_SPACING + 2 * BRG_W - 2 * T        # 32.0 -> spacing 40.00
    H = J5_J6 + 12.0                # bore 12 mm above the base (now 42)
    y = cq.Workplane("XY").box(W, SPAN + 2 * T, H, centered=(True, True, False))
    y = y.edges("|Z").fillet(5.0)
    y = y.cut(cq.Workplane("XY").box(W + 2, SPAN, H - 12.0,
                                     centered=(True, True, False))
              .translate((0, 0, 12.0)))
    zc = 12.0                       # J5 axis height above the mounting face
    y = y.cut(cq.Workplane("XZ").workplane(offset=-(SPAN / 2 + T + 1)).center(0, zc)
              .circle(SEAT / 2).extrude(SPAN + 2 * T + 2))
    for k, off in enumerate((-(SPAN / 2 + T) - 0.01, SPAN / 2 + T - BRG_W + 0.01)):
        y = y.cut(cq.Workplane("XZ").workplane(offset=off).center(0, zc)
                  .circle(POCKET / 2).extrude(BRG_W))
        # lead-in chamfer at each cheek's pocket mouth. These pockets face
        # OUTWARD in opposite directions, so the cone opens the opposite way on
        # each cheek -- getting that backwards cuts into the seat instead of the
        # mouth and quietly enlarges the bore the bearing has to grip.
        mouth = off if k == 0 else off + BRG_W
        y = y.cut(cq.Workplane("XZ").workplane(offset=mouth).center(0, zc)
                  .circle(POCKET / 2 + BRG_CHAMFER)
                  .workplane(offset=BRG_CHAMFER if k == 0 else -BRG_CHAMFER)
                  .circle(POCKET / 2).loft(combine=False))
    y = y.cut(cq.Workplane("XY").workplane(offset=zc - (SERVO_T + 2 * SERVO_CLR) / 2)
              .center(SERVO_AXIS_OFFSET, -(SPAN / 2 + T / 2))
              .rect(SERVO_L + 2 * SERVO_CLR, T + 2)
              .extrude(SERVO_T + 2 * SERVO_CLR))
    y = servo_fixings(y, "XY", zc - (SERVO_T + 2 * SERVO_CLR) / 2 - 4,
                      SERVO_AXIS_OFFSET, -(SPAN / 2 + T / 2), depth=SERVO_T + 8)
    # J5 drives the wrist output -> horn pattern concentric with the bore
    y = horn_pattern(y, "XZ", -(SPAN / 2 + T) - 0.01, depth=8.0)
    y = (y.faces("<Z").workplane().polarArray(34.0 / 2, 45, 360, 4)
         .circle(M3_CLEAR / 2).cutThruAll())
    return y


def wrist_j6_output():
    """J6 roll plus the tool flange, in one part. J6 axis -> TCP = 30 mm.
    Ø52 so a full-size ST3215 fits: the diameter is perpendicular to the chain,
    so growing it costs nothing in length."""
    D = 52.0
    x_to6 = SERVO_AXIS_OFFSET + (SERVO_L + 2 * SERVO_CLR) / 2 + 2.4 - D / 2
    o = _racetrack(D, max(0.0, x_to6), J6_TCP - 6.0)
    o = o.cut(cq.Workplane("XY").circle(POCKET / 2).extrude(BRG_W))
    o = _chamfer_mouth(o, 0, 0, BRG_W - BRG_CHAMFER, POCKET, BRG_CHAMFER, down=False)
    o = o.cut(cq.Workplane("XY").circle(SEAT / 2).extrude(J6_TCP).translate((0, 0, -1)))
    # integral tool flange, 4 x M3 on a Ø30 bolt circle
    o = o.union(_racetrack(D, max(0.0, x_to6), 6.0)
                .translate((0, 0, J6_TCP - 6.0)))
    o = o.cut(cq.Workplane("XZ").workplane(offset=-D / 2 - 1)
              .center(SERVO_AXIS_OFFSET, (J6_TCP - 6.0) / 2)
              .rect(SERVO_L + 2 * SERVO_CLR, SERVO_W + 2 * SERVO_CLR)
              .extrude(SERVO_T + 2 * SERVO_CLR + 1))
    o = servo_fixings(o, "XZ", -D / 2 - 1, SERVO_AXIS_OFFSET, (J6_TCP - 6.0) / 2, depth=D)
    o = horn_pattern(o, "XY", 0.0, depth=BRG_W + 2)
    # 2026-08-21 AUDIT FIX. This was polarArray(..., 45, 360, 4) -- four holes at
    # 45/135/225/315 deg. The servo pocket opening occupies the -Y side of the
    # flange (x -10.31..35.31, y -27.00..-0.88), so the 315 deg hole landed in
    # empty space and simply did not exist. The part shipped with three of four
    # bolt holes while the drawing said four.
    #
    # Only ~219 deg of the Ø30 bolt circle has material behind it, which is not
    # enough for four holes at 90 deg (needs 270). So this is now an honest
    # THREE-bolt interface, on the same Ø30 circle at 90 deg spacing, placed
    # where material actually is. A tool drilled 4 x 90 deg still bolts on with
    # three. Widening it to four would mean moving the servo, which costs chain
    # length the 450 mm budget does not have.
    # One explicit XY workplane, all three points in a single cut. Looping with
    # .faces(">Z").workplane() re-selects a DIFFERENT top face after each cut and
    # re-origins the workplane on it, so only the last hole survived -- the audit
    # found one hole where three were intended.
    _pts = [(FLANGE_BCD / 2 * math.cos(math.radians(a)),
             FLANGE_BCD / 2 * math.sin(math.radians(a)))
            for a in TOOL_BOLT_ANGLES]
    o = o.cut(cq.Workplane("XY").workplane(offset=J6_TCP - 6.0)
              .pushPoints(_pts).circle(M3_CLEAR / 2).extrude(6.0 + 1.0))
    # Ø10 CENTRE PILOT. The design's standard tool interface is "4 x M3 on a
    # Ø30 bolt circle, Ø10 centre pilot" -- that is what cad/base_wrist.py
    # tool_flange() has built since the beginning. The integrated wrist grew its
    # own flange and never got the pilot, so the two tool interfaces in the same
    # machine did not match. Without it a tool is located only by four clearance
    # holes, which leaves it free to sit off-centre by the hole clearance.
    # It doubles as the cable route from the tool into the hollow wrist.
    o = o.cut(cq.Workplane("XY").circle(FLANGE_PILOT / 2)
              .extrude(8.0).translate((0, 0, J6_TCP - 6.5)))
    try:
        o = o.edges(">Z").fillet(0.8)
    except Exception:          # the servo pocket now breaks that edge loop
        pass
    return o


def rep(part, name):
    bb = part.val().BoundingBox(); v = part.val().Volume()
    print(f"  {name:20s} {bb.xlen:5.1f} x {bb.ylen:5.1f} x {bb.zlen:5.1f} mm   "
          f"{v/1000:5.1f} cm3  ~{v*1.29e-3*0.5:4.0f} g")
    cq.exporters.export(part, os.path.join(OUT, f"{name}.step"))
    cq.exporters.export(part, os.path.join(OUT, f"{name}.stl"),
                        tolerance=0.01, angularTolerance=0.1)


if __name__ == "__main__":
    print(f"Integrated wrist — J4->J5 {J4_J5:.0f}, J5->J6 {J5_J6:.0f}, "
          f"J6->TCP {J6_TCP:.0f}  = {J4_J5+J5_J6+J6_TCP:.0f} mm\n")
    rep(wrist_j4_housing(), "wrist_j4_housing")
    rep(wrist_j5_yoke(), "wrist_j5_yoke")
    rep(wrist_j6_output(), "wrist_j6_output")
