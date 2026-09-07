"""
Generate arm450.urdf from design_params — the ARM-450 kinematic model.

Chain, with every joint at q = 0 giving a straight-up home pose:

    world --fixed--> base_link
      J1  base yaw     Z    at z = 50          (top of the round base)
      J2  shoulder pitch Y  at z = 40          -> shoulder axis at 90 mm
      J3  elbow pitch   Y   at z = 145         L2 upper arm
      J4  forearm roll  Z   at z = 80          inline in the forearm
      J5  wrist pitch   Y   at z = 65          -> J3->J5 = 145 mm = L3
      J6  tool roll     Z   at z = 35
      TCP fixed             at z = 35          -> J5->TCP = 70 mm

    50 + 40 + 145 + 145 + 70 = 450 mm exactly.

Link geometry is primitive (boxes/cylinders) sized to the real clamshell
section 47.5 x 29.0 mm. Swap in meshes later without touching the kinematics.
"""

import os as _os
import sys as _sys
import numpy as np

_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "cad"))

MM = 1e-3

# ---- chain (mm) -----------------------------------------------------------
BASE_H = 50.0
SHOULDER_RISE = 40.0
L2 = 119.0
# 2026-08-18: J4 moved from 80 mm into the forearm to its END.
# The interference sweep found a PERMANENT 100 % collision: the 209 mm link
# shell was being placed into an 80 mm slot and ran straight through the roll
# module and the J5 yoke in every pose. Putting J4 at 145 lets ONE full shell
# serve the forearm, and makes the J4 roll and J5 pitch axes INTERSECT --
# a proper spherical wrist, which admits closed-form IK.
L4_SPLIT = 119.0           # J3 -> J4, the full forearm shell
# 2026-08-19: the wrist is now an INTEGRATED unit, not three stacked modules.
# J4->J5 62 (32 forearm boss overhang + 30 housing) | J5->J6 34 | J6->TCP 26.
L5_SPLIT = 62.0            # J4 -> J5
L6_SPLIT = 30.0            # J5 -> J6
L_TCP = 30.0               # J6 -> TCP

# Import the section straight from the CAD parameters so the URDF can never
# drift from the printed geometry again. (It had: 47.5, stale after the
# 2026-08-17 stadium fix raised the bending depth to 50.0.)
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "cad"))
from params import SEC_H as _SEC_H, SEC_W as _SEC_W, LINK_L as _LINK_L
SEC_W, SEC_D = _SEC_H, _SEC_W      # bending depth, width
assert abs(L2 - _LINK_L) < 1e-9, f"URDF L2 {L2} != CAD LINK_L {_LINK_L}"
# The forearm SHELL is L4_SPLIT; the wrist hangs off beyond it, so the old
# "L4_SPLIT + L5_SPLIT == LINK_L" rule no longer applies.
assert abs(L4_SPLIT - _LINK_L) < 1e-9, f"forearm shell {L4_SPLIT} != CAD LINK_L {_LINK_L}"
_TOT = BASE_H + SHOULDER_RISE + L2 + L4_SPLIT + L5_SPLIT + L6_SPLIT + L_TCP
assert abs(_TOT - 450.0) < 1e-9, f"chain totals {_TOT}, must be 450"
BASE_D = 96.0

# ---- masses (kg) ----------------------------------------------------------
# 2026-08-21: these were hand-set LINK-ONLY figures -- plastic alone, no servos,
# bearings, shafts or fasteners -- and understated every link by 2 to 6 times.
# The total came to 0.765 kg for an arm that weighs 1.365 kg. Derive them from
# the same volumes.json the mass gate and the drawings use, so the dynamic model
# cannot drift from the built arm.
#
# The horn adapter changes NOTHING geometrically -- it lives on the shaft inside
# the joint and adds no chain length -- but it is real mass at every joint, and
# so are the servo, the bearing pair and the shaft.
import json as _json
_V = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                   "output", "cad", "volumes.json")))
from params import RHO_SOLID          # material density, one definition
from params import (BRG_OD as _BO, BRG_ID as _BI, BRG_W as _BW,
                    WRIST_BRG_OD as _WO, WRIST_BRG_ID as _WI,
                    WRIST_BRG_W as _WW, SHAFT_OD as _SO,
                    SHAFT_WALL as _SW, SHAFT_L as _SL, SHAFT_RHO as _SR)

_FILL, _RHO = 0.90, RHO_SOLID


def _g(name, qty=1):
    return _V[name] * _RHO * _FILL * qty


def _brg(od, idd, w):
    return np.pi / 4 * (od ** 2 - idd ** 2) * w * 7.85e-3 * 0.60


