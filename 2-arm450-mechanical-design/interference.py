"""
ARM-450 — interference sweep across the joint limits.

The animation proves kinematics. It does NOT prove the parts clear each other:
the renderer paints depth-sorted triangles and performs no collision detection.
This does the real check, with exact mesh-mesh collision (FCL).

METHOD
  * sample the 6-D joint space across the URDF limits
  * build the assembly at each pose
  * test every pair of bodies that is NOT adjacent in the chain
    (adjacent bodies share a joint and legitimately touch)
  * report which joint combinations collide, and the safe limits that follow

Adjacency is by chain index: bodies i and j are exempt if |i-j| <= 1 in the
kinematic order, plus the two halves of the same link, which are meant to touch.
"""

import numpy as np
import trimesh
import assemble as A

# Joint limits, degrees — READ FROM THE URDF, not copied.
# They were hardcoded here, and when J5 was narrowed to its measured
# collision-free range (-91..+49, from +/-110) this sweep carried on sampling
# poses the arm is no longer allowed to reach, and carried on reporting them as
# collisions. A limit written down twice is a limit that will disagree with
# itself.
import xml.etree.ElementTree as _ET
import os as _os

_URDF = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "arm450.urdf")
LIM = np.degrees(np.array([
    [float(j.find("limit").get("lower")), float(j.find("limit").get("upper"))]
    for j in _ET.parse(_URDF).getroot().findall("joint")
    if j.get("type") == "revolute"], float))

# chain index of each body returned by build(), in order.
# 0 base | 1 turret | 2,3 upper-arm halves | 4 shaft | 5 clamp | 6 collar
# 7,8 forearm halves | 9 shaft | 10 clamp | 11 collar | 12 rollJ4 | 13 yokeJ5
# 14 rollJ6 | 15 flange | 16 tool
CHAIN_IDX = [0, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 5, 6, 6]
NAMES = ["base", "turret", "upper-A", "upper-B", "shaft2", "clamp2", "collar2",
         "fore-A", "fore-B", "shaft3", "clamp3", "collar3",
         "j4housing", "yokeJ5", "j6output", "tool"]
# A fitted tool adds bodies past index 15. They all ride on link 6, so they take
# the same chain index as the tool they replace -- the adapter and the tool body
# legitimately touch j6output and each other.
TOOL_IDX, TOOL_NAMES = 6, ["adapter", "toolbody", "jawA", "jawB"]

# SERVICES -- the fluid tube and the cable bundle -- are not single bodies that
# ride on one link. They run the WHOLE chain, clipped to every link on the way.
# Treating them as one body at chain index 6 (which is what happened the first
# time) makes every contact with the base, the turret and the links a reported
# collision, because |6 - 0| > 1. The offsets then make no difference at all,
# which is the tell: pushing the tube 46 mm clear changed nothing, because the
# checker was flagging contacts the tube MUST make.
#
# So a service is added SEGMENT BY SEGMENT, each carrying the chain index of the
# link it is clipped to. A segment on the upper arm touching the upper arm is
# fine; the same segment touching the base is not.
SERVICE = {}          # body index -> (chain index, name)


def register_service(i, chain, name):
    SERVICE[i] = (chain, name)


def clear_services():
    SERVICE.clear()


def _chain(i):
    if i in SERVICE:
        return SERVICE[i][0]
    return CHAIN_IDX[i] if i < len(CHAIN_IDX) else TOOL_IDX


def _name(i):
    if i in SERVICE:
        return SERVICE[i][1]
    if i < len(NAMES):
        return NAMES[i]
    k = i - len(NAMES)
    return TOOL_NAMES[k] if k < len(TOOL_NAMES) else f"tool{k}"


def exempt(i, j):
    """True if this pair is allowed to touch."""
    if abs(_chain(i) - _chain(j)) <= 1:
        return True
    return False


def check(parts, tol=0.0):
    """Return the list of colliding (i, j) pairs."""
    mgr = trimesh.collision.CollisionManager()
    for k, (m, _) in enumerate(parts):
        mgr.add_object(str(k), m)
    hit, names = mgr.in_collision_internal(return_names=True)
    if not hit:
        return []
    out = []
    for a, b in names:
        i, j = int(a), int(b)
        if not exempt(i, j):
            out.append((min(i, j), max(i, j)))
    return sorted(set(out))


def sweep(n=70, seed=0):
    rng = np.random.default_rng(seed)
    tally = {}
    worst = []
    bad = 0
    for k in range(n):
        q = rng.uniform(LIM[:, 0], LIM[:, 1])
        parts, _ = A.build(*np.radians(q))
        c = check(parts)
        if c:
            bad += 1
            for pr in c:
                tally[pr] = tally.get(pr, 0) + 1
            if len(worst) < 6:
                worst.append((q.copy(), c))
    return bad, n, tally, worst


if __name__ == "__main__":
    print("=" * 74)
    print("INTERFERENCE SWEEP — exact mesh collision across the URDF joint limits")
    print("=" * 74)
    bad, n, tally, worst = sweep()
    print(f"\n  {bad} of {n} sampled poses collide  ({bad/n*100:.0f} %)\n")
    if tally:
        print(f"  {'pair':34s} {'hits':>6s}  {'% of samples':>12s}")
        print("  " + "-" * 58)
        for (i, j), c in sorted(tally.items(), key=lambda kv: -kv[1]):
            print(f"  {NAMES[i]:15s} <-> {NAMES[j]:15s} {c:6d} {c/n*100:11.1f} %")
        print("\n  worst-case poses (deg, J1..J6):")
        for q, c in worst[:4]:
            pr = ", ".join(f"{NAMES[i]}/{NAMES[j]}" for i, j in c)
            print("    " + " ".join(f"{v:+7.1f}" for v in q) + f"   -> {pr}")
    else:
        print("  no interference found anywhere in the sampled joint space")

    # --- where is it safe? bisect the dominant joint --------------------
    print("\n" + "=" * 74)
    print("SAFE LIMITS — narrowing the joint that causes most collisions")
    print("=" * 74)
    for jidx, jname in ((2, "J3 elbow"), (4, "J5 wrist")):
        print(f"\n  {jname}: collision rate vs its own limit")
        for cap in (150, 100, 60):
            rng = np.random.default_rng(7)
            L = LIM.copy()
            L[jidx] = [-cap, cap]
            b = 0
            for _ in range(18):
                q = rng.uniform(L[:, 0], L[:, 1])
                if check(A.build(*np.radians(q))[0]):
                    b += 1
            print(f"    +/-{cap:4d} deg -> {b/18*100:5.1f} % of poses collide")
