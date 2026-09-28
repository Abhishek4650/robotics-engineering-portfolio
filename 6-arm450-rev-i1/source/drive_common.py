#!/usr/bin/env python3
"""
Shared, MEASURED geometry for a servo-driven revolute joint on ARM-450.

Everything here is read from the user's own models, not typed from a spec:

  Motor.stl (ST3215), in the joint frame (output on -Z, horn axis at 0,0):
      full-case step  -> back of case            33.10
      cap  40.2 x 24.4, from the step down        1.50   <- the TRUE front plane
      step 39.4 x 14.0, cap face down to          1.10   (dz 1.55..2.60)
      horn disc O19.2, cap face down to           3.011  (horn tip)
  Motor_mount.stl (the coupler that worked on the user's previous arm):
      horn face  4 x O2.52 on BCD 14.00 (cross) + O2.52 centre

So the servo seats with its CAP FACE on the housing's parting plane P:
    horn face  = P - 3.011
    case back  = P + 34.589
"""
import numpy as np
import cadquery as cq

CAP_FACE_BELOW_STEP = 1.50
HORN_BELOW_CAP = 3.011          # horn tip below the cap face
CASE_ABOVE_CAP = 34.589         # back of case above the cap face
CLR = 0.40
BAY_T = CASE_ABOVE_CAP + CLR    # 34.99, from P to the back wall
PINCH = 24.50
BAY_L = 45.22 + 2 * CLR         # 46.02
SERVO_OFF = 12.50               # case centre is +12.50 from the horn axis

# relief in p1 for the step and horn under the cap face
RELIEF_X = (-9.90, 34.40)
RELIEF_Y = 7.30
RELIEF_D = (2.60 - CAP_FACE_BELOW_STEP) + 0.30      # 1.40 below P

# wiring: the ST3215's two bus sockets (manufacturer's STEP, matches the
# user's photo 2026-09-24): one block x 11.70..16.70 from the output axis,
# |y| <= 10.2, sunk in the back face; the plugs stay inside the case, the
# wires leave straight out at x 13.2..15.2. The cover window passes the wires
# (was 12 x 20 centred on the case: the plugs' footprint reached 0.2 past its
# edge); its -x edge stops short of the near screw pads.
WIRE_WIN_X0, WIRE_WIN_X1 = 11.0, 18.5
WIRE_WIN_X = WIRE_WIN_X1 - WIRE_WIN_X0      # along the case
WIRE_WIN_Y = 22.0                            # across the case

# SERVO FIXED BY ITS OWN BACK-FACE HOLES (user's requirement; audit M1).
# Waveshare ST3215-2D.zip (exact DXF circles), confirmed by the user's photo
# (hole ratio 1.14 ~ drawing 1.19) and measurements (37.24 / O5.95 vs 37.25 /
# O6.0): 4 holes x 8.30 / 32.75 from the output axis, y +-10.25, opening on
# the back PLATEAU 32.0 above the seat face, 3.0 deep (both servo models,
# height map). Features standing higher than the plateau all lie inside
# |y| < 9.6 (idler horn r 9.6, label block |y| 9, rear boss O5.9): the rear
# boss stands 2.589 above it (Motor.stl: back of case 34.589 -- the user's
# servo shows the boss bare, no idler horn), the idler horn 2.04. The pads keep
# |y| < KEEP_Y clear for KEEP_H, so a servo still slides along its channel
# (J1/J4/J6) or drops into its bay (forks) past them. (KEEP_H 2.35 cleared the
# idler horn but not the boss: the J6 servo's boss snagged 0.24 mm on the new
# bridge while sliding in -- caught by verify_wrist's insertion check.)
SCREW_NEAR = ((8.30, 10.25), (8.30, -10.25))
SCREW_FAR = ((32.75, 10.25), (32.75, -10.25))
PLATEAU = 32.0                  # back plateau above the seat (cap) face
SSCR_L = 8.0                    # self-tapping screws from the servo box (user: ~8 mm)
SSCR_HEAD = BAY_T + 2.4         # 37.389: head seat above the seat face = a fork cover's outer face
SSCR_ENG = PLATEAU + SSCR_L - SSCR_HEAD      # 2.611 into the servo: its holes are 3.0 deep
SSCR_CLR_D = 3.4                # clearance: any self-tapper up to 2.9 mm
SSCR_CB_D = 5.6                 # head counterbore (pan head up to O5.2)
PAD_D = 7.6                     # pad round a clearance hole
POST_D = 8.0                    # post round a head counterbore
KEEP_Y, KEEP_H = 9.9, 2.9

