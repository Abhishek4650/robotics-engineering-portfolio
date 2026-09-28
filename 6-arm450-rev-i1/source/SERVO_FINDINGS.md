# Servo fit — findings and one retraction

**Date:** 2026-09-22

---

## 0. RETRACTION — the "35.30 mm servo" was my error

I reported that the ST3215 case body was **35.30 mm** along its output axis,
that `SERVO_T = 24.72` was therefore wrong, and that every bay in the arm was
8.68 mm short. **That was wrong.**

You confirmed with a caliper: **24.72 is correct**, and the four case-mounting
holes are on a **19.05 × 20.29** pattern.

**What I misread.** The supplied `ST3215.stl` does **not model the mounting
tabs** — I searched all three axes for a 19.05 × 20.29 four-hole pattern and
found none. Without the tabs I took the 37.80 mm overall span as the output
direction. Profiling the mesh properly shows the case body is
**45.2 × 24.7 at every station** from y = −25.2 to y = +4.8; the 37.80 span is
body height plus a 6 × 6 cable boss at y = −27.70 and the Ø19.2 horn disc at
y = +7.30.

**Consequence of the error:** I grew `J4_module` from 36.72 to 45.90 mm.
**That growth is reverted.** The module is back at 36.72 mm, 52 500 mm³,
1 solid, all fastener positions unchanged.

**Verified after reverting:** the real ST3215 sits in the J4 bay with its top
at z = 34.82 against a module top of 36.72 — fully inside — with **0 of 3 324
envelope points in material**, and the **horn axis on the J4 axis to 0.000 mm**.

`BAY_T = SERVO_T + BAY_CLR + 1.5 = 26.62` against a 24.72 case gives
**1.90 mm to spare**. The bay was right all along.

---

## 1. CONFIRMED DEFECT — the J1 pod bore is 1.52 mm too small

This one is **not** an axis-mapping question. It follows from arithmetic that
holds in either orientation, because both put the 45.22 mm length in the bore
plane:

```
servo case            45.22 long x 24.72 across
output axis offset    12.50 mm from the case centre   (params; measured 12.51)

horn on the joint axis  ->  case centre sits 12.50 off-axis
far corner radius = sqrt((45.22/2 + 12.50)^2 + (24.72/2)^2)
                  = sqrt(35.11^2 + 12.36^2)
                  = 37.22 mm

j1_pod inner bore radius, measured constant over z -30..-5  =  35.70 mm

INTERFERENCE = 1.52 mm
```

An insertion sweep from z = −46 to −4 finds **no height at which the servo
clears**.

**It is a released-design defect.** The bore measures 35.65 mm in *both*
`out_cad/j1_pod.step` and `REV_H/j1_pod.step`, so my access window did not
cause it.

**Why it cannot simply be bored out:** the required bore is Ø74.44 against a
Ø76.0 outer, leaving **0.78 mm of wall** — below the 1.2 mm load floor.

### Options, none free

| | change | cost |
|---|---|---|
| A | grow `j1_pod` outer Ø76 → Ø80 | new part; check it still clears the base bolt circle at r = 34 and the 4 × M3 pod mounts |
| B | move the servo so the horn is **not** on the pod axis, driving J1 through an offset hub or a belt | changes the J1 drive train; `j1_drive_hub` is designed coaxial |
| C | confirm the physical pod accepts the servo | if your previous arm worked with this pod, the released bore may differ from what I measured — worth a caliper across the pod bore |

**Recommendation: measure the printed pod's inner bore.** You said the
industry-standard design fitted on your previous arm. If the real pod bore is
≥ 74.5 mm, the CAD and the hardware disagree and the CAD is what needs
correcting. If it is ~71.4 mm as modelled, option A is the fix.

---

## 2. Still to check

The same far-corner arithmetic applies wherever a servo has its horn on the
joint axis inside a round pocket. **J2, J3, J5 have not been checked this
way** — their bays are rectangular, not bores, so the constraint is different,
but it has not been verified.

---

## 3. What is verified and unchanged

* `J4_module` — servo clears, horn on axis to 0.000 mm, 0 thin features
* `j6_body` — both Ø4.10 stations driven through
* `servo_strap_micro` — side-mounted, coaxial to 0.000 mm
* `spigot_collar` + `j1_pod` window — both pinch bolts now reachable,
  60 mm hex-key clearance
* `j1_drive_hub` — nose chamfer corrected, monotonic taper
