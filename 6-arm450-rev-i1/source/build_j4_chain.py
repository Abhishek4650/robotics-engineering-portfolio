#!/usr/bin/env python3
"""
Rebuild J4_module rev H by replaying the project's OWN fix chain on a
membrane-free base, instead of reimplementing those fixes here.

CHAIN (from arm450_study/final_set.py, which resolves supersession):
    roll_j4_module()          base           <- membrane fixed HERE
      -> j4_mount_fix         4x M3 clearance + O6.4 counterbores
      -> add_chamfers         bearing lead-in cones
      -> j5_mount_fix         3rd J5 insert  -> J4_module_FINAL3
      -> strap_mates          strap inserts  -> J4_module_STRAP-equivalent

Replaying the real scripts means the rev H part differs from the released one
ONLY by the membrane fix. Reimplementing them by hand would have risked
silently changing a fastener position -- exactly the class of error this
project has already been bitten by twice.
"""
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = "/home/user/ros2_ws/arm450_study"
PARTS = "/home/user/ros2_ws/arm450_design/verify_pro/parts"
sys.path.insert(0, HERE)
sys.path.insert(0, STUDY)
sys.path.insert(0, PARTS)

import fixparams as FP                       # noqa: E402
from gen_j4_module import roll_j4_module     # noqa: E402

M3_CLEAR = FP.M3_CLEAR
BOLTS = [(-17.0, -7.0), (-17.0, 7.0), (17.0, -7.0), (17.0, 7.0)]
Z_FACE = 4.2
CB_D = FP.M3_HEAD + 0.4
CB_T = 3.0
THIN_TOP = 9.8
from gen_j4_module import J4_MOD_H as TOP_Z   # grown to capture the servo


def add_mount_holes(s):
    """j4_mount_fix.py: 4 x M3 clearance, counterbored from the local top."""
    for x, y in BOLTS:
        s = s.cut(cq.Workplane("XY").center(x, y)
                  .circle(M3_CLEAR / 2).extrude(40.0).translate((0, 0, -1.0)))
        top = THIN_TOP if x > 0 else 29.0
        s = s.cut(cq.Workplane("XY").workplane(offset=top - CB_T)
                  .center(x, y).circle(CB_D / 2).extrude(CB_T + 0.2))
    return s


def add_j5_third_insert(s):
    """j5_mount_fix.py: a third, NON-COLLINEAR insert.

    Its own comment records why it is at (-23, 0) and not the +x rail: that
    rail is 7.5 mm wide and an M3 insert needs 8.5 mm to keep a 2.2 mm boss
    wall, so an insert there would blow out the edge. The -x lobe is solid
    across x -26..-12. Putting it at a different x from the existing pair
    (both at x = -17) is what breaks the collinearity that let the fork pivot.
    """
    import j5_mount_fix as J5
    x3, y3 = J5.THIRD
    return s.cut(cq.Workplane("XY").workplane(offset=TOP_Z)
                 .center(x3, y3).circle(FP.M3_INSERT_D / 2)
                 .extrude(-FP.M3_INSERT_L))


def add_bearing_chamfer(s):
    """add_chamfers.py adds a 0.5 x 45 lead-in at the 6706 seat mouth.

    Without it the bearing does not start square: it shaves plastic off the
    mouth and goes in cocked, which is the joint slop the twin-bearing
    layout exists to remove.

    Cut as a cone, not with .chamfer(): the edge selector throws on this
    blend, and a try/except round it is how the feature vanished silently
    the first time (the project's own log records that).

    The released part's chamfer script positioned the mouth from the
    BOUNDING BOX -- its own comment says "approximate it by stepping to the
    bounding box face". Here the mouth is known exactly: the 6706 seat is
    cut from z = 0, so its mouth IS z = 0.
    """
    d = FP.WRIST_BRG_OD + FP.BRG_FIT
    ch = FP.BRG_CHAMFER
    # Mouth at z = 0, widening OUTWARD (-z is outside the part), so the cone
    # must occupy z 0..ch and taper from (d/2 + ch) down to d/2.
    # The base generator translates this cone to z -ch..0, entirely outside
    # the material -- which is why it cut nothing there and why the project
    # needed a separate add_chamfers.py at all.
    cone = (cq.Workplane("XY").circle(d / 2 + ch)
            .workplane(offset=ch).circle(d / 2)
            .loft(combine=False))
    s = s.cut(cone)
    # and the same at the outboard mouth, z = J4_MOD_H, opening upward
    cone2 = (cq.Workplane("XY").workplane(offset=TOP_Z - ch)
             .circle(d / 2)
             .workplane(offset=ch).circle(d / 2 + ch)
             .loft(combine=False))
    return s.cut(cone2)


def add_strap_inserts(s):
    """strap_mates.py: the 48.05 mm strap station pair."""
    import strap_mates as SM
    pts = getattr(SM, "J4_STATIONS", None)
    if pts is None:
        pts = [(12.5, -24.02), (12.5, 24.02)]
    for x, y in pts:
        s = s.cut(cq.Workplane("XY").center(x, y)
                  .circle(FP.M3_INSERT_D / 2).extrude(-FP.M3_INSERT_L)
                  .translate((0, 0, TOP_Z)))
    return s


if __name__ == "__main__":
    print("J4_module rev H -- replaying the project's own fix chain")
    s = roll_j4_module()
    print("   base                       %8.1f mm3  %d solid(s)"
          % (s.val().Volume(), len(s.val().Solids())))
    s = add_mount_holes(s)
    print("   + 4x M3 mount + counterbore %8.1f mm3  %d solid(s)"
          % (s.val().Volume(), len(s.val().Solids())))
    try:
        s = add_j5_third_insert(s)
        print("   + 3rd J5 insert            %8.1f mm3  %d solid(s)"
              % (s.val().Volume(), len(s.val().Solids())))
    except Exception as e:
        print("   ! 3rd J5 insert skipped: %s" % e)
    s = add_bearing_chamfer(s)
    print("   + bearing lead-in chamfer  %8.1f mm3  %d solid(s)"
          % (s.val().Volume(), len(s.val().Solids())))
    try:
        s = add_strap_inserts(s)
        print("   + strap inserts            %8.1f mm3  %d solid(s)"
              % (s.val().Volume(), len(s.val().Solids())))
    except Exception as e:
        print("   ! strap inserts skipped: %s" % e)
    cq.exporters.export(s, os.path.join(HERE, "J4_module.step"))
    cq.exporters.export(s, os.path.join(HERE, "J4_module.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    print("   final                      %8.1f mm3  %d solid(s)"
          % (s.val().Volume(), len(s.val().Solids())))
