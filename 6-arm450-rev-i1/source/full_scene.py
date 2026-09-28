#!/usr/bin/env python3
"""The complete rev-I arm in WORLD coordinates: every printed part, every
bought part we model (6 x ST3215), placed exactly as the generators and the
released assembly define. Used by the whole-arm motion sweep."""
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import asm_meshes as AM          # noqa: E402
import asm_xforms as AX          # noqa: E402
import verify_drive as VD        # noqa: E402
import verify_j1 as V1           # noqa: E402
from verify_j4 import servo_up   # noqa: E402
import gen_drive_j4 as J4        # noqa: E402
import gen_wrist as W            # noqa: E402

FORK_R = np.array([[0., 1., 0.], [0., 0., 1.], [1., 0., 0.]])


def M(R=np.eye(3), t=(0, 0, 0)):
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t; return T


J3W = M(FORK_R, (0, 0, 209.0))
J5W = M(FORK_R, (0, 0, W.Z_J5_WORLD))
TURW = M(t=(0, 0, 50.0))
J2J = trimesh.transformations.rotation_matrix(np.radians(90), [1, 0, 0])   # J2 joint -> turret
J2J[2, 3] = 40.0
ABC2J5 = trimesh.transformations.rotation_matrix(np.radians(120), [1, 1, 1])


def ld(nm, T=None):
    m = trimesh.load(os.path.join(HERE, nm + ".stl"))
    if T is not None:
        m.apply_transform(T)
    return m


def scene():
    rel = AM.load()
    X = AX.xforms()
    s = {}
    for k in ("shaft_clamp_1", "shaft_clamp_2", "shaft_clamp_3", "shaft_clamp_4"):
        s[k] = rel[k]
    # the released upper GROOVE: its own STL (0.3 mm finer than the assembly
    # STEP's 0.4 mm-deflection tessellation, which read the 0.025 ring fit as a
    # 0.15 mm clash) + its exact BRep for containment
    s["link_upper_groove"] = trimesh.load(os.path.join(AM.REL_DIR, "link_upper_groove.stl"))
    s["link_upper_groove"].apply_transform(X["link_upper_groove"])
    VD.attach_occ(s["link_upper_groove"], os.path.join(AM.REL_DIR, "link_upper_groove.step"), X["link_upper_groove"])
    s["link_upper_tongue"] = ld("link_upper_tongue", X["link_upper_tongue"])   # rev I: flush heads
    s["base"] = ld("base")          # rev I: lower 6806 pocket opens from underneath
    # the released upper tongue's mesh is non-manifold in every export; its
    # STEP is valid, so checks use the exact solid (verify_drive.contains)
    import cadquery as cq
    from OCP.gp import gp_Trsf
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    T = X["link_upper_tongue"]
    tr = gp_Trsf(); tr.SetValues(*[float(T[i, j]) for i in range(3) for j in range(4)])
    sh = cq.importers.importStep(os.path.join(HERE, "link_upper_tongue.step")).val().wrapped
    s["link_upper_tongue"].occ = BRepBuilderAPI_Transform(sh, tr, True).Shape()
    s["spigot_collar"] = ld("spigot_collar")
    s["j1_mount"] = ld("j1_mount"); s["j1_hub"] = ld("j1_hub")
    s["J2_turret_p1"] = ld("J2_turret_p1", TURW); s["J2_turret_p2"] = ld("J2_turret_p2", TURW)
    s["J2_shaft"] = ld("J2_shaft", TURW)
    s["J3_p1"] = ld("J3_p1", J3W); s["J3_p2"] = ld("J3_p2", J3W); s["J3_shaft"] = ld("J3_shaft", J3W)
    for k in ("link_fore_tongue", "link_fore_groove"):
        s[k] = ld(k, X[k])
        VD.attach_occ(s[k], os.path.join(HERE, k + ".step"), X[k])   # exact, memory-safe
    for k in ("j4_base", "j4_cap", "j4_hub"):
        s[k] = ld(k)
    for k in ("J5_p1", "J5_p2", "J5_shaft", "j6_body", "j6_cap", "j6_flange"):
        s[k] = ld(k, J5W)
    s["J5_spacer_A"] = ld("J5_spacer", J5W)
    b = ld("J5_spacer"); b.apply_translation([0, 0, -(2 * W.BLADE_HALF + W.SPACER_T)])
    b.apply_transform(J5W); s["J5_spacer_B"] = b
    # gravity-spring collars (clamped on the upper link and the forearm)
    import spring_parts as SP
    import cadquery as cq
    for nm, sy, zc in (("collar_upper_+y", 1, SP.J2_AXIS_Z + SP.B2), ("collar_upper_-y", -1, SP.J2_AXIS_Z + SP.B2),
                       ("collar_fore_+y", 1, SP.J3_AXIS_Z + SP.B3), ("collar_fore_-y", -1, SP.J3_AXIS_Z + SP.B3)):
        tmp = os.path.join(HERE, "_" + nm.replace("+", "p").replace("-", "m") + ".stl")
        cq.exporters.export(SP.collar_half(sy, zc), tmp, tolerance=0.02, angularTolerance=0.2)
        s[nm] = trimesh.load(tmp)
    # the six servos
    s["servo_J1"] = V1.servo_world()
    v = VD.seated_servo(28.5); v.apply_transform(J2J); v.apply_transform(TURW); s["servo_J2"] = v
    v = VD.seated_servo(28.5); v.apply_transform(J3W); s["servo_J3"] = v
    s["servo_J4"] = servo_up(J4.Z_CAP)
    v = VD.seated_servo(W.P5); v.apply_transform(J5W); s["servo_J5"] = v
    v = servo_up(W.X6_CAP); v.apply_transform(ABC2J5); v.apply_transform(J5W); s["servo_J6"] = v
    return s


