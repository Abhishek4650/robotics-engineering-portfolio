# ARM-450 rev H — corrections and a third inspection method

**Date:** 2026-09-22
**Files:** `REV_H/*.step`, `REV_H/*.stl` (4 parts) · **released files untouched**
**Reproduce:** `cd REV_H && python3 gen_j4_module.py && python3 build_j4_chain.py && python3 gen_j1_drive_hub.py && python3 gen_collar_access.py`

---

## 1. A third inspection method — layer slicing

You asked whether anything beyond gates, meshes and booleans exists. **Yes:
slice the part the way the printer will.** `PRINT_GATE/slice_check.py` uses
`trimesh` + `shapely` to cut the mesh plane by plane at the real 0.20 mm
layer height and ask, per layer, what a nozzle can actually lay down:

| test | what it catches |
|---|---|
| **erosion by half a nozzle** | a layer that vanishes when shrunk by 0.20 mm cannot be printed — this is literally the test a slicer applies before emitting an extrusion |
| **true islands** | a connected component with *no contact* with the layer below — prints in mid-air |
| **sub-layer bands** | horizontal faces closer together than one layer |

### The sub-layer test is the important one

Slicing alone **could not see** the 0.100 mm membrane: no 0.20 mm layer plane
ever falls inside a 0.100 mm band, so the slicer steps straight over it.

**That is itself the finding.** The printer does exactly the same thing — it
lays nothing there. A 0.1 mm "skin" does not print as a fragile film; it
prints as a **hole** where a floor was meant to be. Worse than fragile, and
invisible to a slice-only check.

So the method reports any pair of horizontal faces closer than one layer.

### Validation — both directions

```
J4 released (known 0.098 mm membrane)  -> SUB-LAYER z=10.000, 505.4 mm2   FOUND
J4 rev H    (fixed)                    -> that finding gone                CONFIRMED
base        (prints successfully)      -> 0 findings                       CLEAN
```

Two earlier versions of this checker failed their controls and were
corrected rather than trusted:

* the island test fired on every outward-growing wall — **178 "islands" on
  `base`**, a part that prints fine. Fixed to require *zero contact* below.
* `trimesh.Path3D.to_2D()` applies its own transform, so a component landed
  at x 40–49 on a part whose x only reaches 37.9, producing a phantom island.
  Fixed by building rings directly in world XY.

Tooling available here: `trimesh 4.12.2`, `shapely 2.1.2`, `vtk 9.6.2`,
`scipy`, `networkx`, `rtree`. No slicer binary, no OpenSCAD, no FreeCAD.

---

## 2. Parts corrected

### 2.1 `J4_module` — 0.100 mm membrane, fixed at the generator

Two expressions for the same plane in `wrist_pro.py roll_j4_module()`:

```python
Ø33 seat : .extrude(WB + 6.0 + 1)            → top z = 10.000
Ø22 bore : .extrude(J4_MOD_H - BAY_T + 1)    → top z = 10.100
```

A **0.100 mm coincident-plane mismatch**. And a second instance of the same
fault: the servo bay floor also sat at 10.100, leaving 0.096 mm crescents at
x 14.5–20.0, y ±4–10 where the rectangular bay overhangs the round bore.

Both now cut to one shared plane with a 0.20 mm overshoot.

Built by **replaying the project's own fix scripts** (`j4_mount_fix`,
`j5_mount_fix THIRD=(-23,0)`, chamfers, strap stations) on a corrected base —
so every fastener lands where it did before.

| check | released | rev H |
|---|---|---|
| bbox | 65.91 × 56.00 × 36.72 | **identical** |
| solids | 1 | **1** |
| Ø3.4 / Ø4.1 / Ø6.4 stations | 4 / 5 / 4 | **same count, same positions** |
| confirmed sub-0.4 mm features | **418** | **0** |
| slice SUB-LAYER findings | 2 | **1 (benign, see below)** |
| servo bay floor | 10.10 mm | 9.89 mm |

The remaining z=29.200 finding is benign: the two faces 0.020 mm apart are at
*different* XY locations — counterbore seats at (−17, ±7) and insert stations
at (12.5, ±24.02), (−23, 0). Columns at each read 3.220 mm solid. No thin
material exists.

Released has 2 × Ø2.70 at (−5, ±10) that rev H lacks. Verified: **void in both
versions** — phantom faces bounding a hole, not drilled holes.

### 2.2 `j1_drive_hub` — 0.200 mm skin from an inverted chamfer

The released nose chamfer subtracts two lofts whose z spans disagree, so the
cut stops partway and leaves a ring of skin. Measured radial profile:

