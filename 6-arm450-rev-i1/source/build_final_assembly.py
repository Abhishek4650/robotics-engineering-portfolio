#!/usr/bin/env python3
"""
ARM-450 rev I -- FINAL ASSEMBLY (Rule 3 item 13 / user item 17).

Every printed part at its true placement, plus the bought hardware as named
solids at their true positions: 6 x ST3215 (envelope built from the measured
profile of the user's Motor.stl), 10 bearings, every horn screw, bolt,
heat-set insert, nut, spring pin and spring. Writes a STEP assembly and a
fastener bill of materials derived from what was placed.
"""
import os
import sys
from collections import Counter

import numpy as np
import cadquery as cq
from OCP.gp import gp_Trsf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_common as DC        # noqa: E402
import gen_drive_j2 as G2        # noqa: E402  (must precede turret_pro)
import gen_drive_j1 as G1        # noqa: E402
import gen_drive_j3 as G3        # noqa: E402
import gen_drive_j4 as G4        # noqa: E402
import gen_wrist as W            # noqa: E402
import gen_base_collar as GB     # noqa: E402
import spring_parts as SP        # noqa: E402
import asm_xforms as AX          # noqa: E402
import turret_pro as TP          # noqa: E402

FORK_R = np.array([[0., 1., 0.], [0., 0., 1.], [1., 0., 0.]])


def M(R=np.eye(3), t=(0, 0, 0)):
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t; return T


def rot(axis, deg, pt=(0, 0, 0)):
    import trimesh
    return trimesh.transformations.rotation_matrix(np.radians(deg), axis, pt)


J3W = M(FORK_R, (0, 0, 209.0))
J5W = M(FORK_R, (0, 0, W.Z_J5_WORLD))
TURW = M(t=(0, 0, 50.0))
J2J = rot([1, 0, 0], 90); J2J[2, 3] = 40.0            # J2 joint frame -> turret frame
ABC = rot([1, 1, 1], 120)                              # J6 abc -> J5 local


def loc(T):
    tr = gp_Trsf(); tr.SetValues(*[float(T[i, j]) for i in range(3) for j in range(4)])
    return cq.Location(tr)


