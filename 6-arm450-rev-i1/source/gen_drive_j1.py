#!/usr/bin/env python3
"""
ARM-450 rev I -- J1 base yaw with a real drive train.

What was wrong (measured, see GO_RETRACTED.md / RULE3 log):
  * j1_drive_hub keyed to the turret by two radial grubs INSIDE a solid
    spigot wall (r 11.0..14.9) with the base boss round it: no key reaches
    them after assembly, so the Ø21.8 plug is a slip fit in the Ø22 bore and
    J1 does not turn the turret.
  * its horn screws ran UP through the horn into blind pilots -- the opposite
    of the user's proven Motor_mount, where screws go THROUGH the coupler
    INTO the horn's threads.
  * released stack: spigot ends z=-9, collar z -7..3, hub z 0..18, pod's
    servo face z=-22. Horn and hub never meet; j1_clamp would bolt straight
    into the spigot and collar.

Rev I stack, world z (J1 axis = Z, base underside z=0):
  spigot end        z_sb = -9.00   (turret_p1, released trim)
  hub flange        z_sb-0.5-4 .. z_sb-0.5     keyed plug up into the D-bore
  horn face         flange bottom + HORN_REC_T
  servo cap face    horn face - 3.011   (bears on the mount's back wall)
  mount             pinch U-channel, stepped back wall, hung from the base's
                    four Ø4.5 foot holes at r = 52; it is also the foot.
"""
import os
import sys

import numpy as np
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_common as DC       # noqa: E402

Z_SB = -9.00
FLANGE_D, FLANGE_T = 29.0, 3.4
PLUG_D, PLUG_L = 21.8, 14.0
# Recess only 1.6 deep: the servo's step (39.4 x 14) rises 1.10 above its
# cap face, and a 2.2 recess put the rotating flange 0.29 mm INTO it.
HORN_REC_D, HORN_REC_T = 19.6, 1.6
CENTRE_D = 7.0                  # horn centre-screw access (M3 head Ø5.5)
CB_D = 4.8                      # counterbore for the horn screw heads
UNDER_HEAD = 3.0                # material under each head, above the horn
FLAT_DIST = 9.0                 # D-flat on the plug, measured from the axis
FLAT_ANG = 45.0                 # between the horn holes, clear of the counterbores
KEY_CLR = 0.2                   # the spigot's D sits this much further out

Z_FLANGE_TOP = Z_SB - 0.5
Z_FLANGE_BOT = Z_FLANGE_TOP - FLANGE_T
Z_HORN = Z_FLANGE_BOT + HORN_REC_T
Z_CAP = Z_HORN - DC.HORN_BELOW_CAP


def _flat_cutter(dist, z0, z1, keep_inside):
    """Half-space beyond a plane at `dist` along FLAT_ANG, between z0..z1."""
    a = np.radians(FLAT_ANG)
    box = (cq.Workplane("XY").center(dist + 20.0, 0).rect(40.0, 80.0)
           .extrude(z1 - z0).translate((0, 0, z0)))
    return box.rotate((0, 0, 0), (0, 0, 1), FLAT_ANG)


def hub():
    """Local frame: flange bottom at z=0, plug on top, horn below."""
    s = cq.Workplane("XY").circle(FLANGE_D / 2).extrude(FLANGE_T)
    s = s.union(cq.Workplane("XY").circle(PLUG_D / 2).extrude(PLUG_L)
                .translate((0, 0, FLANGE_T)))
    s = s.cut(cq.Workplane("XY").circle(HORN_REC_D / 2).extrude(HORN_REC_T))
    s = s.cut(cq.Workplane("XY").circle(CENTRE_D / 2)
              .extrude(FLANGE_T + PLUG_L + 2).translate((0, 0, -1)))
    top = FLANGE_T + PLUG_L
    for a in (0, 90, 180, 270):
        x = DC.HORN_BCD / 2 * np.cos(np.radians(a))
        y = DC.HORN_BCD / 2 * np.sin(np.radians(a))
        s = s.cut(cq.Workplane("XY").center(x, y).circle(DC.HORN_HOLE_D / 2)
                  .extrude(top + 1).translate((0, 0, HORN_REC_T - 0.5)))
        z_head = HORN_REC_T + UNDER_HEAD
        s = s.cut(cq.Workplane("XY").center(x, y).circle(CB_D / 2)
                  .extrude(top - z_head + 1).translate((0, 0, z_head)))
    # D-flat on the plug only (the flange stays round)
    s = s.cut(_flat_cutter(FLAT_DIST, FLANGE_T, top + 1, False))
    # 0.5 x 45 lead-in on the plug nose
    s = s.faces(">Z").edges(cq.selectors.RadiusNthSelector(-1)).chamfer(0.5)
    return s


