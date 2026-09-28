#!/usr/bin/env python3
"""
RULE 4 -- parts FIT, they do not OVERLAP; they interact only through proper
pathways. Exact OpenCascade solids of the final assembly (212 components).

For every pair of components closer than TOUCH:
  1. OVERLAP  common volume > VOL is a failure, except the two designed
              interferences, each confined to where it belongs:
                * ST3215 in its -0.22 pinch channel (0.11 per side, on the
                  channel walls only)
                * an M3 grub cutting its own thread in a printed pilot
                  (inside the grub's thread annulus only)
  2. CONTACT  classified from the faces that actually touch:
                planar mate   coplanar, normals opposite, real contact area
                cyl. fit      coaxial cylinders, equal radius (+ clearance)
                flush         coplanar, SAME side (side by side, no load)
              anything else (edge / point / tangent graze) is a failure.
  3. PATHWAY  every part belongs to one rigid body (ground, turret, upper
              link, forearm, J4 hub, blade, flange). Contact ACROSS a joint
              is allowed only
                * through that joint's bearing -- housing side on the OUTER
                  race band only, shaft side on the INNER race band only
                * servo horn face -> its coupler, and its horn screws
              anything else is a part rubbing across a joint = failure.
  4. CLAMPED  every bolted joint really clamps: the part under the head and
              the part holding the insert / nut share a planar mate.
Controls: a part pushed 0.3 mm into its neighbour, a part lifted 0.2 mm off
its seat, and the upper link moved onto the J2 cheek must each be caught.
"""
import os
import re
import sys
import time

import numpy as np
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED, TopAbs_VERTEX
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane, GeomAbs_Cylinder
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRep import BRep_Tool
from OCP.gp import gp_Trsf, gp_Vec
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import verify_fasteners as VF       # noqa: E402
import build_final_assembly as BA   # noqa: E402

TOUCH = 0.03     # mm: closer = touching
VOL = 1e-3       # mm3: more shared volume = overlap
MIN_MATE = 0.05  # mm2: less contact area than this is an edge, not a mate

BODY = [
    (0, r"^(j1_mount|base|foot_ins_\d|m4_base_foot_\d|servo_J1|servo_scr_J1_\d)$"),
    (1, r"^(J2_turret_p[12]|spigot_collar|collar_pinch|collar_ins|j1_hub|horn_screw_J1_\d+|split_J2_\d|"
        r"split_ins_J2_\d|pin_J2_turret_[+-]1(_ins)?|servo_J2|servo_scr_J2_\d)$"),
    (2, r"^(J2_shaft|horn_screw_J2_\d+|shaft_clamp_[12]|link_set_[12]_\d+|link_upper_(groove|tongue)|"
        r"seam_(ins_)?upper_\d|ear_(bolt|ins)_upper|link_end_ins_\d|collar_upper_[+-]y|collar_clamp_158_[+-]1|"
        r"collar_nut_158_[+-]1|pin_J2_collar_[+-]1(_ins)?|J3_p[12]|split_J3_\d|split_ins_J3_\d|j3fork_link_\d|"
        r"pin_J3_fork_[+-]1(_ins)?|servo_J3|servo_scr_J3_\d)$"),
    (3, r"^(J3_shaft|horn_screw_J3_\d+|shaft_clamp_[34]|link_set_[34]_\d+|link_fore_(groove|tongue)|"
        r"seam_(ins_)?fore_\d|ear_(bolt|ins)_fore|forearm_ins_\d|collar_fore_[+-]y|collar_clamp_299_[+-]1|"
        r"collar_nut_299_[+-]1|pin_J3_collar_[+-]1(_ins)?|j4_base|j4base_forearm_\d|j4_cap|cap_J4_\d|"
        r"cap_ins_J4_\d|servo_J4|servo_scr_J4_\d)$"),
    (4, r"^(j4_hub|j4hub_ins_\d|horn_screw_J4_\d+|J5_p[12]|split_J5_\d|split_ins_J5_\d|j5fork_j4hub_\d|servo_J5|servo_scr_J5_\d)$"),
    (5, r"^(J5_shaft|horn_screw_J5_\d+|J5_spacer_[AB]|j6_body|j5_grub|j6_cap|cap_J6_\d|cap_ins_J6_\d|servo_J6|servo_scr_J6_\d)$"),
    (6, r"^(j6_flange|horn_screw_J6_\d+|tool_ins_\d+)$"),
]
LINK_OF = {"1": "link_upper_groove", "2": "link_upper_tongue", "3": "link_fore_groove", "4": "link_fore_tongue"}
BEARING_JOINT = {"brg_J1": (0, 1), "brg_J2": (1, 2), "brg_J3": (2, 3), "brg_J4": (3, 4), "brg_J5": (4, 5), "brg_J6": (5, 6)}
SPRING_JOINT = {"spring_J2": (1, 2), "spring_J3": (2, 3)}
# SKF catalogue: 61806 d1 33.7 / D1 38.35, 61706 d1 32.4 / D1 34.6 (inner-ring
# and outer-ring shoulder diameters). A part turning WITH the inner ring may
# touch the bearing only inside d1; a part on the OUTER ring's side must stay
# clear of the inner ring (outside d1 + 0.5 running margin).
RACES = {42.0: (33.7 / 2, 38.35 / 2), 37.0: (32.4 / 2, 34.6 / 2)}


