"""
The sine trace on a VERTICAL board and on a HORIZONTAL plate, side by side.

The vertical board is the shipped demonstration and it solves beautifully. The
horizontal plate is the same curve on a table, and it is a genuinely harder
problem for one reason: the tool has to point DOWN.

On a vertical board the tool points forward (+X), roughly along the forearm, so
the wrist barely has to do anything. On a table it must point at the floor,
which is most of a right angle away from the arm's natural reach direction --
and J5's travel was narrowed to -91..+49 deg to stop the J4 housing striking
the J6 body. That narrowing is what this measures against.

Everything is swept rather than asserted: board distance and height for the
vertical case, plate height and reach for the horizontal one.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.expanduser("~/ros2_ws/src/Rsine"))
from Rsine.sine_path import DrawingPlane, sine_waypoints      # noqa: E402
from sine_check import ik, fk_full                            # noqa: E402
import plan_sine as PS                                        # noqa: E402

AMP, LEN, N, CYC = PS.AMP, PS.LEN, PS.N, PS.CYCLES


def solve(plane, n=120, w_cont=PS.W_CONT, w_ori=PS.W_ORI, tool=0.0, seed=None):
    """Track the curve from a fixed seed; return the usual four metrics."""
    pos, _ = sine_waypoints(plane, amplitude=AMP, length=LEN, n_points=n,
                            cycles=CYC)
    pen = plane.n
    q = np.array([0., 0.9, -1.4, 0., -0.5, 0.]) if seed is None else seed
    E, T, Q = [], [], []
    for k, p in enumerate(pos):
        q, ok, e = ik(np.asarray(p), pen, q, w_cont=w_cont, w_ori=w_ori,
                      track=(k > 0), tip=tool)
        pa, z = fk_full(q)
        E.append(e * 1000)
        T.append(np.degrees(np.arccos(np.clip(np.dot(z, pen), -1, 1))))
        Q.append(q.copy())
    Q = np.array(Q)
    return (float(np.sqrt(np.mean(np.square(E)))), float(max(E)),
            float(np.sqrt(np.mean(np.square(T)))), float(max(T)),
            float(np.degrees(np.abs(np.diff(Q, axis=0))).max()), Q)


def main():
    print("=" * 82)
    print("SINE TRACE — VERTICAL BOARD vs HORIZONTAL PLATE")
    print("=" * 82)

    print("\n1. VERTICAL BOARD — the shipped demonstration")
    print(f"   {'board x':>8s} {'z centre':>9s} {'rms mm':>8s} {'max mm':>8s} "
          f"{'tilt rms':>9s} {'step°':>7s}")
    print("   " + "-" * 56)
    best_v = None
    for bx in (0.26, 0.30, 0.34):
        for zc in (0.20, 0.22, 0.24):
            pl = DrawingPlane.vertical_board(x=bx, z_center=zc)
            r = solve(pl)
            if best_v is None or r[0] < best_v[0][0]:
                best_v = (r, bx, zc)
            print(f"   {bx*1000:8.0f} {zc*1000:9.0f} {r[0]:8.3f} {r[1]:8.3f} "
                  f"{r[2]:9.3f} {r[4]:7.2f}")

    print("\n2. HORIZONTAL PLATE — the same curve on a table")
    print("   the tool must point DOWN, which is what J5's narrowed range fights")
    print(f"   {'plate z':>8s} {'x centre':>9s} {'rms mm':>8s} {'max mm':>8s} "
          f"{'tilt rms':>9s} {'step°':>7s}")
    print("   " + "-" * 56)
    best_h = None
    for pz in (0.06, 0.10, 0.14, 0.18):
        for xc in (0.16, 0.22, 0.28):
            pl = DrawingPlane.flat_plate(z=pz, x_center=xc)
            # a downward-pointing pen needs a different starting posture
            r = solve(pl, seed=np.array([0., 1.2, -1.9, 0., -0.9, 0.]))
            if best_h is None or r[0] < best_h[0][0]:
                best_h = (r, pz, xc)
            print(f"   {pz*1000:8.0f} {xc*1000:9.0f} {r[0]:8.3f} {r[1]:8.3f} "
                  f"{r[2]:9.3f} {r[4]:7.2f}")

    print("\n" + "=" * 82)
    (rv, bx, zc), (rh, pz, xc) = best_v, best_h
    print(f"  VERTICAL   best: board {bx*1000:.0f} mm, z {zc*1000:.0f} mm")
    print(f"             {rv[0]:.3f} mm rms, {rv[1]:.3f} max, tilt {rv[2]:.3f}° rms, "
          f"step {rv[4]:.2f}°")
    print(f"  HORIZONTAL best: plate z {pz*1000:.0f} mm, x {xc*1000:.0f} mm")
    print(f"             {rh[0]:.3f} mm rms, {rh[1]:.3f} max, tilt {rh[2]:.3f}° rms, "
          f"step {rh[4]:.2f}°")
    print(f"\n  horizontal is {rh[0]/max(rv[0],1e-9):.0f}x worse on position "
          f"and {rh[2]/max(rv[2],1e-9):.0f}x on tilt")
    print("=" * 82)
    return best_v, best_h


if __name__ == "__main__":
    main()
