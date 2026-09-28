# `j1_clamp` — J1 servo mount, ported from your working design

**File:** `REV_H/j1_clamp.step` / `.stl` · **Generator:** `REV_H/gen_j1_clamp.py`
**Replaces:** `j1_pod` as the servo holder (the pod may still serve as a shroud)

---

## Why it exists

`j1_pod` cannot hold the ST3215. The arithmetic holds in any orientation,
because both put the 45.22 mm length in the bore plane:

```
output axis sits 12.50 mm off the case centre
horn on the J1 axis -> case centre 12.50 off-axis
far corner = sqrt((45.22/2 + 12.50)^2 + (24.72/2)^2) = 37.22 mm
j1_pod inner bore radius (measured z -30..-5)        = 35.70 mm
                                     INTERFERENCE    =  1.52 mm
```

An insertion sweep from z = −46 to −4 clears at **no height**. The bore is
35.65 mm in *both* `out_cad` and `REV_H`, so this is in the released design.
Boring to Ø74.44 against a Ø76.0 outer leaves **0.78 mm** of wall.

---

## What was ported

From `~/roboARM/Robotic_arm_design/motor fixer.stl` — the part you built and ran:

| measured on yours | value | ported |
|---|---|---|
| channel gap | 24.50 mm | **24.50** |
| servo width | 24.72 mm | same servo (`Motor.stl` 45.22 × 37.60 × 24.72) |
| interference | **−0.22 mm** | **−0.22** — the pinch *is* the orientation lock |
| back wall | flat bearing face | 5.00 mm flange |
| side walls | full height | 31.00 mm |
| fixing | 4 × Ø2.50 through ears | 4 × Ø3.40 (ARM-450 is M3) |

---

## As built and verified

| check | result |
|---|---|
| bbox | 77.11 × 60.00 × 31.00 |
| solids | **1** |
| volume | 25 207.8 mm³ |
| channel gap | 24.50 → **0.22 mm pinch** on the 24.72 case |
| **servo seats at** | **z = 5.00**, on the flange |
| overlap at seating | **pinch only**, starting z = 16.82 at the walls |
| **horn on the J1 axis** | **0.000 mm** |
| bolts | **4 × M3 at r = 24.00**, at ±45° |
| bolts land on base | **4 of 4 SOLID** |
| thin-feature gate | 4 candidates, **0 confirmed** — CLEAN |
| slice check | 155 layers, **0 findings** |

---

## Three errors found and corrected while building it

1. **Channel on the wrong side.** I set `cx = -AXIS_OFF`. With the horn on
   the axis the case actually lands at x −10.10…+35.12, centre **+12.51** —
   so `cx = +AXIS_OFF`. The first version put the channel opposite the servo.

2. **Bolts in mid-air.** First at r = 34, then r = 44 — both in the base's
   **void ring**. Measured at z = +2.0 the base is solid only at
   **r = 20–28** and **r = 48–58**. Bolts moved to **r = 24.0**, and only 2
   holes were being generated instead of 4.

3. **Servo seated too low.** At z = 4.0 its base fouled the 5 mm flange.
   Swept to find the true seat: **z = 5.00**, above which all overlap is the
   intended wall pinch.

---

## How it assembles

1. Servo lies with its **45.22 length along X**, **24.72 width across Y** in
   the channel, horn pointing **+Z** on the J1 axis.
2. It presses in against a **0.22 mm pinch** — that grip locks the
   orientation, no pocket needed.
3. Case base bears on the **5.00 mm flange at z = 5.00**.
4. **4 × M3** through the flange at r = 24.00, ±45°, up into the base.
5. Horn then drives `j1_drive_hub`, whose Ø19.60 recess and 4 × Ø1.90 pilots
   on BCD 14.00 are already coaxial with J1.

Both open sides give hand and driver access — the failure mode of the pod
was that the only way in was through the bore from below.

---

## Not yet done

* `j1_pod`'s role is now shroud only; its Ø4.1 strap inserts at (0, ±24.02)
  are redundant if the clamp holds the servo. **Decide whether to keep the
  pod at all.**
* J2, J3, J5 bays are rectangular pockets, not bores, so the far-corner
  constraint differs — **they have not been checked against the real servo.**
