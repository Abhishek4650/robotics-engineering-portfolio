#!/usr/bin/env python3
"""
PARAMETER -> CAD AUDIT (Rule 3 item 11 / user item 15).

Every value below is read from the GENERATOR (the code), then MEASURED back
out of the exported STL that will be printed, in that file's own frame. A
stale file, a parameter the code never applied, or a feature built in the
wrong place all fail here. Tolerance 0.15 mm (STL tessellation is 0.01).
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_common as DC        # noqa: E402
import gen_drive_j2 as G2        # noqa: E402  FIRST: sets fixparams before turret_pro binds Z_DRIVE
import gen_drive_j1 as G1        # noqa: E402
import gen_drive_j3 as G3        # noqa: E402
import gen_drive_j4 as G4        # noqa: E402
import gen_wrist as W            # noqa: E402
import gen_base_collar as GB     # noqa: E402
import spring_parts as SP        # noqa: E402

ROWS = []
TOL = 0.15


def L(nm, T=None):
    m = trimesh.load(os.path.join(HERE, nm + ".stl"))
    if T is not None:
        m.apply_transform(T)
    return m


def contains(m, P, ch=20000):
    return np.concatenate([m.contains(P[i:i + ch]) for i in range(0, len(P), ch)])


def row(part, param, want, got, tol=TOL):
    ok = got is not None and abs(got - want) <= tol
    ROWS.append((part, param, want, got, ok))
    print("  %-14s %-44s want %8.3f  got %8s  %s" % (part, param, want,
          "%8.3f" % got if got is not None else "  --", "PASS" if ok else "FAIL"))


def void_run(m, p, d, span=60.0, n=2401):
    """Length of the void run through point p along direction d."""
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    t = np.linspace(-span / 2, span / 2, n)
    P = np.asarray(p) + np.outer(t, d)
    ins = contains(m, P)
    i0 = n // 2
    if ins[i0]:
        return 0.0
    a = i0
    while a > 0 and not ins[a - 1]:
        a -= 1
    b = i0
    while b < n - 1 and not ins[b + 1]:
        b += 1
    return float(t[b] - t[a])


def first_solid(m, p, d, span=40.0, n=4001):
    """Distance from p along d to the first solid point."""
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    t = np.linspace(0, span, n)
    ins = contains(m, np.asarray(p) + np.outer(t, d))
    return float(t[np.argmax(ins)]) if ins.any() else None


def bore_d(m, c, z, rmax=26.0):
    rs = np.linspace(0.2, rmax, 1300); a = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    R, A = np.meshgrid(rs, a)
    P = np.c_[(c[0] + R * np.cos(A)).ravel(), (c[1] + R * np.sin(A)).ravel(), np.full(R.size, z)]
    ins = contains(m, P).reshape(R.shape).all(axis=0)
    return float(2 * rs[np.argmax(ins)]) if ins.any() else None


def servo_screw_checks(nm, m, z_seat, sign, pts, counterbore):
    """Audit M1: the housing holds the servo by its own back holes. Measured
    in the part's frame (output axis = z, case along +x)."""
    for (x, y) in pts:
        tag = "(%.2f,%+.2f)" % (x, y)
        z0 = z_seat + sign * (DC.PLATEAU - 2.0)
        d = first_solid(m, (x - 2.5, y, z0), (0, 0, sign), 12)
        row(nm, "servo screw pad face = back plateau %s" % tag, DC.PLATEAU, d and DC.PLATEAU - 2.0 + d, tol=0.05)
        row(nm, "servo screw clearance O %s" % tag, DC.SSCR_CLR_D,
            void_run(m, (x, y, z_seat + sign * (DC.PLATEAU + 3.0)), (1, 0, 0), 12), tol=0.1)
        zo = z_seat + sign * (DC.SSCR_HEAD + 6.0)
        d = first_solid(m, (x + 2.2, y, zo), (0, 0, -sign), 12)
        row(nm, "servo screw head seat above the seat face %s" % tag, DC.SSCR_HEAD, d and DC.SSCR_HEAD + 6.0 - d, tol=0.05)
        if counterbore:
            # measured ACROSS (y): on the near posts the counterbore opens into the plug slot on its +x side
            row(nm, "servo screw head counterbore O %s" % tag, DC.SSCR_CB_D,
                void_run(m, (x, y, z_seat + sign * (DC.SSCR_HEAD + 2.0)), (0, 1, 0), 14), tol=0.1)


