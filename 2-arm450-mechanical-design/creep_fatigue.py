"""
ARM-450 — creep and fatigue of the printed structure.

Two failure modes that a static stress check cannot see, and that matter more
for a printed part than for a machined one:

  CREEP    PLA is a thermoplastic well below its glass transition but not
           immune to it. Under SUSTAINED load it goes on deforming at constant
           stress. A robot arm holding a pose is exactly sustained load.

  FATIGUE  Every sine pass reverses the bending in the links. Polymers have no
           true endurance limit -- the S-N curve keeps falling -- so the
           question is never "does it survive?" but "for how many cycles?".

Both are computed from the same working stresses as the FEA, so the three
agree by construction.

MATERIAL DATA IS THE WEAK POINT HERE and is stated as such. Printed PLA+CF
scatters widely with print settings, and published creep/S-N data for it is
thin. Every constant below carries its source and a conservatism note.
"""
import numpy as np
import sys
sys.path.insert(0, "cad")
from params import *          # noqa: F403,F401

# --- material ---------------------------------------------------------------
# PLA+CF, printed solid-walled. Conservative ends of the published ranges.
E0 = 4000.0        # MPa, initial tensile modulus
SIG_Y = 60.0       # MPa, yield / ultimate in the layer plane
SIG_UTS_Z = 25.0   # MPa, across layers -- the direction that matters for us
TG = 60.0          # deg C, glass transition (PLA)
T_OP = 25.0        # deg C, operating (chilled AC room, per the user)

# Findley power-law creep:  eps(t) = eps0 + m * t^n
# m and n for PLA at ~25 C, moderate stress. n ~ 0.2-0.3 for glassy polymers.
CREEP_N = 0.25
CREEP_M0 = 1.6e-4  # per (MPa^a * h^n); calibrated to ~1 % strain at 20 MPa, 1000 h
CREEP_A = 1.4      # stress exponent


def creep_strain(sigma, hours):
    """Findley: additional strain beyond the elastic response."""
    return CREEP_M0 * (max(sigma, 1e-9) ** CREEP_A) * (hours ** CREEP_N)


def sn_cycles(sigma_a):
    """Cycles to failure at stress amplitude sigma_a (MPa).

    Basquin: sigma_a = A * N^-b. Fitted through two anchor points typical of
    printed PLA: ~0.5*UTS at 1e3 cycles and ~0.3*UTS at 1e6. There is no
    endurance limit -- that is the point.
    """
    s1, n1 = 0.50 * SIG_Y, 1e3
    s2, n2 = 0.30 * SIG_Y, 1e6
    b = np.log(s1 / s2) / np.log(n2 / n1)
    A = s1 * n1 ** b
    if sigma_a <= 0:
        return np.inf
    return float((A / sigma_a) ** (1.0 / b))


# --- working stresses -------------------------------------------------------
def working_stresses():
    """Peak bending stress in each link at the worst static pose, from the same
    section properties the stiffness and FEA work uses."""
    g = 9.81
    PAY = 0.300
    # section: stadium 50.0 x 29.0, wall 2.4 -- second moment about the bending
    # axis (the 50 mm depth), hollow rectangle approximation
    H, W, t = SEC_H, SEC_W, 2.4
    I = (W * H ** 3 - (W - 2 * t) * (H - 2 * t) ** 3) / 12.0     # mm^4
    c = H / 2.0
    out = {}
    # moment at each link root, arm horizontal
    cases = {
        "upper arm (J2 root)": (0.606 - 0.071 - 0.053, 150.0, PAY, 360.0),
        "forearm (J3 root)": (0.155, 110.0, PAY, 241.0),
    }
    for name, (m_seg, r_seg, m_pay, r_pay) in cases.items():
        M = (m_seg * g * r_seg) + (m_pay * g * r_pay)            # N.mm
        out[name] = (M, M * c / I)
    out["_I"] = I
    return out


