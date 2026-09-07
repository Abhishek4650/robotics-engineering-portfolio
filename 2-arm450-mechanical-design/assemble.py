"""
ARM-450 — full assembly, built from the real CAD at true mating positions.

Every part is placed by its MATING FACE, not approximately:
  * the two link halves meet at the seam plane, tongue into groove
  * the shaft sits on the joint axis, through both bearings
  * the clamp sits in the Ø38 through-bore between the bearings
  * the wrist mounts on the same Ø42 bearing interface as every joint
  * the base's turret seat sits on the J1 axis

Chain (matches arm450.urdf exactly):
  base 50 | shoulder rise 40 | L2 145 | L3 145 | wrist->TCP 70  =  450 mm
"""

import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "output", "cad")
INK, STEEL = "#1b2733", "#6b7f95"

BASE_H, SHOULDER = 50.0, 40.0
L2 = L3 = 119.0
J4_J5, J5_J6, J6_TCP = 62.0, 30.0, 30.0
SEC_W = 29.0                      # link width = seam-to-seam
HALF_D = SEC_W / 2.0

# material palette — restrained, reads as a real machine
C_SHELL = (0.66, 0.71, 0.77)      # printed structural shell
C_JOINT = (0.28, 0.55, 0.62)      # joint housings / turret
C_SERVO = (0.72, 0.36, 0.28)      # servo + collar
C_STEEL = (0.55, 0.57, 0.61)      # shaft, bearings
C_BASE = (0.48, 0.51, 0.55)
C_TOOL = (0.30, 0.32, 0.36)


_CACHE = {}


def load(n, centre=True):
    """Cached. build() is called hundreds of times in a sweep, and re-reading
    every STL from disk each time dominated the runtime."""
    k = (n, centre)
    if k not in _CACHE:
        m = trimesh.load(os.path.join(CAD, n), force="mesh")
        if centre:
            m.apply_translation(-m.bounds.mean(axis=0))
        _CACHE[k] = m
    return _CACHE[k].copy()


def rot(axis, a):
    ax = np.array(axis, float); ax /= np.linalg.norm(ax)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def place(mesh, R=np.eye(3), t=(0, 0, 0)):
    m = mesh.copy()
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t
    m.apply_transform(T)
    return m


# The shells are modelled with:  X = link length,  Z = split normal (seam).
# The assembly needs:             length -> chain +Z,  split normal -> joint axis +Y.
# roty(-90) alone maps X->Z but sends the split normal to -X, which laid the two
# halves down edge-on instead of stacking them across the joint axis.
# Build the mapping explicitly instead (columns = images of x, y, z):
MESH2CHAIN = np.array([[0.0, 1.0, 0.0],
                       [0.0, 0.0, 1.0],
                       [1.0, 0.0, 0.0]])


def link_assembly(tongue, groove, shaft, clamp, origin, R, length, explode=0.0):
    """One complete link: two halves mated at the seam, shaft + clamp on axis."""
    out = []
    # halves: groove open-face +Z_local, tongue flipped to close onto it.
    # local frame has the link running along +Z after MESH2CHAIN.
    RL = R @ MESH2CHAIN
    for half, flip, dy in ((groove, False, -HALF_D / 2.0),
                           (tongue, True, +HALF_D / 2.0)):
        # flip the tongue half about the chain axis so its open face turns to meet
        # the groove half; they then mate at the seam plane y = 0.
        Rh = RL @ (rot([1, 0, 0], np.pi) if flip else np.eye(3))
        off = R @ np.array([0, dy + np.sign(dy) * explode, length / 2.0])
        out.append((place(half, R=Rh, t=origin + off), C_SHELL))
    # shaft on the joint axis at the inboard end
    out.append((place(shaft, R=R @ rot([1, 0, 0], np.pi / 2),
                      t=origin + R @ np.array([0, explode * 2.2, 0])), C_STEEL))
    out.append((place(clamp, R=R @ rot([1, 0, 0], np.pi / 2),
                      t=origin + R @ np.array([0, -explode * 1.4, 0])), C_JOINT))
    return out


