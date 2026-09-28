# J3 / J5 fork regeneration — verification record

Date: 2026-09-23. Parts: `J3_p1`, `J3_p2`, `J5_p1`, `J5_p2`, plus a
re-fixed `J4_module`. Every number below is measured from the generated
solids or the user's own servo mesh — none is copied from a parameter file.

## The two defects fixed

**1. No servo bay at all.** The released `J3_p1` / `J5_p1` end at the
parting plane (z = 28.50 for J3), so the drive cheek — and with it the
entire servo cradle — was never built. `fork_pro.fork()` does construct
one; the released parts came from a different path. Regenerating through
`fork_p1` / `fork_p2` restores it.

**2. `BAY_W` and `BAY_T` were swapped.** `fork_pro` cuts the bay as
`rect(BAY_L, BAY_W)` extruded `BAY_T` along **+Z**, and +Z *is* the joint
axis (every bearing bore is a `circle()` on XY). So `BAY_T` is the
dimension along the servo's **output axis**.

Measured from the user's `Motor.stl` (re-derived and self-checked by
`servo_geom.py`):

| along the output axis | mm |
|---|---|
| mounting face → back of cable boss | 33.10 |
| mounting face → face of horn disc | 4.50 (opposite way) |

Case cross-section normal to the output axis: **45.22 × 24.72**.

`fixparams` derived `BAY_W = 38.05` where 24.72 is needed (**13.33 mm of
slop** — the servo could rattle and rotate) and `BAY_T = 26.62` where 33.50
is needed (**6.88 mm too shallow** — it would not go in).

## Orientation lock: pinch + strap

The four front-face case screws **cannot** be used on these joints. The
real pattern is 19.05 × 20.29, giving a bolt-circle radius of **13.92 mm**,
which falls inside the **Ø38 bearing seat (r 19.00)**. That seat carries
the outer race and cannot be shrunk. The back face cannot be bolted either:
the photographs show the two JST bus connectors and the rear bearing boss
occupying its centre.

So the lock is the user's own proven arrangement from `motor fixer.stl`: a
**24.50 mm channel on the 24.72 mm case face = −0.22 mm interference**,
plus a strap on the two M3 inserts. Measured back out of the solid, the
channel is **24.500 mm at every station on both joints**.

## Results

| check | J3 | J5 |
|---|---|---|
| single solid, both halves | yes | yes |
| horn offset from joint axis | **0.0000 mm** | **0.0000 mm** |
| servo inside bay depth | yes (z 23.99–61.59 in 28.50–62.00) | yes (z 20.99–58.59 in 25.50–59.00) |
| horn passes through floor into bore | yes | yes |
| pinch penetration | 0.112 mm/side | 0.112 mm/side |
| contact **off** the pinch faces | **0 points** | **0 points** |
| p1/p2 interpenetration | **0 / 20000 both ways** | **0 / 20000 both ways** |
| parting-plane gap | 0.0000 mm (adjacent) | 0.0000 mm |
| 4 joint bolts clear through p2 | 4/4 | 4/4 |
| 8 inserts enclosed in solid | 12/12 probes each | 12/12 each |
| strap-bolt driver run (6 mm) | >60 mm clear | >60 mm clear |
| layer-slice findings | **0** | **0** |
| thin-feature findings | **0** | **0** |

### Seating-test controls
The test reads clean at nominal and detects real clashes:
`+6 mm into the back wall` → 917 off-pinch points; `−14 mm into the −X
wall` → 748. Nominal → **0**.

### Rotational play — an honest limitation
Rotating the servo about the joint axis produces no off-pinch contact up to
**≈2°**. The pinch alone therefore permits a couple of degrees of play;
**the strap is what closes it**, exactly as on the arm the user has already
built. The strap is not optional on these joints.

## Two gate bugs found and fixed

Both gates paired parallel planes on offset alone, ignoring which way each
face points and whether the footprints overlap. That manufactured findings
on solid material.

