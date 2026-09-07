# ARM-450 — Design Log

- **Updated:** 2026-08-22

---

## Current state: 6-DOF, all axes have hardware

| axis | joint | part | status |
| --- | --- | --- | --- |
| J1 | base yaw | `turret_j1` | NEW — first pass, unverified |
| J2 | shoulder pitch | `link boss + shaft + clamp + collar` | validated, printed |
| J3 | elbow pitch | `link boss + shaft + clamp + collar` | validated, printed |
| J4 | forearm roll | `roll_module` | NEW — first pass, unverified |
| J5 | wrist pitch | `wrist_yoke_j5 + wrist` | NEW — first pass, unverified |
| J6 | tool roll | `roll_module (2nd)` | NEW — first pass, unverified |

**One interface everywhere:** Ø42 pocket · 6806 bearing (30×42×7) · Ø30 shaft. One bearing part number for the whole machine.

---

## Parts released

| part | STEP | STL |
| --- | --- | --- |
| `arm450_parts_kit` | yes | yes |
| `base` | yes | yes |
| `bearing_yoke` | yes | yes |
| `joint_shaft` | yes | yes |
| `link_half_groove` | yes | yes |
| `link_half_tongue` | yes | yes |
| `roll_module` | yes | yes |
| `servo_collar` | yes | yes |
| `shaft_clamp` | yes | yes |
| `tool_flange` | yes | yes |
| `turret_j1` | yes | yes |
| `wrist` | yes | yes |
| `wrist_yoke_j5` | yes | yes |

---

## Verification log

| date | check | result |
| --- | --- | --- |
| 2026-08-13 | link bending axis | CORRECTED — I=87,514 not 39,899 (servo fit proved the orientation) |
| 2026-08-13 | seam open/closed | CORRECTED — no bending penalty; torsion 215x |
| 2026-08-14 | printer shrinkage | MEASURED 0.02 mm XY -> bearing pocket Ø42.15 to Ø42.00 |
| 2026-08-14 | joint load sweep | J2 2.62 / J3 1.27 N·m — both UNDER-SPECCED on continuous |
| 2026-08-14 | topology opt | validates the box section; no redesign needed |
| 2026-08-17 | stadium profile | CORRECTED — boss was not tangent, 0.48 mm corner error |
| 2026-08-17 | seam gap | CORRECTED — tongue bottomed (non-integer layers) + wedged |
| 2026-08-18 | joint stack fit | clamp OD 42 to 38 — belongs in the through-bore |
| 2026-08-18 | URDF vs CAD | CORRECTED — section was stale; now imported + asserted |
| 2026-08-18 | DOF audit | was 2 of 6; now 6 of 6 |
| 2026-08-18 | chain budget | turret gave J2 at 30 mm not 40 — CORRECTED, now 81 mm tall |
| 2026-08-18 | assembly DOF | `build()` took only q2,q3,q5 — J1/J4/J6 never wired. CORRECTED to q1..q6 |
| 2026-08-18 | wrist J5→TCP | yoke 30 + roll module 34 + flange 6 = 70 mm, exact |
| 2026-08-18 | forearm J4 | roll module 34 mm of 145, shell carries 111 — passes |
| 2026-08-19 | interference sweep | 100 % of poses collided. J4 was mid-forearm and a 209 mm shell was placed in an 80 mm slot |
| 2026-08-19 | wrist redesign | 3 stacked modules needed 152 mm against a 70 mm allowance. Integrated wrist: 62/30/30 |
| 2026-08-19 | interference re-run | **100 % -> 16 %**, and every remaining hit is arm-vs-base, none arm-vs-arm |
| 2026-08-19 | links shortened | 145 -> **119 mm** to buy wrist length. Reach unchanged at 360 mm |
| 2026-08-19 | dead zone | naive formula said 62 mm; the 60 mm wrist points inward so the real TCP void is **0** (60k-pose FK sweep) |
| 2026-08-19 | FEA, new parts | turret SF 77, J4 housing 408, J5 yoke 417, J6 output 199 — all pass |
| 2026-08-19 | servo fit | J4 and J6 had **no room for a servo**. J4 housing Ø46->Ø56 (free); wrist rebalanced 34/26 -> 30/30 so J6 takes a full ST3215 |
| 2026-08-19 | servo mounting | every part had a POCKET but **no mounting holes and no horn pattern**. Both added; the pattern values are PLACEHOLDERS pending measurement |
| 2026-08-19 | uniform servo | ST3215 everywhere works **for drawing** (J2 14–29 % of stall with a pen). Fails only at 300 g on full extension (89 %) |
| 2026-08-19 | Rsine on ARM-450 | **vertical board 40/40, 0.03 mm rms, pen tilt 0.5°** at x=240 and x=300 |
| 2026-08-19 | Rsine horizontal | table FAILS: J2, J4, J5 all pinned at limits simultaneously. Widening J5 110->150° cuts pen-tilt error 54°->16° but still 0/40 |
| 2026-08-19 | URDF extraction | the URDF was parameter-linked, **not** geometry-extracted. `arm450_meshes.urdf` now carries real meshes + inertias from the STEP solids; FK identical to 0.000 µm |
| 2026-08-19 | interference sweep | **100 % of poses collided** — first time this was ever checked |
| 2026-08-19 | wrist budget | needs 152 mm J4→TCP, had 70 — short 82 mm, a budget failure |
| 2026-08-19 | reach vs split | reach is 360 mm for ANY link split; shortening links is free |
| 2026-08-19 | links 145→119 | both, L2=L3 preserved; frees 52 mm for the wrist |
| 2026-08-19 | integrated wrist | 3 nesting parts, 122 mm total, 6-DOF retained |
| 2026-08-19 | dead zone | naive formula said 62 mm; true TCP void 0.00 (60k-pose FK sweep) |
| 2026-08-19 | interference re-run | **14 %, all base/turret only** — no arm-to-arm collisions |
| 2026-08-19 | FEA turret + wrist | SF 77 (turret) to 417 (yoke) — no structural concern |
| 2026-08-19 | shaft/bearing fit | one interface Ø42/6806/Ø30 verified across all six joints |
| 2026-08-19 | servo clearance | **wrist parts had NO servo pockets** — J4 grown Ø46→Ø56, J6 to a micro servo |
| 2026-08-19 | wrist servo sizing | J4/J5 need 10.1 kgf·cm, J6 needs 3.0 — ST3215 is 3–10× oversized |
| 2026-08-19 | wobble bounded | c is bearing internal clearance: CN 0.16–0.65 mm; specify C2 → 0.03 mm |
| 2026-08-19 | fastening audit | **no servo case fixings, no horn patterns, no cable exits anywhere** — all added |
| 2026-08-19 | servo hole dims | ST3215.stl is an outer shell with no holes modelled — 4 params are PLACEHOLDERS |
| 2026-08-19 | FEA re-run | pockets turned J4 into an open C-section; re-checked at **servo STALL**: SF 41/21/105 |
| 2026-08-19 | J4 load case | was lateral force; corrected to TORSION about the roll axis |

