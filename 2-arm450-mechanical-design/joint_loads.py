"""
ARM-450 — which joint bears which load.

Full static gravity torque on every joint, swept over the reachable configuration
space, by recursive Newton-Euler with zero velocity and acceleration.

Method
------
Forward pass: place every link frame and every centre of mass in world coordinates.
Backward pass: accumulate force and moment from the tool inward. The torque a joint
must hold is the component of the accumulated moment along that joint's own axis:

    f_i   = f_{i+1} + m_i * g
    n_i   = n_{i+1} + (p_{ci} - p_i) x m_i*g + (p_{i+1} - p_i) x f_{i+1}
    tau_i = n_i . z_i

Sign convention: tau is what the actuator must SUPPLY to hold the pose.
"""

import numpy as np

G_VEC = np.array([0.0, 0.0, -9.80665])

# ---------------------------------------------------------------------------
# chain: (name, origin offset from previous joint (m), axis, link mass, servo mass)
# link mass acts at the MIDPOINT of that link's own segment.
# servo mass sits AT the joint.
# ---------------------------------------------------------------------------
CHAIN = [
    ("J1", np.array([0, 0, 0.050]), np.array([0, 0, 1.]), 0.100, 0.060),
    ("J2", np.array([0, 0, 0.040]), np.array([0, 1, 0.]), 0.145, 0.080),  # ST3250
    ("J3", np.array([0, 0, 0.145]), np.array([0, 1, 0.]), 0.130, 0.060),
    ("J4", np.array([0, 0, 0.080]), np.array([0, 0, 1.]), 0.060, 0.060),
    ("J5", np.array([0, 0, 0.065]), np.array([0, 1, 0.]), 0.060, 0.060),
    ("J6", np.array([0, 0, 0.035]), np.array([0, 0, 1.]), 0.090, 0.060),
]
TCP_OFFSET = np.array([0, 0, 0.035])
PAYLOAD = 0.300

# A tool whose centre of mass is offset from the wrist roll axis — this is what
# actually loads the roll joints J4 and J6.
# The offset must be perpendicular to BOTH the roll axis and gravity to produce
# a moment. Local +Y is perpendicular to the link axis (local +Z), so with the
# arm horizontal this offset stays horizontal and does load the roll joints.
# An offset along local +X would point straight down in that pose and produce
# nothing — a degenerate case that is easy to demo by accident.
TOOL_LATERAL = np.array([0.0, 0.030, 0.0])

SERVOS = {"ST3215": dict(stall=2.94, cont=0.88),
          "ST3250": dict(stall=4.90, cont=1.47)}
FITTED = ["ST3215", "ST3250", "ST3215", "ST3215", "ST3215", "ST3215"]


def rot(axis, q):
    a = axis / np.linalg.norm(axis)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(q) * K + (1 - np.cos(q)) * K @ K


def kinematics(q, tool_offset=True, tool_reach=0.0):
    """Return joint origins p[i], joint axes z[i], and CoM positions."""
    R = np.eye(3)
    p = np.zeros(3)
    origins, axes, coms, masses = [], [], [], []
    for i, (name, off, ax, m_link, m_servo) in enumerate(CHAIN):
        p = p + R @ off
        R = R @ rot(ax, q[i])
        origins.append(p.copy())
        axes.append((R @ ax).copy())
        # servo lumped at the joint
        coms.append(p.copy())
        masses.append(m_servo)
        # link mass at the midpoint of the NEXT segment (this link's own body)
        nxt = CHAIN[i + 1][1] if i + 1 < len(CHAIN) else TCP_OFFSET
        coms.append(p + R @ (nxt / 2.0))
        masses.append(m_link)
    tcp = p + R @ TCP_OFFSET
    # A FITTED TOOL moves the load further out along the tool axis. The lever
    # arm is what sizes J2 and J3, so a 75 g gripper 42 mm past the flange is
    # not equivalent to 75 g AT the flange -- it is the offset that costs.
    work = tcp + R @ np.array([0.0, 0.0, tool_reach])
    pay_pos = work + (R @ TOOL_LATERAL if tool_offset else np.zeros(3))
    return np.array(origins), np.array(axes), np.array(coms), np.array(masses), tcp, pay_pos


def joint_torques(q, payload=PAYLOAD, tool_offset=True, tool_reach=0.0):
    """Static gravity torque each joint must supply, N.m."""
    origins, axes, coms, masses, tcp, pay_pos = kinematics(q, tool_offset,
                                                           tool_reach)

    # every gravity load as (position, force)
    loads = [(coms[k], masses[k] * G_VEC) for k in range(len(masses))]
    if payload > 0:
        loads.append((pay_pos, payload * G_VEC))

    tau = np.zeros(6)
    for i in range(6):
        pi = origins[i]
        n = np.zeros(3)
        for (pos, f) in loads:
            # only loads OUTBOARD of joint i load that joint. Everything at or
            # beyond joint i+1 is outboard; the servo at joint i is not.
            n = n + np.cross(pos - pi, f)
        tau[i] = -np.dot(n, axes[i])
    # subtract inboard contributions: recompute per joint using only outboard mass
    tau = np.zeros(6)
    for i in range(6):
        pi = origins[i]
        n = np.zeros(3)
        for k in range(len(masses)):
            # index k: even = servo at joint k//2, odd = link body of joint k//2
            jidx = k // 2
            if jidx < i:
                continue
            if jidx == i and k % 2 == 0:
                continue          # this joint's own servo sits on the axis, no moment
            n = n + np.cross(coms[k] - pi, masses[k] * G_VEC)
        if payload > 0:
            n = n + np.cross(pay_pos - pi, payload * G_VEC)
        tau[i] = -np.dot(n, axes[i])
    return tau


