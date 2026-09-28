# ARM-450 rev I.1 -- print-ready files

**PRINT STATUS (2026-09-24 audit, J3_p1 re-verified 2026-09-27): see `PRINT_STATUS.txt`. Print the fit test
first; when coupon 07 screws onto the back of your servo, print everything.**

## rev I.1 (2026-09-27): reprint `12_J3_p1` only

Your slicer view was right: the two J3 spring lugs stood on the round cheek tops joined
by a 0.1 mm sliver (corners 0.4 mm in the air). They are now sunk 1.5 mm into the cheeks
and blended in by R3 webs (joint area 34 -> 136 mm2). Every other file is unchanged.

Every STL in `STL_print_ready/` is already rotated to its checked print
orientation and set on the bed. Print the quantity in the file name.
`STEP_design_frame/` holds the same parts in their design frame.

## Print the fit test FIRST (`00_FIT_TEST_print_first/`, about 2 h)

Coupon 07 is a copy of a servo cover's back: lay it on the BACK of a servo and drive the
4 self-tapping screws from the servo box -- they must line up, bite and pull it flat.
If they do not line up, stop: every servo mount uses these holes.
The key fits are finer than an FDM printer's accuracy (+-0.1..0.2 mm): bearing
seats O42.00 / O37.02, printed shafts O29.95 in 30 mm bores, the -0.22 mm servo
pinch, the 0.025 mm centring-ring fit. The six coupons carry exactly those fits.
Print them with the settings you will use for the arm; if a bearing does not press
in, a shaft does not slide or the servo rattles, tune the slicer's XY hole / contour
compensation (or tell me the measured numbers) before printing the big parts.

## Changed by the 2026-09-24 audit (reprint these if you printed the earlier set)

`j1_mount` (idler-horn pocket, 4 table holes, end wall 7.0), `base` (foot floor 3.0 mm),
`spigot_collar`, `J3_p2`, `J5_p2` (2.4 mm shell round the bay), `J5_shaft` (flat to
the idle end), `j4_base` (idler-horn pocket), `j4_cap`, `j6_body`, `j6_cap`,
`shaft_clamp`, `link_fore_tongue`, `link_fore_groove`, `link_upper_tongue` (cable skin
1.2 mm); servo-screw pads / posts / bridge and new wire windows in `j1_mount`,
`J2_turret_p2`, `J3_p2`, `J5_p2`, `j4_base`, `j6_body`. `ARM450_AUDIT_REPORT.pdf` says why.

## Print list

