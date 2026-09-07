"""
Unidirectional trajectory strategy — the free 6x precision gain.

Backlash only costs you when a joint REVERSES. A raster sine that draws
left-to-right, then right-to-left, reverses every joint at every sweep end.
Drawing one way and lifting on the return keeps every joint turning the same
way through the whole stroke, so the gear flanks never change contact.

This checks whether that is actually true for THIS arm on THIS path -- a joint
can still reverse mid-stroke even in a one-way sweep, and then the strategy
buys nothing.
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.expanduser("~/ros2_ws/src/Rsine"))
from Rsine.sine_path import DrawingPlane, sine_waypoints
from sine_check import ik, fk_full


def joint_traj(plane, amplitude, length, n=60):
    pos, _ = sine_waypoints(plane, amplitude=amplitude, length=length, n_points=n)
    pen = plane.n
    q = np.array([0., 0.9, -1.4, 0., -0.5, 0.])
    Q, ok = [], 0
    for p in pos:
        q, good, e = ik(np.asarray(p), pen, q)
        Q.append(q.copy()); ok += good
    return np.array(Q), ok, n


def reversals(Q):
    """How many times does each joint change direction along the stroke?"""
    d = np.diff(Q, axis=0)
    sign = np.sign(d)
    rev = np.zeros(6, dtype=int)
    for j in range(6):
        s = sign[:, j]
        s = s[s != 0]
        rev[j] = int((np.diff(s) != 0).sum())
    return rev


if __name__ == "__main__":
    print("="*76)
    print("DOES A ONE-WAY SWEEP ACTUALLY KEEP EVERY JOINT UNIDIRECTIONAL?")
    print("="*76)
    for x in (0.24, 0.30):
        pl = DrawingPlane.vertical_board(x=x, z_center=0.20)
        Q, ok, n = joint_traj(pl, 0.04, 0.14)
        rev = reversals(Q)
        print(f"\n  board x = {x*1000:.0f} mm, {ok}/{n} points solved")
        print(f"  {'joint':>6s} {'reversals':>10s} {'travel deg':>11s}")
        for j in range(6):
            print(f"  {'J'+str(j+1):>6s} {rev[j]:10d} {np.degrees(np.ptp(Q[:,j])):11.1f}")
        clean = (rev == 0).sum()
        print(f"  -> {clean}/6 joints never reverse. "
              + ("backlash fully avoided" if clean == 6 else
                 f"{6-clean} joint(s) still reverse -> partial gain only"))

    print("\n" + "="*76)
    print("WHY THIS MATTERS")
    print("="*76)
    print("""
  A sine is a WAVE: the pen goes up and down as it advances. The joints that
  produce the wave MUST reverse -- that is the shape. Only the joints producing
  the ADVANCE stay one-way.

  So the honest gain is partial: the advance joints (mostly J1) hold their
  flanks, while the wave joints (J2/J3/J5) reverse twice per cycle.
""")