C_TUBE = (0.85, 0.35, 0.30)      # the fluid line, when it is fitted


def build(q1=0.0, q2=0.0, q3=0.0, q4=0.0, q5=0.0, q6=0.0, explode=0.0,
          tool="pen", plumbing=None):
    """`plumbing` = None | "external" | "internal".

    Until 2026-08-23 there was no way to put the fluid line in the assembly, so
    every collision result in this project is for a bare arm. That is fine for
    a bare arm and wrong the moment a tube is proposed: this path clears the
    base pedestal by about 1 mm and the tube is 6 mm across."""
    # all six axes, matching arm450.urdf:
    #   J1 yaw(Z) | J2 pitch(Y) | J3 pitch(Y) | J4 roll(Z) | J5 pitch(Y) | J6 roll(Z)
    turret = load("turret_j1.stl", centre=False)
    j4h = load("wrist_j4_housing.stl", centre=False)
    yoke5 = load("wrist_j5_yoke.stl", centre=False)
    j6out = load("wrist_j6_output.stl", centre=False)
    tongue = load("link_half_tongue.stl")
    groove = load("link_half_groove.stl")
    shaft = load("joint_shaft.stl")
    clamp = load("shaft_clamp.stl")
    collar = load("servo_collar.stl")
    base = load("base.stl", centre=False)
    wrist = load("wrist.stl", centre=False)
    flange = load("tool_flange.stl")

    P = []
    # --- base: sits on the ground, top face at z = BASE_H --------------------
    b = base.copy(); b.apply_translation(-b.bounds[0] * np.array([0, 0, 1]))
    b.apply_translation([-b.bounds.mean(axis=0)[0], -b.bounds.mean(axis=0)[1], 0])
    P.append((b, C_BASE))

    # --- J1 base yaw: the turret rotates about Z ----------------------------
    R1 = rot([0, 0, 1], q1)
    tu = turret.copy(); tu.apply_translation([0, 0, -tu.bounds[0][2] - 14.0])
    P.append((place(tu, R=R1, t=(0, 0, BASE_H + explode * 0.6)), C_JOINT))

    j2 = np.array([0.0, 0.0, BASE_H + SHOULDER])

    R2 = R1 @ rot([0, 1, 0], q2)
    P += link_assembly(tongue, groove, shaft, clamp, j2, R2, L2, explode)
    P.append((place(collar, R=R2, t=j2 + R2 @ np.array([0, 44 + explode * 2, 6])), C_SERVO))

    # --- J3 elbow, then the forearm splits at the J4 roll module ------------
    j3 = j2 + R2 @ np.array([0, 0, L2])
    R3 = R2 @ rot([0, 1, 0], q3)
    P += link_assembly(tongue, groove, shaft, clamp, j3, R3, L3, explode)
    P.append((place(collar, R=R3, t=j3 + R3 @ np.array([0, 44 + explode * 2, 6])), C_SERVO))

    # --- J4 forearm roll: everything outboard spins about the link axis -----
    j4 = j3 + R3 @ np.array([0, 0, L3])      # J4 now at the forearm END
    R4 = R3 @ rot([0, 0, 1], q4)
    # J4 roll module sits BEHIND its own axis, inside the end of the forearm.
    # Extending it forward put it in the same 34 mm as the J6 module (they
    # collided in 99 % of sampled poses).
    hh = j4h.copy(); hh.apply_translation([0, 0, -hh.bounds[0][2]])
    P.append((place(hh, R=R4, t=j4 + R4 @ np.array([0, 0, 32.0 + explode * 1.2])), C_JOINT))

    j5 = j4 + R4 @ np.array([0, 0, J4_J5])
    # --- J5 wrist pitch -----------------------------------------------------
    yk = yoke5.copy(); yk.apply_translation([0, 0, -yk.bounds[0][2]])
    P.append((place(yk, R=R4, t=j4 + R4 @ np.array([0, 0, J4_J5 - 12.0 + explode * 1.4])), C_SHELL))
    R5 = R4 @ rot([0, 1, 0], q5)
    # wrist: its Ø42 bore centre sits 12 mm from the part origin along +X
    # --- J6 tool roll: a second roll_module, then the flange and tool -------
    R6 = R5 @ rot([0, 0, 1], q6)
    oo = j6out.copy(); oo.apply_translation([0, 0, -oo.bounds[0][2]])
    P.append((place(oo, R=R6, t=j5 + R6 @ np.array([0, 0, J5_J6 + explode * 1.8])), C_JOINT))
    tcp = j5 + R5 @ np.array([0, 0, J5_J6 + J6_TCP])
    # flange is now integral to wrist_j6_output
    # --- the fitted tool ----------------------------------------------------
    # Was a bare Ø12 x 30 cylinder standing in for "some tool". That is fine for
    # kinematics and useless for collision: the real quick-change adapter plus a
    # gripper reaches 31 mm beyond the J6 face and is 48 mm across, so a path
    # solved against the placeholder is not automatically valid with a tool on.
    if tool in ("gripper", "dock"):
        ad = load("tool_adapter.stl")
        ad.apply_translation([0, 0, 6.0])          # spigot tip to plate bottom
        P.append((place(ad, R=R6, t=tcp + R6 @ np.array([0, 0, explode * 3.0])),
                  C_TOOL))
        tm = load("tool_gripper.stl" if tool == "gripper" else "tool_dock.stl")
        # the tool's SOCKET is in its top face, so it mounts flipped: rotate 180
        # about X and land that face on the adapter plate.
        tm.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
        tm.apply_translation([0, 0, -tm.bounds[0][2]])
        P.append((place(tm, R=R6,
                        t=tcp + R6 @ np.array([0, 0, 5.0 + explode * 4.0])), C_TOOL))
        if tool == "gripper":
            jw = load("gripper_jaw.stl")
            for sy in (-1, 1):
                j = jw.copy()
                if sy < 0:
                    j.apply_transform(trimesh.transformations.rotation_matrix(
                        np.pi, [0, 0, 1]))
                j.apply_translation([0, sy * 12.8, 0])
                j.apply_translation([0, 0, -j.bounds[0][2] + 5.0 + 3.0])
                P.append((place(j, R=R6, t=tcp + R6 @ np.array(
                    [0, 0, explode * 4.5])), C_TOOL))
    else:
        ph = trimesh.creation.cylinder(radius=6, height=30)
        P.append((place(ph, R=R6,
                        t=tcp + R6 @ np.array([0, 0, 15 + explode * 3.5])), C_TOOL))

    if plumbing:
        import plumbing as PL
        import interference as _I
        frames = [(np.array([0.0, 0.0, BASE_H * 0.5]), np.eye(3)),
                  (np.array([0.0, 0.0, BASE_H]), R1),
                  (j2, R2), (j3, R3), (j4, R4), (j5, R5), (tcp, R6)]
        want = ("tube", "cable") if plumbing == "both" else (plumbing,)
        for svc in want:
            od = PL.TUBE_OD if svc == "tube" else PL.CABLE_OD
            lat = 0.0 if svc == "tube" else PL.CABLE_LAT
            for m, ch, nm in PL.route(frames, od=od, lateral=lat):
                _I.register_service(len(P), ch, f"{svc}:{nm}")
                P.append((m, C_TUBE))
    return P, tcp


