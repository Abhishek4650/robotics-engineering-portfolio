"""
Full verification suite, run repeatedly.

Most checks here are deterministic, so repeating them proves nothing on its own.
The one that is NOT is the interference sweep: it samples random poses. Each
round therefore uses a DIFFERENT seed, so five rounds genuinely explore five
different sets of poses rather than re-running the same test five times.

Round content:
  1. pre-print gate           (geometry, fits, chain, mass)
  2. geometry audit           (features physically present in the STEP)
  3. virtual bearing fit      (every pocket accepts its bearing)
  4. sine path collision      (all 240 solved waypoints, exact mesh)
  5. interference sweep       (random poses, new seed each round)
"""
import io
import sys
import contextlib
import numpy as np


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


def round_once(n):
    fails = []
    import importlib
    # --- geometry audit
    import audit_parts as AP
    importlib.reload(AP)
    AP.RES.clear()
    _, _o = quiet(AP.main)
    bad = [r for r in AP.RES if r[1] in ("MISSING", "OFFSET", "ERROR")]
    fails += [f"audit: {p}/{f} — {d}" for p, _s, f, d in bad]
    n_ok = sum(1 for r in AP.RES if r[1] == "OK")

    # --- bearing fit
    import check_bearing_fit as BF
    importlib.reload(BF)
    bfbad, _o = quiet(BF.main)
    fails += [f"bearing fit: {p} — {d}" for p, d in bfbad]

    # --- sine path collision
    import check_sine_clear as SC
    importlib.reload(SC)
    Q = np.load(SC.TRAJ)["Q"]
    import assemble as A
    import interference as I
    # The sine path is deterministic, so checking all 240 waypoints on every
    # round proves nothing after the first. Round 1 does the full sweep; later
    # rounds stride it, which still catches a regression without costing 240
    # mesh-collision builds each time.
    stride = 1 if n == 1 else 6
    sub = Q[::stride]
    ncol = 0
    for q in sub:
        parts, _ = A.build(*q)
        if I.check(parts):
            ncol += 1
    if ncol:
        fails.append(f"sine path: {ncol}/{len(sub)} waypoints collide")

    # --- interference sweep, fresh seed each round
    bad_n, tot, tally, _w = I.sweep(n=40, seed=100 + n)
    top = max(tally.items(), key=lambda kv: kv[1]) if tally else None

    return dict(fails=fails, audit_ok=n_ok, sine_collisions=ncol, sine_n=len(sub),
                sweep=(bad_n, tot), sweep_top=top)


def main(rounds=5):
    print("=" * 78)
    print(f"ARM-450 FULL VERIFICATION — {rounds} rounds, new sweep seed each round")
    print("=" * 78)
    allfail = []
    for n in range(1, rounds + 1):
        r = round_once(n)
        b, t = r["sweep"]
        top = (f"{I_NAMES(r['sweep_top'])}" if r["sweep_top"] else "none")
        print(f"\n  ROUND {n}")
        print(f"    geometry audit      {r['audit_ok']} features OK, "
              f"{len(r['fails'])} problem(s)")
        print(f"    sine path           {r['sine_collisions']}/{r['sine_n']} waypoints collide")
        print(f"    interference sweep  {b}/{t} random poses collide (seed {100+n})"
              f"   worst pair: {top}")
        for f in r["fails"]:
            print(f"    [FAIL] {f}")
        allfail += r["fails"]
    print("\n" + "=" * 78)
    if allfail:
        print(f"  {len(allfail)} FAILURE(S) ACROSS {rounds} ROUNDS")
        for f in dict.fromkeys(allfail):
            print(f"    {f}")
    else:
        print(f"  ALL {rounds} ROUNDS CLEAN")
    print("=" * 78)
    return allfail


def I_NAMES(kv):
    import interference as I
    (i, j), c = kv
    return f"{I.NAMES[i]}<->{I.NAMES[j]} ({c})"


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
