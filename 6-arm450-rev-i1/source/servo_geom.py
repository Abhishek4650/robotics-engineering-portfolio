#!/usr/bin/env python3
"""
ST3215 geometry MEASURED from the user's own `Motor.stl`, expressed in the
frame the joint actually uses: +Z is the OUTPUT AXIS.

Why this file exists
--------------------
`fixparams.py` carries SERVO_L/W/T = 45.22 / 37.25 / 24.72 and derives
    BAY_W = SERVO_W + 2*BAY_CLR = 38.05
    BAY_T = SERVO_T + BAY_CLR + 1.5 = 26.62
In `fork_pro.fork()` the bay is cut rect(BAY_L, BAY_W) extruded BAY_T along
+Z, and +Z is the joint axis (every bearing bore is a circle() on XY). So
BAY_T is the dimension along the OUTPUT AXIS.

Measured from Motor.stl, along the output axis:
    mounting face .. back of cable boss = 33.10 mm
    mounting face .. face of horn disc  =  4.50 mm   (goes the other way)
The case cross-section normal to the output axis is 45.22 x 24.72.

So 37.25 and 24.72 are SWAPPED with respect to the orientation the joint
axis forces: BAY_W gets 38.05 where 25.52 is needed (13.33 mm of slop, the
servo can rattle and rotate), and BAY_T gets 26.62 where 33.50 is needed
(6.88 mm short, the servo does not fit).

Both numbers here are derived from the mesh, not typed.
"""
import numpy as np
import trimesh

MOTOR_STL = "/home/user/roboARM/Robotic_arm_design/Motor.stl"

# --- measured, output axis = mesh Y ---------------------------------------
BELOW_FACE = 33.10     # mounting face -> back of cable boss
ABOVE_FACE = 4.50      # mounting face -> outer face of horn disc
CASE_L = 45.22         # normal to output axis
CASE_W = 24.72         # normal to output axis
HORN_DISC_D = 19.20
BOSS_D = 40.00         # the O40 shoulder between face and horn

CLR = 0.40             # per side, same value fork_pro uses

# --- the orientation lock -------------------------------------------------
# The four front-face case screws CANNOT be used on J3/J5: their bolt circle
# is r = 13.92 mm, which falls inside the O38 bearing seat (r = 19.00) that
# carries the outer race. The seat is structural and cannot be shrunk. The
# back face cannot be bolted either -- the photographs show the two JST bus
# connectors and the rear bearing boss occupying its centre.
#
# So the lock is a PINCH plus a STRAP, which is what the user's own proven
# `motor fixer.stl` does on the arm they have already built and run: a
# 24.50 mm channel gripping the 24.72 mm case face, i.e. -0.22 mm of
# interference. That interference IS the orientation lock; the strap then
# carries the case into the cradle so joint torque goes through the pocket
# walls in bearing rather than through screws.
PINCH = 24.50          # channel width on the case's 24.72 face (-0.22)
PINCH_INTERF = CASE_W - PINCH

# --- bay, in the joint frame (+Z = output axis) ---------------------------
BAY_L_Z = CASE_L + 2 * CLR     # 46.02  along X, clearance
BAY_W_Z = PINCH                # 24.50  along Y, PINCH -- not a clearance
BAY_T_Z = BELOW_FACE + CLR     # 33.50  along Z


def measure(stl=MOTOR_STL, tol=0.15):
    """Re-derive the constants above from the mesh and check them."""
    m = trimesh.load(stl)
    m.apply_translation(-m.bounds.mean(axis=0))
    b = m.bounds
    # the output axis is the one carrying the O19.2 circular boss
    best = None
    for ax in range(3):
        for sgn in (+1, -1):
            t = (b[1][ax] if sgn > 0 else b[0][ax]) - sgn * 0.6
            o3 = [0, 0, 0]; o3[ax] = t
            n3 = [0, 0, 0]; n3[ax] = 1
            sl = m.section(plane_origin=o3, plane_normal=n3)
            if sl is None:
                continue
            v = np.asarray(sl.vertices)
            o = [i for i in range(3) if i != ax]
            e0, e1 = np.ptp(v[:, o[0]]), np.ptp(v[:, o[1]])
            if abs(e0 - e1) < 0.3 and abs(e0 - HORN_DISC_D) < 0.5:
                best = (ax, sgn, e0)
    if best is None:
        raise RuntimeError("could not find the horn boss")
    ax, sgn, d = best
    # mounting face: last slab whose cross-section is still full case width
    lo, hi = b[0][ax], b[1][ax]
    face = None
    for t in np.linspace(lo + 0.05, hi - 0.05, 400)[::sgn]:
        o3 = [0, 0, 0]; o3[ax] = t
        n3 = [0, 0, 0]; n3[ax] = 1
        sl = m.section(plane_origin=o3, plane_normal=n3)
        if sl is None:
            continue
        v = np.asarray(sl.vertices)
        o = [i for i in range(3) if i != ax]
        if max(np.ptp(v[:, o[0]]), np.ptp(v[:, o[1]])) > CASE_L - 1.0:
            face = t
    back = lo if sgn > 0 else hi
    below = abs(face - back)
    above = abs((hi if sgn > 0 else lo) - face)
    ok = (abs(below - BELOW_FACE) < tol) and (abs(above - ABOVE_FACE) < tol)
    return dict(axis="XYZ"[ax], sign=sgn, horn_d=d, face=face,
                below=below, above=above, ok=ok)


if __name__ == "__main__":
    r = measure()
    print("ST3215 measured from", MOTOR_STL)
    print("   output axis      mesh %s%s" % ("+-"[r["sign"] < 0], r["axis"]))
    print("   horn disc        O%.2f   (constant %.2f)" % (r["horn_d"], HORN_DISC_D))
    print("   below face       %.2f    (constant %.2f)" % (r["below"], BELOW_FACE))
    print("   above face       %.2f    (constant %.2f)" % (r["above"], ABOVE_FACE))
    print("   agree            %s" % ("YES" if r["ok"] else "NO"))
    print()
    print("   bay in joint frame  %.2f x %.2f x %.2f  (X, Y, Z=output)"
          % (BAY_L_Z, BAY_W_Z, BAY_T_Z))