def sweep(n=60000, seed=0, payload=PAYLOAD, tool_offset=True, tool_reach=0.0):
    """Random sweep of the configuration space; return worst case per joint."""
    rng = np.random.default_rng(seed)
    lim = np.radians([165, 115, 150, 165, 110, 175])
    best = np.zeros(6)
    best_q = [None] * 6
    for _ in range(n):
        q = rng.uniform(-lim, lim)
        t = np.abs(joint_torques(q, payload, tool_offset, tool_reach))
        for i in range(6):
            if t[i] > best[i]:
                best[i] = t[i]
                best_q[i] = q.copy()
    return best, best_q


def inertial_J1(alpha=3.0):
    """
    J1 sees NO gravity torque (its axis is vertical). What loads it is INERTIA.
    Rotational inertia of the outstretched arm about the vertical base axis,
    times an angular acceleration alpha (rad/s^2).
    """
    q = np.zeros(6)
    q[1] = np.pi / 2                       # arm horizontal = worst case
    origins, axes, coms, masses, tcp, pay_pos = kinematics(q)
    I = 0.0
    for k in range(len(masses)):
        r = np.linalg.norm(coms[k][:2])    # distance from the vertical axis
        I += masses[k] * r ** 2
    I += PAYLOAD * np.linalg.norm(pay_pos[:2]) ** 2
    return I, I * alpha


if __name__ == "__main__":
    print("=" * 82)
    print("1. THE POSE EVERYONE CHECKS — arm horizontal, fully extended")
    print("=" * 82)
    q = np.zeros(6)
    q[1] = np.pi / 2
    t = joint_torques(q)
    for i, (name, *_rest) in enumerate(CHAIN):
        print(f"  {name}  {t[i]:+7.3f} N.m")

    print("\n" + "=" * 82)
    print("2. WORST CASE OVER THE WHOLE CONFIGURATION SPACE  (60k random poses)")
    print("=" * 82)
    best, best_q = sweep()
    print(f"{'joint':6s} {'worst N.m':>10s} {'servo':>9s} {'stall':>7s} "
          f"{'cont.':>7s} {'SF cont':>8s}  verdict")
    print("-" * 82)
    for i, (name, *_r) in enumerate(CHAIN):
        s = SERVOS[FITTED[i]]
        sf = s["cont"] / best[i] if best[i] > 1e-9 else float("inf")
        v = ("OVER-SPECCED" if sf > 5 else
             "ok" if sf >= 1.5 else
             "MARGINAL" if sf >= 1.0 else "UNDER-SPECCED")
        print(f"{name:6s} {best[i]:10.3f} {FITTED[i]:>9s} {s['stall']:7.2f} "
              f"{s['cont']:7.2f} {sf:8.2f}  {v}")

    print("\nworst-case configurations (deg):")
    for i, (name, *_r) in enumerate(CHAIN):
        if best_q[i] is not None:
            print(f"  {name}: " + " ".join(f"{np.degrees(a):+7.1f}" for a in best_q[i]))

    print("\n" + "=" * 82)
    print("3. J1 — THE JOINT GRAVITY NEVER LOADS")
    print("=" * 82)
    print("J1's axis is VERTICAL, and gravity acts vertically, so the gravity")
    print("moment about it is identically zero in ANY static pose.")
    print("What loads J1 is INERTIA during acceleration:")
    for alpha in (1.0, 3.0, 5.0, 10.0):
        I, tau = inertial_J1(alpha)
        print(f"   I = {I:.5f} kg.m^2,  alpha = {alpha:5.1f} rad/s^2 "
              f"->  tau = {tau:.3f} N.m")

    print("\n" + "=" * 82)
    print("4. THE ROLL JOINTS J4 AND J6 — loaded only by an OFFSET load")
    print("=" * 82)
    print(f"With the tool CoM on the roll axis (no offset):")
    q2 = np.zeros(6); q2[1] = np.pi/2
    t0 = joint_torques(q2, tool_offset=False)
    print(f"   J4 = {t0[3]:.4f} N.m   J6 = {t0[5]:.4f} N.m")
    print(f"With a {np.linalg.norm(TOOL_LATERAL)*1000:.0f} mm lateral tool offset:")
    t1 = joint_torques(q2, tool_offset=True)
    print(f"   J4 = {t1[3]:.4f} N.m   J6 = {t1[5]:.4f} N.m")
    print("-> a roll joint carries nothing until the load is offset from its axis.")
    print("   Tool eccentricity, not payload weight, is what sizes J4 and J6.")

    print("\n" + "=" * 82)
    print("5. PAYLOAD SENSITIVITY — how much of each joint's load is the payload")
    print("=" * 82)
    bp, _ = sweep(20000, seed=1, payload=PAYLOAD)
    bn, _ = sweep(20000, seed=1, payload=0.0)
    print(f"{'joint':6s} {'with 300g':>10s} {'no payload':>11s} {'payload share':>14s}")
    print("-" * 82)
    for i, (name, *_r) in enumerate(CHAIN):
        share = (bp[i] - bn[i]) / bp[i] * 100 if bp[i] > 1e-9 else 0.0
        print(f"{name:6s} {bp[i]:10.3f} {bn[i]:11.3f} {share:13.0f}%")
