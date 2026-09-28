# ARM-450 rev I — Fusion 360 design trees, one script per part

Every printed part of the arm (27) and the 7 fit-test coupons, each as a **Fusion 360 script
that builds the part as an editable parametric design** — a timeline of sketches, extrudes,
lofts, combines (join / cut / intersect), fillets and chamfers — and **saves it as `.f3d`**.

| folder | what is in it |
|---|---|
| `00_BUILD_ALL_f3d/` | **one script that builds every part and saves each `.f3d`** (run this once) |
| `parts/NN_part_xQ/` | one folder per part: `NN_part_xQ.py` (the script), `.manifest`, `.json` (its feature list), `_released.step` (the released solid, to compare) |
| `fit_test/fit_0N_…/` | the same for the 7 fit-test coupons |
| `tools/` | how these were made (recorder, unfolder, script writer, the offline check) |
| `VERIFY_MOCK_FUSION.log` | the offline check of every script against the released STEP |

## Why a script and not the `.f3d` file itself

`.f3d` is Autodesk's own archive format: only Fusion 360 can write it. This machine has no
Fusion, so the `.f3d` files are made **by Fusion on your computer** — run the script once and
the `.f3d` appears in the part's folder, next to the script.

## Run

1. Fusion 360 → **UTILITIES → ADD-INS → Scripts and Add-Ins** (Shift+S) → **Scripts** tab.
2. Click the green **+** next to *My Scripts* → pick the folder `00_BUILD_ALL_f3d`
   (or one part's folder) → select it → **Run**.
3. Each part opens as a new design, is built feature by feature, checked against the released
   part (volume + bounding box; the report says `MATCHES THE RELEASED PART` or `CHECK`), saved as
   `parts/NN_part_xQ/NN_part_xQ.f3d` with a `_BUILD_REPORT.txt`, and closed (BUILD ALL) or left
   open (single part). `00_BUILD_ALL_f3d/BUILD_ALL_REPORT.txt` lists every part.

## Edit

Open a part's `.f3d` (File → Open → *Open from my computer*). The timeline at the bottom is the
design tree:

* **Sketch → Extrude / Loft** — double-click the sketch to change its lines and circles,
  double-click the extrude to change its distance.
* **Combine** — join / cut / intersect exactly as the generator did it; edit or suppress one to
  add back or remove material.
* **Fillet / Chamfer** — edit the radius / distance.
* **Move** — follows the extrude of a body that is not square to the XY plane (it is sketched on
  XY and moved into place).
* Every item is named `NNNN <what> <generator function> L<line>` — the line of the ARM-450 generator
  (`REV_H/*.py`, `arm450_design/…`) that made it; the timeline is grouped by generator function.

The parts are built in the arm's **design frame** (the released STEP frame, mm), not in print
orientation — the print orientation of each part is in `../PRINTABLE_FILES` / the print list.

## Results (rev I.1, 2026-09-27)

* **34 parts, 1616 features** (rev I.1: `12_J3_p1` now carries the sunk spring lugs with R3 webs).
  Every recorded solid equals its released STEP (largest difference 0.006 mm³, `10_link_upper_tongue` —
  see the note below).
* **Offline rebuild: 34 / 34 match** the released STEP (largest difference 0.006 mm³), in both
  readings of Fusion's rules: `VERIFY_MOCK_FUSION.log` (Fusion accepts a cut tool that misses the
  body and a join of bodies that do not touch) and `VERIFY_MOCK_FUSION_STRICT.log` (it refuses
  them — the scripts then cut tool by tool and join pair by pair).
* `00_BUILD_ALL_f3d` was run the same way offline: 34 parts, 0 to check.