# ---------------- hardware solids (local frame: axis +Z) ------------------
def servo():
    """ST3215 envelope in the joint frame: horn on -Z at (0,0), cap face at z=0,
    case along +X (centre +12.5), measured from Motor.stl."""
    case = cq.Workplane("XY").center(12.5, 0).rect(45.22, 24.72).extrude(DC.CASE_ABOVE_CAP - 1.5 - 3.9).translate((0, 0, 1.5))
    # connector cover: from the full case's end (tip - 3.905) to tip - 0.8 (Motor.stl)
    back = cq.Workplane("XY").center(13.2, 0).rect(32.4, 17.9).extrude(3.1).translate((0, 0, DC.CASE_ABOVE_CAP - 3.9))
    cap = cq.Workplane("XY").center(14.8, 0).rect(40.2, 24.4).extrude(1.5)
    step = cq.Workplane("XY").center(14.4, 0).rect(39.4, 14.0).extrude(-1.1)
    # horn: a 2.50 disc, then 2.0 mm of clearance to the case (Motor.stl, probed
    # along the axis at r 7 and r 9) -- a solid horn to the cap face made every
    # hub screw tip read as a clash
    horn = (cq.Workplane("XY").circle(9.6).extrude(-2.5).translate((0, 0, -DC.HORN_BELOW_CAP + 2.5))
            .union(cq.Workplane("XY").circle(3.0).circle(2.0).extrude(-(1.69 + DC.HORN_BELOW_CAP - 2.5))
                   .translate((0, 0, 1.69))))          # spline hub, horn back -> case
    boss = cq.Workplane("XY").circle(2.95).extrude(0.8).translate((0, 0, DC.CASE_ABOVE_CAP - 0.8))
    # back PLATEAU 32.0 above the seat face, x 6.5..34.6, |y| <= 12.0, with
    # the socket slot (x 11.7..16.7, |y| <= 9.8) sunk in it and the 4 back
    # mounting holes, O2.0 x 3.0 deep, O2.5 at the surface (height maps of
    # Motor.stl AND the manufacturer's STEP agree; Waveshare DXF; user's
    # calipers). Earlier envelope stopped at 30.69 there.
    plateau = (cq.Workplane("XY").center(20.55, 0).rect(28.1, 24.0)
               .extrude(DC.PLATEAU - (DC.CASE_ABOVE_CAP - 3.9)).translate((0, 0, DC.CASE_ABOVE_CAP - 3.9)))
    plateau = plateau.cut(cq.Workplane("XY").center(14.2, 0).rect(5.0, 19.6).extrude(5.0)
                          .translate((0, 0, DC.CASE_ABOVE_CAP - 3.9 + 0.01)))
    s = case.union(back).union(cap).union(step).union(plateau)
    for (x, y) in DC.SCREW_NEAR + DC.SCREW_FAR:
        s = s.cut(cq.Workplane("XY").center(x, y).circle(1.0).extrude(3.01).translate((0, 0, DC.PLATEAU - 3.0)))
        s = s.cut(cq.Workplane("XY").center(x, y).circle(1.25).extrude(0.31).translate((0, 0, DC.PLATEAU - 0.3)))
    s = s.cut(cq.Workplane("XY").circle(9.8).extrude(1.49 + 1.2).translate((0, 0, -1.2)))
    s = s.union(horn).union(boss)
    for a in (0, 90, 180, 270):
        s = s.cut(cq.Workplane("XY").center(7 * np.cos(np.radians(a)), 7 * np.sin(np.radians(a)))
                  .circle(1.25).extrude(2.9).translate((0, 0, -DC.HORN_BELOW_CAP - 0.01)))
    return s


def bearing(od, w, idd=30.0):
    return cq.Workplane("XY").circle(od / 2).circle(idd / 2).extrude(w)


def screw(d, L, head_d, head_h):
    """Head on top of z=0, shank down to -L."""
    return (cq.Workplane("XY").circle(d / 2).extrude(-L)
            .union(cq.Workplane("XY").circle(head_d / 2).extrude(head_h)))


def insert(d=4.1, L=5.7, thread=3.0):
    return cq.Workplane("XY").circle(d / 2).circle(thread / 2).extrude(-L)


def nut_m3():
    """M3 nyloc nut, 5.5 AF x 4.0 (locks against vibration)."""
    return cq.Workplane("XY").polygon(6, 6.35).circle(1.5).extrude(4.0)


