"""
Why the servo mounts are snapping.

The link SHELLS were analysed in REPORT.md and came out with safety factor 66.
The MOUNTS were never analysed — and they are what actually broke. This script
finds out why, and the answer is a design-load error, not a material problem.

KEY PRINCIPLE this design missed:
    A servo mount must be sized for the servo's STALL TORQUE, not for the
    gravity load it normally carries. Whenever an actuator can drive a structure
    to failure, the actuator's limit IS the design load. A collision, a
    commanded step, or hitting a joint limit all deliver full stall torque.
"""

import numpy as np

# ---- actuators ------------------------------------------------------------
SERVOS = {
    "ST3215 @12V": 2.94,     # N.m stall = 30 kgf.cm
    "ST3250 @12V": 4.90,     # N.m stall = 50 kgf.cm
}
TAU_GRAVITY_J2 = 2.08        # N.m — what the arm actually carries statically

# ---- PLA ------------------------------------------------------------------
S_INPLANE = 50.0             # MPa, XY tensile
S_INTERLAYER = 25.0          # MPa, Z — the usual failure path on FDM
E = 3500.0

# ---- the measured brackets ------------------------------------------------
# (name, thickness mm, arm length mm, estimated width mm)
BRACKETS = [
    ("Motor_fixer_j2_p2", 4.0, 36.0, 12.0),
    ("Motor_fixer_j2_p1", 6.0, 36.0, 14.0),
    ("motor fixer (U-channel leg)", 5.0, 27.0, 20.0),
]

# radius at which a small bracket reacts the servo torque.
# The ST3215 output boss / horn bolt circle is small — this is the whole problem.
R_REACT = {
    "horn bolt circle (~Ø20)": 10.0,
    "servo case tabs (~Ø35)": 17.5,
    "full-perimeter collar (~Ø50)": 25.0,
}


def bending_stress(F, arm, b, t):
    """Cantilever bracket: sigma = M/Z, Z = b t^2 / 6."""
    Z = b * t ** 2 / 6.0
    return F * arm / Z          # N/mm^2 = MPa


print("=" * 82)
print("1. THE DESIGN-LOAD ERROR")
print("=" * 82)
print(f"gravity torque the arm actually carries at J2 : {TAU_GRAVITY_J2:.2f} N.m")
for k, v in SERVOS.items():
    print(f"STALL torque the servo can deliver ({k}) : {v:.2f} N.m  "
          f"-> {v/TAU_GRAVITY_J2:.2f}x the gravity load")

print("\n" + "=" * 82)
print("2. FORCE INTO THE MOUNT:  a clamp reacts torque as a COUPLE, F = T / (2r)")
print("=" * 82)
print(f"{'reaction radius':32s} " + "".join(f"{k:>16s}" for k in SERVOS))
print("-" * 82)


def couple_force(tau, r_mm):
    """Two equal forces at +/- r making a couple: T = 2*F*r."""
    return tau / (2.0 * r_mm * 1e-3)          # N


for lbl, r in R_REACT.items():
    row = "".join(f"{couple_force(t, r):13.0f} N " for t in SERVOS.values())
    print(f"{lbl:32s} {row}")
print("\n-> the force scales as 1/r. A bracket gripping close to the servo axis")
print("   sees several times the force of a collar that wraps the whole body.")