| file | qty | orientation used | supports | size (mm) | note |
|---|---|---|---|---|---|
| `01_base_x1.stl` | 1 | +Z up | REQUIRED | 120 x 120 x 50 | rev I: lower 6806 pocket opens from underneath |
| `02_spigot_collar_x1.stl` | 1 | +Z up | none | 46 x 46 x 12 | split clamp + J1 collet closer, slot 2.0, 1 x M3 pinch bolt |
| `03_j1_mount_x1.stl` | 1 | +Z up | none | 128 x 128 x 70 | J1 servo mount + the arm's foot |
| `04_j1_hub_x1.stl` | 1 | +Z up | advised | 29 x 29 x 17 | J1 horn coupler, D-keys the turret |
| `05_J2_turret_p1_x1.stl` | 1 | +X up | REQUIRED | 138 x 70 x 84 | turret; spigot end slit as a collet (J1 zero play); land on the 6806 inner ring only |
| `06_J2_turret_p2_x1.stl` | 1 | -Y up | advised | 83 x 66 x 37 | J2 servo pod (2.4 shell round the whole servo), 4 x M3x45 split bolts |
| `07_J2_shaft_x1.stl` | 1 | +Y up | none | 30 x 30 x 50 | printed J2 shaft, bolts to the horn; double-D flats for the M5 set screws |
| `08_shaft_clamp_x4.stl` | 4 | -Z up | none | 37 x 38 x 14 | link centring ring (0.025 fits); links locked by 2 x M5 set screws each |
| `09_link_upper_groove_x1.stl` | 1 | +Z up | advised | 110 x 50 x 14 | released, unchanged (reuse your printed one) |
| `10_link_upper_tongue_x1.stl` | 1 | +Z up | advised | 110 x 50 x 16 | rev I: released + head counterbores (or drill yours: O6.0x3.2 seam, O5.0x2.7 ear) |
| `11_collar_upper_x2.stl` | 2 | +Z up | none | 64 x 24 x 10 | J2 spring collar, print 2 (same part) |
| `12_J3_p1_x1.stl` | 1 | -Z up | REQUIRED | 98 x 50 x 53 | J3 fork; J3 spring lugs (both pockets) |
| `13_J3_p2_x1.stl` | 1 | -Z up | none | 72 x 50 x 37 | J3 servo cradle, bay 34.99 deep, 2.4 back wall |
| `14_J3_shaft_x1.stl` | 1 | -Z up | none | 30 x 30 x 50 | printed J3 shaft, double-D flats for the M5 set screws |
| `15_link_fore_tongue_x1.stl` | 1 | +Z up | advised | 144 x 50 x 16 | rev I forearm: socket end, valid solid, flush seam-screw heads |
| `16_link_fore_groove_x1.stl` | 1 | +Z up | advised | 144 x 50 x 14 | rev I forearm: socket end, valid solid |
| `17_collar_fore_x2.stl` | 2 | +Z up | none | 64 x 24 x 10 | J3 spring collar, print 2 (same part) |
| `18_j4_base_x1.stl` | 1 | -Z up | REQUIRED | 57 x 38 x 65 | J4 servo base; lip tops relieved off the 6706 inner ring |
| `19_j4_cap_x1.stl` | 1 | -Z up | none | 58 x 45 x 10 | J4 cap, holds the 6706 |
| `20_j4_hub_x1.stl` | 1 | -Z up | none | 46 x 46 x 20 | J4 hub, carries the J5 fork |
| `21_J5_p1_x1.stl` | 1 | +X up | advised | 48 x 50 x 66 | J5 fork |
| `22_J5_p2_x1.stl` | 1 | -Z up | none | 66 x 50 x 37 | J5 servo cradle, bay 34.99 deep, 2.4 back wall |
| `23_J5_shaft_x1.stl` | 1 | -Z up | none | 30 x 30 x 45 | printed J5 axle |
| `24_J5_spacer_x2.stl` | 2 | +Z up | none | 32 x 32 x 3 | blade spacers, exactly 3.0 (close the J5 stack), print 2 |
| `25_j6_body_x1.stl` | 1 | -X up | REQUIRED | 43 x 54 x 87 | J5 blade + J6 servo housing |
| `26_j6_cap_x1.stl` | 1 | -X up | none | 45 x 58 x 10 | J6 cap, holds the 6706 |
| `27_j6_flange_x1.stl` | 1 | -X up | none | 46 x 46 x 20 | tool flange, bolts to the J6 horn |

**Supports:** 'REQUIRED' = touching build plate is enough except J2_turret_p1 and
J3_p1 (bearing pockets): use everywhere. 'advised' = small overhangs, supports
make them cleaner. Forearm/upper link halves print flat, web down, with
build-plate supports (same as the released link halves).

**Suggested settings (PETG or PLA+):** 0.2 mm layers, 4 perimeters, 40 %
gyroid infill; shafts, hubs and the tool flange 100 % infill (they carry
the joint torque). Heat-set inserts after printing.

## Bought hardware

| item | qty |
|---|---|
| item | qty |
|---|---|
| 6706 bearing (30x37x4) | 4 |
| 6806 bearing (30x42x7) | 6 |
| M2.5 heat-set insert | 2 |
| M2.5 x 16 socket head | 2 |
| M2.5 x 6 socket head (horn) | 24 |
| M3 heat-set insert | 55 |
| M3 nyloc nut | 4 |
| M3 x 10 socket head | 12 |
| M3 x 12 socket head | 16 |
| M3 x 16 socket head | 10 |
| M3 x 20 socket head | 1 |
| M3 x 4 set screw | 1 |
| M3 x 45 socket head | 16 |
| M4 heat-set insert | 4 |
| M4 x 12 socket head | 4 |
| M5 x 10 set screw (cup point) | 8 |
| ST3215 servo | 6 |
| extension spring J2 (7.4 N @ 36.0 / 12.4 N @ 58.2 mm, inside hooks) | 2 |
| extension spring J3 (2.2 N @ 43.0 / 5.0 N @ 91.4 mm, inside hooks) | 2 |
| self-tapping screw ~2.2 x 8 pan head (from the servo box) | 20 |

Plus the six ST3215 servos' own horn screws are replaced by the M2.5 x 6 above.
Every screw above was placed in the model and checked as a solid: runs free in its
hole, engages its insert / nut / horn >= 3 mm (M3), head seated, tip clear of the
pocket floor (`REV_H/FASTENER_CHECK.log`). Lengths are standard sizes -- do not
substitute longer ones: several would bottom out.

## Your already-printed upper link

The released **groove** half is reused as printed. The **tongue** half needs flush
screw heads (its outer face runs 1.0 mm from the turret cheek, a standard head
stands 3 mm proud and jams J2). Either print the rev-I tongue in this folder, or
counterbore yours by hand from the OUTER face: O6.0 x 3.2 mm deep on the four
O3.4 seam holes, O5.0 x 2.7 mm on the ear hole next to the clamp bore.