```
z 17.30 : r 5.01 .. 10.90
z 17.40 : r 5.01 .. 10.40   <- steps IN
z 17.90 : r 5.01 .. 10.90   <- back OUT
z 18.00 : VOID
```

The nose narrows then widens: the last 0.6 mm is an **overhanging lip 0.5 mm
proud, sitting on nothing**. Rev H cuts a true 45° lead-in:

```
z 17.40 : r 5.01 .. 10.90
z 17.90 : r 5.01 .. 10.40   monotonic, no overhang
```

Two wrong attempts on the way, both caught by slice inspection: a solid cone
from r = 10.30 removed the whole 5.90 mm nose ring (layer at z 17.70 eroded
to 0.00 mm² — UNPRINTABLE). Corrected to an annular tool.

### 2.3 `spigot_collar` + `j1_pod` — BLOCKING access defect, fixed

The collar stops the whole arm lifting off its J1 bearings. **Neither pinch
bolt could be tightened.**

```
bolt A  z = -4.20   j1_pod wall SOLID y 35.70..38.00, then open
bolt B  z = +0.20   base SOLID from y+0.2 — inside the base
j1_pod radial holes near z = -4.2 :  NONE
```

**My first proposal was wrong and measurement refuted it.** I suggested
moving bolt B down. Testing every height from +0.20 to −4.20 in the real
assembly: **all blocked** — the pod wall encloses the whole collar, not just
bolt B. Moving the bolt alone fixes nothing.

The actual fix, two changes:

1. **`j1_pod` gains a 9.0 mm radial access window** centred z = −3.35. With
   the pod removed from the assembly, clearance at z = −4.20 is 60 mm for a
   hex key *and* 60 mm for a full 6 mm driver — the best access on the part.
2. **bolt B moves +0.20 → −2.50**, clearing the base underside. At +0.20 no
   window can help.

Verified in the rev H assembly:

| bolt | hex key | driver body | verdict |
|---|---|---|---|
| A (z = −4.20) | **60.0 mm** | **60.0 mm** | OK |
| B (z = −2.50) | **60.0 mm** | 2.5 mm | OK — hex key |

Trade-off, stated plainly: bolt spacing drops 4.40 → 1.70 mm, so the couple
closing the split collar is weaker than intended. I chose this over a single
bolt (which clamps only the collar's lower half and lets the top creep on the
spigot). The collar was rebuilt from measured dimensions — OD 46.00, bore
30.15, height 10.00 — because patching the imported solid produced a 372 mm³
fragment from an 8 932 mm³ part. Rev H is 9 037 mm³, within 1.2 %.

---

## 3. Access findings that are NOT defects

| station | full assembly | correct build stage |
|---|---|---|
| `j1_drive_hub` cross-bolt A | 0.0 mm | **33.5 mm** before the turret |
| `j1_drive_hub` cross-bolt B | 0.0 mm | **40.0 mm** before the turret |

Both reachable in the specified build order.

**`servo_strap` / `servo_strap_micro` flags are placement artifacts** — both
are parked at the origin in the assembly's HARDWARE group, buried inside the
base, rather than at their joints. Only one of five straps is placed at all.

---

## 4. Flagged parts resolved

| part | flag | verdict |
|---|---|---|
| `J2_turret_p2` | 38 confirmed, min 0.315 mm | **benign feather edge** — wall tapers linearly 1.63 → 0.17 mm to its boundary. A slicer drops sub-extrusion material automatically; the edge ends a fraction early. Not a membrane spanning void. |
| `j1_drive_hub` | 28 confirmed, min 0.200 mm | **real — fixed**, §2.2 |
| `base`, `j1_pod`, `joint_tube`, `spigot_collar` | candidates | **all artifacts, CLEAN** |

---

## 5. Still open

1. **Micro-strap orientation (B3).** `servo_strap_micro` bolts run along Z;
   `j6_body` threads along X. Spans match at 30.00 mm, only the axis
   disagrees, and neither part rotates to fit the other. **Needs your
   decision:** side-mounted strap, or top-mounted?
2. **Batches 2 and 3 of the 21-part gate** did not finish — the cross-check
   is slow. `J2_turret_p1`, `J3_p1/p2`, the four links, `J5_p1/p2`,
   `tool_flange`, `shaft_clamp`, `servo_strap*` are scanned but not yet
   cross-checked.
3. **`J5_p1` Ø24 bore** — unresolved since 2026-09-21.
4. **`BRG_FIT = 0.00` is deliberate.** Print the Ø42 coupon and try a real
   6806 before committing to the turret.
