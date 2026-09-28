# J2 / J3 / J5 have no servo pockets — the finding that ends five failed searches

**Date:** 2026-09-23 · **Method:** derivation from `fork_pro.py` + manual slice
inspection

---

## The finding

**`J2_turret_p1`, `J3_p1` and `J5_p1` contain no enclosed servo bay.** They are
open forks and shells: a thin back plate plus two ring-shaped cheeks, open
everywhere between.

This is why five seating searches failed. **They were looking for a pocket that
does not exist.** The right answer was never a better probe.

---

## How it was established

### 1. The three missing constants were found

`fork_pro.py` lines 32–35: `FLOOR_T = 4.0`, `BACK_T = 2.4`, `SEAT_T = 2.0`.
Its own docstring gives the intended stack:

```
Ø38 seat shoulder   2.0
Ø42 bearing pocket  7.0
bay floor           4.0     carries the four M2.5 case screws
servo bay          25.3     ST3215 + 0.3/side
back wall           2.4
```

So `z_bay = FORK_HALF + SEAT_T + brg_w + FLOOR_T = 15.50 + 2.0 + 7.0 + 4.0
= 28.50`, bay spanning 28.50 … 55.12, and the drive cheek ending at
**z_drive = 57.52**.

### 2. No released part matches it

| part | fork-axis span | needs |
|---|---|---|
| `J3_p1` | z −24.50 … **28.50** (53.00 mm) | drive cheek alone 42.02 mm **plus** an idle cheek |
| `J2_turret_p1` | z −59.00 … 67.00 | no face at 57.52 |
| `J5_p1` | z −26.00 … 22.00 (48.00 mm) | z_drive 54.52 |

`J3_p1` ends at **exactly where the bay is supposed to begin**.

### 3. Manual slice inspection confirms it

`J3_p1` at the bay wall midplane is solid only at x −38 … −32 — a back plate.
Slices at z = −10, 0, +10 show the same: a plate on one edge, open air
everywhere else. The rings at z = ±20 are the bearing cheeks.

`J5_p1` and `J2_turret_p1` show the same pattern.

---

## Two invalid tests, discarded rather than reported

**Enclosure test (≥4 of 6 faces backed by material).** Reported J4_module at
**2 of 6** — a bay verified to seat the servo with zero interference. Re-run at
J4's known-good centre it scores **3 of 6**, because the bay is open at the top
and the servo nearly fills it, so probing 3 mm beyond the case lands outside
the module. **The threshold is wrong for an open-topped bay.**

**Face-derived pocket search.** `contains() == 0` also means *outside the
part*: it "seated" J4 at z = −12.36 on a module spanning z 0 … 36.72.

Both were caught by a control before being reported.

---

## What this means

The wall pairs found earlier at BAY_L 46.00 and BAY_W 38.05 are real
dimensions, but they bound **nothing** — two parallel faces the right distance
apart, not a pocket.

`J4_module` is the only joint with a genuine servo bay, and it verifies:
**0 of 3 324 envelope points in material, horn on the joint axis to 0.010 mm.**

**J2, J3 and J5 need a servo mount built.** The proven pattern is the
`motor fixer` U-clamp from the user's working arm, already ported successfully
as `j1_clamp`:

* 24.50 mm channel gripping the servo's 24.72 width — **0.22 mm pinch**, which
  locks orientation without a pocket
* flat flange as the bearing face
* 4 × M3 through the flange, all landing on solid material
* horn on the joint axis to **0.000 mm**
* zero thin features, passes slice inspection