# PLUG SLOT (user, 2026-09-24: "give slots to insert the pin in servos"): a bus
# plug must come straight out of its socket and past the back plateau with the
# arm assembled. Its passage -- both plugs' footprint (x 11.7..16.7, y -9.8..
# 10.2) + 0.3 slop + margin -- is kept free of every pad and post, from the
# plateau outward; the fork covers' wire window is the same passage.
PLUG_PASS_X = (11.0, 17.3)
PLUG_PASS_Y = 10.7


def plug_passage(z_seat, sign, h=40.0):
    lo, hi = _span(z_seat, sign, PLATEAU - 1.0, PLATEAU + h)
    return (cq.Workplane("XY").center((PLUG_PASS_X[0] + PLUG_PASS_X[1]) / 2, 0)
            .rect(PLUG_PASS_X[1] - PLUG_PASS_X[0], 2 * PLUG_PASS_Y).extrude(hi - lo).translate((0, 0, lo)))


def _span(z_seat, sign, h0, h1):
    a, b = z_seat + sign * h0, z_seat + sign * h1
    return min(a, b), max(a, b)


def screw_pads(z_seat, sign, pts, h_to, d=PAD_D, keep_to=None):
    """Pads (part frame, output axis = z at x = y = 0) from the servo's back
    plateau out to h_to above the seat face."""
    lo, hi = _span(z_seat, sign, PLATEAU, h_to)
    s = None
    for (x, y) in pts:
        c = cq.Workplane("XY").center(x, y).circle(d / 2).extrude(hi - lo).translate((0, 0, lo))
        s = c if s is None else s.union(c)
    lo, hi = _span(z_seat, sign, PLATEAU - 6.0, keep_to if keep_to is not None else PLATEAU + KEEP_H)
    keep = cq.Workplane("XY").center(12.5, 0).rect(80.0, 2 * KEEP_Y).extrude(hi - lo).translate((0, 0, lo))
    return s.cut(keep).cut(idler_clearance(z_seat, sign)).cut(plug_passage(z_seat, sign))


# Fork-floor bolt heads that face a turning link are sunk into the floor
# (verify_head_clearance: the J3 fork's 4 heads came within 1.28 mm of the
# swinging forearm at +-72 deg and would touch at 81 deg).
FLOOR_CB_D, FLOOR_CB_T = 6.2, 3.2


def floor_head_counterbores(pts_world, z_floor_world, z_axis_world):
    """Counterbores (in a fork's local frame: world = FORK_R @ local + (0, 0,
    z_axis_world), i.e. local x = world z, local y = world x, local z = world y)
    for bolt heads standing on a fork floor whose top is at z_floor_world."""
    x0 = z_floor_world - FLOOR_CB_T - z_axis_world
    s = None
    for (xw, yw) in pts_world:
        c = cq.Workplane("YZ").center(xw, yw).circle(FLOOR_CB_D / 2).extrude(FLOOR_CB_T + 6.0).translate((x0, 0, 0))
        s = c if s is None else s.union(c)
    return s


