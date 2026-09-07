"""
Run the Rsine sine-tracing task on the ARM-450 we designed.

Rsine's DrawingPlane / sine_waypoints are pure geometry and robot-agnostic, so
they are IMPORTED UNCHANGED from the frozen Rsine package. Only the kinematics
are swapped: myCobot Modified-DH -> the arm450 URDF chain.

This answers the question the whole mechanical design exists to serve:
can ARM-450 trace a sine with the pen held normal to the surface?
"""
import sys, os
import numpy as np

sys.path.insert(0, os.path.expanduser("~/ros2_ws/src/Rsine"))
from Rsine.sine_path import DrawingPlane, sine_waypoints      # noqa: E402
from sine_check import fk_full, LIM, ik                       # arm450 kinematics


def trace(plane, amplitude, length, n=40, label="", flip=False):
    pos, _ = sine_waypoints(plane, amplitude=amplitude, length=length, n_points=n)
    # The pen must point INTO the surface. For a vertical board the plane
    # normal already points away from the base (+X). For a flat plate the
    # normal points UP (+Z) and must be flipped, or the arm tries to draw on
    # the underside of the table.
    pen = -plane.n if flip else plane.n
    q = np.array([0., 0.9, -1.4, 0., -0.5, 0.])
    solved, errs, ori = 0, [], []
    for p in pos:
        q, ok, e = ik(np.asarray(p), pen, q)
        _, z = fk_full(q)
        errs.append(e * 1000)
        ori.append(np.degrees(np.arccos(np.clip(np.dot(z, pen), -1, 1))))
        solved += ok
    errs, ori = np.array(errs), np.array(ori)
    print(f"  {label:26s} {solved:3d}/{n}  pos rms {np.sqrt((errs**2).mean()):6.3f} mm"
          f"  max {errs.max():6.2f} mm   pen tilt max {ori.max():5.1f} deg")
    return solved, errs, ori


if __name__ == "__main__":
    print("RSINE ON ARM-450 — pen normal to the surface\n")
    print("  DrawingPlane + sine_waypoints imported unchanged from the frozen")
    print("  Rsine package; only the kinematics are arm450's.\n")
    print(f"  {'configuration':26s} {'solved':>7s}  {'position error':>26s}  {'orientation'}")
    print("  " + "-" * 92)

    print("\n  VERTICAL BOARD (pen horizontal, +X into the board)")
    for x in (0.20, 0.24, 0.28, 0.30):
        pl = DrawingPlane.vertical_board(x=x, z_center=0.20)
        trace(pl, 0.04, 0.14, label=f"board at x = {x*1000:.0f} mm")

    print("\n  HORIZONTAL TABLE (pen pointing down)")
    for z in (0.06, 0.10, 0.14):
        pl = DrawingPlane.flat_plate(z=z, x_center=0.22)
        trace(pl, 0.04, 0.14, label=f"table at z = {z*1000:.0f} mm", flip=True)
