"""
Part-by-part geometric audit, straight from the STEP files.

Reads the real B-rep -- not a mesh, not the source that made it -- enumerates
every cylindrical face, groups them into physical holes/bosses, and checks each
part against a schedule of the features it is SUPPOSED to have.

Reports per part:
    OK        expected feature found at the expected size and place
    MISSING   expected feature not present            <- the ones that matter
    EXTRA     a hole in the part that nothing accounts for
    OFFSET    right size, wrong position

Why STEP and not STL: an STL is a tessellation, so a Ø10.00 bore measures
Ø9.97-Ø10.03 depending on where you sample it, and a 0.02 mm fit decision cannot
be made on that. The STEP carries the exact analytic surface.
"""
import os
import sys
import math
import numpy as np
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_SurfaceType

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad"))
from params import *          # noqa: F403,F401

CAD = "output/cad"
TOL_R = 0.06                  # radius match tolerance, mm
TOL_P = 0.60                  # position match tolerance, mm


def _axis_key(d):
    """Direction with a canonical sign, so +Z and -Z are the same axis."""
    v = np.array([d.X(), d.Y(), d.Z()], float)
    v = v / (np.linalg.norm(v) + 1e-12)
    for c in v:
        if abs(c) > 1e-6:
            if c < 0:
                v = -v
            break
    return np.round(v, 3)


def cylinders(step_path):
    """Every cylindrical face, grouped into distinct holes/bosses."""
    solid = cq.importers.importStep(step_path).val()
    raw = []
    for f in solid.Faces():
        a = BRepAdaptor_Surface(f.wrapped)
        if a.GetType() != GeomAbs_SurfaceType.GeomAbs_Cylinder:
            continue
        cyl = a.Cylinder()
        ax = cyl.Axis()
        p = np.array([ax.Location().X(), ax.Location().Y(), ax.Location().Z()])
        d = _axis_key(ax.Direction())
        bb = f.BoundingBox()
        ext = np.array([bb.xlen, bb.ylen, bb.zlen])
        raw.append(dict(r=cyl.Radius(), d=d, p=p,
                        length=float(abs(ext @ np.abs(d))),
                        bb=(np.array([bb.xmin, bb.ymin, bb.zmin]),
                            np.array([bb.xmax, bb.ymax, bb.zmax]))))
    # Group by (radius, axis direction, axis line) AND THEN split by axial gaps.
    # Without the second step two pockets facing each other down the same axis --
    # the J5 yoke's cheeks, the two ends of a bore -- merge into one "feature"
    # whose depth is the whole span, and the audit reports 1 pocket 52 mm deep
    # instead of 2 pockets 7 mm deep.
    lines = []
    for c in raw:
        perp = c["p"] - c["d"] * (c["p"] @ c["d"])
        hit = None
        for g in lines:
            if (abs(g["r"] - c["r"]) < 1e-4
                    and np.allclose(g["d"], c["d"], atol=1e-3)
                    and np.linalg.norm(g["perp"] - perp) < 1e-3):
                hit = g
                break
        lo = float(c["bb"][0] @ np.abs(c["d"]))
        hi = float(c["bb"][1] @ np.abs(c["d"]))
        if hit is None:
            lines.append(dict(r=c["r"], d=c["d"], perp=perp, iv=[(lo, hi)]))
        else:
            hit["iv"].append((lo, hi))
    out = []
    for g in lines:
        iv = sorted(g["iv"])
        runs = [list(iv[0])]
        for lo, hi in iv[1:]:
            if lo <= runs[-1][1] + 0.05:            # touching or overlapping
                runs[-1][1] = max(runs[-1][1], hi)
            else:
                runs.append([lo, hi])               # a genuine second feature
        for lo, hi in runs:
            out.append(dict(r=g["r"], d=g["d"], perp=g["perp"], n=len(iv),
                            axial=(lo, hi), depth=hi - lo))
    for g in out:
        g["dia"] = 2 * g["r"]
    return sorted(out, key=lambda g: (-g["dia"], tuple(g["perp"])))


# ---------------------------------------------------------------------------
RES = []


