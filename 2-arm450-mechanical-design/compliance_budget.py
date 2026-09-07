"""
Independent compliance budget for the 145 mm clamshell arm.

Written to CROSS-CHECK the workflow's answer, not to replace it. Everything here
is first-principles with the formula stated, so any disagreement is traceable.

Question: at full extension with a 300 g payload, where does TCP error come from?
"""

import numpy as np

import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), 'cad'))
from params import E_MOD, G_RATIO, MATERIAL   # noqa: E402

G = 9.80665

# ---- geometry (mm) --------------------------------------------------------
L2 = L3 = 145.0            # upper arm, forearm (joint-to-joint)
L_WRIST = 70.0             # J5 -> TCP
REACH = L2 + L3 + L_WRIST  # 360 mm from J1 axis

# ---- section (mm) ---------------------------------------------------------
B, H = 47.5, 29.0          # clamshell outer width x depth


def box_I(b, h, t):
    return (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12.0


def box_J(b, h, t):
    """Bredt closed thin-tube torsion constant."""
    Am = (b - t) * (h - t)
    peri = 2 * ((b - t) + (h - t))
    return 4 * Am ** 2 * t / peri


# ---- materials: E in MPa (= N/mm^2), so I in mm^4 gives N.mm -------------
MATS = {
    "PLA":        dict(E=3500.0, Gr=0.36, note="typical FDM XY"),
    "PLA+CF":     dict(E=7000.0, Gr=0.36, note="typical, brand-dependent"),
    "BUILD":      dict(E=E_MOD, Gr=G_RATIO, note=f"params.MATERIAL = {MATERIAL}"),
    "SLA resin":  dict(E=2500.0, Gr=0.37, note="standard resin"),
}

# ---- loads ---------------------------------------------------------------
PAYLOAD = 0.300                     # kg at TCP
M_WRIST = 0.150                     # kg wrist cluster
M_FOREARM = 0.130                   # kg forearm incl. J4 servo
M_UPPER = 0.145                     # kg upper arm incl. J3 servo

# ---- servo backlash ------------------------------------------------------
BACKLASH_DEG = (0.3, 0.5, 1.0)      # ST3215 output spline, typical range


def cantilever_tip(P_N, L_mm, E, I):
    """Point load at the free end: d = P L^3 / (3 E I)."""
    return P_N * L_mm ** 3 / (3.0 * E * I)


def udl_tip(w_N_per_mm, L_mm, E, I):
    """Uniform load: d = w L^4 / (8 E I)."""
    return w_N_per_mm * L_mm ** 4 / (8.0 * E * I)


print("=" * 78)
print("COMPLIANCE BUDGET — TCP error at full extension, 300 g payload")
print("=" * 78)

for t in (2.0, 3.0):
    I = box_I(B, H, t)
    Jt = box_J(B, H, t)
    print(f"\n### wall t = {t:.1f} mm   I_closed = {I:,.0f} mm^4   "
          f"J_closed = {Jt:,.0f} mm^4")
    print(f"{'source':34s} {'PLA':>10s} {'PLA+CF':>10s}   (mm at TCP)")
    print("-" * 70)

    rows = {}
    for mat, mp in (("PLA", MATS["PLA"]), ("PLA+CF", MATS["PLA+CF"])):
        E = mp["E"]
        Gmod = E * mp["Gr"]

        # --- forearm bending: carries wrist + payload -----------------------
        P_fore = (M_WRIST + PAYLOAD) * G
        d_fore = cantilever_tip(P_fore, L3, E, I)
        w_fore = M_FOREARM * G / L3
        d_fore += udl_tip(w_fore, L3, E, I)

        # --- upper arm bending: carries everything outboard -----------------
        P_up = (M_FOREARM + M_WRIST + PAYLOAD) * G
        d_up = cantilever_tip(P_up, L2, E, I)
        w_up = M_UPPER * G / L2
        d_up += udl_tip(w_up, L2, E, I)
        # slope at the upper-arm tip also swings the whole outboard arm
        theta_up = P_up * L2 ** 2 / (2.0 * E * I)
        d_slope = theta_up * (L3 + L_WRIST)

        # --- torsion: payload offset from the link axis twists the shell ----
        # worst case the tool is offset by half the link depth
        offset = 40.0
        T = PAYLOAD * G * offset                       # N.mm
        phi = T * (L2 + L3) / (Gmod * Jt)              # rad
        d_tors = phi * L_WRIST

        rows.setdefault("forearm bending", {})[mat] = d_fore
        rows.setdefault("upper-arm bending", {})[mat] = d_up
        rows.setdefault("upper-arm slope x outboard", {})[mat] = d_slope
        rows.setdefault("shell torsion (40 mm offset)", {})[mat] = d_tors

    for k, v in rows.items():
        print(f"{k:34s} {v['PLA']:10.3f} {v['PLA+CF']:10.3f}")

    struct = {m: sum(v[m] for v in rows.values()) for m in ("PLA", "PLA+CF")}
    print(f"{'STRUCTURE SUBTOTAL':34s} {struct['PLA']:10.3f} {struct['PLA+CF']:10.3f}")

print("\n" + "=" * 78)
print("NON-STRUCTURAL sources — independent of material choice")
print("=" * 78)
for bl in BACKLASH_DEG:
    r = np.radians(bl)
    d_j2 = REACH * np.tan(r)
    d_j3 = (L3 + L_WRIST) * np.tan(r)
    # joints add in quadrature if independent, linearly worst-case
    rss = np.hypot(d_j2, d_j3)
    print(f"servo backlash {bl:.1f} deg   J2 -> {d_j2:5.2f} mm   "
          f"J3 -> {d_j3:5.2f} mm   combined(RSS) {rss:5.2f} mm")

print("\nbearing/boss play in a 2 mm printed wall: assume 0.05-0.15 mm radial at each")
print("joint; at J2 that projects to roughly the same magnitude at the TCP.")

# ---- the seam: what an UNBOLTED clamshell actually costs ------------------
print("\n" + "=" * 78)
print("THE SEAM — closed (properly bolted) vs open (two half-shells touching)")
print("=" * 78)


def open_J(b, h, t):
    """Two independent open channels: J = sum(b*t^3/3) over the strips."""
    hh = h / 2.0
    return 2.0 * ((2 * b + 2 * hh) * t ** 3 / 3.0)


for t in (2.0, 3.0):
    E = MATS["PLA"]["E"]
    Gmod = E * MATS["PLA"]["Gr"]
    Jc, Jo = box_J(B, H, t), open_J(B, H, t)
    Ic, Io = box_I(B, H, t), box_I(B, H, t) / 4.0   # open loses ~4x in bending

    T = PAYLOAD * G * 40.0
    d_tors_c = T * (L2 + L3) / (Gmod * Jc) * L_WRIST
    d_tors_o = T * (L2 + L3) / (Gmod * Jo) * L_WRIST

    P_up = (M_FOREARM + M_WRIST + PAYLOAD) * G
    d_bend_c = cantilever_tip(P_up, L2, E, Ic)
    d_bend_o = cantilever_tip(P_up, L2, E, Io)

    print(f"\nt = {t:.1f} mm, PLA")
    print(f"  torsion at TCP   closed {d_tors_c:6.3f} mm   "
          f"OPEN {d_tors_o:7.3f} mm   ({Jc/Jo:.0f}x worse)")
    print(f"  bending at TCP   closed {d_bend_c:6.3f} mm   "
          f"OPEN {d_bend_o:7.3f} mm   ({Io and Ic/Io:.0f}x worse)")
    print(f"  -> an unbolted seam costs about "
          f"{(d_tors_o + d_bend_o) - (d_tors_c + d_bend_c):.2f} mm at the TCP")

print("\n" + "=" * 78)
print("VERDICT CHECK")
print("=" * 78)
I2, I3 = box_I(B, H, 2.0), box_I(B, H, 3.0)
print(f"wall 2.0 -> 3.0 mm raises I by {I3/I2:.2f}x  "
      f"(deflection drops to {I2/I3*100:.0f}%)")
print(f"PLA -> PLA+CF raises E by {MATS['PLA+CF']['E']/MATS['PLA']['E']:.2f}x  "
      f"(deflection drops to {MATS['PLA']['E']/MATS['PLA+CF']['E']*100:.0f}%)")
print(f"link 97.9 -> 145 mm raises bending deflection by "
      f"{(145/97.9)**3:.2f}x at constant section (L^3 law)")
