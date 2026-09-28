#!/usr/bin/env python3
"""Whole-arm motion sweep on the rev-I assembly, servos included.
Differential: contact present at rest (seated faces, bolted joints, pinch)
stays constant; only a RISE through the travel is a clash. A planted
obstacle proves the test can see one."""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import full_scene as FS           # noqa: E402
from verify_drive import contains  # noqa: E402

N = 1500


def overlap(moving, fixed, samples):
    tot, pairs = 0, {}
    for mk, P in samples.items():
        mb = np.r_[P.min(0), P.max(0)]
        for fk, f in fixed.items():
            fb = f.bounds
            if (fb[1] < mb[:3]).any() or (fb[0] > mb[3:]).any():
                continue
            n = int(contains(f, P).sum())
            if n:
                tot += n; pairs[(mk, fk)] = n
    return tot, pairs


def sweep(s, name, pt, ax, half, mov, steps=9):
    moving = {k: s[k] for k in mov if k in s}
    fixed = {k: v for k, v in s.items() if k not in mov}
    base = {k: m.sample(N) for k, m in moving.items()}
    rest, rest_pairs = overlap(moving, fixed, base)
    worst, wa, wp = 0, 0.0, {}
    for a in np.linspace(-half, half, steps):
        T = trimesh.transformations.rotation_matrix(np.radians(a), ax, pt)
        samp = {k: (T[:3, :3] @ P.T).T + T[:3, 3] for k, P in base.items()}
        o, pairs = overlap(moving, fixed, samp)
        if o - rest > worst:
            worst, wa = o - rest, a
            wp = {k: v - rest_pairs.get(k, 0) for k, v in pairs.items() if v - rest_pairs.get(k, 0) > 0}
    return rest, worst, wa, wp


if __name__ == "__main__":
    s = FS.scene()
    print("WHOLE-ARM MOTION SWEEP -- rev I, 35 parts incl. 6 x ST3215")
    print("rise above the rest-pose contact; > 15 points = clash\n")
    bad = 0
    for (name, pt, ax, half, mov) in FS.JOINTS:
        rest, worst, wa, wp = sweep(s, name, pt, ax, half, mov)
        flag = "  <-- CLASH" if worst > 15 else ""
        bad += worst > 15
        print("  %-12s +-%5.1f deg  rest %5d  worst rise %4d at %+6.1f%s" % (name, half, rest, worst, wa, flag))
        if worst > 15:
            for k, v in sorted(wp.items(), key=lambda kv: -kv[1])[:4]:
                print("        %s vs %s: +%d" % (k[0], k[1], v))
    # control: an obstacle in the J3 elbow's path must be seen
    blk = trimesh.creation.box(extents=[30, 30, 30]); blk.apply_translation([60, 0, 250])
    s2 = dict(s); s2["TEST_BLOCK"] = blk
    _, worst, _, _ = sweep(s2, *FS.JOINTS[2])
    print("\n  CONTROL (block in the J3 arc): rise %d -> %s" % (worst, "DETECTED" if worst > 15 else "BLIND"))
    print("\njoints with a clash: %d" % bad)
