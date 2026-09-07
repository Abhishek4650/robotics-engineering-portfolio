"""
Cross-check the Craig-DH kinematics against ikpy — an outside package.

Three implementations that share no code have to agree:

  1. dh_kinematics.fk        modified-DH, the user's convention, written here
  2. sine_check.fk_full      the URDF chain the rest of the project runs on
  3. ikpy                    a third-party library, fed the URDF directly

Agreement between 1 and 2 proves the DH table. Agreement with 3 proves that
neither of the first two shares a mistake with the other, which is the failure
mode a self-written cross-check cannot catch.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dh_kinematics as K
import sine_check as SC

URDF = os.path.join(HERE, "arm450.urdf")
R = []


def chk(ok, name, det):
    R.append((bool(ok), name, det))


def main():
    print("=" * 78)
    print("KINEMATICS CROSS-CHECK — Craig DH vs URDF vs ikpy")
    print("=" * 78)

    # ikpy will not import cleanly here without a shim, and the reason is worth
    # recording: sympy stringifies numpy scalars, numpy 2 changed their repr to
    # "np.float64(1.0)", and sympy then cannot parse its own input. ikpy converts
    # numpy scalars internally, so it dies before doing any kinematics. Route the
    # converter through float() instead of the string path.
    import sympy.core.sympify as _sy
    import sympy.core.numbers as _sn
    from sympy.core.numbers import Float, Integer

    def _conv(a, precision=None):
        if isinstance(a, np.ndarray) and a.ndim == 0:
            a = a.item()
        if isinstance(a, np.integer):
            return Integer(int(a))
        return Float(float(a))
    _sy._convert_numpy_types = _conv
    _sn._convert_numpy_types = _conv

    import logging
    import warnings
    logging.getLogger("ikpy").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore", module="ikpy")
    from ikpy.chain import Chain
    chain = Chain.from_urdf_file(URDF, base_elements=["base_link"])
    mask = [bool(getattr(l, "joint_type", "fixed") != "fixed") for l in chain.links]
    chain.active_links_mask = mask
    n_act = sum(mask)
    print(f"\n  ikpy chain: {len(chain.links)} links, {n_act} actuated")

    rng = np.random.default_rng(0)
    QS = [rng.uniform(-1.2, 1.2, 6) for _ in range(200)]

    def ikpy_fk(q):
        full = np.zeros(len(chain.links))
        k = 0
        for i, m in enumerate(mask):
            if m:
                full[i] = q[k]; k += 1
        return chain.forward_kinematics(full)

    e_du, e_di, e_ui = 0.0, 0.0, 0.0
    ez = 0.0
    for q in QS:
        Td = K.fk(q); pd = Td[:3, 3] / 1000.0
        pu, zu = SC.fk_full(q)
        Ti = ikpy_fk(q); pi = Ti[:3, 3]
        e_du = max(e_du, np.linalg.norm(pd - pu) * 1000)
        e_di = max(e_di, np.linalg.norm(pd - pi) * 1000)
        e_ui = max(e_ui, np.linalg.norm(pu - pi) * 1000)
        ez = max(ez, np.linalg.norm(Td[:3, 2] - zu))

    chk(e_du < 1e-6, "FK: Craig DH == URDF chain", f"worst {e_du:.2e} mm over 200 poses")
    chk(e_di < 1e-6, "FK: Craig DH == ikpy", f"worst {e_di:.2e} mm")
    chk(e_ui < 1e-6, "FK: URDF chain == ikpy", f"worst {e_ui:.2e} mm")
    chk(ez < 1e-9, "tool axis agrees", f"worst {ez:.2e}")

    # --- Jacobian: propagation vs finite difference
    ej = max(np.abs(K.jacobian(q) - K.jacobian_numeric(q)).max() for q in QS[:50])
    chk(ej < 1e-3, "Jacobian: velocity propagation == finite difference",
        f"worst element {ej:.2e} (mm/rad and rad/rad)")

    # --- IK round trip, both solvers
    print("\n  IK ROUND TRIP — solve for a reachable pose, then FK back")
    err_dh, err_ik = [], []
    for q in QS[:40]:
        T = K.fk(q); p = T[:3, 3]
        qs, e = K.ik(p, q0=q + rng.normal(0, 0.05, 6))
        err_dh.append(e)
        tgt = np.eye(4); tgt[:3, 3] = p / 1000.0
        sol = chain.inverse_kinematics(p / 1000.0,
                                       initial_position=np.zeros(len(chain.links)))
        err_ik.append(np.linalg.norm(chain.forward_kinematics(sol)[:3, 3] - p / 1000.0) * 1000)
    chk(np.median(err_dh) < 0.01, "IK (Craig DH + propagated Jacobian) converges",
        f"median {np.median(err_dh):.2e} mm, worst {max(err_dh):.2e} mm")
    chk(np.median(err_ik) < 1.0, "IK (ikpy) converges",
        f"median {np.median(err_ik):.3f} mm, worst {max(err_ik):.3f} mm")

    print()
    for ok, name, det in R:
        print(f"  [{' PASS ' if ok else ' FAIL '}] {name:48s} {det}")
    bad = [r for r in R if not r[0]]
    print("\n" + "=" * 78)
    print(f"  {len(R)-len(bad)} passed, {len(bad)} failed")
    print("=" * 78)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