## Assembly notes that matter

* Link lock (J2, J3): before assembly, run an M5 screw into each link half's two
  O4.2 side holes (90/270 deg) to form the thread. Slide a centring ring into each
  half with its gap over the seam ear, put the link on the shaft, then drive the
  2 x M5 x 10 cup-point set screws per half through the side holes onto the shaft's
  two flats. Zero play; the ring only centres.
* Fork floors (J3 fork on the upper link, J5 fork on the J4 hub): 4 x M3 x 10 each, heads
  sunk in the floor's counterbores (they sit under the swinging link / blade).
* J1: the spigot end is slit (a collet). Tighten the spigot-collar pinch bolt LAST,
  after the hub is on the horn: it closes the spigot onto the hub plug.
* J5: the two 3.0 mm spacers close the blade stack between the inner rings with no
  play; if a print is thick, sand the spacer until the axle slides home.
* Bearings (J2, J3, J5 drive side): each presses into its pocket from the fork gap
  and is held by that press fit (seat O42.00 / O37.00, measured); the floor behind it
  stands 0.5 mm clear, so it never touches either ring. Add a drop of bearing-
  retaining compound (e.g. Loctite 641) on the outer ring so it cannot creep.
* J2/J3/J5 servo covers (p2) close with 4 x M3 x 45 each into p1's inserts.
* EVERY SERVO IS SCREWED BY ITS OWN BACK HOLES with the self-tapping screws from its
  box (~8 mm; 2.6 mm go into the servo -- a longer screw needs a washer). J2/J3/J5: 4
  through the cover, heads on its outer face, after the M3 x 45s. J1: 4 from UNDER the
  foot plate, before the foot goes on the table. J4: 2 from under the J4 base plate (in
  the finished arm the forearm spring collars cover them). J6: 2 through the bridge over
  the servo's far end, on the bench before the blade goes into the J5 fork.
* J5 axle: its flat runs out of the idle end; turn the flat to the blade's D-bore
  and slide it in from the idle side (checked free both ways, in and out).
