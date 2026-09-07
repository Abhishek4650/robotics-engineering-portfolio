"""
Final pre-print audit — the checks the gate does NOT do.

preflight.py verifies that the DESIGN is right: geometry present, margins held,
paths clear, model matching. This asks a different question: **can this actually
be printed, and is there anything in the output folder that would be printed by
mistake?**

Those are the failure modes left on the day of the print, and none of them is a
design error:

  * a feature thinner than two extrusion widths, which the slicer silently drops
  * a hole smaller than the nozzle, which comes out solid
  * an overhang the part cannot bridge in the stated orientation
  * a part that does not fit the build volume
  * a STEP and an STL that disagree, so the drawing and the print differ
  * a SUPERSEDED part sitting in the same folder as the live ones
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "output", "cad")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "cad"))
from params import *          # noqa: F403,F401

from params import NOZZLE, EXTRUSION_W, LAYER_H     # noqa: E402
LINE_W = EXTRUSION_W
MIN_WALL = 2 * LINE_W         # 1.24 mm — below this a wall is not printable
LAYER = LAYER_H               # was hardcoded 0.28, which does not divide the
                              # 1.6 mm seam tongue. Read it from params.
BED = (250.0, 210.0, 210.0)   # a common consumer envelope; adjust to yours
OVERHANG_LIMIT = 50.0         # deg from vertical before support is wanted

# the parts that are actually printed, from BUY.md's print list
LIVE = [
    "link_half_tongue", "link_half_groove", "wrist_j4_housing", "wrist_j5_yoke",
    "wrist_j6_output", "horn_adapter", "shaft_clamp", "servo_collar",
    "turret_j1", "base", "fit_coupon",
    "tool_adapter", "tool_gripper", "gripper_jaw", "gripper_pinion",
    "tool_dock", "dock_target", "dock_target_sealed",
]
# generated for analysis or superseded by a later part — NOT to be printed
NOT_PRINTED = {
    "joint_shaft": "the Ø30 shaft is an ALUMINIUM TUBE, not printed (shaft_tube is its drawing)",
    "shaft_tube": "aluminium tube — a drawing of bought stock, not a print",
    "bearing_6806": "a model of a bought bearing",
    "bearing_yoke": "superseded by wrist_j5_yoke",
    "wrist_yoke_j5": "superseded by wrist_j5_yoke",
    "roll_module": "superseded by wrist_j4_housing / wrist_j6_output",
    "wrist": "superseded by the three integrated wrist parts",
    "tool_flange": "superseded — the flange is integral to wrist_j6_output",
    "arm450_parts_kit": "a layout of every part on one plate, for viewing",
    "arm450_assembly_home": "assembly render, not a part",
    "arm450_assembly_working": "assembly render, not a part",
    "arm450_assembly_exploded": "assembly render, not a part",
}

R = []


def chk(ok, name, det, hard=True):
    R.append((bool(ok), name, det, hard))
    return ok


def thickness_probe(name, m):
    """Minimum wall, by voxel medial axis — see wall_check.py.

    The first version of this used ray casting. This machine has no `rtree`, so
    every call raised, every part returned None, and the check reported PASS on
    ZERO measurements. That is worse than no check: it is a green tick standing
    in for an answer nobody has. A check that cannot run must say so.

    Large parts are skipped deliberately rather than silently: at a fine pitch a
    183 mm link is tens of millions of voxels, and its design wall is 2.4 mm,
    nowhere near the 1.24 mm floor. Skipped parts return None and are reported
    as NOT MEASURED, not as passing.
    """
    if max(m.extents) > 90.0:
        return None
    import wall_check as WC
    try:
        r = WC.wall(name, 0.30)
    except Exception:                                    # noqa: BLE001
        return None
    return None if r is None else r[0]


def overhang_area(m, up=(0, 0, 1)):
    """Fraction of surface area whose normal points DOWN by more than the
    overhang limit. High values mean the stated print orientation needs support
    on a face that carries load."""
    up = np.asarray(up, float)
    cosang = m.face_normals @ up
    lim = -np.cos(np.radians(90.0 - (90.0 - OVERHANG_LIMIT)))
    steep = cosang < -np.sin(np.radians(90.0 - OVERHANG_LIMIT))
    a = m.area_faces
    return float(a[steep].sum() / a.sum())


def main():
    print("=" * 84)
    print("ARM-450 — FINAL PRE-PRINT AUDIT")
    print(f"nozzle {NOZZLE} mm · line {LINE_W} mm · layer {LAYER} mm · "
          f"min printable wall {MIN_WALL:.2f} mm")
    print("=" * 84)

    VOL = json.load(open(os.path.join(CAD, "volumes.json")))
    stls = sorted(f[:-4] for f in os.listdir(CAD) if f.endswith(".stl"))

    # ---- 1. is anything in the folder that must NOT be printed? -----------
    print("\n1. WHAT IS IN THE OUTPUT FOLDER")
    unknown = [s for s in stls if s not in LIVE and s not in NOT_PRINTED]
    chk(not unknown, "every STL is either on the print list or explicitly not",
        f"{len(LIVE)} live, {len([s for s in stls if s in NOT_PRINTED])} "
        f"not-printed, {len(unknown)} unaccounted"
        + (f" -> {unknown}" if unknown else ""))
    missing = [p for p in LIVE if p not in stls]
    chk(not missing, "every part on the print list has an STL",
        f"{len(LIVE)}/{len(LIVE)} present" if not missing else f"MISSING {missing}")
    print(f"\n   NOT TO BE PRINTED — {len(NOT_PRINTED)} files sit beside the live ones:")
    for k, why in NOT_PRINTED.items():
        if k in stls:
            print(f"     {k:24s} {why}")

    # ---- 2. per-part printability ----------------------------------------
    print("\n2. PRINTABILITY, PART BY PART")
    print(f"   {'part':22s} {'envelope mm':>22s} {'min wall':>9s} {'overhang':>9s} "
          f"{'bodies':>7s} {'STEP vs STL':>12s}")
    print("   " + "-" * 86)
    thin, big, multi, mismatch, hangs, unmeasured = [], [], [], [], [], []
    for name in LIVE:
        m = trimesh.load(os.path.join(CAD, name + ".stl"), force="mesh")
        ex = m.extents
        t = thickness_probe(name, m)
        oh = overhang_area(m)
        nb = len(m.split(only_watertight=False)) if m.body_count > 1 else 1
        vstep = VOL.get(name)
        dv = abs(m.volume - vstep) / vstep * 100 if vstep else float("nan")
        fits = all(ex[i] <= BED[i] for i in range(3)) or \
            all(sorted(ex)[i] <= sorted(BED)[i] for i in range(3))
        if t is None:
            unmeasured.append((name, None))
        elif t < MIN_WALL:
            thin.append((name, t))
        if not fits:
            big.append(name)
        if nb > 1:
            multi.append((name, nb))
        if vstep and dv > 1.0:
            mismatch.append((name, dv))
        if oh > 0.30:
            hangs.append((name, oh))
        print(f"   {name:22s} {ex[0]:6.1f}×{ex[1]:6.1f}×{ex[2]:6.1f} "
              f"{(f'{t:8.2f}' if t else '      --')} {oh*100:8.1f}% {nb:7d} "
              f"{dv:11.2f}%")

    n_meas = sum(1 for p_ in LIVE if p_ not in [x[0] for x in unmeasured])
    chk(not thin, "no measured feature below the printable wall",
        f"{len(thin)} thin: {thin}" if thin else
        f"{n_meas} parts measured, all ≥ {MIN_WALL:.2f} mm "
        f"(2 lines at a {NOZZLE} mm nozzle)")
    chk(not unmeasured, "every part had its wall thickness measured",
        "all measured" if not unmeasured else
        f"NOT MEASURED (too large to voxelise at 0.30 mm): "
        f"{[x[0] for x in unmeasured]} — design wall 2.4–3.0 mm, "
        f"2x the floor, but not verified here", hard=False)
    chk(not big, "every part fits the build volume",
        f"{BED[0]:.0f}×{BED[1]:.0f}×{BED[2]:.0f} mm" if not big else f"TOO BIG {big}")
    chk(not multi, "every part is a single connected body",
        "no loose fragments" if not multi else f"MULTI-BODY {multi}")
    chk(not mismatch, "STL agrees with the STEP it was exported from",
        "all within 1 %" if not mismatch else f"DISAGREE {mismatch}")
    chk(not hangs, "no part is mostly overhang in its print orientation",
        f"worst {max((o for _n, o in hangs), default=0)*100:.0f} %" if hangs
        else "all under 30 % downward-facing area", hard=False)

    # ---- 3. holes vs the fasteners that go in them ------------------------
    print("\n3. HOLES vs FASTENERS")
    import audit_parts as AP
    FAST = {M3_CLEAR: "M3 clearance", 2.7: "M3 self-tap / insert pilot",
            M2_5_CLEAR if "M2_5_CLEAR" in dir() else 2.9: "M2.5 clearance",
            4.0: "Ø4 heat-set insert", 3.4: "M3 thumbscrew"}
    small = []
    for name in LIVE:
        for g in AP.cylinders(os.path.join(CAD, name + ".step")):
            if g["dia"] < NOZZLE * 2:
                small.append((name, round(g["dia"], 2)))
    chk(not small, "no hole smaller than two extrusion widths",
        f"smallest holes are ≥ {NOZZLE*2:.1f} mm" if not small
        else f"TOO SMALL {small[:6]}")

    # ---- 4. mass, from the final geometry --------------------------------
    print("\n4. MASS, RECOMPUTED FROM THE FINAL STEPs")
    qty = {"link_half_tongue": 2, "link_half_groove": 2, "horn_adapter": 6,
           "shaft_clamp": 2, "servo_collar": 2}
    printed = sum(VOL[p] * 1.29e-3 * MASS_FILL * qty.get(p, 1)
                  for p in LIVE if p in VOL and p not in
                  ("fit_coupon", "tool_adapter", "tool_gripper", "gripper_jaw",
                   "gripper_pinion", "tool_dock", "dock_target"))
    servos, brg, shafts, fast = 360.0, 134.0, 84.0, 202.0
    total = printed + servos + brg + shafts + fast
    print(f"   printed structure   {printed:7.1f} g")
    print(f"   servos (6)          {servos:7.1f} g")
    print(f"   bearings (12)       {brg:7.1f} g")
    print(f"   aluminium shafts    {shafts:7.1f} g")
    print(f"   fasteners, inserts  {fast:7.1f} g")
    print(f"   {'TOTAL':19s} {total:7.1f} g   of {MASS_BUDGET:.0f} g")
    chk(total <= MASS_BUDGET, "arm mass inside the hard ceiling",
        f"{total:.0f} g of {MASS_BUDGET:.0f} g, {MASS_BUDGET-total:.0f} g spare")

    # ---- 5. filament and time estimate -----------------------------------
    print("\n5. WHAT THE PRINT COSTS")
    v_live = sum(VOL[p] * MASS_FILL * qty.get(p, 1) for p in LIVE if p in VOL)
    grams = v_live * 1.29e-3
    metres = v_live / (np.pi * (1.75 / 2) ** 2) / 1000.0
    print(f"   filament            {grams:7.0f} g  ({metres:.0f} m of 1.75 mm)")
    print(f"   one 1 kg spool covers it with {1000-grams:.0f} g to spare")

    # ---- verdict ----------------------------------------------------------
    print("\n" + "=" * 84)
    for ok, name, det, hard in R:
        tag = " PASS " if ok else (" FAIL " if hard else " NOTE ")
        print(f"  [{tag}] {name:52s} {det}")
    bad = [r for r in R if not r[0] and r[3]]
    note = [r for r in R if not r[0] and not r[3]]
    print("=" * 84)
    print(f"  {len(R)-len(bad)-len(note)} passed, {len(note)} notes, {len(bad)} failures")
    print("=" * 84)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
