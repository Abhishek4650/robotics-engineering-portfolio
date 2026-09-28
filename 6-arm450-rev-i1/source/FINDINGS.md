# ARM-450 rev H — verification findings

**Date:** 2026-09-22
**Measured from:** `out_cad/`, `REV_H/`, `PRINT_GATE/fixed/`, `ARM450_FINAL_ASSEMBLY.step`

---

## 1. The 0.1 mm defect — root cause found and fixed at source

### Where it came from

`arm450_design/verify_pro/parts/wrist_pro.py`, `roll_j4_module()`. Two cuts
that must meet at the servo bay floor were written as different expressions:

```python
# Ø33 bearing seat + journal clearance
.extrude(WB + 6.0 + 1)           from z = −1  →  top at z = 10.000
# Ø22 horn bore, "stops at the bay floor"
.extrude(J4_MOD_H - BAY_T + 1)   from z = −1  →  top at z = 10.100
```

`WB + 7.0 = 11.000` vs `J4_MOD_H − BAY_T + 1 = 11.100`. **A 0.100 mm
coincident-plane mismatch.** The annulus between Ø22 and Ø33 kept a
0.100 mm skin at z 10.000–10.100.

Measured in the released part: at (14, 0) the *only* material in the entire
z column is **z 10.002–10.100 = 0.098 mm**, with void below it.

### A second instance of the same fault

After fixing the first, a cross-check found **0.096 mm still present** at
x 14.5–20.0, y ±4–10 — two crescents. Cause: the servo bay floor is also at
z = 10.100, so where the rectangular bay overhangs the Ø33 circle the two
cuts again met exactly and left a sliver.

### The fix

One shared plane, computed once, with an overshoot so no two faces land
coincident:

```python
BAY_FLOOR = J4_MOD_H - BAY_T        # 10.100
OVERSHOOT = 0.20
depth = (BAY_FLOOR + OVERSHOOT) - (-1.0)
# Ø33 and Ø22 both cut to this depth
# the bay cuts from BAY_FLOOR - OVERSHOOT
```

Generator: `REV_H/gen_j4_module.py`. Fix chain replay: `REV_H/build_j4_chain.py`.

### Why not fix the STEP file

Five boolean attempts on the output, every one rejected by verification:

| # | tool | outcome |
|---|---|---|
| 1 | Ø22 at origin | removed 0.213 mm³ — skin untouched |
| 2 | Ø33 at origin | left the skin at r > 16.5 |
| 3 | Ø37+Ø56, full height | removed 13 918 mm³, **split into 2 solids** |
| 4 | same, z-bounded | cut the real 10.096 mm flange, **split the part** |
| 5 | 415 per-column cutters | membrane gone, ring intact, **44 solids** |

The skin and the legitimate flange share one z band and are topologically
interleaved. No boolean on the output separates them.

### Rev H verification

| check | released | rev H |
|---|---|---|
| bounding box | 65.91 × 56.00 × 36.72 | **identical** |
| solids | 1 | **1** |
| M3 clearance Ø3.4 | 4 | **4, same positions** |
| M3 insert Ø4.1 | 5 | **5, same positions** |
| counterbore Ø6.4 | 4 | **4, same positions** |
| bearing chamfer cones | 9 | **7, RefRadius 19.0 at z=0 — matches** |
| mesh scan candidates | 510 | 94 |
| **confirmed real thin** | **418** | **0** |
| servo bay floor | 10.10 mm | 9.89 mm (one layer traded) |

Built by **replaying the project's own fix scripts** (`j4_mount_fix`,
`j5_mount_fix` `THIRD = (-23, 0)`, `add_chamfers`, strap stations) on a
corrected base — not by reimplementing them. That is why every fastener
lands in the same place.

**One difference:** released has 2 × Ø2.70 at (−5, ±10) that rev H does not.
Verified: those sit in **void** in *both* versions — phantom faces bounding a
hole, not drilled holes in material. Nothing functional is lost.

