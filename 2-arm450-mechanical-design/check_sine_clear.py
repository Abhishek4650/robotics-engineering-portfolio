"""
Is the sine trajectory collision-free?

The interference sweep samples the WHOLE joint-limit box and reports ~43 % of
poses colliding. That number says almost nothing about the task actually run:
the sine trace uses J1 +/-16, J2 79..115, J3 -68..-33, J4 +/-23, J5 42..48,
J6 0 -- a narrow corner of that box.

This checks the 240 solved waypoints themselves, with the same exact mesh-mesh
collision (FCL) the sweep uses.
"""
import os
import numpy as np
import assemble as A
import interference as I

TRAJ = os.path.expanduser("~/ros2_ws/src/arm450_sine/sine_traj.npz")


def main(tool="pen", stride=1, plumbing=None):
    """`tool` is not cosmetic. A fitted gripper reaches 42 mm past the J6 face
    and is 48 mm across; the dock probe is 36 mm and Ø46. A path solved and
    cleared against a bare flange is not automatically clear with either on."""
    Q = np.load(TRAJ)["Q"][::stride]
    print("=" * 74)
    print(f"SINE PATH COLLISION CHECK — {len(Q)} waypoints, exact mesh "
          f"collision, tool = {tool}"
          + (f", plumbing = {plumbing}" if plumbing else ""))
    print("=" * 74)
    bad, pairs = [], {}
    for k, q in enumerate(Q):
        parts, _ = A.build(*q, tool=tool, plumbing=plumbing)
        hits = I.check(parts)
        if hits:
            bad.append(k)
            for i, j in hits:
                pairs[(i, j)] = pairs.get((i, j), 0) + 1
    print(f"\n  colliding waypoints: {len(bad)} of {len(Q)}"
          f"   ({100*len(bad)/len(Q):.1f} %)")
    if pairs:
        print(f"\n  {'pair':38s} {'hits':>5s}")
        print("  " + "-" * 48)
        for (i, j), n in sorted(pairs.items(), key=lambda kv: -kv[1]):
            # I.NAMES is only the ARM bodies. Tools and the fluid line are
            # appended after it, so index straight into NAMES and you get an
            # IndexError the moment anything is fitted. _name() handles both.
            print(f"  {I._name(i):18s} <-> {I._name(j):16s} {n:5d}")
        print(f"\n  first colliding waypoint: {bad[0]}  "
              f"q = {np.degrees(Q[bad[0]]).round(1)}")
    else:
        print("\n  *** THE SINE PATH IS COLLISION-FREE ***")
        print(f"  Every one of the {len(Q)} poses checked clears, on exact mesh "
              f"geometry.")
    # how close does it get?
    print("\n  CLEARANCE MARGIN — re-testing with the parts grown by a tolerance:")
    for tol in (0.5, 1.0, 2.0, 3.0):
        n = 0
        for q in Q[::8]:
            parts, _ = A.build(*q, tool=tool, plumbing=plumbing)
            grown = []
            for m, c in parts:
                g = m.copy()
                g.vertices += g.vertex_normals * tol
                grown.append((g, c))
            if I.check(grown):
                n += 1
        tag = "clear" if n == 0 else f"{n} of {len(Q[::8])} poses touch"
        print(f"    grown by {tol:.1f} mm/face : {tag}")
    return bad


if __name__ == "__main__":
    import sys
    tools = sys.argv[1:] or ["pen", "gripper", "dock"]
    # The bare/pen path is the one the demo actually runs, so it gets every
    # waypoint. The fitted tools re-validate a path already solved and cleared,
    # so every 4th pose is enough to catch an envelope change -- adjacent
    # waypoints are at most 2.09 deg apart.
    fail = 0
    for t in tools:
        if t.startswith("tube:"):
            # tube:external / tube:internal -- the fluid line, with a pen tool
            fail += len(main("pen", stride=4, plumbing=t.split(":", 1)[1]))
        else:
            fail += len(main(t, stride=1 if t == "pen" else 4))
        print()
    print("=" * 74)
    print(f"  {len(tools)} tool configuration(s) checked, "
          f"{fail} colliding waypoint(s) in total")
    print("=" * 74)
    sys.exit(1 if fail else 0)
