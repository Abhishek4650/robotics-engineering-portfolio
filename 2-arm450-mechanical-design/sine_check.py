"""
Can ARM-450 trace a sine with the pen NORMAL to a vertical board?

That is the immediate task (and the prerequisite for the docking work).
Position alone is 3 DOF; holding the pen normal adds 2 more, so it is a 5-DOF
task and this is a 6-DOF arm -- there should be one redundant DOF to spare.

Damped least-squares IK on the URDF chain, checking every point on the path.
"""
import numpy as np, xml.etree.ElementTree as ET

r = ET.parse('arm450.urdf').getroot()
J = []
for j in r.findall('joint'):
    o = j.find('origin'); ax = j.find('axis'); lim = j.find('limit')
    J.append((j.get('type'), np.array([float(v) for v in o.get('xyz').split()]),
              np.array([float(v) for v in ax.get('xyz').split()]) if ax is not None else None,
              (float(lim.get('lower')), float(lim.get('upper'))) if lim is not None else None))
LIM = np.array([l for t,_,_,l in J if t == 'revolute'])

def R(a, q):
    a = a/np.linalg.norm(a)
    K = np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]])
    return np.eye(3) + np.sin(q)*K + (1-np.cos(q))*K@K

def fk_full(qs):
    """Return TCP position and the tool Z axis (the pen direction)."""
    T = np.eye(4); i = 0
    for t, xyz, ax, _ in J:
        A = np.eye(4); A[:3,3] = xyz
        if t == 'revolute':
            A[:3,:3] = R(ax, qs[i]); i += 1
        T = T @ A
    return T[:3,3], T[:3,:3] @ np.array([0,0,1.])

def jac(q, eps=1e-6):
    p0, z0 = fk_full(q)
    Jm = np.zeros((6, 6))
    for k in range(6):
        dq = q.copy(); dq[k] += eps
        p1, z1 = fk_full(dq)
        Jm[:3,k] = (p1-p0)/eps
        Jm[3:,k] = (z1-z0)/eps
    return Jm, p0, z0

from scipy.optimize import least_squares


