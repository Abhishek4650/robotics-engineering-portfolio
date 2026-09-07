"""
Do the parts that bolt together actually line up?

Every check so far has looked at parts ONE AT A TIME: does this part have six
Ø3.40 holes, is that pocket Ø42. None of them has asked whether the six holes in
the tongue half land on the six inserts in the groove half — which is the thing
that decides whether the arm can be assembled at all.

A hole pattern can be right on both parts and still not mate: mirrored, rotated
by one position, or offset along the link. This checks the actual coordinates.
"""
import os
import sys

import numpy as np

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


def holes(part, dia, tol=0.08):
    """(x, y) of every hole of this diameter, sorted, in the part's own frame."""
    out = []
    for g in AP.cylinders(os.path.join(CAD, part + ".step")):
        if abs(g["dia"] - dia) < tol:
            out.append((round(g["perp"][0], 3), round(g["perp"][1], 3)))
    return sorted(set(out))


def main():
    print("=" * 82)
    print("MATING CHECK — do the holes in parts that bolt together line up?")
    print("=" * 82)

    # ---- 1. the link seam: tongue clearance vs groove inserts
    print("\n1. LINK SEAM — 6 x M3 through the tongue into inserts in the groove")
    a = holes("link_half_tongue", M3_CLEAR)
    b = holes("link_half_groove", M3_INSERT_D)
    chk(len(a) == len(b) == 6, "same number of seam holes on both halves",
        f"tongue {len(a)} x Ø{M3_CLEAR:.2f}, groove {len(b)} x Ø{M3_INSERT_D:.2f}")
    if len(a) == len(b):
        # the halves meet face to face, so the groove half is MIRRORED in Y
        bm = sorted([(x, -y) for x, y in b])
        d = [np.hypot(ax - bx, ay - by) for (ax, ay), (bx, by) in zip(a, bm)]
        d_un = [np.hypot(ax - bx, ay - by) for (ax, ay), (bx, by) in zip(a, b)]
        best, how = (max(d), "mirrored in Y") if max(d) <= max(d_un) else (max(d_un), "as-is")
        chk(best < 0.05, "seam holes are coaxial across the joint",
            f"worst {best:.4f} mm apart ({how})")
        print(f"    tongue x: {[round(x,1) for x,_ in a]}")
        print(f"    groove x: {[round(x,1) for x,_ in b]}")

    # ---- 2. tip ears
    print("\n2. LINK TIP EARS — 2 x M2.5")
    a = holes("link_half_tongue", 2.70)
    b = holes("link_half_groove", TIP_INSERT_D)
    chk(len(a) == len(b) == 2, "same number of tip-ear holes",
        f"tongue {len(a)}, groove {len(b)}")
    if len(a) == len(b) == 2:
        bm = sorted([(x, -y) for x, y in b])
        d = max(np.hypot(ax-bx, ay-by) for (ax,ay),(bx,by) in zip(a,bm))
        chk(d < 0.05, "tip-ear holes are coaxial", f"worst {d:.4f} mm")

    # ---- 3. the two link halves are the same length
    print("\n3. THE TWO HALVES ARE THE SAME PART LENGTH")
    import trimesh
    mt = trimesh.load(os.path.join(CAD, "link_half_tongue.stl"), force="mesh")
    mg = trimesh.load(os.path.join(CAD, "link_half_groove.stl"), force="mesh")
    chk(abs(mt.extents[0] - mg.extents[0]) < 0.02, "half lengths match",
        f"tongue {mt.extents[0]:.3f} vs groove {mg.extents[0]:.3f} mm")
    chk(abs(mt.extents[1] - mg.extents[1]) < 0.02, "half widths match",
        f"{mt.extents[1]:.3f} vs {mg.extents[1]:.3f} mm")
    # joint-to-joint pitch from the bearing pockets themselves
    for part in ("link_half_tongue", "link_half_groove"):
        pk = [g for g in AP.cylinders(os.path.join(CAD, part + ".step"))
              if abs(g["dia"] - BRG_OD) < 0.3]
        xs = sorted({round(g["perp"][0], 3) for g in pk})
        pitch = max(xs) - min(xs) if len(xs) > 1 else 0.0
        chk(abs(pitch - LINK_L) < 0.02, f"{part}: joint pitch",
            f"{pitch:.3f} mm (spec {LINK_L:.2f})")

    # ---- 4. tool face vs adapter
    print("\n4. J6 TOOL FACE vs THE ADAPTER")
    j = holes("wrist_j6_output", M3_CLEAR)
    t = holes("tool_adapter", M3_CLEAR)
    chk(len(j) == len(t) == 3, "3 bolts each side", f"J6 {len(j)}, adapter {len(t)}")
    if len(j) == len(t) == 3:
        aj = sorted(round(np.degrees(np.arctan2(y, x)) % 360) for x, y in j)
        at = sorted(round(np.degrees(np.arctan2(y, x)) % 360) for x, y in t)
        rj = np.mean([np.hypot(x, y) for x, y in j])
        rt = np.mean([np.hypot(x, y) for x, y in t])
        chk(aj == at, "bolt angles match", f"{aj} vs {at}")
        chk(abs(rj - rt) < 0.05, "bolt circle matches", f"Ø{2*rj:.2f} vs Ø{2*rt:.2f}")

    # ---- 5. servo collar vs the servo it clamps
    print("\n5. SERVO COLLAR")
    # TWO clamp screws through the split lugs. holes() dedups by (x, y), and a
    # through-hole is two cylindrical faces at one position, so expect 2 positions
    # -- the third Ø3.40 position is the counterbore's own pilot.
    c = holes("servo_collar", M3_CLEAR)
    chk(len(c) >= 2, "servo collar clamp screws", f"{len(c)} position(s) x Ø{M3_CLEAR:.2f}")

    # ---- 6. horn adapter vs the horn
    print("\n6. HORN ADAPTER")
    h = holes("horn_adapter", HORN_PILOT_D, tol=0.15)
    chk(len(h) == HORN_N, f"{HORN_N} horn screw holes on Ø{HORN_BCD:.0f} BCD",
        f"{len(h)} found")
    if h:
        r = np.mean([np.hypot(x, y) for x, y in h])
        chk(abs(2*r - HORN_BCD) < 0.1, "horn bolt circle matches the datasheet",
            f"Ø{2*r:.2f} vs Ø{HORN_BCD:.1f}")
    pin = holes("horn_adapter", CLAMP_PIN_D, tol=0.15)
    chk(len(pin) >= 1, "roll-pin hole present", f"{len(pin)} x Ø{CLAMP_PIN_D:.1f}")

    print()
    for ok, name, det, hard in R:
        tag = " PASS " if ok else (" FAIL " if hard else " NOTE ")
        print(f"  [{tag}] {name:44s} {det}")
    bad = [r for r in R if not r[0] and r[3]]
    print("\n" + "=" * 82)
    print(f"  {len(R)-len(bad)} passed, {len(bad)} failures")
    print("=" * 82)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