---

## Open / unverified

- J1, J4, J5, J6 parts are **first-pass**: no FEA, no fit check against the shaft, servo horn clearance and cable routing unchecked


- **Wobble still never measured.** Now bounded at 0.16–0.65 mm (CN class) by bearing spec
  rather than by an unjustified assumption, but the dial-indicator test is still the
  single most valuable open number
- J6 micro servo is a REQUIREMENT (≥3 kgf·cm in 29×13×30 mm), not a sourced part
- **Servo mounting hole positions and horn BCD are PLACEHOLDERS** — measure the real
  servo and correct the four values in `cad/params.py`

- J2/J3 continuous-torque shortfall needs a counterbalance decision

- Gripper not designed; tool flange is the interface only
- **Horizontal-table tracing does not work** — needs wider J2/J5 travel or a wrist redesign
- Servo mounting-hole and horn-bolt patterns are PLACEHOLDERS; measure a real ST3215
- "Space grade" is geometry-compatible only: PLA, hobby servos and wet-grease bearings all fail vacuum/thermal
- Residual 4 % base collisions need a planner-level collision check, not joint limits
- Exploded-view offsets still tuned for the old 3-DOF assembly; parts barely separate
- Renders are depth-sorted triangles, not a real renderer — use Blender/Fusion for presentation


---

## End goal

Sine tracing with the pen normal to the surface (Rsine / mycobot thesis). That is a 5-DOF task minimum — J1 gives the writing sweep, J5+J6 give pen orientation, J4 avoids wrist singularities. All six now exist in CAD.

### 2026-08-20 — shaft material corrected, mass budget error found

User questioned the steel tube on weight grounds. Investigation found the BUY list
specified Ø30 × 5 steel (222 g each) while quoting "~93 g", and the pre-print gate
counted only 2 shafts against 12 bearings (= 6 pairs = 6 joints = 6 shafts). Six steel
tubes would have been 1332 g, taking the arm to 2270 g against a 1.2 kg limit.

Load analysis of the shaft (4 load paths):
  torque 0.55 MPa SF 32 | bending 0.57 MPa SF 104 | preload thread 16 vs 18 MPa MARGINAL
  | press fit creep — plastic relaxes, fit fades

Printing rejected on the preload thread and the creeping press fit, NOT on strength.
Both failures are local, so the fix puts metal only at those two places.

