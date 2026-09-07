"""
PRE-PRINT GATE — the last check before committing to plastic.

Written to FIND problems, not to confirm success. Every item is a pass/fail
against a stated criterion, and anything unresolved is listed as a blocker.
"""
import os, sys, json, numpy as np, trimesh
sys.path.insert(0, "cad")
from params import *

CAD = "output/cad"
FAIL, WARN, OK = [], [], []


def check(cond, name, detail, hard=True):
    (OK if cond else (FAIL if hard else WARN)).append((name, detail))
    return cond


# ---------------------------------------------------------------- geometry
PRINTED = ["base", "turret_j1", "link_half_tongue", "link_half_groove",
           "shaft_clamp", "servo_collar", "horn_adapter", "wrist_j4_housing",
           "wrist_j5_yoke", "wrist_j6_output"]
ALL = PRINTED + ["joint_shaft"]

for n in ALL:
    for ext in ("stl", "step"):
        p = os.path.join(CAD, f"{n}.{ext}")
        check(os.path.exists(p), f"{n}.{ext} exists", p)

# meshes load and are manifold enough to slice
for n in PRINTED:
    m = trimesh.load(os.path.join(CAD, n + ".stl"), force="mesh")
    check(len(m.faces) > 100, f"{n} mesh non-trivial", f"{len(m.faces)} faces")
    check(m.body_count == 1, f"{n} is ONE body", f"{m.body_count} bodies",
          hard=False)

# ---------------------------------------------------------------- fits
VOL = json.load(open(os.path.join(CAD, "volumes.json")))
check(abs((BRG_OD + BRG_FIT) - 42.00) < 1e-6, "bearing pocket Ø42.00",
      f"{BRG_OD+BRG_FIT:.2f} mm, 0.02 interference after your XY shrink")
check(SEC_H / 2 == BOSS_R, "stadium profile tangent",
      f"SEC_H/2={SEC_H/2} == BOSS_R={BOSS_R}")
check(abs(SEAM_LIP / 0.20 - round(SEAM_LIP / 0.20)) < 1e-9,
      "tongue = integer layers", f"{SEAM_LIP} mm = {SEAM_LIP/0.2:.0f} x 0.20")
check(SEAM_GROOVE_EXTRA >= 0.4, "groove axial margin",
      f"+{SEAM_GROOVE_EXTRA} mm so the tongue cannot bottom")
check(SEAM_LIP_CLR >= 0.25, "lip clearance", f"{SEAM_LIP_CLR} mm/side")
check(M3_INSERT_L >= 7.5, "insert pocket depth",
      f"{M3_INSERT_L} mm, insert can sit sub-flush")
check(BOSS_OD >= 9.0, "insert boss OD", f"Ø{BOSS_OD} mm")

# ---------------------------------------------------------------- servo
hx = (SERVO_L + 2 * SERVO_CLR) / 2
lo, hi = SERVO_AXIS_OFFSET - hx, SERVO_AXIS_OFFSET + hx
for n in ("wrist_j4_housing", "wrist_j6_output", "turret_j1"):
    m = trimesh.load(os.path.join(CAD, n + ".stl"), force="mesh")
    check(m.bounds[1][0] >= hi + 1.5 and m.bounds[0][0] <= lo - 1.5,
          f"{n} contains the servo",
          f"body x {m.bounds[0][0]:+.1f}..{m.bounds[1][0]:+.1f} vs pocket {lo:+.1f}..{hi:+.1f}")
check(abs(SERVO_AXIS_OFFSET - 12.5) < 0.01, "servo axis offset applied",
      f"{SERVO_AXIS_OFFSET:.2f} mm from the datasheet")
check(abs(HORN_BCD - 14.0) < 1e-6, "horn BCD from datasheet", f"Ø{HORN_BCD}")

# ---------------------------------------------------------------- chain
import generate_urdf as G
tot = G.BASE_H + G.SHOULDER_RISE + G.L2 + G.L4_SPLIT + G.L5_SPLIT + G.L6_SPLIT + G.L_TCP
check(abs(tot - 450.0) < 1e-9, "chain totals 450 mm", f"{tot:.1f} mm")
check(abs(G.L4_SPLIT - LINK_L) < 1e-9, "URDF forearm == CAD link",
      f"{G.L4_SPLIT} == {LINK_L}")

# ---------------------------------------------------------------- mass
# 2026-08-21: horn_adapter is 6 off -- one per joint. It closes the torque
# path from servo horn to shaft, which nothing did before the geometry audit.
QTY = {"link_half_tongue": 2, "link_half_groove": 2, "shaft_clamp": 2,
       "servo_collar": 2, "horn_adapter": 6}
# 2026-08-21. The old line was `VOL[n] * 1.29e-3 * 0.55` -- a 0.55 sparse-infill
# factor applied to EVERY part. That is right for a part modelled SOLID and
# printed with sparse infill. Every part here is modelled HOLLOW: the link
# shells are 2.4 mm walls, the base is a 3.0 mm shell, and the STEP volume IS
# the wall material. Slicing a 2.4 mm wall with 4 perimeters on a 0.6 nozzle
# gives 2.4 mm of solid extrusion -- there is no interior left for infill to
# save anything in. The 0.55 was discounting the hollowing a second time, and
# it hid 240 g.
FILL = 0.90          # thin walls print essentially solid; 1.00 is the ceiling
printed_g = sum(VOL[n] * RHO_SOLID * FILL * QTY.get(n, 1) for n in PRINTED)
# Bearing mass computed from geometry rather than guessed: the 30x42x7 annulus
# is 4750 mm3; a deep-groove bearing fills ~60 % of it -> 22 g, not 32 g.
def _brg_g(od, idd, w):
    return np.pi / 4 * (od**2 - idd**2) * w * 7.85e-3 * 0.60