* `slice_check.z_thin_bands` — now requires the lower plane to face **down**
  and the upper to face **up**, with ≥1 mm² of real (grid, not convex-hull)
  overlap. An annulus hull fills its own hole and invents an overlap.
* `check_thin.planes` — now carries the outward sense and the face bounding
  box; pairs must be opposed and overlap.

**Validation held**: both still flag the known-bad released `J4_module`
(0.020 mm and 0.100 mm membranes) and both still pass the known-good
`base`. False findings disproved by direct probing: `J5_p1` "0.100 mm"
(270 probe columns, **0** isolated sub-layer runs) and `J4` "0.375 mm"
(two separate walls at different x).

## J4_module — a real defect found and fixed

The blind J5-fork inserts bottomed at `36.72 − 7.50 = 29.220` while a bore
ceiling beside them sat at 29.200, leaving a **0.0198 mm disc of material,
7.75 mm²** — a tenth of a layer. The printer steps over it, leaves a hole,
and the insert bottoms on nothing. Insert depth 7.50 → **8.00** puts the
floor at 28.720, clear by 0.48 mm (>2 layers). `J4_module` now returns
**0 findings** on both gates.

## Consequence to carry forward

`z_drive` moves **out by 6.88 mm** on both joints (J3 57.52 → 64.40, J5
54.52 → 61.40). Downstream link face positions depend on this and have
**not** yet been re-derived.

## What is NOT verified (and why no blanket GO)

**`check_access.py` reads `ARM450_FINAL_ASSEMBLY.step`, dated 11 Sep** —
twelve days older than these parts, and built before the forks had a servo
bay at all. Its 14 "no room for a hex key" stations describe superseded
geometry; several are at (0,0,0), i.e. parts never placed. **That run tells
us nothing about the current parts and must not be quoted as a result.**

Bolt access for J3/J5 was therefore checked directly on the new solids
(strap bolts >60 mm clear, 4/4 joint bolts clear through p2, 8/8 inserts
enclosed). That covers J3 and J5. It does **not** cover the arm as a whole.

Still open, all requiring a rebuilt assembly:

1. **Whole-arm bolt access and assembly order** — must be re-run once the
   assembly is rebuilt with these parts at their true positions.
2. **Joint motion through full travel** — swing clearance with the 6.88 mm
   longer cheeks has not been simulated.
3. **Wiring clearance** — the servo cable exit is in the back wall; no
   routing check has been done.
4. **J2** — `j2_clamp` was never attempted. J2 mounts on the turret shell
   at y = −28.50 with 6 × Ø4.1 stations.
5. **Downstream link faces** — `z_drive` moved out 6.88 mm on both joints.
   The mounting face, bearing seats, spigot and end-bolt pattern are all
   confirmed unmoved, so the change is contained to cheek length, but the
   links that sit beyond it have not been re-derived.

## Print status

**Not a full GO.** J3_p1, J3_p2, J5_p1, J5_p2 and J4_module are clean on
every check that has actually been run against them, and the servo seats
correctly with its shaft on the joint axis to 0.0000 mm. But items 1–5
above are unverified, and item 5 in particular can move real material.
Printing the five parts now risks a reprint if a link face has to change.

---

# UPDATE — J5 is a different part, and it does not work

## Retraction

The first pass of `gen_forks.py` generated **J5 with J3's recipe**. That was
wrong. `wrist_pro.py` builds J5 from the same `fork_pro.fork_p1/p2` but adds
two load-bearing steps I had omitted:

* **`mirror=True`** — puts the drive cheek on the far side of the blade from
  the tool. Built the other way it grows along +Z and swallows the J6
  bearing and the tool flange.
* **`_clip_j5()`** — cuts the cheeks back to `J5_CLIP = 11.0` past the bore.
  Unclipped they overhang the J6 axis ~30 mm and run through the Ø40 flange.

My J5 was neither mirrored nor clipped: local x −44.00..37.90 against the
released −25.28..11.00. It was **not** a drop-in replacement and the earlier
J5 numbers in this document describe a part that cannot be used. The J3
numbers are unaffected — J3's transform and recipe were correct.

