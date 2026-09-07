"""
ARM-450 — joint shaft and shaft clamp.

These are the two parts that were missing: without them the link halves, the
bearings and the servo have no mechanical connection and nothing rotates.

SHAFT (Ø30, runs in the two 6806 bearings inside the link boss)
  * integral shoulder locates the FIRST inner race
  * plain Ø30 through both bearings, 22 mm apart
  * D-FLAT so the clamp cannot slip under torque -- a plain round clamp on a
    printed part relies on friction alone and will creep
  * M5 tapped end for the PRELOAD screw. That screw pulls the two INNER races
    together against the spacer while the outer races stay seated on the Ø38
    shoulders in the link. Preload is what turns 6.55 mm of wobble into 0.65 mm.
  * 4 x M3 on a Ø20 bolt circle in the shoulder face for the servo horn

CLAMP (presses into the mating link's existing Ø42 bearing pocket)
  * Ø42 OD, so it reuses the pocket already in the printed link -- no change to
    the parts you have
  * Ø30 bore onto the shaft, split, with two radial M3 grub screws bearing on
    the D-flat
"""

import os
import sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *      # noqa: F403,F401

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")
os.makedirs(OUT, exist_ok=True)

SHAFT_D = BRG_ID                 # 30
SHAFT_L = 72.0
SHOULDER_D, SHOULDER_L = 36.0, 4.0
FLAT_DEPTH = 2.0                 # D-cut depth
FLAT_FROM = 44.0                 # flat starts here, in the clamp zone
PRELOAD_TAP = 4.2                # M5 tap drill
PRELOAD_DEPTH = 14.0
HORN_BCD, HORN_N = 20.0, 4

# 2026-08-18: was Ø42 (the BEARING POCKET) x 12 wide -- but that pocket is only
# 7 mm deep per half, so 5 mm of the clamp hung out and it could never seat.
# The boss has three zones through its 29 mm: Ø42 pocket 7 | Ø38 through 15 |
# Ø42 pocket 7. The clamp belongs in the Ø38 THROUGH-BORE, between the bearings.
CLAMP_OD = BRG_OD - 2 * BRG_SHOULDER     # 38, the through-bore
CLAMP_W = 14.0                            # <= the 15 mm through-bore length
CLAMP_BORE = SHAFT_D + 0.2
CLAMP_SPLIT = 1.2


def shaft():
    s = (cq.Workplane("XY").circle(SHOULDER_D / 2).extrude(SHOULDER_L)
         .faces(">Z").workplane().circle(SHAFT_D / 2)
         .extrude(SHAFT_L - SHOULDER_L))
    # D-flat in the clamp zone
    s = s.cut(cq.Workplane("XY")
              .box(SHAFT_D, SHAFT_D, SHAFT_L - FLAT_FROM, centered=(True, True, False))
              .translate((0, SHAFT_D / 2 + (SHAFT_D / 2 - FLAT_DEPTH), FLAT_FROM)))
    # preload tap in the far end
    s = s.cut(cq.Workplane("XY").circle(PRELOAD_TAP / 2)
              .extrude(PRELOAD_DEPTH).translate((0, 0, SHAFT_L - PRELOAD_DEPTH)))
    # servo-horn bolt circle in the shoulder face
    s = (s.faces("<Z").workplane()
         .polarArray(HORN_BCD / 2, 0, 360, HORN_N)
         .circle(M3_CLEAR / 2).cutBlind(-9.0))
    s = s.edges("|Z").fillet(0.4) if False else s
    return s


def clamp():
    c = (cq.Workplane("XY").circle(CLAMP_OD / 2).extrude(CLAMP_W)
         .faces(">Z").workplane().circle(CLAMP_BORE / 2).cutThruAll())
    # split slot
    c = c.cut(cq.Workplane("XY")
              .box(CLAMP_SPLIT, CLAMP_OD, CLAMP_W + 2)
              .translate((0, CLAMP_OD / 4, -1)))
    # two radial M3 grub screws bearing on the D-flat
    for dz in (CLAMP_W * 0.3, CLAMP_W * 0.7):
        c = c.cut(cq.Workplane("XZ").workplane(offset=-CLAMP_OD)
                  .center(0, dz).circle(3.0 / 2).extrude(2 * CLAMP_OD))
    try:
        c = c.edges("|Z").fillet(1.0)
    except Exception:          # noqa: BLE001 -- split-slot edges are too tight
        pass                   # for a 1 mm fillet; cosmetic only, skip it
    return c


def report(part, name):
    bb = part.val().BoundingBox()
    v = part.val().Volume()
    print(f"{name}")
    print(f"  envelope  {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
    print(f"  volume    {v/1000:.1f} cm3")
    cq.exporters.export(part, os.path.join(OUT, f"{name}.step"))
    cq.exporters.export(part, os.path.join(OUT, f"{name}.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    print(f"  wrote     {name}.step / .stl")


if __name__ == "__main__":
    print(f"shaft Ø{SHAFT_D:.0f} x {SHAFT_L:.0f}, bearings {BRG_ID}x{BRG_OD}x{BRG_W} "
          f"at {SEC_W-BRG_W:.0f} mm spacing\n")
    report(shaft(), "joint_shaft")
    print()
    report(clamp(), "shaft_clamp")
    print("\nNOTE: the shaft is a STEEL part -- print it only as a fit check.")
    print("A printed Ø30 shaft will creep under the 2.6 N.m shoulder torque.")
