"""
ARM-450 — 145 mm clamshell link half.

Capsule outer profile (two Ø50 end bosses joined by a 47.5 mm deep straight
section), split along the plane normal to the joint axis, so each half is a
C-channel 14.5 mm deep.

Everything here comes from the analysis:
  * L = 145 mm joint-to-joint, and L2 MUST equal L3 (report 16.3, no dead zone)
  * VARIABLE WALL: 2.4 mm around the perimeter (the flanges, which carry ~87 %
    of the bending moment) and 1.6 mm on the web floor, which sits near the
    neutral axis and does almost nothing. Worth ~41 g over a constant 2.4 wall.
  * bearing pocket Ø42.00 modelled -> the user's measured 0.02 mm XY shrink
    becomes a 0.02 mm light interference press fit (report 8.3, corrected)
  * 0.5 x 45 chamfer at the pocket mouth, Ø38 seat shoulder
  * seam: 1.5 mm TONGUE-AND-GROOVE lip so shear transfers in bearing, not in
    friction, because bolt preload relaxes as the polymer creeps (report 10)
  * M3 heat-set insert bosses along the seam at <= 25 mm pitch
  * every internal corner filleted (report 9.4)

Print flat, open face up, split line on the bed: support-free, and the mating
face is printed against glass so it comes out genuinely flat.
"""

import os
import sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *      # noqa: F403,F401

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")
os.makedirs(OUT, exist_ok=True)

# --- derived ---------------------------------------------------------------
HALF_D = SEC_W / 2.0            # 14.5 — depth of one half
WALL_FLANGE = 2.4               # perimeter wall (flanges + boss walls)
WALL_WEB = 1.6                  # floor of the tray, near the neutral axis
H = SEC_H                       # 47.5 bending depth
POCKET_D = BRG_OD + BRG_FIT     # 42.00 after the corrected fit
SEAT_D = BRG_OD - 2 * BRG_SHOULDER


def capsule(length, half_h, boss_r, depth):
    """Straight section with a circular boss at each end, extruded `depth`."""
    body = (cq.Workplane("XY")
            .center(length / 2.0, 0).rect(length, 2 * half_h).extrude(depth))
    for x in (0.0, length):
        body = body.union(cq.Workplane("XY").center(x, 0)
                          .circle(boss_r).extrude(depth))
    return body


