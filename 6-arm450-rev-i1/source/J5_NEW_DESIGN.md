# J5 — new design, not a modification

The released J5 could not be fixed by changing parameters: the ST3215 was
9.74 mm too long for the 36.28 mm between two faces that cannot move, and
the released `J5_p2` was an open C-channel with no floor. Patching it would
have meant moving J4→J5 spacing or the tool flange — disturbing parts that
are already correct. So J5 is redesigned from scratch in `gen_j5_new.py`.

## The insight: rotate the servo, don't make room

The old design ran the servo's **45.22 mm case length along local x** — the
one direction boxed in between the mounting face (−25.28, set by J4→J5
spacing) and the clip plane (+11.00, set by the J6 bearing and Ø40 flange).

At **J3, which works**, the case length runs *along the arm* and the output
axis runs *across* it. Measured with J5 removed from the assembly, the only
thing near the J5 axis is `j6_body` at |y| ≤ 15.00 — beyond that the space
is open.

So the new J5 uses J3's topology exactly:

| | direction | extent | obstructed? |
|---|---|---|---|
| output axis | local Z (joint axis) | 37.60 | on the bore |
| case length | local X (along the arm) | 45.22 | **open** |
| case width | local Y (across) | 24.72 | **open** |

**The arm stays 450 mm.** No link lengthening was needed — the fix is
orientation, not space. J4, j6_body and tool_flange are untouched.

## Stack, outboard from the blade face

```
fork gap        16.00   J5_GAP, 1.00 mm clearance per side on the blade
bearing seat     2.00   6706 outer race lands here
bearing          4.00   6706, 30 x 37 x 4
bay floor        4.00   carries the Ø24 horn bore
servo bay       33.50   measured: mounting face -> back of case + 0.40
back wall        2.40
                -----
                61.90   z_drive
```
Parting plane at z = 26.00.

## Two things the first attempt got wrong

* **The case is not symmetric about the output axis.** The horn sits
  12.50 mm off the case centre, so centring the bay on the bore left the
  case hanging 12.10 mm past the +x wall. The bay is offset by `BAY_OFF`.
* **A Workplane's pending wires are consumed by the first `.extrude()`.**
  Reusing one raised "No pending wires present". It is now a function.

## Flange clearance — clip the corner, not the extension

The drive cheek needs a racetrack extension to x = 37.91 to wrap the case.
Mapped into this part's local frame, `tool_flange` occupies x ≥ 24.00 with
|z| ≤ 19.85, so the two overlap in one corner. The cut removes **only that
corner**. Clipping the whole extension is what left no room for the servo
in the released design.

## Verification

| check | result |
|---|---|
| all three parts single solids | yes |
| horn offset from joint axis | **0.0000 mm** |
| servo inside bay | x −10.11..35.11, z 21.49..59.09 in 26.00..59.50 |
| contact **off** the pinch faces | **0** |
| pinch penetration | 0.112 mm/side (−0.22 design interference) |
| vs `tool_flange` | **clear** |
| vs `j6_body` | **clear** |
| vs `J4_module` | 0.0000 z-spread = coincident mating face, 0 points inside |
| p1/p2 interpenetration | **0 / 20000 both ways**, gap 0.0000 |
| 4 joint bolts through p2 | 0/300 blocked, all 4 |
| 4 inserts in p1 | surround 12/12 each |
| layer-slice | **0 findings** (p1, p2, strap) |
| thin-feature | 1.150 mm slab on p1 — above the 0.80 mm wall floor |

Controls detect: +6 mm into the back wall → 599 off-pinch, −14 mm into the
−X wall → 977, 5° rotation → 126. Nominal → **0**.

**The strap is not optional.** As at J3, the pinch alone leaves ~2° of
rotational play; the strap closes it.
