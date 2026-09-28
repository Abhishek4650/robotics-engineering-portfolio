# J3 / J5 servo mounts — decision required

**Date:** 2026-09-23 · **Status: NOT READY TO PRINT. No GO.**

---

## What is solved, and it is the hard part

| | j3_clamp | j5_clamp |
|---|---|---|
| **shaft on the joint axis** | **0.000 mm** | **0.000 mm** |
| servo orientation locked by 0.22 mm pinch | yes | yes |
| single solid | 1 | 1 |
| thin features (two-method gate) | **0 confirmed** | **0 confirmed** |
| bolt stations on real material | measured, yes | measured, yes |

## What is not

**The clamp body still intersects the host.** Nine configurations tried:

| # | change | overlap |
|---|---|---|
| 1 | flange mid-plate x = −35 | 377 |
| 2 | fork's own (±17, ±7) bolts | those stations are in **VOID** |
| 3 | re-measured bolts, flange on outer face | 316 |
| 4 | channel shortened 45.22 → 22.00 | 375 |
| 5 | flange profiled to the 22 × 21 pad | **2 disconnected solids** |
| 6 | mount on the full-width slab | 915 |
| 7 | flange inward, sized 42 × 42 to the free envelope | 671 / 213 |
| 8 | **added a 42 × 42 × 6 pad to the host, pad on −X** | 1212 / 1064 |
| 9 | **pad moved inboard (+X)** | 1491 / 1210 |

Adding the pad moved the conflict rather than removing it: the servo channel
must run **+X toward the joint axis**, and the pad now occupies that path.

**A measurement error of mine, corrected along the way:** at step 6 I probed
the host at z = 0 only and called the overlap a false positive. Re-probing the
reported points showed it is **real**, at the fork cheek corners y = ±23,
z = ±20. Both hosts are watertight, so containment is reliable.

---

## Why no flange shape works

`J3_p1` and `J5_p1` are **open forks with curved cheeks**. The joint axis runs
through the middle of the open bay, and the servo — 45.22 mm long with its
horn 12.50 mm off-centre — must sit *in that bay* with its shaft on the axis.
Anything that holds it there occupies the bay. Anything bolted to the fork
walls reaches across it.

**These forks were built for a servo buried in a thick drive cheek** (the
`fork_pro` design, `z_bay = 28.50`, drive cheek to `z_drive = 57.52`). The
released parts do not have that cheek — `J3_p1` ends at exactly 28.50. The
servo mount was never built, and the fork geometry has no room to bolt one on.

---

## The two honest options

**A — Regenerate `J3_p1` and `J5_p1` from `fork_pro.py` with the drive cheek
intact.** That is the design as intended: servo buried in the cheek, shaft
through the bearing bore already on the axis, no clamp needed. Cost: both
parts change shape and must be reprinted, and the downstream link faces move.

**B — Keep the released forks and accept an external servo pod** bolted to the
link *behind* the fork, driving the joint through a short shaft or coupling.
Cost: a new part and a longer torque path, but the forks print as-is.

**Recommendation: A.** It is the design the rest of the arm was dimensioned
for, `fork_pro.py` already exists, and it removes the problem rather than
routing around it. B adds a coupling to a joint that already has a bearing
pair sized for a direct drive.

---

## Unaffected and verified

`j1_clamp`, `J4_module`, `j6_body`, `spigot_collar`, `j1_drive_hub`,
`servo_strap_micro` — all pass their gates and are independent of this
decision.

**I am not issuing a print GO while J3 and J5 have no working servo mount.**
