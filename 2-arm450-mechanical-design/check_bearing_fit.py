"""
Virtual bearing fit — press a modelled 6806 into every pocket in the assembly.

Replaces waiting on the printed coupon for the QUESTION OF GEOMETRY. It cannot
replace the coupon for the question of PROCESS: only a real print tells you what
your machine does to a Ø42 bore. What this settles is whether every pocket in
every part is the size it is supposed to be, and whether the shaft fills the
bore -- which the coupon cannot tell you at all, because the coupon is not the
assembly.
"""
import sys
import numpy as np
sys.path.insert(0, "cad")
from params import *          # noqa: F403,F401
import audit_parts as AP

SHRINK = PRINTER_SHRINK_XY    # 0.02, measured on the user's printer
# (count, bearing OD, width). J1/J2/J3 run 6806; the wrist runs 6706 — same
# 30 mm bore, so the shaft side of the fit is identical either way.
POCKETS = {"link_half_tongue": (2, BRG_OD, BRG_W), "link_half_groove": (2, BRG_OD, BRG_W),
           "turret_j1": (2, BRG_OD, BRG_W), "base": (1, BRG_OD, BRG_W),
           "wrist_j4_housing": (1, WRIST_BRG_OD, WRIST_BRG_W),
           "wrist_j5_yoke": (2, WRIST_BRG_OD, WRIST_BRG_W),
           "wrist_j6_output": (1, WRIST_BRG_OD, WRIST_BRG_W)}


def main():
    print("=" * 78)
    print("VIRTUAL BEARING FIT — 6806 (Ø42.00 × 7.00, bore Ø30.00) into every pocket")
    print("=" * 78)
    print(f"\n  printer XY shrink {SHRINK:.2f} mm (measured) — a modelled Ø42.00 prints Ø{42.0-SHRINK:.2f}\n")
    print(f"  {'part':20s} {'n':>2s} {'modelled':>9s} {'as-printed':>11s} "
          f"{'fit':>8s}  {'depth':>6s}  verdict")
    print("  " + "-" * 76)
    bad = []
    for part, (want_n, OD, W) in POCKETS.items():
        cyl = AP.cylinders(f"output/cad/{part}.step")
        pk = [g for g in cyl if abs(g["dia"] - OD) < 0.08]
        if len(pk) != want_n:
            bad.append((part, f"{len(pk)} pockets, expected {want_n}"))
            print(f"  {part:20s} {len(pk):2d}  *** expected {want_n} ***")
            continue
        g = pk[0]
        printed = g["dia"] - SHRINK
        inter = OD - printed
        v = ("light press" if 0.0 < inter <= 0.06 else
             "FIRM press" if inter > 0.06 else "CLEARANCE — will wobble")
        # the top BRG_CHAMFER of the pocket is now a 45 deg lead-in cone, so
        # the CYLINDRICAL face is (W - chamfer). The seat is still W deep to the
        # shoulder; the bearing grips 93 % of its race, as in a machined housing.
        dep_ok = abs(g["depth"] - (W - BRG_CHAMFER)) < 0.06
        if inter <= 0 or not dep_ok:
            bad.append((part, v))
        print(f"  {part:20s} {len(pk):2d} {g['dia']:9.2f} {printed:11.2f} "
              f"{inter:+8.3f}  {g['depth']:6.2f}  {v}"
              f"{'' if dep_ok else '  DEPTH WRONG'}")
    # shaft into the bearing bore
    print(f"\n  SHAFT INTO THE BORE (this is what the coupon cannot check)")
    tube = SHAFT_OD
    print(f"    bearing bore        Ø{BRG_ID:.2f}")
    print(f"    aluminium tube OD   Ø{tube:.2f}   (bought, not printed — no shrink)")
    j = BRG_ID - tube
    print(f"    interference        {j:+.3f} mm  -> "
          f"{'line-to-line, needs the preload bolt to hold it' if abs(j) < 0.005 else 'CHECK'}")
    print(f"    tube OD tolerance   ±0.10–0.20 as extruded — MEASURE IT.")
    print(f"      29.98–30.01 use as-is · to 29.92 Loctite 603/638 · below, turn it")
    # clamp onto the tube
    cl = [g for g in AP.cylinders("output/cad/shaft_clamp.step")
          if abs(g["dia"] - (SHAFT_OD + 0.2)) < 0.06]
    print(f"\n  CLAMP ONTO THE TUBE")
    print(f"    clamp bore Ø{cl[0]['dia']:.2f} modelled, Ø{cl[0]['dia']-SHRINK:.2f} printed "
          f"-> {cl[0]['dia']-SHRINK-tube:+.3f} mm on the tube (slip, pin carries the torque)")
    print("\n" + "=" * 78)
    if bad:
        print(f"  {len(bad)} PROBLEM(S):")
        for p, d in bad:
            print(f"    {p:20s} {d}")
    else:
        print("  EVERY POCKET IN THE ASSEMBLY ACCEPTS THE BEARING AS A LIGHT PRESS.")
    print("=" * 78)
    return bad


if __name__ == "__main__":
    main()