def spigot_key(z0, z1):
    """Material ADDED inside the turret's Ø22 spigot bore to form the D,
    KEY_CLR beyond the plug's flat. World frame."""
    seg = (cq.Workplane("XY").circle(11.0 + 0.05).extrude(z1 - z0)
           .translate((0, 0, z0)))
    return seg.intersect(_flat_cutter(FLAT_DIST + KEY_CLR, z0, z1, True))


if __name__ == "__main__":
    h = hub()
    n = len(h.val().Solids())
    print("J1 rev I stack (world z):  spigot end %.2f  flange %.2f..%.2f  horn %.3f  cap face %.3f"
          % (Z_SB, Z_FLANGE_BOT, Z_FLANGE_TOP, Z_HORN, Z_CAP))
    print("   j1_hub  %.1f mm3  solids %d" % (h.val().Volume(), n))
    cq.exporters.export(h.translate((0, 0, Z_FLANGE_BOT)),
                        os.path.join(HERE, "j1_hub.step"))
    cq.exporters.export(h.translate((0, 0, Z_FLANGE_BOT)),
                        os.path.join(HERE, "j1_hub.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    sys.exit(0 if n == 1 else 1)


# ---------------------------------------------------------------------------
# J1 MOUNT -- replaces j1_clamp + j1_pod. Holds the J1 servo AND is the
# arm's foot. World frame. PRINTS AS IT STANDS: bottom plate on the bed,
# everything rises from it (rev I first cut hung the channel walls from a
# plate and their bottoms were islands -- the slice gate caught it).
#
# The servo SLIDES IN along +X into a locating end wall, which puts the horn
# on the J1 axis with zero clearance. Two lips over the cap face hold it down
# onto two pedestals under the case back, and the pinch walls hold it across.
# Once the hub is bolted to the horn and keyed into the spigot it cannot slide
# back out -- so there is no strap.
# ---------------------------------------------------------------------------
LIP_T = 4.0
Z_LIP_BOT = Z_CAP                       # the cap face bears here
Z_LIP_TOP = Z_CAP + LIP_T
SLOT_Y = 10.0                           # horn O19.2 + step slide through this
POST_XY = 36.77                         # base foot holes, 4 x O4.5 at r = 52
POST_D = 14.0
M4_INS_D, M4_INS_L = 5.6, 8.0
WALL_T = 6.5
CASE_X0 = -10.112                       # case body end at the horn end
X_OPEN = 35.51                          # channel open end (servo goes in here)
END_T = 7.0                             # 6.0 left a 0.6 mm crescent where the O31 hub bore cuts it (audit)
Z_TIP = Z_CAP - DC.CASE_ABOVE_CAP       # case back tip (rear boss)
# Measured by probing along the axis under the pedestal's footprint: the case
# face at the horn end starts 3.905 above the tip (a coarse slice said 4.5,
# which put the pedestal 0.6 mm into the case).
Z_BACK_FULL = Z_TIP + 3.905
BASE_T = 4.0
Z_TABLE = Z_TIP - 17.0 - BASE_T         # 17 mm under the back for plugs + cable
BASE_R = 64.0
TABLE_R, TABLE_HOLE = 58.0, 5.5          # table-mounting holes (tipping)
TABLE_HOLE_R = 58.0


def mount():
    zb = Z_TABLE + BASE_T                              # top of the bottom plate
    s = cq.Workplane("XY").circle(BASE_R).extrude(BASE_T).translate((0, 0, Z_TABLE))
    for a in (0, 90, 180, 270):
        s = s.cut(cq.Workplane("XY")
                  .center(TABLE_HOLE_R * np.cos(np.radians(a)), TABLE_HOLE_R * np.sin(np.radians(a)))
                  .circle(4.5 / 2).extrude(BASE_T + 2).translate((0, 0, Z_TABLE - 1)))
    # four columns up to the base flange, M4 heat-set insert in each top
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * POST_XY, sy * POST_XY
            s = s.union(cq.Workplane("XY").center(x, y).circle(POST_D / 2)
                        .extrude(-zb).translate((0, 0, zb)))
            s = s.cut(cq.Workplane("XY").center(x, y).circle(M4_INS_D / 2)
                      .extrude(M4_INS_L + 0.5).translate((0, 0, -M4_INS_L)))
    yw = DC.PINCH / 2 + WALL_T / 2
    # pinch walls, bottom plate up to the lip tops
    for sy in (-1, 1):
        s = s.union(cq.Workplane("XY").center((CASE_X0 + X_OPEN) / 2, sy * yw)
                    .rect(X_OPEN - CASE_X0, WALL_T).extrude(Z_LIP_TOP - zb)
                    .translate((0, 0, zb)))
        # lip over the cap face: inward from the wall to |y| = SLOT_Y
        s = s.union(cq.Workplane("XY")
                    .center((CASE_X0 + X_OPEN) / 2, sy * (SLOT_Y + DC.PINCH / 2) / 2)
                    .rect(X_OPEN - CASE_X0, DC.PINCH / 2 - SLOT_Y).extrude(LIP_T)
                    .translate((0, 0, Z_LIP_BOT)))
    # locating end wall at the horn end, full height
    s = s.union(cq.Workplane("XY").center(CASE_X0 - END_T / 2, 0)
                .rect(END_T, DC.PINCH + 2 * WALL_T).extrude(Z_LIP_TOP - zb)
                .translate((0, 0, zb)))
    # pedestals under the case back, clear of the rear boss and connectors
    s = s.union(cq.Workplane("XY").center((CASE_X0 + -3.4) / 2, 0)
                .rect(-3.4 - CASE_X0, 2 * 12.0).extrude(Z_BACK_FULL - DC.CLR - zb)
                .translate((0, 0, zb)))
    # ONE pedestal only. A second one at the far end blocked the servo's
    # raised back cover as it slides in -- the insertion sweep caught it. The
    # far end is held by the pinch walls along the whole case length.
    # hub flange O29 turns inside the lips: clear it on the axis
    s = s.cut(cq.Workplane("XY").circle(DC.BORE_CLR_D / 2)
              .extrude(Z_LIP_TOP - Z_LIP_BOT + 2).translate((0, 0, Z_LIP_BOT - 1)))
    # SERVO SCREWED BY ITS OWN BACK HOLES (user's requirement, audit M1): 4
    # posts from the foot plate to the servo's back plateau; the self-tapping
    # screws go in from under the foot plate (before the foot is fixed down),
    # heads in O5.6 counterbores, 2.6 mm into the servo.
    pts = DC.SCREW_NEAR + DC.SCREW_FAR
    s = s.union(DC.screw_pads(Z_CAP, -1, pts, Z_CAP - zb + 0.5, d=DC.POST_D))
    s = DC.screw_holes(s, Z_CAP, -1, pts, Z_CAP - Z_TABLE + 1.0, counterbore=True)
    # the near posts' head counterbores run 0.1 mm from the plug slot (Rule 8 /
    # plug slot): merge the two between the head seat and the plate top -- no
    # sliver wall; the head seat itself is untouched
    for (x, y) in DC.SCREW_NEAR:
        z1, z0 = Z_CAP - DC.SSCR_HEAD, zb + 0.01
        y0, y1 = max(y - DC.SSCR_CB_D / 2, -DC.PLUG_PASS_Y), min(y + DC.SSCR_CB_D / 2, DC.PLUG_PASS_Y)
        s = s.cut(cq.Workplane("XY").center((x + 1.5 + DC.PLUG_PASS_X[0]) / 2 + 0.1, (y0 + y1) / 2)
                  .rect(DC.PLUG_PASS_X[0] - x - 1.5 + 0.2, y1 - y0).extrude(z1 - z0).translate((0, 0, z0)))
    # the real ST3215's rear IDLER horn (official model) turns right where the
    # pedestal stood (169 mm3 of overlap): keep it clear
    s = s.cut(DC.idler_clearance(Z_CAP, -1))
    # TABLE MOUNTING (audit, tipping): at full reach the arm's centre of mass
    # is 117.7 mm from the J1 axis against a 64 mm foot -- it falls over unless
    # the foot is fixed down. 4 x O5.5 (M5 / #10 wood screw) through the plate
    # at r 58, between the 45-deg columns; drive them before the base goes on.
    for a in (0, 90, 180, 270):
        c, s_ = np.cos(np.radians(a)), np.sin(np.radians(a))
        s = s.cut(cq.Workplane("XY").center(TABLE_R * c, TABLE_R * s_).circle(TABLE_HOLE / 2)
                  .extrude(BASE_T + 2).translate((0, 0, Z_TABLE - 1)))
    return s


def build_mount():
    print("J1 mount  lips %.3f..%.3f  back tip %.3f  table %.3f"
          % (Z_LIP_BOT, Z_LIP_TOP, Z_TIP, Z_TABLE))
    p = mount()
    n = len(p.val().Solids())
    bb = p.val().BoundingBox()
    print("   j1_mount %9.1f mm3  solids %d  z %7.2f..%7.2f"
          % (p.val().Volume(), n, bb.zmin, bb.zmax))
    cq.exporters.export(p, os.path.join(HERE, "j1_mount.step"))
    cq.exporters.export(p, os.path.join(HERE, "j1_mount.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    return n == 1