Spec now: AL6061 Ø30 × 2 wall × 72, 34 g each / 205 g for six, total 1144 g.
  - M5 × 90 through-bolt down the Ø26 bore + nyloc replaces the M5 tapped end
  - Ø3 roll pin (double shear 4241 N vs 196 N, SF 22) replaces grub screws + D-flat
  - tube OD must be measured on arrival: extrusion tolerance ±0.10-0.20 is 10-20x
    looser than a bearing seat needs. Loctite 603/638 covers gaps to 0.10 mm.

Gate rerun: 55 passed, 0 warnings, 0 failures. Mass line now derived from params.py
with an assertion tying shaft count to bearing count.

### 2026-08-21 — horn adapter added; mass model corrected; budget fixed at 1450 g

- **`cad/horn_adapter.py`** (6 off, 7.3 g each at 0.90 fill). Closes the torque path
  servo horn → adapter → roll pin → tube → clamp → link, which did not exist: the old solid
  shaft carried its own horn shoulder and lost it when the shaft became a bought tube.
  Reuses the tube's existing pin hole. Sized on stall 2.94 N·m — horn screws SF 4.6 (binding),
  roll pin SF 7.3, hub torsion SF 40.
- **Mass model corrected.** 0.55 infill factor was being applied to hollow-modelled parts,
  discounting the hollowing twice and hiding ~240 g. `FILL = 0.90`. True mass **1437 g**,
  not the 1215 g previously reported.
- **Budget.** 1200 → 1300 → **1450 g hard ceiling**, user decision. Mass is now a HARD gate
  failure, not a warning. Headroom 13 g.
- Base foot lightened (underside recess, plate 7 → 5.5 mm): −21 g.
- All three drawing sets now carry the adapter: iso 13 pp, 3-view 13 pp, verification 10 sheets.
- Gate: 58 passed, 0 failures. Geometry audit: 52 features verified, 0 outstanding.

### 2026-08-21 (later) — sine collision found and fixed, wrist bearings, workspace

**The sine path was not collision-free.** Exact-mesh check on the 240 SOLVED waypoints
(not the random joint sweep) found 72/240 colliding — base ↔ upper arm, 1.27 mm
penetration at z = 50.0, the arm grazing the top rim of the pedestal.
Fix: `Z_CENTER` 0.20 → **0.22**. Result **0/240 collisions AND 0.194 → 0.014 mm rms**,
because the IK stops working against the J2 limit. Strictly better on every metric.
Also narrowed `PED_D_TOP` 80 → 72 (−7 g) and added a collision-aware IK seed bank; neither
was sufficient alone.

**Wrist bearings 6806 → 6706** (Ø37 × 4), J1/J2/J3 unchanged. Loads computed: worst wrist
case is SF 103. Same 30 mm bore, so tube/clamp/adapter untouched. Bearings 268 → 176 g,
wrist parts +18 g, **net −75 g**. Two part numbers now — BUY.md rewritten to lead with that.

**Mass model corrected earlier the same day** (0.55 → 0.90 fill; the 0.55 was discounting
hollow-modelled parts twice and hid ~240 g). **Arm is 1365 g against a 1450 g hard ceiling,
85 g headroom.** Gate fails rather than warns on mass.

**Horn adapter** added (6 off) and a 2-body defect in it fixed — the grip-flat cut used
`centered=(True, False, False)`, which grew the box in +Y only and sliced a 0.20 cm³ sliver
loose on the −Y side. Caught by the gate's "is ONE body" check.

**New tools:** `check_sine_clear.py`, `check_bearing_fit.py`, `cad/bearing_6806.py`,
`verify_all.py` (5 rounds, new sweep seed each), `workspace.py`.

**Verification:** 5 rounds all clean. Gate 60 passed / 0 warnings / 0 failures. Geometry
audit 52 features / 0 outstanding. Virtual bearing fit: all 10 pockets light press.
Workspace: 190 litres reachable, 20 % workable with the pen normal.

### 2026-08-21 (evening) — playback continuity, RViz model, URDF mass

**Playback was discontinuous.** `sine_node.tick()` wrapped the last waypoint straight to
the first: **J4 jumped 43.30°, J1 32.2° in one tick — 21× the largest normal step — and
the tool teleported 139.8 mm.** Replaced with **ping-pong** playback (forward, then back
along the same waypoints, as Rsine does), plus a `loop_mode` parameter (`pingpong` default,
`wrap` retained). Verified live at 60 Hz: largest step **2.094°**, zero steps above 5°.

**RViz showed the wrong robot — two faults.**
1. The launch files loaded `arm450.urdf`, which carries box/cylinder primitives, so RViz
   rendered a stack of blocks. Both launch files now load `arm450_meshes.urdf`.
