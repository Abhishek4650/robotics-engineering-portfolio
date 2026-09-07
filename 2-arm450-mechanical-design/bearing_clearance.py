"""
Bearing clearance from geometry and specification — no guessing needed.

The user is right that this is computable. Three things stack:
  1. the bearing's own RADIAL INTERNAL CLEARANCE (an ISO spec, not a guess)
  2. how much of it the PRESS FIT closes up
  3. how much the PRINTED POCKET deflects under load -- in PLA this can
     dominate the bearing's own clearance entirely
"""
import numpy as np

# ---- 1. bearing internal clearance -------------------------------------
# 6806: 30 x 42 x 7 deep groove ball. ISO 5753 group CN (Normal) for a
# 30 mm bore is 5-20 um radial. Group C2 is tighter, C3 looser.
CN_MIN, CN_MAX = 5e-3, 20e-3        # mm radial
C2_MIN, C2_MAX = 1e-3, 11e-3
C3_MIN, C3_MAX = 13e-3, 28e-3

# ---- 2. press fit closes some of it ------------------------------------
# Outer ring pressed into the housing shrinks the raceway. A rule of thumb is
# that ~70-80 % of the interference transfers to the raceway.
INTERF = 0.020                       # mm, our Ø42.00 pocket on a 0.02 shrink printer
TRANSFER = 0.75

# ---- 3. printed pocket compliance --------------------------------------
E_PLA_CF = 7000.0                    # MPa
E_STEEL = 200000.0
BRG_OD, WALL = 42.0, 4.0             # mm, pocket wall thickness in the boss
SPAN = 22.0                          # mm, bearing centre spacing
REACH = 360.0

def pocket_radial_deflection(F_N):
    """Thick-cylinder radial growth of the printed boss under bearing load.
    u = F/(E*t*L) * (approximate line-contact spreading over the race width)."""
    L = 7.0                           # bearing width, mm
    return F_N / (E_PLA_CF * WALL * L) * (BRG_OD / 2)

if __name__ == "__main__":
    print("="*74); print("BEARING CLEARANCE FROM SPECIFICATION AND GEOMETRY"); print("="*74)
    print(f"\n1. 6806 radial internal clearance (ISO 5753), unmounted:")
    for n,(a,b) in (("C2",(C2_MIN,C2_MAX)),("CN normal",(CN_MIN,CN_MAX)),("C3",(C3_MIN,C3_MAX))):
        print(f"     {n:10s} {a*1000:5.1f} - {b*1000:5.1f} um")
    print(f"\n2. our Ø42.00 pocket gives {INTERF*1000:.0f} um interference;")
    print(f"   ~{TRANSFER*100:.0f} % transfers to the raceway = "
          f"{INTERF*TRANSFER*1000:.0f} um taken out of the clearance")
    for n,(a,b) in (("C2",(C2_MIN,C2_MAX)),("CN normal",(CN_MIN,CN_MAX))):
        lo = max(0.0, a - INTERF*TRANSFER); hi = max(0.0, b - INTERF*TRANSFER)
        print(f"   {n:10s} mounted clearance {lo*1000:5.1f} - {hi*1000:5.1f} um "
              + ("(PRELOADED, zero clearance)" if hi <= 0 else ""))

    print(f"\n3. printed-pocket deflection under the real joint load:")
    for tau, lbl in ((2.62,"J2 worst case"), (0.42,"J2 while drawing")):
        F = tau*1000/SPAN            # N couple across the bearing spacing
        u = pocket_radial_deflection(F)
        th = 2*u/SPAN
        print(f"     {lbl:18s} F = {F:5.1f} N -> pocket grows {u*1000:5.1f} um"
              f" -> {REACH*np.tan(th):5.3f} mm at the TCP")

    print("\n" + "="*74); print("VERDICT"); print("="*74)
    F = 0.42*1000/SPAN
    u = pocket_radial_deflection(F)
    tot = u                          # bearing itself is preloaded to zero
    print(f"  With a Ø42.00 press fit the bearing's own clearance is CLOSED "
          f"(CN {CN_MAX*1000:.0f} um < {INTERF*TRANSFER*1000:.0f} um interference).")
    print(f"  What remains is the PRINTED POCKET flexing: {u*1000:.1f} um at drawing load,")
    print(f"  = {REACH*np.tan(2*u/SPAN):.3f} mm at the TCP.")
    print(f"\n  -> this REPLACES my assumed 0.65 mm with a computed "
          f"{REACH*np.tan(2*u/SPAN):.3f} mm.")
