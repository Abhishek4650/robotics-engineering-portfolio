"""
ARM-450 — quick-change end effectors.

Three parts:
  tool_adapter   stays bolted to the J6 face; the arm side of the coupling
  tool_gripper   parallel-jaw gripper, SG90 driven
  tool_dock      docking probe -- latches using J6 itself, no 7th actuator

THE COUPLING is a three-lug bayonet. Push on, twist 30 deg, nip one thumbscrew.
Off in about five seconds with no tools. That was the requirement -- "easy to
install and remove" -- and it is the reason the interface is a bayonet rather
than the obvious four bolts.

WHY NOT MORE BOLTS: the J6 face already has only THREE bolt holes, because the
servo pocket eats the fourth quadrant. Asking the user to start three M3s
blind, up under a wrist, every time the tool changes is the wrong answer to a
tool-change problem.

MASS BUDGET. The arm is 1365 g against a 1450 g HARD ceiling -- 85 g spare, and
an end effector will not fit in that. It does not have to: every load analysis
in this project assumed a **300 g payload at the TCP**, and a tool is payload,
not arm. Both tools below are sized against the 300 g allowance, and both come
in far under it. Only one is fitted at a time.
"""
import math
import os
import sys
import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *      # noqa: F403,F401

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")
os.makedirs(OUT, exist_ok=True)

# --- the J6 face we must mate to (measured off wrist_j6_output.step) --------
J6_BCD = 30.0
J6_BOLT_ANG = (160.0, 250.0, 340.0)
J6_PILOT = 10.0
J6_FACE_D = 52.0

# --- bayonet coupling ------------------------------------------------------
BAY_D = 26.0            # spigot outside diameter
BAY_LUG_H = 3.0         # lug thickness
BAY_LUG_ARC = 42.0      # degrees of arc per lug
BAY_LUG_OUT = 3.2       # how far a lug stands proud
BAY_N = 3
BAY_TWIST = 30.0        # degrees from insert to locked
BAY_CLR = 0.30          # per-side running clearance, printed
PLATE_T = 5.0
LOCK_SCREW = 3.4        # M3 thumbscrew through the collar


def _lugs(r_in, r_out, h, z, twist=0.0, clr=0.0):
    """BAY_N lugs as an angular sweep — the male half of the bayonet."""
    s = None
    for k in range(BAY_N):
        a0 = 360.0 * k / BAY_N + twist - (BAY_LUG_ARC + clr) / 2.0
        w = (cq.Workplane("XY").workplane(offset=z)
             .moveTo(0, 0)
             .lineTo(r_out * math.cos(math.radians(a0)),
                     r_out * math.sin(math.radians(a0)))
             .radiusArc((r_out * math.cos(math.radians(a0 + BAY_LUG_ARC + clr)),
                         r_out * math.sin(math.radians(a0 + BAY_LUG_ARC + clr))),
                        -r_out)
             .close().extrude(h))
        w = w.cut(cq.Workplane("XY").workplane(offset=z - 1)
                  .circle(r_in).extrude(h + 2))
        s = w if s is None else s.union(w)
    return s


def tool_adapter():
    """Arm side. Bolts to J6 once and stays there; tools bayonet onto it."""
    a = cq.Workplane("XY").circle(J6_FACE_D / 2 - 2.0).extrude(PLATE_T)
    # pilot spigot down into the J6 Ø10 bore -- this is what centres the tool
    a = a.union(cq.Workplane("XY").workplane(offset=-6.0)
                .circle(J6_PILOT / 2 - 0.15).extrude(6.0))
    # the three J6 bolts, counterbored so the heads sit flush and a tool can
    # pass over them
    for ang in J6_BOLT_ANG:
        x = J6_BCD / 2 * math.cos(math.radians(ang))
        y = J6_BCD / 2 * math.sin(math.radians(ang))
        a = a.cut(cq.Workplane("XY").workplane(offset=-1)
                  .center(x, y).circle(M3_CLEAR / 2).extrude(PLATE_T + 2))
        a = a.cut(cq.Workplane("XY").workplane(offset=2.6)
                  .center(x, y).circle(6.2 / 2).extrude(PLATE_T))
    # male bayonet spigot with three lugs
    a = a.union(cq.Workplane("XY").workplane(offset=PLATE_T)
                .circle(BAY_D / 2).circle(6.0).extrude(BAY_LUG_H + 4.0))
    a = a.union(_lugs(BAY_D / 2 - 0.01, BAY_D / 2 + BAY_LUG_OUT,
                      BAY_LUG_H, PLATE_T + 4.0))
    a = a.edges("|Z").fillet(0.6)
    return a


