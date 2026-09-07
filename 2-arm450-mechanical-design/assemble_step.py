#!/usr/bin/env python3
"""
ARM-450 — inspection assembly, exported as STEP.

Why a second assembly script. `assemble.py` builds the arm from the STL meshes
and renders pictures of it. That is what the interference sweep and the sine
clearance check run against, and it is the right tool for those jobs -- but an
STL assembly is a bag of triangles. Opened in SolidWorks it has no part names,
no separable bodies, no colours and no B-rep, so it cannot be sectioned,
measured or inspected. This script places the SAME parts at the SAME positions
and writes a real STEP assembly.

Placement is not re-derived. Every transform here comes from `assemble.build()`
-- the same joint frames, the same mating offsets -- and each part is centred
using the bounding box of its own STL, so a component lands in exactly the
position the collision sweep cleared. If the two ever disagree, the STEP is
wrong, and `check_assembly_step.py` is what says so.

Bought items are included as models, distinguished by colour from the printed
structure: bearings, shafts and servo bodies are not printed and an inspector
should not have to guess which is which.

Writes:
    output/cad/arm450_assembly_home.step        all joints at zero
    output/cad/arm450_assembly_working.step     a mid-trace pose
    output/cad/arm450_assembly_exploded.step    separated along the mating axes
"""
import os
import numpy as np
import cadquery as cq
import trimesh
from OCP.gp import gp_Trsf
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder

import sys

import assemble as A          # the verified placement logic and constants
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad"))
import params as P            # bearing sizes, so nothing is restated here

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "output", "cad")

# --- colours: printed structure vs bought items -------------------------
COL = {
    "shell":  cq.Color(0.66, 0.71, 0.77, 1.0),
    "joint":  cq.Color(0.28, 0.55, 0.62, 1.0),
    "servo":  cq.Color(0.72, 0.36, 0.28, 1.0),
    "steel":  cq.Color(0.55, 0.57, 0.61, 1.0),
    "base":   cq.Color(0.48, 0.51, 0.55, 1.0),
    "tool":   cq.Color(0.30, 0.32, 0.36, 1.0),
    "brg":    cq.Color(0.85, 0.72, 0.20, 1.0),
}

_CACHE = {}


def part(stem, centre=True):
    """The STEP solid, translated by the SAME offset assemble.py applies to the
    STL. Using the mesh bounds rather than the solid's own bounding box is
    deliberate: OCCT's box is computed on the exact surfaces and differs from
    the tessellated one by a few microns, and the point of this file is to
    reproduce the mesh assembly exactly, not to be independently right."""
    key = (stem, centre)
    if key in _CACHE:
        return _CACHE[key]
    shp = cq.importers.importStep(os.path.join(CAD, f"{stem}.step"))
    off = np.zeros(3)
    if centre:
        m = trimesh.load(os.path.join(CAD, f"{stem}.stl"), force="mesh")
        off = -m.bounds.mean(axis=0)
    _CACHE[key] = (shp, off)
    return _CACHE[key]


def mesh_bounds(stem):
    return trimesh.load(os.path.join(CAD, f"{stem}.stl"), force="mesh").bounds


def pockets(stem, od, tol=0.12):
    """Every cylindrical face at diameter `od` in a part, returned as the
    MIDPOINT of that face along its own axis, plus the axis direction, in the
    part's own coordinates.

    Bearing seats are read out of the B-rep rather than assumed. Placing them
    from a nominal spacing would put a bearing wherever the constant said,
    including in parts that have no pocket at all -- which is how a render ends
    up showing hardware the part cannot accept."""
    shp, _ = part(stem, centre=False)
    out = []
    for f in shp.faces().vals():
        a = BRepAdaptor_Surface(f.wrapped)
        if a.GetType() != GeomAbs_Cylinder:
            continue
        cyl = a.Cylinder()
        if abs(cyl.Radius() * 2 - od) > tol:
            continue
        ax = cyl.Axis()
        d = np.array([ax.Direction().X(), ax.Direction().Y(), ax.Direction().Z()])
        p0 = np.array([ax.Location().X(), ax.Location().Y(), ax.Location().Z()])
        vs = [np.array([v.X, v.Y, v.Z]) for v in f.Vertices()]
        if not vs:
            continue
        ts = [(v - p0) @ d for v in vs]
        out.append((p0 + d * ((min(ts) + max(ts)) / 2.0), d))
    return out


def _z_to(d):
    """Rotation taking +Z onto unit vector d."""
    d = np.asarray(d, float); d = d / np.linalg.norm(d)
    z = np.array([0.0, 0.0, 1.0])
    v = np.cross(z, d); c = float(z @ d)
    if np.linalg.norm(v) < 1e-12:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1.0 + c)


