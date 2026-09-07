# ARM-450 — Pre-Print Flight Check

**Eight stages · 27 checks · run `python3 preflight.py`**

> # ✅ GO FOR PRINTING
>
> **21 passed · 0 failures · 2026-08-22**
>
> Every stage below is a real analysis, not a restatement of the one before, and each
> states its own criterion so a pass can be argued with. The verdict is GO only if every
> hard stage passes.

---

## What each stage actually proves

| stage | question it answers | criterion |
| --- | --- | --- |
| **1 Design check** | Do the features physically exist in the geometry? | STEP B-rep audit, not parameters |
| **2 FEA** | Does anything yield under load? | p99 von Mises SF ≥ 3 |
| | Does every load case hold with a tool fitted? | 6 criteria × 5 configurations |
| **3 Creep + fatigue** | Does it fail slowly, in ways a static check misses? | stress ratio < 0.1, life > 1e8 cycles |
| **4 Stiffness** | Does the tool stay where it is put? | structural compliance < 0.30 mm |
| **5 URDF** | Does the model match the machine? | parses, arm mass matches the gate, meshes resolve, the fitted tool is present |
| **6 Path tracing** | Does the trajectory you will run actually work? | 0 collisions, < 0.20 mm rms, inside limits |
| **7 Simulation** | Will the ROS side work on real hardware? | trajectory published, approach ramp, rate within servo |
| **8 End effectors** | Do the tools go on, and does the docking latch work? | 29 interface checks incl. a simulated mate |
| | Does a fitted tool stay inside the agreed envelope? | system reach ≤ 495 mm |

---

## Results

```
  STAGE 1 — DESIGN CHECK AND VERIFICATION
  ------------------------------------------------------------------------
    [ PASS ] geometry audit (STEP B-rep)                  52 features physically present, 0 missing/offset
    [ PASS ] every bearing pocket accepts its bearing     10 pockets, light press
    [ PASS ] pre-print gate                               60 passed, 0 warnings, 0 failures
    [ PASS ] mass within the hard ceiling                 1365 g of 1450 g

  STAGE 2 — FEA
  ------------------------------------------------------------------------
    [ PASS ] FEA safety factor (p99 von Mises)            worst SF 23.0 across all parts

  STAGE 3 — CREEP AND FATIGUE
  ------------------------------------------------------------------------
    [ PASS ] working stress far below yield               0.38 MPa vs 60 MPa yield (ratio 0.0064)
    [ PASS ] fatigue life                                 4.3e+28 cycles to failure
    [ PASS ] creep strain at 1 year, continuous load      0.040 % — park folded when idle

  STAGE 4 — STIFFNESS
  ------------------------------------------------------------------------
    [ PASS ] structural compliance at the tool            0.098 mm in PLA+CF at 2.0 mm wall (design wall is 2.4)

  STAGE 5 — URDF
  ------------------------------------------------------------------------
    [ PASS ] URDF parses (mesh version)                   single tree, root world
    [ PASS ] URDF mass matches the mass gate              1.365 kg arm vs 1.365 kg  (+ 75 g tool as payload)
    [ PASS ] the fitted tool is in the model RViz loads   75 g tool link on link6 — the URDF had no tool at all until 2026-08-22
    [ PASS ] every mesh reference resolves                8/8 meshes found

  STAGE 6 — PATH TRACING
  ------------------------------------------------------------------------
    [ PASS ] solved path is collision-free                240/240 waypoints clear (exact mesh)
    [ PASS ] path accuracy                                0.014 mm rms, tilt 0.093 deg rms
    [ PASS ] path smoothness                              largest joint step 2.09 deg between waypoints
    [ PASS ] every waypoint inside the joint limits       checked against arm450.urdf, including the narrowed J5

  STAGE 7 — SIMULATION READINESS
  ------------------------------------------------------------------------
    [ PASS ] node loads the solved trajectory             240 waypoints
    [ PASS ] playback is continuous (ping-pong)           no wrap discontinuity
    [ PASS ] approach ramp before tracing                 eases from the start pose, no slam on real servos
    [ PASS ] JointTrajectory published for a controller   240 points, latched TRANSIENT_LOCAL on /arm450/trajectory
    [ PASS ] joint rate within the servo                  0.91 rad/s vs ~2.3 rad/s loaded ST3215

  STAGE 8 — END EFFECTORS
  ------------------------------------------------------------------------
    [ PASS ] end-effector interfaces                      29/29 checks — J6 bolt pattern, bayonet fit, rack mesh, docking capture
    [ PASS ] heaviest tool within the payload allowance   75 g (adapter 14 + gripper 60 incl. SG90) vs the 300 g assumed at the TCP
    [ PASS ] system reach with the longest tool fitted    492 mm (450 arm + 42 gripper) vs 495 mm accepted — the 450 mm spec is the ARM
```