def body_of(k):
    for b, rx in BODY:
        if re.match(rx, k):
            return b
    return None


def faces(sh):
    out = []
    e = TopExp_Explorer(sh, TopAbs_FACE)
    while e.More():
        f = TopoDS.Face_s(e.Current())
        out.append((f, VF.bbox(f)))
        e.Next()
    return out


def dist(a, b):
    d = BRepExtrema_DistShapeShape(a, b)
    return d.Value() if d.IsDone() else 1e9


def area(sh):
    g = GProp_GProps(); BRepGProp.SurfaceProperties_s(sh, g); return g.Mass()


def verts(sh):
    out = []
    e = TopExp_Explorer(sh, TopAbs_VERTEX)
    while e.More():
        p = BRep_Tool.Pnt_s(TopoDS.Vertex_s(e.Current())); out.append((p.X(), p.Y(), p.Z()))
        e.Next()
    return np.array(out) if out else np.zeros((0, 3))


def surf(f):
    s = BRepAdaptor_Surface(f)
    t = s.GetType()
    if t == GeomAbs_Plane:
        pl = s.Plane(); n = pl.Axis().Direction(); o = pl.Location()
        n = np.array([n.X(), n.Y(), n.Z()])
        if f.Orientation() == TopAbs_REVERSED:
            n = -n
        return ("plane", n, np.array([o.X(), o.Y(), o.Z()]))
    if t == GeomAbs_Cylinder:
        c = s.Cylinder(); a = c.Axis(); d = a.Direction(); o = a.Location()
        return ("cyl", np.array([d.X(), d.Y(), d.Z()]), np.array([o.X(), o.Y(), o.Z()]), c.Radius())
    return ("other",)


def classify(fa, fb):
    """Contact type of two touching faces + the shared region (or None)."""
    sa, sb = surf(fa), surf(fb)
    if sa[0] == "plane" and sb[0] == "plane":
        par = sa[1] @ sb[1]
        off = abs((sb[2] - sa[2]) @ sa[1])
        if abs(abs(par) - 1) < 1e-4 and off < TOUCH:
            c = BRepAlgoAPI_Common(fa, fb); c.Build()
            ar = area(c.Shape()) if c.IsDone() else 0.0
            if par < 0:
                return ("planar mate" if ar > MIN_MATE else "edge (coplanar, opposite)"), ar, c.Shape()
            return "flush", ar, None
        return "edge/point", 0.0, None
    if sa[0] == "cyl" and sb[0] == "cyl":
        par = abs(sa[1] @ sb[1])
        v = sb[2] - sa[2]
        lat = np.linalg.norm(v - (v @ sa[1]) * sa[1])
        if par > 1 - 1e-6 and lat < TOUCH and abs(sa[3] - sb[3]) < 0.15:
            # both faces' extent along the common axis: a real fit overlaps
            # axially; two stacked holes only meet at a plane (a rim)
            za = verts(fa) @ sa[1]; zb = verts(fb) @ sa[1]
            if len(za) and len(zb) and min(za.max(), zb.max()) - max(za.min(), zb.min()) > 0.1:
                return "cyl. fit", abs(sa[3] - sb[3]), None
        return "edge/point", 0.0, None
    return "edge/point", 0.0, None


