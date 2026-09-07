# ARM-450 — Why the Design Changed

**From a printed arm that failed in service, to ARM-450, and how both relate to a space-grade manipulator.**

Revision 2 · 2026-09-02 · every figure derived in the supporting documents listed in §7

---

## 1. What this report answers

Three questions, in order:

1. **What was the previous design, and what did it actually do?**
2. **Why was it changed, and what did the change buy?**
3. **How do the old arm, ARM-450 and a real space manipulator compare** — where they are
   the same, and where they are not?

Everything here is measured or derived. Where a number is an assumption rather than a
measurement, it says so.

![ARM-450 detailed assembly](figures/assembly_detail.png)

---

## 2. The previous design

A printed 6-DOF arm, exported from Fusion 360, built and run. It broke. Three faults were
diagnosed, and all three were measured from the geometry rather than guessed at from the
symptoms.

![The previous arm](figures/existing_assembly.png)

### 2.1 The servo mounts snapped

The mounts were sized for the torque the arm carries in normal motion — **2.08 N·m** at the
shoulder. But a servo does not deliver its operating torque into its own mount. In a
collision, on a commanded step, or when a joint hits its limit, it delivers **stall torque**:
2.94 N·m for an ST3215, 4.90 N·m for an ST3250.

The 4 mm bracket runs at **17–95 MPa** depending on where it grips, against a realistically
sustainable **~9 MPa** for printed PLA under repeated load. It fails under every assumption
in that range, and it did.

There is a second trap inside the first: fitting a *stronger* ST3250 multiplies mount stress
**2.36×** while changing the load the arm actually carries by nothing at all. A bigger motor
makes the structural problem worse.

### 2.2 The joints wobbled, and tuning could not fix it

Each joint ran on a **Ø42 × 3.7 mm thrust ball bearing**. A thrust bearing carries axial
load — its balls run between two flat races, so the joint is free to **tilt**. A robot
joint's dominant load is a **bending moment**: 2.08 N·m at the shoulder from everything
outboard on a long lever.

Angular play follows θ = 2c/d. With effectively no bearing spacing (d ≈ 5 mm) and 0.2 mm
clearance, that is **28.9 mm of wobble at 360 mm reach** — larger than every other error
source in the arm combined.

The oscillation that came with it was mechanical, not a control problem. Clearance in a
position-controlled joint is a **dead zone**: the servo turns and nothing moves until the
slack takes up, then it moves suddenly. A feedback loop pushing against a dead zone produces
a limit cycle. Lowering the gain makes the arm sluggish and the oscillation smaller — never
absent.

### 2.3 A revision opened a hole in the workspace

Revision 1.1 lengthened one link and not the other: 195.1 mm joint-to-joint against 97.9 mm.
The reachable region of a two-link chain is an annulus whose **inner radius is |L2 − L3|**,
so that split created a **Ø194 mm dead zone directly in front of the robot** — and the chain
totalled 453 mm, over the 450 mm limit it was meant to meet.

The original links were 97.9 / 97.9: equal, and with no dead zone at all. The revision broke
something that had been right.

---

## 3. Why the shift

The three faults are not unrelated. Each is the same kind of error — **a design sized
against the wrong quantity** — and each has a general rule behind it.

| the fault | what it was sized against | what it should have been sized against |
| --- | --- | --- |
| Mounts snapped | the torque the arm *uses* | the torque the servo *can deliver* |
| Joints wobbled | the shaft diameter | the **direction** of the load |
| Dead zone | one link at a time | the **difference** between the links |

That is the shift. Not "make it stronger" — the previous arm was not weak in the places it
broke, it was strong against the wrong load. ARM-450 changes what each part is designed
against:

> **Wherever an actuator can drive its own structure to failure, the actuator's limit is the
> design load.** Gravity torque sets what the servo must do; stall torque sets what the
> mount must survive.

> **Match the bearing to the load direction, not to the shaft diameter.** Moment stiffness
> scales with bearing **spacing squared** — worth far more than bearing size or count.

> **For a two-link arm, L2 = L3 eliminates the dead zone, and it is nearly free.** Shoulder
> torque is almost flat in the split, because the dominant term is the payload at a fixed
> reach.

---

## 4. What changed, and what it bought

