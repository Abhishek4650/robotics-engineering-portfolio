# ARM-450 rev I — every joint driven, verified part-against-part

2026-09-23. Supersedes rev H and `GO_RETRACTED.md`. Every number is measured
from the solids or from your own models (`Motor.stl`, `Motor_mount.stl`,
`motor fixer.stl`).

> ## J2 shoulder torque -- DECIDED (your choice: keep ST3215 + simple springs, no payload)
> Without springs, arm horizontal: J2 1.649 N·m (ST3215 SF 0.53 cont), J3 0.860 N·m.
> With the two gravity springs per joint, worst case over the whole range:
> **J2 SF 1.07, J3 SF 1.26** on the 0.88 N·m continuous rating. The arm moves
> itself; it is not rated for a payload held continuously.
> The latest verification is the **release pass at the end of this file**.

## What was wrong (all six joints)

| # | defect | where | fix |
|---|---|---|---|
| 1 | servo bay sized from the case **width** (24.72) not its depth along the output axis (33.10) — 6.9 mm short, 13.3 mm slop | J2 J3 J4 J5 | bay from the measured servo, **−0.22 mm pinch** (your motor fixer) |
| 2 | servo **front cap** (40×24×1.5 + step + horn) sank 2.61 mm into the floor | J1–J6 | servo seats on its **cap face**; floor relief for the step/horn |
| 3 | **horn drove nothing** — spun inside the Ø26 tube bore / slip-fit hub | J1–J6 | every horn **bolted** (4 × Ø2.52 on BCD 14, your Motor_mount pattern) to a shaft/hub keyed to the next link |
| 4 | J1 hub grubs **unreachable** (inside a solid spigot) | J1 | **D-key** plug in a D-bore, no grubs |
| 5 | J5 had **no axle** — blade floated between two empty bearings | J5 | printed axle through both bearings + blade, **D-key + grub**, spacers |
| 6 | J6 wrist built for a micro servo; you have an ST3215 | J6 | new J6 housing + tool flange |
| 7 | **drive bearing trapped** (shoulder + floor both in p1) — could never be fitted | J2 J3 J5 | pocket opens to the fork gap; presses in, floor lip holds the outer race |
| 8 | J2 idle bearing opened into the turret interior — no straight fitting path | J2 | presses in from the gap; Ø38 ring on the outer race |
| 9 | J4 horn screws only drivable from **inside the forearm** | J4 | forearm gets the proven socket end; J4 base bolts on like J3 |
| 10 | 0.0198 mm floating disc (a tenth of a layer) | J4_module | insert depth 7.5 → 8.0 (J4_module now superseded) |
| 11 | J1 mount walls hung in mid-air (unprintable) | J1 | foot prints upright; servo slides in to a locating wall |
| 12 | fork **split bolts** at r 20: inserts broke into the bearing pocket, and 2 of 4 ran **through the servo bay** (fork_pro says "clear of the bay and the bore" — neither was true) | J3 J5 | moved to r 25–30, outside every bearing, clear of the bay, on solid bosses |
| 13 | J4 **cap bolt shanks ran through the bearing**; J6 cap bolts on the bearing's edge | J4 J6 | moved out to r 21–23 |
| 14 | cap bolt heads under the rotating hub flange (0.5 mm gap) | J4 J6 | counterbored, heads below the cap top |
| 15 | 6706 race recess sized for a 6806 (wider than the bearing) | J5 | Ø34 for the 6706 |

## How each joint works now (the same pattern everywhere)

**Servo fixed to the previous link** in a −0.22 mm pinch channel, cap face on
a lip, a locating wall, a pedestal under the back — held on all six sides, no
strap. **Horn bolted** to a printed shaft/hub on the proven 14-mm pattern.
**Shaft/hub keyed to the next link** (shaft clamps + D-flat at J2/J3,
D-key at J1, bolted face at J4/J6, D-bore + grub at J5).

## Verification — every part against every other

| check | J1 | J2 | J3 | J4 | J5 | J6 |
|---|---|---|---|---|---|---|
| horn on axis | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| horn bolted to shaft/hub face | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| servo touches only lip/pinch/stop | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| servo clear of every other part | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| key/clamp transmits torque | D-key bites < 2° | clamps | clamps | bolted | D + grub | bolted |
| bearings installable | (base, released) | ✓ both | ✓ both | ✓ cap | ✓ both | ✓ cap |
| servo insertion path | slide ✓ | from P ✓ | from P ✓ | slide ✓ | from P ✓ | slide ✓ |
| failures | **0** | **0** | **0** | **0** | **0** | **0** |