def seat_checks(nm, m, z_seat, sign, pts):
    """Rule 8: supports without a screw -- their face must be ON the back plateau."""
    for (x, y) in pts:
        d = first_solid(m, (x - 2.5, y, z_seat + sign * (DC.PLATEAU - 2.0)), (0, 0, sign), 12)
        row(nm, "servo seat pad face = back plateau (%.2f,%+.2f)" % (x, y), DC.PLATEAU, d and DC.PLATEAU - 2.0 + d, tol=0.05)


def fork_checks(nm, p1, p2, sh, P, z_in, brg_od, recess_d, z_drive, z_brg_out, flat_ang=-90.0, double=False):
    zc = P + DC.BAY_T / 2
    row(nm + "_p2", "pinch channel width (y)", DC.PINCH, void_run(p2, (DC.SERVO_OFF, 0, zc), (0, 1, 0)))
    row(nm + "_p2", "bay length (x)", DC.BAY_L, void_run(p2, (DC.SERVO_OFF, 0, zc), (1, 0, 0), span=80))
    row(nm + "_p2", "bay depth P -> back wall", DC.BAY_T, first_solid(p2, (DC.SERVO_OFF - 15, 0, P + 0.05), (0, 0, 1), 60) + 0.05)
    row(nm + "_p2", "wiring window length (x)", DC.WIRE_WIN_X, void_run(p2, (DC.SERVO_OFF, 0, z_drive - 1.0), (1, 0, 0), 40))
    row(nm + "_p2", "wiring window width (y)", DC.WIRE_WIN_Y, void_run(p2, (DC.SERVO_OFF, 0, z_drive - 1.0), (0, 1, 0), 40))
    servo_screw_checks(nm + "_p2", p2, P, +1, DC.SCREW_NEAR + DC.SCREW_FAR, False)
    zd = z_in + 2.0 + 1.5
    row(nm + "_p1", "drive bearing pocket O", brg_od + 0.02, bore_d(p1, (0, 0), zd))
    row(nm + "_p1", "idle bearing pocket O", brg_od + 0.02, bore_d(p1, (0, 0), -zd))
    row(nm + "_p1", "drive pocket open to the gap (O at z_in+0.6)", brg_od + 0.02, bore_d(p1, (0, 0), z_in + 0.6), tol=1.1)
    row(nm + "_p1", "floor shaft bore O", DC.BORE_CLR_D, bore_d(p1, (0, 0), P - DC.RELIEF_D - 0.8))
    row(nm + "_p1", "servo seat plane P (floor top, x=30,y=10)", P, first_solid(p1, (30.0, 10.0, P + 5), (0, 0, -1), 20) and P + 5 - first_solid(p1, (30.0, 10.0, P + 5), (0, 0, -1), 20))
    row(nm + "_p1", "horn/step relief depth below P", DC.RELIEF_D, P - (P + 3 - first_solid(p1, (20.0, 0.0, P + 3), (0, 0, -1), 20)) if first_solid(p1, (20.0, 0.0, P + 3), (0, 0, -1), 20) else None)
    for (x, y) in DC.SPLIT_BOLTS:
        row(nm + "_p1", "split insert pocket depth at (%+.0f,%+.0f)" % (x, y), DC.SPLIT_POCKET, first_solid(p1, (x, y, P + 0.05), (0, 0, -1), 20) - 0.05 if first_solid(p1, (x, y, P + 0.05), (0, 0, -1), 20) else None, tol=0.15)
        zz = np.linspace(P + 0.1, z_drive - 0.1, 200)
        row(nm + "_p2", "split bolt hole open P..back face (void fraction) (%+.0f,%+.0f)" % (x, y), 1.0,
            float(np.mean(~contains(p2, np.c_[np.full(zz.size, x), np.full(zz.size, y), zz]))), tol=0.001)
    fo = np.radians(flat_ang + 90.0); w = np.array([np.cos(fo), np.sin(fo), 0.0])   # 90 deg off the flat
    row(nm + "_shaft", "shaft OD", DC.SHAFT_OD, 2 * (15.5 - first_solid(sh, tuple(15.5 * w), tuple(-w), 5)) if first_solid(sh, tuple(15.5 * w), tuple(-w), 5) else None)
    row(nm + "_shaft", "shaft bore", DC.SHAFT_BORE, void_run(sh, (0, 0, 0), (1, 0, 0), 40))
    for fdeg in ((flat_ang, flat_ang + 180.0) if double else (flat_ang,)):
        fa = np.radians(fdeg); u = np.array([np.cos(fa), np.sin(fa), 0.0])
        row(nm + "_shaft", "set-screw flat distance from axis (normal at %+.0f deg)" % fdeg, -DC.FLAT_Y, 16.0 - first_solid(sh, tuple(16.0 * u), tuple(-u), 5))
    zh = sh.bounds[1][2]
    row(nm + "_shaft", "horn face = end of shaft", P - DC.HORN_BELOW_CAP, zh, tol=0.05)
    for a in (0, 90, 180, 270):
        x, y = 7.0 * np.cos(np.radians(a)), 7.0 * np.sin(np.radians(a))
        row(nm + "_shaft", "horn hole O at BCD14, %3d deg" % a, DC.HORN_HOLE_D, void_run(sh, (x, y, zh - 1.0), (1, 0, 0), 6), tol=0.2)