def _tool_socket(body, z_face):
    """Female half of the bayonet, cut into any tool body."""
    # bore for the spigot
    body = body.cut(cq.Workplane("XY").workplane(offset=z_face - 0.01)
                    .circle(BAY_D / 2 + BAY_CLR)
                    .extrude(BAY_LUG_H + 4.0 + BAY_CLR))
    # entry slots: lugs pass straight in here
    body = body.cut(_lugs(BAY_D / 2 - 1.0, BAY_D / 2 + BAY_LUG_OUT + BAY_CLR,
                          BAY_LUG_H + 4.0 + BAY_CLR, z_face - 0.01,
                          twist=0.0, clr=2 * BAY_CLR))
    # the locking groove the lugs rotate into
    body = body.cut(_lugs(BAY_D / 2 - 1.0, BAY_D / 2 + BAY_LUG_OUT + BAY_CLR,
                          BAY_LUG_H + 2 * BAY_CLR,
                          z_face + 4.0 - BAY_CLR,
                          twist=BAY_TWIST, clr=BAY_TWIST * 2 + 2 * BAY_CLR))
    # thumbscrew that stops it twisting back
    body = body.cut(cq.Workplane("XZ").workplane(offset=-30.0)
                    .center(0, z_face + 2.0).circle(LOCK_SCREW / 2)
                    .extrude(60.0))
    return body


# ---------------------------------------------------------------- GRIPPER
SG90_L, SG90_W, SG90_H = 23.0, 12.4, 22.8      # body only, excl. tabs
GRIP_STROKE = 30.0
# 2026-08-22: 16.0 -> 20.0. At 16 the half-turn stroke was 25.1 mm against a
# 30 mm design opening, and the rack pitch line sat 1.20 mm outside the pinion
# PCD so the teeth never touched. Caught by check_tool_fit.py, not by eye --
# a gear mesh is exactly the thing that looks fine in a render and does nothing
# in plastic.
PINION_PCD = 20.0
TOOTH = 2.0
JAW_T = 8.0
TOOTH_DEPTH = 2.4
RACK_OFFSET = PINION_PCD / 2 + JAW_T / 2 - TOOTH_DEPTH / 2


def tool_gripper():
    """Parallel jaws, rack and pinion, one SG90 (9 g).

    Parallel rather than scissor because the jaw faces stay square to each
    other through the stroke. A scissor grips a cylinder at two points that
    migrate as it closes, which is how small parts get squeezed out of one.
    """
    # DEPTH 34 -> 38. The rack channels sit at +/-RACK_OFFSET = 12.80 and are
    # JAW_T + 0.5 = 8.50 wide, so their outer edge is at 17.05 -- and the body
    # half-depth was 17.00. The channels broke through the outside face by
    # 0.05 mm, leaving the jaws in an OPEN slot retained only by the gear mesh,
    # which is the one direction the grip reaction pushes them. At D = 38 the
    # outer wall is 1.95 mm, above the 1.24 mm printable floor.
    W, D, H = 54.0, 38.0, 26.0
    g = (cq.Workplane("XY").box(W, D, H, centered=(True, True, False))
         .edges("|Z").fillet(3.0))
    g = _tool_socket(g, H - (BAY_LUG_H + 4.0 + BAY_CLR) - 1.0)
    g = g.cut(cq.Workplane("XY").workplane(offset=3.0)
              .center(0, -3.0).box(SG90_L + 0.4, SG90_W + 0.4, SG90_H,
                                   centered=(True, True, False)))
    for sx in (-1, 1):
        g = g.cut(cq.Workplane("XY").workplane(offset=3.0 + SG90_H - 6.0)
                  .center(sx * (SG90_L / 2 + 2.4), -3.0)
                  .box(4.8, SG90_W + 0.4, 2.6, centered=(True, True, False)))
    # Rack channels. The offset is NOT simply PCD/2 + JAW_T/2: the teeth are cut
    # TOOTH_DEPTH into the bar, so the pitch line sits that much inside the bar
    # face. Place the channel so the pitch line lands on the pinion PCD.
    for sy in (-1, 1):
        g = g.cut(cq.Workplane("XY").workplane(offset=-0.01)
                  .center(0, sy * RACK_OFFSET)
                  .box(W + 2, JAW_T + 0.5, 6.0, centered=(True, True, False)))
    return g


