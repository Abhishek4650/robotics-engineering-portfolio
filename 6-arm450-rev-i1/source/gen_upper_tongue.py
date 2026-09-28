#!/usr/bin/env python3
"""
ARM-450 rev I -- upper-link TONGUE half = the released part + flush heads.

The released link_upper_tongue is used unchanged EXCEPT that its seam-screw
holes and its ear-screw hole get counterbores (gen_forearm.py explains why:
1.0 mm from link face to fork cheek, heads stood 3 mm proud into the J2
turret cheek). Hole centres are MEASURED on the released solid first (the
counterbore goes where the hole really is, not where a constant says).

If your upper links are already printed: the same counterbores can be drilled
by hand -- O6.0 x 3.2 deep on each O3.4 seam hole, O5.0 x 2.7 on the ear hole,
from the tongue's OUTER face.
"""
import os
import sys

import numpy as np
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_forearm as GF      # noqa: E402
LP = GF.LP
REL = os.path.join(HERE, "..", "out_cad", "link_upper_tongue.step")


def hole_centre(sh, x0, y0, z, r_max=3.0):
    """Centre + diameter of the hole near (x0, y0) at height z, from 24 radial
    probes (exact classifier on the released solid)."""
    clf = BRepClass3d_SolidClassifier(sh)

    def solid(x, y):
        clf.Perform(gp_Pnt(float(x), float(y), float(z)), 1e-6)
        return clf.State() == TopAbs_IN
    c = np.array([x0, y0], float)
    for _ in range(3):
        pts = []
        for a in np.radians(np.arange(0, 360, 15)):
            d = np.array([np.cos(a), np.sin(a)])
            for r in np.arange(0.2, r_max, 0.005):
                if solid(*(c + r * d)):
                    pts.append(c + r * d); break
        pts = np.array(pts)
        # algebraic circle fit
        A = np.c_[2 * pts, np.ones(len(pts))]
        bb = (pts ** 2).sum(1)
        sol = np.linalg.lstsq(A, bb, rcond=None)[0]
        c = sol[:2]
        rad = np.sqrt(sol[2] + c @ c)
    return c, 2 * rad


def build():
    s = cq.importers.importStep(REL)
    sh = s.val().wrapped
    holes = []
    for (x, y) in GF.seam_holes(LP.UPPER_FACE_X, 0.0):
        c, d = hole_centre(sh, x, y, 6.0)
        holes.append((c, d))
    ce, de = hole_centre(sh, GF.EAR_XC, 0.0, 6.0)
    return s, holes, (ce, de)


if __name__ == "__main__":
    from OCP.BRepCheck import BRepCheck_Analyzer
    s, holes, ear = build()
    for (c, d), (x, y) in zip(holes, GF.seam_holes(LP.UPPER_FACE_X, 0.0)):
        print("seam hole  expected (%6.2f,%+6.2f)  measured (%6.2f,%+6.2f)  O %.2f" % (x, y, c[0], c[1], d))
    print("ear hole   expected (%6.2f,%+6.2f)  measured (%6.2f,%+6.2f)  O %.2f" % (GF.EAR_XC, 0, ear[0][0], ear[0][1], ear[1]))
    ok = all(abs(d - 3.4) < 0.1 for _, d in holes) and abs(ear[1] - LP.TIP_CLEAR) < 0.1
    assert ok, "a hole is not what the design says -- stop"
    v0 = s.val().Volume()
    # TANGENCY BRIDGES. Each seam boss (O9.5 at y +-17.85) touches the
    # flange's inner wall (y +-22.6) along a single LINE -- the released STL
    # is open along exactly those 8 lines (non-manifold), which a slicer has
    # to guess at. A 3 x 1.2 mm web at each touch turns the line into a face.
    # Holes do not move (the released groove's inserts still line up).
    wall_y = LP.SEC_H / 2 - LP.WALL_FLANGE
    for (c, _) in holes:
        sy = np.sign(c[1])
        s = s.union(cq.Workplane("XY").center(c[0], sy * (wall_y - 0.5))
                    .rect(3.0, 1.2).extrude(LP.HALF_D - LP.WALL_WEB).translate((0, 0, LP.WALL_WEB)))
    # cable-bore skin: the released O10 bore (centre 5.5 from the outer face)
    # left 0.5 mm of outer skin over its last 30 mm (audit); fill its bottom
    # 0.7 mm -> 1.2 mm skin, as the rev-I forearm. The fill ENDS at the
    # link's end face x = UPPER_FACE_X: a first version ran 0.5 mm past it
    # into the J3 fork (Rule 4 check: 1.2 mm3 overlap).
    fx = LP.UPPER_FACE_X
    fill = (cq.Workplane("YZ").workplane(offset=fx - 29.5).center(0, LP.HALF_D - 9.0)
            .circle(LP.CABLE_D / 2).extrude(29.5)
            .intersect(cq.Workplane("XY").center(fx - 15.0, 0).rect(30.0, 12.0).extrude(0.8).translate((0, 0, 0.4))))
    s = s.union(fill)
    t = GF.counterbores(s, LP.UPPER_FACE_X, 0.0, holes=[tuple(c) for c, _ in holes])
    # the ear counterbore at the measured ear centre
    if np.linalg.norm(ear[0] - np.array([GF.EAR_XC, 0.0])) > 0.02:
        raise SystemExit("ear hole moved: %s" % ear[0])
    sol = t.val()
    bb = sol.BoundingBox()
    assert abs(bb.xmax - fx) < 1e-6, "tongue runs past its end face: x max %.3f" % bb.xmax
    print("link_upper_tongue rev I  %.1f mm3 (released %.1f)  solids %d  BRep valid %s"
          % (sol.Volume(), v0, len(sol.Solids()), BRepCheck_Analyzer(sol.wrapped).IsValid()))
    cq.exporters.export(t, os.path.join(HERE, "link_upper_tongue.step"))
    cq.exporters.export(t, os.path.join(HERE, "link_upper_tongue.stl"), tolerance=0.01, angularTolerance=0.1)
    import trimesh
    m = trimesh.load(os.path.join(HERE, "link_upper_tongue.stl")); m.merge_vertices(digits_vertex=4)
    print("STL watertight %s  (released STL: open along the 8 boss/wall tangency lines)" % m.is_watertight)
