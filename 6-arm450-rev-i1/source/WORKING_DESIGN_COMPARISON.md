# How your working arm mounts its servo — and what ARM-450 does differently

**Reference:** `~/roboARM/Robotic_arm_design/` — the design you built and ran.
**Measured:** 2026-09-22, from the STL files in that folder.

---

## 1. Their servo is the same servo

```
Motor.stl          45.22 x 37.60 x 24.72
ARM-450 ST3215.stl 45.22 x 37.80 x 24.72
params.py          SERVO_L 45.22  SERVO_W 37.80  SERVO_T 24.72
```

Identical to 0.20 mm. **So the servo is not the variable — the mount is.**
This also settles the question you answered with a caliper: 24.72 is right,
and my earlier "35.30 mm case body" was a misreading of an untabbed mesh.

---

## 2. What the working design actually does

`motor fixer.stl` — **64.80 × 27.20 × 31.00**

Measured cross-sections show a **U-shaped channel**, not an enclosure:

```
z = -14.50   #####################     solid back wall
z =  -7.25   #...................#     two upright side walls
z =   0.00   #...................#
z = +14.50   #...................#     open at the top
```

| feature | measured | what it does |
|---|---|---|
| channel gap | **24.50 mm** in X | grips the servo's **24.72 narrow** dimension |
| interference | **−0.22 mm** | it *pinches* — this is what locks the orientation |
| back wall | z −15.50 … −13.x | the face the servo **bears on** |
| side walls | full 31 mm height | react the joint torque in shear |
| overall length | 64.80 vs servo 45.22 | **19.6 mm of overhanging ears** |
| bolt holes | **4 × Ø2.50** at x = ±29.4, z = 2.02 / 8.52 | M2.5 clearance, through the ears into the link |
| bolt spacing | **58.8 × 6.5 mm** | wide stance, so the clamp cannot rock |

**The scheme:** servo lies with its 45.22 length along the channel and its
24.72 width across it. The clamp pinches those two faces. The horn points out
of the open +Z side, on the joint axis. Four M2.5 bolts through the ears fix
the whole assembly to the link face.

**Orientation is locked by the pinch, not by a pocket.** That is why it worked
in hardware: a −0.22 mm grip on a printed part is a press that holds.

---

## 3. What ARM-450 does instead — and why it fails

`j1_pod` — **Ø76.0 outer, Ø71.40 bore, 46.0 tall**. A round **shroud**. The
servo is supposed to go *inside the bore*.

```
servo case        45.22 long, output axis 12.50 off the case centre
horn on the J1 axis -> case centre sits 12.50 off-axis
far corner radius = sqrt((45.22/2 + 12.50)^2 + (24.72/2)^2) = 37.22 mm
j1_pod inner bore radius (measured)                          = 35.70 mm
                                              INTERFERENCE   =  1.52 mm
```

An insertion sweep from z = −46 to −4 finds **no height at which it clears**.
The bore measures 35.65 mm in *both* `out_cad/j1_pod.step` and
`REV_H/j1_pod.step`, so this is in the released design, not something the
rev-H access window introduced.

**It cannot be bored out:** Ø74.44 is needed against a Ø76.0 outer, leaving
**0.78 mm** of wall — below the 1.2 mm load floor.

---

## 4. The fix, from your own working design

Replace the round shroud with the U-clamp pattern that already works:

| | working design | ARM-450 j1_pod |
|---|---|---|
| form | open U-channel | closed round bore |
| grip | 24.50 on the 24.72 width, −0.22 pinch | none — servo floats in a Ø71.4 bore |
| bearing face | flat back wall | none |
| fixing | 4 × M2.5 through overhanging ears, 58.8 × 6.5 | 4 × M3 pod-to-base, servo held only by a strap |
| orientation lock | the pinch | the strap alone |
| clearance for hands | open on two sides | bore, access only from below |

The working clamp is **64.80 × 27.20 × 31.00** — far smaller than the Ø76 ×
46 pod, and it does not have the 1.52 mm interference because the servo never
has to fit *inside a circle* whose centre is 12.50 mm off the horn.

---

## 5. What I recommend

**Do not print `j1_pod` as drawn.** Either:

* **A — port the U-clamp.** Build a `motor fixer`-style bracket for J1 sized
  to the ARM-450 base bolt pattern. This is the option your hardware has
  already proven.
* **B — grow the pod** to Ø80 outer so the bore can reach Ø74.44 with a
  2.78 mm wall. Larger, heavier, and still relies on the strap alone to lock
  orientation.

**A is better on the evidence.** It is smaller, it locks orientation by pinch,
it gives a real bearing face, and it has been built.

---

## 6. Still unverified

`J2`, `J3`, `J5` bays are rectangular pockets rather than bores, so the
far-corner constraint does not apply the same way — but they have **not** been
checked against the real servo yet.
