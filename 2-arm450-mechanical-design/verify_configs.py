"""
The whole verification suite, run WITH and WITHOUT an end effector.

Every load analysis in this project was written against a single number: 300 g
at the TCP. That was a deliberate envelope, and it is generous -- but it says
nothing about a fitted tool as such, because a tool is not just mass. It moves
the load 42 mm further out along the tool axis, and the lever arm is what sizes
J2 and J3 and what sets the compliance at the working point. 75 g on a 42 mm
stick is not the same load case as 75 g at the flange.

So each configuration is run end to end:

  bare          nothing fitted, nothing carried -- the lower bound
  pen           the sine-trace demo as it actually runs
  gripper       the tool fitted, gripping nothing
  gripper+load  the tool fitted and carrying 225 g -- 300 g all in, the
                envelope every earlier analysis assumed
  dock          the docking probe, which carries no payload by definition

Nothing here is a new model. Torques come from joint_loads.py, the compliance
terms are the same four closed-form terms as compliance_budget.py, and the
creep and S-N laws are creep_fatigue.py's. What is new is that they are all
driven from one place with the tool as a parameter, so the answer for "with the
gripper on" cannot be a different vintage from the answer for "bare".
"""
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
# params lives in cad/. This module imports it directly, so it has to put cad/
# on the path itself -- it was relying on whatever imported it having done so,
# which meant `draw_paper_figs.py` crashed on import and never reached the
# figure it was run for.
sys.path.insert(0, os.path.join(_HERE, "cad"))
import joint_loads as JL
from params import E_MOD, G_RATIO, YIELD_MPA, RHO_SOLID, MATERIAL  # noqa: E402
import creep_fatigue as CF

G = 9.80665
# --- section and geometry: identical to compliance_budget.py ---------------
L2 = L3 = 145.0
L_WRIST = 70.0
B, H, WALL = 47.5, 29.0, 2.4
E_PLA_CF, G_RATIO = E_MOD, G_RATIO       # from params.MATERIAL
M_WRIST, M_FOREARM, M_UPPER = 0.150, 0.130, 0.145
YIELD = YIELD_MPA                 # from params.MATERIAL
SF_MIN = 3.0
COMPLIANCE_MAX = 0.30             # mm at the working point
BACKLASH_DEG = 0.5

# name -> (tool mass kg, grasped mass kg, reach past the flange m)
CONFIGS = {
    "bare":         (0.000, 0.000, 0.000),
    "pen":          (0.015, 0.000, 0.030),
    "gripper":      (0.075, 0.000, 0.042),
    "gripper+load": (0.075, 0.225, 0.042),
    "dock":         (0.062, 0.000, 0.036),
}


