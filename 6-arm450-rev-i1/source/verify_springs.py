#!/usr/bin/env python3
"""Gravity springs: posed through the J2 x J3 range, every spring (as a Ø9
body along its real line of action) against every part; collars against the
links they clamp."""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import full_scene as FS            # noqa: E402
import spring_parts as SP          # noqa: E402
from verify_drive import contains  # noqa: E402

RES = []


def rec(label, ok, detail):
    print("   %-62s %s  %s" % (label, "PASS" if ok else "FAIL", detail))
    RES.append((label, ok, detail))


def cq2tm(wp):
    import cadquery as cq
    p = os.path.join("/tmp/claude-1000/-home-user-ros2-ws-Arm-450-new-design/d7055e52-889b-4cd2-992e-dd3a2338ce75/scratchpad", "_c.stl")
    cq.exporters.export(wp, p, tolerance=0.01, angularTolerance=0.1)
    return trimesh.load(p)


def spring_body(a, b, trim=4.0, d=9.0):
    v = b - a; L = np.linalg.norm(v); u = v / L
    a2, b2 = a + u * trim, b - u * trim
    c = trimesh.creation.cylinder(radius=d / 2, segment=[a2, b2])
    return c, L


def main():
    s = FS.scene()
    cu = {"collar_upper_+y": cq2tm(SP.collar_half(+1, SP.J2_AXIS_Z + SP.B2)),
          "collar_upper_-y": cq2tm(SP.collar_half(-1, SP.J2_AXIS_Z + SP.B2))}
    cf = {"collar_fore_+y": cq2tm(SP.collar_half(+1, SP.J3_AXIS_Z + SP.B3)),
          "collar_fore_-y": cq2tm(SP.collar_half(-1, SP.J3_AXIS_Z + SP.B3))}
    print("=" * 92); print("GRAVITY SPRINGS"); print("=" * 92)
    # collars vs the link they clamp (0.2 clearance until tightened) and everything else
    for nm, m in list(cu.items()) + list(cf.items()):
        Q = m.sample(20000)
        hits = {k: int(contains(v, Q).sum()) for k, v in s.items()
                if k != nm and not ((v.bounds[1] < Q.min(0)).any() or (v.bounds[0] > Q.max(0)).any())}
        bad = {k: n for k, n in hits.items() if n}
        rec("%s clear of every part at rest" % nm, not bad, str(bad) if bad else "clear")
    up = FS.ABOVE_J2 + FS.ABOVE_J3 + FS.ABOVE_J4 + FS.ABOVE_J5 + FS.ABOVE_J6
    fore = FS.ABOVE_J3 + FS.ABOVE_J4 + FS.ABOVE_J5 + FS.ABOVE_J6
    worst = {}
    lens = {"J2": [], "J3": []}
    for q2 in np.linspace(-54, 54, 7):
        for q3 in np.linspace(-72, 72, 7):
            R2 = trimesh.transformations.rotation_matrix(np.radians(q2), [0, 1, 0], [0, 0, 90.0])
            R3 = trimesh.transformations.rotation_matrix(np.radians(q3), [0, 1, 0], [0, 0, 209.0])
            posed = {}
            for k, m in s.items():
                T = np.eye(4)
                if k in fore:
                    T = R2 @ R3
                elif k in up:
                    T = R2
                mm = m.copy(); mm.apply_transform(T); posed[k] = mm
            for k, m in cu.items():
                mm = m.copy(); mm.apply_transform(R2); posed[k] = mm
            for k, m in cf.items():
                mm = m.copy(); mm.apply_transform(R2 @ R3); posed[k] = mm
            for (jn, a, b) in SP.springs_world(q2, q3):
                body, L = spring_body(a, b)
                lens[jn].append(L)
                Q = body.sample(4000)
                for k, m in posed.items():
                    if (m.bounds[1] < Q.min(0)).any() or (m.bounds[0] > Q.max(0)).any():
                        continue
                    n = int(contains(m, Q).sum())
                    if n:
                        key = (jn, k)
                        if n > worst.get(key, (0,))[0]:
                            worst[key] = (n, q2, q3)
    if worst:
        for (jn, k), (n, q2, q3) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
            rec("%s spring vs %s" % (jn, k), False, "%d pts at q2 %+.0f q3 %+.0f" % (n, q2, q3))
    else:
        rec("all 4 springs clear of every part over J2 +-54 x J3 +-72", True, "49 poses")
    def spec(a, b, rng):          # derived from the anchor geometry, never typed
        return (b - a, float(np.sqrt(a * a + b * b - 2 * a * b * np.cos(np.radians(rng)))))
    for jn, want in (("J2", spec(SP.A2, SP.B2, 54)), ("J3", spec(SP.A3, SP.B3, 72))):
        rec("%s spring stays in its specified length range" % jn,
            min(lens[jn]) >= want[0] - 0.5 and max(lens[jn]) <= want[1] + 0.5,
            "%.1f .. %.1f mm (spec %.1f .. %.1f)" % (min(lens[jn]), max(lens[jn]), *want))
    fails = [r for r in RES if not r[1]]
    print("\nFAILURES: %d" % len(fails))
    for f in fails:
        print("  - %s | %s" % (f[0], f[2]))


if __name__ == "__main__":
    main()