def _pt_near(p, faces_):
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
    from OCP.gp import gp_Pnt
    v = BRepBuilderAPI_MakeVertex(gp_Pnt(*p)).Vertex()
    return any(dist(v, f) < TOUCH for f in faces_)


def sol_points(d, i):
    """Both points of extrema solution i, recomputed from their supports
    (PointOnShape returns (0,0,0) for edge supports in this OCP build)."""
    from OCP.BRepExtrema import BRepExtrema_SupportType as ST
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    out = []
    for k, (typ, sup, par_e, par_f) in enumerate(((d.SupportTypeShape1(i), d.SupportOnShape1(i), d.ParOnEdgeS1, d.ParOnFaceS1),
                                                   (d.SupportTypeShape2(i), d.SupportOnShape2(i), d.ParOnEdgeS2, d.ParOnFaceS2))):
        if typ == ST.BRepExtrema_IsVertex:
            p = BRep_Tool.Pnt_s(TopoDS.Vertex_s(sup))
        elif typ == ST.BRepExtrema_IsOnEdge:
            t = par_e(i)
            p = BRepAdaptor_Curve(TopoDS.Edge_s(sup)).Value(t if not isinstance(t, tuple) else t[0])
        else:
            uv = par_f(i)
            u, v = (uv if isinstance(uv, tuple) else (uv, 0.0))
            p = BRepAdaptor_Surface(TopoDS.Face_s(sup)).Value(u, v)
        out.append((p.X(), p.Y(), p.Z()))
    return out


def contacts(A, B, fa_list, fb_list, bbA, bbB):
    """Touching face pairs, classified. An edge/point contact that sits on the
    RIM of a proper mate or fit between the same two parts (both its points
    lie on faces taking part in that mate) is the mate's boundary, not a
    graze, and is dropped. Anything else stays and fails."""
    raw = []
    fa_near = [(f, b) for f, b in fa_list if VF.overlap(b, bbB, TOUCH + 0.05)]
    fb_near = [(f, b) for f, b in fb_list if VF.overlap(b, bbA, TOUCH + 0.05)]
    for f1, b1 in fa_near:
        for f2, b2 in fb_near:
            if VF.overlap(b1, b2, TOUCH + 0.02) and dist(f1, f2) < TOUCH:
                kind, val, reg = classify(f1, f2)
                raw.append((kind, val, reg, f1, f2))
    good = [c for c in raw if not c[0].startswith("edge")]
    fa_ok = [c[3] for c in good]; fb_ok = [c[4] for c in good]
    planes = [(surf(c[3])[1], surf(c[3])[2]) for c in good if c[0] == "planar mate"]

    def on_mate_plane(p):
        return any(abs((np.asarray(p) - o) @ n) < TOUCH for n, o in planes)
    out = list(good)
    for c in raw:
        if not c[0].startswith("edge"):
            continue
        d = BRepExtrema_DistShapeShape(c[3], c[4]); d.Perform()
        rim = d.IsDone() and d.NbSolution() > 0 and fa_ok and fb_ok
        if rim:
            for i in range(1, d.NbSolution() + 1):
                p1, p2 = sol_points(d, i)
                if not ((_pt_near(p1, fa_ok) or on_mate_plane(p1)) and (_pt_near(p2, fb_ok) or on_mate_plane(p2))):
                    rim = False; break
        if not rim:
            out.append(c)
    return out


def loc_frame(ch):
    T = ch.loc.wrapped.Transformation()
    R = np.array([[T.Value(i, j) for j in (1, 2, 3)] for i in (1, 2, 3)])
    o = np.array([T.Value(i, 4) for i in (1, 2, 3)])
    return R, o


