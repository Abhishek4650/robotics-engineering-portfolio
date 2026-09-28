# ARM-450 rev I -- editable CAD

Everything in this folder was exported from the verified rev-I design (all
release checks at 0, Rule 4 mating check at 0). Units are mm (URDF: m).

## What is here

| folder / file | what | open with |
|---|---|---|
| `parts_step/` | the 27 printed parts, one solid each, STEP AP214 | SolidWorks, Fusion 360, FreeCAD, Onshape, any CAD |
| `assembly_step/ARM450_ASSEMBLY.step` | the whole arm: 7 components, one per moving body (ground, turret, upper_link, forearm, j4_hub, blade, flange), with every part, servo, bearing, screw, insert and spring placed inside | any CAD |
| `assembly_step/body_*.step` | the same 7 bodies as separate files (the Fusion script imports these) | any CAD |
| `fit_test_step/` | the 7 fit-test coupons (print these first), STEP | any CAD |
| `fusion360/ARM450_joints.py` | Fusion 360 script: imports the 7 bodies, grounds the base, creates the 6 revolute joints with their limits, saves a native `.f3d` | Fusion 360 |
| `fusion360/ARM450_import_all.py` | Fusion 360 script: EVERY STEP of `parts_step/`, `fit_test_step/` and `assembly_step/` into its own Fusion design, saved in your project under `ARM450_rev_I/<folder>` and exported as a local `.f3d` in `fusion360/f3d/<folder>/` | Fusion 360 |
| `fusion360_parts/` | 34 individual part script folders (one per printable part + 7 fit test coupons): import and edit any part individually | Fusion 360 |
| `solidworks/ARM450_to_solidworks.swb` | SolidWorks macro: saves every part as `.SLDPRT` and the assembly as `.SLDASM` | SolidWorks |
| `urdf/` | `arm450.urdf` + meshes + `display.launch.py`: drag the 6 joints with sliders in RViz | ROS 2 Jazzy |
| `JOINT_AXES.csv` | each joint: point, axis direction, range (measured on the bearing pockets and servo horns) | spreadsheet |
| `PARAMETERS.csv` | 265 key dimensions: design value vs value measured in the exported file | spreadsheet |

**Native `.sldprt` / `.f3d` files can only be written by SolidWorks / Fusion
themselves.** Run the script or macro once and your CAD program creates them.
Neither script could be run on the build machine (no licence there). If one
stops, its message says where, and the manual steps below do the same thing.

## Fusion 360: individual part scripts (one folder per printable part)

If you only want to inspect or modify one specific part without running the full 41-file import:
1. Utilities > **Scripts and Add-Ins** > Scripts > green **+** > browse to `fusion360_parts/<part_name>` (e.g. `05_J2_turret_p1_x1` or `fit_01_servo_pinch`).
2. Select the part name in the list and click **Run**.
3. If an assembly is open, you can choose to open the part in a **new document** or insert it as a component into your **active design**.
4. Each folder is completely self-contained with its `.py` script, `.manifest`, `.step` CAD model, `.stl` printable file, and `README.md`.

## Fusion 360: every part as its own editable design

Utilities > **Scripts and Add-Ins** > Scripts > green **+** > the `fusion360`
folder > `ARM450_import_all` > **Run**. It takes a few minutes (41 files): each
STEP opens as a new design, is saved in your active project (folders
`ARM450_rev_I/parts_step`, `.../fit_test_step`, `.../assembly_step`) and exported
as a local `.f3d` into `fusion360/f3d/`. The message box at the end lists every
file and whether it worked.

## Fusion 360: an assembly you drag by its joints

1. Utilities > **Scripts and Add-Ins** > Scripts > the green **+** > pick the
   `fusion360` folder > select `ARM450_joints` > **Run**.
2. It imports the seven bodies, grounds `ground`, creates the six **revolute**
   joints (J1 base yaw ... J6 tool roll) with their limits, and saves
   `ARM450_rev_I` in your active project.
3. Grab any link with the pointer and drag it: it turns about its joint only,
   like the revolute-joint preview. Double-click a joint to **Animate** it.

If a joint is reported as failed, make it by hand: **Assemble > Joint**,
type **Revolute**, pick the child body then the parent body, and snap both
to the circle of that joint's bearing pocket. The axes are in
`JOINT_AXES.csv`. Set the limits under **Edit Joint Limits** (range column).

**Editing a part in Fusion:** STEP imports as a solid with no history. Use
**Press Pull** (change a face offset, a hole diameter or a pocket depth),
**Delete** (remove a face or feature: the hole closes up), **Extrude** from
a sketch on a face (add or cut), and **Move/Copy** (reposition faces). To
get a timeline, right-click the body > Capture Design History.

## SolidWorks: `.SLDPRT` + `.SLDASM`

1. Tools > Macro > **Run** > `solidworks/ARM450_to_solidworks.swb`.
2. Every part is saved as `.SLDPRT`, and the assembly as `ARM450_ASSEMBLY.SLDASM`
   with its part files, all in the `solidworks` folder.
3. **Features you can edit:** open a part, then Insert > FeatureWorks >
   **Recognize Features**. Holes, extrudes, cuts and fillets become features
   in the tree with dimensions you can change.
4. **Motion:** in the assembly, float every body except `ground`, then add
   **Concentric** mates on each joint's bearing pocket plus a **Coincident**
   mate on its face. Add a **Limit Angle** mate for the range in
   `JOINT_AXES.csv`. Now drag a link and it rotates about its joint.

(Or File > Open the assembly STEP directly: SolidWorks converts it to an
assembly and parts, and you add the mates as in step 4.)

## ROS 2: drag the joints with sliders

```
source /opt/ros/jazzy/setup.bash
ros2 launch ~/ros2_ws/Arm_450_new_design/EDITABLE_CAD/urdf/display.launch.py
```
RViz opens together with a slider window, one slider per joint. In RViz set
Fixed Frame = `ground` and add a **RobotModel** display (topic
`/robot_description`). The URDF was checked here: `check_urdf` parses it,
its kinematics match the verified joint axes to within 1e-12 mm over 200
random poses, and `robot_state_publisher` loads it. Your existing
`ros2_ws/src/arm450_description` package was **not** touched.

## Changing the design at the source

Every part is generated by a Python (CadQuery) script in `../REV_H/`, where
each dimension is a named parameter at the top of the file. Examples:
`gen_drive_j3.py` (J3 fork), `gen_clamp.py` (link centring ring),
`drive_common.py` (shared: bay, pinch, shaft, flats, split bolts). After a
change, run `../REV_H/release_run.sh`: every check is repeated and the print
files are rebuilt.
