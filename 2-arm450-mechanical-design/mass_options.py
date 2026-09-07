"""
Getting back under the 1450 g ceiling.

fastener_mass.py found the gate omits fasteners entirely and the real arm is
1608 g — 158 g over a ceiling the project has already agreed cannot move again.
This costs the options out. Each row is a change that can be made without
touching a printed part, so none of them invalidates the verification already
done; the last group does touch printed parts and is listed separately because
it would.
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fastener_mass as F

RHO = {"steel": 7.85e-3, "titanium": 4.43e-3, "aluminium": 2.70e-3,
       "brass": 8.50e-3, "nylon": 1.15e-3}

GATE = 1364.75
CEIL = 1450.0
BASE_TOTAL = GATE + F.total()


def opt(label, saving, risk, touches_print=False):
    return dict(label=label, save=saving, risk=risk, print=touches_print)


def main():
    print("=" * 88)
    print("GETTING BACK UNDER 1450 g")
    print("=" * 88)
    print(f"\n  starting point   {BASE_TOTAL:7.1f} g   ({GATE:.0f} gate + "
          f"{F.total():.0f} fasteners)")
    print(f"  ceiling          {CEIL:7.1f} g")
    print(f"  must remove      {BASE_TOTAL - CEIL:7.1f} g\n")

    # --- changes that touch NO printed part -------------------------------
    m5_steel = 6 * F.cap_screw(5.0, 90)
    m5_ti = 6 * F.cap_screw(5.0, 90, RHO["titanium"])
    m4_steel = 6 * F.cap_screw(4.0, 90)
    shim_steel = 6 * F.tube(36, 30, 2) * RHO["steel"]
    shim_al = 6 * F.tube(36, 30, 2) * RHO["aluminium"]
    wash_steel = 30 * F.washer(3.0)
    wash_ny = 30 * F.washer(3.0, RHO["nylon"])
    m3_20_steel = 24 * F.cap_screw(3.0, 20)
    m3_20_ti = 24 * F.cap_screw(3.0, 20, RHO["titanium"])

    A = [
        opt("bearing shims steel → ALUMINIUM (they only carry compression)",
            shim_steel - shim_al, "none — a spacer in pure compression"),
        opt("M5 × 90 preload bolt → TITANIUM grade 5",
            m5_steel - m5_ti,
            "none mechanically; Ti M5 is ~10× the price and needs sourcing"),
        opt("M5 × 90 → M4 × 90 preload bolt",
            m5_steel - m4_steel,
            "CHECK FIRST: preload sets the bearing pair. M4 has 64 % of M5's "
            "tensile area, so the same torque gives less clamp"),
        opt("M3 washers → nylon", wash_steel - wash_ny,
            "none — they only spread head load"),
        opt("M3 × 20 seam screws → titanium", m3_20_steel - m3_20_ti,
            "none mechanically; 24 off, cost adds up"),
    ]
    print("  A. NO PRINTED PART CHANGES — the verification already done still stands")
    print(f"     {'change':62s} {'saves g':>8s}")
    print("     " + "-" * 72)
    for o in A:
        print(f"     {o['label']:62s} {o['save']:8.1f}")
        print(f"       └ {o['risk']}")
    print(f"     {'A TOTAL (all of them)':62s} {sum(o['save'] for o in A):8.1f}")

    combo = shim_steel - shim_al
    # The two preload-bolt options are MUTUALLY EXCLUSIVE -- one bolt, one
    # spec. Summing both was a double count that made the total look reachable.
    EXCLUSIVE = {"M5 × 90 preload bolt → TITANIUM grade 5",
                 "M5 × 90 → M4 × 90 preload bolt"}
    best_excl = max((o for o in A if o["label"] in EXCLUSIVE),
                    key=lambda o: o["save"])
    pool = [o for o in A if o["label"] not in EXCLUSIVE] + [best_excl]
    run = sum(o["save"] for o in pool)
    print(f"\n     EVERYTHING compatible, taken together "
          f"(the two preload-bolt options exclude each other):")
    for o in sorted(pool, key=lambda x: -x["save"]):
        print(f"       + {o['label']:60s} {o['save']:7.1f}")
    print(f"       {'':62s} {run:7.1f} g removed")
    res = BASE_TOTAL - run
    print(f"       {'RESULT':62s} {res:7.1f} g "
          f"({'UNDER' if res <= CEIL else 'STILL %.0f g OVER' % (res - CEIL)})")

    # --- changes that DO touch printed parts ------------------------------
    print("\n  B. TOUCHES PRINTED PARTS — would need the FEA and gate re-run")
    import json
    VOL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "output", "cad", "volumes.json")))
    base_g = VOL["base"] * 1.29e-3 * 0.90
    print(f"     {'base pedestal is the heaviest single printed part':62s} "
          f"{base_g:8.1f}")
    print(f"       └ a 20 % lightening of it saves {base_g*0.20:.1f} g, but it is the "
          f"part\n         that reacts every joint moment into the bench")
    QTY = (("base", 1), ("turret_j1", 1), ("link_half_tongue", 2),
           ("link_half_groove", 2), ("shaft_clamp", 2), ("servo_collar", 2),
           ("horn_adapter", 6), ("wrist_j4_housing", 1), ("wrist_j5_yoke", 1),
           ("wrist_j6_output", 1))
    fill_save = sum(VOL[n] * 1.29e-3 * 0.05 * q for n, q in QTY)
    print(f"     {'drop MASS_FILL 0.90 → 0.85 across all printed parts':62s} "
          f"{fill_save:8.1f}")
    print("       └ NOT a design change — a claim about what the slicer does. It "
          "would\n         need the fit coupon weighed to justify, not asserted")

    print("\n" + "=" * 88)
    print("  RECOMMENDATION")
    print("=" * 88)
    print("""
  Take the two zero-risk swaps first:

      aluminium bearing shims        -19.4 g   pure compression, no downside
      nylon M3 washers                -2.6 g   they only spread head load

  That leaves ~137 g still to find, and the only single item big enough is the
  M5 × 90 preload bolt at 93.6 g for six. Titanium takes it to 52.8 g (-41 g);
  going to M4 takes it to 58.8 g (-35 g) but changes the preload, which sets the
  bearing pair, so it needs checking rather than assuming.

  NONE of these combinations reaches 158 g without either titanium fasteners or
  a printed-part change. THIS IS A DECISION, NOT A CALCULATION, and it is yours:

    1. Accept ~1610 g and record that the 1450 g figure covered structure +
       actuators + bearings + shafts, not fasteners. Nothing needs reprinting;
       every structural margin above is unchanged, because fastener mass adds
       ~1 % to the gravity torque the analysis already covers with 46-102x.
    2. Buy titanium M5 × 90 and M3 × 20, plus aluminium shims: -80 g -> 1528 g.
       Still over.
    3. Lighten the base and re-run the gate. This is the only route that gets
       under 1450 g, and it invalidates the FEA on that part until re-run.
""")


if __name__ == "__main__":
    main()