def gripper_jaw():
    """One jaw; print two, the second mirrored in the slicer."""
    L, H = 46.0, 34.0
    j = (cq.Workplane("XY").box(L, JAW_T, 6.0, centered=(True, True, False))
         .edges("|Z").fillet(1.2))
    # Inset the tooth pattern half a pitch from each end. Starting at
    # -L/2 + TOOTH put the first cut 1.0 mm from the bar end, leaving a 1.20 mm
    # land -- the only feature in the whole design below the 1.24 mm printable
    # floor, and a fragile end tooth. Half a pitch in leaves 2.0 mm at both
    # ends and costs one tooth out of eleven.
    n = int((L - TOOTH) / (2 * TOOTH))
    for k in range(n):
        x = -L / 2 + 1.5 * TOOTH + k * 2 * TOOTH
        # teeth on the -Y face -- the side that faces the pinion. Cutting them
        # on +Y put the toothed face on the far side of the bar, where it could
        # never engage anything.
        # 2026-08-23. The cutter was CENTRED ON THE BAR FACE at y = -JAW_T/2,
        # so only half of its TOOTH_DEPTH lay in material: the teeth came out
        # 1.20 mm deep against a 2.40 design, measured off the STL. That also
        # moved the pitch line 0.60 mm, which RACK_OFFSET assumes.
        # check_tool_fit.py's "rack meshes the pinion" passed throughout,
        # because it computed the pitch line from the PARAMETERS instead of
        # measuring the teeth -- the same failure as the bearing pockets.
        # Offset the cutter inward so the full depth is cut from the face.
        j = j.cut(cq.Workplane("XY").workplane(offset=-0.01)
                  .center(x, -JAW_T / 2 + TOOTH_DEPTH / 2)
                  .box(TOOTH, TOOTH_DEPTH, 6.02, centered=(True, True, False)))
    f = (cq.Workplane("XY").workplane(offset=-H + 6.0)
         .center(-L / 2 + 7.0, 0).box(12.0, JAW_T, H - 6.0,
                                      centered=(True, True, False)))
    j = j.union(f)
    # V-GROOVE in the gripping face, running the height of the finger.
    # A flat jaw touches a cylinder on ONE line, so the part is free to roll out
    # sideways under load -- which is the failure a parallel gripper exists to
    # prevent. A 90 deg V touches on two lines per jaw, four in total, and
    # locates a round part on its own axis whatever the diameter.
    VD = 3.0                                    # groove depth
    j = j.cut(cq.Workplane("YZ")
              .workplane(offset=-L / 2 + 7.0 + 6.0)
              .moveTo(-JAW_T / 2 - 0.1, 0).lineTo(0, -VD)
              .lineTo(JAW_T / 2 + 0.1, 0).close()
              .extrude(-(H - 6.0) - 1.0)
              .translate((0, 0, 6.0)))
    return j


def pinion():
    p = cq.Workplane("XY").circle(PINION_PCD / 2 + TOOTH / 2).extrude(5.5)
    n = int(math.pi * PINION_PCD / (2 * TOOTH))
    for k in range(n):
        a = 360.0 * k / n
        p = p.cut(cq.Workplane("XY").workplane(offset=-0.01)
                  .center((PINION_PCD / 2 + TOOTH / 2) * math.cos(math.radians(a)),
                          (PINION_PCD / 2 + TOOTH / 2) * math.sin(math.radians(a)))
                  .circle(TOOTH * 0.55).extrude(5.52))
    p = p.cut(cq.Workplane("XY").workplane(offset=-0.01).circle(2.5).extrude(5.52))
    for k in range(4):
        a = 90.0 * k
        p = p.cut(cq.Workplane("XY").workplane(offset=2.0)
                  .center(7.0 * math.cos(math.radians(a)),
                          7.0 * math.sin(math.radians(a)))
                  .circle(0.95).extrude(4.0))
    return p