def loc(R=np.eye(3), t=(0.0, 0.0, 0.0), pre=(0.0, 0.0, 0.0)):
    """A cq.Location for rotation R about the origin then translation t, with
    `pre` applied in the part's own frame first (the centring offset)."""
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = np.asarray(t, float) + R @ np.asarray(pre, float)
    # cq.Location(cq.Matrix(...)) is not an overload in this cadquery build --
    # it reads a single argument as a translation and rejects it. Go through a
    # gp_Trsf, which takes the 3x4 rigid transform directly.
    trsf = gp_Trsf()
    trsf.SetValues(*[float(v) for v in M[:3, :].reshape(-1)])
    return cq.Location(trsf)


def build_step(q=(0, 0, 0, 0, 0, 0), explode=0.0, tool="gripper"):
    q1, q2, q3, q4, q5, q6 = q
    assy = cq.Assembly(name="ARM-450")
    # Seats already filled, in assembly coordinates. At a SHARED joint the
    # outboard pocket of one link and the inboard pocket of the next are the
    # same hole in space, so seating "every pocket" put two bearings inside
    # each other -- four at the elbow. One bearing per location.
    assy._seats = []

    def add(stem, R, t, colour, name=None, centre=True, extra=(0.0, 0.0, 0.0)):
        shp, off = part(stem, centre)
        pre = np.asarray(off) + np.asarray(extra)
        assy.add(shp, name=name or stem, loc=loc(R, t, pre), color=COL[colour])
        return R, np.asarray(t, float), pre

    # --- base: bottom face on z = 0, centred in XY -----------------------
    bb = mesh_bounds("base")
    pl = add("base", np.eye(3), (0, 0, 0), "base", centre=False,
             extra=(-bb.mean(axis=0)[0], -bb.mean(axis=0)[1], -bb[0][2]))
    _seat(assy, "base", pl, "J1_base")

    # --- J1 turret -------------------------------------------------------
    R1 = A.rot([0, 0, 1], q1)
    tb = mesh_bounds("turret_j1")
    pl = add("turret_j1", R1, (0, 0, A.BASE_H + explode * 0.6), "joint",
             centre=False, extra=(0, 0, -tb[0][2] - 14.0))
    _seat(assy, "turret_j1", pl, "J1")

    j2 = np.array([0.0, 0.0, A.BASE_H + A.SHOULDER])
    R2 = R1 @ A.rot([0, 1, 0], q2)
    _link(assy, add, j2, R2, A.L2, explode, "L2")
    add("servo_collar", R2, j2 + R2 @ np.array([0, 44 + explode * 2, 6]),
        "servo", name="servo_collar_J2")

    j3 = j2 + R2 @ np.array([0, 0, A.L2])
    R3 = R2 @ A.rot([0, 1, 0], q3)
    _link(assy, add, j3, R3, A.L3, explode, "L3")
    add("servo_collar", R3, j3 + R3 @ np.array([0, 44 + explode * 2, 6]),
        "servo", name="servo_collar_J3")

    # --- wrist -----------------------------------------------------------
    j4 = j3 + R3 @ np.array([0, 0, A.L3])
    R4 = R3 @ A.rot([0, 0, 1], q4)
    hb = mesh_bounds("wrist_j4_housing")
    pl = add("wrist_j4_housing", R4,
             j4 + R4 @ np.array([0, 0, 32.0 + explode * 1.2]),
             "joint", centre=False, extra=(0, 0, -hb[0][2]))
    _seat(assy, "wrist_j4_housing", pl, "J4", stub="bearing_6706")

    j5 = j4 + R4 @ np.array([0, 0, A.J4_J5])
    yb = mesh_bounds("wrist_j5_yoke")
    pl = add("wrist_j5_yoke", R4,
             j4 + R4 @ np.array([0, 0, A.J4_J5 - 12.0 + explode * 1.4]),
             "shell", centre=False, extra=(0, 0, -yb[0][2]))
    _seat(assy, "wrist_j5_yoke", pl, "J5", stub="bearing_6706")

    R5 = R4 @ A.rot([0, 1, 0], q5)
    R6 = R5 @ A.rot([0, 0, 1], q6)
    ob = mesh_bounds("wrist_j6_output")
    pl = add("wrist_j6_output", R6,
             j5 + R6 @ np.array([0, 0, A.J5_J6 + explode * 1.8]),
             "joint", centre=False, extra=(0, 0, -ob[0][2]))
    _seat(assy, "wrist_j6_output", pl, "J6", stub="bearing_6706")

    tcp = j5 + R5 @ np.array([0, 0, A.J5_J6 + A.J6_TCP])

    # --- fitted tool -----------------------------------------------------
    if tool in ("gripper", "dock"):
        add("tool_adapter", R6, tcp + R6 @ np.array([0, 0, explode * 3.0]),
            "tool", extra=(0, 0, 6.0))
        stem = "tool_gripper" if tool == "gripper" else "tool_dock"
        Rflip = R6 @ A.rot([1, 0, 0], np.pi)
        tb2 = mesh_bounds(stem)
        # the socket is in the tool's top face, so it mounts flipped
        add(stem, Rflip, tcp + R6 @ np.array([0, 0, 5.0 + explode * 4.0]),
            "tool", centre=False,
            extra=(-tb2.mean(axis=0)[0], -tb2.mean(axis=0)[1], -tb2[1][2]))
        if tool == "gripper":
            for k, sy in enumerate((-1, 1)):
                Rj = R6 @ (A.rot([0, 0, 1], np.pi) if sy < 0 else np.eye(3))
                jb = mesh_bounds("gripper_jaw")
                # assemble.py translates the CENTRED mesh by -bounds[0][2]+8,
                # and after centring bounds[0][2] is -h/2. Using the RAW bounds
                # here put both jaws 11.00 mm out -- caught by the centroid
                # comparison in check_assembly_step.py, not by eye.
                h = jb[1][2] - jb[0][2]
                add("gripper_jaw", Rj,
                    tcp + R6 @ np.array([0, sy * 12.8, explode * 4.5]),
                    "tool", name=f"gripper_jaw_{k+1}",
                    extra=(0, 0, h / 2.0 + 8.0))
    return assy, tcp


