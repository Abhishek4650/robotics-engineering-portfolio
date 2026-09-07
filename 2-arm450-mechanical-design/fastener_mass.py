"""
Fastener and insert mass — the term the mass gate does not have.

preprint_check.py computes:

    total = printed + servos + bearings + shafts

and stops. There is no fastener term at all. That is not a rounding error: this
design uses SIX M5 x 90 preload through-bolts, forty M3 brass heat-set inserts
and roughly a hundred smaller screws, and steel and brass are 6-7x the density
of the plastic they are holding together.

Every figure below is computed from the fastener's own geometry and material
density, from the quantities in BUY.md section 4 -- not looked up, so each one
can be argued with.
"""
import sys
import numpy as np

RHO_STEEL = 7.85e-3          # g/mm3
RHO_BRASS = 8.50e-3

def cyl(d, l):
    return np.pi / 4 * d ** 2 * l

def tube(od, idd, l):
    return np.pi / 4 * (od ** 2 - idd ** 2) * l

def cap_screw(d, length, rho=RHO_STEEL):
    """Socket cap head is ~1.5d across and 1.0d tall (ISO 4762)."""
    return (cyl(d, length) + cyl(1.5 * d, 1.0 * d)) * rho

def nut_nyloc(d, rho=RHO_STEEL):
    return (cyl(1.8 * d, 1.0 * d) - cyl(d, 1.0 * d)) * rho

def washer(d, rho=RHO_STEEL):
    return (cyl(2.2 * d, 0.5) - cyl(1.1 * d, 0.5)) * rho

def insert(od, l, thread, rho=RHO_BRASS):
    return (cyl(od, l) - cyl(thread * 0.83, l)) * rho


# name, qty, grams each, note
ITEMS = [
    ("M3 heat-set insert Ø4.6 × 5.8", 40, insert(4.6, 5.8, 3.0),
     "link seams, wrist, collars — brass"),
    ("M2.5 heat-set insert Ø3.6 × 4.0", 12, insert(3.6, 4.0, 2.5),
     "link tip ears — brass"),
    ("M3 × 20 socket cap", 24, cap_screw(3.0, 20), "link seams"),
    ("M3 × 16 socket cap", 12, cap_screw(3.0, 16), "collars, wrist interfaces"),
    ("M5 × 90 socket cap", 6, cap_screw(5.0, 90),
     "bearing preload through-bolt — the single heaviest fastener item"),
    ("M5 nyloc + 2 washers", 6, nut_nyloc(5.0) + 2 * washer(5.0), "on the preload bolt"),
    ("Ø3 × 20 spring/roll pin", 12, tube(3.0, 1.8, 20) * RHO_STEEL,
     "clamp anti-rotation — hollow, so light"),
    ("M2.5 × 8", 24, cap_screw(2.5, 8), "servo case mounting"),
    ("M2 × 6", 24, cap_screw(2.0, 6), "servo horns"),
    ("M3 washer", 30, washer(3.0), "under every head"),
    ("Ø36/Ø30 × 2 shim", 6, tube(36.0, 30.0, 2.0) * RHO_STEEL,
     "between the bearing inner races"),
]
# not carried by the arm
EXCLUDED = [("M4 × 16 base-to-bench", 4, cap_screw(4.0, 16),
             "bolts the base to the bench — not arm mass")]


def total():
    return sum(q * g for _n, q, g, _w in ITEMS)


def main():
    print("=" * 78)
    print("FASTENER AND INSERT MASS — computed from geometry, not looked up")
    print("=" * 78)
    print(f"\n  {'item':34s} {'qty':>4s} {'each g':>8s} {'total g':>9s}")
    print("  " + "-" * 74)
    for n, q, g, w in ITEMS:
        print(f"  {n:34s} {q:4d} {g:8.2f} {q*g:9.1f}   {w}")
    t = total()
    print("  " + "-" * 74)
    print(f"  {'CARRIED BY THE ARM':34s} {'':4s} {'':8s} {t:9.1f}")
    for n, q, g, w in EXCLUDED:
        print(f"  {n:34s} {q:4d} {g:8.2f} {q*g:9.1f}   EXCLUDED — {w}")
    return t


if __name__ == "__main__":
    t = main()
    import json, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad"))
    from params import MASS_BUDGET
    GATE = 1364.75          # preprint_check.py's total, printed+servos+brg+shafts
    print("\n" + "=" * 78)
    print(f"  gate total (printed + servos + bearings + shafts) {GATE:8.1f} g")
    print(f"  fasteners and inserts, NOT in the gate            {t:8.1f} g")
    print(f"  {'REAL ARM MASS':49s} {GATE + t:8.1f} g")
    print(f"  {'hard ceiling':49s} {MASS_BUDGET:8.1f} g")
    d = GATE + t - MASS_BUDGET
    print(f"  {'OVER by' if d > 0 else 'headroom':49s} {abs(d):8.1f} g")
    print("=" * 78)