def designed_overlap(a, b, common_shape, C):
    """The two designed interferences, each confined to where it belongs."""
    P = verts(common_shape)
    if not len(P):
        return None
    for s, h in ((a, b), (b, a)):
        m = re.match(r"^servo_J(\d)$", s)
        if m and body_of(h) == body_of(s):
            R, o = loc_frame(C[s])
            y = np.abs((P - o) @ R[:, 1])
            if y.min() > 12.20 and y.max() < 12.40:
                return "ST3215 pinch (-0.22 channel), |y| %.2f..%.2f" % (y.min(), y.max())
        ms = re.match(r"^servo_scr_J(\d)_\d$", s)
        if ms and h == "servo_J" + ms.group(1):
            R, o = loc_frame(C[s])
            rel = P - o
            r = np.linalg.norm(rel - np.outer(rel @ R[:, 2], R[:, 2]), axis=1)
            if r.min() > 0.95 and r.max() < 1.15:
                return "self-tapping screw forms its thread in the servo's O2.0 back hole, r %.2f..%.2f" % (r.min(), r.max())
        m5 = re.match(r"^link_set_(\d)_\d+$", s)
        if (m5 and h == LINK_OF[m5.group(1)]) or (s == "j5_grub" and h == "j6_body"):
            R, o = loc_frame(C[s])
            rel = P - o
            r = np.linalg.norm(rel - np.outer(rel @ R[:, 2], R[:, 2]), axis=1)
            lo, hi = (2.05, 2.55) if m5 else (1.25, 1.55)
            if r.min() > lo and r.max() < hi:
                return "set screw forms its thread in the %s pilot, r %.2f..%.2f" % ("O4.2" if m5 else "O2.6", r.min(), r.max())
    return None


def analyse(S, C, B, F, names, pairs=None, verbose=True):
    """Returns (fails, records). records[(a,b)] = list of contact kinds."""
    fails, rec = [], {}
    keys = sorted(names)
    todo = pairs if pairs is not None else [(a, b) for i, a in enumerate(keys) for b in keys[i + 1:]
                                            if VF.overlap(B[a], B[b], TOUCH)]
    for a, b in todo:
        if dist(S[a], S[b]) > TOUCH:
            continue
        v = VF.common(S[a], S[b])
        kinds = []
        if v > VOL:
            c = BRepAlgoAPI_Common(S[a], S[b]); c.SetFuzzyValue(1e-5); c.Build()
            why = designed_overlap(a, b, c.Shape(), C)
            if why:
                kinds.append(("designed overlap", v, why))
            else:
                fails.append((a, b, "OVERLAP %.3f mm3" % v)); kinds.append(("OVERLAP", v, ""))
        cs = contacts(S[a], S[b], F[a], F[b], B[a], B[b])
        rec[(a, b)] = kinds + [(k, val, reg) for k, val, reg, _, _ in cs]
        FACEPAIRS[(a, b)] = [(k, f1, f2, val) for k, val, reg, f1, f2 in cs]
        ba, bb = body_of(a), body_of(b)
        # --- grazes ---
        if v <= VOL:
            for k, val, reg, f1, f2 in cs:
                if k.startswith("edge"):
                    fails.append((a, b, "graze: %s" % k))
            if not cs:
                fails.append((a, b, "touching (%.4f mm) with no face pair found" % dist(S[a], S[b])))
        # --- pathways ---
        for s, o in ((a, b), (b, a)):
            bj = next((j for p, j in BEARING_JOINT.items() if s.startswith(p)), None)
            if bj:
                bo = body_of(o)
                if bo not in bj:
                    fails.append((s, o, "bearing touches a part of body %s (joint %s)" % (bo, bj)))
                    continue
                # race bands on the side faces
                R, org = loc_frame(C[s])
                od = 42.0 if abs(B[s][1] - B[s][0]).max() > 40 else 37.0
                r_in, r_out = RACES[od]
                fits = [val for k, val, reg in rec[(a, b)] if k == "cyl. fit"]
                for k, val, reg in rec[(a, b)]:
                    if k != "planar mate" or reg is None:
                        continue
                    P = verts(reg)
                    if not len(P):
                        continue
                    rel = P - org
                    r = np.linalg.norm(rel - np.outer(rel @ R[:, 2], R[:, 2]), axis=1)
                    # which ring does this body carry? the body fitted on the OD is the housing
                    side = HOUSING.get((s, bo))
                    if side == "outer" and r.min() < r_in + 0.5:
                        fails.append((s, o, "housing side touches the turning INNER ring (r %.2f < d1/2 + 0.5 = %.2f)" % (r.min(), r_in + 0.5)))
                    if side == "inner" and r.max() > r_in + 0.02:
                        fails.append((s, o, "turning side reaches past the inner ring (r %.2f > d1/2 = %.2f)" % (r.max(), r_in)))
        if not (a.startswith("brg_") or b.startswith("brg_")) and ba is not None and bb is not None and ba != bb:
            ok = False
            for s, o in ((a, b), (b, a)):
                m = re.match(r"^servo_J(\d)$", s)
                if m and body_of(o) == body_of(s) + 1:
                    # the servo's faces in contact must all belong to the HORN
                    # (the part that turns): below the case (local z <= -0.49)
                    # and inside its O19.2
                    R, org = loc_frame(C[s])
                    good = not any(k == "designed overlap" for k, _, _ in rec[(a, b)])
                    for k, f1, f2, _v in FACEPAIRS[(a, b)]:
                        fs = f1 if s == a else f2
                        P = verts(fs); rel = P - org
                        z = rel @ R[:, 2]; rr = np.linalg.norm(rel - np.outer(z, R[:, 2]), axis=1)
                        good &= bool(len(P) and z.max() <= -0.49 and rr.max() <= 9.65)
                    ok = good
            sp = [p for p in SPRING_JOINT if a.startswith(p) or b.startswith(p)]
            if sp:
                ok = True
            if not ok:
                fails.append((a, b, "contact ACROSS a joint (body %s <-> %s) outside bearing / horn face" % (ba, bb)))
        if verbose:
            print("  %-22s %-22s b%s|b%s  %s" % (a, b, ba, bb, "; ".join(
                "%s%s" % (k, (" %.1f mm2" % val) if k == "planar mate" else (" clr %.3f" % val) if k == "cyl. fit"
                          else (" %.3f mm3 (%s)" % (val, reg)) if k == "designed overlap" else "")
                for k, val, reg in rec[(a, b)]) or "touch"))
    return fails, rec