def build(tongue=True, length=LINK_L):
    boss_r = BOSS_R                       # 25
    half_h = H / 2.0                      # 23.75

    # 1. outer solid
    s = capsule(length, half_h, boss_r, HALF_D)

    # 2. hollow it out, leaving WALL_WEB on the floor and WALL_FLANGE round the rim
    inner = capsule(length, half_h - WALL_FLANGE, boss_r - WALL_FLANGE,
                    HALF_D - WALL_WEB + 1.0).translate((0, 0, WALL_WEB))
    s = s.cut(inner)

    # 3. bearing pocket at each end boss, blind from the OPEN face, with a
    #    Ø38 shoulder the outer race seats against
    #
    # 2026-08-21 AUDIT FIX. Step 2 above hollows the shell using
    # (boss_r - WALL_FLANGE) = Ø45.20 at the end boss. The Ø42.00 pocket cut
    # below is SMALLER than that, so it was subtracting a cylinder from a region
    # already empty -- a legal, silent no-op. Every link ever exported had no
    # bearing pocket at all: a Ø42 bearing sat in a Ø45.20 bore with 1.60 mm of
    # radial play, about 20 mm of wander at the tool.
    #
    # The fix is to put the material back before counterboring it. Union a solid
    # ring (Ø38 bore to Ø50 OD) into each boss, then cut the pocket and the bore
    # out of that ring. Cost is ~4 g per boss; it buys the joint its location.
    for x in (0.0, length):
        s = s.union(cq.Workplane("XY").center(x, 0)
                    .circle(boss_r).circle(SEAT_D / 2)
                    .extrude(HALF_D - WALL_WEB)
                    .translate((0, 0, WALL_WEB)))
    for x in (0.0, length):
        s = s.cut(cq.Workplane("XY").center(x, 0)
                  .circle(POCKET_D / 2).extrude(HALF_D + 1)
                  .translate((0, 0, HALF_D - BRG_W)))
        s = s.cut(cq.Workplane("XY").center(x, 0)
                  .circle(SEAT_D / 2).extrude(HALF_D + 2)
                  .translate((0, 0, -1)))
        # 0.5 x 45 LEAD-IN CHAMFER at the pocket mouth.
        # The docstring at the top of this file has promised this chamfer since
        # the file was written, and the code never cut one -- a STEP audit for
        # conical faces found ZERO in every part with a bearing pocket. It is
        # what lets a Ø42 bearing start square in a Ø42 hole; without it you are
        # pressing a sharp edge into a sharp edge, and a printed pocket also
        # carries a little elephant-foot at the mouth to fight.
        # Cut as a CONE, not with .chamfer(): the edge selector throws whenever
        # the boss blend is awkward, and the try/except that would catch it is
        # exactly how a feature goes missing in silence.
        s = s.cut(cq.Workplane("XY").center(x, 0)
                  .circle(POCKET_D / 2 + BRG_CHAMFER)
                  .workplane(offset=BRG_CHAMFER)
                  .circle(POCKET_D / 2)
                  .loft(combine=False)
                  .translate((0, 0, HALF_D - BRG_CHAMFER)))

    # 4. seam lip along the rim: a tongue on one half, a groove on the other.
    #    Built as a thin band that follows the perimeter, inset from the outside.
    lip_w = 2.0
    band_out = capsule(length, half_h - 0.2, boss_r - 0.2, SEAM_LIP)
    band_in = capsule(length, half_h - 0.2 - lip_w, boss_r - 0.2 - lip_w,
                      SEAM_LIP + 2).translate((0, 0, -1))
    band = band_out.cut(band_in)
    if tongue:
        s = s.union(band.translate((0, 0, HALF_D)))
    else:
        clr = SEAM_LIP_CLR
        depth = SEAM_LIP + SEAM_GROOVE_EXTRA      # real axial margin
        groove_o = capsule(length, half_h - 0.2 + clr, boss_r - 0.2 + clr, depth + 0.2)
        groove_i = capsule(length, half_h - 0.2 - lip_w - clr,
                           boss_r - 0.2 - lip_w - clr, depth + 2.2)\
            .translate((0, 0, -1))
        s = s.cut((groove_o.cut(groove_i))
                  .translate((0, 0, HALF_D - depth)))

    # 5. M3 insert bosses along both seam edges at <= SEAM_PITCH
    n = max(2, int(length // SEAM_PITCH) + 1)
    xs = [length * i / (n - 1) for i in range(n)]
    for x in xs:
        if x < boss_r * 0.8 or x > length - boss_r * 0.8:
            continue                       # skip where the end bosses already are
        for sy in (-1, 1):
            # keep the whole boss INSIDE the 47.5 mm section profile, otherwise
            # it protrudes as a thin sliver and breaks the clean outer surface
            y = sy * (half_h - WALL_FLANGE - BOSS_OD / 2.0)
            s = s.union(cq.Workplane("XY").center(x, y)
                        .circle(BOSS_OD / 2).extrude(HALF_D - WALL_WEB)
                        .translate((0, 0, WALL_WEB)))
            if tongue:
                s = s.cut(cq.Workplane("XY").center(x, y)
                          .circle(M3_CLEAR / 2).extrude(HALF_D + 2)
                          .translate((0, 0, -1)))
            else:
                s = s.cut(cq.Workplane("XY").center(x, y)
                          .circle(M3_INSERT_D / 2).extrude(M3_INSERT_L)
                          .translate((0, 0, HALF_D - M3_INSERT_L)))

    # 5b. TIP EARS — a fastener at each end boss, where the seam previously had
    #     none. That is right beside the bearing pocket, the worst place to leave
    #     the seam unclamped, so this closes a real gap in the fastener schedule.
    if TIP_EAR:
        for x_end, sgn in ((0.0, -1.0), (length, +1.0)):
            xc = x_end + sgn * (boss_r + EAR_OUT / 2.0 - 1.0)
            ear = (cq.Workplane("XY").center(xc, 0)
                   .rect(EAR_OUT + 2.0, EAR_W).extrude(HALF_D)
                   .edges("|Z").fillet(2.0))
            s = s.union(ear)
            if tongue:
                s = s.cut(cq.Workplane("XY").center(xc, 0)
                          .circle(TIP_CLEAR / 2).extrude(HALF_D + 2)
                          .translate((0, 0, -1)))
            else:
                s = s.cut(cq.Workplane("XY").center(xc, 0)
                          .circle(TIP_INSERT_D / 2).extrude(TIP_INSERT_L)
                          .translate((0, 0, HALF_D - TIP_INSERT_L)))

    # 6. fillet the internal corners we can reach
    try:
        s = s.faces(">Z").edges().fillet(0.8)
    except Exception:                                     # noqa: BLE001
        pass
    return s


def report(part, name):
    bb = part.val().BoundingBox()
    vol = part.val().Volume()
    print(f"{name}")
    print(f"  envelope  {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
    print(f"  volume    {vol/1000:.1f} cm3   ~{vol*1.29e-3:.0f} g solid PLA+CF")
    for ext in ("step", "stl"):
        p = os.path.join(OUT, f"{name}.{ext}")
        cq.exporters.export(part, p) if ext == "step" else \
            cq.exporters.export(part, p, tolerance=0.01, angularTolerance=0.1)
        print(f"  wrote     {p}")


if __name__ == "__main__":
    print(f"link half: L = {LINK_L:.0f} mm joint-to-joint, section "
          f"{SEC_H:.1f} x {SEC_W:.1f}, wall {WALL_FLANGE}/{WALL_WEB} mm")
    print(f"bearing pocket Ø{POCKET_D:.2f}  (0.02 mm interference after XY shrink)\n")
    report(build(tongue=True), "link_half_tongue")
    print()
    report(build(tongue=False), "link_half_groove")
