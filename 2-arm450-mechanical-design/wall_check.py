"""
Minimum wall thickness, measured from the mesh.

final_audit.py's first attempt used ray casting and this machine has no rtree,
so every call raised, every part returned None, and the check reported PASS on
zero measurements. A check that cannot run must say so, not pass.

This uses a voxel distance transform instead, which needs only scipy:
voxelise, take the Euclidean distance from every solid voxel to the nearest
empty one, and read the local maxima -- the medial axis. Twice the distance at
a medial voxel is the local thickness there, and the smallest of those is the
thinnest wall in the part.

Parts are scanned in size order and the pitch adapts, because a 183 mm link at
a fine pitch is tens of millions of voxels and buys nothing: its design wall is
2.4 mm, nowhere near the 1.24 mm floor. The small parts carry the fine features
-- 2 mm gear teeth, 3 mm bayonet lugs -- and get the fine pitch.
"""
import os
import sys

import numpy as np
import trimesh
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "output", "cad")
NOZZLE, LINE_W = 0.6, 0.62
MIN_WALL = 2 * LINE_W

# small, fine-featured parts first -- these are the ones that can actually be
# too thin, and they are cheap to voxelise
FINE = ["gripper_pinion", "gripper_jaw", "shaft_clamp", "horn_adapter",
        "tool_adapter", "dock_target", "tool_dock", "tool_gripper",
        "wrist_j5_yoke", "wrist_j4_housing", "wrist_j6_output", "servo_collar"]
COARSE = ["turret_j1", "base", "link_half_groove", "link_half_tongue",
          "fit_coupon"]


def wall(name, pitch):
    m = trimesh.load(os.path.join(CAD, name + ".stl"), force="mesh")
    v = m.voxelized(pitch=pitch).fill()
    M = v.matrix
    if M.sum() == 0:
        return None
    D = ndimage.distance_transform_edt(M) * pitch
    mx = ndimage.maximum_filter(D, size=3)
    ridge = (D >= mx - 1e-9) & (D > 0)
    t = 2.0 * D[ridge]
    # the 1st percentile, not the raw minimum: a single voxel at a fillet run-out
    # or a tessellation sliver reads as near-zero and is not a wall
    return float(np.percentile(t, 1.0)), float(np.median(t)), int(M.sum())


def main():
    print("=" * 74)
    print(f"MINIMUM WALL THICKNESS — voxel medial axis")
    print(f"floor = {MIN_WALL:.2f} mm (two {LINE_W} mm lines at a {NOZZLE} mm nozzle)")
    print("=" * 74)
    print(f"\n  {'part':22s} {'pitch':>6s} {'min wall':>9s} {'median':>8s} {'verdict':>9s}")
    print("  " + "-" * 60)
    bad, done = [], 0
    for group, pitch in ((FINE, 0.30), (COARSE, 0.70)):
        for n in group:
            try:
                r = wall(n, pitch)
            except Exception as e:                       # noqa: BLE001
                print(f"  {n:22s} {pitch:6.2f}   FAILED {type(e).__name__}")
                continue
            if r is None:
                continue
            t1, tm, nv = r
            ok = t1 >= MIN_WALL
            done += 1
            if not ok:
                bad.append((n, t1))
            print(f"  {n:22s} {pitch:6.2f} {t1:9.2f} {tm:8.2f} "
                  f"{'ok' if ok else 'THIN':>9s}")
            sys.stdout.flush()
    print("\n" + "=" * 74)
    print(f"  {done} parts measured, {len(bad)} below the {MIN_WALL:.2f} mm floor")
    if bad:
        for n, t in bad:
            print(f"    {n}: {t:.2f} mm")
    print("=" * 74)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