# ---------------------------------------------------------------- DOCKING
# 2026-08-22, THROAT 12 -> 16 and MOUTH 30 -> 34.
# At a 12 mm throat the target spigot had a 1.65 mm wall (outer 5.65, fluid
# bore 4.00) and the capture groove was cut 3.30 mm deep into it -- straight
# through. That severed the spigot tip from the base: dock_target came out as
# FOUR bodies, three of them loose 49 mm3 fragments. Widening the throat gives
# the spigot a 2.45 mm wall at the groove root, and the mouth goes up with it
# so the +/-9.00 mm capture tolerance is unchanged.
DOCK_MOUTH = 34.0        # capture cone mouth
DOCK_THROAT = 16.0       # bore the target spigot slides into
# CONE DEPTH 16 -> 9. A capture cone is a lead-in, and a lead-in that is deeper
# than the post it guides is a trap: the cone mouth grounded on the target's
# Ø34 flange 9.8 mm BEFORE the spigot could reach the latch, so probe and
# target fouled at every insertion depth and every roll angle. Either the post
# out-reaches the cone or the cone gets shallower; shallower is cheaper in
# plastic, in mass and in target height, and 45 deg still deflects a spigot in.
DOCK_CONE_L = 9.0
DOCK_LUG_N = 3
DOCK_LUG_ARC = 40.0
DOCK_TWIST = 30.0
FLUID_BORE = 8.0         # central pass-through for the refuelling line

# ---- the mate, defined once, in the PROBE's frame (throat entry = z 0) -----
# Everything downstream is derived from these four numbers, so the probe
# geometry, the target geometry and check_tool_fit.py cannot drift apart.
LATCH_Z0, LATCH_Z1 = 3.0, 5.4         # the probe's inward latch lugs
CONE_STANDOFF = 2.0                   # cone mouth to target flange when latched
LATCH_CLR = 0.5                       # groove overruns the lug at each end
TIP_ABOVE_GROOVE = 4.1                # spigot material above the groove

SEAT_DZ = -(DOCK_CONE_L + CONE_STANDOFF)          # -11.0  spigot base, seated
SPG_CLR = 0.35                        # spigot-to-throat running clearance
SPG_R = DOCK_THROAT / 2 - SPG_CLR     # 7.65  spigot outer radius
GRV_DEPTH = 1.20                      # capture groove, cut into the OUTER face
GRV_R = SPG_R - GRV_DEPTH             # 6.45  groove root
GRV_Z0 = LATCH_Z0 - SEAT_DZ - LATCH_CLR           # 13.5, from the spigot base
GRV_Z1 = LATCH_Z1 - SEAT_DZ + LATCH_CLR           # 16.9
SPG_H = GRV_Z1 + TIP_ABOVE_GROOVE                 # 21.0  spigot height
FLANGE_H = 10.0                       # target bolt-down flange
THROAT_DEPTH = 12.0                   # cylindrical bore above the cone
assert SEAT_DZ + SPG_H <= THROAT_DEPTH, "spigot tip bottoms out in the throat"


