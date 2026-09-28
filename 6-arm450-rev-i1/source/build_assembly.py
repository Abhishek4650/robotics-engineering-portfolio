#!/usr/bin/env python3
"""
Rebuild the arm assembly with the rev H parts at their TRUE world placements.

The placements are not invented: they are read out of
`ARM450_FINAL_ASSEMBLY.step` (the 11 Sep release) so every part that did not
change stays exactly where it was, and the five regenerated parts drop into
the same transforms their predecessors occupied.

The forks carry a cyclic rotation, recovered from the release:
    R = [[0,1,0],[0,0,1],[1,0,0]]
i.e. local Z (the joint axis) -> world X
     local X                  -> world Y
     local Y                  -> world Z
J4_module is identity. This matters: a fork verified in its own local frame
says nothing about swing clearance until it is placed.
"""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASM = os.path.join(ROOT, "ARM450_FINAL_ASSEMBLY.step")

# local -> world, read from the release
FORK_R = np.array([[0.0, 1.0, 0.0],
                   [0.0, 0.0, 1.0],
                   [1.0, 0.0, 0.0]])
IDENT = np.eye(3)

# the five parts we regenerated, with the transform their predecessor had
REV_H_PARTS = {
    "J3_p1":     (FORK_R, np.array([0.0, 0.0, 209.0])),
    "J3_p2":     (FORK_R, np.array([0.0, 0.0, 209.0])),
    "J4_module": (IDENT,  np.array([0.0, 0.0, 328.0])),
    "J5_p1":     (FORK_R, np.array([0.0, 0.0, 390.0])),
    "J5_p2":     (FORK_R, np.array([0.0, 0.0, 390.0])),
    # J2 turret: identity, read from the release (translation 0,0,50)
    "J2_turret_p1": (IDENT, np.array([0.0, 0.0, 50.0])),
    "J2_turret_p2": (IDENT, np.array([0.0, 0.0, 50.0])),
}


def placed(name):
    """The rev H part as a mesh, at its world placement."""
    R, t = REV_H_PARTS[name]
    m = trimesh.load(os.path.join(HERE, name + ".stl"))
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = t
    m.apply_transform(M)
    return m


def servo_in_joint_local():
    """ST3215 in a fork's LOCAL frame: output on -Z, horn axis at (0,0),
    mounting face at local z=0. Caller translates to the bay floor."""
    sys.path.insert(0, HERE)
    import servo_geom as SG
    m = trimesh.load(SG.MOTOR_STL)
    m.apply_translation(-m.bounds.mean(axis=0))
    m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2,
                                                              [1, 0, 0]))
    zmin = m.bounds[0][2]
    cx = cy = None
    for dz in (0.3, 0.8, 1.3):
        sl = m.section(plane_origin=[0, 0, zmin + dz], plane_normal=[0, 0, 1])
        if sl is None:
            continue
        v = np.asarray(sl.vertices)
        if abs(np.ptp(v[:, 0]) - SG.HORN_DISC_D) > 0.4:
            continue
        cx = (v[:, 0].max() + v[:, 0].min()) / 2
        cy = (v[:, 1].max() + v[:, 1].min()) / 2
        break
    z_face = None
    for z in np.linspace(zmin, zmin + 8.0, 400):
        sl = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if sl is None:
            continue
        if np.ptp(np.asarray(sl.vertices)[:, 0]) > SG.CASE_L - 0.6:
            z_face = z
            break
    m.apply_translation([-cx, -cy, -z_face])
    return m


def placed_servo(joint, z_floor):
    """The servo seated in `joint`, expressed in WORLD coordinates."""
    R, t = REV_H_PARTS[joint + "_p2"]
    s = servo_in_joint_local()
    s.apply_translation([0, 0, z_floor])
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = t
    s.apply_transform(M)
    return s


if __name__ == "__main__":
    print("rev H parts at their world placements")
    print()
    for nm in REV_H_PARTS:
        m = placed(nm)
        b = m.bounds
        print("  %-11s x %8.2f..%8.2f   y %8.2f..%8.2f   z %8.2f..%8.2f"
              % (nm, b[0][0], b[1][0], b[0][1], b[1][1], b[0][2], b[1][2]))
    print()
    for jn, zf in (("J3", 28.50), ("J5", 25.50)):
        s = placed_servo(jn, zf)
        b = s.bounds
        print("  %s servo   x %8.2f..%8.2f   y %8.2f..%8.2f   z %8.2f..%8.2f"
              % (jn, b[0][0], b[1][0], b[0][1], b[1][1], b[0][2], b[1][2]))
