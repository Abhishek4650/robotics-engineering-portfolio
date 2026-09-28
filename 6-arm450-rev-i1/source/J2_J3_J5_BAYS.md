# J2 / J3 / J5 servo bays — checked

**Date:** 2026-09-22

---

## Result: the bays exist and are the right size

Every joint carries wall pairs at exactly the design bay dimensions:

| part | wall pair found | along |
|---|---|---|
| `J2_turret_p1` | **BAY_L 46.00** | Y |
| `J3_p1` | **BAY_L 46.00** | Z |
| `J5_p1` | **BAY_W 38.00** (×3) | Z |
| `J5_p2` | **BAY_W 38.04** | Y |
| `J4_module` | **BAY_W 38.04** and **BAY_L 46.00 / 46.02** | Y and X |

`BAY_L = 46.02`, `BAY_W = 38.05` from `fixparams.py`. The measured pairs match
to within 0.05 mm.

**No J1-style defect here.** J1 failed because `j1_pod` is a round **bore**:
with the horn on the joint axis the case centre sits 12.50 mm off-axis and the
far corner swings to r = 37.22 against a 35.70 bore. J2, J3 and J5 use
**rectangular pockets**, where the case sits square against flat walls and
that far-corner constraint never arises.

---

## A false alarm I generated, and why

My first pass reported:

```
J2  REAL SERVO DOES NOT FIT at any of the 6 most open candidates
J3  REAL SERVO FITS at (0.61, -0.10, -0.14), margin 23.95 mm
J5  no room for the case footprint in any orientation
```

**All three are wrong.** The parts are open forks, not closed boxes:

| part | solid volume | % of bounding box |
|---|---|---|
| `J2_turret_p1` | 121 334 mm³ | **16.3 %** |
| `J3_p1` | 50 403 mm³ | **23.2 %** |
| `J5_p1` | 26 514 mm³ | **30.5 %** |

So "free space inside the bounding box" is mostly **open air outside the
part**. The J3 "fit" with a 23.95 mm margin was the servo floating in space
beside the fork, not seated in a bay. The J2 and J5 failures were the search
grid never landing on the actual pocket.

A bounding-box void scan cannot locate a pocket in an open part. Detecting the
**wall pair at the design bay dimension** can, and does.

---

## What is still not verified

The wall pairs prove the pockets are the right **size**. They do not prove:

1. **that the real servo seats in them without fouling** — a mesh-vs-mesh test
   at the true pocket origin, as done for J4, has not been run for J2/J3/J5.
   J4's pocket could be derived exactly from the generator; these cannot
   without locating each pocket's origin first.
2. **that a hand and driver can reach the strap bolts** once the servo is in.

Both need the pocket origin per joint. That is a bounded piece of work, not a
search.

---

## J1 — pod dropped

`j1_pod` is **removed from the print set**. Measured, with `j1_clamp` holding
the servo it carries:

* **no structural load** — it has no bolt holes to the base, and nothing in
  the assembly mates to its Ø32.00 register or Ø71.20 bore
* its only unique feature was a **Ø8 cable exit**, now cut into `j1_clamp`
* **44 g of PLA and 230 print layers**

If you want a dust shroud later it can be reprinted unchanged — nothing else
depends on it.
