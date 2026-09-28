#!/usr/bin/env python3
"""
WIRING (Rule 3): can both bus plugs go into every servo, and can their wires
get out?

Where the sockets are: the manufacturer's STEP (PCB-CHAZUO: the two 3-pin
5264 sockets, one block x 11.70..16.70 from the output axis, y -9.80..10.20,
top 26.90 above the seat face, sunk in a slot of the back face), confirmed by
the user's photo of the back of their servo (2026-09-24: both sockets in the
band just past the rear boss, plug entering square to the back face, wires
leaving straight out of it).

Plug model FROM THE PHOTO (zoomed): the plug sits inside the socket shroud,
as wide as the socket, its top about level with the shroud top; the three
wires leave it side by side along the socket, straight out of the back face.
  plug housing  socket footprint, socket top .. +2.0 mm
  wire bundle   7.5 (along the socket) x 2.0, straight on for 8.0 mm
Both sockets are plugged (daisy chain in / out). An UPPER-BOUND envelope is
reported too (footprint + 0.25, 8.0 mm housing + 5.0 mm lead) to show the
margin if the real plug stands taller than the photo suggests.

Checked, exact solids, servo seated in the final assembly:
  1. plug + lead volume vs every other part (printed parts, screws, springs)
     -- must be 0: a plug that hits a wall cannot be inserted
  2. clearance round the plugs (nearest part)
  3. way out: from the end of each lead, free run in the five directions of the
     servo frame -- or straight out a little further, then sideways; the wires
     need a route with >= 25 mm free run
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

SOCK_X = (11.70, 16.70)
SOCK_Y = ((-9.80, 0.20), (0.20, 10.20))
SOCK_TOP = 26.90
PLUG_ABOVE, WIRE_W, WIRE_T, WIRE_L = 2.0, 7.5, 2.0, 8.0          # photo model
PAD, PLUG_H, LEAD_L = 0.25, 8.0, 5.0                              # upper bound
RUN_MIN = 25.0


def envelope(T, upper=False):
    out = []
    cx = (SOCK_X[0] + SOCK_X[1]) / 2
    for i, (y0, y1) in enumerate(SOCK_Y):
        cy = (y0 + y1) / 2
        if upper:
            b = (cq.Workplane("XY").center(cx, cy).rect(SOCK_X[1] - SOCK_X[0] + 2 * PAD, y1 - y0 + 2 * PAD)
                 .extrude(PLUG_H + LEAD_L).translate((0, 0, SOCK_TOP)))
        else:
            b = (cq.Workplane("XY").center(cx, cy).rect(SOCK_X[1] - SOCK_X[0], y1 - y0).extrude(PLUG_ABOVE)
                 .translate((0, 0, SOCK_TOP))
                 .union(cq.Workplane("XY").center(cx, cy).rect(WIRE_T, WIRE_W).extrude(WIRE_L)
                        .translate((0, 0, SOCK_TOP + PLUG_ABOVE))))
        out.append(("plug_%s" % "AB"[i], VO.place(b.val().wrapped, T)))
    return out


def lead_top():
    return SOCK_TOP + PLUG_ABOVE + WIRE_L


def dist(a, b):
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    d = BRepExtrema_DistShapeShape(a, b); d.Perform()
    return d.Value() if d.IsDone() else float("nan")


def free_run(pt, direc, shapes, L=60.0, step=0.5):
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_IN
    clfs = [BRepClass3d_SolidClassifier(s) for s in shapes]
    for t in np.arange(step, L + 1e-9, step):
        p = pt + t * direc
        for c in clfs:
            c.Perform(gp_Pnt(*map(float, p)), 1e-6)
            if c.State() == TopAbs_IN:
                return t
    return L


def main():
    A, _ = VO.BA.build()
    S = {c.name: (VF.world(c), c) for c in A.children if VF.world(c) is not None}
    problems = 0
    print("WIRING -- both bus plugs in every servo (manufacturer's socket position, user's photo)")
    print("  plug (photo): socket footprint, %.1f mm above the socket top; wires %.1f x %.1f straight for %.1f mm"
          % (PLUG_ABOVE, WIRE_W, WIRE_T, WIRE_L))
    for k in range(1, 7):
        Ts = MV.seat_T(S, k)
        env = envelope(Ts)
        print("\nJ%d" % k)
        near = []
        for nm_e, e in envelope(Ts, upper=True):         # upper bound: report only
            be = VF.bbox(e)
            hit = [(nm, VF.common(e, w)) for nm, (w, _) in S.items()
                   if nm != "servo_J%d" % k and VF.overlap(be, VF.bbox(w), 1.0)]
            hit = [h for h in hit if h[1] > 1e-3]
            print("   upper-bound %s: %s" % (nm_e, ", ".join("touches %s %.1f mm3" % h for h in hit) if hit else "clear"))
        for nm_e, e in env:
            be = VF.bbox(e)
            hits, dmin, who = [], 99.0, None
            for nm, (w, _) in S.items():
                if nm == "servo_J%d" % k or not VF.overlap(be, VF.bbox(w), 20.0):
                    continue
                near.append(w)
                v = VF.common(e, w)
                if v > 1e-3:
                    hits.append((nm, v))
                else:
                    d = dist(e, w)
                    if d < dmin:
                        dmin, who = d, nm
            if hits:
                problems += 1
                print("   %s  BLOCKED: %s" % (nm_e, ", ".join("%s %.1f mm3" % h for h in hits)))
            else:
                print("   %s  fits, nearest part %.2f mm (%s)" % (nm_e, dmin, who))
        # way out, from the end of each lead, servo-frame directions
        R = Ts[:3, :3]
        best = []
        for (y0, y1) in SOCK_Y:
            tip = Ts @ np.array([(SOCK_X[0] + SOCK_X[1]) / 2, (y0 + y1) / 2, lead_top(), 1.0])
            runs = {}
            for lab, d in (("+x (along case)", (1, 0, 0)), ("-x", (-1, 0, 0)), ("+y", (0, 1, 0)), ("-y", (0, -1, 0)),
                           ("+z (straight out)", (0, 0, 1))):
                runs[lab] = free_run(tip[:3], R @ np.array(d, float), near)
            lab, r = max(runs.items(), key=lambda kv: kv[1])
            route = "%s %.1f" % (lab, r)
            if r < RUN_MIN:
                # the wires may run straight out a little further, THEN bend
                out = R @ np.array([0, 0, 1.0])
                for s_ in np.arange(2.0, min(runs["+z (straight out)"], 20.0) - 0.5 + 1e-9, 2.0):
                    p_ = tip[:3] + s_ * out
                    for lab2, d in (("+x", (1, 0, 0)), ("-x", (-1, 0, 0)), ("+y", (0, 1, 0)), ("-y", (0, -1, 0))):
                        r2 = free_run(p_, R @ np.array(d, float), near)
                        if r2 > r:
                            r, route = r2, "straight out %.0f mm, then %s %.1f" % (s_, lab2, r2)
                    if r >= RUN_MIN:
                        break
            best.append(r)
            print("   lead end: free run %s   -> way out: %s" % ("  ".join("%s %.1f" % kv for kv in runs.items()), route))
        if min(best) < RUN_MIN:
            problems += 1
            print("   NO WAY OUT: longest free run %.1f mm < %.0f" % (min(best), RUN_MIN))
    # CONTROL: the same envelope moved 22 mm along the case (x 33.7..38.7,
    # into the end of the J3 bay) must be reported blocked
    Tc = MV.seat_T(S, 3) @ np.array([[1, 0, 0, 22.0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])
    hit = any(VF.common(e, S[p][0]) > 1e-3 for _, e in envelope(Tc) for p in ("J3_p1", "J3_p2"))
    print("\nCONTROL  plugs moved 22 mm into the J3 bay end -> %s" % ("DETECTED" if hit else "NOT DETECTED"))
    problems += 0 if hit else 1
    print("\nWIRING CHECK: %d problem(s)" % problems)


if __name__ == "__main__":
    main()