| item | previous | ARM-450 | benefit |
| --- | --- | --- | --- |
| Mount sizing load | 2.08 N·m operating | **stall, 2.94 / 4.90 N·m** | the failure mode that broke the arm is designed out |
| Joint bearing | Ø42 × 3.7 thrust washer | **6806 pair, 40 mm apart** | wobble **28.9 mm → 0.65 mm** |
| Wrist bearing | as above | **6706 pair** | **−92.6 g**, no loss of moment stiffness |
| Joint preload | none | **M5 × 90 through-bolt** | removes the dead zone that caused the limit cycle |
| Link lengths | 195.1 / 97.9 mm | **119.0 / 119.0 mm** | Ø194 mm dead zone **eliminated** |
| Chain total | 453 mm | **450.0 mm** | inside budget |
| Bending axis | about the section width | **about its depth** | load is transverse to the link |
| Section depth | 29.0 mm | **50.0 mm at the boss** | stiffness ∝ depth³ |
| Link construction | single shell | **split shell, tongue-and-groove seam** | prints flat, no supports, no bridging over bores |
| Open-section penalty | applied | **withdrawn** | seam bolts close the section |
| Backlash budget | J2, J3 only | **all six joints** | the error budget is now complete |
| Tool interface | bolted | **three-lug bayonet, 30° twist** | tool change without three blind M3s under a wrist |

![Revision comparison](figures/revision_compare.png)

### 4.1 The benefits, stated as results

| | previous | ARM-450 |
| --- | --- | --- |
| Joint wobble at full reach | 28.9 mm | **0.65 mm** |
| Workspace dead zone | Ø194 mm | **none** |
| Mount stress vs allowable | 17–95 MPa vs ~9 MPa — **fails** | worst p99 safety factor **23.0** |
| Tip deflection under load | not analysed | **0.197 mm** against a 0.30 mm limit |
| Chain length | 453 mm (over) | **450.0 mm** |
| Vertical sine trace | not achievable | **0.014 mm rms**, 240/240 waypoints clear |
| Horizontal reach | — | **360 mm** (myCobot 280: 300 mm) |
| Vertical surface drawable | — | **52.3 %** (myCobot 280: 57.9 %) |

The kinematics were derived by hand as a modified (Craig) DH table and then checked against
two independent routes — the URDF chain and `ikpy`, an outside package. Agreement is
**2.17 × 10⁻¹³ mm**. Three routes cannot share one mistake.

### 4.2 The honest limit

The structure is no longer what limits accuracy, and has not been for some time. **Backlash
in the hobby serial servos accounts for about 98 % of the predicted tool error** — 2.25 mm
of a 2.25 mm total, against the structure's 0.197 mm. It is also the one significant
quantity in this report that has not been measured. Building the arm tests that assumption;
it does not primarily test §4.1, which has been checked three ways.

---

## 5. Old arm, ARM-450, and a space-grade manipulator

Sixteen subsystems were compared against a flight equivalent. **Three survive unchanged, two
need rework, eleven must be replaced.**

![Space-grade comparison](figures/spacegrade_compare.png)

### 5.1 Where all three are the same

| | why it transfers |
| --- | --- |
| **6R serial kinematics** | A six-revolute chain with this layout is unaffected by what it is made of. The URDF, the IK and the workspace transfer directly from bench to flight. |
| **One bore, one shaft, one bearing family per joint** | Good practice at any grade. Only the part numbers and the lubricant change. |
| **Bolt patterns and load paths** | Flight versions add locking compound, staking and vented screws — in the same places. |

The old arm shares the first of these and fails the second: it had the serial architecture
right and the joint architecture wrong.

### 5.2 Where ARM-450 and space-grade diverge

| | ground manipulator | space manipulator |
| --- | --- | --- |
| Gravity | dominates sizing; the arm must hold itself up | ~0 g. Sizing is driven by inertia and dynamics |
| What limits payload | actuator torque against gravity | **reaction on the base** — the arm moves the spacecraft |
| Base | bolted to a rigid floor | free-floating; momentum must be managed |
| Structure | stiff enough not to sag | stiff enough not to **oscillate** — no damping in vacuum |
| Thermal | 20 ± 15 °C | −120 to +120 °C; CTE mismatch drives joint clearances |
| Lubrication | wet grease | dry film (MoS₂) or PFPE — wet grease outgasses and creeps |
| Materials | anything | TML < 1 %, CVCM < 0.1 %; no trapped volumes |
| Radiation | none | TID-rated electronics, latch-up immunity |
| Backlash | tolerable | often unacceptable — no operator in the loop |
| Repair | trivial | none. Single-fault tolerance or redundancy |
| Qualification | "it works" | vibration, shock, thermal-vac, EMC, life test |
| Control | position | often impedance or force — contact dynamics with a free target |

