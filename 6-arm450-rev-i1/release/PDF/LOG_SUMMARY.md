# ARM-450 rev I.1 -- log summary, release pass 2026-09-27 (J3_p1 lug fix)

**ALL 25 CHECKS AT 0 FAILURES -- print verdict GREEN (fit test first; the 6 servo housings after coupon 07 fits your servo).**

| # | check | what it proves | result | key numbers |
|---|---|---|---|---|
| 1 | Drive trains | J1 .. J6: servo seat, horn on the axis, coupler, bearings, shaft, every part of the joint against every other, servo insertion path | 0 failures | 23 + 21 + 23 + 16 + 46 individual checks passed (J1, J2, J3, J4, J5/J6) |
| 2 | Bearings and bolts as solids | every bearing seated on its pockets, every bolt through real holes | 0 failures | 54 checks passed |
| 3 | Link lock | J2 / J3 links on their shafts: M5 set screws on the double-D flats, centring rings | 0 failures | 2 x M5 x 10 per link half, all tightened on a flat |
| 4 | Every fastener | each screw passes free, bites >= its minimum, head seated, tip free; inserts in pockets | 0 failures | 114 screws, 61 inserts, 4 nuts against 49 parts |
| 5 | Parameters in the files | every key dimension measured back out of the exported print files | 0 failures | 265 measured, 0 off |
| 6 | Tool access | a hex key / screwdriver reaches every screw at the build step where it is fitted | 0 failures | 114 screws: 78 always clear, 36 clear at their step |
| 7 | Rule 4: mate, never overlap | all pairs of the whole assembly, exact Boolean volume; only designed pathways (bearing race, horn, screw); every body attached; 3 injected faults must be caught | 0 failures | 232 components; 3 of 3 faults detected |
| 8 | Gravity springs | spring points, lengths and forces; J2 / J3 torque with the springs | 0 failures | worst case arm level: J2 SF 1.07, J3 SF 1.26 (ST3215 0.88 N.m continuous); no payload |
| 9 | Whole-arm sweep | each joint through its range, every part against every other; injected block caught | 0 failures | joints with a clash: 0; control DETECTED |
| 10 | 6 degrees of freedom | each axis measured twice (servo horn = bearing pockets), Jacobian rank | 0 failures | rank 6 in the working range; spherical wrist (axes meet within 0.000 mm) |
| 11 | Manufacturer's servo | Waveshare's own ST3215 model (rear idler horn) in all 6 seats; servo screws in its holes; driven chains shifted 0.20 mm (its horn) | 0 failures | servo screw cores in the real holes 20 / 20; worst joint clearance 0.502 mm |
| 12 | Take it apart | each servo unit slid out along its path, exact Booleans, our servo AND the manufacturer's | 0 failures | 7 of 7 paths free, both servo models |
| 13 | Joints moving together | 450 combined poses of J1 .. J5: every pair of bodies | 0 failures | every pair: neighbours >= 0.47 mm (running gaps), all others >= 15.0 mm |
| 14 | Tipping | centre of mass over the poses vs the foot | 0 failures | COM up to 118.0 mm out vs 64 mm foot: foot MUST be fixed (4 table holes) |
| 15 | Thin walls / bed | inward rays on every printed part (< 0.8 mm); bed size | 0 failures | thin walls: 0 part(s); all parts fit a 180 mm cube |
| 16 | Print orientation gates | each part sliced in its chosen print orientation: islands, sub-layer features | 0 failures | 0 islands; the 2 'MARGINAL z 16.1' notes are the seam lip's top face (2.0 mm wide below) |
| 17 | Static all-pairs | second, independent method: sampled points + penetration depth | 0 failures | 39 parts, 17 touching pairs, 0 clashes |
| 18 | Wiring | both bus plugs into every servo (sockets from the maker's model + your photo), way out for wires | 0 failures | nearest wall 1.98 mm; every lead has a way out |
| 19 | Screw heads vs turning parts | every screw beside a joint, joint turned -180 .. +180 deg: clearance in range, first contact angle | 0 failures | J3 fork heads 4.32 mm (contact at 94 deg), J5 6.85 mm, caps 1.30 mm |
| 20 | Union joints | every glued feature of every printed part joined over >= 0.80 of its own section (rev I.1, after the J3 lugs were found on a 0.1 mm sliver) | 0 failures | 0 weak joint(s); the J3 lugs now 136 mm2 (were 34) |
| 21 | Plug slots | each bus plug pulled out of its socket with the arm ASSEMBLED: straight through a slot, or straight then sideways out | 0 failures | 0 of 12 plugs cannot; routes in PLUG_INSERT.log |
| 22 | Cable route | one joint per cable; path change over the range; loop to leave | 0 failures | largest path change 42 mm; loops 31 .. 61 mm |
| 23 | Sections (manual check) | every joint sliced through its axis, each interface measured | 0 failures | 0 clashes in the sections |
| 24 | Print slicer | the print-ready STLs themselves sliced | 0 failures | 0 islands, 0 unprintable layers |
| 25 | Assembly | the full arm exported as STEP | 0 failures | 232 components (parts, servos, bearings, every screw, insert, spring) |

## Important PDFs

| file | pages | what it is for |
|---|---|---|
| `ARM450_AUDIT_REPORT.pdf` | 38 | READ FIRST: the verdict, what was found and fixed, your 4 snapshot questions answered with pictures, what is still to do |
| `ARM450_REV_I_FINAL.pdf` | 48 | every joint as exact sections (overlap in red, contact green, gaps measured), the whole arm, and every check log in full |
| `ARM450_POSES.pdf` | 6 | the full assembly in 6 poses, clearance measured in each |
| `ARM450_PARTS.pdf` | 54 | every printed part alone: 4 views + sections of its features |
| `../ASSEMBLY_MANUAL/ARM450_ASSEMBLY_MANUAL.pdf` | 32 | the build, one page per step (added parts in red), every screw's size and place, cable loops, service notes |
| `ARM450_REV_I.pdf` | 8 | the six joints, one page each: fixed side, driven side, servo, how it is held |
| `RULE5_VIEWS/ARM450_INTERFACES.pdf` | 19 | the Rule 5 interface sections on their own (also inside the FINAL pdf) |
| `LOG_SUMMARY.pdf` | 2 | this summary |
| `REV_H_VERIFICATION.pdf` | 1 | SUPERSEDED rev H report: now a pointer page (original in archive_superseded/) |

Full logs: `REVI_CHECKS.log` (every check stage), `FINAL_RUN.log` (assembly, sections, print folder, slicer), and per check: FASTENER_CHECK, TOOL_ACCESS, MATING_CHECK, OFFICIAL_SERVO_CHECK, DISASSEMBLY_CHECK(_OFFICIAL), AUDIT_GAPS, WIRING_CHECK, HEAD_CLEARANCE, CABLE_ROUTE, DOF6_CHECK, CLAMP_CHECK (.log), PARAM_AUDIT.md, SECTION_MEASURE.md.
