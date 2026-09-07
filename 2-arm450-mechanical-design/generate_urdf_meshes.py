"""
Extract a URDF from the CAD — real meshes, real inertias.

generate_urdf.py builds a URDF from the same PARAMETERS as the CAD (link lengths
and joint origins, tied by assertions). But its visual/collision geometry was
primitive boxes and its inertias were estimates. That is a parameter link, not
an extraction.

This builds each URDF link by combining the actual exported STLs at their true
placement, then computes mass and the full inertia tensor from that geometry.
"""
import os, json, numpy as np, trimesh
import generate_urdf as G

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "output", "cad")
MESH = os.path.join(HERE, "meshes")
# Exact solid volumes from the STEP B-reps. trimesh reports the tessellated
# link shells as non-watertight, so summing mesh .volume silently DROPPED them
# and under-reported link2/link3 mass by more than half.
VOL = json.load(open(os.path.join(CAD, "volumes.json")))
os.makedirs(MESH, exist_ok=True)

RHO_PLA_CF = 1290.0      # kg/m3 solid
FILL = 0.55              # effective solid fraction at ~6 perimeters + 15 % infill
SERVO_KG = 0.060

MM = 1e-3
SEC_W = 29.0


def rot(axis, a):
    ax = np.array(axis, float); ax /= np.linalg.norm(ax)
    K = np.array([[0,-ax[2],ax[1]],[ax[2],0,-ax[0]],[-ax[1],ax[0],0]])
    return np.eye(3) + np.sin(a)*K + (1-np.cos(a))*K@K


M2C = np.array([[0.,1.,0.],[0.,0.,1.],[1.,0.,0.]])   # link mesh -> chain frame


def load(n, centre=False):
    m = trimesh.load(os.path.join(CAD, n), force="mesh")
    if centre:
        m.apply_translation(-m.bounds.mean(axis=0))
    return m


def place(m, R=np.eye(3), t=(0,0,0)):
    m = m.copy(); T = np.eye(4); T[:3,:3] = R; T[:3,3] = t
    m.apply_transform(T); return m


def link_shell_pair(length):
    """Both halves of one link, in the link's own frame (origin at its joint)."""
    out = []
    for n, flip, dy in (("link_half_groove.stl", False, -SEC_W/4),
                        ("link_half_tongue.stl", True, +SEC_W/4)):
        h = load(n, centre=True)
        R = M2C @ (rot([1,0,0], np.pi) if flip else np.eye(3))
        out.append(place(h, R, (0, dy, length/2)))
    for n in ("joint_shaft.stl", "shaft_clamp.stl"):
        out.append(place(load(n, centre=True), rot([1,0,0], np.pi/2), (0,0,0)))
    out.append(place(load("servo_collar.stl", centre=True), np.eye(3), (0, 44, 6)))
    return out


# which exported solids make up each URDF link (for the exact volume lookup)
PART_FILES = {
    "base_link": ["base"],
    "link1":     ["turret_j1"],
    "link2":     ["link_half_groove", "link_half_tongue", "joint_shaft",
                  "shaft_clamp", "servo_collar"],
    "link3":     ["link_half_groove", "link_half_tongue", "joint_shaft",
                  "shaft_clamp", "servo_collar"],
    "link4":     ["wrist_j4_housing"],
    "link5":     ["wrist_j5_yoke"],
    "link6":     ["wrist_j6_output"],
}

LINKS = {
    "base_link": [("base.stl", np.eye(3), (0,0,0), False)],
    "link1":     [("turret_j1.stl", np.eye(3), (0,0,-14.0), False)],
    "link2":     None,     # built by link_shell_pair
    "link3":     None,
    "link4":     [("wrist_j4_housing.stl", np.eye(3), (0,0,32.0), False)],
    "link5":     [("wrist_j5_yoke.stl", np.eye(3), (0,0,0), False)],
    "link6":     [("wrist_j6_output.stl", np.eye(3), (0,0,0), False)],
}
SERVOS = {"link1":1, "link2":1, "link3":1, "link4":1, "link5":1, "link6":1}