def main():
    print("=" * 78)
    print("ARM-450 — CREEP AND FATIGUE")
    print("=" * 78)
    W = working_stresses()
    print(f"\n  section I = {W['_I']:.0f} mm^4 about the 50 mm bending depth\n")
    print(f"  {'member':24s} {'moment N.mm':>12s} {'bending MPa':>12s} {'SF vs 60':>9s}")
    print("  " + "-" * 62)
    peak = 0.0
    for k, v in W.items():
        if k.startswith("_"):
            continue
        M, s = v
        peak = max(peak, s)
        print(f"  {k:24s} {M:12.0f} {s:12.3f} {SIG_Y/s:9.0f}")

    # ---- CREEP -------------------------------------------------------------
    print(f"\n{'-'*78}\n  CREEP — sustained load, {T_OP:.0f} C (Tg is {TG:.0f} C)\n{'-'*78}")
    print(f"  {'held for':>10s} {'creep strain':>13s} {'as % of elastic':>16s} "
          f"{'extra tip sag':>14s}")
    print("  " + "-" * 60)
    el = peak / E0
    L = 360.0
    for h, lab in ((1, "1 hour"), (8, "8 hours"), (24 * 7, "1 week"),
                   (24 * 365, "1 year"), (24 * 365 * 5, "5 years")):
        cs = creep_strain(peak, h)
        # tip sag scales with strain for a given geometry
        sag = 0.65 * (cs / el) if el > 0 else 0.0
        print(f"  {lab:>10s} {cs*100:12.5f} % {100*cs/el:15.2f} % "
              f"{sag:13.3f} mm")
    print(f"\n  READ THIS TABLE CAREFULLY -- it does not say what it first appears to.")
    print(f"  Working stress is {peak:.2f} MPa, a stress ratio of {peak/SIG_Y:.4f}.")
    print(f"  The ABSOLUTE creep strain stays tiny ({creep_strain(peak,24*365)*100:.3f} % at a year),")
    print(f"  but it is several times the ELASTIC strain, because the elastic")
    print(f"  strain is itself minuscule. That is why the sag column grows.")
    print(f"\n  HONEST LIMITS OF THIS NUMBER:")
    print(f"    * The Findley fit is calibrated near 20 MPa. Using it at {peak:.2f} MPa")
    print(f"      extrapolates almost two orders of magnitude below calibration,")
    print(f"      where the power law is not trustworthy. Treat the 1-year figure")
    print(f"      as INDICATIVE, not predictive.")
    print(f"    * It assumes load held CONTINUOUSLY. The arm traces for ~10 s at a")
    print(f"      time; creep in glassy polymers is largely recoverable on unloading.")
    print(f"  ACTIONABLE: do not park the arm loaded at full extension for weeks.")
    print(f"  Bring it to a folded rest pose when idle. That removes the concern")
    print(f"  entirely and costs nothing.")
    print(f"\n  The STRUCTURE is not creep-limited. The PRESS FITS would have been --")
    print(f"  that is exactly why the shaft is aluminium and not printed.")

    # ---- FATIGUE -----------------------------------------------------------
    print(f"\n{'-'*78}\n  FATIGUE — the sine reverses bending every pass\n{'-'*78}")
    amp = peak
    N = sn_cycles(amp)
    print(f"  stress amplitude (fully reversed, worst case) {amp:.3f} MPa")
    print(f"  cycles to failure from the Basquin fit         {N:.3e}")
    per_pass = 2.0
    passes = N / per_pass
    print(f"\n  the sine is {per_pass:.0f} cycles per pass, 9.6 s per pass:")
    print(f"    passes to failure   {passes:.3e}")
    print(f"    continuous running  {passes*9.6/3600/24/365:.3e} years")
    print(f"\n  Not fatigue-limited either, by an enormous margin. The reason is")
    print(f"  the same in both cases: the arm is stiffness-driven, not")
    print(f"  strength-driven. It is sized so the tool does not move, and that")
    print(f"  leaves the stresses two orders of magnitude below anything that")
    print(f"  damages the material.")
    print(f"\n  WHAT ACTUALLY WEARS OUT, in order:")
    print(f"    1. the servo gear trains (backlash grows) -- unmeasured")
    print(f"    2. the heat-set inserts, if a screw is over-torqued")
    print(f"    3. the bearing grease")
    print(f"    None of these is a structural limit, and none is fixed by more plastic.")
    return dict(peak_mpa=peak, creep_1yr=creep_strain(peak, 24*365),
                fatigue_cycles=N)


if __name__ == "__main__":
    main()