def rec(part, status, feature, detail):
    RES.append((part, status, feature, detail))


def find(cyl, dia, tol=TOL_R):
    return [g for g in cyl if abs(g["dia"] - dia) < tol]


def check_count(part, cyl, dia, want, label, tol=TOL_R):
    got = find(cyl, dia, tol)
    n = len(got)
    if n == want:
        rec(part, "OK", label, f"Ø{dia:.2f} × {n}")
    elif n < want:
        rec(part, "MISSING", label, f"Ø{dia:.2f}: expected {want}, found {n}")
    else:
        rec(part, "EXTRA", label, f"Ø{dia:.2f}: expected {want}, found {n}")
    return got


def check_coaxial(part, cyl, d1, d2, label):
    """A bearing pocket and its through bore must share an axis. If they do not,
    the outer race sits square while the shaft runs at an angle -- exactly the
    tilt the paired-bearing design exists to remove."""
    a, b = find(cyl, d1), find(cyl, d2)
    if not a or not b:
        rec(part, "SKIP", label, f"need Ø{d1} and Ø{d2}")
        return
    worst, pair = 0.0, None
    for g in a:
        near = min(b, key=lambda h: np.linalg.norm(h["perp"] - g["perp"]))
        e = float(np.linalg.norm(near["perp"] - g["perp"]))
        if e > worst:
            worst, pair = e, (g, near)
    if worst < 0.02:
        rec(part, "OK", label, f"Ø{d1}/Ø{d2} coaxial to {worst*1000:.0f} µm")
    else:
        rec(part, "OFFSET", label, f"Ø{d1}/Ø{d2} axes differ by {worst:.3f} mm")


def check_depth(part, cyl, dia, want, label, tol=0.05):
    for g in find(cyl, dia):
        if abs(g["depth"] - want) > tol:
            rec(part, "OFFSET", label,
                f"Ø{dia:.2f} depth {g['depth']:.2f}, expected {want:.2f}")
            return
    if find(cyl, dia):
        rec(part, "OK", label, f"Ø{dia:.2f} × {want:.2f} deep")


def check_spacing(part, cyl, dia, want, label):
    """Distance between the two features of a pair -- joint pitch, cheek gap."""
    g = find(cyl, dia)
    if len(g) < 2:
        rec(part, "SKIP", label, f"need 2 × Ø{dia}, found {len(g)}")
        return
    d = max(float(np.linalg.norm(a["perp"] - b["perp"]))
            for a in g for b in g)
    if abs(d - want) < 0.05:
        rec(part, "OK", label, f"{d:.2f} mm")
    else:
        rec(part, "OFFSET", label, f"{d:.2f} mm, expected {want:.2f}")


def dump(part, cyl):
    print(f"\n  cylindrical features in {part}:")
    for g in cyl:
        ax = "XYZ"[int(np.argmax(np.abs(g["d"])))]
        print(f"    Ø{g['dia']:7.2f}  axis {ax}  at ({g['perp'][0]:+7.2f},"
              f"{g['perp'][1]:+7.2f},{g['perp'][2]:+7.2f})  depth {g['depth']:6.2f}")


SEAT = BRG_OD - 2 * BRG_SHOULDER            # 38
POCKET = BRG_OD + BRG_FIT                   # 42