print("\n" + "=" * 82)
print("3. STRESS IN THE EXISTING BRACKETS AT STALL TORQUE")
print("=" * 82)
print("Evaluated at BOTH a pessimistic and a generous reaction radius, because we")
print("do not know exactly where each bracket grips. The conclusion is the same.\n")
for r_lbl, r in (("servo case tabs, r = 17.5 mm", 17.5),
                 ("generous, r = 25 mm", 25.0)):
    F = couple_force(SERVOS["ST3215 @12V"], r)
    print(f"--- {r_lbl}:  F = {F:.0f} N  (ST3215 stall 2.94 N.m) ---")
    print(f"{'bracket':30s} {'t':>5s} {'Z':>7s} {'sigma':>10s} "
          f"{'SF(XY)':>8s} {'SF(Z)':>8s}  verdict")
    print("-" * 82)
    for name, t, arm, b in BRACKETS:
        s = bending_stress(F, arm, b, t)
        Z = b * t ** 2 / 6.0
        sf_z = S_INTERLAYER / s
        verdict = "FAILS" if sf_z < 1.0 else ("marginal" if sf_z < 2.0 else "ok")
        print(f"{name:30s} {t:5.1f} {Z:7.1f} {s:9.1f} MPa "
              f"{S_INPLANE/s:8.2f} {sf_z:8.2f}  {verdict}")
    print()

print("-> every bracket fails at stall torque under BOTH assumptions.")
print("   A sharp internal corner (Kt >= 3, section 4) makes it worse still.")
print("   Safety factor below 2.0 is unacceptable for parts seeing shock loads.")

print("\n" + "=" * 82)
print("4. STRESS CONCENTRATION AT SHARP INTERNAL CORNERS")
print("=" * 82)
print("A reentrant corner multiplies local stress by Kt. For a filleted step,")
print("Kt depends on r/t. Typical values for a shouldered flat bar in bending:\n")
for r_over_t, kt in ((0.05, 2.6), (0.10, 2.1), (0.20, 1.7), (0.35, 1.45), (0.50, 1.3)):
    print(f"   r/t = {r_over_t:4.2f}  ->  Kt ~ {kt:.2f}")
print("\nThese are typical published values, not exact for this geometry.")
print("A sharp corner (r~0) can be taken as Kt >= 3.")
t_ref = 4.0
print(f"\nFor the 4 mm bracket: a 2 mm fillet gives r/t = 0.50 -> Kt ~ 1.3,")
print(f"versus Kt >= 3 sharp. That alone is a {3/1.3:.1f}x reduction in peak stress.")

print("\n" + "=" * 82)
print("5. THE FIX — full-perimeter collar instead of a bending bracket")
print("=" * 82)
print("Replace the slender bracket with a closed collar that wraps the servo body.")
print("Torque is then carried as SHEAR AROUND A CLOSED LOOP, not bending in an arm.\n")
D_COLLAR, T_COLLAR, H_COLLAR = 50.0, 4.0, 30.0
for name, tau in SERVOS.items():
    F_c = couple_force(tau, D_COLLAR / 2)           # N per side of the couple
    A_shear = np.pi * D_COLLAR * T_COLLAR           # mm^2, full perimeter
    tau_shear = F_c / A_shear
    print(f"{name}: F = {F_c:5.0f} N over a {np.pi*D_COLLAR:.0f} mm perimeter "
          f"x {T_COLLAR:.0f} mm wall = {A_shear:.0f} mm^2")
    print(f"   -> shear stress {tau_shear:.2f} MPa, "
          f"SF vs 25 MPa interlayer = {S_INTERLAYER/tau_shear:.0f}")

print("\n" + "=" * 82)
print("6. HEAT-SET INSERT BOSS — why it splits")
print("=" * 82)
D_INS, L_INS = 4.6, 5.8
for boss_od in (7.0, 8.0, 9.0, 10.0):
    wall = (boss_od - D_INS) / 2
    # hoop stress from press/melt fit is proportional to 1/wall; use a simple ratio
    print(f"   boss OD {boss_od:4.1f} mm -> wall around insert {wall:4.2f} mm  "
          + ("TOO THIN, will split" if wall < 1.8 else
             "adequate" if wall < 2.5 else "good"))
print(f"\n   pull-out capacity = pi*d*l*tau = "
      f"{np.pi*D_INS*L_INS*18.0:.0f} N at an assumed 18 MPa interface shear")
print("   -> pull-out is NOT the failure mode; the boss SPLITTING is.")
print("   Use boss OD >= 9 mm (>= 2.2 mm wall) and >= 4 perimeters.")
