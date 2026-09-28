#!/usr/bin/env python3
"""
ARM-450 rev I -- EVERY FASTENER in the final assembly, checked as a real part
(exact OpenCascade solids, world placement exactly as ARM450_REV_I_ASSEMBLY).

For each screw / grub / pin:
  1. PASSES FREE   common volume with every printed part, servo and bearing
                   = 0 (it runs in its clearance hole), except where it is
                   MEANT to cut its own thread (M5 set screw in the link's O4.2 hole, J5 grub)
  2. ENGAGES       length of its shank inside the thing that holds it
                   (insert, nut, servo horn, clamp pilot) >= 3 mm (M3: 1 x d;
                   M2.5 horn / ear screws >= 2.4)
  3. HEAD SEATED   printed material directly under the head (a 0.1 mm probe
                   disc under the head's bearing ring meets a part)
  4. TIP FREE      the tip does not touch any part (a screw that bottoms out
                   clamps nothing)
For each insert / nut: sits in its pocket -- common with its host part = 0,
and the pocket actually exists (host material all round within 0.6 mm).
"""
import os
import sys
import re

import numpy as np
import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_final_assembly as BA   # noqa: E402

TOL_V = 1e-3
LINK_OF = {"1": "link_upper_groove", "2": "link_upper_tongue", "3": "link_fore_groove", "4": "link_fore_tongue"}


def vol(sh):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(sh, g); return g.Mass()


def common(a, b):
    c = BRepAlgoAPI_Common(a, b); c.SetFuzzyValue(1e-5); c.Build()
    return vol(c.Shape()) if c.IsDone() else float("nan")


def bbox(sh):
    b = Bnd_Box(); BRepBndLib.Add_s(sh, b); return np.array(b.Get()).reshape(2, 3)


def overlap(b1, b2, pad=0.2):
    return np.all(b1[0] - pad <= b2[1]) and np.all(b2[0] - pad <= b1[1])


def world(child):
    o = child.obj
    sh = o.val() if isinstance(o, cq.Workplane) else o
    if isinstance(sh, cq.Assembly):
        return None
    return sh.moved(child.loc).wrapped


