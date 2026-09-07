"""
ARM-450 — SERVO HORN ADAPTER.

The part that closes the torque path. Until this existed there was none: the
servo horn had nothing to drive.

How that gap appeared. The old solid `joint_shaft` carried its own horn
interface -- a Ø36 shoulder with 4 x M3 on a Ø20 bolt circle. When the shaft
became a bought aluminium tube (because a printed shaft strips its preload
thread and creeps out of its press fit) the shoulder went with it, and nothing
replaced it. Separately, `horn_pattern()` was being called on the wrist parts
but cut at r = 7.0, which lands inside the Ø38 through bore -- already-empty
space, so a silent no-op. The 2026-08-21 geometry audit found both at once.

  servo (in link A)  ->  horn  ->  THIS PART  ->  roll pin  ->  tube
       ->  clamp  ->  link B

It reuses the roll-pin hole the tube already has 12 mm from each end, so the
tube needs no extra machining: one pin drives the clamp at one end, one drives
this adapter at the other.

Sized against servo STALL (2.94 N.m), not the gravity load:
    4 x M2 on Ø14 BCD   105 N/screw, bearing 13.1 MPa on the 4 mm face, SF 4.6
    Ø3 roll pin         196 N, bearing 8.2 MPa on the 4 mm wall,        SF 7.3
    hub torsion         0.45 MPa against ~18 interlayer,                SF 40
The binding path is bearing under the horn screws, which is why the face is
4 mm and not thinner.
"""
import math
import os
import sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *      # noqa: F403,F401

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")
os.makedirs(OUT, exist_ok=True)

HUB_OD = 36.0                     # 3.0 wall over the Ø30 tube. Was 38 (4.0);
                                  # pin bearing SF is still 5.5 and six adapters
                                  # are 6 g lighter, which the budget needed.
HUB_BORE = SHAFT_OD + 0.20        # 30.20 slip fit -- the pin locates it, not the fit
HUB_L = 16.0                      # straddles the pin at 12 mm with 4 mm to spare
FACE_T = 4.0                      # horn-screw bearing face
PIN_FROM_FACE = HUB_L - 12.0 + FACE_T   # aligns with the tube's own pin hole
HORN_RECESS_D = HORN_DISC_D + 0.4       # Ø19.6, receives the horn disc
HORN_RECESS_T = 1.6                     # so the face lands flat on the horn
HORN_PILOT_D = 1.9                      # M2 self-tapper into plastic


def horn_adapter():
    a = (cq.Workplane("XY").circle(HUB_OD / 2).extrude(FACE_T + HUB_L))
    # bore for the tube, blind -- the face stays solid to carry the horn screws
    a = a.cut(cq.Workplane("XY").workplane(offset=FACE_T)
              .circle(HUB_BORE / 2).extrude(HUB_L + 1))
    # recess so the adapter seats on the horn disc, not on the servo body
    a = a.cut(cq.Workplane("XY").circle(HORN_RECESS_D / 2).extrude(HORN_RECESS_T))
    # horn screws
    a = a.cut(cq.Workplane("XY")
              .pushPoints([(HORN_BCD / 2 * math.cos(2 * math.pi * k / HORN_N),
                            HORN_BCD / 2 * math.sin(2 * math.pi * k / HORN_N))
                           for k in range(HORN_N)])
              .circle(HORN_PILOT_D / 2).extrude(FACE_T + 0.5))
    # cable/tool clearance straight through the middle
    a = a.cut(cq.Workplane("XY").circle(6.0 / 2).extrude(FACE_T + 1))
    # roll pin, radial, through both hub walls AND the tube
    a = a.cut(cq.Workplane("XZ").workplane(offset=-HUB_OD)
              .center(0, PIN_FROM_FACE).circle(CLAMP_PIN_D / 2)
              .extrude(2 * HUB_OD))
    # scallop the face between the horn screws -- that material carries nothing
    for k in range(HORN_N):
        th = 2 * math.pi * (k + 0.5) / HORN_N
        a = a.cut(cq.Workplane("XY").workplane(offset=-0.5)
                  .center(11.5 * math.cos(th), 11.5 * math.sin(th))
                  .circle(4.2).extrude(FACE_T + 1))
    # Flats so it can be gripped while the pin is driven.
    # centered=(True, False, False) makes the box grow in +Y ONLY from the point
    # it is translated to. On the -Y side that ran the slab INWARD through the
    # part instead of outward, slicing off a 0.20 cm3 sliver that came away as a
    # separate body -- the part would have printed as two loose pieces. Caught by
    # the gate's "is ONE body" check. Centre the box properly and place it so it
    # spans from the flat depth outward, on both sides.
    FLAT_D, FLAT_BOX = 1.2, 8.0
    for sgn in (-1, 1):
        a = a.cut(cq.Workplane("XY")
                  .box(HUB_OD + 4, FLAT_BOX, HUB_L + FACE_T + 2,
                       centered=(True, True, False))
                  .translate((0, sgn * (HUB_OD / 2 - FLAT_D + FLAT_BOX / 2), -1)))
    try:
        a = a.edges("|Z").fillet(0.8)
    except Exception:          # noqa: BLE001 -- the grip flats cut the vertical
        pass                   # edge loop; the fillet is cosmetic, skip it
    return a


if __name__ == "__main__":
    p = horn_adapter()
    v = p.val().Volume()
    bb = p.val().BoundingBox()
    cq.exporters.export(p, os.path.join(OUT, "horn_adapter.step"))
    cq.exporters.export(p, os.path.join(OUT, "horn_adapter.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    print(f"horn_adapter  {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
    print(f"  volume {v/1000:.2f} cm3   ~{v*1.29e-3*0.55:.1f} g each   "
          f"{6*v*1.29e-3*0.55:.0f} g for six")
    print(f"  bore Ø{HUB_BORE:.2f}  pin Ø{CLAMP_PIN_D:.1f} at {PIN_FROM_FACE:.1f} "
          f"from the horn face")
    print(f"  {HORN_N} × Ø{HORN_PILOT_D:.1f} on Ø{HORN_BCD:.0f} BCD, "
          f"recess Ø{HORN_RECESS_D:.1f} × {HORN_RECESS_T:.1f}")
    print(f"  wrote horn_adapter.step / .stl")