def audit_link(kind):
    part = f"link_half_{kind}"
    cyl = cylinders(f"{CAD}/{part}.step")
    check_count(part, cyl, POCKET, 2, "bearing pockets")
    # SEAT DEPTH vs CYLINDRICAL DEPTH. Since the 0.5 x 45 lead-in chamfers were cut
    # (2026-08-25) the top BRG_CHAMFER of every pocket is a CONE, so the cylindrical
    # face reads (W - chamfer): 6.50 of a 7.00 seat, 3.50 of 4.00. The seat is still
    # its full depth to the shoulder and the bearing still grips 93 % of its race,
    # which is what a machined housing does too. Expecting the full width here fails
    # a part that is right -- and this is the THIRD copy of that expectation, after
    # dim_audit.py and check_bearing_fit.py.
    check_depth(part, cyl, POCKET, BRG_W - BRG_CHAMFER, "pocket depth")
    check_count(part, cyl, SEAT, 2, "through bores")
    check_coaxial(part, cyl, POCKET, SEAT, "pocket/bore coaxial")
    check_spacing(part, cyl, POCKET, LINK_L, "joint-to-joint pitch")
    if kind == "tongue":
        check_count(part, cyl, M3_CLEAR, 6, "M3 seam clearance holes")
        check_count(part, cyl, TIP_CLEAR, 2, "M2.5 tip-ear clearance")
    else:
        check_count(part, cyl, M3_INSERT_D, 6, "M3 insert holes")
        check_count(part, cyl, TIP_INSERT_D, 2, "M2.5 tip-ear inserts")
        check_depth(part, cyl, M3_INSERT_D, M3_INSERT_L, "insert depth")
    check_count(part, cyl, BOSS_OD, 6, "insert bosses")
    return part, cyl


def audit_clamp():
    part = "shaft_clamp"
    cyl = cylinders(f"{CAD}/{part}.step")
    check_count(part, cyl, BRG_OD - 2 * BRG_SHOULDER, 1, "clamp OD")
    check_count(part, cyl, SHAFT_OD + 0.2, 1, "shaft bore")
    check_count(part, cyl, CLAMP_PIN_D, 2, "roll-pin holes")
    check_coaxial(part, cyl, 38.0, 30.2, "OD/bore coaxial")
    return part, cyl


def audit_shaft():
    part = "shaft_tube"
    cyl = cylinders(f"{CAD}/{part}.step")
    check_count(part, cyl, SHAFT_OD, 1, "tube OD")
    check_count(part, cyl, SHAFT_OD - 2 * SHAFT_WALL, 1, "tube bore")
    # each cross hole pierces BOTH tube walls -> two cylindrical faces per hole
    check_count(part, cyl, CLAMP_PIN_D, 4, "roll-pin bores (2 holes × 2 walls)")
    check_coaxial(part, cyl, SHAFT_OD, SHAFT_OD - 2 * SHAFT_WALL, "OD/bore coaxial")
    return part, cyl


def audit_wrist(part, n_pocket):
    """The wrist runs 6706 (Ø37 x 4), not the 6806 used at J1/J2/J3."""
    WP = WRIST_BRG_OD + BRG_FIT
    WS = WRIST_BRG_OD - 2 * WRIST_BRG_SHOULDER
    cyl = cylinders(f"{CAD}/{part}.step")
    check_count(part, cyl, WP, n_pocket, "bearing pockets (6706)")
    check_depth(part, cyl, WP, WRIST_BRG_W - BRG_CHAMFER, "pocket depth")
    check_count(part, cyl, WS, 1 if part == "wrist_j5_yoke" else n_pocket,
                "through bore")
    check_coaxial(part, cyl, WP, WS, "pocket/bore coaxial")
    if part == "wrist_j5_yoke":
        # The yoke has ONE bore running through both cheeks, with a pocket
        # counterbored into each end. Expecting two separate Ø38 bores was my
        # error, not the part's.
        p = find(cyl, WP)
        if len(p) == 2:
            gap = abs(p[0]["axial"][0] - p[1]["axial"][1])
            gap = min(gap, abs(p[1]["axial"][0] - p[0]["axial"][1]))
            rec(part, "OK" if abs(gap - BRG_SPACING) < 0.1 else "OFFSET",
                "cheek spacing (bearing faces)",
                f"{gap:.2f} mm, expected {BRG_SPACING:.2f}")
    if part == "wrist_j6_output":
        # THREE by design: the servo pocket leaves only ~219 deg of the Ø30
        # circle in material, not the 270 deg four holes at 90 deg would need.
        check_count(part, cyl, M3_CLEAR, 3, "tool-face bolt holes")
        check_count(part, cyl, 10.0, 1, "Ø10 centre pilot")
    return part, cyl