**Bearings and bolts as solids** (`verify_hw.py`, 54 checks): every
bearing seats only on its OD and faces and touches nothing else; every split
and cap bolt clears the servo, the bearings, the shaft and the turning hubs.
Every bearing can be **fitted**: each one slides out along its fitting path
without touching the part.

**Whole-arm motion sweep**, 35 parts incl. 6 × ST3215, every joint through
its travel: **0 clashes**. Control (a block planted in the elbow arc)
detected (rise 309).

**Print gates:** 0 sub-layer, 0 unprintable on every part. All forks/shafts/
hubs island-free in their chosen orientation. Forearm halves carry the same
supportable edge strip the released link halves always had.

**Tool access:** all housing bolts reachable (70 mm clear driver runs); horn
screws through each shaft bore or hub counterbore; collar bolt A driver or key,
bolt B **hex key only** (base lip); J5 grub from the side between the cheeks.

Details: `REVI_CHECKS.log` (full run), `verify_*.py`, `sweep_arm.py`.

## Print list (rev I)

| part | qty | orientation (face up) | supports |
|---|---|---|---|
| `j1_mount` | 1 | +Z up | none |
| `j1_hub` | 1 | +Z up | advised |
| `J2_turret_p1` | 1 | +X up | REQUIRED |
| `J2_turret_p2` | 1 | -Y up | advised |
| `J2_shaft` | 1 | +Y up | none |
| `J3_p1` | 1 | +Y up | REQUIRED |
| `J3_p2` | 1 | -Z up | none |
| `J3_shaft` | 1 | -Z up | none |
| `link_fore_tongue` | 1 | +Z up (flat, web down) | REQUIRED (touching build plate) |
| `link_fore_groove` | 1 | +Z up (flat, web down) | REQUIRED (touching build plate) |
| `j4_base` | 1 | -Z up | advised |
| `j4_cap` | 1 | -Z up | none |
| `j4_hub` | 1 | -Z up | none |
| `J5_p1` | 1 | +X up | advised |
| `J5_p2` | 1 | -Z up | none |
| `J5_shaft` | 1 | -Z up | none |
| `J5_spacer` | 2 | +Z up | none |
| `j6_body` | 1 | -X up | advised |
| `j6_cap` | 1 | -X up | none |
| `j6_flange` | 1 | -X up | none |

Released parts still used unchanged: `base`, `spigot_collar` (rev H),
`shaft_clamp` ×4, `link_upper_groove/tongue` (you have printed these).
**No longer used:** `J4_module`, old `j6_body`, `tool_flange`, `servo_strap`,
`servo_strap_micro`, `j1_pod`, `j1_clamp`, `j1_drive_hub`, `j3_clamp`,
`j5_clamp`, `J5_strap`, and the **aluminium joint tubes** (replaced by printed
shafts, your choice).

## Hardware

* 6 × ST3215 (J2: see the torque decision)
* bearings unchanged from the released list: 6806 at J2/J3, 6706 at J4/J5/J6
* horn screws: 4 per joint × 6 = **24 × M2.5×6** (the size your Motor_mount's
  Ø2.52 holes took — check against your horn)
* M4 × 4 + 4 M4 heat-set inserts (J1 foot ↔ base)
* M3 heat-set inserts + bolts at every face joint; 1 × M3 grub (J5 blade)

## Assembly order (per joint)

* **J1** foot on the table → servo slides in to the stop → hub on the horn
  (screws from above) → base on the columns (M4 from inside the base) →
  turret down onto the hub's D → collar.
* **J2 / J3 / J5** bearings pressed into p1 from the fork gap → blade/links +
  clamps (or blade + spacers) into the gap → shaft in from the idle side →
  servo into p2 → p2 onto p1 (4 × M3) → horn screws through the shaft bore
  → tighten clamps / grub.
* **J4 / J6** base on the previous link → servo slides in → cap with bearing →
  hub/flange through the bearing onto the horn (screws from above) → next
  link on the hub.

## J2 torque — options

1. **ST3250 at J2 + a bolt-on counterbalance spring** (recommended): balances
   most of the 1.65 N·m; bolts to the turret and upper link without changing
   any printed part above.
2. **ST3250 at J2 only**: lifts through horizontal (stall SF 2.97) but should
   not hold horizontal for long; no payload margin.
3. **Lighten the wrist** (lower infill, trim): about −0.2 N·m — helps, does
   not close the gap on its own.

---

## Release pass -- 2026-09-24 (`release_run.sh`: REVI_CHECKS.log + FINAL_RUN.log)

Every stage 0: J1..J6 drive trains, bearings as solids, shaft clamps, every
fastener (94 screws / 61 inserts / 4 nuts), parameter audit (151 measured),
springs (49 poses), whole-arm sweep, print gates in the chosen print
orientation, static all-pairs interference, 6-DOF, tool access at each build
step, manual section check of each joint, slicer on the print-ready files.