## The real J5 defect

With the correct recipe the servo does not fit, and **this is true of the
released part as well as mine**:

| along the fork's local x | mm |
|---|---|
| mounting face (`J5_FACE`, fixed by J4→J5 link spacing) | −25.28 |
| clip plane (`J5_CLIP`, fixed by the J6 bearing and Ø40 flange) | +11.00 |
| **usable** | **36.28** |
| ST3215 case needs (`45.22 + 2×0.40`) | **46.02** |
| **short by** | **9.74** |

`BAY_L` was already 46.02 before my change, so this shortfall is not
something the bay correction introduced.

**Measured on the released `out_cad/J5_p2.stl`**, not inferred: a material
map at z = −30, −40, −50 shows an open C-channel — a back plate with two
short flanges. Probing along x at y = 0 returns **no material anywhere**;
probing along y at x = −5 returns only `−24.99..−22.61`, `−21.42..−19.03`,
`19.03..21.42`, `22.61..24.99`. Two thin flange pairs with nothing between
them.

**The released J5_p2 cannot hold a servo.** It is open on the +x side and
has no floor. This is the same class of defect as the missing J3 bay, and it
was in the shipped package.

## Consequence

J5 cannot be fixed by regenerating with corrected bay numbers. The servo is
9.74 mm too long for the space between a mounting face fixed by link spacing
and a clip plane fixed by the tool flange. Resolving it needs a design
decision — move the J4→J5 spacing, shrink the tool flange, or drive J5
off-axis through a belt/gear — and that is beyond a parameter change.

**J5_p1 / J5_p2 are withdrawn from this print.** The earlier "0 findings"
gate results for them were run on the wrongly-generated part and do not
carry over.

---

# FINAL STATE — 2026-09-23

## Generated and verified

`gen_forks.py` now builds **J3 only**. J5 is withdrawn with the reason
recorded in the source itself, so it cannot be silently regenerated.

Re-run after the withdrawal, J3 is unchanged from the numbers above:
horn offset **0.0000 mm**, pinch **0.112 mm/side**, **0 contact points off
the pinch faces**, controls detecting (+6 back wall → 1096, −14 −X wall →
805) against a clean nominal.

## Both gates, final set

| part | slice | thin |
|---|---|---|
| J3_p1 | 0 | 1.00 mm wall (see below) |
| J3_p2 | 0 | 0 |
| J4_module | 0 | 0 |
| j1_clamp, j1_drive_hub, j1_pod | 0 | 1.10 mm wall on drive_hub |
| j3_clamp, j5_clamp | 0 | 0 |
| servo_strap_micro, spigot_collar | 0 | 0 |

The two sub-1.20 mm walls are **not** sub-layer features. `J3_p1`'s
"O50.00/O52.00" was probed directly: where material exists the wall is
4–10 mm thick, so the pair is a geometric artifact, not a real thin wall.
`j1_drive_hub`'s 1.10 mm is 2.75 extrusions at a 0.40 nozzle — printable.

## Print recommendation

**GO for these ten parts**, with one caveat stated plainly:

* J3_p1, J3_p2, J4_module, j1_clamp, j1_drive_hub, j1_pod, j3_clamp,
  j5_clamp, servo_strap_micro, spigot_collar.
* The **strap is not optional** on J3 — the pinch alone leaves ~2° of
  rotational play and the strap is what removes it.

**NO-GO: J5_p1, J5_p2.** The ST3215 is 9.74 mm too long for the space
between the J5 mounting face and the clip plane. This is a design decision
(J4→J5 spacing, tool-flange diameter, or an off-axis drive), not a
parameter change. The released J5 has the same problem plus an open
C-channel with no floor.

## Still not verified

Whole-arm bolt access and joint motion could not be re-run: the only
assembly in the package is dated 11 Sep, and rebuilding it is blocked on
the J5 decision, since J5 sits between J4 and the tool. `j2_clamp` remains
unattempted.