* Fix the foot to the table: at full reach the arm's centre of mass is 118 mm from
  the J1 axis, the foot's radius is 64 mm -- unfixed, it tips. Drive 4 x M5 bolts
  (or #10 wood screws) through the O5.5 holes in the foot plate BEFORE the base goes
  on (the base covers them), or clamp the foot plate to the table.
* The real ST3215 has a O19.2 idler horn on its back face that turns with the
  output. The J1 foot, the J4 base and the J6 body have a O20.4 pocket for it; the
  fork bays J2/J3/J5 clear it by 0.95 mm. Keep the pocket clean of stringing.
* Servo cables: both bus sockets sit in a slot across the servo's back face, 11.7-16.7 mm
  from the output axis (manufacturer's model, matches your photo). Plug both cables in
  BEFORE closing a cover: J2/J3/J5 wires leave straight out through the 12 x 20 window
  in the cover (1.05 mm to spare), J1/J4/J6 wires run along the channel under the servo
  (checked: REV_H/WIRING_CHECK.log). Leave a service loop at every joint.
* Plug slots: every plug can go in and out with the arm assembled (REV_H/PLUG_INSERT.log):
  J2/J3/J5 straight through the cover window; J1/J4 lift it 10 mm, move it a few mm to
  the side, then out past the open end of the servo channel; J6 lift 14 mm, then out
  sideways. Long-nose pliers help at J1/J4/J6.
* Temperature: the J2 servo runs near its continuous rating in a closed pod. Read the
  ST3215 temperature register in your control code and back off if it climbs.
* Heat-set inserts: every pocket is sized for 4.1 mm OD x 5.7 mm M3 inserts
  (M4: 5.6 x 8; M2.5 ear insert: 3.5 x 4).

## Cables: one joint per cable, nothing can wind up

The bus is a daisy chain (controller -> J1 -> ... -> J6). Each cable crosses ONE joint -- the
one driven by the servo it leaves -- and no joint turns more than 180 deg in total, so a cable
only flexes back and forth. Leave the loop below at each joint and tie the cable down on both
sides of it (REV_H/CABLE_ROUTE.log):

```
  cable      crosses range        exit r from axis         span min..max (mm)     change     loop / cable
  J1 -> J2   J1      +-90.0       40.0 mm (bound   80)      144.6 .. 179.0         34.5 mm    54 / 263 mm
  J2 -> J3   J2      +-54.0       14.8 mm (bound   24)      184.1 .. 200.7         16.6 mm    37 / 267 mm
  J3 -> J4   J3      +-72.0       14.8 mm (bound   28)      141.6 .. 155.1         13.5 mm    33 / 219 mm
  J4 -> J5   J4      +-90.0       40.0 mm (bound   80)      106.8 .. 148.4         41.6 mm    62 / 240 mm
  J5 -> J6   J5      +-46.5       14.8 mm (bound   21)       74.6 .. 85.3          10.7 mm    31 / 146 mm
  J6 is the last servo on the bus: no cable leaves it
```

## Gravity springs (buy to these two points each)

Lengths are **inside the hooks** (on the O3 pins; pin centre to pin centre is 3.0 mm less).
A spring with initial tension is fine as long as it passes through both points.

* J2 x2: **7.4 N at 36.0 mm** and **12.4 N at 58.2 mm** inside hooks (rate 0.224 N/mm)
* J3 x2: **2.2 N at 43.0 mm** and **5.0 N at 91.4 mm** inside hooks (rate 0.056 N/mm)
* each hooks over an M3 x 12 screw in a heat-set insert, 5 mm spacer under the hook

## What the springs buy -- and the limit

Arm held level, worst case over the whole J2 x J3 range, ST3215 continuous
0.88 N.m: J2 0.824 N.m (SF 1.07), J3 0.701 N.m (SF 1.26). **The arm moves
itself; it is not rated for a payload held continuously** (your choice:
simple springs, no payload).

## Build sequence (the order every screw was checked to be reachable in)

 1. foot: J1 servo into the foot, its 4 screws from under the foot plate
 2. J1 hub onto the horn
 3. base + J1 bearings onto the foot
 4. turret p1 + J2 bearings, spigot collar
 5. BENCH upper link
 6. BENCH J2 servo + shaft
 7. JOIN link into the J2 gap, servo+shaft down the axis
 8. J2 pod on, servo screws, link set screws
 9. J3 fork p1 onto the upper link
10. BENCH forearm
11. BENCH J4 base on the forearm
12. BENCH J4 servo (2 screws from under the plate), bearing, cap
13. BENCH J4 hub onto the horn
14. BENCH J5 fork p1 onto the hub
15. BENCH blade: J6 servo, bearing, cap
16. BENCH blade: tool flange onto the J6 horn
17. BENCH J5 servo + axle
18. JOIN blade into the J5 gap, spacers, axle down the axis
19. J5 cover, servo screws, axle grub
20. BENCH J3 servo + shaft
21. JOIN forearm into the J3 gap, servo+shaft down the axis
22. J3 cover, servo screws, link set screws
23. spring collars
24. spring pins + springs

BENCH = done on the table as a sub-assembly; JOIN = the sub-assemblies go together.
Two of the four base->foot M4 bolts sit under the J2 servo pod at J1 = 0: to service
them later turn J1 to +45 (bolt 2) or -45 deg (bolt 3) -- measured, TOOL_ACCESS.log.

## Degrees of freedom

Six: J1 base yaw, J2 shoulder, J3 elbow, J4 forearm roll, J5 wrist pitch, J6 tool roll
(spherical wrist). Checked in `REV_H/DOF6_CHECK.log`: each axis measured from the servo
horn AND from its bearing pockets (they coincide), Jacobian rank 6 over the working range.
Swept ranges without a clash: J1 +-90, J2 +-54, J3 +-72, J4 +-90, J5 +-46.5, J6 +-90 deg.
Straight up (the modelled home) is singular, as for any arm of this layout; park and
start from a bent 'ready' pose (e.g. J2 30, J3 -60, J5 30).

## Verification behind this folder

* drive trains J1..J6, bearings as solids, shaft clamps, every fastener, springs,
  whole-arm motion, print gates: FAILURES per stage = 0, 0, 0, 0, 0, 0, 0
* static all-pairs interference: CLASHES (penetration >= 0.15 mm) -- must each be explained:
* manual check by slicing each joint: TOTAL CLASHES IN THE SECTIONS: 0
* parameter -> CAD audit: 265 parameters measured back out of these files, 0 fail
* manufacturer's ST3215 STEP in all six seats: OFFICIAL-SERVO CHECK: 0 problem
* assembly / disassembly paths (both servo models): DISASSEMBLY PATHS: 0 blocked, DISASSEMBLY PATHS: 0 blocked
* joints together, tipping, thin walls, bed: JOINTS TOGETHER: 0 pair(s) too close, TIPPING: 0 problem(s), THIN WALLS: 0 part(s) with a thin wall, BED: 0 part(s) too big for a 180 mm cube
* see `REV_H/REVI_CHECKS.log`, `REV_H/PARAM_AUDIT.md`, `REV_H/ARM450_REV_I_FINAL.pdf`