Found and fixed in this pass (each measured first, then re-checked):

| finding | fix |
|---|---|
| released O38 shaft clamp cannot enter the link bores (seam ear, 2.3-3.0 mm) | C-clamp straddling the ear, gap 11.4 (~1 deg play), M3 grub on the D-flat |
| J2 shaft flat faced neither clamp grub | flat turned to face +X (one grub per clamp lands on it, measured) |
| J2 servo cover (turret p2) held by nothing -- cover-bolt axes in air | servo pod (2.4 shell round the servo) + 4 x M3x45 split bolts |
| J2 bay broke out of the turret outline (no back wall over x 7..35) | same pod |
| J3/J5 bays 35.99 deep, back wall 1.4 (fork generator cuts +1) | bay 34.99, wall 2.4 |
| -y spring-lug insert pockets missing (translate-then-mirror) | lug built on +y, mirrored whole |
| seam / ear screw heads 3 mm into the fork cheeks (1.0 mm gap) and under the forearm collars | counterbored tongue seam holes (O6.0x3.2, ear O5.0x2.7) |
| released upper tongue STL open along 8 boss/wall tangency lines | rev-I tongue with 3x1.2 webs (holes unchanged) |
| spigot-collar insert broke out of the O46 surface (78 % surround) | pads, insert 100 % embedded, flat entry face |
| M3x43 (not sold), cap bolts 0.22 mm off the floor, M4 base bolts bottoming | M3x45 / M3x12 / M4x12, pockets 8.1 deep |
| collar clamp bolt + 2.4 nut only 2.4 engaged | M3x45 + nyloc |
| forearm tongue/groove 0.27 mm overlap | groove recut after the boss union |
| checker bugs: turret_pro imported before its parameters (stale Z_DRIVE), probes through grub holes, section servo horn solid | fixed; each listed in the scripts |

6 DOF: axes measured from servo horns and from bearing pockets agree to
0.0000 deg / 0.0000 mm; spherical wrist; Jacobian rank 6 at every one of
3000 random poses in range; near-singular poses are only the three textbook
ones (elbow straight, wrist aligned, wrist centre over J1). Control caught.

Limits (accepted): simple gravity springs, no continuous payload (J2 SF 1.07,
J3 SF 1.26 worst case arm level).

---

## Rule 4 round -- 2026-09-24 (mate, never overlap; interact only through proper pathways)

New check `verify_mating.py` on the exact solids of the final assembly: every
touching pair classified by its real faces (planar mate / cylindrical fit /
graze), every part assigned to one of the 7 rigid bodies, contact across a
joint allowed only through that joint's bearing (right race, SKF d1/D1),
horn face or springs; every body must be reached from what drives it through
parts that TOUCH (clearance-only keys fail); every bolted joint must clamp
faces normal to the bolt. Controls: 3 of 3 detected. Result after fixes: 0.

| found | fixed |
|---|---|
| J1 hub D-plug in the spigot with 0.1 / 0.2 mm clearance: +-1.9 deg yaw play | spigot end slit into a collet; the spigot collar (slot 2.0, 1.10 needed) closes it on the plug |
| J2/J3 links hung on the clamp by +-0.2 mm clearances (+-1 deg) | 2 x M5 x 10 cup-point set screws per link half, self-tapped in the link's own O4.2 side holes, on double-D shaft flats; the ring only centres (0.025 fits) |
| turret underside land sat on the base and the upper 6806's outer ring | land only inside the inner ring (r 16.75 < d1/2 16.85) |
| J4/J6 stationary lips on the 6706's turning inner ring (r 15.5) | 0.5 mm relief to r 16.75 |
| J4/J6 caps overlapped the bearing by 0.01 mm (1.67 mm3) | pocket exactly BRG_W deep |
| J5 spacers floated 0.05 mm on both faces | exactly 3.0: the stack closes |
| grubs modelled 0.05 / 0.35 mm short, springs off their pins | every set screw, grub and hook modelled in its tightened state |

Also measured this round: the drive-bearing floor stands 0.5 mm clear of the
bearing (the earlier "floor lip bears on the outer race" was wrong): the
bearings are held by their press fit; use retaining compound.

Release pass after the fixes: 19 stages at 0 (REVI_CHECKS.log, FINAL_RUN.log).
Documents: ARM450_REV_I_FINAL.pdf (Rule 5 pages), ARM450_POSES.pdf (6 poses,
each clearance-checked), ARM450_PARTS.pdf (every part + measured details),
../EDITABLE_CAD/ (Rule 7), ../PRINTABLE_FILES/ (copied to USB).