2. `generate_urdf_meshes.py` emitted `package://arm450_design/meshes/...`. **`arm450_design`
   is the design directory, not a ROS package**, so all 7 meshes failed to resolve with no
   error visible in the viewer. Fixed to `package://arm450_description/`. 7/7 resolve.

**URDF mass was wrong twice over.**
- `generate_urdf.py` carried hand-set LINK-ONLY masses — no servos, bearings or shafts.
  link4 was 173 % light; the total said 0.765 kg for a 1.365 kg arm. Now derived from
  `volumes.json`.
- `arm450_meshes.urdf` took its inertials straight from mesh geometry, so it was plastic
  only at 0.784 kg. Non-printed mass is now added as a lumped mass at each link origin —
  an approximation that gets mass and gravity torque right and slightly understates
  rotational inertia, stated in the code.
- **A third defect surfaced from comparing the two totals:** the model allocated ONE
  bearing per link where every joint runs a PAIR — 4 × 6806 instead of 6, 44.8 g light.
  Fixed; the URDF now totals **1.365 kg, matching the mass gate exactly.**

**State:** gate 60 passed / 0 warnings / 0 failures. Geometry audit 52 features / 0
outstanding. 3 verification rounds clean. Runtime verified end to end: robot_state_publisher
loads the mesh URDF with no errors, `tf2_echo base_link tcp` → [0.300, 0.043, 0.194].

### 2026-08-22 — wrist self-collision investigated and fixed

**It was a pure J5 fold.** Mapping the wrist joint space showed **every J4 row identical** —
J4 has no influence. Bisecting on real meshes put the collision-free J5 range at
**−94.2° … +52.7°** against a declared ±110°: 57° optimistic on the + side, 16° on the −,
and asymmetric because the wrist is (the servo pocket sits on one side). 5° past the edge
the penetration is 5.87 mm — a real overlap, not a graze.

Fixed by declaring `joint5` **−91° … +49°** (measured range, 3° margin). No geometry change.
Sine unaffected: uses +40.4…+48.0°, re-solves at 0.014 mm rms, 0/240 collisions.

**Second defect this exposed:** `interference.py` carried a HARDCODED copy of the joint
limits and never read the URDF, so after the narrowing it kept sampling poses the arm can
no longer reach and reporting them as collisions. Now reads the URDF.

**Result: random-pose collisions ~30 % → ~12 %, and `j4housing ↔ j6output` is gone.**
What remains is `base ↔ j4housing` and `turret ↔ fore-B` — the arm folding onto its own
base, which every arm does and no geometry change removes.

Also added `workspace.figure_3panel()` → `figures/workspace_arm450.png`, the three-panel
reachable-workspace figure in the same layout as the myCobot study, with the sine demo
overlaid. ARM-450 reaches **0.360 m** horizontally vs the myCobot 280's 0.30 m.

### 2026-08-22 — simulation made hardware-ready; staged preflight; GO

**Hardware readiness** (three gaps that only bite on real servos):
- **Approach ramp.** The node published waypoint 0 on its first tick — invisible in RViz,
  a full-speed slam on hardware. Now a cosine ramp from `start_pose` over `approach_time`
  (default 3 s), zero velocity at both ends.
- **JointTrajectory topic.** `/joint_states` is a visualisation stream a controller will
  not follow. The solved path is now published once as a 240-point JointTrajectory on
  `/arm450/trajectory`, latched TRANSIENT_LOCAL, velocities by central difference.
- **Velocity check** against the actuator at startup: 0.91 rad/s demanded vs ~2.3 rad/s for
  a loaded ST3215. Over-rate does not error — the servo lags and the traced path silently
  stops being the solved path — so the node warns and names the highest safe rate.

**New `creep_fatigue.py`** — the two failure modes a static check cannot see. Working
stress is 0.38 MPa, a stress ratio of 0.0064; fatigue life 4.3e28 cycles. Neither is
limiting, because the arm is stiffness-driven, not strength-driven. Creep needed an honest
correction: the absolute strain is tiny (0.040 %/year) but it is several times the elastic
strain, and the Findley fit is being used two orders of magnitude below its calibration.
Actionable outcome: park the arm folded when idle, not extended.

**New `preflight.py`** — seven staged gates with a single verdict: design check, FEA,
creep+fatigue, stiffness, URDF, path tracing, simulation readiness. Exits 0 on GO.

**RESULT: 21 checks, 7 stages, 0 failures — GO FOR PRINTING.**
Worst FEA SF 23.0 · compliance 0.098 mm · path 0.014 mm rms, 0/240 collisions ·
URDF mass 1.365 kg matching the gate · mass 1365 g of 1450 g.

---

## 2026-08-22 — the docking interface did not work, and three drawings lied