def ik(p_t, z_t, q0, w_ori=0.05, w_cont=0.0, lock_j6=True, track=False,
       tip=0.0):
    """Bounded least-squares IK. The hand-rolled DLS solver stalled at joint
    limits and carried a bad seed forward; least_squares respects the bounds
    natively and is far more robust. Falls back to random restarts."""
    def res(qf):
        # J6 rolls the tool about its OWN axis, which is the pen direction --
        # a pen is rotationally symmetric, so J6 does nothing for this task and
        # is pure redundancy. Locking it turns an under-determined 6-DOF solve
        # (5 task constraints, infinite solutions, solver wanders 135 deg between
        # waypoints) into an exactly-determined 5-DOF one.
        q = np.concatenate([qf, [0.0]]) if lock_j6 else qf
        p, z = fk_full(q)
        # CONTROL THE TOOL TIP, not the bare flange.
        # fk_full returns the TCP -- the J6 tool face. With a gripper fitted the
        # working point is `tip` metres further along the tool axis, so a path
        # solved for the TCP puts the FLANGE on the board and the fingers 42 mm
        # through it. Solving p + z*tip against the target puts the actual tip
        # on the curve, and because z is what the orientation residual is
        # already driving, the two constraints stay consistent.
        if tip:
            p = p + z * tip
        r = [(p_t - p), w_ori * (z_t - z)]
        if w_cont > 0.0:
            # NULL-SPACE REGULARISATION, not global damping.
            # J4 and J6 are both roll axes; when J5 -> 0 they go collinear and
            # only their SUM is determined, so the solver wanders along that null
            # direction and jumps up to 45 deg between adjacent waypoints.
            # Penalising ALL joints equally fixed the jumping but wrecked accuracy
            # (0.02 -> 8.8 mm rms) because it also fought J1/J2/J3/J5, which are
            # doing the actual task. Damp ONLY the redundant pair.
            w = np.array([0.0, 0.0, 0.0, 1.0, 0.0, 1.0]) * w_cont
            d = (q0 - q)
            r.append((w * d)[:5] if lock_j6 else w * d)
        return np.concatenate(r)
    # Always try several seeds. Restricting to [q0] whenever w_cont > 0 meant a
    # single bad solve at the first waypoint poisoned the entire path (rms went
    # 0.02 -> 8.4 mm). The continuity residual already biases the result toward
    # q0, so extra seeds cost nothing and rescue a stuck start.
    seeds = [q0, np.array([0., 0.9, -1.4, 0., -0.5, 0.]),
             np.array([0., 0.6, -1.0, 0., -0.8, 0.]),
             np.array([0., 1.2, -1.8, 0., -0.2, 0.])]
    # TRACKING MODE: once the first waypoint is solved, every later one starts
    # ONLY from the previous solution. Offering alternative seeds mid-path lets
    # the solver hop to a far branch that scores marginally better and the arm
    # snaps 135 deg. Multi-seed is for acquiring the first pose, not for tracking.
    if track:
        seeds = [q0]
    n = 5 if lock_j6 else 6
    LO, HI = LIM[:n, 0], LIM[:n, 1]
    seeds = [s0[:n] for s0 in seeds]
    # Score seeds on the FULL residual, not on position error alone. Scoring by
    # position only let a distant seed win by a hair and threw away continuity,
    # putting the 135 deg J4 jumps straight back.
    best, bcost, bep = None, 1e18, 1e9
    for s0 in seeds:
        s0 = np.clip(s0, LO + 1e-6, HI - 1e-6)
        r = least_squares(res, s0, bounds=(LO, HI),
                          xtol=1e-12, ftol=1e-12, max_nfev=500)
        qx = np.concatenate([r.x, [0.0]]) if lock_j6 else r.x
        p, z = fk_full(qx)
        # score the CONTROLLED point. Leaving this as the bare TCP made every
        # tip-offset solve report ~42 mm of error -- the tool length -- so the
        # acceptance test and the collision-seed filter both rejected perfectly
        # good poses.
        ep, eo = np.linalg.norm(p_t - (p + z * tip)), np.linalg.norm(z_t - z)
        cost = float(np.sum(res(r.x) ** 2))
        if cost < bcost:
            best, bcost, bep = qx, cost, ep
    p, z = fk_full(best)
    ok = (np.linalg.norm(p_t - (p + z * tip)) < 1e-4) and (np.linalg.norm(z_t - z) < 0.02)
    return best, ok, bep

if __name__ == "__main__":
    # Guarded 2026-08-20. This sweep was at MODULE level, so every
    # `from sine_check import ik` -- plan_sine.py, the gate, anything --
    # silently ran a 200-pose IK sweep before doing its own work.
    print("SINE TRACE — pen normal to a vertical board\n")
    print(f"  {'board X':>8s} {'amp':>6s} {'span':>6s} {'solved':>8s} {'max err':>10s}")
    print("  " + "-"*46)
    for bx in (0.16, 0.20, 0.24, 0.28):
        for amp in (0.03, 0.05):
            ys = np.linspace(-0.07, 0.07, 25)
            zt = 0.20
            z_t = np.array([1.0, 0, 0])           # pen points +X, INTO the board.
            # -X was my error: it points back at the base and needs the wrist to
            # fold 180 deg, outside the +/-110 deg J5 limit.
            q = np.array([0, 0.9, -1.4, 0, -0.5, 0])
            ok = 0; worst = 0.0
            for y in ys:
                p_t = np.array([bx, y, zt + amp*np.sin(2*np.pi*y/0.07)])
                q, good, err = ik(p_t, z_t, q)
                ok += good; worst = max(worst, err)
            print(f"  {bx*1000:7.0f} {amp*1000:5.0f} {140:5.0f} {ok:5d}/25 {worst*1000:9.2f} mm")
    print("\n  amp/span/err in mm. 'solved' = points reaching < 0.2 mm with the pen normal.")
