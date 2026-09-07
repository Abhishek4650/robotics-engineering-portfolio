"""
Does the sealed docking target still dock, and does the seal actually seal?

Two separate questions and they are easy to conflate. The groove is 0.45 mm
deep in a spigot that has to slide through a Ø16 bore, so:

  * it must not foul the throat, the latch, or the entry slots
  * the ORIGINAL unsealed target must still work, unchanged
  * the squeeze that a PRINTED bore actually delivers is the open question
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "cad"))
import end_effector as EE

R = []


def chk(ok, name, det):
    R.append((bool(ok), name, det))


def mate(target_stl, rot, gap, dx=0.0):
    P = trimesh.load(os.path.join(HERE, "output/cad/tool_dock.stl"), force="mesh")
    T = trimesh.load(os.path.join(HERE, "output/cad", target_stl), force="mesh")
    T.apply_transform(trimesh.transformations.rotation_matrix(
        np.radians(rot), [0, 0, 1]))
    T.apply_translation([dx, 0, EE.SEAT_DZ - EE.FLANGE_H - gap])
    m = trimesh.collision.CollisionManager()
    m.add_object("p", P); m.add_object("t", T)
    return m.in_collision_internal()


def main():
    print("=" * 78)
    print("SEALED DOCKING TARGET — verification")
    print("=" * 78)

    # --- the groove itself
    print(f"\n  O-ring groove, from cad/end_effector.py")
    print(f"    cord            {EE.SEAL_CORD:.2f} mm")
    print(f"    groove Ø        {EE.SEAL_GROOVE_D:.2f}   (spigot Ø{2*EE.SPG_R:.2f})")
    print(f"    depth           {(2*EE.SPG_R - EE.SEAL_GROOVE_D)/2:.2f} mm")
    print(f"    width           {EE.SEAL_GROOVE_W:.2f} mm")
    print(f"    at s            {EE.SEAL_Z:.1f}  (plain band is {-EE.SEAT_DZ:.1f} .. {EE.GRV_Z0:.1f})")
    wall = EE.SEAL_GROOVE_D / 2 - EE.FLUID_BORE / 2
    chk(wall >= 2.0, "spigot wall survives the seal groove",
        f"{wall:.2f} mm between the groove root and the Ø{EE.FLUID_BORE:.0f} fluid bore")
    lo = EE.SEAL_Z - EE.SEAL_GROOVE_W / 2
    hi = EE.SEAL_Z + EE.SEAL_GROOVE_W / 2
    chk(lo > -EE.SEAT_DZ, "groove is fully inside the straight throat",
        f"starts at s {lo:.2f}, throat entry at s {-EE.SEAT_DZ:.1f}")
    chk(hi < EE.GRV_Z0, "groove clears the capture groove",
        f"ends at s {hi:.2f}, capture groove starts at s {EE.GRV_Z0:.1f}")

    # --- both targets must still dock
    print("\n  DOCKING, both variants")
    for name, stl in (("original", "dock_target.stl"),
                      ("sealed  ", "dock_target_sealed.stl")):
        cases = [("6 mm short", 0.0, 6.0, False),
                 ("seated", 0.0, 0.0, False),
                 (f"latched {EE.DOCK_TWIST:.0f}°", EE.DOCK_TWIST, 0.0, False),
                 ("latched, pulled 2 mm", EE.DOCK_TWIST, 2.0, True),
                 ("unlatched, withdrawn", 0.0, 6.0, False)]
        bad = 0
        for lab, rot, gap, want in cases:
            got = mate(stl, rot, gap)
            bad += (got != want)
        chk(bad == 0, f"{name} target completes the full mate cycle",
            f"5/5 states as expected" if bad == 0 else f"{bad} state(s) wrong")

    # --- squeeze, and what a printed bore does to it
    print("\n  SQUEEZE — the number the seal lives or dies by")
    nom_gap = (EE.DOCK_THROAT - EE.SEAL_GROOVE_D) / 2
    print(f"    nominal radial gap  {nom_gap:.3f} mm   cord {EE.SEAL_CORD:.2f}")
    print(f"    nominal squeeze     {(EE.SEAL_CORD-nom_gap)/EE.SEAL_CORD*100:.0f} %")
    print(f"\n    {'bore error':>12s} {'gap':>8s} {'squeeze':>9s}   verdict")
    print("    " + "-" * 50)
    worst = []
    for err in (-0.20, -0.10, -0.05, 0.00, +0.05, +0.10, +0.20):
        gap = nom_gap + err / 2.0
        sq = (EE.SEAL_CORD - gap) / EE.SEAL_CORD * 100
        v = ("LEAKS" if sq < 8 else
             "crushed" if sq > 35 else "ok")
        worst.append(sq)
        print(f"    {err:+11.2f} {gap:8.3f} {sq:8.0f} %   {v}")
    chk(min(worst) >= 8.0, "seal survives a ±0.20 mm printed bore error",
        f"squeeze range {min(worst):.0f}–{max(worst):.0f} % across ±0.20 mm")

    print()
    for ok, name, det in R:
        print(f"  [{' PASS ' if ok else ' FAIL '}] {name:46s} {det}")
    bad = [r for r in R if not r[0]]
    print("\n" + "=" * 78)
    print(f"  {len(R)-len(bad)} passed, {len(bad)} failed")
    print("=" * 78)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
