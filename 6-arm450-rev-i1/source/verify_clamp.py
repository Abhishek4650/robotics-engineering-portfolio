#!/usr/bin/env python3
"""
ARM-450 rev I -- LINK LOCK at J2 / J3 (Rule 4: attached, zero play).

Each link half: M5 x 10 cup-point set screws at 90 / 270 deg (link frame),
self-tapped into the link's OWN O4.2 side holes, through the centring ring's
O5.4 holes, tip on the shaft's double-D flat. Checked part against part on
the exact solids, in the world:
  1. ring x link, ring x shaft: common volume 0; ring fits 0.025 (touching)
  2. seam ear inside the ring gap (the ring can be fitted), ring play vs ear
  3. each set-screw axis: the link has its O4.2 hole there (measured on the
     link), the ring hole clears the screw, the shaft surface on that line is
     the FLAT at r 14.20 on BOTH sides (probed), thread length in the link
  4. hex key (2.5 mm, O3.2 path) reaches each screw from outside, whole arm
"""
import os
import sys

import numpy as np
import cadquery as cq
from OCP.gp import gp_Trsf, gp_Pnt
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_IN
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asm_xforms as AX    # noqa: E402
import gen_clamp as GC     # noqa: E402
import drive_common as DC  # noqa: E402

FORK_R = np.array([[0., 1., 0.], [0., 0., 1.], [1., 0., 0.]])


def M(R=np.eye(3), t=(0, 0, 0)):
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t; return T


TURW = M(t=(0, 0, 50.0))
J3W = M(FORK_R, (0, 0, 209.0))
REL = os.path.join(HERE, "..", "out_cad")


def step(p):
    return cq.importers.importStep(p).val().wrapped


def place(sh, T):
    tr = gp_Trsf(); tr.SetValues(*[float(T[i, j]) for i in range(3) for j in range(4)])
    return BRepBuilderAPI_Transform(sh, tr, True).Shape()


def vol(sh):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(sh, g); return g.Mass()


def common(a, b):
    c = BRepAlgoAPI_Common(a, b); c.SetFuzzyValue(1e-5); c.Build()
    return vol(c.Shape()) if c.IsDone() else float("nan")


def inside(sh, p):
    c = BRepClass3d_SolidClassifier(sh); c.Perform(gp_Pnt(*map(float, p)), 1e-6)
    return c.State() == TopAbs_IN


def main():
    X = AX.xforms()
    ring0 = step(os.path.join(HERE, "shaft_clamp.step"))
    js = {"J2": place(step(os.path.join(HERE, "J2_shaft.step")), TURW),
          "J3": place(step(os.path.join(HERE, "J3_shaft.step")), J3W)}
    rows = [("1", "link_upper_groove", REL, "J2"), ("2", "link_upper_tongue", HERE, "J2"),
            ("3", "link_fore_groove", HERE, "J3"), ("4", "link_fore_tongue", HERE, "J3")]
    fails, SCREWS = 0, []
    for k, lk, fold, j in rows:
        T = X[lk]; ax = T[:3, 2]
        link = place(step(os.path.join(fold, lk + ".step")), T)
        ring = place(ring0, T); sh = js[j]
        print("ring %s in %s (axis %s)" % (k, lk, np.round(ax, 3)))
        v1, v2 = common(ring, link), common(ring, sh)
        d1 = BRepExtrema_DistShapeShape(ring, link).Value(); d2 = BRepExtrema_DistShapeShape(ring, sh).Value()
        ok = v1 < 1e-3 and v2 < 1e-3 and d1 < 0.03 and d2 < 0.03
        fails += not ok
        print("   1  ring x link %.4f mm3, x shaft %.4f mm3; touching link %.3f / shaft %.3f mm  %s"
              % (v1, v2, d1, d2, "ok" if ok else "FAIL"))
        env = cq.Workplane("XY").circle(GC.OD / 2).circle(GC.BORE / 2).extrude(GC.W) \
            .intersect(cq.Workplane("XY").center(-GC.OD / 4 - 2.0, 0).rect(GC.OD / 2 + 4.0, GC.GAP)
                       .extrude(GC.W)).val().wrapped
        ve = common(place(env, T), link)
        ok = ve > 1.0
        fails += not ok
        print("   2  seam ear inside the ring gap: %.1f mm3 (ring slides in over it)  %s" % (ve, "ok" if ok else "FAIL"))
        for ang in (90, 270):
            a = np.radians(ang)
            g = T[:3, :3] @ np.array([np.cos(a), np.sin(a), 0.0])
            p0 = T[:3, 3] + T[:3, :3] @ np.array([0, 0, GC.SET_Z])
            # link hole: void on the axis from r 19.3 out through the flank, material at r 2.4 off-axis
            u = np.cross(g, ax); u /= np.linalg.norm(u)
            rr = np.arange(19.3, 24.9, 0.1)
            axis_void = all(not inside(link, p0 + g * r) for r in rr)
            hole_r = None
            for r_off in np.arange(1.0, 3.0, 0.02):
                if inside(link, p0 + g * 22.0 + u * r_off):
                    hole_r = r_off; break
            thread = sum(inside(link, p0 + g * r + u * 2.4) for r in rr) * 0.1
            # ring hole clears the M5
            ring_clear = all(not inside(ring, p0 + g * r + u * 2.6) for r in np.arange(15.2, 19.1, 0.1))
            # shaft surface on the screw axis
            r_s = next((r for r in np.arange(16.0, 10.0, -0.005) if inside(sh, p0 + g * r)), None)
            on_flat = r_s is not None and abs(r_s - 14.20) < 0.03
            ok = axis_void and hole_r is not None and abs(2 * hole_r - 4.2) < 0.15 and ring_clear and on_flat and thread >= 4.5
            fails += not ok
            SCREWS.append((k, ang, p0, g))
            print("   3  set screw %3d deg: link hole O%.2f (M5 self-tap), thread in link %.1f mm, ring hole clears M5 %s, "
                  "shaft surface on the axis r %.3f -> %s  %s"
                  % (ang, 2 * hole_r if hole_r else -1, thread, ring_clear, r_s or -1,
                     "ON the flat" if on_flat else "NOT on a flat", "ok" if ok else "FAIL"))
    # 4. hex-key access in the assembled arm
    import full_scene as FS
    import verify_drive as VD
    sc = FS.scene()
    print("\n4  hex key (O3.2 path from the screw's outer end, 80 mm) in the whole assembled arm")
    for k, ang, p0, g in SCREWS:
        u = np.cross(g, [0, 0, 1.0])
        if np.linalg.norm(u) < 0.1:
            u = np.cross(g, [1.0, 0, 0])
        u /= np.linalg.norm(u); w = np.cross(g, u)
        r0 = -DC.FLAT_Y + GC.SET_L + 0.2
        P = np.array([p0 + g * r + 1.6 * (np.cos(t) * u + np.sin(t) * w) for r in np.arange(r0, r0 + 80, 0.5)
                      for t in np.linspace(0, 2 * np.pi, 8, endpoint=False)] +
                     [p0 + g * r for r in np.arange(r0, r0 + 80, 0.5)])
        hits = []
        for nm, m in sc.items():
            lo, hi = m.bounds
            sel = np.all((P >= lo - 0.1) & (P <= hi + 0.1), axis=1)
            if sel.any() and VD.contains(m, P[sel]).any():
                hits.append(nm)
        ok = not hits
        fails += not ok
        print("   ring %s screw %3d: %s" % (k, ang, "CLEAR" if ok else "BLOCKED by " + ", ".join(hits)))
    print("\nLINK LOCK VERIFICATION: %d failure(s)" % fails)
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
