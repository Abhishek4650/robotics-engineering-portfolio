# Pending verification — J2 / J3 / J5 servo seating

**Status: NOT VERIFIED after five attempts.** Reported as unknown rather than
guessed. One hard result was obtained along the way (§3).

---

## 1. What IS established

**The bays are the right size.** Each part carries a parallel wall pair at
exactly the design bay dimension, located from the geometry itself:

| part | wall pair | axis | centre-line |
|---|---|---|---|
| `J2_turret_p1` | **BAY_L 46.00** | Y | −5.500 |
| `J3_p1` | **BAY_L 46.00** | Z | +5.500 |
| `J5_p1` | **BAY_W 38.00** | Z | −3.000 |
| `J5_p2` | **BAY_W 38.05** | Y | 0.000 |
| `J4_module` | **BAY_W 38.05** | Y | 0.000 |

Design: `BAY_L = 46.02`, `BAY_W = 38.05`. Match within 0.05 mm.

---

## 2. Five failed attempts, and why each was discarded

| # | method | why it was invalid |
|---|---|---|
| 1 | bounding-box void scan | these are open forks (16–30 % solid) so most "free space" is open air **outside** the part; the J3 "fit with 23.95 mm margin" was the servo floating beside it |
| 2 | full 3-axis search | timed out twice (exit 124, 143) |
| 3 | coarse 4 mm centre-line sweep | **failed its control** — missed J4, a bay known to seat the servo; 4 mm cannot land on 0.5 mm clearance and one axis range collapsed to empty |
| 4 | batched sweep | OOM-killed (exit 137), then hung: J2 alone needs **15 912** `contains()` calls on a 10 042-triangle mesh |
| 5 | derive pocket from its own faces | `contains()==0` also means **outside the part** — it "seated" J4 at z = −12.36 on a module spanning z 0…36.72. Adding a containment requirement fixed that, but floor selection still picks the wrong face: it returns (1.75, 0, 13.00) where the known-good J4 centre is (12.51, 0, 22.46) |

**Every attempt was caught by a control, not shipped.** Attempt 3 would have
reported three false defects.

---

## 3. One hard result: `J5_p2` cannot hold the servo

Settled by arithmetic, no probe required:

```
ST3215 case      45.22 x 37.80 x 24.72
J5_p2 bounding box   36.28 x 50.00 x 29.02
sorted: part 29.02 / 36.28 / 50.00   vs   servo 24.72 / 37.80 / 45.22
                      36.28 < 37.80  ->  short by 1.52 mm
```

The part is **1.52 mm too small in its second dimension**, so no orientation
fits. **The J5 servo is not in `J5_p2`** — it must be in `J5_p1`, whose box
(36.28 × 50.00 × 48.00) does accept the case.

---

## 4. Why J4 could be verified and these cannot, yet

J4's pocket origin is **derivable from its generator**: `rect(BAY_L, BAY_W)`
centred on `SERVO_AXIS_OFFSET`, floor at `J4_MOD_H − BAY_T`. Place the servo
there once: **0 of 3 324 points in material**, horn on the joint axis to
0.010 mm.

J2/J3/J5 are built by `fork()` in `fork_pro.py`, which computes the bay in a
local frame (`z_bay = z_in + SEAT_T + brg_w + FLOOR_T`) and then transforms it.
`SEAT_T`, `FLOOR_T` and `BACK_T` are not in `fixparams.py` — they come from
elsewhere in the import chain. **Recovering that chain is the remaining work**,
and it is a derivation, not a search.

---

## 5. Honest position

**Do not treat J2 / J3 / J5 servo fit as verified.** The bays are the right
size and there is no evidence of a J1-style defect — J1 failed because its pod
is a round *bore* where the far corner swings to r = 37.22 against a 35.70
bore, which cannot arise in a rectangular pocket. But "no evidence of a defect"
is not "verified to fit".

**`J5_p2` is a real finding** and should be treated as one: it cannot contain
the servo, so any documentation showing the J5 servo there is wrong.