def box_I(b, h, t):
    return (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12.0


def box_J(b, h, t):
    Am = (b - t) * (h - t)
    peri = 2 * ((b - t) + (h - t))
    return 4 * Am ** 2 * t / peri


def compliance(payload_kg, reach_mm, E=E_PLA_CF, t=WALL):
    """Structural deflection at the WORKING POINT, mm.

    Same four terms as compliance_budget.py. The tool adds two effects and they
    pull in the same direction: more load at the end, and a longer arm from the
    last bending joint to the point you actually care about.
    """
    I, Jt = box_I(B, H, t), box_J(B, H, t)
    Gm = E * G_RATIO
    Lw = L_WRIST + reach_mm                     # J5 -> working point

    P_fore = (M_WRIST + payload_kg) * G
    d = P_fore * L3 ** 3 / (3 * E * I)
    d += (M_FOREARM * G / L3) * L3 ** 4 / (8 * E * I)

    P_up = (M_FOREARM + M_WRIST + payload_kg) * G
    d += P_up * L2 ** 3 / (3 * E * I)
    d += (M_UPPER * G / L2) * L2 ** 4 / (8 * E * I)
    d += (P_up * L2 ** 2 / (2 * E * I)) * (L3 + Lw)      # slope x outboard

    T = payload_kg * G * 40.0                            # 40 mm lateral offset
    d += (T * (L2 + L3) / (Gm * Jt)) * Lw                # shell torsion
    return d


def working_stress(tau_j3_Nm, t=WALL):
    """Bending stress in the link shell from the J3 moment, MPa.

    sigma = M c / I, with c = H/2. The link shell is what carries it, so the
    J3 torque is the right moment to use -- it is the one the forearm reacts.
    """
    I = box_I(B, H, t)
    return (tau_j3_Nm * 1000.0) * (H / 2.0) / I


def run(name, n=20000, seed=1):
    m_tool, m_load, reach = CONFIGS[name]
    payload = m_tool + m_load
    tau, _ = JL.sweep(n, seed=seed, payload=payload, tool_reach=reach)

    servo_stall = np.array([JL.SERVOS[s]["stall"] for s in JL.FITTED])
    servo_cont = np.array([JL.SERVOS[s]["cont"] for s in JL.FITTED])
    margin = servo_stall / np.maximum(tau, 1e-9)
    cont_ratio = tau / servo_cont

    d = compliance(payload, reach * 1000.0)
    sigma = working_stress(tau[2])
    sf = YIELD / max(sigma, 1e-9)
    creep_1y = CF.creep_strain(sigma, 24 * 365) * 100.0     # %
    life = CF.sn_cycles(sigma / 2.0)                        # fully-reversed amp
    backl = (L3 + L_WRIST + reach * 1000.0) * np.tan(np.radians(BACKLASH_DEG))

    return dict(
        config=name, tool_kg=m_tool, load_kg=m_load, payload_kg=payload,
        reach_mm=reach * 1000.0,
        tau=[float(v) for v in tau],
        tau_max=float(tau.max()),
        servo_margin_min=float(margin.min()),
        cont_ratio_max=float(cont_ratio.max()),
        compliance_mm=float(d),
        stress_MPa=float(sigma), sf=float(sf),
        creep_1y_pct=float(creep_1y), fatigue_cycles=float(life),
        backlash_mm=float(backl),
        total_error_mm=float(np.hypot(d, backl)),
    )


CRIT = [
    ("FEA — safety factor on yield", "sf", lambda v: v >= SF_MIN, "≥ 3"),
    ("stiffness — structural compliance", "compliance_mm",
     lambda v: v <= COMPLIANCE_MAX, "≤ 0.30 mm"),
    ("creep — strain at 1 year held", "creep_1y_pct",
     lambda v: v <= 0.5, "≤ 0.5 %"),
    ("fatigue — cycles to failure", "fatigue_cycles",
     lambda v: v >= 1e8, "≥ 1e8"),
    ("servo — stall margin", "servo_margin_min", lambda v: v >= 1.5, "≥ 1.5×"),
    ("servo — continuous rating", "cont_ratio_max",
     lambda v: v <= 3.0, "≤ 3× cont"),
]


def main():
    print("=" * 92)
    print("ARM-450 — VERIFICATION WITH AND WITHOUT AN END EFFECTOR")
    print("=" * 92)
    res = {n: run(n) for n in CONFIGS}

    print(f"\n  {'config':13s} {'tool':>6s} {'held':>6s} {'reach':>7s} "
          f"{'J2':>6s} {'J3':>6s} {'σ MPa':>7s} {'SF':>7s} "
          f"{'δ mm':>7s} {'creep%':>8s} {'cycles':>9s}")
    print("  " + "-" * 88)
    for n, r in res.items():
        print(f"  {n:13s} {r['tool_kg']*1000:5.0f}g {r['load_kg']*1000:5.0f}g "
              f"{r['reach_mm']:6.0f}mm {r['tau'][1]:6.2f} {r['tau'][2]:6.2f} "
              f"{r['stress_MPa']:7.3f} {r['sf']:7.1f} {r['compliance_mm']:7.3f} "
              f"{r['creep_1y_pct']:8.4f} {r['fatigue_cycles']:9.1e}")

    print(f"\n  PASS/FAIL — every criterion, every configuration")
    print(f"\n  {'criterion':36s} {'limit':>10s}  " +
          "".join(f"{n:>14s}" for n in CONFIGS))
    print("  " + "-" * (48 + 14 * len(CONFIGS)))
    bad = 0
    for label, key, ok, limit in CRIT:
        cells = ""
        for n in CONFIGS:
            v = res[n][key]
            good = ok(v)
            bad += (not good)
            txt = (f"{v:.3g}" if abs(v) < 1e4 else f"{v:.1e}")
            cells += f"{('PASS ' if good else 'FAIL ') + txt:>14s}"
        print(f"  {label:36s} {limit:>10s}  {cells}")

    print(f"\n  PRECISION at the working point (structural + {BACKLASH_DEG}° backlash)")
    print(f"  {'config':13s} {'structural':>12s} {'backlash':>10s} {'combined':>10s}")
    print("  " + "-" * 48)
    for n, r in res.items():
        print(f"  {n:13s} {r['compliance_mm']:11.3f}m {r['backlash_mm']:9.2f}m "
              f"{r['total_error_mm']:9.2f}m")
    print("\n  Backlash dominates in every configuration, by roughly 20x. That is")
    print("  the honest headline: this arm is servo-limited, not structure-limited,")
    print("  and no change to the printed parts moves the number.")

    print("\n" + "=" * 92)
    print(f"  {len(CRIT)*len(CONFIGS) - bad} passed, {bad} failed "
          f"({len(CRIT)} criteria x {len(CONFIGS)} configurations)")
    print("=" * 92)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "output", "verify_configs.json")
    json.dump(res, open(out, "w"), indent=1)
    print(f"  wrote {out}")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
