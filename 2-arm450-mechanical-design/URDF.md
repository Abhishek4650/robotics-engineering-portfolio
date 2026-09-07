# ARM-450 — URDF Reference

**Robot name** `arm450` · 6 revolute joints · 450 mm chain · generated 2026-08-20

This document covers the URDF alone: the kinematic chain, every link and joint, the
verification it has passed, and the complete source. Kinematics theory (Modified-DH,
transforms, FK derivation) is in `ARM450_KINEMATICS.pdf`; how to run it is in
`ARM450_RUN.pdf`.

---

## 1. The chain

```
world
 └── base_link                    fixed at origin
      └── link1        joint1     Z roll    z = 50    base yaw / turret
           └── link2   joint2     Y pitch   z = 40    shoulder
                └── link3         joint3    Y pitch   z = 119   elbow
                     └── link4    joint4    Z roll    z = 119   forearm roll
                          └── link5   joint5   Y pitch   z = 62   wrist pitch
                               └── link6  joint6   Z roll   z = 30   tool roll
                                    ├── tcp      fixed    z = 30   tool centre point
                                    └── tool     fixed    z = 0    fitted end effector
                                         └── tool_tip  fixed  z = 72  working point
```

Eleven links, ten joints, six of them actuated. `world`, `tcp` and `tool_tip` are massless
frames — `world` gives RViz a fixed root to attach to, `tcp` is the point the IK solves
for, and `tool_tip` is where the fitted tool actually works from.

### The `tool` link

Added 2026-08-22. Before that the URDF stopped at `link6` and **RViz drew a bare J6 face**,
even though the sine path had been re-verified collision-free with a gripper fitted and the
workspace recomputed for it. All of that lived in `assemble.py` — the CAD and collision
assembly — and none of it reached the model RViz loads.

`tool` is a fixed link on `link6` carrying the quick-change adapter, the tool body and (for
the gripper) both jaws as a single combined mesh, placed by `assemble.build()` so the thing
RViz draws is the geometry the collision check cleared.

| fitted | mass | `tool_tip` at | note |
| --- | --- | --- | --- |
| gripper | 74.6 g | z = 72 mm from link6 | 42 mm past the J6 face |
| dock probe | 62.4 g | z = 66 mm from link6 | 36 mm past the J6 face |
| none | — | — | bare face, the old behaviour |

Switch with `EMIT=1 TOOL=dock python3 generate_urdf_meshes.py` — see ARM450_RUN.pdf §9A.

**The tool is payload, not arm.** The mass check in preflight stage 5 sums the arm links
only and reports the tool separately; adding it in would have inflated the total by 75 g
and quietly broken the one check that ties the model to the 1450 g budget.

### The 450 mm budget

```
  base            50
  shoulder rise   40
  L2 upper arm   119
  L3 forearm     119
  J4 → J5         62
  J5 → J6         30
  J6 → TCP        30
  -----------------
  TOTAL          450 mm   ✓ requirement met exactly
```

`generate_urdf.py` asserts this sum at build time, so the chain cannot silently drift
past 450 mm. It also asserts `L2 == LINK_L` and `L4_SPLIT == LINK_L` against the CAD
parameters, which is what keeps the URDF and the printed parts describing the same robot.

**L2 = L3 = 119 mm is deliberate.** The inner radius of a reachable annulus is |L2 − L3|,
so equal links drive the dead zone to zero. A 60 000-pose FK sweep confirms no unreachable
inner region.

---

## 2. Joints

| joint | type | parent → child | origin z (mm) | axis | range | effort (N·m) |
| --- | --- | --- | --- | --- | --- | --- |
| `world_to_base` | fixed | world → base_link | 0 | — | — | — |
| `joint1` | revolute | base_link → link1 | 50 | Z (roll) | ±165° | 2.94 |
| `joint2` | revolute | link1 → link2 | 40 | Y (pitch) | ±115° | 4.9 |
| `joint3` | revolute | link2 → link3 | 119 | Y (pitch) | ±150° | 2.94 |
| `joint4` | revolute | link3 → link4 | 119 | Z (roll) | ±165° | 2.94 |
| `joint5` | revolute | link4 → link5 | 62 | Y (pitch) | ±110° | 2.94 |
| `joint6` | revolute | link5 → link6 | 30 | Z (roll) | ±175° | 2.94 |
| `link6_to_tcp` | fixed | link6 → tcp | 30 | — | — | — |

