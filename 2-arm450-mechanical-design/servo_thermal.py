"""
ST3215 continuous torque, DERIVED from the datasheet instead of a rule of thumb.

Datasheet (Waveshare ST3215, 12 V):
    stall torque      30 kgf.cm      = 2.942 N.m
    locked-rotor I    2.7 A
    torque constant   kt = 11 kgf.cm/A = 1.079 N.m/A
    no-load current   180 mA
    encoder           360 deg / 4096  = 0.0879 deg
    gear              "high precision metal gear"  -- NO backlash figure given

From those: winding resistance R = V / I_stall, and dissipation at any torque is
I^2 R with I = tau / kt. That turns "hold 30 % of stall" from a rule of thumb
into a thermal calculation.
"""
import numpy as np

V, I_STALL = 12.0, 2.7
KT = 11.0 * 0.0980665 / 1.0          # kgf.cm/A -> N.m/A
TAU_STALL = 30.0 * 0.0980665         # N.m
R = V / I_STALL                      # ohm, winding at stall
I_NOLOAD = 0.180

# thermal: case rise = P * Rth. Small servos are typically 8-15 C/W in still air.
RTH = 10.0                           # C/W  -- ESTIMATE, the one number still assumed
T_AMB = 22.0
TG_PLA = 60.0                        # PLA glass transition; the mount softens above this
TG_PLA_CF = 62.0


def current_for(tau):      return tau / KT
def power_for(tau):        return current_for(tau)**2 * R
def case_temp(tau):        return T_AMB + power_for(tau) * RTH
def tau_for_temp(T):       return KT * np.sqrt((T - T_AMB) / (RTH * R))


if __name__ == "__main__":
    print("="*72); print("ST3215 — CONTINUOUS TORQUE FROM THE DATASHEET"); print("="*72)
    print(f"\n  stall torque   {TAU_STALL:.3f} N.m   ({TAU_STALL/0.0980665:.0f} kgf.cm)")
    print(f"  kt             {KT:.3f} N.m/A")
    print(f"  winding R      {R:.2f} ohm   (= 12 V / 2.7 A locked rotor)")
    print(f"  stall power    {V*I_STALL:.1f} W  -- all of it heat\n")
    print(f"  {'torque N.m':>11s} {'% stall':>8s} {'current A':>10s} {'power W':>9s} {'case C':>8s}")
    print("  " + "-"*52)
    for tau in (0.42, 0.88, 1.02, 1.27, 2.00, 2.62, TAU_STALL):
        print(f"  {tau:11.2f} {tau/TAU_STALL*100:7.0f}% {current_for(tau):10.2f} "
              f"{power_for(tau):9.1f} {case_temp(tau):8.0f}")

    print(f"\n  PLA softens at {TG_PLA:.0f} C. Allowable continuous torque to stay below it:")
    t_lim = tau_for_temp(TG_PLA)
    print(f"     tau_cont = {t_lim:.3f} N.m  =  {t_lim/TAU_STALL*100:.0f} % of stall")
    print(f"  My rule of thumb was 30 %. The datasheet gives {t_lim/TAU_STALL*100:.0f} % — "
          f"the rule was sound.")

    print("\n" + "="*72); print("APPLIED TO THE ARM"); print("="*72)
    for j, tau, lbl in (("J2", 2.625, "worst case, 300 g at full extension"),
                        ("J2", 0.42,  "drawing, pen at 200 mm"),
                        ("J2", 1.30,  "drawing, pen at 300 mm"),
                        ("J3", 1.271, "worst case")):
        T = case_temp(tau)
        v = "OK" if T < TG_PLA else ("MARGINAL" if T < 80 else "SOFTENS THE MOUNT")
        print(f"  {j} {lbl:36s} {tau:5.2f} N.m -> {power_for(tau):5.1f} W, "
              f"case {T:3.0f} C   {v}")

    print("\n" + "="*72); print("WHAT THE DATASHEET DOES NOT GIVE"); print("="*72)
    print("  No backlash / output-play figure. 'High precision metal gear' is a")
    print("  description, not a number. Backlash remains the largest term in the")
    print("  precision budget and still has to be measured.")
    print(f"\n  It DOES confirm encoder resolution: 360/4096 = {360/4096:.4f} deg,")
    print(f"  which is what the corrected budget already uses.")