# ---------------------------------------------------------------------------
def view(az, el):
    a, e = np.radians(az), np.radians(el)
    ca, sa, ce, se = np.cos(a), np.sin(a), np.cos(e), np.sin(e)
    r = np.array([ca, -sa, 0.]); u = np.array([sa * se, ca * se, ce])
    return np.vstack([r, u, np.cross(r, u)])


KEY = np.array([0.35, 0.35, 0.87]);  KEY /= np.linalg.norm(KEY)
FILL = np.array([-0.6, 0.2, 0.4]);   FILL /= np.linalg.norm(FILL)


def render(ax, parts, az, el, centre=None, scale=None):
    R = view(az, el)
    T, C, Z = [], [], []
    for m, base in parts:
        V = (m.vertices - centre) @ R.T
        tri = V[m.faces]
        n = m.face_normals @ R.T
        vis = n[:, 2] > 0
        if vis.sum() == 0:
            continue
        nv = n[vis]
        # two-light shading + ambient: reads as a rendered part, not flat
        lam = np.clip(nv @ KEY, 0, 1) * 0.62 + np.clip(nv @ FILL, 0, 1) * 0.22 + 0.30
        spec = np.clip(nv[:, 2], 0, 1) ** 14 * 0.28
        col = np.array(base)[None, :] * lam[:, None] + spec[:, None]
        T.append(tri[vis][:, :, :2]); C.append(col); Z.append(tri[vis][:, :, 2].mean(1))
    T = np.concatenate(T); C = np.clip(np.concatenate(C), 0, 1)
    o = np.argsort(np.concatenate(Z))
    ax.add_collection(PolyCollection(T[o], facecolors=C[o], edgecolors="none"))
    lim = scale if scale else np.abs(T).max() * 1.05
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
    ax.set_aspect("equal"); ax.axis("off")
    return lim


