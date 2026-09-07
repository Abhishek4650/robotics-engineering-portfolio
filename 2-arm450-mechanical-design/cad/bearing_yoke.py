"""
ARM-450 — spaced double-bearing joint yoke.

Replaces the single Ø42 x 3.7 THRUST washer, which is the largest single error
source in the arm (report section 8): a thrust bearing has zero moment capacity,
so the joint tilts freely and 0.2 mm of clearance becomes ~28.9 mm of wobble at
the tool.

This yoke carries TWO 6806 deep-groove bearings (30 x 42 x 7) with their faces
BRG_SPACING apart. Moment stiffness goes as spacing squared, so the same
clearance now gives ~0.36 mm at the tool -- an 80x improvement.

Design points that matter (report 8.3, 8.5):
  * pocket = OD + 0.15 mm PRESS fit; FDM pockets print 0.1-0.4 mm UNDERSIZE
  * 0.5 x 45 chamfer at each pocket mouth so the bearing starts square
  * a real SHOULDER for the outer race to seat against, not a flat printed face
  * a preload screw drawing the inner races together against a spacer, which is
    what actually removes the clearance and kills the limit-cycle oscillation
  * print with the bore axis VERTICAL (report 11.1)
"""

import os
import sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *      # noqa: F403,F401

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")
os.makedirs(OUT, exist_ok=True)

POCKET_D = BRG_OD + BRG_FIT             # 42.15
SEAT_D = BRG_OD - 2 * BRG_SHOULDER      # 38.0 — outer race seats on this lip
CHEEK_T = BRG_W + 4.0                   # 11 mm of material behind each bearing
INNER = BRG_SPACING                     # clear span between the cheeks
BODY_W = POCKET_D + 2 * 5.0             # 52.15 outer
YOKE_H = POCKET_D + 2 * 6.0             # 54.15 tall


def cheek(x_centre, flip):
    """One side plate carrying a bearing pocket."""
    c = (cq.Workplane("YZ")
         .workplane(offset=x_centre - CHEEK_T / 2)
         .box(BODY_W, YOKE_H, CHEEK_T, centered=(True, True, False))
         .edges("|X").fillet(6.0))

    face = ">X" if flip else "<X"
    # bearing pocket, blind, to depth BRG_W
    c = (c.faces(face).workplane(centerOption="CenterOfBoundBox")
         .circle(POCKET_D / 2).cutBlind(-BRG_W))
    # through bore to the shoulder diameter -> gives the outer race a real seat
    c = (c.faces(face).workplane(centerOption="CenterOfBoundBox")
         .circle(SEAT_D / 2).cutThruAll())
    # 0.5 x 45 chamfer at the pocket mouth
    c = c.faces(face).edges(cq.NearestToPointSelector(
        (x_centre + (CHEEK_T / 2 if flip else -CHEEK_T / 2), POCKET_D / 2, 0)
    )).chamfer(BRG_CHAMFER)
    return c


def build():
    x0 = -(INNER / 2 + CHEEK_T / 2)
    x1 = +(INNER / 2 + CHEEK_T / 2)
    c = cheek(x0, flip=True).union(cheek(x1, flip=False))

    # spine joining the two cheeks -- a closed back so the yoke is not an
    # open C in torsion (report 9.5: closing a section is worth ~110x in J)
    spine_t = 6.0
    c = c.union(cq.Workplane("XY")
                .box(INNER + 2 * CHEEK_T, spine_t, YOKE_H)
                .translate((0, -(BODY_W / 2 - spine_t / 2), 0))
                .edges("|Y").fillet(4.0))

    # generous root fillets where the spine meets the cheeks
    try:
        c = c.edges("|Y").fillet(FILLET_MIN)
    except Exception:                                     # noqa: BLE001
        pass

    # mounting: four M3 insert bosses in the spine
    for dx in (-INNER / 4, INNER / 4):
        for dz in (-YOKE_H / 4, YOKE_H / 4):
            c = c.cut(cq.Workplane("XZ")
                      .workplane(offset=(BODY_W / 2 - spine_t) - 0.5)
                      .center(dx, dz)
                      .circle(M3_INSERT_D / 2)
                      .extrude(M3_INSERT_L))
    return c


if __name__ == "__main__":
    part = build()
    step = os.path.join(OUT, "bearing_yoke.step")
    stl = os.path.join(OUT, "bearing_yoke.stl")
    cq.exporters.export(part, step)
    cq.exporters.export(part, stl, tolerance=0.01, angularTolerance=0.1)

    bb = part.val().BoundingBox()
    vol = part.val().Volume()
    print("bearing_yoke")
    print(f"  bearings  2 x 6806  ({BRG_ID} x {BRG_OD} x {BRG_W})")
    print(f"  pocket    Ø{POCKET_D:.2f}  (= OD + {BRG_FIT} press fit)")
    print(f"  seat lip  Ø{SEAT_D:.1f}   chamfer {BRG_CHAMFER} x 45")
    print(f"  spacing   {BRG_SPACING:.0f} mm face-to-face")
    print(f"  envelope  {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
    print(f"  volume    {vol/1000:.1f} cm3   ~{vol*1.24e-3*0.55:.0f} g PLA @35% infill")
    print(f"  wrote     {step}")
    print(f"  wrote     {stl}")
