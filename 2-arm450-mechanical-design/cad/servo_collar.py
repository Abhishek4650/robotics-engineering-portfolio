"""
ARM-450 — servo clamp collar.

Replaces Motor_fixer_j2_p1/p2 and the notched U-channel, which fail at servo
stall torque (report 9.3). A full-perimeter split collar wraps the whole servo
body so the reaction torque is carried as shear flow around a closed loop:

    q = T/(2*Am),  tau = q/wall
    Am = 48.2 x 40.8 = 1967 mm^2  ->  tau = 0.25 MPa at ST3215 stall
    vs 17-95 MPa bending in the 4 mm bracket it replaces.

Orientation note: the servo output axis runs along its 24.7 mm thickness, so
the collar wraps the 45.2 x 37.8 cross-section and its height runs along the
output axis. Print it with that axis VERTICAL (report 11.1).
"""

import os
import sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *      # noqa: F403,F401

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")
os.makedirs(OUT, exist_ok=True)

# --- bore = servo body + clearance all round -------------------------------
BORE_L = SERVO_L + 2 * SERVO_CLR        # 45.6
BORE_W = SERVO_W + 2 * SERVO_CLR        # 38.2

# --- outer envelope --------------------------------------------------------
OUT_L = BORE_L + 2 * COLLAR_WALL        # 51.6
OUT_W = BORE_W + 2 * COLLAR_WALL        # 44.2


def build():
    # 1. outer body, corners rounded so there is no sharp reentrant corner
    c = (cq.Workplane("XY")
         .box(OUT_L, OUT_W, COLLAR_H)
         .edges("|Z").fillet(4.0))

    # 2. the servo pocket, straight through along the output axis
    c = (c.faces(">Z").workplane(centerOption="CenterOfBoundBox")
         .rect(BORE_L, BORE_W)
         .cutThruAll())
    # soften the bore corners — this is where a crack would start
    c = c.edges("|Z").edges(cq.selectors.BoxSelector(
        (-BORE_L / 2 - 0.6, -BORE_W / 2 - 0.6, -COLLAR_H),
        (BORE_L / 2 + 0.6, BORE_W / 2 + 0.6, COLLAR_H))).fillet(FILLET_MIN)

    # 3. clamp lugs, standing off the +Y face either side of the split
    lug_y = OUT_W / 2 + LUG_L / 2
    for sx in (-1, 1):
        c = (c.union(
            cq.Workplane("XY")
            .box(LUG_W, LUG_L, LUG_T)
            .translate((sx * (LUG_W / 2 + COLLAR_SPLIT / 2), lug_y, 0))
            .edges("|Z").fillet(2.0)))

    # 4. the split: a slot from the +Y outer face into the bore
    c = c.cut(cq.Workplane("XY")
              .box(COLLAR_SPLIT, LUG_L + OUT_W, COLLAR_H + 2)
              .translate((0, OUT_W / 4 + LUG_L / 2, 0)))

    # 5. TWO clamp screws through the lugs, spaced along the collar height,
    #    so the clamp closes evenly instead of pivoting about a single bolt.
    for dz in (-COLLAR_H / 4, COLLAR_H / 4):
        c = c.cut(cq.Workplane("YZ")
                  .workplane(offset=-OUT_L)
                  .center(lug_y, dz)
                  .circle(M3_CLEAR / 2)
                  .extrude(2 * OUT_L))
        # counterbore for the socket head on the -X lug
        c = c.cut(cq.Workplane("YZ")
                  .workplane(offset=-(LUG_W + COLLAR_SPLIT / 2))
                  .center(lug_y, dz)
                  .circle(M3_HEAD / 2)
                  .extrude(LUG_W))

    return c


def build_with_flange(flange_t=6.0):
    """
    Collar with an integral bolt FLANGE on the -X face.

    Deliberately NOT a cantilever stub arm: report 9.5 shows a slender arm in
    bending is exactly the topology that failed. A flange bolted flat against
    the link shell puts the fasteners in shear and adds no bending arm at all.
    """
    c = build()
    fl_w, fl_h = OUT_W + 2 * 6.0, COLLAR_H
    flange = (cq.Workplane("XY")
              .box(flange_t, fl_w, fl_h)
              .translate((-(OUT_L / 2 + flange_t / 2 - 0.01), 0, 0))
              .edges("|X").fillet(3.0))
    c = c.union(flange)

    # four M3 clearance holes through the flange, well outside the collar wall
    for dy in (-(OUT_W / 2 + 3.0), (OUT_W / 2 + 3.0)):
        for dz in (-COLLAR_H / 4, COLLAR_H / 4):
            c = c.cut(cq.Workplane("YZ")
                      .workplane(offset=-(OUT_L / 2 + flange_t + 1))
                      .center(dy, dz)
                      .circle(M3_CLEAR / 2)
                      .extrude(flange_t + 2))
    return c


if __name__ == "__main__":
    part = build_with_flange()
    step = os.path.join(OUT, "servo_collar.step")
    stl = os.path.join(OUT, "servo_collar.stl")
    cq.exporters.export(part, step)
    cq.exporters.export(part, stl, tolerance=0.01, angularTolerance=0.1)

    bb = part.val().BoundingBox()
    vol = part.val().Volume()
    print("servo_collar")
    print(f"  bore      {BORE_L:.1f} x {BORE_W:.1f} mm  (servo {SERVO_L} x {SERVO_W} "
          f"+ {SERVO_CLR} per side)")
    print(f"  envelope  {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
    print(f"  volume    {vol/1000:.1f} cm3   ~{vol*1.24e-3*0.55:.0f} g PLA @35% infill")
    print(f"  wrote     {step}")
    print(f"  wrote     {stl}")
