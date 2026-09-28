# PRINT GO RETRACTED — 2026-09-23

The GO given for J3_p1/p2, J5_p1/p2 (and the 15-part list in
RULE3_VERIFICATION.md) is **withdrawn**. Do not print any servo housing.
Every seating test until now checked the servo against **p2 only**; the
horn end sits in **p1**, and nothing checked whether the horn actually
**drives** the next link. Checking both found four defects.

## 1. Servo front cap clashes with the housing floor — J2, J3, J4, J5
The ST3215 has a raised front cap between the case body and the horn disc,
measured from Motor.stl in the joint frame:

| below the mounting face | footprint |
|---|---|
| 0.0 – 2.0 mm | 40.13 × 24.18 (x −5.30..34.84) |
| 2.0 – 2.4 mm | 39.39 × 13.91 |
| ~2.4 mm | 43.53 × 19.20 (x −9.60..33.93) |
| 2.6 – 4.5 mm | Ø19.20 horn disc |

The floor only has a Ø24 horn bore, so the cap sinks **2.61 mm into p1**:
J3 4032/60000 points, J5 3977/60000. At J4 it also hits the forearm ends.

## 2. The horn drives nothing — J2, J3 (and J5 unverified)
At J3 the joint tube is Ø30 / Ø26 (bought aluminium). The Ø19.2 horn disc
sits **inside the Ø26 bore** with its face at y = 23.99, 1.01 mm inside the
tube end, touching nothing: 0 servo points inside the tube, either shaft
clamp, or either forearm half. **The servo would turn and the elbow would
not.** The released `fork_pro` docstring ("no clamp, no coupling") assumed
the shaft passing through the bore was enough. It is not; something must
bolt to the horn.

The proven coupler is the user's own `Motor_mount.stl` (measured): Ø24 horn
face, **4 × Ø2.52 on a 14.00 BCD** in a cross + Ø2.52 centre, Ø24 hub,
Ø40 flange with **6 × Ø2.52 on a 33.00 BCD**. Inside the tube, any coupler
must key to the tube from the inside, which needs a decision on the bought
tubes (see below).

## 3. J4 bay 6.47 mm too shallow — same root cause
`J4_module` has `BAY_T = 26.62` along the roll (output) axis. The seated
servo reaches world z 371.19 against a module top of 364.72, so it runs
**6.47 mm into J5_p1** (4309/40000 points). The J4_MOD_H revert to 36.72
earlier this project was based on the 24.72 case *width*, which is correct
as a width but not the dimension along the output axis.

## 4. Two claims in the earlier summary were wrong
* **"The pinch leaves ~2° of play; the strap closes it."** Wrong: that came
  from an off-pinch count that ignores shallow contact. Measured wall
  penetration rises immediately — 0.112 → 0.248 mm at 0.25°, 0.677 at 1°.
  The walls resist rotation from the start.
* **"Fit the strap on its two M3 inserts."** Impossible: the inserts are
  cut into p2 at the parting plane and **p1 is solid directly over them**.
  A strap there would stop the halves closing. The strap is a leftover
  `fork_pro` feature and is not needed: with p1 bolted on, the servo is
  captured on all six sides. **`J5_strap` withdrawn.**

## Still valid
Layer-slice and thin-feature gates (0 findings), the gate fixes, the J4
0.0198 mm membrane fix, the J5 re-orientation idea, the motion sweep of the
structure, bolt access of the housing fasteners, the pinch channel width.
Parts with no servo in them are unaffected: j1_drive_hub, j1_pod, j1_clamp,
spigot_collar, j3_clamp, j5_clamp, servo_strap_micro — but J1 and J6 horn
coupling have **not** been checked the same way yet.