**Shop drawings for the six end-effector parts** were the outstanding item: they existed in
CAD and in `END_EFFECTORS.md`, but not on a dimensioned sheet. Adding them to `draw_iso.py`
and `draw_3view.py` meant looking hard at the geometry, and the geometry did not survive
it.

### `tool_dock` had no latch

The three latch lugs sat **5.5 mm clear of the bore they were meant to grow out of**,
inside the capture cone at a height where it had already opened to Ø25.8. The part exported
as **four solids**: the probe and three loose 19 mm³ crumbs. A CadQuery `.union()` of
shapes that do not touch succeeds and returns a compound, so nothing complained — not the
render, not the drawing, not the mass budget.

### `dock_target` had cut its own spigot in half

The capture groove was cut from r3.10 to r6.40 through a wall running r4.00 to r5.65 — a
**3.30 mm groove in a 1.65 mm wall**. That severs; the three entry slots then chopped the
severed tip into three loose arcs. Also **four solids.**

### And they could not have mated anyway

The capture cone was **16 mm deep, the spigot 10 mm tall.** The cone mouth grounds on the
Ø34 flange while the tip is still 6 mm short of the throat. Probe and target collide at
every insertion depth and every roll angle. Neither part is at fault on its own; the defect
lives in the relationship, which is why single-part inspection could never have found it.

### Fixes

| was | now | why |
| --- | --- | --- |
| throat Ø12 | **Ø16** | gives the spigot a 2.45 mm wall at the groove root |
| mouth Ø30 | **Ø34** | keeps ±9 mm capture at the wider throat |
| cone 16 mm deep | **9 mm** | a lead-in must not out-reach the post it guides |
| spigot 10 mm | **21 mm** | reaches the latch with 2 mm of standoff |
| lugs floating | **grown inward from the throat wall, 1 mm overlap** | real material to fuse to |
| flange 18 mm | **10 mm** | it was never doing anything |

`tool_dock` 38 → **31 mm tall, 48.0 g**; `dock_target` 28 → **31 mm, 12.6 g**.

### The mate is now simulated, not asserted

`check_tool_fit.py` drives the exported probe mesh onto the exported target mesh:

| state | expected | result |
| --- | --- | --- |
| 6 mm short, slots aligned | clear | clear |
| seated | clear | clear |
| rolled 30° to latch | clear | clear |
| latched, pulled 2 mm | **must catch** | catches |
| rolled back, withdrawn | must release | releases |

Capture envelope is **measured** by sweeping the probe sideways until it fouls:
**±9.75 mm** at the mouth, 7× the ~1.4 mm the arm can make. It also counts
`len(shape.Solids())` for all six tool parts and fails on anything but 1.

`cad/end_effector.py` **now exports itself.** It never had a `__main__`; the six parts had
been written once by hand, so every edit to that file since had been silently absent from
the STLs the drawings and collision checks read.

### Two documentation defects, found the same way

- Three three-view sheets carried a bold red **NO Ø42.00 BEARING POCKET** banner from a
  hardcoded list of part names. Those pockets were fixed on 2026-08-21. The banner now
  reads the count out of the STEP, and shows green with the count when present.
- Every isometric sheet quoted mass at **55 % fill** while the budget and the gate use
  **90 %** — under-quoting every part by 39 %. `mass_of()` now takes `params.MASS_FILL`.
- `TOOL_REACH` in `workspace.py` was hardcoded; the dock entry (43 mm) went stale when the
  cone shortened. It is now measured off `assemble.build()`. Real figure: **36 mm.**

### State

### Verification re-run with and without a tool; paper and deck written

**`verify_configs.py`** runs the whole load suite across five payload configurations —
bare, pen, gripper, gripper+225 g, dock — from one driver, so the "with gripper" answer
cannot be a different vintage from the "bare" answer.

The point is not the extra mass. Every earlier analysis used 300 g at the TCP, which
bounds a 75 g gripper comfortably. The point is the **lever arm**: a tool moves the load
42 mm along the tool axis, and that is what sizes J2/J3 and sets compliance at the working
point. **75 g on a 42 mm stick is not the load case 75 g at the flange is.**

| config | J2 N·m | σ MPa | SF | δ mm | creep %/y | cycles |
| --- | --- | --- | --- | --- | --- | --- |
| bare | 1.55 | 0.197 | 305 | 0.036 | 0.0159 | 3.9e36 |
| pen | 1.61 | 0.208 | 288 | 0.041 | 0.0172 | 1.8e36 |
| gripper | 1.85 | 0.257 | 234 | 0.054 | 0.0230 | 1.1e35 |
| gripper + 225 g | 2.74 | 0.437 | 137 | 0.098 | 0.0486 | 8.0e31 |
| dock | 1.79 | 0.245 | 245 | 0.051 | 0.0216 | 2.0e35 |