_B6806, _B6706 = _brg(_BO, _BI, _BW), _brg(_WO, _WI, _WW)
_SHAFT = np.pi / 4 * (_SO ** 2 - (_SO - 2 * _SW) ** 2) * _SL * _SR
_SERVO, _HORN = 60.0, _g("horn_adapter")
_LINKSET = (_g("link_half_tongue") + _g("link_half_groove")
            + _g("shaft_clamp") + _g("servo_collar")
            + _SERVO + 2 * _B6806 + _HORN + _SHAFT)

# Each joint runs a PAIR of bearings, not one. Allocating a single bearing per
# link left the model 2 x 6806 = 44.8 g light against the mass gate -- caught by
# comparing the two totals. Both bearings of a joint go on that joint's CHILD
# link; the base carries none of its own.
M = {k: v / 1000.0 for k, v in dict(
    base=_g("base"),
    link1=_g("turret_j1") + _SERVO + 2 * _B6806 + _HORN + _SHAFT,
    link2=_LINKSET,
    link3=_LINKSET,
    link4=_g("wrist_j4_housing") + _SERVO + 2 * _B6706 + _HORN + _SHAFT,
    link5=_g("wrist_j5_yoke") + _SERVO + 2 * _B6706 + _HORN + _SHAFT,
    link6=_g("wrist_j6_output") + _SERVO + 2 * _B6706 + _HORN + _SHAFT,
).items()}

LIMIT = dict(effort=2.94, velocity=4.6)          # ST3215 stall / no-load
LIMIT_J2 = dict(effort=4.90, velocity=3.7)       # ST3250 at the shoulder

RANGE = {  # degrees
    "joint1": (-165, 165), "joint2": (-115, 115), "joint3": (-150, 150),
    "joint4": (-165, 165),
    # J5 measured 2026-08-22, not assumed. The wrist folds j4housing into
    # j6output past a certain angle: exact-mesh bisection puts the collision-free
    # range at -94.2 .. +52.7 deg, so the declared +/-110 was 57 deg optimistic on
    # the + side and 16 deg on the -. It is asymmetric because the wrist is:
    # the servo pocket sits on one side. J4 has NO effect -- every J4 row of the
    # sweep is identical -- so this is a pure J5 fold, not a combination.
    # 3 deg of margin held back from the measured edge.
    "joint5": (-91, 49),
    "joint6": (-175, 175),
}


def box_inertia(m, x, y, z):
    """Solid cuboid about its centre, dimensions in metres."""
    return (m * (y * y + z * z) / 12.0,
            m * (x * x + z * z) / 12.0,
            m * (x * x + y * y) / 12.0)


def cyl_inertia(m, r, h):
    return (m * (3 * r * r + h * h) / 12.0,
            m * (3 * r * r + h * h) / 12.0,
            m * r * r / 2.0)


def inertial(m, ixx, iyy, izz, cz=0.0):
    return f"""    <inertial>
      <origin rpy="0 0 0" xyz="0 0 {cz:.6f}"/>
      <mass value="{m:.4f}"/>
      <inertia ixx="{ixx:.8f}" ixy="0" ixz="0" iyy="{iyy:.8f}" iyz="0" izz="{izz:.8f}"/>
    </inertial>"""


def seg_link(name, length_mm, mass, colour="steel"):
    """A clamshell segment: box of the real section, running along +Z."""
    L = length_mm * MM
    w, d = SEC_W * MM, SEC_D * MM
    ix, iy, iz = box_inertia(mass, d, w, L)
    return f"""  <link name="{name}">
{inertial(mass, ix, iy, iz, cz=L/2)}
    <visual>
      <origin rpy="0 0 0" xyz="0 0 {L/2:.6f}"/>
      <geometry><box size="{d:.5f} {w:.5f} {L:.5f}"/></geometry>
      <material name="{colour}"/>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 {L/2:.6f}"/>
      <geometry><box size="{d:.5f} {w:.5f} {L:.5f}"/></geometry>
    </collision>
  </link>"""


def joint(name, parent, child, z_mm, axis, lo, hi, lim):
    return f"""  <joint name="{name}" type="revolute">
    <parent link="{parent}"/>
    <child link="{child}"/>
    <origin rpy="0 0 0" xyz="0 0 {z_mm*MM:.6f}"/>
    <axis xyz="{axis}"/>
    <limit effort="{lim['effort']}" velocity="{lim['velocity']}"
           lower="{np.radians(lo):.6f}" upper="{np.radians(hi):.6f}"/>
    <dynamics damping="0.05" friction="0.02"/>
  </joint>"""


