"""
ARM-450 joint shaft — the AL6061 tube that replaced the printed solid shaft.

This is a BOUGHT part; the only operations are cut to length and drill two
cross holes for the roll pin. It is modelled so the assembly, the mass budget
and the drawing all describe the same object.

Why a tube and not a printed shaft: printing does not fail on strength (SF 32
in torsion, SF 104 in bending at servo stall). It fails because the M5 preload
thread strips -- threads cut across layer lines hold ~18 MPa against ~16 MPa
demand -- and because a press fit is stored elastic strain, which plastic
relaxes away over days. Both are local, so metal goes only where it is needed.
"""
import os
import sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *      # noqa: F403,F401

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")
os.makedirs(OUT, exist_ok=True)

PIN_INSET = 12.0          # roll-pin holes this far from each end


def shaft_tube():
    t = (cq.Workplane("XY").circle(SHAFT_OD / 2)
         .circle(SHAFT_OD / 2 - SHAFT_WALL)
         .extrude(SHAFT_L))
    for z in (PIN_INSET, SHAFT_L - PIN_INSET):
        t = t.cut(cq.Workplane("XZ").workplane(offset=-SHAFT_OD)
                  .center(0, z).circle(CLAMP_PIN_D / 2).extrude(2 * SHAFT_OD))
    return t


if __name__ == "__main__":
    p = shaft_tube()
    v = p.val().Volume()
    m = v * SHAFT_RHO
    cq.exporters.export(p, os.path.join(OUT, "shaft_tube.step"))
    cq.exporters.export(p, os.path.join(OUT, "shaft_tube.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    print(f"shaft_tube  Ø{SHAFT_OD:.0f} x {SHAFT_WALL:.0f} wall x {SHAFT_L:.0f}")
    print(f"  volume {v/1000:.2f} cm3   mass {m:.1f} g each   {6*m:.0f} g for six")
    print(f"  roll-pin holes Ø{CLAMP_PIN_D:.1f} at {PIN_INSET:.0f} from each end")
    print(f"  wrote shaft_tube.step / .stl")