**30/30 criteria pass.** The re-implementation cross-checks: compliance in the
gripper+225 g case comes out at 0.098 mm, matching `compliance_budget.py`'s published
figure for 300 g exactly.

The finding worth keeping: **backlash beats structural deflection by ≈20× in every
configuration**, so the conclusion "this arm is servo-limited, not structure-limited" is
invariant to whether a tool is fitted. Nobody should spend print time stiffening it.

Gate is now **27 checks**.

**`ARM450_PAPER.pdf`** (15 pp) — the work as a paper: requirements, architecture,
kinematics, end effectors, the verification method and its results, a comparison against a
space-grade equivalent, the thirteen defects the gate caught, limitations, conclusions.
§9 is **[AWAITING HARDWARE]**: seven measurements, each with a prediction and a stated
falsification condition, and a blank for the number. Written before the test on purpose —
a prediction recorded beforehand is evidence; one recorded afterwards is not.

**`ARM450_SLIDES.pdf`** (20 slides, 16:9) — generated by `make_slides.py` from the same
modules, so no number on a slide is a third copy. The generator prints a warning when a
bullet list overruns its slide, which caught five overflowing slides that would otherwise
have shown up on the projector.

**Space-grade comparison**: of sixteen subsystems, **3 survive unchanged** (kinematics,
joint architecture, fastening scheme), **2 need rework**, **11 must be replaced**. The
material is the wall — and re-made in Al 6061-T6 the same geometry is ≈1.13 kg, *lighter*
than printed, and about 10× stiffer, so the swap is an improvement that costs money rather
than a compromise.

### A generated command reference — and five aliases I deleted by accident

`ARM450_COMMANDS.pdf` (9 pp): every alias, every raw ROS 2 equivalent, the
`plan_sine.py` options, and a troubleshooting table. **It is generated** —
`make_commands.py` parses the alias table out of `arm450_aliases.sh` and the
trajectory options out of `plan_sine.py --help`. A hand-typed command sheet is
exactly the document this project has now watched go stale three times, so this
one cannot: `a450cmds` rebuilds it.

**Two things it exposed.**

`build_pdf.py` stamped the literal footer *"ARM-450 · stress & stiffness
analysis"* on **every PDF it has ever produced** — right for the one report it
was written for, wrong on the other seventeen. The footer now takes the
document's own H1. All 18 PDFs rebuilt.

And while restructuring the aliases I replaced a slice of the file that ran from
a comment to `a450help() {` — which silently ate **`a450gate`, `a450flight`,
`a450cad`, `a450docs` and `a450open`**. All five restored.

**The audit that was supposed to catch that did not**, and the reason matters:
it tested each alias by re-typing the command the alias was *supposed* to run,
so it passed with the alias itself deleted. It now checks that every name is
`type -t`-defined first, and executes the alias by name inside a subshell that
sources the file. Also: **bash disables aliases in non-interactive shells**, so
the harness needs `shopt -s expand_aliases` or everything silently fails for the
wrong reason. 50 checks, all passing; kept as `audit_aliases.sh`.

> Testing what a thing is meant to do, rather than the thing itself, is not a
> test. It is a restatement of the intention.

### The sine was traced by the flange, not by the tool

Spotted in RViz: the yellow curve sat at the J6 flange while the gripper fingers stuck out
42 mm past it. On hardware that is not cosmetic — the flange would meet the board while the
fingers were already 42 mm through it.

**The trajectory drives the TCP, which is the J6 tool face.** Everything about that was
correct for a bare flange and quietly wrong the moment a tool went on.

Measured, then compared two fixes on the number that matters — tip position against the
intended sine:

| | board at | joint step | tip error |
| --- | --- | --- | --- |
| **flange path, board moved out** | **342 mm** | **2.09°** | **0.055 mm rms · 0.834 max** |
| tip-driven IK, board fixed | 300 mm | 2.87° | 0.087 mm rms · 1.019 max |

**Moving the board wins on every axis**, and it is free: the joint trajectory is byte-for-
byte the one already verified collision-free, so the posture, the joint loads and the
clearance margins are all unchanged. Only the board moves.

Both are now available. `plan_sine.py --tool gripper` reports the board distance out loud;
`--tip-ik` drives the tip instead, for a board that cannot move.

**Two things had to be fixed to make `--tip-ik` work at all.** `ik()` scored its result
against the bare TCP, so every tip-offset solve reported ~42 mm of error — the tool length —
and the acceptance test and collision-seed filter rejected perfectly good poses. And at
the shipped `w_ori = 0.05` the solver traded **21° of tool tilt** for position error,
because with a tool fitted a tilt moves the tip; position and orientation stop being
independent. It needs `w_ori 0.2` and the trace raised to 260 mm.