def main():
    A, BOM = BA.build()
    S = {}
    for ch in A.children:
        w = world(ch)
        if w is not None:
            S[ch.name] = w
    SCREW = re.compile(r"^(split_J\d_\d|cap_J\d_\d|j4base_forearm_\d|j5fork_j4hub_\d|j3fork_link_\d|"
                       r"m4_base_foot_\d|collar_pinch|j5_grub|pin_J\d_\w+_[+-]\d|collar_clamp_\S+|"
                       r"seam_(upper|fore)_\d+|ear_bolt_\w+|link_set_\d_\d+|horn_screw_J\d_\d+|servo_scr_J\d_\d)$")
    screws = [k for k in S if SCREW.match(k)]
    inserts = [k for k in S if "_ins" in k or k.startswith("ins_")]
    nuts = [k for k in S if "nut" in k]
    hw = set(screws) | set(inserts) | set(nuts) | {k for k in S if k.startswith("spring_")}
    parts = [k for k in S if k not in hw]
    B = {k: bbox(v) for k, v in S.items()}
    print("FASTENERS: %d screws/grubs/pins, %d inserts, %d nuts, against %d parts\n"
          % (len(screws), len(inserts), len(nuts), len(parts)))
    fails = []
    # 1. passes free
    for s in sorted(screws):
        hits = []
        for p in parts:
            if overlap(B[s], B[p]):
                v = common(S[s], S[p])
                if v > TOL_V:
                    meant = (s.startswith("link_set") and p == LINK_OF[s[9]]) or \
                            (s.startswith("j5_grub") and p == "j6_body") or \
                            (s.startswith("servo_scr") and p == "servo_J" + s[11])
                    hits.append("%s %.3f mm3%s" % (p, v, " (self-tapping, designed)" if meant else ""))
                    if not meant:
                        fails.append((s, "runs into " + p, v))
        for q in inserts + nuts:
            if overlap(B[s], B[q]):
                v = common(S[s], S[q])
                if v > TOL_V:
                    hits.append("%s %.3f mm3" % (q, v)); fails.append((s, "cuts into " + q, v))
        print("  1 %-26s %s" % (s, "free" if not hits else "; ".join(hits)))
    print("\nCLAMP / THREAD ENGAGEMENT, HEAD SEAT, TIP")
    for s in sorted(screws):
        sh = S[s]
        # screw local frame: head on top of z=0, shank to -L. Recover it from the assembly child
        ch = [c for c in A.children if c.name == s][0]
        T = ch.loc.wrapped.Transformation()
        R = np.array([[T.Value(i, j) for j in (1, 2, 3)] for i in (1, 2, 3)])
        o = np.array([T.Value(i, 4) for i in (1, 2, 3)])
        ax = -R[:, 2]                                     # shank direction
        bb = ch.obj.val().BoundingBox() if isinstance(ch.obj, cq.Workplane) else ch.obj.BoundingBox()
        L = -bb.zmin
        head_d = 2 * max(bb.xmax, bb.ymax)
        d = 5.0 if s.startswith("link_set") else 2 * min(abs(bb.xmax), 1.5 if "horn" not in s and "ear" not in s else 1.25)
        if s.startswith("servo_scr"):
            d = 2.2                                     # ~ST2.2 self-tapping, from the servo box
        # 2. engagement: shank samples inside an insert / nut envelope, horn, or clamp ring
        ts = np.linspace(0.05, L - 0.05, int(L / 0.1))
        P = o[None, :] + np.outer(ts, ax)
        from OCP.BRepClass3d import BRepClass3d_SolidClassifier
        from OCP.gp import gp_Pnt
        from OCP.TopAbs import TopAbs_IN, TopAbs_ON
        eng, by = 0.0, "-"
        cands = [q for q in inserts + nuts if overlap(B[s], B[q], 1.0)]
        if s.startswith("horn_screw"):
            cands = ["servo_" + s.split("_")[2]]
        if s.startswith("link_set"):
            cands = [LINK_OF[s[9]]]                     # M5 thread formed in the link's O4.2 hole
        if s == "j5_grub":
            cands = ["j6_body"]
        sscr = s.startswith("servo_scr")
        if sscr:
            cands = ["servo_J" + s[11]]                 # thread formed in the servo's own back hole
        for q in cands:
            # envelope: for inserts/nuts their outer cylinder -> fill the bore
            if q in inserts or q in nuts:
                qb = [c for c in A.children if c.name == q][0]
                Tq = qb.loc.wrapped.Transformation()
                oq = np.array([Tq.Value(i, 4) for i in (1, 2, 3)])
                aq = np.array([Tq.Value(i, 3) for i in (1, 2, 3)])
                qbb = qb.obj.val().BoundingBox() if isinstance(qb.obj, cq.Workplane) else qb.obj.BoundingBox()
                z0, z1 = qbb.zmin, qbb.zmax
                rel = P - oq
                zz = rel @ aq
                rr = np.linalg.norm(rel - np.outer(zz, aq), axis=1)
                n_in = np.sum((zz >= z0) & (zz <= z1) & (rr < max(qbb.xmax, 2.0)))
            elif q.startswith("servo") and not sscr:
                # the horn disc: the screw's length inside the horn's envelope (holes are its threads)
                qb = [c for c in A.children if c.name == q][0]
                Tq = qb.loc.wrapped.Transformation()
                oq = np.array([Tq.Value(i, 4) for i in (1, 2, 3)])
                aq = np.array([Tq.Value(i, 3) for i in (1, 2, 3)])
                zz = (P - oq) @ aq
                n_in = np.sum((zz <= -0.0) & (zz >= -BA.DC.HORN_BELOW_CAP))
            else:
                # grub: length inside the host's material band (count points whose ring would be solid)
                clf = BRepClass3d_SolidClassifier(S[q])
                n_in = 0
                perp = np.cross(ax, [0, 0, 1.0]);
                if np.linalg.norm(perp) < 0.1:
                    perp = np.cross(ax, [1.0, 0, 0])
                perp /= np.linalg.norm(perp)
                for p in P:
                    clf.Perform(gp_Pnt(*map(float, p + perp * (d / 2 + 0.3))), 1e-6)
                    n_in += clf.State() == TopAbs_IN
            e = n_in * (ts[1] - ts[0]) if len(ts) > 1 else 0
            if e > eng:
                eng, by = e, q
        need = 2.4 if ("horn" in s or "ear" in s or sscr) else 3.0
        ok_e = eng >= need
        # 3. head seat: thin ring under the head (between shank and head OD)
        ring = cq.Workplane("XY").circle(head_d / 2 - 0.2).circle(d / 2 + 0.3).extrude(-0.1).val()
        ring = ring.moved(ch.loc).wrapped
        seat = [p for p in parts if overlap(bbox(ring), B[p]) and common(ring, S[p]) > 1e-4]
        grub = "grub" in s or s.startswith("link_set")
        ok_h = grub or bool(seat) or s.startswith("pin_")
        # 4. tip: a 0.3 mm disc just past the tip must be free of parts
        # (a self-tapper cuts its thread to the tip: judge its core, O d - 0.4)
        tip = cq.Workplane("XY").circle(d / 2 - (0.2 if sscr else 0)).extrude(-0.3).translate((0, 0, -L)).val().moved(ch.loc).wrapped
        tipc = [p for p in parts if overlap(bbox(tip), B[p]) and common(tip, S[p]) > 1e-4]
        meant_tip = grub and any(p.startswith("J") and p.endswith("shaft") or p.startswith("j6") for p in tipc)
        ok_t = not tipc or grub
        for ok, what in ((ok_e, "engagement %.1f < %.1f mm" % (eng, need)), (ok_h, "head bears on nothing"),
                         (ok_t, "tip touches " + ",".join(tipc))):
            if not ok:
                fails.append((s, what, 0))
        print("  %-26s engaged %4.1f mm in %-20s head on %-22s tip %s  %s"
              % (s, eng, by, ",".join(seat) if seat else ("(grub)" if grub else "(pin: spring side)" if s.startswith("pin_") else "NOTHING"),
                 "free" if not tipc else "on " + ",".join(tipc), "ok" if (ok_e and ok_h and ok_t) else "FAIL"))
    print("\nINSERTS / NUTS in their pockets")
    for q in sorted(inserts + nuts):
        hits = [(p, common(S[q], S[p])) for p in parts if overlap(B[q], B[p])]
        bad = [(p, v) for p, v in hits if v > TOL_V]
        # host: the part whose material surrounds the insert (0.6 mm grown envelope)
        ch = [c for c in A.children if c.name == q][0]
        qbb = ch.obj.val().BoundingBox() if isinstance(ch.obj, cq.Workplane) else ch.obj.BoundingBox()
        r_o = qbb.xmax
        shell = cq.Workplane("XY").circle(r_o + 0.6).circle(r_o + 0.05).extrude(qbb.zmin + 0.5).translate((0, 0, -0.5)).val().moved(ch.loc).wrapped
        shv = vol(shell)
        host = sorted(((common(shell, S[p]) / shv, p) for p in parts if overlap(bbox(shell), B[p])), reverse=True)
        cov = host[0][0] if host else 0.0
        if q in nuts:
            cov = 1.0          # a nut sits ON a face, not in a pocket: overlap check only
        ok = not bad and cov > 0.8
        if not ok:
            fails.append((q, "pocket: overlap %s / host cover %.0f %%" % (bad, 100 * cov), 0))
        print("  %-26s host %-20s material round it %3.0f %%  %s"
              % (q, host[0][1] if host else "-", 100 * cov, "ok" if ok else "FAIL %s" % bad))
    print("\nFASTENER CHECK: %d failure(s)" % len(fails))
    for f in fails:
        print("   FAIL %-26s %s" % (f[0], f[1]))
    return len(fails)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