**The four that rule ARM-450 out as a flight article:**

1. **The material is the wall.** PLA's glass transition is ~60 °C; a sun-facing surface in
   LEO exceeds it, and it outgasses. Re-made in Al 6061-T6 the *same geometry* is
   **≈1.13 kg — lighter than printed — and about 10× stiffer.** The swap is an improvement
   that costs money, not a compromise.
2. **The actuators.** Hobby serial servos: plastic gears, wet grease, no radiation
   tolerance, no joint-side feedback. This one choice sets the 2.2 mm precision figure.
3. **Vacuum compatibility was never designed in.** The printed parts contain closed internal
   volumes with no vent path.
4. **Nothing has been qualified.**

### 5.3 What genuinely is space-relevant

**The docking interface.** Capture tolerance is solved as **geometry**, not as accuracy: a
Ø34 mouth over a Ø16 throat gives a measured **±9.75 mm** capture envelope against ≈2.2 mm
of arm error. That is exactly how real docking hardware works, and it is the transferable
idea — you do not make the arm accurate enough to hit a hole, you make the hole forgiving
enough to be hit.

**Fluid transfer.** A radial O-ring in the spigot, compressed by the bayonet itself, with a
Ø8 pass-through in both halves: the architecture of an orbital refuelling coupling at
demonstration scale.

**No seventh actuator.** The docking latch is driven by J6, which has ±175° of travel and
nothing to do during a docking approach. Using an existing degree of freedom to drive a
mechanism is a mass-saving technique that matters far more in orbit than on a bench.

**The verification method**, which is grade-independent: every dimensional check reads the
exported geometry and measures what is actually there, rather than trusting what the
parameter file says should be there.

> **The honest framing.** ARM-450 is a **kinematic and architectural prototype** of a space
> manipulator and a **functional demonstrator** of a docking interface. It is not a flight
> article, and it is not presented as one. What transfers is the geometry, the joint scheme,
> the docking principle and the verification method. Eleven of sixteen subsystems do not
> transfer, and §5.2 names them.

---

## 6. Conclusion

The previous arm failed for three reasons, and all three were design errors rather than
manufacturing faults: mounts sized against the load the arm uses instead of the load the
servo can deliver, a bearing chosen for the wrong load *direction*, and a link revision that
opened a dead zone in a workspace that had been correct. Each had a measurable signature —
17–95 MPa against a 9 MPa allowable, 28.9 mm of wobble, a Ø194 mm unreachable region.

The shift was not to make the arm stronger. It was to change **what each part is designed
against**. Every load case now runs at servo stall; the joints run on spaced, preloaded
bearing pairs chosen for moment capacity; the links are equal.

What that bought is measurable: wobble from 28.9 mm to 0.65 mm, the dead zone gone, a
worst-case structural safety factor of 23, 0.197 mm of tip deflection against a 0.30 mm
limit, and a vertical sine traced at 0.014 mm rms with every waypoint clear. The arm is
450.0 mm to the tool face, prints in plain PLA on a 0.4 mm nozzle in about 21 hours from
thirteen parts with no supports, and its kinematics agree with two independent
implementations to 10⁻¹³ mm.

Against a space-grade manipulator the picture is deliberately unflattering and deliberately
specific: three subsystems transfer, eleven do not, and the reasons are material, actuator,
vacuum compatibility and qualification — not geometry. The geometry is the part that would
survive, and the docking interface is the part worth carrying forward, because it solves
capture the way flight hardware solves it: with tolerance built into the shape rather than
demanded of the arm.

One item remains open. The assembled arm is **1584 g against a 1450 g ceiling** — 134 g
over, and the overage is fasteners: 244 g of inserts, through-bolts and screws that were
absent from the mass model until it was made a hard check. It is reported rather than
absorbed. Either the figure is accepted and recorded, or the base is lightened and its FEA
re-run.

---

## 7. Supporting documents

| document | what it carries |
| --- | --- |
| `ARM450_LESSONS.pdf` | every error found in the previous arm, with the reasoning that exposed it |
| `ARM450_REPORT.pdf` | the full engineering record, part by part |
| `ARM450_DEFENCE.pdf` | review dossier, method, and anticipated questions with answers |
| `ARM450_KINEMATICS.pdf` | DH derivation, Jacobian, IK and the ikpy cross-check |
| `ARM450_BUY.pdf` | bill of materials and print order |
| `ARM450_DRAWINGS_ISO.pdf` | per-part drawings |
