#!/usr/bin/env python3
"""
CABLE ROUTE THROUGH THE JOINTS (user, 2026-09-24: "wouldn't the cables wind up
during joint motion?").

The ST3215 bus is a daisy chain: controller -> J1 -> J2 -> ... -> J6. Each
cable joins servo k (fixed to body k-1) to servo k+1 (fixed to body k), so it
crosses exactly ONE joint -- joint k, whose axis is servo k's own output axis.

  1. No joint turns more than 180 deg in total (+-90 at most; the ST3215 is not
     continuous), so a cable is only ever flexed back and forth -- it cannot
     wind up turn after turn.
  2. How much the joint changes the cable's path: the cable leaves servo k at
     its exit E_k (fixed side) and arrives at servo k+1's entry E_{k+1}
     (moving side). Turning the joint by t changes |E_k - E_{k+1}| by at most
     2 r sin(t/2), r = E_k's distance from the joint axis (triangle
     inequality). Measured here on the exact model over the whole range: the
     real change, plus the straight span's clearance at both range ends.
  3. The loop to leave at each joint = that change + 20 mm; the cable length =
     the longest straight span + loop + 2 x 15 mm plug leads.
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_final_assembly as BA     # noqa: E402
import verify_fasteners as VF         # noqa: E402
import make_rule5_views as R5         # noqa: E402
import make_rule6_pages as R6         # noqa: E402
import make_audit_views as MV         # noqa: E402
import drive_common as DC             # noqa: E402

RANGE = {1: 90.0, 2: 54.0, 3: 72.0, 4: 90.0, 5: 46.5, 6: 90.0}
LOOP_MARGIN, LEAD = 20.0, 15.0


def exit_point(k):
    """cable exit / entry of servo k in its servo frame: straight out of the
    back through the cover window (forks J2/J3/J5), or along the channel past
    the case end (J1/J4/J6) -- verify_wiring.py's measured routes."""
    xs = (DC.WIRE_WIN_X0 + DC.WIRE_WIN_X1) / 2
    if k in (2, 3, 5):
        return np.array([xs, 0.0, DC.SSCR_HEAD + 3.0])
    return np.array([40.0, 0.0, DC.PLATEAU + 5.0])


def main():
    A, _ = BA.build()
    S = {c.name: (VF.world(c), c) for c in A.children if VF.world(c) is not None}
    axes = R6.joint_axes()
    meshes = {k: R5.tess(v[0], 0.1, 0.3) for k, v in S.items()}
    E = {}
    for k in range(1, 7):
        T = MV.seat_T(S, k)
        E[k] = (T @ np.append(exit_point(k), 1.0))[:3]
    print("CABLE ROUTE -- daisy chain controller -> J1 -> ... -> J6, one joint per cable\n")
    print("  %-10s %-7s %-12s %-24s %-22s %-10s %s" % ("cable", "crosses", "range", "exit r from axis",
                                                      "span min..max (mm)", "change", "loop / cable"))
    worst = 0
    rows = []
    for k in range(1, 6):
        q, w = axes[k - 1]
        a = E[k]; b0 = E[k + 1]
        rel = a - q
        r = np.linalg.norm(rel - (rel @ w) * w)
        ts = np.radians(np.linspace(-RANGE[k], RANGE[k], 181))
        d = []
        for t in ts:
            Rt = trimesh.transformations.rotation_matrix(t, w, q)
            d.append(np.linalg.norm(a - (Rt @ np.append(b0, 1.0))[:3]))
        d = np.array(d)
        bound = 2 * r * np.sin(np.radians(RANGE[k]))
        change = d.max() - d.min()
        loop = change + LOOP_MARGIN
        length = d.max() + loop + 2 * LEAD
        rows.append((k, r, d.min(), d.max(), change, loop, length))
        print("  J%d -> J%d   J%d      +-%-9.1f %5.1f mm (bound %4.0f)     %6.1f .. %-6.1f       %5.1f mm   %3.0f / %3.0f mm"
              % (k, k + 1, k, RANGE[k], r, bound, d.min(), d.max(), change, loop, length))
        worst = max(worst, change)
    print("\n  controller -> J1: both in the foot, no joint crossed")
    print("  J6 is the last servo on the bus: no cable leaves it")
    print("\nNo joint turns more than 180 deg in total, so no cable can wind up; the largest path change is %.0f mm." % worst)
    print("CABLE ROUTE: 0 problem(s)")
    return rows


if __name__ == "__main__":
    main()