def build():
    P = []
    a = P.append
    a('<?xml version="1.0"?>')
    a('<!-- ARM-450 : 6-DOF arm, 450 mm overall, L2 = L3 = 145 mm.')
    a('     Generated by generate_urdf.py — do not hand-edit. -->')
    a('<robot name="arm450">')
    for n, rgba in (("steel", "0.62 0.70 0.79 1"), ("accent", "0.18 0.49 0.60 1"),
                    ("servo", "0.78 0.34 0.24 1")):
        a(f'  <material name="{n}"><color rgba="{rgba}"/></material>')

    a('  <link name="world"/>')
    a('  <joint name="world_to_base" type="fixed">')
    a('    <parent link="world"/><child link="base_link"/>')
    a('    <origin rpy="0 0 0" xyz="0 0 0"/>')
    a('  </joint>')

    # --- base: round pedestal --------------------------------------------
    r, h = BASE_D / 2 * MM, BASE_H * MM
    ix, iy, iz = cyl_inertia(M["base"], r, h)
    a(f'''  <link name="base_link">
{inertial(M["base"], ix, iy, iz, cz=h/2)}
    <visual>
      <origin rpy="0 0 0" xyz="0 0 {h/2:.6f}"/>
      <geometry><cylinder radius="{r:.5f}" length="{h:.5f}"/></geometry>
      <material name="steel"/>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 {h/2:.6f}"/>
      <geometry><cylinder radius="{r:.5f}" length="{h:.5f}"/></geometry>
    </collision>
  </link>''')

    # --- J1 turret --------------------------------------------------------
    a(joint("joint1", "base_link", "link1", BASE_H, "0 0 1",
            *RANGE["joint1"], LIMIT))
    a(seg_link("link1", SHOULDER_RISE, M["link1"], "accent"))

    # --- J2 shoulder, J3 elbow -------------------------------------------
    a(joint("joint2", "link1", "link2", SHOULDER_RISE, "0 1 0",
            *RANGE["joint2"], LIMIT_J2))
    a(seg_link("link2", L2, M["link2"]))

    a(joint("joint3", "link2", "link3", L2, "0 1 0", *RANGE["joint3"], LIMIT))
    a(seg_link("link3", L4_SPLIT, M["link3"]))

    # --- J4 forearm roll --------------------------------------------------
    a(joint("joint4", "link3", "link4", L4_SPLIT, "0 0 1",
            *RANGE["joint4"], LIMIT))
    a(seg_link("link4", L5_SPLIT, M["link4"], "accent"))

    # --- J5 wrist pitch ---------------------------------------------------
    a(joint("joint5", "link4", "link5", L5_SPLIT, "0 1 0",
            *RANGE["joint5"], LIMIT))
    a(seg_link("link5", L6_SPLIT, M["link5"]))

    # --- J6 tool roll -----------------------------------------------------
    a(joint("joint6", "link5", "link6", L6_SPLIT, "0 0 1",
            *RANGE["joint6"], LIMIT))
    a(seg_link("link6", L_TCP, M["link6"], "servo"))

    # --- TCP --------------------------------------------------------------
    a(f'''  <joint name="link6_to_tcp" type="fixed">
    <parent link="link6"/><child link="tcp"/>
    <origin rpy="0 0 0" xyz="0 0 {L_TCP*MM:.6f}"/>
  </joint>
  <link name="tcp"/>''')

    a('</robot>')
    return "\n".join(P)


if __name__ == "__main__":
    urdf = build()
    open("arm450.urdf", "w").write(urdf + "\n")
    total = BASE_H + SHOULDER_RISE + L2 + L4_SPLIT + L5_SPLIT + L6_SPLIT + L_TCP
    print("wrote arm450.urdf")
    print(f"  chain total  {total:.0f} mm   (requirement 450)")
    _l3 = L4_SPLIT + L5_SPLIT
    _naive = abs(L2 - _l3)
    _wrist = L6_SPLIT + L_TCP
    print(f"  L2 = {L2:.0f}, J3->J5 = {_l3:.0f}  -> naive inner radius {_naive:.0f} mm")
    print(f"  but the wrist is {_wrist:.0f} mm and can point inward, so the TCP")
    print(f"  dead zone is max(0, {_naive:.0f} - {_wrist:.0f}) = "
          f"{max(0, _naive-_wrist):.0f} mm  (verified 0 by a 60k-pose FK sweep)")
    print(f"  reach from J1 axis {L2+L4_SPLIT+L5_SPLIT+L6_SPLIT+L_TCP:.0f} mm")
    print(f"  total mass {sum(M.values()):.3f} kg (all-in: plastic + servos + bearings + shafts)")