def tool_dock():
    """docking probe.

    NO SEVENTH ACTUATOR. The latch is a bayonet and J6 -- the tool roll axis --
    turns it. Insert the probe, roll J6 by 30 deg, the lugs are captured.
    Reverse to undock. J6 has +/-175 deg of travel and does nothing during a
    docking approach, so the motion is free.

    CAPTURE TOLERANCE is the number that matters. The cone mouth is 34 mm over
    a 16 mm throat, so it self-centres anything arriving within +/-9 mm of the
    axis. Measured end-to-end arm precision is expected around 1.4 mm once
    servo backlash is included -- so the cone carries roughly 6x the error the
    arm can actually make. That margin is deliberate: docking is the one task
    where a miss is expensive.

    2026-08-22: the throat is now a REAL CYLINDRICAL BORE, THROAT_DEPTH deep,
    not the knife edge where the cone happened to reach its minimum. The old
    shape had nothing for the spigot to enter and nothing for a lug to stand
    on -- the three latch lugs were placed inside the cone at a height where
    the bore was already 25.8 mm across, so they floated 5.5 mm clear of the
    wall and came out of the slicer as three loose 19 mm3 crumbs. The latch,
    which is the entire reason this tool needs no actuator, did not exist.
    """
    W, H = 46.0, 22.0
    d = (cq.Workplane("XY").box(W, W, H, centered=(True, True, False))
         .edges("|Z").fillet(4.0))
    d = _tool_socket(d, H - (BAY_LUG_H + 4.0 + BAY_CLR) - 1.0)
    # capture cone, opening downward away from the arm
    d = d.union(cq.Workplane("XY").workplane(offset=-DOCK_CONE_L)
                .circle(DOCK_MOUTH / 2 + 3.0)
                .workplane(offset=DOCK_CONE_L)
                .circle(DOCK_THROAT / 2 + 4.0).loft())
    d = d.cut(cq.Workplane("XY").workplane(offset=-DOCK_CONE_L - 1)
              .circle(DOCK_MOUTH / 2)
              .workplane(offset=DOCK_CONE_L + 1)
              .circle(DOCK_THROAT / 2).loft())
    # the throat proper: a straight bore the spigot can actually climb into
    d = d.cut(cq.Workplane("XY").workplane(offset=-0.01)
              .circle(DOCK_THROAT / 2).extrude(THROAT_DEPTH + 0.01))
    # LATCH LUGS. They grow INWARD from the throat wall, and r_out reaches 1 mm
    # PAST it so the union has real material to fuse to rather than a tangent
    # touch. Radially they stop 0.10 short of the target groove root.
    d = d.union(_lugs(GRV_R + 0.10, DOCK_THROAT / 2 + 1.0,
                      LATCH_Z1 - LATCH_Z0, LATCH_Z0)
                .intersect(cq.Workplane("XY").workplane(offset=LATCH_Z0 - 0.5)
                           .circle(DOCK_THROAT / 2 + 1.0)
                           .extrude(LATCH_Z1 - LATCH_Z0 + 1.0)))
    # fluid pass-through, from the top of the throat up and out the back
    d = d.cut(cq.Workplane("XY").workplane(offset=THROAT_DEPTH - 0.01)
              .circle(FLUID_BORE / 2).extrude(H - THROAT_DEPTH + 4))
    return d


# ---------------------------------------------------------------- FLUID SEAL
# A RADIAL (piston) seal, not a face seal, and the reason is axial play.
#
# The bayonet latch has LATCH_CLR = 0.5 mm of clearance at each end of the
# capture groove, so the two halves can sit anywhere in a 1.0 mm axial band. A
# face seal's squeeze is set by exactly that gap -- it would be fully loaded at
# one end of the play and completely unloaded at the other. A radial seal's
# squeeze is set by DIAMETERS only and does not care where the spigot sits
# axially, which is the one uncertainty this joint actually has.
#
# It has to live in the only full-circumference plain band of spigot that is
# inside the straight Ø16 throat: between the throat entry and the capture
# groove, 2.5 mm of it. Above the groove the entry slots cut clean through the
# wall, so nothing can seal there.
SEAL_CORD = 1.0                       # O-ring cross-section
SEAL_SQUEEZE = 0.20                   # 20 % -- 15-30 % is the usual band
SEAL_GROOVE_D = DOCK_THROAT - 2 * SEAL_CORD * (1 - SEAL_SQUEEZE)   # Ø14.40
SEAL_GROOVE_W = SEAL_CORD * 1.30      # 1.30 wide, so the ring can roll
SEAL_Z = 12.2                         # spigot coords, mid-band
assert -SEAT_DZ + 0.4 < SEAL_Z - SEAL_GROOVE_W / 2, "seal groove starts before the throat"
assert SEAL_Z + SEAL_GROOVE_W / 2 < GRV_Z0 - 0.4, "seal groove runs into the capture groove"


