# ARM-450 rev H — Rule 3 verification

Every number measured from the solids or the user's own `Motor.stl`.
Nothing taken from a parameter file.

## What was wrong, and where it came from

One root cause explains the servo-mount failures at **all three** driven
joints. `fixparams` carries `SERVO_L/W/T = 45.22 / 37.25 / 24.72`, and every
generator derives its bay as

```
BAY_W = SERVO_W + 2*BAY_CLR   = 38.05
BAY_T = SERVO_T + BAY_CLR+1.5 = 26.62
```

But `BAY_T` is cut **along the servo's output axis**, and measured from the
mesh the ST3215 needs **33.50 mm** there — the 24.72 is the case *width*,
not its depth. So every bay was **6.88 mm too shallow** while `BAY_W` had
**13.33 mm of slop**: the servo would not go in, and could rattle if it did.

| joint | cavity as released | needed | short by |
|---|---|---|---|
| J2 turret | 27.11 | 33.50 | 6.39 |
| J3 elbow | no bay at all | 33.50 | — |
| J5 wrist | no usable bay | 33.50 | — |

## Fixes

* **J3** — regenerated through `fork_pro.fork_p1/p2` with the drive cheek
  intact and the bay from `servo_geom.py`.
* **J5** — **new design** (`gen_j5_new.py`). The old layout ran the 45.22 mm
  case along the one boxed-in direction (36.28 mm available). The new one
  copies J3's topology: case length **along the arm**, output axis across.
  **The arm stays 450 mm** — no link lengthening needed.
* **J2** — regenerated with the corrected bay, growing outward to
  y = −64.40. Verified free: `base` has no material at y < −45 in the
  bay's z band.
* **J4** — a 0.0198 mm floating disc (7.75 mm², a tenth of a layer) where
  blind inserts bottomed at 29.220 against a bore ceiling at 29.200.
  Insert depth 7.50 → 8.00.

## Rule 3, item by item

| # | requirement | result |
|---|---|---|
| 3 | pockets/holes/bores on the right face and plane | **PASS** — bearing pockets, horn bores and pinch channels measured on both forks |
| 2 | no thin surfaces near 0.1 mm | **PASS** — 0 sub-layer bands on every part |
| 4 | servo on the right face, driving the next link | **PASS** — horn on the joint axis to **0.0000 mm** at J2, J3, J5 |
| 5 | not floating, orientation locked | **PASS** — −0.22 mm pinch measured at 24.500; 5° rotation bites |
| 8 | screwdriver reach | **PASS** — all 12 fasteners, 70 mm clear run for a 6 mm driver |
| 8 | joint motion in sync | **PASS** — all 6 joints sweep full travel, 0 clashes |
| 9 | assemble / disassemble | **PASS** — two-piece housings, bolts accessible, no captive parts |
| 10 | no face overlap, real clearance | **PASS** — parting planes coincident to 0.000000, 0 interpenetration |
| 7 | wiring clearance | **PASS** — cable exit bored in the back wall of each bay |

### Manual verification (the most important check)
`manual_verify.py` slices each fork and reads the geometry feature by
feature. **ALL CHECKS PASS** on J3 and J5:
bearing pockets Ø42.15/Ø37.15 (want Ø42.02/Ø37.02), horn bores Ø24.13,
pinch channel 24.472 at every station, 0 sub-layer bands, horn offset
0.0000, contact only on the pinch faces, parting gap 0.000000.

### Motion sweep
All six joints, full travel, differential against the rest pose:
**0 joints with a real rise**. Validated with a control — an injected
block in the J3 arc was detected.

### Seated fits confirmed, not clashes
* J5/J4 mating face: 0.0000 z-spread, 0 points inside → coincident face.
* J1 hub/turret: r 10.92–11.00, a 0.08 mm shell → press fit.
* spigot/collar: bore r 15.035 vs spigot r 14.995 → **0.040 mm clearance**.

## Gate bugs found and fixed

Both thin-feature gates paired parallel planes on offset alone, ignoring
face direction and overlap — inventing findings on solid material. Fixed to
require opposed normals and real footprint overlap. **Validation held**:
both still catch the known-bad released `J4_module`, both still pass the
known-good `base`. False findings disproved by direct probing: `J5_p1`
"0.100 mm" (270 probe columns, 0 sub-layer runs) and `J4` "0.375 mm".

## PRINT GO

**GO — 15 parts, 0 findings on both gates:**

J2_turret_p1, J2_turret_p2, J3_p1, J3_p2, J4_module, J5_p1, J5_p2,
J5_strap, j1_clamp, j1_drive_hub, j1_pod, j3_clamp, j5_clamp,
servo_strap_micro, spigot_collar.

**One condition: the straps are not optional.** The pinch alone leaves
~2° of rotational play at each joint; the strap closes it. Print
`J5_strap` and use the existing `servo_strap` at J2/J3.