**The path marker now follows the tip** — verified at 0.00 mm from the furthest point of
the tool mesh, not just eyeballed. A third RViz config, `arm450_side.rviz`, looks along −Y,
because perspective in the other two makes the curve look like it passes through the
gripper when it does not.

Re-verified with the regenerated trajectory: **gripper 0/60, dock 0/60.**

Two more stale aliases found while testing: `a450reset` still carried the old
`--z-center 0.20` (the height that collided with the base pedestal, fixed days earlier),
and `a450urdf` rebuilt only the box-primitive URDF, leaving the mesh URDF RViz loads
stale — the exact mechanism behind the earlier "RViz is showing the wrong model".

### The URDF had no tool on it

Asked directly whether the design had been run in RViz *with* the end effector, the answer
was **no** — and worse, it could not have been. `arm450_meshes.urdf` had seven links,
`base_link` through `link6`, and stopped at a bare J6 face. The sine path had been
re-verified collision-free with a gripper fitted, the workspace recomputed for it, the
reach measured off the assembly — and every one of those numbers came from `assemble.py`,
the CAD and collision assembly. **None of it was in the model RViz loads.** Every RViz run
in this project has shown an arm with nothing on the end of it.

`tool` is now a fixed link on `link6`, built the way every other link here is built: the
real STLs at their true placement, combined into one mesh, mass and inertia from the exact
STEP volumes. Placement comes from `assemble.build()` rather than being re-derived, so what
RViz draws is the geometry the collision check cleared. `tool_tip` follows it at the
working point. Selectable: `EMIT=1 TOOL=dock python3 generate_urdf_meshes.py`.

Gripper 74.6 g, tip 42 mm past the J6 face. Dock 62.4 g, 36 mm.

**Stage 5 needed fixing with it.** Its mass check summed *every* link with an inertial, so
the moment the tool became a link the 1.365 kg comparison would have broken — a 75 g
payload silently failing the check that ties the model to the mass budget. It now sums the
arm links only and reports the tool separately, plus a new check that the tool link is
present at all.

Run and captured: `figures/rviz_gripper_wide.png` / `.webm` and
`figures/rviz_gripper_close.png` / `.webm`.

Two incidental fixes fell out of actually running it:

- **RViz opened at 728 × 604** — its built-in default, with the Displays panel eating half.
  A 45 mm gripper on a 450 mm arm is invisible at that size. The config now carries a
  `Window Geometry` block at 1500 × 900, and a second config `arm450_tool.rviz` parks the
  camera on the wrist.
- **RViz would not start at all** from a terminal inside the VS Code snap:
  `libpthread.so.0: undefined symbol: __libc_pthread_init, GLIBC_PRIVATE`. The cause is
  **`GTK_PATH`**, which the snap points at its own GTK module directory; RViz's Qt/GTK
  integration loads a module from there and it drags in snap glibc. `unset GTK_PATH` is the
  entire fix — bisected, and the snap entries in `LD_LIBRARY_PATH`, `PATH` and `LOCPATH`
  turn out to be red herrings. (I said it was `LD_LIBRARY_PATH` at first; that was wrong.)
  Alias `a450unsnap`. A plain Ubuntu terminal never has the problem.

**450 mm settled.** Asked whether the 450 mm was a hard stowage envelope or a
target for the arm alone, the user accepted **492 mm with a gripper fitted**. So 450 mm
binds the arm — base to the J6 tool face — and a tool is payload beyond it. Recorded as
`params.SYSTEM_REACH_MAX = 495` and checked in stage 8, so a later and longer tool cannot
push the system past what was agreed without the gate saying so.

**Pre-print gate: 27 checks, 8 stages, 0 notes, 0 failures — GO FOR PRINTING.**
Stage 8 is now **29/29** (was 15/15). Workspace with a gripper fitted: 492 mm reach,
262 L swept.

---

## 2026-08-25 — Craig DH, velocity-propagation Jacobian, ikpy cross-check

Built the kinematics a second time in the user's own convention — modified/Craig
DH with a velocity-propagation Jacobian — as an independent derivation rather
than a restatement of the URDF.

**The table has two numbers that are not what they look like.** Taking the joint
axes from the URDF at q = 0 and computing common normals: every axis passes
through the base Z line, so every `a` is zero except **a₂ = 119** between the two
parallel pitch axes. And **d₄ = 181, not 119** — frame 3's origin sits at z = 209
and frame 4's at z = 390, so the offset along Z₄ is 119 + 62. Writing 119 there,
which is the obvious link length, puts the tool **193 mm** out. That was this
file's first answer.