**Axis convention:** at `q = 0` every joint is at its home position and the arm stands
straight up along +Z. `joint2` carries the ST3250 (4.9 N·m) because the shoulder sees the
largest gravity moment; every other joint is an ST3215 at 2.94 N·m.

**Why the limits are asymmetric in usefulness:** `joint5` at ±110° is the tightest, and it
is the joint that runs out of travel first when tracing on a horizontal surface. Vertical
board tracing — the Rsine task — stays well inside it.

---

## 3. Links

| link | mass (kg) | ixx (kg·m²) | iyy | izz |
| --- | --- | --- | --- | --- |
| `world` | *frame only* | | | |
| `base_link` | 0.1800 | 1.412e-04 | 1.412e-04 | 2.074e-04 |
| `link1` | 0.1000 | 3.417e-05 | 2.034e-05 | 2.784e-05 |
| `link2` | 0.1450 | 2.013e-04 | 1.813e-04 | 4.037e-05 |
| `link3` | 0.1300 | 1.805e-04 | 1.625e-04 | 3.619e-05 |
| `link4` | 0.0600 | 3.172e-05 | 2.343e-05 | 1.671e-05 |
| `link5` | 0.0600 | 1.700e-05 | 8.700e-06 | 1.671e-05 |
| `link6` | 0.0900 | 2.550e-05 | 1.306e-05 | 2.506e-05 |
| `tcp` | *frame only* | | | |
| **total** | **0.765** | | | |


Link mass totals 0.765 kg. This is the URDF's dynamic model, not the build mass — it
excludes servos, bearings and shafts, which the mass gate accounts for separately
(1144 g all-in against the 1.2 kg limit).

Inertias are solid-cuboid approximations about each link's own centre, computed from the
real clamshell section (50.0 × 29.0 mm). They are good enough for visualisation and
gravity-torque estimates. **They are not measured**, so do not use them for high-bandwidth
control tuning without re-deriving from the CAD.

---

## 4. Geometry

Visual and collision geometry are boxes and a cylinder sized to the real printed section,
not meshes. That is a deliberate choice: primitives keep collision checks cheap and make
the kinematics legible.

STL meshes for all seven bodies exist in `arm450_description/meshes/` and can be swapped
into the `<visual>` blocks when a photorealistic render is wanted. Doing so changes
nothing kinematic.

| material | rgba | used for |
| --- | --- | --- |
| `steel` | 0.62 0.70 0.79 1 | base, link2, link3, link5 |
| `accent` | 0.18 0.49 0.60 1 | link1, link4 |
| `servo` | 0.78 0.34 0.24 1 | link6 |

---

## 5. Verification

| check | result |
| --- | --- |
| `check_urdf` parse | **Passed** — single tree, root `world`, 9 links, no orphans |
| Chain sums to 450 mm | **450.0 mm**, asserted at generation |
| URDF ↔ CAD link length | 119.0 == 119.0, asserted |
| FK vs Modified-DH, 5000 random poses | **0.000 nm** position error |
| Dead zone (60 000-pose sweep) | **0 mm** — no unreachable inner region |
| `robot_state_publisher` load | Publishes full TF tree, all 6 joints |
| Sine trajectory replay | 240 waypoints, 0.193 mm rms path error |

The DH rotation differs from the URDF by a constant 180° about Z. That is frame labelling
only — position agreement is exact, and the constant offset is documented in
`ARM450_KINEMATICS.pdf`.

---

## 6. How it is generated

The URDF is **generated, never hand-edited.** `generate_urdf.py` imports the section and
link length straight from `cad/params.py`, so a change to the printed geometry propagates
to the model automatically.

