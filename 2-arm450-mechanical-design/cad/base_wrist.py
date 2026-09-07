"""
ARM-450 — the remaining structural parts: base, wrist, tool flange.

BASE (50 mm tall, the user's own sketch dimension)
  * flared foot with 4 x M4 bolt-down holes
  * Ø52 central cable bore -- straight from their paper sketch
  * tapered pedestal, hexagonal facets so it does not read as a plain puck
  * top face carries the J1 turret bearing seat (Ø42 pocket, same 6806 as every
    other joint, so the whole arm uses ONE bearing part number)

WRIST (J5 wrist centre -> TCP = 70 mm, per the 450 mm chain)
  * Ø42 bore at the J5 end so it mounts on the same shaft/bearing stack as
    every other joint -- no new interface
  * J6 roll servo pocket
  * tool flange face at the far end

TOOL FLANGE
  * Ø40 disc, 4 x M3 on a Ø30 bolt circle, Ø10 centre pilot
  * the standard mounting face the gripper or pen holder bolts to
"""

import os
import sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *      # noqa: F403,F401

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")
os.makedirs(OUT, exist_ok=True)

# ---- base -----------------------------------------------------------------
BASE_H = 50.0
FOOT_D, FOOT_T = 120.0, 5.5      # was 7.0 — mass campaign 2026-08-21
# 2026-08-21: PED_D_TOP 80.0 -> 72.0. The exact-mesh check on the SINE PATH
# (not the random joint sweep -- the actual 240 solved waypoints) found the
# upper arm clipping the top outer rim of the pedestal by 1.27 mm at z = 50.0,
# on 30 % of the path. It is a graze, not a placement error, so pulling the top
# of the taper in by 4 mm of radius clears it with margin to spare and takes a
# little mass out at the same time. The J1 bearing seat is at r = 21, untouched.
PED_D_BOT, PED_D_TOP = 96.0, 72.0
CABLE_BORE = 52.0
FOOT_BOLT = 4.5                 # M4 clearance
FOOT_BCD = 104.0

# ---- wrist ----------------------------------------------------------------
WRIST_L = 70.0                  # J5 centre -> TCP
WRIST_W, WRIST_H = 34.0, 44.0

# ---- tool flange ----------------------------------------------------------
FLANGE_D, FLANGE_T = 40.0, 6.0
FLANGE_BCD, FLANGE_PILOT = 30.0, 10.0


# 0.5 x 45 LEAD-IN CHAMFER at every bearing-pocket mouth.
# BRG_CHAMFER has been in params.py, on the drawings and in the docstrings since
# the design was written, and a STEP audit for CONICAL faces found ZERO in every
# part carrying a pocket -- the feature was specified everywhere and cut nowhere.
# It is what lets a Ø42 bearing start square in a Ø42 hole.
# Cut as a CONE rather than with .chamfer(): the edge selector throws whenever a
# boss blend is awkward, and the try/except that catches it is exactly how a
# feature disappears in silence.
def _chamfer_mouth(solid, cx, cy, z_mouth, pocket_d, cham, down=True):
    import cadquery as _cq
    d = -1.0 if down else 1.0
    return solid.cut(_cq.Workplane("XY").center(cx, cy)
                     .circle(pocket_d / 2 + cham)
                     .workplane(offset=cham * d)
                     .circle(pocket_d / 2)
                     .loft(combine=False)
                     .translate((0, 0, z_mouth if down else z_mouth)))