**Three implementations sharing no code now agree to 2 × 10⁻¹³ mm:** the Craig-DH
FK written here, the URDF chain the project already ran on, and `ikpy`. The
propagated Jacobian matches finite differences to 1.8 × 10⁻⁵, and both IK solvers
converge — 1.6 × 10⁻¹¹ mm median for the DH one. **7 of 7 checks pass.**

> Agreement between the first two proves the DH table. Agreement with ikpy proves
> the first two do not share a mistake, which is the failure a self-written
> cross-check cannot catch.

**ikpy does not import on this machine**, and it is not ikpy's fault: sympy
stringifies numpy scalars, numpy 2 changed their repr to `np.float64(1.0)`, and
sympy then cannot parse its own input. `check_ikpy.py` shims the converter
through `float()`. Nothing to do with the arm — but reporting "ikpy unavailable"
would have quietly dropped the only outside opinion in the check.

### Also: the sine trace on a horizontal plate does not work, and now we know why

Swept 12 plate positions. Best is **11.7 mm rms** against **0.020 mm** on the
vertical board — 585× worse. **J2 is hard against its +115° stop:** to reach out
over a table and tip the tool down, the shoulder runs out of travel. A 90° bent
tool adapter was tried and improved it to 8.1 mm, at which point **J2 and J5 both
saturate**. It is a joint-range limit, not a solver or tool problem, and it traces
back to J5 being narrowed from ±110° to −91°/+49° to stop the J4 housing striking
the J6 body.

### And the missing chamfers

`BRG_CHAMFER = 0.5` has been in params, on the drawings and in the docstrings
since the design was written. A STEP audit for **conical** faces found **zero** in
every part with a bearing pocket — `link_shell.py` promised it in its docstring
and never called it; `fit_coupon.py` called `.chamfer()` inside a `try/except`
that threw every time. **15 lead-in chamfers now cut**, as cones rather than
`.chamfer()` calls. The cylindrical bore is now 6.5 mm of the 7 mm seat, which is
normal — the bearing still grips 93 % of its race and the fit check still reads
light press.

Dimensional audit: **49 checks, 0 failures.**


---

## 2026-09-01 — the fit coupon tested only half the bearings

Six 6706 bearings arrived and would not fit the coupon. The bearings are correct.
The coupon was wrong.

The wrist moved from the 6806 to the smaller **6706 (30 × 37 × 4)** on 2026-08-21,
and that change was followed through into `wrist_integrated.py`, `check_bearing_fit.py`,
`dim_audit.py`, `generate_urdf.py`, `preprint_check.py` and `BUY.md` — into every
place except the one part whose entire purpose is to measure a bearing fit before
anything else is printed. The coupon kept its three Ø42.00 stations and never gained
a Ø37.00 one, so **six of the arm's twelve bearings had no fit test at all**.

The failure presents as a hardware fault. A 6706 offered up to a Ø42 pocket has
2.5 mm of radial slop and drops straight through, which reads as the wrong bearing
having been delivered. `BUY.md` had even written the warning down — *"a 6706 dropped
into a Ø42 pocket has 2.5 mm of radial slop and will look almost right"* — and the
coupon still made exactly that mistake unavoidable, because it offered no other hole.

**Fixed.** The coupon now carries two rows: Ø42 × 7 deep for the 6806 (J1/J2/J3) and
Ø37 × 4 deep for the 6706 (J4/J5/J6), each stepped ±0.05 mm, each with its own lead-in
chamfer cut as a cone, each labelled with raised numerals, dot counts and the bearing
part number on the strip. 150 × 139 × 12 mm, 70 g, ≈2.3 h — up from 27 g and 0.9 h.

Three further defects fell out of the fix:

- `audit_parts.py` checked the three Ø42 pockets and nothing else. It now checks both
  rows' diameters, both seat bores and **both pocket depths** — the depth check is what
  would have caught a Ø37 pocket cut 7 mm deep instead of 4.
- `draw_iso.py` placed its pocket callouts at `y = 0`, which was the main row's centre
  only while the coupon had one row. The second row moved the part centroid and every
  leader would have pointed at bare plate. The row centres are now computed once in
  `fit_coupon.py` and imported, rather than assumed twice.
- `BUY.md` and `DRAWINGS_2D.md` embedded `figures/cad_coupon.png`, an orphan produced
  by no current script and last written 2026-08-20. Both PDFs were showing a picture of
  the single-row coupon beside text describing the two-row one. Repointed at the
  generated drawing.

Part audit after the change: **59 ok, 0 need attention.**

This is the same class as the missing chamfers and the vacuous wall check — a
parameter changed in the model and the thing that was supposed to verify it was
never told. What makes this one worse is that the unverified item *was the verifier*.