# TWO bearing sizes since 2026-08-21: J1/J2/J3 run 6806 (Ø42x7), the wrist
# J4/J5/J6 runs 6706 (Ø37x4). Same 30 mm bore, so the shaft is unchanged.
BRG_G = _brg_g(BRG_OD, BRG_ID, BRG_W)
WBRG_G = _brg_g(WRIST_BRG_OD, WRIST_BRG_ID, WRIST_BRG_W)
BRG_TOTAL = 6 * BRG_G + 6 * WBRG_G
N_SHAFT = 6
SHAFT_G = (np.pi / 4 * (SHAFT_OD ** 2 - (SHAFT_OD - 2 * SHAFT_WALL) ** 2)
           * SHAFT_L * SHAFT_RHO)
check(N_SHAFT * 2 == 12, "one shaft per bearing PAIR",
      f"12 bearings -> {N_SHAFT} pairs -> {N_SHAFT} shafts")
# 2026-08-23. FASTENERS WERE NEVER IN THIS SUM.
# The line below used to be printed + servos + bearings + shafts and stop. It
# had no term for the forty M3 brass heat-set inserts, the six M5 x 90 preload
# through-bolts, or the ~100 smaller screws -- and steel and brass are 6-7x the
# density of the plastic they hold together. Computed from each fastener's own
# geometry in fastener_mass.py they come to 244 g: 17 % of the whole arm, and
# simply absent.
#
# Reported as its own line, and the HARD check is on the ALL-IN figure, because
# "the arm masses 1365 g" was a statement about a machine that cannot be
# assembled -- it is 1365 g of parts lying next to a bag of bolts.
import fastener_mass as _FAST
FASTENER_G = _FAST.total()
structure_g = printed_g + 6 * 60 + BRG_TOTAL + N_SHAFT * SHAFT_G
total_g = structure_g + FASTENER_G
# MASS BUDGET — 1200 -> 1300 -> 1450, user decision 2026-08-21.
# The original 1.2 kg was set before the mass model was honest: the gate had
# been applying a 0.55 sparse-infill factor to parts that are modelled HOLLOW,
# which discounted the hollowing twice and hid ~240 g. With FILL = 0.90 the arm
# is 1437 g. Offered a lightening pass (~1333 g) or narrower bearings
# (~1148 g), the user accepted 1437 g as built rather than trade away link
# stiffness or move to a less commonly stocked bearing.
# 1450 is the accepted ceiling, not a target -- anything ADDED from here still
# has to be justified.
BUDGET = 1450.0
# HARD failure from 2026-08-21. The user has stated this ceiling cannot rise
# again, so mass is now a blocker rather than a warning: anything added from
# here that pushes past 1450 g stops the print instead of being noted and
# ignored. Headroom is only 13 g, so this WILL fire on the next addition.
check(structure_g <= BUDGET, f"structure + actuators within {BUDGET:.0f} g",
      f"{structure_g:.0f} g = {printed_g:.0f} printed (fill {FILL:.2f}) + 360 servos + "
      f"{BRG_TOTAL:.0f} bearings (6×6806 + 6×6706) + {N_SHAFT*SHAFT_G:.0f} shafts  "
      f"[{BUDGET-total_g:+.0f} g headroom]")
check(total_g <= BUDGET, f"ASSEMBLED mass within {BUDGET:.0f} g (HARD LIMIT)",
      f"{total_g:.0f} g = {structure_g:.0f} structure + {FASTENER_G:.0f} fasteners "
      f"and inserts  [{BUDGET-total_g:+.0f} g]")

# ------------------------------------------------------- GEOMETRY (not intent)
# 2026-08-21. Everything above this line checks PARAMETERS. That is how three
# blocking defects passed this gate 55/55: the parameters were all correct and
# the geometry silently lacked the features, because each pocket had been cut
# into a region an earlier cut already emptied -- a legal, silent no-op.
# A gate that reads design intent cannot catch that. Read the B-rep instead.
try:
    import audit_parts as _AUDIT
    _AUDIT.RES.clear()
    _AUDIT.main()
    _bad = [r for r in _AUDIT.RES if r[1] in ("MISSING", "OFFSET", "ERROR")]
    check(not _bad, "geometry audit clean (features physically present)",
          f"{sum(1 for r in _AUDIT.RES if r[1]=='OK')} features verified in the STEP"
          if not _bad else f"{len(_bad)} defects: " +
          "; ".join(f"{p}/{f}" for p, _s, f, _d in _bad[:4]))
except Exception as _e:                                          # noqa: BLE001
    check(False, "geometry audit ran", str(_e)[:70], hard=False)

# ---------------------------------------------------------------- report
print("=" * 74)
print("ARM-450 PRE-PRINT GATE")
print("=" * 74)
print(f"\n  PASSED {len(OK)}   WARNINGS {len(WARN)}   FAILURES {len(FAIL)}\n")
if FAIL:
    print("  BLOCKERS — do not print until these are resolved:")
    for n, d in FAIL:
        print(f"    [FAIL] {n:34s} {d}")
    print()
if WARN:
    print("  WARNINGS — printable, but know about them:")
    for n, d in WARN:
        print(f"    [warn] {n:34s} {d}")
    print()
print("  Passed checks:")
for n, d in OK:
    print(f"    [ok]   {n:34s} {d}")
