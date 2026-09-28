# J2 / J3 / J5 servo mounts — status

**Date:** 2026-09-23

---

## The underlying finding stands

**J2, J3 and J5 have no servo pocket.** Established three independent ways
(see `NO_SERVO_POCKETS.md`):

* `fork_pro.py` derives `z_bay = 28.50` and a drive cheek ending at
  `z_drive = 57.52`. **`J3_p1` ends at exactly 28.50** — where the bay should
  begin. No released part has a face at 57.52.
* Manual slice inspection: back plate plus two ring cheeks, open air between.
* Five seating searches failed because they were hunting a pocket never cut.

`J4_module` is the only joint with a real bay, and it verifies clean.

---

## What the new clamps achieve

`REV_H/j3_clamp.{step,stl}`, `REV_H/j5_clamp.{step,stl}` — single solids,
built on the `motor fixer` pattern.

| requirement | j3_clamp | j5_clamp |
|---|---|---|
| **shaft on the joint axis** | **0.000 mm** | **0.000 mm** |
| servo gripped by the 0.22 mm pinch | yes, walls ±12.25 vs case ±12.36 | yes |
| servo overlap outside the pinch | **0** | 16 pts, at the walls |
| single solid | **1** | **1** |
| thin features (2-method gate) | 8 candidates, **0 confirmed** | 8 candidates, **0 confirmed** |
| **clamp vs host interpenetration** | **375 points — NOT RESOLVED** | **618 points — NOT RESOLVED** |

---

## The unresolved problem, stated plainly

**The flange interferes with the host.** Four flange positions were tried and
each failed for a different, measured reason:

1. flange at x = −35.00 (mid-plate) → 377 points inside the host
2. bolts at (±17, ±7) → those stations are in **void**: J3_p1's boss is only
   y ±11, z −10…+11
3. bolts moved to the measured (±10, ±6) for J3 and (±17, ±5) for J5, flange
   on the outer face → channel ran into the fork interior, 316 points
4. channel shortened to 22.00 mm → channel now clears, but the **flange**
   overlaps at x −43.93…−21.75

**Why:** J3_p1's mounting boss is **not a flat plate**. Mapped at z = 0:

```
x = -41 .. -35     .....#######.....      narrow stem, y +/-10
x = -32 .. -29     #################      full-width slab
x = -26 and beyond .................      open
```

A rectangular flange laid across that will always intersect the step. The
mount needs a flange profiled to the stepped boss — or the boss itself
modified — not another rectangle.

---

## Honest position

**Do not print `j3_clamp` or `j5_clamp` as they stand.** They get the two
hardest things right — the shaft is on the joint axis to 0.000 mm and the
servo is properly pinched — but the flange-to-host interface is not solved,
and printing a part that interferes with its host wastes filament.

**What remains is bounded:** profile the flange to the stepped boss
(x −41…−35 at y ±10, then x −32…−29 full width), or cut a flat seating pad
into the boss in the host part. Either is one shape change, then re-run the
same three checks: containment, pinch, horn offset.

`j2_clamp` has not been attempted — J2's mount is on the turret shell's
y = −28.50 face with 6 × Ø4.1 stations, a different arrangement again.
