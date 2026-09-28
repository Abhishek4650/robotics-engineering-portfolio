#!/usr/bin/env python3
"""
ARM-450 rev H -- flat servo-mount pads added to J3_p1 and J5_p1.

WHY
---
Seven flange shapes were tried against these forks and every one interfered
(671 and 213 points at best). The reason is geometric, not a modelling slip:
`J3_p1` and `J5_p1` are OPEN FORKS WITH CURVED CHEEKS. Cross-sectioned at
z = 0, J3_p1 is a narrow stem (y +/-11) that steps out to a full-width slab
and then opens entirely. Any flange large enough to carry a 24.50 mm servo
channel reaches into the stem, the cheeks, or the bay walls.

The fork was never designed to carry a servo mount -- the same finding as
NO_SERVO_POCKETS.md, seen from the other side.

So: give the host a real flat face to bolt to, rather than keep reshaping the
clamp. One boss per part, added at the outboard face, carrying the four M3
stations. This follows the project's own pattern (j5_mount_fix.py imports the
released STEP, adds a feature, exports) rather than boolean surgery on a
finished assembly.

MEASURED INPUTS
---------------
  J3_p1  outboard face of the full-width slab  x = -27.00
         free envelope inboard of it           44 x 44 mm
  J5_p1  outboard face                          x = -17.25
         free envelope inboard of it           44 x 44 mm

The pad stands PROUD of the fork on -X, so it cannot foul anything inside the
bay, and the clamp then bolts to a genuinely flat face.
"""
import os
import sys

import cadquery as cq

PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
sys.path.insert(0, PARTS)
from fixparams import M3_INSERT_D, M3_INSERT_L     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "/home/user/ros2_ws/Arm_450_new_design/out_cad"

# Pad on the INBOARD (+X) side of the mounting face, so the servo channel --
# which must run +X toward the joint axis -- has clear air in front of it.
# A first version put the pad on -X; the clamp channel then ran back through
# it (1212 overlap points), and the blind insert cuts hollowed the pad out.
PAD_T = 6.0
PAD_W, PAD_H = 42.0, 42.0

HOSTS = {
    "J3_p1": dict(face_x=-27.00, bolts=[(-15.0, -15.0), (-15.0, 15.0),
                                        (15.0, -15.0), (15.0, 15.0)]),
    "J5_p1": dict(face_x=-17.25, bolts=[(-15.0, -15.0), (-15.0, 15.0),
                                        (15.0, -15.0), (15.0, 15.0)]),
}


def add_pad(nm, face_x, bolts):
    s = cq.Workplane(obj=cq.importers.importStep(
        os.path.join(OUT, nm + ".step")).val())
    # pad on the outboard face, growing away from the part
    # pad grows INBOARD from the mounting face
    pad = (cq.Workplane("YZ").workplane(offset=face_x)
           .rect(PAD_W, PAD_H).extrude(PAD_T))
    s = s.union(pad)
    # M3 heat-set stations, blind INTO the pad from its outer face (x=face_x),
    # so the pad keeps its full thickness behind each insert
    for y, z in bolts:
        s = s.cut(cq.Workplane("YZ").workplane(offset=face_x - 0.5)
                  .center(y, z).circle(M3_INSERT_D / 2)
                  .extrude(M3_INSERT_L + 0.5))
    return s


if __name__ == "__main__":
    print("Adding flat servo-mount pads")
    print("   pad %.0f x %.0f x %.1f, 4 x O%.1f inserts on (+/-15, +/-15)"
          % (PAD_W, PAD_H, PAD_T, M3_INSERT_D))
    print()
    for nm, cfg in HOSTS.items():
        s = add_pad(nm, cfg["face_x"], cfg["bolts"])
        n = len(s.val().Solids())
        print("   %-10s pad on x = %.2f   volume %.1f mm3   solids %d"
              % (nm, cfg["face_x"], s.val().Volume(), n))
        cq.exporters.export(s, os.path.join(HERE, nm + ".step"))
        cq.exporters.export(s, os.path.join(HERE, nm + ".stl"),
                            tolerance=0.01, angularTolerance=0.1)
    print()
    print("written to %s" % HERE)