SCREW_RX = (r"^(split_J\d_\d|cap_J\d_\d|j4base_forearm_\d|j5fork_j4hub_\d|j3fork_link_\d|"
            r"m4_base_foot_\d|collar_pinch|pin_J\d_\w+_[+-]\d|collar_clamp_\S+|"
            r"seam_(upper|fore)_\d+|ear_bolt_\w+|horn_screw_J\d_\d+|servo_scr_J\d_\d)$")


def bolted(rec, names, C, split_pairs, verbose=False):
    """Every bolted joint really clamps: the part under the head and the part
    holding the thread share a planar mate whose normal is ALONG the screw
    (a side-by-side wall contact clamps nothing), or they are the two halves
    of a declared split clamp."""
    out = []
    screws = [k for k in names if re.match(SCREW_RX, k)]
    parts = [k for k in names if not re.match(r".*(_ins(_\d+)?|_ins_\w+|nut.*)$", k) and k not in screws
             and not k.startswith(("brg_", "spring_", "link_set"))]

    def mates(x, kind):
        r = set()
        for (p, q), ks in rec.items():
            if x in (p, q) and any(k == kind for k, _, _ in ks):
                r.add(q if p == x else p)
        return r
    if verbose:
        print("\nBOLTED JOINTS -- the two parts a screw joins share a planar mate normal to the screw")
    for s in sorted(screws):
        if s.startswith("pin_"):
            continue                                    # shoulder pin: holds a spring, clamps nothing
        R, _ = loc_frame(C[s]); axis = R[:, 2]
        head = [p for p in mates(s, "planar mate") if p in parts]
        holders = set()
        if s.startswith("servo_scr"):                   # self-tapping: its thread IS the designed overlap
            holders |= {q for q in mates(s, "designed overlap") if q in parts}
        for q in mates(s, "cyl. fit"):
            if q in parts:
                holders.add(q)
            elif "nut" in q:
                holders |= {p for p in mates(q, "planar mate") if p in parts}
            else:
                holders |= {p for p in mates(q, "cyl. fit") if p in parts}
        pairs = [(h, k) for h in head for k in holders if h != k]

        def clamped(h, k):
            key = (min(h, k), max(h, k))
            if key in split_pairs or (h.startswith("collar_") and k.startswith("collar_") and h[:-2] == k[:-2]):
                return True
            for kk, f1, f2, val in FACEPAIRS.get(key, []):
                if kk == "planar mate" and val > 5.0 and abs(surf(f1)[1] @ axis) > 0.99:
                    return True
            return False
        ok = bool(head) and bool(holders) and all(clamped(h, k) for h, k in pairs)
        if not ok:
            out.append((s, ",".join(head) + " / " + ",".join(sorted(holders)), "bolted joint without clamped faces"))
        if verbose:
            print("  %-22s head on %-28s holds in %-28s %s" % (s, ",".join(head) or "-", ",".join(sorted(holders)) or "-",
                                                           "clamped" if ok and pairs else ("same part" if ok else "FAIL")))
    return out