ABOVE_J1 = ["J2_turret_p1", "J2_turret_p2", "servo_J2", "j1_hub"]
ABOVE_J2 = ["J2_shaft", "shaft_clamp_1", "shaft_clamp_2", "link_upper_groove", "link_upper_tongue",
            "J3_p1", "J3_p2", "servo_J3", "collar_upper_+y", "collar_upper_-y"]
ABOVE_J3 = ["J3_shaft", "shaft_clamp_3", "shaft_clamp_4", "link_fore_tongue", "link_fore_groove",
            "j4_base", "j4_cap", "servo_J4", "collar_fore_+y", "collar_fore_-y"]
ABOVE_J4 = ["j4_hub", "J5_p1", "J5_p2", "servo_J5"]
ABOVE_J5 = ["J5_shaft", "J5_spacer_A", "J5_spacer_B", "j6_body", "j6_cap", "servo_J6"]
ABOVE_J6 = ["j6_flange"]

JOINTS = [  # name, point, axis, half travel, moving set
    ("J1 yaw", (0, 0, 0), (0, 0, 1), 90, ABOVE_J1 + ABOVE_J2 + ABOVE_J3 + ABOVE_J4 + ABOVE_J5 + ABOVE_J6),
    ("J2 shoulder", (0, 0, 90.0), (0, 1, 0), 54, ABOVE_J2 + ABOVE_J3 + ABOVE_J4 + ABOVE_J5 + ABOVE_J6),
    ("J3 elbow", (0, 0, 209.0), (0, 1, 0), 72, ABOVE_J3 + ABOVE_J4 + ABOVE_J5 + ABOVE_J6),
    ("J4 roll", (0, 0, 0), (0, 0, 1), 90, ABOVE_J4 + ABOVE_J5 + ABOVE_J6),
    ("J5 pitch", (0, 0, W.Z_J5_WORLD), (0, 1, 0), 46.5, ABOVE_J5 + ABOVE_J6),
    ("J6 roll", (0, 0, 0), (0, 0, 1), 90, ABOVE_J6),
]