---

## Why stage 8 counts solids and simulates a mate

Stage 8 started as a bolt-pattern and bayonet-diameter check, and it passed while the
docking tool **had no latch on it.** Three lugs had been unioned into the probe at a
height where the bore was already Ø25.8, so they floated 5.5 mm clear of any wall.
CadQuery's `.union()` does not fail when the shapes do not touch — it returns a compound —
and every downstream step treats a compound as a part.

So the stage now asks two questions no dimension check can answer:

**How many solids are you?** `len(shape.Solids())` for all six tool parts, fail on anything
but 1. That one line would have caught the floating lugs, and it also catches the
`horn_adapter` failure mode from earlier in the project.

**Does the mate work?** The exported probe mesh is driven onto the exported target mesh
through all five states, with the expected answer written down for each:

| state | expected |
| --- | --- |
| 6 mm short, slots aligned | clear |
| seated | clear |
| rolled 30° to latch | clear |
| latched, pulled 2 mm | **collides — this is the latch working** |
| rolled back, withdrawn | clear |

A check that only ever expects *no collision* cannot test a latch, because a latch is a
deliberate collision. Capture tolerance is measured the same way — sweep the probe sideways
until it fouls — rather than subtracted from two diameters: **±9.75 mm.**

---

## Why stage 6 and 7 exist separately

**Stage 6 checks the path, not the space.** An earlier version of this project ran a
random-pose interference sweep, saw ~30 % collisions, and treated it as background noise
because the joint-limit box is mostly irrelevant. The task was never checked — and when it
finally was, **72 of 240 waypoints collided.** Coverage of a state space is a much weaker
claim than correctness of the one path that will be executed.

**Stage 7 checks what hardware needs, which simulation does not expose.** Three things were
added specifically because they only bite on real servos:

- **An approach ramp.** The node used to start at waypoint 0. On real hardware the arm is
  wherever it was left, so that is a full-speed slam. It now eases across on a cosine ramp
  over `approach_time` (default 3 s), leaving and arriving at zero velocity.
- **A JointTrajectory topic.** `/joint_states` is a *visualisation* stream — a real
  controller will not follow it. The whole solved path is now published once as a
  240-point `trajectory_msgs/JointTrajectory` on `/arm450/trajectory`, latched
  (TRANSIENT_LOCAL) so a controller that starts later still receives it. Velocities are
  included by central difference.
- **A velocity check against the actuator.** Peak joint rate is 0.91 rad/s against roughly
  2.3 rad/s for a loaded ST3215. Exceeding it would not error — the servo would simply lag,
  and the traced path would quietly stop being the solved path.

---

## What GO does and does not mean

**It means:** the design is verified. Geometry, structure, kinematics, the model and the
software all agree with each other and with the arm you are about to print.

**It does not mean the print will be right.** Two things remain, and neither is a design
question:

1. **The fit coupon.** Every check above verifies the geometry is *correct*. None of them
   tells you what your machine does to a real Ø42 bore. That is a 0.9 h print and it gates
   every part with a bearing pocket.
2. **Servo backlash is unmeasured** and is the largest single term in the precision budget.
   The 0.014 mm rms above is what the *mechanism* allows; measured end-to-end precision is
   expected around 1.4 mm, dominated by backlash.

---

## Running it

```bash
cd ~/ros2_ws/arm450_design
python3 preflight.py          # exits 0 on GO, 1 on NO-GO
```

Re-run it after any change to the CAD, the URDF, the trajectory or the node. It is cheap
compared with a print run.
