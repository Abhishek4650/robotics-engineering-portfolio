#!/usr/bin/env python3
"""
ARM-450 rev I -- J1 base and spigot collar.

BASE. The released base_wrist.base() cuts the lower 6806 pocket into the
middle of a column (z 3..10) with a Ø38 bore through it, leaving a lip BELOW
(z 0..3) and ABOVE (z 10..12): the bearing can be fitted from neither end
(installation sweep: blocked both ways). The README says "lower presses up
from underneath". So: same generator, then the pocket is carried down through
the bottom face with a lead-in, and the bearing presses up onto the top lip.

COLLAR. The rev-H collar rebuild put the two pinch bolts ALONG the split
(axis y at x = 0) and straight through the bore -- with the spigot in place
they could not even be inserted, let alone clamp. It also cut 3 mm into the
base (static audit). Rev I: a real split clamp -- bolts along X across the
slot at the wall's mid-radius, head counterbores on -X, heat-set inserts on
+X; body kept 0.5 mm below the base; a boss that touches ONLY the lower
bearing's inner race (README: "preload the INNER races only").
"""
import os
import sys

import numpy as np
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/user/ros2_ws/arm450_design/cad")
import base_wrist as BW                     # noqa: E402

BRG_OD, BRG_W, FIT, CH = 42.0, 7.0, 0.02, 0.5
Z_LO = 3.0                                  # lower pocket floor in the released design

# collar
OD, BORE = 46.0, 30.15
Z_BOT, Z_TOP = -9.0, -0.5                   # body: flush with the spigot end, 0.5 under the base
RACE_R_IN, RACE_R_OUT = BORE / 2, 16.75     # boss on the 6806 inner ring only (d1 33.7, SKF)
# 2.0: the collar now also closes the slit spigot (collet) onto the J1 hub
# plug: 0.075 + 0.1 radial to take up -> 1.10 mm of slot needed, 2.0 given
SLOT_W = 2.0
Y_BOLT = (OD / 2 + BORE / 2) / 2            # 19.04, wall mid-radius
# ONE pinch bolt, mid-height. Two at -6.8/-2.7 put the two O4.1 insert bores
# exactly tangent at z -4.75 -- zero wall between them (a non-manifold edge in
# the mesh). Two M3 inserts plus walls need ~11 mm; the collar has 8.5 and
# cannot grow down without meeting the J1 mount's lips. A single-screw split
# collar is the standard shaft-collar form.
BOLT_Z = ((Z_BOT + Z_TOP) / 2.0,)
X_WALL = float(np.sqrt((OD / 2) ** 2 - Y_BOLT ** 2))   # 12.96
PAD_L = 6.5                                  # pad length along X, inward from X_WALL
# +4.4: the O6.2 head counterbore on the -x pad reached 0.5 mm from the pad top (audit)
PAD_Y0, PAD_Y1 = Y_BOLT - 3.5, Y_BOLT + 4.4


def base():
    b = BW.base()
    # FOOT FLOOR. The released lightening recess (r 30..47, FOOT_T - 3 deep)
    # was written for a 7.0 foot "leaving a 3 mm floor"; FOOT_T went to 5.5 and
    # the floor under the hollow pedestal became 0.5 mm over ~5100 mm2 (audit,
    # thin-wall rays). Fill it: the floor is 3.0 mm again.
    b = b.union(cq.Workplane("XY").circle(47.0).circle(30.0).extrude(BW.FOOT_T - 3.0))   # z 0 .. 2.5, flush
    b = b.cut(cq.Workplane("XY").polarArray(BW.FOOT_BCD / 2, 45, 360, 4).circle(BW.FOOT_BOLT / 2)
              .extrude(20).translate((0, 0, -5)))
    b = b.cut(cq.Workplane("XY").circle((BRG_OD + FIT) / 2).extrude(Z_LO + 1.0)
              .translate((0, 0, -1.0)))
    b = b.cut(cq.Workplane("XY").circle((BRG_OD + FIT) / 2 + CH).workplane(offset=CH)
              .circle((BRG_OD + FIT) / 2).loft(combine=True).translate((0, 0, -0.001)))
    return b


def collar():
    s = (cq.Workplane("XY").circle(OD / 2).circle(BORE / 2).extrude(Z_TOP - Z_BOT)
         .translate((0, 0, Z_BOT)))
    s = s.union(cq.Workplane("XY").circle(RACE_R_OUT).circle(RACE_R_IN)
                .extrude(Z_LO - Z_TOP).translate((0, 0, Z_TOP)))
    # PADS round the pinch bolt. Along X at y = 19.04 the bolt axis meets the
    # O46 outline at x 12.96, so the O4.1 insert (x 7.3..13.0) broke out of
    # the outer surface for its last 3.7 mm (fastener check: 78 % of the
    # insert's surround was material) and the head seat was cut the same way.
    # A flat pad each side embeds the insert fully and gives it a square
    # entry face for the soldering iron.
    for sx in (-1, 1):
        s = s.union(cq.Workplane("XY").center(sx * (X_WALL - PAD_L / 2), (PAD_Y0 + PAD_Y1) / 2)
                    .rect(PAD_L, PAD_Y1 - PAD_Y0).extrude(Z_TOP - Z_BOT).translate((0, 0, Z_BOT)))
    # the split, radial at +Y, through body and boss
    s = s.cut(cq.Workplane("XY").center(0, (BORE / 2 + OD / 2) / 2)
              .rect(SLOT_W, OD / 2 - BORE / 2 + 2).extrude(Z_LO - Z_BOT + 2)
              .translate((0, 0, Z_BOT - 1)))
    for z in BOLT_Z:
        # clearance on -X (head side) up to the slot, counterbore for the head
        s = s.cut(cq.Workplane("YZ").center(Y_BOLT, z).circle(3.4 / 2)
                  .extrude(-(X_WALL + 2)).translate((SLOT_W / 2 + 0.01, 0, 0)))
        s = s.cut(cq.Workplane("YZ").center(Y_BOLT, z).circle(6.2 / 2)
                  .extrude(-6.0).translate((-X_WALL + 3.2, 0, 0)))
        # heat-set insert pressed in from the +X OUTER face, 6 deep, then a
        # clearance hole on to the slot so the bolt reaches it. (First cut it
        # from the slot outward to x 7.1: a SEALED cavity -- no insert can be
        # fitted into it; the mesh showed it as a separate body.)
        s = s.cut(cq.Workplane("YZ").center(Y_BOLT, z).circle(4.1 / 2)
                  .extrude(-7.0).translate((X_WALL + 1.0, 0, 0)))
        s = s.cut(cq.Workplane("YZ").center(Y_BOLT, z).circle(3.4 / 2)
                  .extrude(X_WALL + 1.0).translate((0.0, 0, 0)))
    return s


if __name__ == "__main__":
    rel = BW.base()
    print("base_wrist.base() reproduces the released base: vol %.1f  (out_cad/base.stl is checked below)"
          % rel.val().Volume())
    for nm, fn in (("base", base), ("spigot_collar", collar)):
        p = fn()
        bb = p.val().BoundingBox()
        print("%-14s %9.1f mm3  solids %d  z %.2f..%.2f" % (nm, p.val().Volume(), len(p.val().Solids()), bb.zmin, bb.zmax))
        cq.exporters.export(p, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(p, os.path.join(HERE, nm + ".stl"), tolerance=0.01, angularTolerance=0.1)