def dock_target(sealed=False):
    """The passive port the probe latches into — the spacecraft side.

    Printed here so the interface can be TESTED on the bench before anything
    flies or floats. It is not part of the arm and not in its mass budget.

    2026-08-22: the capture groove is now cut GRV_DEPTH into the outer face of
    the spigot and no deeper. It used to be cut from r3.10 to r6.40 through a
    wall that ran r4.00 to r5.65 -- a 3.30 mm groove in a 1.65 mm wall, which
    is not a groove, it is a parting cut. It severed the tip, and the three
    entry slots then chopped what was left into three loose arcs. A bench test
    of the latch would have found three fragments in the bag.
    """
    D, H = 34.0, FLANGE_H
    t = cq.Workplane("XY").circle(D / 2).extrude(H)
    # Spigot, with the lead-in chamfer BUILT IN rather than cut.
    # The chamfer used to be a cone-minus-cylinder cutter, and it was inverted:
    # the cone was widest at the BOTTOM of the chamfer band, so it machined the
    # spigot away over the 2 mm below the tip and left a mushroom lip standing
    # proud at the very top -- an undercut, on the one surface whose whole job
    # is to guide a probe on. Lofting the taper directly cannot be inverted.
    CH = 1.5
    t = t.union(cq.Workplane("XY").workplane(offset=H)
                .circle(SPG_R).extrude(SPG_H - CH))
    t = t.union(cq.Workplane("XY").workplane(offset=H + SPG_H - CH)
                .circle(SPG_R)
                .workplane(offset=CH)
                .circle(SPG_R - CH).loft())
    # capture groove: the probe lugs rotate into this. Cut to GRV_R only, so
    # the 2.45 mm of wall between the root and the fluid bore keeps the tip
    # attached to the base.
    t = t.cut(cq.Workplane("XY").workplane(offset=H + GRV_Z0)
              .circle(SPG_R + 1.0).circle(GRV_R)
              .extrude(GRV_Z1 - GRV_Z0))
    # entry slots so the lugs can pass down to the groove
    t = t.cut(_lugs(GRV_R, SPG_R + 1.0,
                    SPG_H - GRV_Z1 + 0.5, H + GRV_Z1, clr=2 * BAY_CLR))
    # fluid pass-through
    t = t.cut(cq.Workplane("XY").workplane(offset=-1)
              .circle(FLUID_BORE / 2).extrude(H + SPG_H + 4))
    # bolt-down, 3 x M3
    for k in range(3):
        a = 120.0 * k + 60.0
        t = t.cut(cq.Workplane("XY").workplane(offset=-1)
                  .center(13.5 * math.cos(math.radians(a)),
                          13.5 * math.sin(math.radians(a)))
                  .circle(M3_CLEAR / 2).extrude(H + 2))
    if sealed:
        # a shallow annular groove in the plain spigot band
        t = t.cut(cq.Workplane("XY").workplane(offset=H + SEAL_Z - SEAL_GROOVE_W / 2)
                  .circle(SPG_R + 0.5).circle(SEAL_GROOVE_D / 2)
                  .extrude(SEAL_GROOVE_W))
    return t


def dock_target_sealed():
    """The same port with an O-ring groove for fluid transfer.

    Kept as a SEPARATE part rather than replacing the original. The dry
    docking demonstration does not need a seal and is one less thing to source
    and fit; the fluid demonstration does. Both are verified.
    """
    return dock_target(sealed=True)


# ---------------------------------------------------------------------------
# BUILD. Everything else in cad/ exports itself when run; this module did not,
# so `python3 cad/end_effector.py` -- the command the plan gives for rebuilding
# the tools -- printed nothing and wrote nothing. The six parts had been
# exported once, by hand, and any edit to this file was silently not in the
# STLs the drawings and the collision checks read.
PARTS = [("tool_adapter", tool_adapter),
         ("tool_gripper", tool_gripper),
         ("gripper_jaw", gripper_jaw),
         ("gripper_pinion", pinion),
         ("tool_dock", tool_dock),
         ("dock_target", dock_target),
         ("dock_target_sealed", dock_target_sealed)]


def build_all(verbose=True):
    out = {}
    for name, fn in PARTS:
        p = fn()
        sh = p.val()
        v, bb = sh.Volume(), sh.BoundingBox()
        cq.exporters.export(p, os.path.join(OUT, name + ".step"))
        cq.exporters.export(p, os.path.join(OUT, name + ".stl"),
                            tolerance=0.01, angularTolerance=0.1)
        out[name] = v
        if verbose:
            # SOLID COUNT. A cadquery union that does not actually touch still
            # "succeeds" -- it just returns a compound with two solids in it.
            # That is how the three dock latch lugs came to be modelled, drawn
            # and mass-budgeted while sitting 5.5 mm clear of anything.
            n = len(sh.Solids())
            flag = "" if n == 1 else f"   <-- {n} SOLIDS, NOT FUSED"
            print(f"  {name:16s} {bb.xlen:5.1f} x {bb.ylen:5.1f} x {bb.zlen:5.1f} mm"
                  f"   {v/1000:6.2f} cm3   {v*1.29e-3*0.55:5.1f} g{flag}")
    return out


if __name__ == "__main__":
    print("END EFFECTORS — quick-change bayonet tools")
    build_all()
    print(f"\n  wrote {len(PARTS)} × .step / .stl to {os.path.normpath(OUT)}")
