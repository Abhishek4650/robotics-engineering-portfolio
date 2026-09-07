"""
Why the joints have visible gaps, wobble, and small oscillations.

User's observation (from the printed hardware, 2026-08-13):
  "between two link joints I see some gaps due to inserting thrust ball bearings
   or similar components ... visible gaps that produce wobbling and has elastic
   nature, it even does small oscillations"

There are THREE separate causes stacked on top of each other. Only one of them
is a printing problem; the other two are design choices.
"""

import numpy as np

REACH = 360.0                # mm, TCP from J1 axis
TAU_J2 = 2.08                # N.m gravity torque at the shoulder
TAU_STALL = 2.94             # N.m ST3215 stall

# the bearing actually used, measured from thrust ball bearing.stl
BRG_OD, BRG_TH = 42.0, 3.7   # mm — a thin thrust washer type


# ===========================================================================
print("=" * 80)
print("CAUSE 1 — a thrust bearing has ZERO moment capacity")
print("=" * 80)
print(f"The bearing in the design is Ø{BRG_OD:.0f} x {BRG_TH:.1f} mm — a thin THRUST")
print("washer type. A thrust ball bearing is designed to carry AXIAL load only:")
print("balls run between two flat races, so the joint is free to TILT.")
print()
print("But a robot joint does not mainly carry axial load. It carries a BENDING")
print("MOMENT — the weight of everything outboard acting on a long lever arm:")
print(f"   moment at the shoulder = {TAU_J2:.2f} N.m (gravity), {TAU_STALL:.2f} N.m (stall)")
print()
print("A single thrust washer resists NONE of that. The joint tilts until")
print("something else stops it — usually the printed bore rubbing on the shaft.")
print("That is exactly what 'visible gap + wobble' looks like.")

# ===========================================================================
print("\n" + "=" * 80)
print("CAUSE 2 — angular play from clearance, amplified by the 360 mm arm")
print("=" * 80)
print("A joint with radial clearance c and bearing SPACING d has angular play")
print("   theta = 2c / d          (two bearings, worst case both at their limit)")
print("and that projects to the tool as  delta = reach * tan(theta).\n")

print(f"{'spacing d':>10s} " + "".join(f"{f'c={c} mm':>13s}" for c in (0.05, 0.10, 0.20)))
print("-" * 80)
for d in (5.0, 10.0, 20.0, 40.0, 60.0):
    row = ""
    for c in (0.05, 0.10, 0.20):
        th = 2 * c / d
        row += f"{REACH*np.tan(th):10.2f} mm"
    print(f"{d:8.0f} mm {row}")

print("\n-> a SINGLE bearing (or two stacked together, d ~ 5 mm) turns 0.1 mm of")
print("   clearance into ~7 mm of wobble at the tool.")
print("-> the same clearance with bearings spaced 40 mm apart gives ~0.9 mm.")
print("   MOMENT STIFFNESS SCALES WITH SPACING SQUARED. Spacing is the whole game.")

# ===========================================================================
print("\n" + "=" * 80)
print("CAUSE 3 — FDM holes print undersize, so the bearing never seats flat")
print("=" * 80)
print("On an FDM printer a circular pocket comes out SMALLER than modelled,")
print("typically by 0.1-0.4 mm on diameter, because the extrudate is laid on the")
print("inside of the curve and the polymer shrinks as it cools.")
print()
print("If a Ø42.0 bearing is pressed into a pocket modelled at Ø42.0, the real")
print("pocket is ~Ø41.7 and the bearing either will not go in, or goes in cocked")
print("and sits proud — leaving the visible gap between the mating faces.")
print()
print("Recommended modelled pocket diameters for a Ø42.0 bearing:")
for fit, extra, note in ((("press fit"), 0.15, "bearing stays put, needs a press"),
                         (("slip fit"), 0.30, "slides in, needs a retaining lip/screw"),
                         (("loose"), 0.50, "AVOID — this is where wobble comes from")):
    print(f"   {fit:10s} model Ø{BRG_OD+extra:.2f} mm   ({extra:+.2f})  {note}")
print()
print("Always print a 15 mm test coupon with the pocket first and measure it.")
print("Printer-to-printer variation is larger than any number quoted here.")

# ===========================================================================
print("\n" + "=" * 80)
print("CAUSE 4 (consequence) — why it OSCILLATES")
print("=" * 80)
print("Clearance in a position-controlled joint is a dead zone: the servo turns")
print("but the link does not move until the slack is taken up, then it moves")
print("suddenly. A feedback controller pushing against a dead zone produces a")
print("LIMIT CYCLE — a small steady oscillation that never settles. That is the")
print("'small oscillation' being observed, and no amount of gain tuning removes")
print("it. The fix is mechanical: remove the clearance with PRELOAD.")

# ===========================================================================
print("\n" + "=" * 80)
print("THE FIX")
print("=" * 80)
print("""
1. REPLACE the single thrust washer with a pair of DEEP-GROOVE ball bearings
   spaced as far apart as the joint allows. Two 6808 (40x52x7) or 6704
   (20x27x4) bearings 30-40 mm apart give real moment stiffness.
   Alternative single-bearing option: a 4-point-contact or crossed-roller
   bearing, which takes moment on its own — more expensive, more compact.

2. PRELOAD the pair with a screw pulling the inner races together against a
   spacer. Preload removes the clearance that causes both the wobble and the
   limit-cycle oscillation. This is the single most important change.

3. Model the pocket +0.15 mm on diameter for a press fit, and add a 0.5 x 45
   chamfer at the pocket mouth so the bearing starts square.

4. Give the bearing a SHOULDER to seat against, not a flat face. A bearing
   pressed against a flat printed surface sits on whatever high spots exist;
   a turned shoulder locates it axially and squarely.

5. Print the bearing bore VERTICALLY (axis parallel to the build Z axis) so the
   bore is defined by the XY motion of the nozzle, which is far rounder than a
   bore built up in layers on its side.
""")

# ===========================================================================
print("=" * 80)
print("WHAT THE FIX IS WORTH — total TCP error before and after")
print("=" * 80)
before = REACH * np.tan(2 * 0.20 / 5.0)      # loose, single bearing
after = REACH * np.tan(2 * 0.02 / 40.0)      # preloaded pair, 40 mm apart
print(f"  now:   loose fit (c=0.20), effectively single bearing (d=5 mm)  "
      f"-> {before:6.1f} mm")
print(f"  fixed: preloaded pair (c=0.02), spaced 40 mm                    "
      f"-> {after:6.2f} mm")
print(f"  improvement: {before/after:.0f}x")
print("\nCompare with the other error sources already quantified:")
print("  servo backlash 0.5 deg .......... 3.14 mm")
print("  unbolted clamshell seam ......... 2.84 mm")
print("  elastic droop (PLA, t=2.0) ...... 0.57 mm")
print("\n-> joint clearance is currently the LARGEST error source in the arm,")
print("   bigger than backlash. It is also the cheapest to fix.")