def screw_holes(s, z_seat, sign, pts, h_out, counterbore=False):
    """Clearance holes from inside the servo's hole out to h_out; with a
    counterbore, the head seat is at SSCR_HEAD and the counterbore runs on
    out to h_out (screws driven from outside)."""
    for (x, y) in pts:
        lo, hi = _span(z_seat, sign, PLATEAU - 1.0, SSCR_HEAD if counterbore else h_out)
        s = s.cut(cq.Workplane("XY").center(x, y).circle(SSCR_CLR_D / 2).extrude(hi - lo).translate((0, 0, lo)))
        if counterbore:
            lo, hi = _span(z_seat, sign, SSCR_HEAD, h_out)
            s = s.cut(cq.Workplane("XY").center(x, y).circle(SSCR_CB_D / 2).extrude(hi - lo).translate((0, 0, lo)))
    return s

# printed drive shaft (user's choice: printed tube with the drive built in)
SHAFT_OD = 29.95                # bearing ID 30.00, slip
SHAFT_BORE = 22.0               # lets a driver reach the horn screws
SHAFT_END_T = 3.5               # end wall that bolts to the horn
HORN_BCD = 14.00
HORN_HOLE_D = 2.52              # as on the proven Motor_mount.stl (M2.5)
FLAT_Y = -14.20                 # the clamp-grub D-flat, as on the alu tube
BORE_CLR_D = 31.0               # shaft clearance through the housing floor
RACE_RECESS_D = 38.0            # 6806: floor touches the OUTER race only
RACE_RECESS_D_6706 = 34.0       # 6706 (OD 37): a Ø38 recess would be WIDER than
                                # the bearing and remove the lip over its outer race
RACE_RECESS_T = 0.60


def p1_floor_cuts(s, z_brg_outer, P, recess_d=RACE_RECESS_D):
    """Cuts applied to p1's floor between the drive bearing and P."""
    s = s.cut(cq.Workplane("XY").circle(recess_d / 2)
              .extrude(RACE_RECESS_T + 0.01).translate((0, 0, z_brg_outer - 0.01)))
    s = s.cut(cq.Workplane("XY").circle(BORE_CLR_D / 2)
              .extrude(P - z_brg_outer + 1.0).translate((0, 0, z_brg_outer)))
    x0, x1 = RELIEF_X
    s = s.cut(cq.Workplane("XY").center((x0 + x1) / 2, 0)
              .rect(x1 - x0, 2 * RELIEF_Y)
              .extrude(RELIEF_D + 1.0).translate((0, 0, P - RELIEF_D)))
    return s


# The ST3215 carries a O19.2 IDLER horn on its back, coaxial with the output
# and turning with it (Waveshare ST3215-3D.zip, part 'metal horn (driven)';
# the user's Motor.stl is the same case without it). Its face stands 34.04 mm
# from the seat (cap) face. Every housing behind a servo keeps this clear.
IDLER_R, IDLER_FACE = 19.2 / 2, 34.04
IDLER_CLR = 0.6


def idler_clearance(z_seat, sign):
    """Cylinder to CUT from a housing: around the output axis (x = y = 0),
    from the case back (30.29 from the seat) to past the idler face.
    sign = +1 if the servo back points to +z from the seat, -1 if to -z."""
    z0, z1 = z_seat + sign * 30.29, z_seat + sign * (IDLER_FACE + IDLER_CLR)
    lo, hi = min(z0, z1), max(z0, z1)
    return cq.Workplane("XY").circle(IDLER_R + IDLER_CLR).extrude(hi - lo).translate((0, 0, lo))


def bay_shell(s, P, z_drive, back_t):
    """A 2.4 mm shell round the whole servo bay of a fork p2 (the fork outline
    left the pinch walls 0.06-0.5 mm thick at the far end of the bay: audit,
    thin-wall rays), then the bay, wiring window, cable exit and split-bolt
    clearances cut again."""
    x0, x1 = SERVO_OFF - BAY_L / 2, SERVO_OFF + BAY_L / 2
    w, hy = 2.4, PINCH / 2
    s = s.union(cq.Workplane("XY").center((x0 + x1) / 2, 0).rect(x1 - x0 + 2 * w, 2 * (hy + w))
                .extrude(z_drive - P).translate((0, 0, P)))
    s = s.cut(cq.Workplane("XY").center((x0 + x1) / 2, 0).rect(x1 - x0, 2 * hy)
              .extrude(BAY_T + 1.0).translate((0, 0, P - 1.0)))
    s = s.cut(cq.Workplane("XY").center(x1 - 6.0, 0).circle(8.0 / 2)
              .extrude(back_t + 2).translate((0, 0, z_drive - back_t - 1)))
    for (x, y) in SPLIT_BOLTS:
        s = s.cut(cq.Workplane("XY").center(x, y).circle(M3_CLEAR_D / 2)
                  .extrude(z_drive - P + 2).translate((0, 0, P - 1)))
    s = p2_servo_screws(s, P, z_drive, back_t)
    return p2_wire_window(s, z_drive, back_t)