```bash
cd ~/ros2_ws/arm450_design
python3 generate_urdf.py                    # writes arm450.urdf
cp arm450.urdf ../src/arm450_description/urdf/
```

If you edit `arm450.urdf` by hand, the next generation overwrites it. Change
`generate_urdf.py` or `cad/params.py` instead.

---

## 7. Complete source

```xml
<?xml version="1.0"?>
<!-- ARM-450 : 6-DOF arm, 450 mm overall, L2 = L3 = 145 mm.
     Generated by generate_urdf.py — do not hand-edit. -->
<robot name="arm450">
  <material name="steel"><color rgba="0.62 0.70 0.79 1"/></material>
  <material name="accent"><color rgba="0.18 0.49 0.60 1"/></material>
  <material name="servo"><color rgba="0.78 0.34 0.24 1"/></material>
  <link name="world"/>
  <joint name="world_to_base" type="fixed">
    <parent link="world"/><child link="base_link"/>
    <origin rpy="0 0 0" xyz="0 0 0"/>
  </joint>
  <link name="base_link">
    <inertial>
      <origin rpy="0 0 0" xyz="0 0 0.025000"/>
      <mass value="0.1800"/>
      <inertia ixx="0.00014118" ixy="0" ixz="0" iyy="0.00014118" iyz="0" izz="0.00020736"/>
    </inertial>
    <visual>
      <origin rpy="0 0 0" xyz="0 0 0.025000"/>
      <geometry><cylinder radius="0.04800" length="0.05000"/></geometry>
      <material name="steel"/>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 0.025000"/>
      <geometry><cylinder radius="0.04800" length="0.05000"/></geometry>
    </collision>
  </link>
  <joint name="joint1" type="revolute">
    <parent link="base_link"/>
    <child link="link1"/>
    <origin rpy="0 0 0" xyz="0 0 0.050000"/>
    <axis xyz="0 0 1"/>
    <limit effort="2.94" velocity="4.6"
           lower="-2.879793" upper="2.879793"/>
    <dynamics damping="0.05" friction="0.02"/>
  </joint>
  <link name="link1">
    <inertial>
      <origin rpy="0 0 0" xyz="0 0 0.020000"/>
      <mass value="0.1000"/>
      <inertia ixx="0.00003417" ixy="0" ixz="0" iyy="0.00002034" iyz="0" izz="0.00002784"/>
    </inertial>
    <visual>
      <origin rpy="0 0 0" xyz="0 0 0.020000"/>
      <geometry><box size="0.02900 0.05000 0.04000"/></geometry>
      <material name="accent"/>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 0.020000"/>
      <geometry><box size="0.02900 0.05000 0.04000"/></geometry>
    </collision>
  </link>
  <joint name="joint2" type="revolute">
    <parent link="link1"/>
    <child link="link2"/>
    <origin rpy="0 0 0" xyz="0 0 0.040000"/>
    <axis xyz="0 1 0"/>
    <limit effort="4.9" velocity="3.7"
           lower="-2.007129" upper="2.007129"/>
    <dynamics damping="0.05" friction="0.02"/>
  </joint>
  <link name="link2">
    <inertial>
      <origin rpy="0 0 0" xyz="0 0 0.059500"/>
      <mass value="0.1450"/>
      <inertia ixx="0.00020132" ixy="0" ixz="0" iyy="0.00018127" iyz="0" izz="0.00004037"/>
    </inertial>
    <visual>
      <origin rpy="0 0 0" xyz="0 0 0.059500"/>
      <geometry><box size="0.02900 0.05000 0.11900"/></geometry>
      <material name="steel"/>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 0.059500"/>
      <geometry><box size="0.02900 0.05000 0.11900"/></geometry>
    </collision>
  </link>
  <joint name="joint3" type="revolute">
    <parent link="link2"/>
    <child link="link3"/>
    <origin rpy="0 0 0" xyz="0 0 0.119000"/>
    <axis xyz="0 1 0"/>
    <limit effort="2.94" velocity="4.6"
           lower="-2.617994" upper="2.617994"/>
    <dynamics damping="0.05" friction="0.02"/>
  </joint>
  <link name="link3">
    <inertial>
      <origin rpy="0 0 0" xyz="0 0 0.059500"/>
      <mass value="0.1300"/>
      <inertia ixx="0.00018049" ixy="0" ixz="0" iyy="0.00016252" iyz="0" izz="0.00003619"/>
    </inertial>
    <visual>
      <origin rpy="0 0 0" xyz="0 0 0.059500"/>
      <geometry><box size="0.02900 0.05000 0.11900"/></geometry>
      <material name="steel"/>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 0.059500"/>
      <geometry><box size="0.02900 0.05000 0.11900"/></geometry>
    </collision>
  </link>
  <joint name="joint4" type="revolute">
    <parent link="link3"/>
    <child link="link4"/>
    <origin rpy="0 0 0" xyz="0 0 0.119000"/>
    <axis xyz="0 0 1"/>
    <limit effort="2.94" velocity="4.6"
           lower="-2.879793" upper="2.879793"/>
    <dynamics damping="0.05" friction="0.02"/>
  </joint>
  <link name="link4">
    <inertial>
      <origin rpy="0 0 0" xyz="0 0 0.031000"/>
      <mass value="0.0600"/>
      <inertia ixx="0.00003172" ixy="0" ixz="0" iyy="0.00002343" iyz="0" izz="0.00001671"/>
    </inertial>
    <visual>
      <origin rpy="0 0 0" xyz="0 0 0.031000"/>
      <geometry><box size="0.02900 0.05000 0.06200"/></geometry>
      <material name="accent"/>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 0.031000"/>
      <geometry><box size="0.02900 0.05000 0.06200"/></geometry>
    </collision>
  </link>
  <joint name="joint5" type="revolute">
    <parent link="link4"/>
    <child link="link5"/>
    <origin rpy="0 0 0" xyz="0 0 0.062000"/>
    <axis xyz="0 1 0"/>
    <limit effort="2.94" velocity="4.6"
           lower="-1.919862" upper="1.919862"/>
    <dynamics damping="0.05" friction="0.02"/>
  </joint>
  <link name="link5">
    <inertial>
      <origin rpy="0 0 0" xyz="0 0 0.015000"/>
      <mass value="0.0600"/>
      <inertia ixx="0.00001700" ixy="0" ixz="0" iyy="0.00000870" iyz="0" izz="0.00001671"/>
    </inertial>
    <visual>
      <origin rpy="0 0 0" xyz="0 0 0.015000"/>
      <geometry><box size="0.02900 0.05000 0.03000"/></geometry>
      <material name="steel"/>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 0.015000"/>
      <geometry><box size="0.02900 0.05000 0.03000"/></geometry>
    </collision>
  </link>
  <joint name="joint6" type="revolute">
    <parent link="link5"/>
    <child link="link6"/>
    <origin rpy="0 0 0" xyz="0 0 0.030000"/>
    <axis xyz="0 0 1"/>
    <limit effort="2.94" velocity="4.6"
           lower="-3.054326" upper="3.054326"/>
    <dynamics damping="0.05" friction="0.02"/>
  </joint>
  <link name="link6">
    <inertial>
      <origin rpy="0 0 0" xyz="0 0 0.015000"/>
      <mass value="0.0900"/>
      <inertia ixx="0.00002550" ixy="0" ixz="0" iyy="0.00001306" iyz="0" izz="0.00002506"/>
    </inertial>
    <visual>
      <origin rpy="0 0 0" xyz="0 0 0.015000"/>
      <geometry><box size="0.02900 0.05000 0.03000"/></geometry>
      <material name="servo"/>
    </visual>
    <collision>
      <origin rpy="0 0 0" xyz="0 0 0.015000"/>
      <geometry><box size="0.02900 0.05000 0.03000"/></geometry>
    </collision>
  </link>
  <joint name="link6_to_tcp" type="fixed">
    <parent link="link6"/><child link="tcp"/>
    <origin rpy="0 0 0" xyz="0 0 0.030000"/>
  </joint>
  <link name="tcp"/>
</robot>
```