def spring(a, b, d=8.0, wire=0.9, pin_d=3.0):
    """Extension spring between two pin axes a, b (both pins along world Y).
    Each end is a hook loop round the pin shank (inner O pin_d + 0.1), a
    short leg, then the coil body -- the body never reaches the pin."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = np.linalg.norm(b - a)
    r_in = pin_d / 2           # the hook bears on the pin under the spring's tension
    r_out = r_in + wire
    e = r_out + 1.5                              # hook + leg before the body
    s = cq.Workplane("XY").circle(d / 2).circle(d / 2 - wire).extrude(L - 2 * e).translate((0, 0, e))
    for zc, sgn in ((0.0, 1), (L, -1)):
        s = s.union(cq.Workplane("XY").circle(wire / 2).extrude(sgn * (e - r_out + 0.2))
                    .translate((0, 0, zc + sgn * (r_out - 0.2))))
        # loop in the plane that contains the spring axis, pin along its normal
        s = s.union(cq.Workplane("XZ").center(0, zc).circle(r_out).circle(r_in)
                    .extrude(wire / 2, both=True))
    z = (b - a) / L
    x = np.cross(z, [0, 0, 1]); x = x / np.linalg.norm(x) if np.linalg.norm(x) > 1e-6 else np.array([1., 0, 0])
    y = np.cross(z, x)
    T = np.eye(4); T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, y, z, a
    return s, T


def axis_frame(p, d):
    """4x4 placing local +Z along direction d at point p."""
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    x = np.cross(d, [0, 0, 1]) if abs(d[2]) < 0.99 else np.cross(d, [0, 1, 0])
    x /= np.linalg.norm(x); y = np.cross(d, x)
    T = np.eye(4); T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, y, d, p
    return T


LABELS = {}          # component name -> its bought-hardware label (filled by build())


def build():
    A = cq.Assembly(name="ARM450_rev_I")
    BOM = Counter()
    X = AX.xforms()
    C = {"print": cq.Color(0.75, 0.2, 0.15), "drive": cq.Color(0.15, 0.4, 0.75),
         "servo": cq.Color(0.1, 0.1, 0.1), "steel": cq.Color(0.65, 0.65, 0.7),
         "brass": cq.Color(0.8, 0.6, 0.2), "spring": cq.Color(0.85, 0.85, 0.9)}

    def part(name, fname, T=np.eye(4), color="print", folder=HERE):
        s = cq.importers.importStep(os.path.join(folder, fname + ".step"))
        A.add(s, name=name, loc=loc(T), color=C[color])

    def hw(name, shape, T, color, bom):
        A.add(shape, name=name, loc=loc(T), color=C[color]); BOM[bom] += 1; LABELS[name] = bom

    # ---- printed parts -------------------------------------------------
    rel = os.path.join(HERE, "..", "out_cad")
    part("base", "base")
    part("spigot_collar", "spigot_collar", color="drive")
    part("j1_mount", "j1_mount"); part("j1_hub", "j1_hub", color="drive")
    for nm in ("J2_turret_p1", "J2_turret_p2"):
        part(nm, nm, TURW, "drive")
    part("J2_shaft", "J2_shaft", TURW, "drive")
    part("link_upper_groove", "link_upper_groove", X["link_upper_groove"], "drive", rel)
    part("link_upper_tongue", "link_upper_tongue", X["link_upper_tongue"], "drive")   # rev I: flush heads
    # rev-I C-clamp (straddles the link's seam ear), seated in its link's frame
    for k, lk in (("shaft_clamp_1", "link_upper_groove"), ("shaft_clamp_2", "link_upper_tongue"),
                  ("shaft_clamp_3", "link_fore_groove"), ("shaft_clamp_4", "link_fore_tongue")):
        part(k, "shaft_clamp", X[lk], "drive")
    for nm in ("J3_p1", "J3_p2", "J3_shaft"):
        part(nm, nm, J3W)
    for k in ("link_fore_tongue", "link_fore_groove"):
        part(k, k, X[k], "drive")
    for nm in ("j4_base", "j4_cap", "j4_hub"):
        part(nm, nm)
    for nm in ("J5_p1", "J5_p2", "J5_shaft", "j6_body", "j6_cap", "j6_flange"):
        part(nm, nm, J5W, "drive" if nm.startswith("j6") else "print")
    part("J5_spacer_A", "J5_spacer", J5W)
    part("J5_spacer_B", "J5_spacer", J5W @ M(t=(0, 0, -(2 * W.BLADE_HALF + W.SPACER_T))))
    for nm, sy, zc in (("collar_upper_+y", 1, SP.J2_AXIS_Z + SP.B2), ("collar_upper_-y", -1, SP.J2_AXIS_Z + SP.B2),
                       ("collar_fore_+y", 1, SP.J3_AXIS_Z + SP.B3), ("collar_fore_-y", -1, SP.J3_AXIS_Z + SP.B3)):
        A.add(SP.collar_half(sy, zc), name=nm, color=C["print"])

    # ---- servos (joint frame: horn -Z, cap face at z=0) -----------------
    sv = servo()
    flipZ = rot([1, 0, 0], 180)
    SERVOS = {
        "servo_J1": M(t=(0, 0, G1.Z_CAP)) @ flipZ,
        "servo_J2": TURW @ J2J @ M(t=(0, 0, TP.Z_BAY)),
        "servo_J3": J3W @ M(t=(0, 0, G3.P)),
        "servo_J4": M(t=(0, 0, G4.Z_CAP)) @ flipZ,
        "servo_J5": J5W @ M(t=(0, 0, W.P5)),
        "servo_J6": J5W @ ABC @ M(t=(0, 0, W.X6_CAP)) @ flipZ,
    }
    for nm, T in SERVOS.items():
        hw(nm, sv, T, "servo", "ST3215 servo")
    # servo screws (audit M1): the self-tapping screws from the servo box,
    # ~ST2.2 x 8 pan head, into the back holes; head seat SSCR_HEAD above
    # the seat face, 2.6 mm into the servo. J4 / J6: far pair only.
    sscr = screw(2.2, DC.SSCR_L, 4.2, 1.6)
    for nm, T in SERVOS.items():
        k = nm[-1]
        pts = DC.SCREW_FAR if k in "46" else DC.SCREW_NEAR + DC.SCREW_FAR
        for i, (x, y) in enumerate(pts):
            hw("servo_scr_J%s_%d" % (k, i), sscr, T @ M(t=(x, y, DC.SSCR_HEAD)), "steel",
               "self-tapping screw ~2.2 x 8 pan head (from the servo box)")

    # ---- bearings -------------------------------------------------------
    b68, b67 = bearing(42.0, 7.0), bearing(37.0, 4.0)
    for z in (3.0, 43.0):
        hw("brg_J1_z%.0f" % z, b68, M(t=(0, 0, z)), "steel", "6806 bearing (30x42x7)")
    for nm, Tj in (("J2", TURW @ J2J), ("J3", J3W)):
        hw("brg_%s_drive" % nm, b68, Tj @ M(t=(0, 0, 17.5)), "steel", "6806 bearing (30x42x7)")
        hw("brg_%s_idle" % nm, b68, Tj @ M(t=(0, 0, -24.5)), "steel", "6806 bearing (30x42x7)")
    hw("brg_J4", b67, M(t=(0, 0, G4.Z_LIP_TOP)), "steel", "6706 bearing (30x37x4)")
    hw("brg_J5_drive", b67, J5W @ M(t=(0, 0, W.J5.Z_IN + W.J5.SEAT_T)), "steel", "6706 bearing (30x37x4)")
    hw("brg_J5_idle", b67, J5W @ M(t=(0, 0, -W.J5.Z_IDLE)), "steel", "6706 bearing (30x37x4)")
    hw("brg_J6", b67, J5W @ ABC @ M(t=(0, 0, W.X6_LIP_TOP)), "steel", "6706 bearing (30x37x4)")

    # ---- horn screws: 4 x M2.5 x 6 per joint, heads on the coupler side ---
    hs = screw(2.5, 6.0, 4.5, 2.5)
    def horn_screws(tag, Tj, z_head, down=True):
        for a in (0, 90, 180, 270):
            p = (7 * np.cos(np.radians(a)), 7 * np.sin(np.radians(a)), z_head)
            T = Tj @ M(t=p) @ (np.eye(4) if down else flipZ)
            hw("horn_screw_%s_%d" % (tag, a), hs, T, "steel", "M2.5 x 6 socket head (horn)")
    # shafts: heads inside the bore on the end wall's inner face, shank toward the horn (+Z)
    horn_screws("J2", TURW @ J2J, 25.489 - DC.SHAFT_END_T, down=False)
    horn_screws("J3", J3W, G3.Z_HORN - DC.SHAFT_END_T, down=False)
    horn_screws("J5", J5W, W.Z5_HORN - DC.SHAFT_END_T, down=False)
    # hubs: heads in the counterbores, shank down toward the horn
    horn_screws("J1", np.eye(4), G1.Z_HORN + 1.6 * 0 + G1.UNDER_HEAD)
    horn_screws("J4", np.eye(4), G4.Z_HORN + G4.UNDER_HEAD)
    horn_screws("J6", J5W @ ABC, W.X6_HORN + G4.UNDER_HEAD)

    # ---- M3 bolts + inserts ---------------------------------------------
    def m3(tag, T, L, bom_len=None):
        hw(tag, screw(3.0, L, 5.5, 3.0), T, "steel", "M3 x %d socket head" % (bom_len or L))
    def ins(tag, T, L=5.7, d=4.1):
        hw(tag, insert(d, L, 3.0 if d < 5 else 4.0), T, "brass",
           "M3 heat-set insert" if d < 5 else "M4 heat-set insert")
    # split bolts J2 / J3 / J5: standard M3 x 45, head on p2's back face,
    # shank down into p1's insert (pocket 8.1 deep: tip 0.49 off the floor)
    zd2 = G2.P + DC.BAY_T + TP.BACK_T
    for tag, Tj, P, zd in (("J2", TURW @ J2J, G2.P, zd2), ("J3", J3W, G3.P, G3.Z_DRIVE),
                           ("J5", J5W, W.P5, W.J5.Z_DRIVE)):
        for i, (x, y) in enumerate(DC.SPLIT_BOLTS):
            m3("split_%s_%d" % (tag, i), Tj @ M(t=(x, y, zd)), DC.SPLIT_BOLT_L)
            ins("split_ins_%s_%d" % (tag, i), Tj @ M(t=(x, y, P)))
    # J4 / J6 cap bolts: heads in counterbores, into the wall-top inserts
    for tag, Tj, bolts, ztop, zlip in (("J4", np.eye(4), G4.CAP_BOLTS, G4.Z_CAP_TOP, G4.Z_LIP_TOP),
                                       ("J6", J5W @ ABC, W.CAP6_BOLTS, W.X6_CAP_TOP, W.X6_LIP_TOP)):
        for i, (x, y) in enumerate(bolts):
            # M3 x 12: an x 14 ended 0.22 mm off the pocket floor (fastener check)
            m3("cap_%s_%d" % (tag, i), Tj @ M(t=(x, y, ztop - G4.CB_HEAD_T)), 12)
            ins("cap_ins_%s_%d" % (tag, i), Tj @ M(t=(x, y, zlip)))
    # J4 base -> forearm (heads on the plate), J5 fork -> J4 hub (heads in the fork)
    for i, (x, y) in enumerate(G4.BOLTS):
        m3("j4base_forearm_%d" % i, M(t=(x, y, G4.Z_PLATE_TOP)), 10)
        ins("forearm_ins_%d" % i, M(t=(x, y, G4.Z_FACE)))
        # heads sunk DC.FLOOR_CB_T into the fork floors (Rule 8): M3 x 10
        m3("j5fork_j4hub_%d" % i, M(t=(x, y, G4.Z_HUB_TOP + 8.0 - DC.FLOOR_CB_T)), 10)
        ins("j4hub_ins_%d" % i, M(t=(x, y, G4.Z_HUB_TOP)))
        # J3 fork -> upper link socket end (released interface), heads inside the fork
        m3("j3fork_link_%d" % i, M(t=(x, y, 175.0 + 8.0 - DC.FLOOR_CB_T)), 10)
        ins("link_end_ins_%d" % i, M(t=(x, y, 175.0)))       # the upper link's end-face inserts
    # tool flange inserts
    for a in (45, 135, 225, 315):
        ins("tool_ins_%d" % a, J5W @ ABC @ M(t=(15 * np.cos(np.radians(a)), 15 * np.sin(np.radians(a)), W.X6_TOOL)))
    # J1: 4 x M4 base -> foot columns, collar pinch bolt, J5 grub
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        # M4 x 12: an x 14 ran 0.48 mm past the 8.0 insert pocket and bottomed out
        hw("m4_base_foot_%d" % i, screw(4.0, 12.0, 7.0, 4.0), M(t=(sx * 36.77, sy * 36.77, 5.5)), "steel", "M4 x 12 socket head")
        ins("foot_ins_%d" % i, M(t=(sx * 36.77, sy * 36.77, 0.0)), L=8.0, d=5.6)
    m3("collar_pinch", axis_frame((-GB.X_WALL + 3.2, GB.Y_BOLT, GB.BOLT_Z[0]), (-1, 0, 0)), 20)
    ins("collar_ins", axis_frame((GB.X_WALL, GB.Y_BOLT, GB.BOLT_Z[0]), (1, 0, 0)))
    # J5 axle grub, TIGHTENED: tip on the axle's flat (a = -14.20), M3 x 4
    hw("j5_grub", cq.Workplane("XY").circle(1.5).extrude(-4.0), J5W @ ABC @ axis_frame((DC.FLAT_Y - 4.0, 0, 0), (-1, 0, 0)), "steel", "M3 x 4 set screw")
    # link seams: M3 x 16 through the tongue half into the groove half's
    # inserts (bosses every <= 25 mm, both flanges) + the ear's M2.5 x 18.
    # Positions from link_pro's own rule; verify_fasteners.py then checks
    # each one against the real holes of both halves.
    import link_pro as LP
    import gen_forearm as GF
    for pair, fx, dy in (("upper", LP.UPPER_FACE_X, 0.0), ("fore", LP.FORE_FACE_X, 0.5)):
        Tt, Tg = X["link_%s_tongue" % pair], X["link_%s_groove" % pair]
        n = max(2, int(fx // LP.SEAM_PITCH) + 1)
        k = 0
        for x in [fx * i / (n - 1) for i in range(n)]:
            if x < LP.BOSS_R * 0.8 or x > fx - 12.0:
                continue
            for sy in (-1, 1):
                y = sy * (LP.SEC_H / 2 - LP.WALL_FLANGE - LP.BOSS_OD / 2 + dy)
                # head in the tongue's O6 x 3.2 counterbore (flush: the fork cheek is 1 mm away)
                m3("seam_%s_%d" % (pair, k), Tt @ axis_frame((x, y, GF.CB_M3_T), (0, 0, -1)), 16)
                ins("seam_ins_%s_%d" % (pair, k), Tg @ axis_frame((x, y, LP.HALF_D), (0, 0, 1)))
                k += 1
        xc = -(LP.BOSS_R - LP.EAR_OUT / 2.0 - 1.0)
        hw("ear_bolt_%s" % pair, screw(2.5, 16.0, 4.5, 2.5), Tt @ axis_frame((xc, 0, GF.CB_M25_T), (0, 0, -1)),
           "steel", "M2.5 x 16 socket head")
        hw("ear_ins_%s" % pair, insert(3.5, 4.0, 2.5), Tg @ axis_frame((xc, 0, LP.HALF_D), (0, 0, 1)),
           "brass", "M2.5 heat-set insert")
    # link lock (Rule 4): 2 x M5 x 10 cup-point set screws per link half,
    # self-tapped into the link's own O4.2 side holes at 90/270 deg (link
    # frame), through the centring ring's O5.4 holes, TIP ON the shaft's
    # double-D flat (r 14.20). Modelled tightened.
    import gen_clamp as GCL
    for k, lk in (("1", "link_upper_groove"), ("2", "link_upper_tongue"),
                  ("3", "link_fore_groove"), ("4", "link_fore_tongue")):
        for ang in (90, 270):
            a = np.radians(ang)
            r_out = -DC.FLAT_Y + GCL.SET_L
            T = X[lk] @ axis_frame((r_out * np.cos(a), r_out * np.sin(a), GCL.SET_Z), (np.cos(a), np.sin(a), 0))
            hw("link_set_%s_%d" % (k, ang), cq.Workplane("XY").circle(2.5).extrude(-GCL.SET_L), T, "steel",
               "M5 x 10 set screw (cup point)")
    # spring pins (shoulder screws + 5 mm spacer), springs, collar clamp bolts + nuts
    def pin(tag, p, sy):
        m3(tag, axis_frame((p[0], sy * (SP.PIN_Y + 6.5), p[2]), (0, sy, 0)), 12, 12)
        ins(tag + "_ins", axis_frame((p[0], sy * SP.PIN_Y, p[2]), (0, sy, 0)))
    for sy in (-1, 1):
        pin("pin_J2_turret_%+d" % sy, (0, 0, SP.J2_AXIS_Z + SP.A2), sy)
        pin("pin_J2_collar_%+d" % sy, (0, 0, SP.J2_AXIS_Z + SP.B2), sy)
        pin("pin_J3_fork_%+d" % sy, (0, 0, SP.J3_AXIS_Z + SP.A3), sy)
        pin("pin_J3_collar_%+d" % sy, (0, 0, SP.J3_AXIS_Z + SP.B3), sy)
    for (jn, a, b) in SP.springs_world(0, 0):
        s, T = spring(a, b)
        hw("spring_%s_%+.0f" % (jn, np.sign(a[1])), s, T, "spring",
           "extension spring %s (%s, inside hooks)" % (jn, "7.4 N @ 36.0 / 12.4 N @ 58.2 mm" if jn == "J2" else "2.2 N @ 43.0 / 5.0 N @ 91.4 mm"))
    for zc in (SP.J2_AXIS_Z + SP.B2, SP.J3_AXIS_Z + SP.B3):
        for sx in (-1, 1):
            x = sx * (SP.LINK_HALF_X + SP.CLR + SP.COLLAR_ARM / 2)
            yb = SP.LINK_HALF_Y + SP.CLR + SP.COLLAR_BACK
            # head on +y, nyloc on -y: grip 37.4 + nut 4.0 -> M3 x 45 stands 3.6 proud of the nut
            m3("collar_clamp_%.0f_%+d" % (zc, sx), axis_frame((x, yb, zc), (0, 1, 0)), 45)
            hw("collar_nut_%.0f_%+d" % (zc, sx), nut_m3(), axis_frame((x, -yb, zc), (0, -1, 0)), "steel", "M3 nyloc nut")
    return A, BOM


if __name__ == "__main__":
    A, BOM = build()
    out = os.path.join(HERE, "ARM450_REV_I_ASSEMBLY.step")
    A.save(out)
    print("written", out, "(%d components)" % len(A.children))
    # every component as a WORLD-placed mesh, so the PDF sections slice exactly
    # what the STEP assembly contains
    md = os.path.join(HERE, "_asm_meshes")
    # start EMPTY: meshes of retired parts (the old M3 clamp grubs) stayed in
    # here and the slice check measured them against the new M5 set screws
    import shutil
    if os.path.isdir(md):
        shutil.rmtree(md)
    os.makedirs(md)
    for ch in A.children:
        obj = ch.obj.val() if hasattr(ch.obj, "val") else ch.obj
        sh = obj.moved(ch.loc)
        cq.exporters.export(cq.Workplane().add(sh), os.path.join(md, ch.name + ".stl"),
                            tolerance=0.05, angularTolerance=0.3)
    print("component meshes in", md)
    with open(os.path.join(HERE, "HARDWARE_BOM.md"), "w") as f:
        f.write("# ARM-450 rev I -- bought hardware (counted from the placed assembly)\n\n| item | qty |\n|---|---|\n")
        for k, v in sorted(BOM.items()):
            f.write("| %s | %d |\n" % (k, v)); print("   %3d x %s" % (v, k))
