"""
Solid bearing models — the real bought parts, so fits can be checked in the
assembly instead of waiting for a test print.

The arm uses TWO sizes and this file now builds both:
    6806-2RS  30 x 42 x 7   J1 turret, J2 shoulder, J3 elbow
    6706-2RS  30 x 37 x 4   J4 roll, J5 pitch, J6 tool roll

Only the 6806 existed until 2026-09-01, so the wrist bearings could not be shown
in an assembly at all. Modelled as two races and a ball track: the OUTER
diameter and the WIDTH are what the pocket has to accept, and the INNER bore is
what the O30 tube has to fill. Those three numbers are the whole fit problem.
"""
import os
import sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *      # noqa: F403,F401

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")


def bearing(od=None, idia=None, w=None):
    od = BRG_OD if od is None else od
    idia = BRG_ID if idia is None else idia
    w = BRG_W if w is None else w
    b = (cq.Workplane("XY").circle(od / 2).circle(idia / 2).extrude(w))
    # relieve the middle so the two races read separately in a section.
    # The relief is proportional to the width: a fixed 1.2 mm shoulder each side
    # leaves 4 - 2.4 = 1.6 mm on the 6706, which is thin but valid; anything
    # wider would cut straight through it.
    sh = min(1.2, w * 0.3)
    b = b.cut(cq.Workplane("XY").workplane(offset=sh)
              .circle(od / 2 - 1.0).circle(idia / 2 + 1.0)
              .extrude(w - 2 * sh))
    return b


if __name__ == "__main__":
    for stem, (od, idia, w) in (
            ("bearing_6806", (BRG_OD, BRG_ID, BRG_W)),
            ("bearing_6706", (WRIST_BRG_OD, WRIST_BRG_ID, WRIST_BRG_W))):
        p = bearing(od, idia, w)
        cq.exporters.export(p, os.path.join(OUT, f"{stem}.step"))
        cq.exporters.export(p, os.path.join(OUT, f"{stem}.stl"),
                            tolerance=0.005, angularTolerance=0.05)
        bb = p.val().BoundingBox()
        print(f"{stem}  Ø{bb.xlen:.2f} × {bb.zlen:.2f}  bore Ø{idia:.2f}")
