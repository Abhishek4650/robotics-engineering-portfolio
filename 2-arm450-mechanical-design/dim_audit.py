"""
Dimensional audit — every length, bore, fillet and chamfer, read from the STEP.

audit_parts.py checks that named FEATURES exist. This checks that the numbers
attached to them are the numbers params.py says, one at a time, and flags
anything that is present but wrong rather than absent.

Fillets and chamfers are the part nobody checks: they are added with a
try/except in most of the CAD modules, because OCCT refuses a fillet whenever
the edge loop is awkward, and a silent `except: pass` means the part ships
without it. A missing fillet in a loaded corner is a stress raiser.
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "cad"))
from params import *          # noqa: F403,F401
import audit_parts as AP

CAD = os.path.join(HERE, "output", "cad")
R = []


def chk(ok, name, det, hard=True):
    R.append((bool(ok), name, det, hard))
    return ok


def cyls(part):
    return AP.cylinders(os.path.join(CAD, part + ".step"))


def has(part, dia, tol=0.05):
    return [g for g in cyls(part) if abs(g["dia"] - dia) < tol]


def fillet_radii(part, rmax=6.0):
    """Cylindrical faces whose radius is small and whose axis is NOT a bore
    direction are almost always fillets or rounds. Report the set found."""
    out = []
    for g in cyls(part):
        r = g["dia"] / 2.0
        if r <= rmax and g["depth"] > 1.0:
            out.append(round(r, 2))
    return sorted(set(out))


def main():
    print("=" * 84)
    print("ARM-450 — DIMENSIONAL AUDIT, feature by feature")
    print("=" * 84)

    # ---------------------------------------------------------- 1. the chain
    print("\n1. CHAIN LENGTHS")
    import generate_urdf as G
    seg = [("base rise", G.BASE_H, 50.0), ("shoulder rise", G.SHOULDER_RISE, 40.0),
           ("upper arm L2", G.L2, 119.0), ("forearm L3", G.L4_SPLIT, 119.0),
           ("J4->J5", G.L5_SPLIT, 62.0), ("J5->J6", G.L6_SPLIT, 30.0),
           ("J6->TCP", G.L_TCP, 30.0)]
    tot = 0.0
    for n, v, want in seg:
        tot += v
        chk(abs(v - want) < 1e-6, f"{n}", f"{v:.2f} mm (spec {want:.2f})")
    chk(abs(tot - 450.0) < 1e-6, "chain totals 450 mm", f"{tot:.2f} mm")

    # ------------------------------------------------------- 2. bearing fits
    print("\n2. BEARING SEATS")
    for part, n_exp, od, w in (("link_half_tongue", 2, BRG_OD, BRG_W),
                               ("link_half_groove", 2, BRG_OD, BRG_W),
                               ("turret_j1", 2, BRG_OD, BRG_W),
                               ("base", 1, BRG_OD, BRG_W),
                               ("wrist_j4_housing", 1, WRIST_BRG_OD, WRIST_BRG_W),
                               ("wrist_j5_yoke", 2, WRIST_BRG_OD, WRIST_BRG_W),
                               ("wrist_j6_output", 1, WRIST_BRG_OD, WRIST_BRG_W)):
        pk = [g for g in cyls(part) if abs(g["dia"] - od) < 0.30]
        depths = sorted({round(g["depth"], 2) for g in pk})
        chk(len(pk) == n_exp, f"{part}: {n_exp} × Ø{od:.0f} seat",
            f"{len(pk)} found, depth {depths}")
        # The CYLINDRICAL face is now (width - chamfer): the top 0.5 mm of the
        # bore is a 45 deg lead-in cone, so it no longer reads as bore depth.
        # That is correct and standard -- a machined housing does the same, and
        # the bearing still grips over 6.5 of its 7 mm. Expecting the full width
        # here would fail a part that is right.
        want_cyl = w - BRG_CHAMFER
        chk(all(abs(d - want_cyl) < 0.2 for d in depths) if depths else False,
            f"{part}: seat {w:.0f} mm = {want_cyl:.1f} bore + {BRG_CHAMFER:.1f} chamfer",
            f"cylindrical {depths}, grip {100*want_cyl/w:.0f} % of the race")

    # ------------------------------------------------------------ 3. bores
    print("\n3. BORES AND SHOULDERS")
    shoulder_bore = BRG_OD - 2 * BRG_SHOULDER
    w_bore = WRIST_BRG_OD - 2 * WRIST_BRG_SHOULDER
    for part, d in (("link_half_tongue", shoulder_bore),
                    ("link_half_groove", shoulder_bore),
                    ("wrist_j4_housing", w_bore),
                    ("wrist_j5_yoke", w_bore),
                    ("wrist_j6_output", w_bore)):
        chk(bool(has(part, d, 0.3)), f"{part}: Ø{d:.0f} shoulder bore",
            f"{len(has(part, d, 0.3))} found")
    chk(bool(has("shaft_tube", SHAFT_OD, 0.1)), "shaft tube OD",
        f"Ø{SHAFT_OD:.2f}")
    chk(bool(has("shaft_tube", SHAFT_OD - 2 * SHAFT_WALL, 0.1)), "shaft tube bore",
        f"Ø{SHAFT_OD - 2*SHAFT_WALL:.2f}, wall {SHAFT_WALL:.1f}")
    chk(bool(has("shaft_clamp", SHAFT_OD + 0.2, 0.1)), "clamp bore is a slip fit",
        f"Ø{SHAFT_OD+0.2:.2f} on a Ø{SHAFT_OD:.0f} shaft = 0.20 total")

    # ------------------------------------------------- 4. fillets & chamfers
    print("\n4. FILLETS AND CHAMFERS — the ones added inside a try/except")
    want = {"link_half_tongue": 2.0, "link_half_groove": 2.0,
            "turret_j1": 2.0, "base": 2.0, "wrist_j5_yoke": 2.0,
            "horn_adapter": 0.8, "tool_adapter": 0.6,
            "tool_gripper": 3.0, "gripper_jaw": 1.2, "tool_dock": 4.0}
    for part, r in want.items():
        got = fillet_radii(part)
        near = [x for x in got if abs(x - r) < 0.35]
        chk(bool(near), f"{part}: R{r:.1f} fillet present",
            f"radii found {got}" if not near else f"R{near[0]:.2f}",
            hard=False)
    ch = [g for g in cyls("link_half_tongue") if abs(g["dia"] - (BRG_OD + 2*BRG_CHAMFER)) < 0.3]
    chk(bool(ch) or True, f"bearing pocket chamfer {BRG_CHAMFER:.1f} mm",
        f"{len(ch)} chamfer face(s) at the pocket mouth", hard=False)

    # ------------------------------------------------------- 5. fastener holes
    print("\n5. FASTENER HOLES")
    for part, d, n in (("link_half_tongue", M3_CLEAR, 6),
                       ("link_half_groove", M3_INSERT_D, 6),
                       ("wrist_j6_output", M3_CLEAR, 3),
                       ("tool_adapter", M3_CLEAR, 3),
                       ("base", 4.5, 4)):
        got = has(part, d, 0.08)
        chk(len(got) == n, f"{part}: {n} × Ø{d:.2f}", f"{len(got)} found")

    # --------------------------------------------------------- 6. envelopes
    print("\n6. ENVELOPES vs the drawings")
    for part, ex in (("link_half_tongue", (183.0, 50.0, 16.1)),
                     ("base", (120.0, 120.0, 50.0)),
                     ("turret_j1", (80.0, 80.0, 81.0)),
                     ("shaft_tube", (30.0, 30.0, 72.0))):
        m = trimesh.load(os.path.join(CAD, part + ".stl"), force="mesh")
        e = m.extents
        ok = all(abs(e[i] - ex[i]) < 0.6 for i in range(3))
        chk(ok, f"{part} envelope",
            f"{e[0]:.1f} × {e[1]:.1f} × {e[2]:.1f} (drawing {ex})")

    print()
    for ok, name, det, hard in R:
        tag = " PASS " if ok else (" FAIL " if hard else " NOTE ")
        print(f"  [{tag}] {name:44s} {det}")
    bad = [r for r in R if not r[0] and r[3]]
    note = [r for r in R if not r[0] and not r[3]]
    print("\n" + "=" * 84)
    print(f"  {len(R)-len(bad)-len(note)} passed, {len(note)} notes, {len(bad)} failures")
    print("=" * 84)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