def build_link(name):
    """Return (mesh path, mass kg, inertia 3x3 about the link origin, mesh).

    Volume is summed over the INDIVIDUAL watertight parts -- concatenating them
    gives a multi-body mesh whose .volume is meaningless (it came back NaN).
    Inertia uses trimesh's unit-density tensor scaled by the real density, then
    shifted to the link origin by the parallel-axis theorem.
    """
    if name in ("link2", "link3"):
        parts = link_shell_pair(G.L2 if name == "link2" else G.L4_SPLIT)
    else:
        parts = [place(load(f, centre=c), R, t) for f, R, t, c in LINKS[name]]

    vol_mm3 = sum(VOL[n] for n in PART_FILES[name])
    m = trimesh.util.concatenate(parts)
    out = os.path.join(MESH, f"{name}.stl")
    m.export(out)

    mass = vol_mm3 * 1e-9 * RHO_PLA_CF * FILL + SERVOS.get(name, 0) * SERVO_KG
    rho_eff = (mass / (vol_mm3 * 1e-9)) if vol_mm3 > 0 else RHO_PLA_CF

    I = np.zeros((3, 3))
    for p in parts:
        if not (p.is_watertight and p.volume > 0):
            continue
        mp = p.volume * 1e-9 * rho_eff
        # trimesh returns the unit-density tensor in mm^5. Converting to kg.m^2
        # is x 1e-15 (mm^5 -> m^5) times the real density in kg/m^3.
        # I first used 1e-12, which made every inertia 1000x too large.
        Ip = np.asarray(p.moment_inertia) * 1e-15 * rho_eff         # kg.m^2 about its CoM
        c = p.center_mass * MM                                     # m
        I += Ip + mp * ((c @ c) * np.eye(3) - np.outer(c, c))      # parallel axis
    return out, mass, I, m


# ---------------------------------------------------------------------------
# THE FITTED TOOL
#
# The URDF had SEVEN links and no tool on any of them. Every RViz run so far
# has shown a bare J6 face, even though the sine path had been re-verified
# collision-free WITH a gripper fitted and the workspace recomputed for it.
# The tool existed in assemble.py -- the CAD/collision assembly -- and nowhere
# in the model RViz actually loads.
#
# Built the same way as every other link here: take the real STLs at their true
# placement and combine them into one mesh, in link6's frame.
TOOL_FILLS = {"tool_adapter": 0.90, "tool_gripper": 0.90,
              "gripper_jaw": 1.00, "gripper_pinion": 1.00,
              "tool_dock": 0.90}
SG90_KG = 0.009
# how far past the J6 TOOL FACE each tool works. Measured, not typed:
# workspace.TOOL_REACH derives the same numbers off assemble.build().
TOOL_TIP = {"gripper": 42.0, "dock": 36.0}


def build_tool(tool="gripper"):
    """Return (mesh path, mass kg, inertia about the LINK6 origin, mesh).

    Placement is taken from assemble.build() rather than re-derived, so the
    thing RViz draws is the same geometry the collision check cleared. At q = 0
    every joint rotation is identity, so the world placement differs from the
    link6 frame by a pure translation.
    """
    import assemble as A
    parts, tcp = A.build(0, 0, 0, 0, 0, 0, tool=tool)
    origin6 = np.asarray(tcp) - np.array([0.0, 0.0, G.L_TCP])   # link6 in world
    got = [m for m, c in parts if c is A.C_TOOL]
    if not got:
        raise RuntimeError(f"assemble.build(tool={tool!r}) placed no tool bodies")
    got = [place(m, np.eye(3), -origin6) for m in got]
    m = trimesh.util.concatenate(got)
    out = os.path.join(MESH, f"tool_{tool}.stl")
    m.export(out)

    # mass from the exact STEP volumes at the fill each part is PRINTED at --
    # the jaw racks and pinion go at 100 %, not MASS_FILL, because their teeth
    # are 2 mm and sparse infill leaves them hollow
    qty = {"gripper": {"tool_adapter": 1, "tool_gripper": 1,
                       "gripper_jaw": 2, "gripper_pinion": 1},
           "dock": {"tool_adapter": 1, "tool_dock": 1}}[tool]
    mass = sum(VOL[k] * 1e-9 * RHO_PLA_CF * TOOL_FILLS[k] * q
               for k, q in qty.items())
    if tool == "gripper":
        mass += SG90_KG
    vol_mm3 = sum(VOL[k] * q for k, q in qty.items())
    rho_eff = mass / (vol_mm3 * 1e-9)

    I = np.zeros((3, 3))
    for pmesh in got:
        if not (pmesh.is_watertight and pmesh.volume > 0):
            continue
        mp = pmesh.volume * 1e-9 * rho_eff
        Ip = np.asarray(pmesh.moment_inertia) * 1e-15 * rho_eff
        c = pmesh.center_mass * MM
        I += Ip + mp * ((c @ c) * np.eye(3) - np.outer(c, c))
    return out, mass, I, m