def p2_wire_window(s, z_drive, back_t):
    return s.cut(cq.Workplane("XY").center((WIRE_WIN_X0 + WIRE_WIN_X1) / 2, 0)
                 .rect(WIRE_WIN_X, WIRE_WIN_Y)
                 .extrude(back_t + 2.0).translate((0, 0, z_drive - back_t - 1.0)))


def p2_servo_screws(s, P, z_drive, back_t):
    """Fork cover (servo back toward +z from the seat P): 4 pads from the
    back plateau to the cover's inner face, 4 clearance holes through; the
    head sits on the cover's outer face, which IS the head seat (checked)."""
    assert abs((z_drive - P) - SSCR_HEAD) < 1e-6, "cover outer face %.4f != head seat %.4f" % (z_drive - P, SSCR_HEAD)
    pts = SCREW_NEAR + SCREW_FAR
    # (inside |y| < KEEP_Y the pads would be a 0.09 mm sliver under the cover
    # wall: they stop at |y| = KEEP_Y all the way up)
    s = s.union(screw_pads(P, +1, pts, z_drive - P - back_t + 0.5, keep_to=z_drive - P - back_t + 0.5))
    return screw_holes(s, P, +1, pts, z_drive - P + 1.0)


def shaft(z_idle_end, z_horn, flat_half, flat_ang=-90.0, double=False, flat_to_idle_end=False):
    """Printed joint shaft, joint axis = Z. Idle end open, drive end closed
    by a wall that bolts to the horn face at z_horn."""
    L = z_horn - z_idle_end
    s = (cq.Workplane("XY").circle(SHAFT_OD / 2).extrude(L)
         .translate((0, 0, z_idle_end)))
    s = s.cut(cq.Workplane("XY").circle(SHAFT_BORE / 2)
              .extrude(L - SHAFT_END_T).translate((0, 0, z_idle_end)))
    # horn bolts: cross pattern + centre, through the end wall
    pts = [(HORN_BCD / 2 * np.cos(np.radians(a)), HORN_BCD / 2 * np.sin(np.radians(a)))
           for a in (0, 90, 180, 270)] + [(0.0, 0.0)]
    for (x, y) in pts:
        s = s.cut(cq.Workplane("XY").center(x, y).circle(HORN_HOLE_D / 2)
                  .extrude(SHAFT_END_T + 2).translate((0, 0, z_horn - SHAFT_END_T - 1)))
    # D-flat for the clamp grubs, only between the bearings
    # flat_ang = direction of the flat's outward normal (deg about Z); it must
    # face one of the clamp grubs at the link's assembled angle
    # flat_to_idle_end: the flat runs out of the idle end, so that end can
    # pass through a D-bore (J5: the blade) on the way in and out
    z_lo = (z_idle_end - 1.0) if flat_to_idle_end else -flat_half
    for ang in ((flat_ang, flat_ang + 180.0) if double else (flat_ang,)):
        s = s.cut(cq.Workplane("XY").center(0, FLAT_Y - 5.0).rect(40, 10)
                  .extrude(flat_half - z_lo).translate((0, 0, z_lo))
                  .rotate((0, 0, 0), (0, 0, 1), ang + 90.0))
    # 0.5 x 45 lead-in at both ends so the bearings start square
    s = s.faces("<Z or >Z").edges("not %LINE").edges(
        cq.selectors.RadiusNthSelector(-1)).chamfer(0.5)
    return s