HOUSING = {}
FACEPAIRS = {}


def main():
    t0 = time.time()
    A, _ = BA.build()
    S, C = {}, {}
    for ch in A.children:
        w = VF.world(ch)
        if w is not None:
            S[ch.name] = w; C[ch.name] = ch
    names = list(S)
    unassigned = [k for k in names if body_of(k) is None and not k.startswith(("brg_", "spring_"))]
    B = {k: VF.bbox(v) for k, v in S.items()}
    F = {k: faces(v) for k, v in S.items()}
    # which body holds each bearing's OUTER ring: the one fitted on its OD
    for bname in [k for k in names if k.startswith("brg_")]:
        R, org = loc_frame(C[bname])
        od = 42.0 if abs(B[bname][1] - B[bname][0]).max() > 40 else 37.0
        for o in names:
            if o == bname or not VF.overlap(B[bname], B[o], TOUCH) or dist(S[bname], S[o]) > TOUCH:
                continue
            for k, val, reg, f1, f2 in contacts(S[bname], S[o], F[bname], F[o], B[bname], B[o]):
                if k == "cyl. fit":
                    s1 = surf(f1)
                    side = "outer" if abs(s1[3] - od / 2) < 0.2 else "inner"
                    HOUSING[(bname, body_of(o))] = side
    print("RULE 4 -- mating, overlap and pathways on %d components (%d unassigned to a body: %s)\n"
          % (len(names), len(unassigned), ", ".join(unassigned) or "none"))
    fails, rec = analyse(S, C, B, F, names)
    # SPLIT CLAMPS are printed OPEN and close when their bolt is tightened; in
    # the model they stand off by their clearance. Each is declared here and
    # CHECKED: the clearance is measured on the solids, and the gap that
    # closes must have the travel to take it up (with 0.3 / 0.05 mm spare).
    import gen_base_collar as GB
    import spring_parts as SP
    import gen_drive_j2 as G2
    SPLIT_EDGES = []
    print("\nSPLIT CLAMPS -- printed open, closed by their bolt: travel needed vs available")
    c1 = dist(S["spigot_collar"], S["J2_turret_p1"]); c2 = dist(S["J2_turret_p1"], S["j1_hub"])
    need = np.pi * 2 * (c1 + c2)
    ok = need <= GB.SLOT_W - 0.3 and np.pi * 2 * c2 <= 2 * G2.COLLET_SLIT - 0.3
    print("  spigot collar + slit spigot (collet) on the J1 hub plug: clearances %.3f + %.3f mm -> slot travel %.2f of %.1f, "
          "spigot slits %.2f of %.1f  %s" % (c1, c2, need, GB.SLOT_W, np.pi * 2 * c2, 2 * G2.COLLET_SLIT, "ok" if ok else "FAIL"))
    if ok:
        SPLIT_EDGES += [("spigot_collar", "J2_turret_p1"), ("J2_turret_p1", "j1_hub")]
    else:
        fails.append(("spigot_collar", "J2_turret_p1", "collet cannot close"))
    for pre, lk in (("collar_upper", "link_upper"), ("collar_fore", "link_fore")):
        cp = dist(S[pre + "_+y"], S[lk + "_tongue"]); cm = dist(S[pre + "_-y"], S[lk + "_groove"])
        ok = cp + cm <= SP.SPLIT_GAP - 0.05
        print("  %-13s halves on the %s: back plates %.3f + %.3f mm off -> arm gap travel %.2f of %.2f  %s"
              % (pre, lk, cp, cm, cp + cm, SP.SPLIT_GAP, "ok" if ok else "FAIL"))
        if ok:
            SPLIT_EDGES += [(pre + "_+y", lk + "_tongue"), (pre + "_-y", lk + "_groove")]
        else:
            fails.append((pre, lk, "split collar cannot close on the link"))
    split_pairs = {(min(p, q), max(p, q)) for p, q in SPLIT_EDGES}
    fails += bolted(rec, names, C, split_pairs, verbose=True)
    # 5. ATTACHED: every part of body k is reached from the servo horn that
    # drives it (body 0: from the foot) through parts that actually TOUCH it
    # (planar mate, fit, designed thread / pinch) inside that body. A part
    # held only across a clearance -- a key with play, a ring in a loose bore
    # -- is not reached: it would rattle, and it fails here.
    import collections
    adj = collections.defaultdict(set)
    for (p, q), ks in rec.items():
        if any(k in ("planar mate", "cyl. fit", "designed overlap") for k, _, _ in ks):
            adj[p].add(q); adj[q].add(p)
    for p, q in SPLIT_EDGES:
        adj[p].add(q); adj[q].add(p)
    print("\nATTACHED -- each body reached from what drives it, through touching parts only")
    for b in range(7):
        members = {k for k in names if body_of(k) == b}
        start = "j1_mount" if b == 0 else "servo_J%d" % b
        seen, todo_ = {start}, [start]
        while todo_:
            x = todo_.pop()
            for y in adj[x]:
                if y not in seen and (body_of(y) == b or (x == start and b > 0 and body_of(y) == b)):
                    if body_of(y) == b:
                        seen.add(y); todo_.append(y)
        loose = sorted(members - seen)
        for k in loose:
            fails.append((k, "body %d" % b, "NOT ATTACHED: no touching path to %s" % start))
        print("  body %d (from %-9s): %3d parts, %3d reached%s" % (b, start, len(members), len(members & seen),
              "" if not loose else "   LOOSE: " + ", ".join(loose)))
    print("\nRULE 4: %d failure(s)   (%.0f s)" % (len(fails), time.time() - t0))
    for f in fails:
        print("   FAIL %-22s %-26s %s" % f)
    # controls
    print("\nCONTROLS")
    def moved(sh, v):
        tr = gp_Trsf(); tr.SetTranslation(gp_Vec(*v)); return BRepBuilderAPI_Transform(sh, tr, True).Shape()
    ctrl = []
    for lab, part, vec, want in (
            ("J3_p2 pushed 0.3 mm into J3_p1 (along the joint axis)", "J3_p2", -0.3 * loc_axis(C, "servo_J3"), "OVERLAP"),
            ("j4_cap lifted 0.2 mm off j4_base", "j4_cap", (0, 0, 0.2), "bolted joint without clamped faces"),
            ("upper link tongue moved 1.1 mm onto the J2 cheek", "link_upper_tongue", (0, 1.1, 0), "ACROSS a joint")):
        S2 = dict(S); S2[part] = moved(S[part], vec)
        B2 = dict(B); B2[part] = VF.bbox(S2[part])
        F2 = dict(F); F2[part] = faces(S2[part])
        todo = [(min(part, o), max(part, o)) for o in names if o != part and VF.overlap(B2[part], B2[o], TOUCH)]
        saved = dict(FACEPAIRS)
        for key in todo:
            FACEPAIRS.pop(key, None)
        f2, rec2 = analyse(S2, C, B2, F2, names, pairs=todo, verbose=False)
        if want.startswith("bolted"):
            r2 = {k: v for k, v in rec.items() if k not in set(todo)}; r2.update(rec2)
            hit = any(f[0].startswith("cap_J4") for f in bolted(r2, names, C, set()))
        else:
            hit = any(want in f[2] for f in f2)
        FACEPAIRS.clear(); FACEPAIRS.update(saved)
        ctrl.append(hit)
        print("  %-58s -> %s" % (lab, "DETECTED" if hit else "NOT DETECTED"))
    if not all(ctrl):
        fails.append(("controls", "", "a control was not detected"))
    return len(fails)


def loc_axis(C, name):
    R, _ = loc_frame(C[name])
    return R[:, 2]


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