if __name__ == "__main__":
    print("EXTRACTING URDF GEOMETRY FROM THE CAD\n")
    print(f"  {'link':11s} {'mesh faces':>11s} {'mass kg':>9s}   inertia about the link origin (kg.m2)")
    print("  " + "-"*88)
    tot = 0.0
    for name in ("base_link","link1","link2","link3","link4","link5","link6"):
        f, mass, I, m = build_link(name)
        tot += mass
        print(f"  {name:11s} {len(m.faces):11d} {mass:9.3f}   "
              f"Ixx {I[0,0]:.6f}  Iyy {I[1,1]:.6f}  Izz {I[2,2]:.6f}")
    print(f"\n  TOTAL MASS {tot:.3f} kg")
    print(f"\n  meshes written to {MESH}/")
    print(f"  vs the 1.2 kg budget: {'OK' if tot<=1.2 else 'OVER'}")


# ---------------------------------------------------------------------------
def emit_urdf(path="arm450_meshes.urdf", tool="gripper"):
    """Emit the mesh URDF.

    NOTE the package name in the mesh references: `arm450_description`, NOT
    `arm450_design`. arm450_design is this design directory -- it is not a ROS
    package and package:// cannot resolve it. Getting that wrong makes every
    mesh fail to load, and RViz falls back to something that looks nothing like
    the arm, with no error obvious in the viewer.
    """
    import generate_urdf as GU
    # The meshes are PRINTED PARTS ONLY. Servos, bearings, shafts and horn
    # adapters are roughly half the arm and none of them appears in a mesh, so
    # an inertial taken straight from the geometry is ~40 % light. GU.M carries
    # the all-in per-link mass derived from volumes.json; the difference is
    # added here as a lumped mass AT THE LINK ORIGIN.
    #
    # Lumping at the origin is deliberate and worth stating: the servo body,
    # the bearing pair and the shaft all sit on or very near the joint axis, so
    # their contribution to inertia ABOUT THAT AXIS is small. This gets total
    # mass and gravity torque right and slightly UNDERSTATES rotational inertia.
    # Do not tune high-bandwidth control against it without re-deriving.
    N2U = {'base_link': 'base', 'link1': 'link1', 'link2': 'link2',
           'link3': 'link3', 'link4': 'link4', 'link5': 'link5',
           'link6': 'link6'}
    data = {}
    print()
    print(f"  {'link':10s} {'mesh kg':>9s} {'non-printed':>12s} {'total kg':>9s}")
    print('  ' + '-' * 46)
    for n in ('base_link', 'link1', 'link2', 'link3', 'link4', 'link5', 'link6'):
        f, mass, I, m = build_link(n)
        extra = max(0.0, GU.M[N2U[n]] - mass)
        data[n] = (os.path.relpath(f, HERE), mass + extra, I)
        print(f'  {n:10s} {mass:9.4f} {extra:12.4f} {mass+extra:9.4f}')

    J = [("joint1", "base_link", "link1", GU.BASE_H, "0 0 1", GU.RANGE["joint1"], GU.LIMIT),
         ("joint2", "link1", "link2", GU.SHOULDER_RISE, "0 1 0", GU.RANGE["joint2"], GU.LIMIT_J2),
         ("joint3", "link2", "link3", GU.L2, "0 1 0", GU.RANGE["joint3"], GU.LIMIT),
         ("joint4", "link3", "link4", GU.L4_SPLIT, "0 0 1", GU.RANGE["joint4"], GU.LIMIT),
         ("joint5", "link4", "link5", GU.L5_SPLIT, "0 1 0", GU.RANGE["joint5"], GU.LIMIT),
         ("joint6", "link5", "link6", GU.L6_SPLIT, "0 0 1", GU.RANGE["joint6"], GU.LIMIT)]

    P = ['<?xml version="1.0"?>',
         '<!-- ARM-450 — geometry and inertia EXTRACTED from the CAD.',
         '     Meshes are the exported solids; inertias are computed from them. -->',
         '<robot name="arm450">',
         '  <material name="shell"><color rgba="0.66 0.71 0.77 1"/></material>',
         '  <material name="tool"><color rgba="0.30 0.32 0.36 1"/></material>',
         '  <link name="world"/>',
         '  <joint name="world_to_base" type="fixed">',
         '    <parent link="world"/><child link="base_link"/>',
         '    <origin rpy="0 0 0" xyz="0 0 0"/>', '  </joint>']

    def link_xml(n):
        rel, mass, I = data[n]
        return f'''  <link name="{n}">
    <inertial>
      <origin rpy="0 0 0" xyz="0 0 0"/>
      <mass value="{mass:.5f}"/>
      <inertia ixx="{I[0,0]:.9f}" ixy="{I[0,1]:.9f}" ixz="{I[0,2]:.9f}"
               iyy="{I[1,1]:.9f}" iyz="{I[1,2]:.9f}" izz="{I[2,2]:.9f}"/>
    </inertial>
    <visual>
      <origin rpy="0 0 0" xyz="0 0 0"/>
      <geometry><mesh filename="package://arm450_description/{rel}" scale="0.001 0.001 0.001"/></geometry>
      <material name="shell"/>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 0"/>
      <geometry><mesh filename="package://arm450_description/{rel}" scale="0.001 0.001 0.001"/></geometry>
    </collision>
  </link>'''

    P.append(link_xml("base_link"))
    for name, par, ch, z, ax, rng, lim in J:
        P.append(f'''  <joint name="{name}" type="revolute">
    <parent link="{par}"/><child link="{ch}"/>
    <origin rpy="0 0 0" xyz="0 0 {z*MM:.6f}"/>
    <axis xyz="{ax}"/>
    <limit effort="{lim['effort']}" velocity="{lim['velocity']}"
           lower="{np.radians(rng[0]):.6f}" upper="{np.radians(rng[1]):.6f}"/>
  </joint>''')
        P.append(link_xml(ch))
    P.append(f'''  <joint name="link6_to_tcp" type="fixed">
    <parent link="link6"/><child link="tcp"/>
    <origin rpy="0 0 0" xyz="0 0 {GU.L_TCP*MM:.6f}"/>
  </joint>
  <link name="tcp"/>''')

    # the fitted tool, as a fixed link on link6
    if tool:
        tf, tmass, tI, _tm = build_tool(tool)
        trel = os.path.relpath(tf, HERE)
        data["tool"] = (trel, tmass, tI)
        P.append(f'''  <joint name="link6_to_tool" type="fixed">
    <parent link="link6"/><child link="tool"/>
    <origin rpy="0 0 0" xyz="0 0 0"/>
  </joint>
  <link name="tool">
    <inertial>
      <origin rpy="0 0 0" xyz="0 0 0"/>
      <mass value="{tmass:.5f}"/>
      <inertia ixx="{tI[0,0]:.9f}" ixy="{tI[0,1]:.9f}" ixz="{tI[0,2]:.9f}"
               iyy="{tI[1,1]:.9f}" iyz="{tI[1,2]:.9f}" izz="{tI[2,2]:.9f}"/>
    </inertial>
    <visual>
      <origin rpy="0 0 0" xyz="0 0 0"/>
      <geometry><mesh filename="package://arm450_description/{trel}" scale="0.001 0.001 0.001"/></geometry>
      <material name="tool"/>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 0"/>
      <geometry><mesh filename="package://arm450_description/{trel}" scale="0.001 0.001 0.001"/></geometry>
    </collision>
  </link>
  <joint name="tool_to_tip" type="fixed">
    <parent link="tool"/><child link="tool_tip"/>
    <origin rpy="0 0 0" xyz="0 0 {(GU.L_TCP + TOOL_TIP[tool])*MM:.6f}"/>
  </joint>
  <link name="tool_tip"/>''')
    P.append('</robot>')
    open(os.path.join(HERE, path), "w").write("\n".join(P) + "\n")
    tot = sum(v[1] for v in data.values())
    print(f"\n  wrote {path}  —  {len(data)} links, total {tot:.3f} kg")
    return path


if os.environ.get("EMIT"):
    # TOOL=gripper (default) | dock | none
    #   EMIT=1 TOOL=dock python3 generate_urdf_meshes.py
    _t = os.environ.get("TOOL", "gripper")
    emit_urdf(tool=None if _t in ("", "none") else _t)
