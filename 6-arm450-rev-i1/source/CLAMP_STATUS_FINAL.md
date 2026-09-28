# J3 / J5 servo clamps — where this stands, and what I recommend

**Date:** 2026-09-23 · **Verdict: NOT READY TO PRINT**

---

## What is solved

| requirement | j3_clamp | j5_clamp |
|---|---|---|
| **shaft on the joint axis** | **0.000 mm** | **0.000 mm** |
| servo gripped, 0.22 mm pinch | yes | yes |
| single solid | **1** | **1** |
| thin features (2-method gate) | **0 confirmed** | **0 confirmed** |
| bolts land on host material | yes, measured | yes, measured |
| **clamp vs host interpenetration** | **671 pts** | **213 pts** |

The two hardest requirements — shaft on the joint axis, servo orientation
locked by geometry — are met exactly. **The flange-to-fork interface is not.**

---

## Seven flange positions tried, each refuted by measurement

| # | change | result |
|---|---|---|
| 1 | flange at x = −35 (mid-plate) | 377 pts inside host |
| 2 | bolts at (±17, ±7), the fork's own stations | those stations are in **VOID** — J3's pad is only y ±11, z −10…+11 |
| 3 | bolts re-measured to (±10, ±6) / (±17, ±5), flange on outer face | channel ran into the fork interior, 316 pts |
| 4 | channel shortened 45.22 → 22.00 mm | channel cleared; **flange** now overlapped, 375 pts |
| 5 | flange profiled to the 22 × 21 pad | exported as **2 disconnected solids** — the pad is too small to reach walls 28.1 mm apart |
| 6 | mount on the full-width slab instead | flange grew outward through the narrow pad, 915 pts |
| 7 | flange grown inward, sized 42 × 42 to the measured 44 × 44 free envelope | still 671 / 213 pts |

**A measurement error of mine, corrected:** at step 6 I probed the host
manually at z = 0 only and concluded "void — the overlap is a false positive".
Re-probing the actual reported points showed the overlap is **real**, at the
fork cheek corners y = ±23, z = ±20. The coarse manual grid missed them. Both
hosts are watertight and winding-consistent, so containment is reliable.

---

## Why this keeps failing

`J3_p1` and `J5_p1` are **open forks with curved cheeks**, not boxes with flat
mounting faces. Cross-sectioned at z = 0, J3_p1 is a narrow stem (y ±11) that
steps out to a full-width slab and then opens entirely. Any rectangular flange
large enough to carry a 24.50 mm channel reaches into either the stem, the
cheeks, or the bay walls.

**The fork was never designed to carry a servo mount** — which is the same
finding as `NO_SERVO_POCKETS.md`, seen from the other side.

---

## Recommendation — change the design, do not keep patching

Per your rule: *if it is fixable, fix it; otherwise change the design.* This is
the second case.

**Modify the HOST, not the clamp.** Add a flat mounting pad to `J3_p1` and
`J5_p1` at the generator — a boss on the outboard face, sized to the clamp
flange, with the four M3 stations in it. That is one feature per part, it
gives the clamp a real flat face to sit on, and it removes every interference
above at a stroke.

That does mean reprinting `J3_p1` and `J5_p1`. The alternative — more flange
shapes against a curved fork — has now failed seven times and I do not
recommend an eighth.

**Not a blocker for the rest of the arm.** `j1_clamp`, `J4_module`, `j6_body`,
`spigot_collar`, `j1_drive_hub` and `servo_strap_micro` are all verified and
unaffected.