| part | print | features | of which | recorded vs released (mm³) | mock-Fusion timeline items | mock rebuild vs released (mm³) |
|---|---|---|---|---|---|---|
| `01_base_x1` | 1 | 33 | 14 combine, 13 extrude, 1 fillet, 5 loft | 0.0000 | 65 | 0.0000 OK |
| `02_spigot_collar_x1` | 1 | 17 | 8 combine, 9 extrude | 0.0000 | 30 | 0.0000 OK |
| `03_j1_mount_x1` | 1 | 106 | 45 combine, 61 extrude | 0.0000 | 200 | 0.0000 OK |
| `04_j1_hub_x1` | 1 | 26 | 12 combine, 1 chamfer, 13 extrude | 0.0000 | 39 | 0.0000 OK |
| `05_J2_turret_p1_x1` | 1 | 93 | 46 combine, 43 extrude, 4 loft | 0.0000 | 171 | 0.0000 OK |
| `06_J2_turret_p2_x1` | 1 | 114 | 49 combine, 63 extrude, 2 loft | 0.0000 | 267 | 0.0000 OK |
| `07_J2_shaft_x1` | 1 | 18 | 8 combine, 1 chamfer, 9 extrude | 0.0000 | 36 | 0.0000 OK |
| `08_shaft_clamp_x4` | 4 | 9 | 4 combine, 5 extrude | 0.0000 | 16 | 0.0000 OK |
| `09_link_upper_groove_x1` | 1 | 65 | 31 combine, 32 extrude, 2 fillet | 0.0000 | 105 | 0.0000 OK |
| `10_link_upper_tongue_x1` | 1 | 81 | 39 combine, 40 extrude, 2 fillet | 0.0061 | 130 | 0.0062 OK |
| `11_collar_upper_x2` | 2 | 13 | 6 combine, 7 extrude | 0.0000 | 23 | 0.0000 OK |
| `12_J3_p1_x1` | 1 | 135 | 65 combine, 67 extrude, 1 fillet, 2 loft | 0.0000 | 227 | 0.0000 OK |
| `13_J3_p2_x1` | 1 | 146 | 63 combine, 81 extrude, 1 fillet, 1 loft | 0.0004 | 271 | 0.0004 OK |
| `14_J3_shaft_x1` | 1 | 18 | 8 combine, 1 chamfer, 9 extrude | 0.0000 | 27 | 0.0000 OK |
| `15_link_fore_tongue_x1` | 1 | 81 | 39 combine, 40 extrude, 2 fillet | 0.0000 | 129 | 0.0000 OK |
| `16_link_fore_groove_x1` | 1 | 85 | 41 combine, 42 extrude, 2 fillet | 0.0000 | 135 | 0.0000 OK |
| `17_collar_fore_x2` | 2 | 13 | 6 combine, 7 extrude | 0.0000 | 23 | 0.0000 OK |
| `18_j4_base_x1` | 1 | 61 | 29 combine, 32 extrude | 0.0000 | 96 | 0.0000 OK |
| `19_j4_cap_x1` | 1 | 23 | 11 combine, 12 extrude | 0.0000 | 35 | 0.0000 OK |
| `20_j4_hub_x1` | 1 | 31 | 15 combine, 16 extrude | 0.0000 | 47 | 0.0000 OK |
| `21_J5_p1_x1` | 1 | 97 | 46 combine, 48 extrude, 1 fillet, 2 loft | 0.0000 | 162 | 0.0000 OK |
| `22_J5_p2_x1` | 1 | 140 | 60 combine, 78 extrude, 1 fillet, 1 loft | 0.0004 | 260 | 0.0004 OK |
| `23_J5_shaft_x1` | 1 | 16 | 7 combine, 1 chamfer, 8 extrude | 0.0000 | 24 | 0.0000 OK |
| `24_J5_spacer_x2` | 2 | 1 | 1 extrude | 0.0000 | 2 | 0.0000 OK |
| `25_j6_body_x1` | 1 | 62 | 30 combine, 32 extrude | 0.0000 | 122 | 0.0000 OK |
| `26_j6_cap_x1` | 1 | 23 | 11 combine, 12 extrude | 0.0000 | 47 | 0.0000 OK |
| `27_j6_flange_x1` | 1 | 31 | 15 combine, 16 extrude | 0.0000 | 63 | 0.0000 OK |
| `fit_01_servo_pinch` | 1 | 3 | 1 combine, 2 extrude | 0.0000 | 5 | 0.0000 OK |
| `fit_02_6806_seat` | 1 | 5 | 2 combine, 3 extrude | 0.0000 | 8 | 0.0000 OK |
| `fit_03_6706_seat` | 1 | 5 | 2 combine, 3 extrude | 0.0000 | 8 | 0.0000 OK |
| `fit_04_shaft_stub` | 1 | 5 | 2 combine, 3 extrude | 0.0000 | 8 | 0.0000 OK |
| `fit_05_centring_ring` | 1 | 1 | 1 extrude | 0.0000 | 2 | 0.0000 OK |
| `fit_06_holes` | 1 | 11 | 5 combine, 6 extrude | 0.0000 | 17 | 0.0000 OK |
| `fit_07_servo_screws` | 1 | 48 | 16 combine, 32 extrude | 0.0000 | 113 | 0.0000 OK |

Note — `10_link_upper_tongue`: the released rev-I tongue was made by reading the released upper
link STEP back and measuring its hole centres. Here the upper link is rebuilt by its generator
(`arm450_design/verify_pro/parts/link_pro.py`, `build(tongue=True, end="socket")`, proven equal to
the released STEP: 0.0000 mm³ both ways), so the measured centres differ in the 5th decimal:
0.006 mm³ in all — far below one printed layer.

## How they were made and checked

1. **Recorded** — the release generators were re-run in a scratch copy (nothing in the release
   was written) with every CadQuery modelling call recorded: each extrude with its exact sketch
   (lines, arcs, circles), each loft, boolean, fillet, chamfer and move.
2. **Recorded = released** — each part's recorded solid was compared with the released STEP by
   boolean difference both ways.
3. **Unfolded** into a Fusion timeline — moves and mirrors carried down onto the sketches; cut
   tools that miss the part dropped (they change nothing).
4. **Rebuilt offline** — every emitted script was run against a stand-in for Fusion's API
   (`tools/mock_adsk`, OpenCascade under the same calls) and its result compared with the released
   STEP (`VERIFY_MOCK_FUSION.log`).

What step 4 cannot prove is how Fusion's own kernel evaluates each feature — that is why every
script re-checks its result inside Fusion and says `MATCHES` or `CHECK`. If a part says `CHECK`,
send its `_BUILD_REPORT.txt`.

Rebuild all of this: `python3 tools/make_trees.py && python3 tools/emit_scripts.py && python3 tools/verify_mock.py`.