---

## 2. `j6_body` — fixed

Two Ø4.10 stations at (±15, 0, 14) were a mirrored pair that did not mirror:
left pocket 2.000 mm deep into a 2.098 mm wall (0.098 mm skin), right pocket
0.100 mm deep. Both now driven through. Thinnest feature **0.095 → 1.30 mm**,
wall untouched at 2.098 mm, single solid.

File: `PRINT_GATE/fixed/j6_body.{step,stl}`.

---

## 3. NEW BLOCKING DEFECT — spigot collar pinch bolt B unreachable

Found by the hardware-access check, not by any geometry gate.

```
collar bbox z      −7.00 … +3.00   (10.00 mm thick)
bolt A axis        z = −4.20       2.80 mm above the collar bottom
bolt B axis        z = +0.20       2.80 mm below the collar top
base underside     z =  0.00
```

**Bolt B sits 0.20 mm above the base underside — inside the base.**

Measured approach clearance along +y, in the assembly:

| bolt | first obstruction | clear run |
|---|---|---|
| A (z = −4.20) | `j1_pod` at y+12.8 | **12.8 mm** |
| B (z = +0.20) | `base` at y+0.2 | **0.2 mm — BLOCKED** |

A 2.5 mm hex key needs ~25 mm of straight arm. Bolt A is recoverable with a
ball-end key or by tightening before the collar is raised. **Bolt B cannot be
reached at any assembly stage.**

The collar is what stops the whole arm lifting off its J1 bearings. One of its
two pinch bolts cannot be tightened.

---

## 4. Access results that are NOT defects

Distinguished by re-running the check at each assembly stage:

| station | full assembly | before the turret |
|---|---|---|
| `j1_drive_hub` bolt A | 0.0 mm | **33.5 mm — OK** |
| `j1_drive_hub` bolt B | 0.0 mm | **40.0 mm — OK** |

Both J1 cross-bolts are reachable in the correct build order (hub bolted
before the turret is fitted), which the build sequence already specifies.

**`servo_strap` and `servo_strap_micro` flags are placement artifacts.** Both
are parked at the origin in the assembly's HARDWARE group — buried inside the
base — rather than at their real joints. Their access numbers are meaningless.
Only one of five straps is placed at all.

---

## 5. Method correction — why earlier scans were unreliable

The mesh ray-scanner flagged sub-0.4 mm features on **every** part, including
`base`, which has printed successfully. Diagnosed: rays grazing a face
register a duplicate hit a few microns away, which reads as a sub-micron wall.
All 65 `base` flags clustered within 0.03 mm of its z = 50 top face.

Fixed by welding hits closer than 0.02 mm — but that alone was not enough.
**The gate now requires two independent methods to agree:**

* mesh ray-march (fast, exhaustive) finds candidates
* solid classifier (slow, authoritative) rules on each one

This caught a premature "rev H is clean" call: 46 mesh flags I had dismissed
as artifacts turned out to be **real** at 0.096 mm, confirmed at 14 of 14
points by the classifier. Without the cross-check I would have passed a part
that still had a membrane.

---

## 6. Still unverified

1. **The 21-part gate did not finish** — it timed out twice and is being run
   in batches. Only `J4_module` has been fully cross-checked so far.
2. **`J5_p1`'s Ø24 bore** — unresolved since 2026-09-21.
3. **Micro-strap orientation (B3)** — `servo_strap_micro` bolts run along Z,
   `j6_body` threads along X. Spans match at 30.00 mm; only the axis
   disagrees. Neither part can be rotated to fit the other. **Needs your
   decision on the intended mating scheme.**
4. **Straps at J2–J5 in assembly coordinates** — verified only by matching
   insert spans in part coordinates.
5. **Real-world tolerance.** All figures are CAD. `BRG_FIT = 0.00` is
   deliberate; print the Ø42 coupon and try a real 6806 first.
