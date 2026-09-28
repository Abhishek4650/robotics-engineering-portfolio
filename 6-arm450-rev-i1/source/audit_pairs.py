#!/usr/bin/env python3
"""STATIC ALL-PAIRS INTERFERENCE AUDIT of the assembled arm (rest pose).

The motion sweep is differential: overlap already present at rest never
shows as a 'rise'. That hid a spigot_collar cutting 3 mm into the base.
This checks every pair once, statically, and classifies each contact:

  FACE   the overlapping samples lie on one plane (thickness < 0.15 mm):
         a seated face, a bolted face, the pinch, a press fit -- designed
  CLASH  the overlap has real thickness in every direction: two parts
         occupy the same space
"""
import itertools
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import full_scene as FS            # noqa: E402
from verify_drive import contains  # noqa: E402


def thickness(pts):
    """Smallest extent of the point cloud along its principal axes."""
    if len(pts) < 4:
        return 0.0
    c = pts - pts.mean(0)
    _, sv, vt = np.linalg.svd(c, full_matrices=False)
    proj = c @ vt[-1]
    return float(proj.max() - proj.min())


def depth(M, P, cap=400, chunk=50):
    """Distance of each inside point to M's surface. Capped + chunked: a
    whole tongue-and-groove seam in one closest_point call exhausted 62 GB."""
    if not len(P):
        return np.zeros(0)
    if len(P) > cap:
        P = P[np.random.default_rng(0).choice(len(P), cap, replace=False)]
    out = [np.abs(trimesh.proximity.closest_point(M, P[i:i + chunk])[1]) for i in range(0, len(P), chunk)]
    return np.concatenate(out)


def audit(s, n=4000, label=""):
    import gc
    rows = []
    keys = sorted(s)
    samp = {k: s[k].sample(n) for k in keys}
    for a, b in itertools.combinations(keys, 2):
        A, B = s[a], s[b]
        if (A.bounds[1] < B.bounds[0]).any() or (B.bounds[1] < A.bounds[0]).any():
            continue
        # only the samples inside the other part's bounding box need a ray test
        sa = samp[a][np.all((samp[a] >= B.bounds[0]) & (samp[a] <= B.bounds[1]), axis=1)]
        sb = samp[b][np.all((samp[b] >= A.bounds[0]) & (samp[b] <= A.bounds[1]), axis=1)]
        pa = sa[contains(B, sa, 5000)] if len(sa) else np.zeros((0, 3))
        pb = sb[contains(A, sb, 5000)] if len(sb) else np.zeros((0, 3))
        gc.collect()
        if len(pa) + len(pb) == 0:
            continue
        pts = np.vstack([pa, pb])
        # PENETRATION DEPTH: how far each overlapping sample lies inside the
        # OTHER part. Seats, press fits, pinch walls and coincident faces are
        # ~0 everywhere; a clash has real depth. (The first version measured
        # the thickness of the contact cloud, which fails for a servo pinched
        # between TWO walls or a spigot in a round socket.)
        da, db = depth(B, pa), depth(A, pb)
        t = float(np.concatenate([da, db]).max())
        rows.append((a, b, len(pts), t, pts.min(0), pts.max(0)))
        print("   %-18s | %-18s %5d pts  depth %.3f  %s" % (a, b, len(pts), t,
              "CLASH" if t >= 0.15 else "surface"), flush=True)
    return rows


if __name__ == "__main__":
    s = FS.scene()
    rows = audit(s)
    print("STATIC ALL-PAIRS AUDIT -- %d parts, %d touching pairs" % (len(s), len(rows)))
    clash = [r for r in rows if r[3] >= 0.15]
    face = [r for r in rows if r[3] < 0.15]
    print("\nSURFACE contacts (penetration < 0.15 mm -- seats, bolted faces, pinch, fits):")
    for a, b, n, t, lo, hi in sorted(face):
        print("   %-18s | %-18s %5d pts  depth %.3f" % (a, b, n, t))
    print("\nCLASHES (penetration >= 0.15 mm) -- must each be explained:")
    for a, b, n, t, lo, hi in sorted(clash, key=lambda r: -r[3]):
        print("   %-18s | %-18s %5d pts  depth %.2f  x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f"
              % (a, b, n, t, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
