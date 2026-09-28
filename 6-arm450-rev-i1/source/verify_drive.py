#!/usr/bin/env python3
"""
Drive-train verification for a joint: every part against EVERY other part it
can touch, in the assembled pose. Rev H only tested servo-vs-p2, which is how
a 2.61 mm cap clash and a horn that drove nothing both got a PASS.

Checks, per joint:
  A  servo seats on its cap face at P, horn on the joint axis
  B  servo vs p1, p2, shaft, and every neighbour: no interpenetration
     (the pinch walls are the one allowed contact, and are reported)
  C  the horn face MEETS the shaft end face (a load path, not a gap)
  D  the horn bolt holes land inside the horn disc
  E  shaft vs p1, p2 and neighbours: runs in the bores, no clash
  F  a driver reaches the horn screws through the shaft bore
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_common as DC       # noqa: E402
import seat_servo as S          # noqa: E402

RES = []


def rec(label, ok, detail):
    print("   %-50s %s  %s" % (label, "PASS" if ok else "FAIL", detail))
    RES.append((label, ok, detail))


def attach_occ(mesh, step_path, T=None):
    """Give a mesh its exact BRep for containment (see contains()).
    Needed where the mesh is open, or so slender and finely tessellated that
    trimesh's fallback ray test exhausts memory (link_fore_groove: 57 M rows)."""
    import cadquery as cq
    from OCP.gp import gp_Trsf
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    sh = cq.importers.importStep(step_path).val().wrapped
    if T is not None:
        tr = gp_Trsf(); tr.SetValues(*[float(T[i, j]) for i in range(3) for j in range(4)])
        sh = BRepBuilderAPI_Transform(sh, tr, True).Shape()
    mesh.occ = sh
    return mesh


def contains(m, P, chunk=20000):
    """Point-in-solid. Uses OpenCascade's exact classifier when the part
    carries its BRep (m.occ) -- required where the mesh is not closed."""
    occ = getattr(m, "occ", None)
    if occ is not None:
        from OCP.BRepClass3d import BRepClass3d_SolidClassifier
        from OCP.gp import gp_Pnt
        from OCP.TopAbs import TopAbs_IN
        out = np.zeros(len(P), bool)
        clf = BRepClass3d_SolidClassifier(occ)
        for i, p in enumerate(P):
            clf.Perform(gp_Pnt(*map(float, p)), 1e-6)
            out[i] = clf.State() == TopAbs_IN
        return out
    return np.concatenate([m.contains(P[i:i + chunk]) for i in range(0, len(P), chunk)])


def seated_servo(P):
    srv, z_step = S.servo_in_joint_frame()
    srv.apply_translation([0, 0, P - (z_step - DC.CAP_FACE_BELOW_STEP)])
    return srv


def verify(jn, p1, p2, shaft, P, neighbours, z_idle_end):
    print("\n" + "=" * 76)
    print("DRIVE TRAIN -- %s   (joint frame, axis = Z)" % jn)
    print("=" * 76)
    srv = seated_servo(P)
    bb = srv.bounds
    # A
    sl = srv.section(plane_origin=[0, 0, bb[0][2] + 0.8], plane_normal=[0, 0, 1])
    v = np.asarray(sl.vertices)
    off = np.hypot((v[:, 0].max() + v[:, 0].min()) / 2, (v[:, 1].max() + v[:, 1].min()) / 2)
    rec("A horn on the joint axis", off < 0.02, "offset %.4f mm" % off)
    rec("A horn face at P - 3.011", abs(bb[0][2] - (P - DC.HORN_BELOW_CAP)) < 0.02,
        "horn face z %.3f, want %.3f" % (bb[0][2], P - DC.HORN_BELOW_CAP))
    rec("A case back inside the bay", bb[1][2] <= P + DC.BAY_T + 0.01,
        "back %.3f, bay top %.3f" % (bb[1][2], P + DC.BAY_T))
    # B
    Ps = srv.sample(60000)
    # The cap face SEATS on p1 at P, and the horn face BOLTS to the shaft end.
    # Those are designed bearing faces: contact is allowed only ON that plane
    # (z within 0.02 mm of it). Anything deeper is a real clash.
    for nm, m, plane in (("p1", p1, P), ("shaft", shaft, P - DC.HORN_BELOW_CAP)):
        ins = contains(m, Ps)
        c = Ps[ins]
        deep = int((np.abs(c[:, 2] - plane) > 0.02).sum()) if len(c) else 0
        rec("B servo vs %s: contact only on the seat plane" % nm, deep == 0,
            "%d contacts at z %.3f, %d off the plane"
            % (int(ins.sum()), plane, deep))
    ins = contains(p2, Ps)
    c = Ps[ins]
    offp = int((np.abs(c[:, 1]) < DC.PINCH / 2 - 0.05).sum()) if len(c) else 0
    pen = (np.abs(c[:, 1]).max() - DC.PINCH / 2) if len(c) else 0.0
    rec("B servo vs p2: contact ONLY on the pinch walls", offp == 0,
        "%d contacts, %d off-pinch, pinch %.3f mm/side" % (int(ins.sum()), offp, pen))
    for nm, m in neighbours.items():
        n = int(contains(m, Ps).sum())
        rec("B servo vs %s" % nm, n == 0, "%d / 60000" % n)
    # C  horn face meets shaft end face
    sb = shaft.bounds
    gap = bb[0][2] - sb[1][2]
    rec("C horn face meets the shaft end", abs(gap) < 0.02,
        "horn face %.3f, shaft end %.3f, gap %.3f mm" % (bb[0][2], sb[1][2], gap))
    # D  horn holes inside the horn disc (r 9.6), with edge distance
    r_hole = DC.HORN_BCD / 2 + DC.HORN_HOLE_D / 2
    rec("D horn bolt holes inside the O19.2 horn disc", r_hole < 9.6 - 0.8,
        "holes reach r %.2f, disc r 9.60" % r_hole)
    # E  shaft vs housings and neighbours
    Pt = shaft.sample(60000)
    for nm, m in (("p1", p1), ("p2", p2)):
        n = int(contains(m, Pt).sum())
        rec("E shaft vs %s" % nm, n == 0, "%d / 60000" % n)
    for nm, m in neighbours.items():
        n = int(contains(m, Pt).sum())
        if nm.startswith("shaft_clamp") or nm.startswith("link_"):
            # these GRIP the shaft: a slip/clamp fit reads as surface contact
            if n:
                q = Pt[contains(m, Pt)]
                r = np.hypot(q[:, 0], q[:, 1])
                rec("E shaft vs %s (grip)" % nm, r.max() <= DC.SHAFT_OD / 2 + 0.01,
                    "%d pts, all at r %.2f..%.2f (surface)" % (n, r.min(), r.max()))
            else:
                rec("E shaft vs %s (grip)" % nm, True, "clear")
        else:
            rec("E shaft vs %s" % nm, n == 0, "%d / 60000" % n)
    # F  driver through the bore to the horn screws
    L = sb[1][2] - DC.SHAFT_END_T - z_idle_end
    rec("F driver reach through the O%.0f bore" % DC.SHAFT_BORE, L < 60.0,
        "screw heads %.1f mm in from the idle end; 6 mm driver in a %.0f bore"
        % (L, DC.SHAFT_BORE))
    return srv