def _link(assy, add, origin, R, length, explode, tag):
    """One link, placed by the SAME arithmetic as assemble.link_assembly():
    two halves mated at the seam, shaft and clamp on the joint axis, and the
    bearing pair read out of the halves' own pockets."""
    RL = R @ A.MESH2CHAIN
    for stem, flip, dy in (("link_half_groove", False, -A.HALF_D / 2.0),
                           ("link_half_tongue", True, +A.HALF_D / 2.0)):
        Rh = RL @ (A.rot([1, 0, 0], np.pi) if flip else np.eye(3))
        off = R @ np.array([0.0, dy + np.sign(dy) * explode, length / 2.0])
        pl = add(stem, Rh, origin + off, "shell", name=f"{stem}_{tag}")
        # the bearing that sits in THIS half, read from the pocket in the part
        _seat(assy, stem, pl, f"{tag}_{'tongue' if flip else 'groove'}")
    Rs = R @ A.rot([1, 0, 0], np.pi / 2)
    add("joint_shaft", Rs, origin + R @ np.array([0, explode * 2.2, 0]),
        "steel", name=f"joint_shaft_{tag}")
    add("shaft_clamp", Rs, origin + R @ np.array([0, -explode * 1.4, 0]),
        "joint", name=f"shaft_clamp_{tag}")


def _seat(assy, stem, placement, tag, stub="bearing_6806"):
    """Drop a bearing into every pocket the part ACTUALLY has, using the same
    placement `add` used for the part itself.

    `placement` is the (R, t, pre) triple add() returns, so the bearing cannot
    drift away from its housing: if the part moves, its bearings move with it
    by construction rather than by a second copy of the same arithmetic."""
    R, t, pre = placement
    od = P.BRG_OD if stub == "bearing_6806" else P.WRIST_BRG_OD
    w = P.BRG_W if stub == "bearing_6806" else P.WRIST_BRG_W
    bshp, _ = part(stub, centre=False)
    n = 0
    for k, (mid, d) in enumerate(pockets(stem, od)):
        Rb = R @ _z_to(d)
        tt = t + R @ (mid + pre)
        if any(np.linalg.norm(tt - s0) < 1.0 for s0 in assy._seats):
            continue                       # this hole already has a bearing
        assy._seats.append(tt)
        assy.add(bshp, name=f"{stub}_{tag}_{k + 1}",
                 loc=loc(Rb, tt, (0.0, 0.0, -w / 2.0)), color=COL["brg"])
        n += 1
    return n


if __name__ == "__main__":
    poses = [("home", (0, 0, 0, 0, 0, 0), 0.0),
             ("working", (0.35, -0.55, 0.95, 0.0, -0.40, 0.0), 0.0),
             ("exploded", (0, 0, 0, 0, 0, 0), 6.0)]
    for name, q, ex in poses:
        assy, tcp = build_step(q, explode=ex)
        out = os.path.join(CAD, f"arm450_assembly_{name}.step")
        assy.save(out)
        n = len(list(assy.traverse())) - 1
        print(f"  wrote {os.path.basename(out)}   {n} components   "
              f"TCP ({tcp[0]:.1f}, {tcp[1]:.1f}, {tcp[2]:.1f})")
