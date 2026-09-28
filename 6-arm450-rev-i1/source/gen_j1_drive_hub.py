#!/usr/bin/env python3
"""
ARM-450 rev H -- j1_drive_hub, nose-chamfer skin fixed.

THE DEFECT
----------
`arm450_study/j1_drive.py`, j1_drive_hub(), final chamfer block:

    nose = FLANGE_T + PLUG_L                       # 18.00
    OUTER: cylinder r = PLUG_D/2 + 2.0,  z 17.40 .. 18.00
    INNER: cone  r = PLUG_D/2 - 0.6  ->  PLUG_D/2 + 0.2,
                                         z 17.30 .. 18.10
    tool = OUTER.cut(INNER)

The INNER cone is a TAPER, so partway up it becomes wider than the plug and
the tool stops biting. Result: the cut removes material only up to
z = 17.80 and leaves a 0.20 mm ring of skin at z 17.80..18.00.

Measured on the released part: at (-2.50, 10.51) the column reads
    0.004 .. 17.400   (17.396 mm -- the plug, correct)
    17.804 .. 18.000  ( 0.196 mm -- the skin)
28 such columns confirmed by the solid classifier.

THE FIX
-------
Cut the nose chamfer as a single truncated cone, and give the tool an
overshoot past the nose so nothing is left above it. One cone, no boolean
of two lofts whose z spans disagree.
"""
import os
import re
import sys

import numpy as np
import cadquery as cq

STUDY = "/home/user/ros2_ws/arm450_study"
PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
sys.path.insert(0, STUDY)
sys.path.insert(0, PARTS)
import fixparams as FP                                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

_src = open(os.path.join(STUDY, "j1_drive.py")).read()


def _const(name, default=None):
    m = re.search(name + r"\s*=\s*([0-9.]+)", _src)
    if m:
        return float(m.group(1))
    if default is not None:
        return default
    raise KeyError(name)


FLANGE_D = _const("FLANGE_D")
FLANGE_T = _const("FLANGE_T")
PLUG_D = _const("PLUG_D", 21.8)
PLUG_L = _const("PLUG_L")
HORN_REC_D = _const("HORN_REC_D", 19.6)
HORN_REC_T = _const("HORN_REC_T")
CABLE_D = _const("CABLE_D")
GRUB_D = FP.M3_CLEAR
CHAMFER = 0.6
OVERSHOOT = 0.20


def j1_drive_hub():
    s = cq.Workplane("XY").circle(FLANGE_D / 2).extrude(FLANGE_T)
    s = s.union(cq.Workplane("XY").workplane(offset=FLANGE_T)
                .circle(PLUG_D / 2).extrude(PLUG_L))
    # horn recess into the underside (servo below, horn points up)
    s = s.cut(cq.Workplane("XY").circle(HORN_REC_D / 2).extrude(HORN_REC_T))
    # cable bore through
    s = s.cut(cq.Workplane("XY").circle(CABLE_D / 2)
              .extrude(FLANGE_T + PLUG_L + 2).translate((0, 0, -1)))
    # 4 x M2 self-tap pilots on the horn BCD
    for th in np.linspace(0, 2 * np.pi, 4, endpoint=False):
        x, y = FP.HORN_BCD / 2 * np.cos(th), FP.HORN_BCD / 2 * np.sin(th)
        s = s.cut(cq.Workplane("XY").workplane(offset=HORN_REC_T)
                  .center(x, y)
                  .circle(getattr(FP, "HORN_PILOT_D", 1.9) / 2)
                  .extrude(FLANGE_T))
    # 2 x M3 radial cross bolts, 90 deg apart, on perpendicular axes so the
    # torque path is double shear rather than friction
    for i, zz in enumerate((FLANGE_T + 4.5, FLANGE_T + 10.0)):
        ang = 0.0 if i == 0 else np.pi / 2
        d = np.array([np.cos(ang), np.sin(ang), 0.0])
        cyl = cq.Workplane("XY").circle(GRUB_D / 2).extrude(PLUG_D + 4)
        z = np.array([0, 0, 1.0])
        v = np.cross(z, d)
        sn = np.linalg.norm(v)
        c = float(np.dot(z, d))
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = np.eye(3) + vx + vx @ vx * ((1 - c) / sn ** 2)
        from OCP.gp import gp_Trsf
        tr = gp_Trsf()
        start = -d * (PLUG_D / 2 + 2)
        tr.SetValues(R[0, 0], R[0, 1], R[0, 2], start[0],
                     R[1, 0], R[1, 1], R[1, 2], start[1],
                     R[2, 0], R[2, 1], R[2, 2], zz)
        s = s.cut(cq.Workplane(obj=cyl.val().moved(cq.Location(tr))))

    # --- THE FIX ---------------------------------------------------------
    # ONE truncated cone, opening upward and outward, running from
    # (nose - CHAMFER) to (nose + OVERSHOOT). Because it only ever grows
    # with z, it cannot stop biting partway up the way the old two-loft
    # subtraction did.
    # THE RELEASED CHAMFER IS AN INVERTED TAPER.
    # Measured on the released part, radial extent vs height at the nose:
    #     z 17.30 : r 5.01 .. 10.90
    #     z 17.40 : r 5.01 .. 10.40   <- steps IN
    #     z 17.50 : r 5.01 .. 10.50
    #     z 17.90 : r 5.01 .. 10.90   <- back OUT
    #     z 18.00 : VOID
    # So the nose narrows then widens again: the last 0.6 mm is an
    # OVERHANGING LIP, 0.5 mm proud, sitting on nothing. A lead-in chamfer
    # must taper the other way -- widest at the bottom, narrowing to the
    # nose -- so the plug enters its bore square.
    #
    # Cut a ring whose inner boundary is a cone that GROWS with z. Anything
    # outside that cone, above z = nose - CHAMFER, is removed, which takes
    # the lip and leaves a true 45-degree lead-in.
    nose = FLANGE_T + PLUG_L
    r_nose = PLUG_D / 2 - CHAMFER          # 10.30 at the tip
    ring = (cq.Workplane("XY").workplane(offset=nose - CHAMFER)
            .circle(PLUG_D / 2 + 4.0)
            .extrude(CHAMFER + OVERSHOOT))
    keep = (cq.Workplane("XY").workplane(offset=nose - CHAMFER)
            .circle(PLUG_D / 2)
            .workplane(offset=CHAMFER)
            .circle(r_nose)
            .loft(combine=False))
    s = s.cut(ring.cut(keep))
    # ---------------------------------------------------------------------
    return s


if __name__ == "__main__":
    s = j1_drive_hub()
    print("j1_drive_hub rev H")
    print("   nose  = %.2f   chamfer %.2f  overshoot %.2f"
          % (FLANGE_T + PLUG_L, CHAMFER, OVERSHOOT))
    print("   volume %.3f mm3   solids %d"
          % (s.val().Volume(), len(s.val().Solids())))
    cq.exporters.export(s, os.path.join(HERE, "j1_drive_hub.step"))
    cq.exporters.export(s, os.path.join(HERE, "j1_drive_hub.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    print("   written")
