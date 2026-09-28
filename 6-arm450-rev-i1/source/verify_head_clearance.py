#!/usr/bin/env python3
"""
SCREW HEADS BESIDE A TURNING PART (user, 2026-09-24: "wouldn't the screw head
collide during joint motion, and at what angle?").

For every screw of the final assembly and every joint k it could meet: the
screw belongs to body b; joint k turns everything on the far side of it. If
the screw is on the fixed side (b < k) its head is checked against the moving
side, and vice versa. Each joint alone is turned from -180 to +180 deg in 1 deg
steps (the others at home); reported per screw: the smallest clearance INSIDE
the joint's working range, and the first angle (each way) where the screw
would touch -- how much margin the range has before a collision.

Only pairs that come within 12 mm somewhere in +-180 are listed. A screw
fails if it comes closer than MIN_CLR inside the range.
"""
import os
import re
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_final_assembly as BA     # noqa: E402
import verify_fasteners as VF         # noqa: E402
import make_rule5_views as R5         # noqa: E402
import make_rule6_pages as R6         # noqa: E402

RANGE = {1: 90.0, 2: 54.0, 3: 72.0, 4: 90.0, 5: 46.5, 6: 90.0}
MIN_CLR = 1.0
SCREW = re.compile(R5.SCREW_RX.pattern)


def main():
    A, _ = BA.build()
    S = {c.name: VF.world(c) for c in A.children if VF.world(c) is not None}
    meshes = {k: R5.tess(v, 0.05, 0.25) for k, v in S.items()}
    axes = R6.joint_axes()
    screws = sorted(k for k in S if SCREW.match(k) and R6.body(k) is not None)
    angles = np.arange(-180.0, 180.01, 1.0)
    fails, rows, curves = 0, [], []
    print("SCREW HEADS vs TURNING PARTS -- each joint alone, -180..+180 deg (1 deg)")
    for k in range(1, 7):
        q, w = axes[k - 1]
        moving = [n for n in meshes if (R6.body(n) or 0) >= k and not n.startswith("spring_")]
        fixed = [n for n in meshes if R6.body(n) is not None and R6.body(n) < k and not n.startswith("spring_")]
        # the joint's own bearing / servo / horn screws turn inside each other by design
        own = lambda n: n.startswith(("brg_J%d" % k, "horn_screw_J%d" % k, "servo_scr_J%d" % k)) or n == "servo_J%d" % k
        for side_s, side_p in ((fixed, moving), (moving, fixed)):
            scr = [n for n in side_s if n in screws and not own(n)]
            if not scr:
                continue
            other = trimesh.collision.CollisionManager()
            for n in side_p:
                if not own(n):
                    V, F = meshes[n]; other.add_object(n, trimesh.Trimesh(V, F, process=False))
            for s in scr:
                V, F = meshes[s]; ms = trimesh.Trimesh(V, F, process=False)
                d0 = other.min_distance_single(ms)
                if d0 > 40.0:
                    continue
                dist = []
                for a in angles:
                    T = V6_rot(q, w, -a if side_s is fixed else a)
                    mt = ms.copy(); mt.apply_transform(T)
                    dist.append(other.min_distance_single(mt, return_name=True))
                d = np.array([x[0] for x in dist])
                if d.min() > 12.0:
                    continue
                inr = np.abs(angles) <= RANGE[k] + 1e-9
                i_min = int(np.argmin(np.where(inr, d, 1e9)))
                touch_pos = next((a for a, dd in zip(angles, d) if a >= 0 and dd <= 0.0), None)
                touch_neg = next((a for a, dd in zip(angles[::-1], d[::-1]) if a <= 0 and dd <= 0.0), None)
                ok = d[inr].min() >= MIN_CLR
                fails += 0 if ok else 1
                rows.append((k, s, d[inr].min(), angles[i_min], dist[i_min][1], touch_neg, touch_pos, ok))
                curves.append(dict(joint=k, screw=s, angles=angles.tolist(), dist=[float(x) for x in d],
                                   range=RANGE[k]))
                print("  J%d %-20s min %.2f mm in +-%.1f (at %+.0f deg, vs %s)   would touch at %s / %s   %s"
                      % (k, s, d[inr].min(), RANGE[k], angles[i_min], dist[i_min][1],
                         "%+.0f deg" % touch_neg if touch_neg is not None else "never (-)",
                         "%+.0f deg" % touch_pos if touch_pos is not None else "never (+)", "ok" if ok else "TOO CLOSE"))
    import json
    json.dump(curves, open(os.path.join(HERE, "HEAD_CLEARANCE.json"), "w"))
    print("\nHEAD CLEARANCE: %d screw(s) closer than %.1f mm to a turning part inside the range" % (fails, MIN_CLR))
    return fails


def V6_rot(q, w, deg):
    """rotation by deg about the axis through q along w (4x4)."""
    return trimesh.transformations.rotation_matrix(np.radians(deg), w, q)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