def audit_turret():
    part = "turret_j1"
    cyl = cylinders(f"{CAD}/{part}.step")
    check_count(part, cyl, POCKET, 1, "J1 bearing seat")
    check_depth(part, cyl, POCKET, BRG_W - BRG_CHAMFER, "seat depth")
    return part, cyl


def audit_base():
    part = "base"
    cyl = cylinders(f"{CAD}/{part}.step")
    check_count(part, cyl, 120.0, 1, "foot OD")
    check_count(part, cyl, 52.0, 2, "cable bore (2 faces: shell steps)")
    check_count(part, cyl, POCKET, 1, "J1 bearing seat")
    check_count(part, cyl, 4.5, 4, "M4 bolt-down holes")
    check_coaxial(part, cyl, 52.0, POCKET, "cable bore / J1 seat coaxial")
    return part, cyl


def audit_collar():
    part = "servo_collar"
    cyl = cylinders(f"{CAD}/{part}.step")
    check_count(part, cyl, M3_CLEAR, 6, "servo fixing holes")
    return part, cyl


def audit_coupon():
    part = "fit_coupon"
    cyl = cylinders(f"{CAD}/{part}.step")
    # main row — 6806, J1/J2/J3
    for d in (41.95, 42.00, 42.05):
        check_count(part, cyl, d, 1, f"6806 test pocket Ø{d}", tol=0.015)
    # wrist row — 6706, J4/J5/J6. Absent from the coupon until 2026-09-01:
    # the wrist moved to the smaller bearing and the coupon never followed,
    # so six of the arm's twelve bearings had no fit test.
    for d in (36.95, 37.00, 37.05):
        check_count(part, cyl, d, 1, f"6706 test pocket Ø{d}", tol=0.015)
    check_count(part, cyl, WRIST_BRG_OD - 2 * WRIST_BRG_SHOULDER, 3,
                "6706 seat bores")
    check_count(part, cyl, BRG_OD - 2 * BRG_SHOULDER, 3, "6806 seat bores")
    check_depth(part, cyl, WRIST_BRG_OD, WRIST_BRG_W - BRG_CHAMFER,
                "6706 pocket depth")
    check_depth(part, cyl, BRG_OD, BRG_W - BRG_CHAMFER, "6806 pocket depth")
    for d in (3.9, 4.1, 4.3):
        check_count(part, cyl, d, 1, f"insert test Ø{d}", tol=0.03)
    return part, cyl


def main():
    print("=" * 78)
    print("ARM-450 PART AUDIT — read from the STEP B-rep, part by part")
    print("=" * 78)
    jobs = [lambda: audit_link("tongue"), lambda: audit_link("groove"),
            audit_clamp, audit_collar,
            lambda: audit_wrist("wrist_j4_housing", 1),
            lambda: audit_wrist("wrist_j5_yoke", 2),
            lambda: audit_wrist("wrist_j6_output", 1),
            audit_turret, audit_base, audit_shaft, audit_coupon]
    parts = []
    for j in jobs:
        try:
            parts.append(j())
        except Exception as e:                              # noqa: BLE001
            rec("?", "ERROR", "audit failed", str(e)[:70])
    cur = None
    for p, s, f, d in RES:
        if p != cur:
            print(f"\n{p}")
            cur = p
        mark = {"OK": "  ok  ", "MISSING": " MISS ", "EXTRA": " EXTRA",
                "OFFSET": "OFFSET", "SKIP": " skip ", "ERROR": " ERR  "}[s]
        print(f"  [{mark}] {f:30s} {d}")
    bad = [r for r in RES if r[1] in ("MISSING", "OFFSET", "ERROR")]
    print("\n" + "=" * 78)
    print(f"  {sum(1 for r in RES if r[1]=='OK')} ok   "
          f"{sum(1 for r in RES if r[1]=='EXTRA')} extra   "
          f"{len(bad)} NEED ATTENTION")
    print("=" * 78)
    for p, s, f, d in bad:
        print(f"  {s:8s} {p:20s} {f:28s} {d}")
    return parts


if __name__ == "__main__":
    P = main()
    if "-v" in sys.argv:
        for part, cyl in P:
            dump(part, cyl)