if __name__ == "__main__":
    fig = plt.figure(figsize=(17.5, 10.4))
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(2, 4, width_ratios=[1.45, 1, 1, 1.25],
                          height_ratios=[1, 1], wspace=0.04, hspace=0.08,
                          left=.02, right=.99, top=.90, bottom=.03)

    POSE = (np.radians(25), np.radians(58), np.radians(-96),
            np.radians(40), np.radians(-38), np.radians(60))
    parts, tcp = build(*POSE)
    allv = np.vstack([m.vertices for m, _ in parts])
    C0 = (allv.min(0) + allv.max(0)) / 2
    S = np.abs(np.vstack([m.vertices for m, _ in parts]) - C0).max() * 1.08

    axh = fig.add_subplot(gs[:, 0])
    render(axh, parts, 34, 20, C0, S)
    axh.set_title("working pose", fontsize=12.5, fontweight="bold", color=INK)

    for k, (az, el, lbl) in enumerate([(0, 0, "front"), (90, 0, "side")]):
        a = fig.add_subplot(gs[0, 1 + k])
        render(a, parts, az, el, C0, S)
        a.set_title(lbl, fontsize=11.5, fontweight="bold", color=INK)

    hp, tcp2 = build()
    ch = (np.vstack([m.vertices for m, _ in hp]).min(0)
          + np.vstack([m.vertices for m, _ in hp]).max(0)) / 2
    a = fig.add_subplot(gs[1, 1])
    render(a, hp, 0, 0, ch, S)
    a.set_title("home — 450 mm", fontsize=11.5, fontweight="bold", color=INK)

    ep, _ = build(q2=np.pi / 2)
    ce = (np.vstack([m.vertices for m, _ in ep]).min(0)
          + np.vstack([m.vertices for m, _ in ep]).max(0)) / 2
    a = fig.add_subplot(gs[1, 2])
    render(a, ep, 0, 0, ce, S)
    a.set_title("extended — 360 mm reach", fontsize=11.5, fontweight="bold", color=INK)

    xp, _ = build(*POSE, explode=13.0)
    cx = (np.vstack([m.vertices for m, _ in xp]).min(0)
          + np.vstack([m.vertices for m, _ in xp]).max(0)) / 2
    a = fig.add_subplot(gs[:, 3])
    render(a, xp, 34, 20, cx, S * 1.18)
    a.set_title("exploded", fontsize=12.5, fontweight="bold", color=INK)

    fig.suptitle("ARM-450   ·   full assembly from the CAD   ·   "
                 "450 mm overall, 360 mm reach, 6-DOF",
                 fontsize=15.5, fontweight="bold", color=INK, x=.02, ha="left", y=.965)
    fig.text(.02, .935, "base · turret J1 · link halves ×4 · joint shafts · shaft clamps · "
             "servo collars · integrated wrist: J4 housing · J5 yoke · J6 output+flange",
             fontsize=10.5, color=STEEL)
    fig.savefig("figures/assembly_pro.png", dpi=185, facecolor="white")
    print("wrote figures/assembly_pro.png")