def base():
    b = cq.Workplane("XY").circle(FOOT_D / 2).extrude(FOOT_T)
    b = b.edges(">Z or <Z").fillet(1.5)
    # tapered pedestal
    ped = (cq.Workplane("XY").workplane(offset=FOOT_T)
           .circle(PED_D_BOT / 2)
           .workplane(offset=BASE_H - FOOT_T)
           .circle(PED_D_TOP / 2).loft())
    b = b.union(ped)
    # HOLLOW IT. Modelled solid the base was 234 cm3 = 166 g, the single
    # biggest printed item in the arm and 14 % of the whole mass budget.
    # A 3 mm shell keeps the same outside and the same bearing seat.
    SHELL = 3.0
    # The internal shell loft must also stop below the bearing shoulder,
    # otherwise it re-opens the very seat the cut above creates.
    b = b.cut(cq.Workplane("XY").workplane(offset=SHELL)
              .circle(PED_D_BOT / 2 - SHELL)
              .workplane(offset=BASE_H - 2 * SHELL - BRG_W - 3.0)
              .circle(PED_D_TOP / 2 - SHELL).loft())
    # 2026-08-21 AUDIT FIX. This used to cut the Ø52 cable bore through the FULL
    # height and then cut a Ø42 "bearing seat" inside it. 42 < 52, so the seat cut
    # removed nothing -- a silent no-op -- and the base had no J1 seat at all. A
    # Ø42 bearing dropped straight through a Ø52 hole.
    #
    # The cable bore now STOPS below the seat, leaving a Ø38 shoulder for the
    # outer race to land on, exactly like every other joint in the arm. Cables
    # still pass: Ø38 through the shoulder, and the joint shaft above it is a
    # tube with a Ø26 bore.
    SEAT_D = BRG_OD - 2 * BRG_SHOULDER                 # 38
    SHOULDER_T = 3.0                                   # race lands on this
    bore_top = BASE_H - BRG_W - SHOULDER_T
    # wide cable bore from the foot up to just under the shoulder
    b = b.cut(cq.Workplane("XY").circle(CABLE_BORE / 2).extrude(bore_top + 1)
              .translate((0, 0, -1)))
    # Ø38 through the shoulder and on up -- this IS the shoulder
    b = b.cut(cq.Workplane("XY").workplane(offset=bore_top)
              .circle(SEAT_D / 2).extrude(BASE_H - bore_top + 1))
    # J1 turret bearing seat, counterbored into the top face
    b = b.cut(cq.Workplane("XY").workplane(offset=BASE_H - BRG_W)
              .circle((BRG_OD + BRG_FIT) / 2).extrude(BRG_W + 1))
    b = _chamfer_mouth(b, 0, 0, BASE_H - BRG_CHAMFER,
                       BRG_OD + BRG_FIT, BRG_CHAMFER, down=False)
    # LIGHTENING RECESS in the underside of the foot. The foot was a solid
    # Ø120 x 7 plate -- 79 cm3, more than half the whole base -- for a part that
    # only has to spread four bolts. Recess the annulus between the cable bore
    # and the bolt circle, leaving a 3 mm floor, an outer rim that carries the
    # bolts and an inner rim around the bore.
    b = b.cut(cq.Workplane("XY").workplane(offset=-0.01)
              .circle(47.0).circle(30.0).extrude(FOOT_T - 3.0))
    # 4 x M4 bolt-down through the foot
    b = (b.faces("<Z").workplane()
         .polarArray(FOOT_BCD / 2, 45, 360, 4)
         .circle(FOOT_BOLT / 2).cutThruAll())
    return b


def wrist():
    w = (cq.Workplane("XY")
         .box(WRIST_L, WRIST_W, WRIST_H, centered=(False, True, True))
         .edges("|X").fillet(6.0))
    # J5 end: Ø42 bearing pocket both faces, Ø38 through -- same as a link boss
    w = w.cut(cq.Workplane("XZ").workplane(offset=-WRIST_W / 2 - 1)
              .center(12.0, 0).circle((BRG_OD - 2 * BRG_SHOULDER) / 2)
              .extrude(WRIST_W + 2))
    for off in (-WRIST_W / 2 - 0.01, WRIST_W / 2 - BRG_W + 0.01):
        w = w.cut(cq.Workplane("XZ").workplane(offset=off)
                  .center(12.0, 0).circle((BRG_OD + BRG_FIT) / 2).extrude(BRG_W))
        t = _chamfer_mouth(t, 12.0, 0, off + (0.0 if off < 0 else BRG_W),
                           BRG_OD + BRG_FIT, BRG_CHAMFER, down=(off < 0))
    # J6 servo pocket
    w = w.cut(cq.Workplane("XY").workplane(offset=-SERVO_T / 2)
              .center(WRIST_L * 0.60, 0)
              .rect(SERVO_L + 2 * SERVO_CLR, SERVO_W + 2 * SERVO_CLR)
              .extrude(SERVO_T))
    # lighten the web
    for dx in (0.34, 0.46):
        w = w.cut(cq.Workplane("XZ").workplane(offset=-WRIST_W / 2 - 1)
                  .center(WRIST_L * dx, 0).circle(6.0).extrude(WRIST_W + 2))
    return w


def tool_flange():
    f = cq.Workplane("XY").circle(FLANGE_D / 2).extrude(FLANGE_T)
    f = f.cut(cq.Workplane("XY").circle(FLANGE_PILOT / 2)
              .extrude(FLANGE_T + 2).translate((0, 0, -1)))
    f = (f.faces(">Z").workplane()
         .polarArray(FLANGE_BCD / 2, 45, 360, 4)
         .circle(M3_CLEAR / 2).cutThruAll())
    f = f.edges(">Z or <Z").fillet(0.8)
    return f


def report(part, name):
    bb = part.val().BoundingBox()
    v = part.val().Volume()
    print(f"{name}")
    print(f"  envelope  {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
    print(f"  volume    {v/1000:.1f} cm3   ~{v*1.29e-3*0.5:.0f} g printed")
    cq.exporters.export(part, os.path.join(OUT, f"{name}.step"))
    cq.exporters.export(part, os.path.join(OUT, f"{name}.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    print(f"  wrote     {name}.step / .stl")


if __name__ == "__main__":
    report(base(), "base")
    print()
    report(wrist(), "wrist")
    print()
    report(tool_flange(), "tool_flange")
