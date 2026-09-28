#!/usr/bin/env python3
"""
ARM-450 rev I -- link centring ring (file name kept: shaft_clamp), 4 off.

History, all measured:
  * the released O38 ring could not enter the links' bores (the seam ear
    intrudes as a flat 16.0 from the axis);
  * the first rev-I C-clamp straddled the ear, but link -> clamp was keyed
    only by that ear with 0.2 mm each side = +-1 deg of play at J2/J3 (about
    +-8 mm at the tool) -- Rule 4 "attached" check: the links hung on
    clearances only.

Now the torque path is: link --(M5 thread, self-tapped in the link's own
O4.2 side holes at 90/270 deg)--> M5 x 10 cup-point set screw --(tip on the
shaft's double-D flat)--> shaft. Zero play, both directions.
This ring only CENTRES the link on the shaft: 0.025 mm running fit on the
O29.95 shaft and in the O38.4 link bore (a C: it springs over a slightly
tight print), a O5.4 clearance hole for each set screw, and the gap still
straddles the seam ear.
"""
import os
import sys

import numpy as np
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OD, BORE, W = 38.35, 30.0, 14.0
# the ear, sliced at z 0.5/3.5/7/10.5/13.5 in all four links (identical):
# half-width 5.49 at r 19.0 -> gap 2 x (5.5 + 0.2)
GAP = 11.4
SET_HOLE = 5.4              # M5 set screw passes through
SET_Z = 7.0                 # the link's side-hole height (PIN_Z)
GRUB_Z = SET_Z              # (old name, used by the checks)
SET_L = 10.0                # M5 x 10: tip on the flat (r 14.2), end 0.8 inside the link flank


def clamp():
    s = cq.Workplane("XY").circle(OD / 2).circle(BORE / 2).extrude(W)
    s = s.cut(cq.Workplane("XY").center(-OD / 4 - 2.0, 0).rect(OD / 2 + 4.0, GAP)
              .extrude(W + 2).translate((0, 0, -1)))
    # trim the knife-edge tips where the parallel gap faces meet the O38.35
    # outside (a 17 deg wedge, 0.3 mm thin -- audit): square them off at x -17.8
    s = s.cut(cq.Workplane("XY").center(-19.9, 0).rect(4.2, 15.0).extrude(W + 2).translate((0, 0, -1)))
    for ang in (90, 270):
        a = np.radians(ang)
        s = s.cut(cq.Workplane("XY").add(
            cq.Solid.makeCylinder(SET_HOLE / 2, OD / 2 + 1,
                                  cq.Vector(0, 0, SET_Z), cq.Vector(np.cos(a), np.sin(a), 0))))
    return s


if __name__ == "__main__":
    from OCP.BRepCheck import BRepCheck_Analyzer
    c = clamp()
    v = c.val()
    print("link centring ring  %.1f mm3  solids %d  shells %d  valid %s"
          % (v.Volume(), len(v.Solids()), len(v.Shells()), BRepCheck_Analyzer(v.wrapped).IsValid()))
    cq.exporters.export(c, os.path.join(HERE, "shaft_clamp.step"))
    cq.exporters.export(c, os.path.join(HERE, "shaft_clamp.stl"), tolerance=0.01, angularTolerance=0.1)
