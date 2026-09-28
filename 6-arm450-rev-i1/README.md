# ARM-450 rev I.1 — the printable arm, verified part against part, with its kinematics

<p align="center">
<img src="kinematics/figures/sine_vertical.gif" width="360" alt="ARM-450 rev I.1 CAD tracing a sine on a vertical board">
<img src="kinematics/figures/sine_table.gif" width="360" alt="ARM-450 rev I.1 CAD tracing a sine on a table">
</p>

The second generation of ARM-450 (the first concept is [Project 2](../2-arm450-mechanical-design)).
Rev I.1 is the version sent to the printer: six ST3215 serial-bus servos, 27 print files
(33 pieces), 114 screws, bearings on every joint, and a full kinematic model derived from the
CAD itself.

Every claim below comes from a check run on the **exported 3D geometry**, not from the
parameters used to draw it. Each check has its own log in [`release/LOGS`](release/LOGS).

## What is in this folder

| Folder | Contents |
| --- | --- |
| [`release/`](release) | The rev I.1 release, as released on 2026-09-27: PDFs, print files, editable CAD, logs |
| [`release/PRINTABLE_FILES`](release/PRINTABLE_FILES) | 27 STL files (33 pieces) and a 7-coupon fit test to print first |
| [`release/EDITABLE_CAD`](release/EDITABLE_CAD) | STEP parts and assembly, Fusion 360 joints script, SolidWorks macro, URDF |
| [`release/FUSION_DESIGN_TREES`](release/FUSION_DESIGN_TREES) | One Fusion 360 script per part; each builds the part as an editable timeline and saves the `.f3d` |
| [`release/PDF`](release/PDF) | Audit report, base-to-flange assembly guide (24 steps), fastener manual, poses, part sheets, interface sections |
| [`kinematics/`](kinematics) | DH table, FK, closed-form and numerical IK, Jacobian, workspace, manipulability, timed sine trajectories, ROS 2 demo |
| [`source/`](source) | The generators and verification scripts that produced the release (CadQuery / OpenCascade) |

Start with [`release/READ_ME_FIRST.txt`](release/READ_ME_FIRST.txt), then
[`release/PDF/ARM450_AUDIT_REPORT.pdf`](release/PDF/ARM450_AUDIT_REPORT.pdf).

## The mechanical design

| | |
| --- | --- |
| Actuators | 6 × Waveshare ST3215 serial-bus servos, each screwed to the previous link by its own back holes |
| Drive | Servo horn bolted to the driven link; the joint rides on a ball bearing coaxial with the servo shaft |
| Shoulder load | Gravity springs on J2 and J3; torque safety factor 1.07 (J2) and 1.26 (J3) with the arm level, no payload |
| Mass | 1509 g (printed parts at 65 % infill + 6 servos) |
| Print set | 27 files, 33 pieces; a fit-test coupon confirms the servo screw pattern before the housings are printed |

**Release checks, all at 0 failures** (25 check stages in
[`REVI_CHECKS.log`](release/LOGS/REVI_CHECKS.log)):

- **Mating, not overlapping.** Parts touch only on designed faces, such as bearing seats, the
  horn face and screws in their holes. Any other overlap is measured as a boolean volume and
  fails the check.
- **Real hardware in the assembly.** The official ST3215 model, bearings and every fastener
  are modelled as solids and tested against every part.
- **Buildability.** A hex key reaches all 114 screws at their build step. Every servo can be
  removed, and every servo plug can be inserted with the arm assembled.
- **Cable routing.** Each joint has a proven cable route; no joint turns more than 180°, so
  no cable winds up.
- **Six working joints.** Each servo axis coincides with its bearing axis, the Jacobian has
  rank 6, and the only singularities are the textbook ones.
- **Printability.** Every glued feature joins over its full section. Rev I.1 exists because
  of this check: the J3 spring lugs sat on a 0.1 mm sliver, now 136 mm²
  ([picture](release/PDF/RULE6_VIEWS/j3_lug_fix.png)).
- **Parameters.** 265 design parameters are checked against the geometry they produced.

**Status.** The print verdict is GREEN from the CAD checks. The arm has not yet been built
and measured, so nothing here claims hardware performance.

## The kinematics ([`kinematics/`](kinematics))

The method is modified (Craig) DH, `^{i-1}_iT = Rot_x(α_{i-1}) Trans_x(a_{i-1}) Rot_z(θ_i) Trans_z(d_i)`,
with a velocity-propagation Jacobian: the same method as Project 1. The DH table is
**derived from the servo axes measured on the CAD**, not typed in.

| i | α_{i-1} | a_{i-1} (mm) | d_i (mm) |
|---|---|---|---|
| 1 | 0 | 0 | 90.000 |
| 2 | −90° | 0 | 0 |
| 3 | 0 | 119.000 | 0 |
| 4 | +90° | 0 | 221.369 |
| 5 | −90° | 0 | 0 |
| 6 | +90° | 0 | 0 |

The tool frame is 88.089 mm beyond the wrist centre. J4, J5 and J6 meet at one point, so
the arm has a spherical wrist.

| Result | Value |
| --- | --- |
| FK vs the CAD (product of exponentials of the measured axes) | max 3.0e-13 mm over 2000 poses |
| FK vs the URDF (ikpy) | max 2.6e-13 mm |
| Closed-form IK (Pieper, 8 branches) | 100 % of 500 poses, 0.18 ms, exact |
| Numerical IK from a nearby seed | DLS 95 %, pseudoinverse 99 %, Levenberg–Marquardt 99.8 % |
| Numerical IK from the ready pose | 18–48 %: these solvers are local, so they are used along paths, seeded by the closed form |
| Reach from the J1 axis | 405.5 mm |
| Pen straight down | **Impossible anywhere.** The pitch joints give 54 + 72 + 46.5 = 172.5°, not 180°. On a table the pen must tilt 15° or more. |
| Sine on a vertical board, timed | ~82 mm/s with the servos at half their no-load rating; the encoder alone limits accuracy to ~0.9 mm |

The design lesson: **the joint limits, not the link lengths, decide what this arm can
draw**. Report: [`kinematics/docs/ARM450_KINEMATICS.pdf`](kinematics/docs/ARM450_KINEMATICS.pdf) ·
slides: [`kinematics/docs/ARM450_KINEMATICS_slides.pptx`](kinematics/docs/ARM450_KINEMATICS_slides.pptx).

## Running it

```bash
cd kinematics && bash run_all.sh                 # every analysis, figure, log and the PDF
source /opt/ros/jazzy/setup.bash
cd kinematics/ros2 && ros2 launch sine_demo.launch.py which:=vertical    # or table
```

The scripts in [`source/`](source) are included as they were run. They read the CAD
inputs from the author's workspace by absolute path, so they document the method but do
not run outside that workspace. The released outputs they produced are in `release/`.
