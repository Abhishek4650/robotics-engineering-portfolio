#!/usr/bin/env python3
"""
PLUG INSERTION (user, 2026-09-24: "give slots to insert the pin in servos --
did you give that clearance?").

verify_wiring.py proves the two bus plugs FIT once plugged in. This checks the
harder question: can a plug be pushed into (and pulled out of) its socket with
the arm ASSEMBLED -- i.e. is there a slot in the housing on the socket's line?

The plug (photo + manufacturer's model: as wide as its socket, 5.0 x 10.0,
+0.3 all round for fingers' slop) with its wire lead is moved straight out of
the socket along the servo's back axis, 0.5 mm steps, 45 mm, exact solids,
against every part except the servo itself. Free = there is an insertion slot.
"""
import os
import sys

import numpy as np
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import verify_official_servo as VO   # noqa: E402
import verify_fasteners as VF        # noqa: E402
import make_audit_views as MV        # noqa: E402
import verify_wiring as VW           # noqa: E402

SLOP, BODY_H, LEAD_L = 0.3, 6.0, 3.0       # plug body above its mated bottom; wire straight for 3 mm, then it bends
                                           # (a 3-wire bus lead bends within ~2x its thickness at the crimp exit)
TRAVEL = 45.0


def plug(T, i):
    y0, y1 = VW.SOCK_Y[i]
    cx, cy = (VW.SOCK_X[0] + VW.SOCK_X[1]) / 2, (y0 + y1) / 2
    zb = VW.SOCK_TOP + VW.PLUG_ABOVE - BODY_H          # mated: the body reaches down into the shroud
    b = (cq.Workplane("XY").center(cx, cy).rect(VW.SOCK_X[1] - VW.SOCK_X[0] + 2 * SLOP, y1 - y0 + 2 * SLOP)
         .extrude(BODY_H).translate((0, 0, zb))
         .union(cq.Workplane("XY").center(cx, cy).rect(VW.WIRE_T, VW.WIRE_W).extrude(LEAD_L)
                .translate((0, 0, zb + BODY_H))))
    return VO.place(b.val().wrapped, T)


def moved(sh, v):
    return VO.place(sh, np.array([[1, 0, 0, v[0]], [0, 1, 0, v[1]], [0, 0, 1, v[2]], [0, 0, 0, 1.0]]))


def hits(sh, S, k):
    bw = VF.bbox(sh)
    for nm2, (sh2, _) in S.items():
        if nm2 == "servo_J%d" % k or nm2.startswith("spring") or not VF.overlap(bw, VF.bbox(sh2), 0.0):
            continue
        v = VF.common(sh, sh2)
        if v > 1e-2:
            return nm2
    return None


def lateral(S, k, Ts, i, lift):
    """from `lift` mm straight out, can the plug (body only) leave sideways?"""
    y0, y1 = VW.SOCK_Y[i]
    cx, cy = (VW.SOCK_X[0] + VW.SOCK_X[1]) / 2, (y0 + y1) / 2
    zb = VW.SOCK_TOP + VW.PLUG_ABOVE - BODY_H + lift
    R = Ts[:3, :3]
    for rot in (0, 90):
        wx, wy = VW.SOCK_X[1] - VW.SOCK_X[0] + 2 * SLOP, y1 - y0 + 2 * SLOP
        if rot:
            wx, wy = wy, wx
        body = VO.place(cq.Workplane("XY").center(cx, cy).rect(wx, wy).extrude(BODY_H).translate((0, 0, zb)).val().wrapped, Ts)
        if hits(body, S, k):
            continue
        D = (("+x", (1, 0, 0)), ("-x", (-1, 0, 0)), ("+y", (0, 1, 0)), ("-y", (0, -1, 0)))
        for lab, d in D:
            dw = R @ np.array(d, float)
            if all(hits(moved(body, dw * t), S, k) is None for t in np.arange(1.0, 45.01, 1.0)):
                return "%s, turned %d deg" % (lab, rot)
        # two moves: a short sideways shift (fingers / pliers), then out
        for lab1, d1 in D:
            for t1 in (2.0, 4.0, 6.0, 8.0):
                v1 = R @ np.array(d1, float) * t1
                if any(hits(moved(body, R @ np.array(d1, float) * t), S, k) for t in np.arange(1.0, t1 + 1e-9, 1.0)):
                    break
                for lab2, d2 in D:
                    if abs(np.dot(d1, d2)) > 0.5:
                        continue
                    dw = R @ np.array(d2, float)
                    if all(hits(moved(body, v1 + dw * t), S, k) is None for t in np.arange(1.0, 45.01, 1.0)):
                        return "%s %.0f mm, then %s, turned %d deg" % (lab1, t1, lab2, rot)
    return None


def main():
    A, _ = VO.BA.build()
    S = {c.name: (VF.world(c), c) for c in A.children if VF.world(c) is not None}
    blocked = 0
    print("PLUG INSERTION -- each bus plug pulled straight out of its socket, arm assembled")
    for k in range(1, 7):
        Ts = MV.seat_T(S, k)
        out = Ts[:3, 2]                                  # servo +z: out of the back
        for i, nm in enumerate("AB"):
            p0 = plug(Ts, i)
            worst, at = 0.0, None
            for s in np.arange(0.0, TRAVEL + 1e-9, 0.5):
                if at is not None:
                    break
                w = VO.place(p0, np.array([[1, 0, 0, out[0] * s], [0, 1, 0, out[1] * s], [0, 0, 1, out[2] * s], [0, 0, 0, 1.0]]))
                bw = VF.bbox(w)
                for nm2, (sh, _) in S.items():
                    if nm2 == "servo_J%d" % k or nm2.startswith("spring") or not VF.overlap(bw, VF.bbox(sh), 0.0):
                        continue
                    v = VF.common(w, sh)
                    if v > 1e-2 and at is None:
                        at = (s, nm2)                    # FIRST contact on the way out (not the largest)
                    worst = max(worst, v)
            if at is not None:
                worst = max(worst, 1e-2)
            ok = at is None
            route = None
            if not ok and at[0] >= 10.0:
                # straight out far enough to be clear of its socket: then sideways to the outside?
                for lift in np.arange(9.5, 20.01, 1.0):     # 9.1 mm lifts the plug body clear of the servo's socket slot
                    if lift < at[0] - 0.5:
                        route = lateral(S, k, Ts, i, lift)
                        if route:
                            route = "%.0f mm straight out, then %s" % (lift, route)
                            break
            ok = ok or route is not None
            blocked += 0 if ok else 1
            print("   J%d plug %s: %s" % (k, nm, "SLOT -- goes straight in and out" if at is None else
                                         ("ACCESS -- %s" % route) if route else
                                         "BLOCKED: touches %s after %.1f mm straight, no way out sideways"
                                         % (at[1], at[0])))
    print("\nPLUG INSERTION: %d plug(s) that cannot be plugged in with the arm assembled" % blocked)
    return blocked


if __name__ == "__main__":
    main()