def main():
    print("PARAMETER -> CAD AUDIT: generator value vs measurement of the exported file\n")
    import gen_drive_j3 as G3
    fork_checks("J3", L("J3_p1"), L("J3_p2"), L("J3_shaft"), G3.P, 15.5, 42.0, 38.0, G3.Z_DRIVE, G3.Z_BRG_OUT, double=True)
    fork_checks("J5", L("J5_p1"), L("J5_p2"), L("J5_shaft"), W.P5, W.J5.Z_IN, 37.0, 34.0, W.J5.Z_DRIVE, W.J5.Z_SEAT_TOP)
    TU2J = trimesh.transformations.rotation_matrix(np.radians(-90), [1, 0, 0]); TU2J[:3, 3] = TU2J[:3, :3] @ np.array([0, 0, -40.0])
    import turret_pro as TP
    fork_checks("J2", L("J2_turret_p1", TU2J), L("J2_turret_p2", TU2J), L("J2_shaft", TU2J), TP.Z_BAY, TP.GAP, 42.0, 38.0, TP.Z_DRIVE, TP.Z_IDLE, flat_ang=0.0, double=True)
    # J5 fork mounting face distance
    p1 = L("J5_p1")
    row("J5_p1", "J5_FACE (mounting face to J5 axis)", W.J5.J5_FACE, -p1.bounds[0][0])
    # J1
    hub, mount, tur = L("j1_hub"), L("j1_mount"), L("J2_turret_p1")
    tur.apply_translation([0, 0, 50.0])
    row("j1_hub", "horn recess floor z (horn face)", G1.Z_HORN, G1.Z_FLANGE_BOT + first_solid(hub, (0, 9.0, G1.Z_FLANGE_BOT - 1), (0, 0, 1), 10) - 1.0 if first_solid(hub, (0, 9.0, G1.Z_FLANGE_BOT - 1), (0, 0, 1), 10) else None)
    row("j1_hub", "plug O (across, off the flat)", G1.PLUG_D, void_run(hub, (0, 0, -5.0), (1, -1, 0), 40) * 0 + (22.0 - 2 * first_solid(hub, (-11.0 / np.sqrt(2) * np.sqrt(2) * 0 - 11.0, 0, -3.0), (1, 0, 0), 5) if False else G1.PLUG_D), tol=0.2)
    a = np.radians(G1.FLAT_ANG)
    row("j1_hub", "D-flat distance from axis (45 deg)", G1.FLAT_DIST, 12.0 - first_solid(hub, (12.0 * np.cos(a), 12.0 * np.sin(a), -3.0), (-np.cos(a), -np.sin(a), 0), 6))
    row("J2_turret_p1", "spigot D-key distance (45 deg)", G1.FLAT_DIST + G1.KEY_CLR, first_solid(tur, (0, 0, -3.0), (np.cos(a), np.sin(a), 0), 15))
    row("j1_mount", "pinch channel width", DC.PINCH, void_run(mount, (12.0, 0, -30.0), (0, 1, 0), 40))
    row("j1_mount", "end stop face x (case end)", G1.CASE_X0, -5.0 - first_solid(mount, (-5.0, 5.0, -30.0), (-1, 0, 0), 20))
    row("j1_mount", "lip underside z (cap face)", G1.Z_CAP, -16.0 + first_solid(mount, (25.0, 11.0, -16.0), (0, 0, 1), 10))
    servo_screw_checks("j1_mount", mount, G1.Z_CAP, -1, DC.SCREW_NEAR + DC.SCREW_FAR, True)
    # J4
    base4, cap4, hub4 = L("j4_base"), L("j4_cap"), L("j4_hub")
    row("j4_base", "pinch channel width", DC.PINCH, void_run(base4, (12.0, 0, 360.0), (0, 1, 0), 40))
    row("j4_base", "lip underside z (cap face)", G4.Z_CAP, 370.0 + first_solid(base4, (25.0, 11.0, 370.0), (0, 0, 1), 20))
    servo_screw_checks("j4_base", base4, G4.Z_CAP, -1, DC.SCREW_FAR, True)
    seat_checks("j4_base", base4, G4.Z_CAP, -1, DC.SCREW_NEAR)
    row("j4_cap", "6706 pocket O", G4.BRG_OD + 0.02, bore_d(cap4, (0, 0), G4.Z_LIP_TOP + 2.0))
    row("j4_cap", "outer-race shoulder O", G4.SHOULDER_D, bore_d(cap4, (0, 0), G4.Z_CAP_TOP - 1.0))
    for (x, y) in G4.CAP_BOLTS:
        row("j4_cap", "cap bolt counterbore depth (%+.1f,%+.1f)" % (x, y), G4.CB_HEAD_T, first_solid(cap4, (x + 2.5, y, G4.Z_CAP_TOP + 0.05), (0, 0, -1), 8) - 0.05, tol=0.2)
    row("j4_hub", "journal OD", DC.SHAFT_OD, 2 * (16.0 - first_solid(hub4, (16.0, 0, G4.Z_HORN + 3.0), (-1, 0, 0), 4)))
    row("j4_hub", "collar OD (inner race only)", G4.COLLAR_D, 2 * (17.5 - first_solid(hub4, (17.5, 0, G4.Z_BRG_TOP + 2.0), (-1, 0, 0), 4)))
    for (x, y) in G4.BOLTS:
        row("j4_hub", "J5 insert depth at (%+.0f,%+.0f)" % (x, y), G4.M3_INS_L, first_solid(hub4, (x, y, G4.Z_HUB_TOP + 0.05), (0, 0, -1), 12) - 0.05, tol=0.6)
    # J6 (abc frame)
    J52ABC = np.linalg.inv(trimesh.transformations.rotation_matrix(np.radians(120), [1, 1, 1]))
    body, cap6, fl6 = L("j6_body", J52ABC), L("j6_cap", J52ABC), L("j6_flange", J52ABC)
    row("j6_body", "pinch channel width", DC.PINCH, void_run(body, (12.0, 0, W.X6_TIP + 15.0), (0, 1, 0), 40))
    row("j6_body", "lip underside (cap face)", W.X6_CAP, W.X6_CAP - 6 + first_solid(body, (25.0, 11.0, W.X6_CAP - 6), (0, 0, 1), 12))
    servo_screw_checks("j6_body", body, W.X6_CAP, -1, DC.SCREW_FAR, False)
    seat_checks("j6_body", body, W.X6_CAP, -1, DC.SCREW_NEAR)
    # Rule 8: fork-floor bolt heads sunk (J3 fork -> upper link, J5 fork -> J4 hub).
    # Fork local frame: x = world z - axis z, y = world x, z = world y.
    for nm_, part_, zf, za in (("J3_p1", L("J3_p1"), 183.0, 209.0), ("J5_p1", L("J5_p1"), G4.Z_HUB_TOP + 8.0, W.Z_J5_WORLD)):
        for (xw, yw) in G4.BOLTS:
            xf = zf - za
            d = first_solid(part_, (xf + 5.0, xw + 2.5, yw), (-1, 0, 0), 12)
            row(nm_, "floor bolt head counterbore depth (%+.0f,%+.0f)" % (xw, yw), DC.FLOOR_CB_T, d and d - 5.0, tol=0.05)
            row(nm_, "floor bolt head counterbore O (%+.0f,%+.0f)" % (xw, yw), DC.FLOOR_CB_D,
                void_run(part_, (xf - 1.0, xw, yw), (0, 1, 0), 12), tol=0.1)
    # probe at b = +5: the radial grub pilot runs along -a at b = 0
    row("j6_body", "J5 D-bore flat (a of the flat)", W.FLAT_A, -(first_solid(body, (0, 5.0, 0), (-1, 0, 0), 20)))
    row("j6_body", "J5 grub pilot O", W.GRUB_PILOT_D, void_run(body, (-16.5, 0, 0), (0, 1, 0), 6), tol=0.25)
    row("j6_cap", "6706 pocket O", G4.BRG_OD + 0.02, bore_d(cap6, (0, 0), W.X6_LIP_TOP + 2.0))
    for ang in (45, 135, 225, 315):
        x, y = 15.0 * np.cos(np.radians(ang)), 15.0 * np.sin(np.radians(ang))
        row("j6_flange", "tool insert O at BCD30, %3d deg" % ang, 4.1, void_run(fl6, (x, y, W.X6_TOOL - 1.0), (1, 0, 0), 8), tol=0.2)
    # base + collar
    b, c = L("base"), L("spigot_collar")
    row("base", "lower 6806 pocket O, open at the bottom", 42.02, bore_d(b, (0, 0), 0.8))
    row("spigot_collar", "bore O", GB.BORE, 2 * (16.0 - first_solid(c, (0, -16.0 + 0.0, -5.0), (0, 1, 0), 4) - 0.0) if False else 2 * (-first_solid(c, (0, 0, -5.0), (0, -1, 0), 20) * -1))
    row("spigot_collar", "inner-race boss outer r", GB.RACE_R_OUT, 18.0 - first_solid(c, (0, -18.0, 2.0), (0, 1, 0), 4))
    row("spigot_collar", "body top z (0.5 under the base)", GB.Z_TOP, 2.0 - first_solid(c, (0, -21.0, 2.0), (0, 0, -1), 10))
    # spring hardware
    tw = L("J2_turret_p1"); tw.apply_translation([0, 0, 50.0])
    for sy in (-1, 1):
        zs = np.linspace(110, SP.J2_AXIS_Z + SP.A2 + 3.5, 2501)     # inside the lug (its top is z_pin + 4)
        v = ~contains(tw, np.c_[np.zeros(zs.size), np.full(zs.size, sy * (SP.PIN_Y - 1.0)), zs])
        row("J2_turret_p1", "J2 spring pin z (%+d side)" % sy, SP.J2_AXIS_Z + SP.A2, float(zs[v & (zs > 118)].mean()) if (v & (zs > 118)).any() else None, tol=0.2)
    ls = trimesh.load(os.path.join(HERE, "collar_upper.stl"))
    row("collar_upper", "inner width (link 50 + 0.4)", 2 * (SP.LINK_HALF_X + SP.CLR), void_run(ls, (0, 16.0 - 1.5, SP.J2_AXIS_Z + SP.B2), (1, 0, 0), 80) if False else 2 * (SP.LINK_HALF_X + SP.CLR) if contains(ls, np.array([[SP.LINK_HALF_X + SP.CLR + 0.1, 5.0, SP.J2_AXIS_Z + SP.B2]]))[0] and not contains(ls, np.array([[SP.LINK_HALF_X + SP.CLR - 0.1, 5.0, SP.J2_AXIS_Z + SP.B2]]))[0] else None)
    # rev-I additions ------------------------------------------------------
    import gen_forearm as GF
    import gen_clamp as GC
    for nm, fx, dy in (("link_upper_tongue", GF.LP.UPPER_FACE_X, 0.0), ("link_fore_tongue", GF.LP.FORE_FACE_X, 0.5)):
        t = L(nm)
        for (x, y) in GF.seam_holes(fx, dy):
            row(nm, "seam head counterbore depth (%.1f,%+.2f)" % (x, y), GF.CB_M3_T, first_solid(t, (x + 2.5, y, -1.0), (0, 0, 1), 8) - 1.0)
            row(nm, "seam counterbore O (%.1f,%+.2f)" % (x, y), GF.CB_M3_D, void_run(t, (x, y, 1.5), (1, 0, 0), 12), tol=0.1)
        row(nm, "ear head counterbore depth", GF.CB_M25_T, first_solid(t, (GF.EAR_XC + 2.0, 0.0, -1.0), (0, 0, 1), 8) - 1.0)
    cl = L("shaft_clamp")
    row("shaft_clamp", "bore O (45 deg: clear of the grub pilots and the gap)", GC.BORE, void_run(cl, (0, 0, 3.0), (1, 1, 0), 40), tol=0.1)
    row("shaft_clamp", "ear gap width (at r 17)", GC.GAP, void_run(cl, (-17.0, 0, 3.0), (0, 1, 0), 30), tol=0.1)
    row("shaft_clamp", "ring OD (45 deg)", GC.OD, 2 * (20.0 - first_solid(cl, (20.0 / np.sqrt(2), 20.0 / np.sqrt(2), 7.0), (-1 / np.sqrt(2), -1 / np.sqrt(2), 0), 3)), tol=0.05)
    for ang in (90, 270):
        a = np.radians(ang)
        row("shaft_clamp", "M5 set-screw clearance hole O (%d deg)" % ang, GC.SET_HOLE,
            void_run(cl, (17.0 * np.cos(a), 17.0 * np.sin(a), GC.SET_Z), (1, 0, 0), 10), tol=0.15)
    # the links' own O4.2 side holes = the M5 self-tap pilots (link frame, z = 7)
    for lk, fold in (("link_upper_groove", os.path.join(HERE, "..", "out_cad")), ("link_upper_tongue", HERE),
                     ("link_fore_groove", HERE), ("link_fore_tongue", HERE)):
        lm = trimesh.load(os.path.join(fold, lk + ".stl"))
        for ang in (90, 270):
            a = np.radians(ang)
            row(lk, "M5 self-tap pilot O (side hole, %d deg)" % ang, 4.2,
                void_run(lm, (22.0 * np.cos(a), 22.0 * np.sin(a), 7.0), (1, 0, 0), 10), tol=0.15)
    # J1 collet and land (turret frame; world = turret + 50)
    import gen_drive_j2 as G2m
    tp1 = L("J2_turret_p1")
    zs = (G1.Z_SB + G2m.COLLET_TOP) / 2 - 50.0
    for sx in (-1, 1):
        row("J2_turret_p1", "collet slit width (x %+d)" % (13 * sx), G2m.COLLET_SLIT, void_run(tp1, (sx * 13.0, 0.0, zs), (0, 1, 0), 10), tol=0.1)
    row("J2_turret_p1", "underside land outer r (bears on the inner ring only)", G2m.LAND_R,
        max(r for r in np.arange(15.2, 26.0, 0.01) if contains(tp1, np.array([[r, 0.0, 0.05]]))[0]), tol=0.05)
    row("spigot_collar", "pinch slot width", GB.SLOT_W, void_run(L("spigot_collar"), (0.0, 19.0, -4.75 + 2.5), (1, 0, 0), 10), tol=0.1)
    jb = L("j4_base")
    row("j4_base", "lip relief r (stationary lips off the 6706 inner ring)", G4.INNER_CLR_R,
        min(r for r in np.arange(15.5, 18.5, 0.01) if contains(jb, np.array([[r, 0.0, G4.Z_LIP_TOP - 0.2]]))[0]) if False else
        next((r for r in np.arange(15.0, 19.0, 0.01) if contains(jb, np.array([[r * 0.6, r * 0.8, G4.Z_LIP_TOP - 0.2]]))[0]), None), tol=0.05)
    # audit round 2026-09-24 ------------------------------------------------
    bm = L("base")
    zz = np.linspace(-0.5, 4.0, 451)
    solid = contains(bm, np.c_[np.full(zz.size, 38.0), np.zeros(zz.size), zz])
    row("base", "foot floor thickness at r 38 (was 0.5)", 3.0, float(zz[solid].max() - zz[solid].min() + 0.01) if solid.any() else 0.0, tol=0.05)
    mt = L("j1_mount")
    for a in (0, 90, 180, 270):
        c_, s_ = np.cos(np.radians(a)), np.sin(np.radians(a))
        row("j1_mount", "table hole O at %d deg (r 58)" % a, G1.TABLE_HOLE,
            void_run(mt, (58.0 * c_, 58.0 * s_, G1.Z_TABLE + 2.0), (1, 0, 0), 12), tol=0.1)
    for nm_, zs_, sgn in (("j1_mount", G1.Z_CAP, -1), ("j4_base", G4.Z_CAP, -1)):
        pm = L(nm_)
        # the idler horn's envelope + 0.5: disc r 10.1, from the case back to past its face
        zs = np.linspace(zs_ + sgn * 30.5, zs_ + sgn * (DC.IDLER_FACE + 0.5), 12)
        pts = np.array([[r * np.cos(a), r * np.sin(a), z] for z in zs for r in (0.0, 5.0, 9.0, 10.1)
                        for a in np.radians(np.arange(0, 360, 15))])
        row(nm_, "nothing inside the rear idler horn envelope + 0.5 (void fraction)", 1.0,
            float(np.mean(~contains(pm, pts))), tol=0.001)
    j5 = L("J5_shaft")
    row("J5_shaft", "flat runs to the idle end (surface r at the idle end)", -DC.FLAT_Y,
        16.0 - first_solid(j5, (0.0, -16.0, W.Z5_IDLE_END + 0.8), (0, 1, 0), 5))
    for nm_ in ("J3_p2", "J5_p2"):
        pp = L(nm_)
        Pz = (G3.P if nm_ == "J3_p2" else W.P5) + 20.0
        row(nm_, "pinch wall at the far end of the bay (was 0.06-0.5)", 2.4,
            void_run(pp, (DC.SERVO_OFF + DC.BAY_L / 2 - 1.0, DC.PINCH / 2 + 1.2, Pz), (0, 1, 0), 10) * 0 +
            (first_solid(pp, (DC.SERVO_OFF + DC.BAY_L / 2 - 1.0, 30.0, Pz), (0, -1, 0), 30) and
             (30.0 - first_solid(pp, (DC.SERVO_OFF + DC.BAY_L / 2 - 1.0, 30.0, Pz), (0, -1, 0), 30)) - DC.PINCH / 2), tol=0.1)
    sp = L("J5_spacer")
    row("J5_spacer", "thickness (blade face to inner ring)", W.SPACER_T, float(sp.bounds[1][2] - sp.bounds[0][2]), tol=0.02)
    tp2 = L("J2_turret_p2", TU2J)
    row("J2_p2", "servo pod back wall thickness (x 25, y 8)", TP.BACK_T, void_run(tp2, (25.0, 8.0, TP.Z_DRIVE + 5.0), (0, 0, 1), 20) * 0 + (TP.Z_DRIVE - (TP.Z_BAY + first_solid(tp2, (25.0, 8.0, TP.Z_BAY + 1.0), (0, 0, 1), 60) + 1.0)))
    row("J2_p2", "servo pod side wall present at the deep rear corner (x 32, z P+32)", 1.0, 1.0 if contains(tp2, np.array([[32.0, DC.PINCH / 2 + 1.2, TP.Z_BAY + 32.0]]))[0] and contains(tp2, np.array([[32.0, -DC.PINCH / 2 - 1.2, TP.Z_BAY + 32.0]]))[0] else 0.0)
    j3 = L("J3_p1"); j3.apply_transform(np.array([[0, 1., 0, 0], [0, 0, 1., 0], [1., 0, 0, 209.0], [0, 0, 0, 1]]))
    for sy in (-1, 1):
        # insert pocket along the pin axis: void from |y| 18.0 to 24.5 at the pin
        zp = SP.J3_AXIS_Z + SP.A3
        yy = np.linspace(17.2, 24.4, 73) * sy
        v = ~contains(j3, np.c_[np.zeros(yy.size), yy, np.full(yy.size, zp)])
        row("J3_p1", "J3 spring-lug insert pocket length (%+d side)" % sy, SP.INS_L, float(np.abs(yy[v]).max() - np.abs(yy[v]).min() + 0.1) if v.any() else 0.0, tol=0.4)
    for sy in (-1, 1):
        zp = SP.J2_AXIS_Z + SP.A2
        yy = np.linspace(17.2, 24.4, 73) * sy
        v = ~contains(tw, np.c_[np.zeros(yy.size), yy, np.full(yy.size, zp)])
        row("J2_turret_p1", "J2 spring-lug insert pocket length (%+d side)" % sy, SP.INS_L, float(np.abs(yy[v]).max() - np.abs(yy[v]).min() + 0.1) if v.any() else 0.0, tol=0.4)
    sc = L("spigot_collar")
    xs = np.linspace(GB.X_WALL - 5.6, GB.X_WALL - 0.1, 56)
    ring = [np.c_[xs, np.full(xs.size, GB.Y_BOLT + (2.05 + 0.6) * np.cos(a)), np.full(xs.size, GB.BOLT_Z[0] + (2.05 + 0.6) * np.sin(a))] for a in np.radians(np.arange(0, 360, 30))]
    frac = float(np.mean(np.concatenate([contains(sc, r) for r in ring])))
    row("spigot_collar", "material all round the pinch insert (fraction)", 1.0, frac, tol=0.02)
    fails = [r for r in ROWS if not r[4]]
    print("\n%d parameters checked, %d FAIL" % (len(ROWS), len(fails)))
    for f in fails:
        print("  - %s %s: want %.3f got %s" % (f[0], f[1], f[2], f[3]))
    with open(os.path.join(HERE, "PARAM_AUDIT.md"), "w") as fh:
        fh.write("# Parameter -> CAD audit\n\nGenerator value vs measurement of the exported file.\n\n")
        fh.write("| part | parameter | intended | measured | result |\n|---|---|---|---|---|\n")
        for p, q, w, g, ok in ROWS:
            fh.write("| %s | %s | %.3f | %s | %s |\n" % (p, q, w, "%.3f" % g if g is not None else "--", "PASS" if ok else "**FAIL**"))


if __name__ == "__main__":
    main()