def open_drive_pocket(s, z_in, seat_t, brg_od, fit=0.02, chamfer=0.5):
    """Make the DRIVE bearing installable.

    fork_pro puts a seat shoulder on the blade side of the drive bearing AND a
    floor on its outer side, both inside p1: the bearing is trapped and can
    never be fitted (its own docstring puts the split at the bearing's outer
    face; the code adds FLOOR_T and splits 4 mm higher). Remove the blade-side
    shoulder so the bearing presses in from the fork gap, which is open on the
    swing side. It is held by its press fit and by the floor lip, which bears
    on the outer race only. Lead-in chamfer on the gap side.
    """
    d = brg_od + fit
    s = s.cut(cq.Workplane("XY").circle(d / 2).extrude(seat_t + 1.0)
              .translate((0, 0, z_in - 1.0)))
    s = s.cut(cq.Workplane("XY").circle(d / 2 + chamfer).workplane(offset=chamfer)
              .circle(d / 2).loft(combine=True).translate((0, 0, z_in - 0.001)))
    return s


# ---------------------------------------------------------------------------
# Split bolts between fork p1 and p2. fork_pro put them at r = 20, where the
# heat-set inserts broke into the drive-bearing pocket (the bearing band) and
# two of the four ran THROUGH the servo bay -- its docstring says "clear of the
# bay and the bore"; neither was true. These sit at r 25-30 from the axis,
# outside every bearing, and clear of the bay (|y| >= 12.5), with a solid boss
# through the lightened cheek so the insert and the shank have material.
# ---------------------------------------------------------------------------
SPLIT_BOLTS = [(-20.0, 16.0), (-20.0, -16.0), (26.0, 16.0), (26.0, -16.0)]
SPLIT_BOSS_D = 7.0
M3_INSERT_D, M3_INSERT_L, M3_CLEAR_D = 4.1, 7.5, 3.4
# The bolt is a STANDARD M3 x 45 (the old zd - P + 6 = 43.4 was not a length
# anyone sells). Head on p2's back face, P + 37.39 -> tip at P - 7.61, so the
# pocket goes 8.1 deep: tip 0.49 clear of the floor, the 5.7 insert fully
# engaged.
SPLIT_BOLT_L = 45.0
SPLIT_POCKET = 8.1


def split_bolts(s, P, z_lo, z_hi, part):
    """part = 'p1' (bosses z_lo..P, inserts down from P) or
    'p2' (bosses P..z_hi, clearance holes all the way through)."""
    for (x, y) in SPLIT_BOLTS:
        if part == "p1":
            s = s.union(cq.Workplane("XY").center(x, y).circle(SPLIT_BOSS_D / 2)
                        .extrude(P - z_lo).translate((0, 0, z_lo)))
            s = s.cut(cq.Workplane("XY").center(x, y).circle(M3_INSERT_D / 2)
                      .extrude(SPLIT_POCKET + 0.5).translate((0, 0, P - SPLIT_POCKET)))
        else:
            s = s.union(cq.Workplane("XY").center(x, y).circle(SPLIT_BOSS_D / 2)
                        .extrude(z_hi - P).translate((0, 0, P)))
            if x < 0:
                # p2's cheek is a lightened shell here: tie the boss to the bay
                # end-wall corner, outside the bay (|y| >= 14), or it floats
                # as a separate solid (it did: J3_p2 / J5_p2 came out as 3).
                x1 = -SERVO_OFF + 1.0          # into the bay end wall
                s = s.union(cq.Workplane("XY").center((x + x1) / 2, y)
                            .rect(x1 - x, 4.0).extrude(z_hi - P).translate((0, 0, P)))
            s = s.cut(cq.Workplane("XY").center(x, y).circle(M3_CLEAR_D / 2)
                      .extrude(z_hi - P + 2).translate((0, 0, P - 1)))
    return s
