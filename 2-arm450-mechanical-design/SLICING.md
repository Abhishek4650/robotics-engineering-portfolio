# ARM-450 — Slicing Specification

**Read the two constraints in §1 before anything else.** They are not preferences; the
parts do not assemble if you get them wrong.

Generated from `cad/params.py`, which now asserts both of them at import.

**Material: plain PLA** (`params.MATERIAL = "PLA"`). E = 3500 MPa, 1.24 g/cm³, yield
55 MPa. Every load case was re-run against it — **10 of 10 pass**, with the worst-case
deflection 0.197 mm against a 0.30 mm limit. Backlash still dominates at 2.25 mm, so the
material change is invisible at the tool.

---

> **If a print is running now, check the perimeter count before anything else.**
> This project's parameter file said `NOZZLE = 0.6` with 4 perimeters until
> 2026-09-02, while the machine in use has a **0.4 mm nozzle**. Four perimeters
> at a 0.48 mm line width is 1.92 mm against a **2.4 mm structural wall** — every
> wall in the arm prints with a 0.48 mm void up its middle, filled with sparse
> infill, and looks perfect from the outside. **Five** perimeters at 0.48 mm
> consume the wall exactly. The nozzle is now the single input and the line
> width and perimeter count are derived from it.


## 1. The two settings that are not yours to choose

### Layer height = 0.20 mm

The link seam is a tongue and groove. **The tongue is 1.60 mm and must be an integer
number of layers**, because a slicer rounds a partial layer *up*:

```
1.60 / 0.20 = 8         exactly            USE THIS
1.60 / 0.16 = 10        exactly            also valid
1.60 / 0.32 = 5         exactly            also valid, coarse
1.60 / 0.25 = 6.4       rounds to 7 -> 1.75 mm tongue
1.60 / 0.28 = 5.71      rounds to 6 -> 1.68 mm tongue
```

An over-tall tongue **bottoms out in the groove before the two rims can touch**, so the
seam sits open and the closed box section — the whole reason the links are a clamshell —
never closes. This already happened once at a 1.50 mm tongue, which is why it is 1.60 now.

### Nozzle = 0.6 mm, hardened steel, 4 perimeters

```
4 perimeters x 0.62 mm line = 2.48 mm  >=  the 2.40 mm design wall
```

The wall is **entirely consumed by perimeters**, which is what makes it print solid, and
that is the assumption behind the whole mass model (`MASS_FILL = 0.90`). Drop to 3
perimeters and you get 1.86 mm of wall with a void behind it — lighter than modelled, and
weaker in exactly the direction the links are loaded.

**2026-08-27 — the build material is now PLAIN PLA, not carbon-filled**, and that
removes the nozzle problem entirely. Carbon fill is abrasive and eats a brass nozzle
inside a spool; plain PLA does not. **A standard brass nozzle is fine**, in 0.4 or 0.6.
No hardened nozzle to buy, no clogging, and layer adhesion is actually *better* — carbon
fibres interrupt the bond between layers.

### If you only have a 0.4 mm nozzle

It works — **but not at the default line width**, and that is the whole catch. At 0.45 mm
you get five perimeters totalling 2.25 mm and a **0.15 mm gap** the slicer fills with
infill or simply leaves open, which breaks the solid-wall assumption the mass model and
the stiffness numbers both rest on.

Two settings consume the 2.40 mm wall exactly:

| nozzle | line width | perimeters | total | |
| --- | --- | --- | --- | --- |
| 0.6 | 0.60 | 4 | **2.40** | the shipped profile |
| **0.4** | **0.48** | **5** | **2.40** | **use this — fewer passes, so faster** |
| 0.4 | 0.40 | 6 | 2.40 | alternative: narrower lines follow the Ø42 bore better |

0.48 is 1.2× the nozzle, which is the normal upper limit and perfectly standard.

**Everything else stays the same.** Layer height is still 0.20 mm — it divides the 1.6 mm
tongue into 8, and that is independent of nozzle. (0.16 and 0.32 also divide it; 0.32 is
the practical ceiling for a 0.4 nozzle if you want the time back.)

**One thing gets better.** The minimum printable wall is two lines, so it falls from
1.24 mm to **0.90 mm** — the 2 mm gear teeth, the bayonet lugs and the raised coupon marks
all get easier, not harder.

**One thing gets worse: time.** Wall passes scale with 1/line-width, so the full set goes
from roughly **21 h to 29 h**.

> ### Two warnings, and the first is not optional
>
> **The nozzle must be HARDENED STEEL, in any diameter.** Carbon fill opens a brass nozzle
> measurably inside one spool. A nozzle that creeps from 0.40 to 0.45 mid-build changes
> every wall and every bearing pocket on the parts printed after it — and nothing warns
> you. You would find out at assembly, with half the parts fitting and half not.
>
> **Carbon fill clogs a 0.4 mm bore far more readily** than a 0.6. Many CF filaments
> specify 0.5 mm minimum for exactly this reason. It is survivable — dry filament, slower
> retraction, higher temperature — but it is the failure mode you will actually meet.
>
> A 0.6 mm hardened nozzle is the cheapest line item in this entire build, and it removes
> the clog risk, the wear risk and eight hours of print time at once. If you can buy one
> before starting, do.

---

## 2. Profile

| setting | value | why |
| --- | --- | --- |
| **Layer height** | **0.20 mm** | §1 — integer tongue |
| First layer | 0.25 mm | adhesion |
| **Nozzle** | 0.6 mm **or** 0.4 mm, **brass is fine** | plain PLA is not abrasive |
| **Wall line width** | **0.48 mm** (0.4 nozzle — the machine in use) · 0.60 mm on a 0.6 | must divide the wall exactly |
| **Perimeters** | **5** (0.4 nozzle) · 4 on a 0.6 | §1 — 5 × 0.48 = 2.40 consumes the wall EXACTLY |
| Top / bottom layers | 5 / 4 | 1.00 / 0.80 mm solid |
| Infill | 40 % gyroid | see §3 for the exceptions |
| Infill overlap | 15 % | bonds infill to the solid wall |
| Nozzle temp | **200–215 °C** | plain PLA; CF would want 225–235 |
| Bed | 60 °C | |
| Cooling | 100 % after layer 3 | |
| Outer wall speed | **25 mm/s** | dimensional accuracy on the Ø42 pockets |
| Inner wall / infill | 60 / 80 mm/s | |
| Wall order | **inner → outer** | the outer wall lands on solid support |
| Z-seam | **Aligned, rear** | never Random — see §4 |
| XY compensation | **0.00 mm to start** | the coupon sets this — expect to need it, §5 |
| Ironing | **OFF** | it smears the pocket mouth |
| Supports | **none** | every part is oriented to avoid them, §3 |
| Brim | 5 mm on tall/narrow parts | §3 |

**Dry the filament** if it has been open a while. Plain PLA is far less hygroscopic than
CF-filled, so this matters less than it did — but a wet-printed furry wall is still an
undersized bearing pocket.

---

## 3. Per part — orientation, infill, brim

Orientation is **not optional**. Each one puts the loaded direction across layers rather
than along them, and keeps overhangs off surfaces that matter.

| part | qty | orientation | infill | brim |
| --- | --- | --- | --- | --- |
| `link_half_tongue` | 2 | split face DOWN, open side up | 40 % | no |
| `link_half_groove` | 2 | split face DOWN, open side up | 40 % | no |
| `wrist_j4_housing` | 1 | bearing bore axis VERTICAL | 50 % | no |
| `wrist_j5_yoke` | 1 | bearing bore axis VERTICAL | 50 % | **yes** |
| `wrist_j6_output` | 1 | bearing bore axis VERTICAL | 50 % | no |
| `turret_j1` | 1 | bearing seat DOWN, axis vertical | 40 % | **yes** |
| `base` | 1 | foot DOWN, upright | 30 % | no |
| `shaft_clamp` | 2 | bore axis VERTICAL | 60 % | no |
| `servo_collar` | 2 | collar axis VERTICAL | 60 % | no |
| `horn_adapter` | 6 | horn face DOWN on the bed | **100 %** | no |
| `fit_coupon` | 1 | flat, pockets facing UP | 40 % | no |
| `tool_adapter` | 1 | spigot UP, flat face on the bed | 60 % | no |
| `tool_gripper` | 1 | socket face UP | 40 % | no |
| `gripper_jaw` | 2 | rack bar FLAT on the bed, teeth sideways | **100 %** | **yes** |
| `gripper_pinion` | 1 | flat, teeth in the XY plane | **100 %** | no |
| `tool_dock` | 1 | cone DOWN on the bed, socket up | 40 % | no |
| `dock_target` | 1 | flat face on the bed, spigot up | 40 % | no |
| `dock_target_sealed` | 1 | flat face on the bed, spigot up | 40 % | no |

**100 % infill where it is called for is not caution.** The pinion teeth are 2.0 mm and the
rack teeth 2.4 mm deep — at 40 % they are hollow shells that shear off the first time the
jaws grip. The horn adapter is 100 % because it is the part that carries servo stall torque
into the shaft; it is small, so it costs nothing.

**`dock_target` and `dock_target_sealed` are alternatives, not a pair.** The plain one is
the dry docking demonstration; the sealed one carries a Ø14.40 × 1.30 O-ring groove in the
spigot for fluid transfer. Print whichever the demonstration needs — they are otherwise
identical and both dock the same way.

> The O-ring groove is **0.45 mm deep and 1.30 mm wide**, cut into a Ø15.30 spigot. Print
> it **spigot up** so the groove is a horizontal feature — printed on its side it becomes a
> stack of stair-steps that the O-ring cannot seal against. Slow the outer wall for that
> part; it is the one printed surface in the design that has to be fluid-tight.

**Brim where listed**: `gripper_jaw` is 46 × 8 mm on its footprint — a tall thin fin.
`turret_j1` is 80 × 80 × 81 and `wrist_j5_yoke` is 42 mm tall on a small base.

**No supports anywhere.** The docking probe's capture cone prints **cone down**, which
makes it a 45° self-supporting overhang. Printing it the other way up needs support
*inside the cone*, and removing that support leaves exactly the surface finish the cone
exists to avoid.

---

## 4. Why the Z-seam setting matters here

Set it to **Aligned** and park it at the **rear**. On Random, the slicer drops a seam
wherever it likes, and on a part like `wrist_j5_yoke` that means somewhere on the Ø37
bearing pocket wall. A seam blob inside a bearing seat is a high spot on the one surface
whose diameter you are trying to control to ±0.05 mm.

---

## 5. Print the fit coupon first — 0.9 h, and it gates 19 h

The coupon carries three pockets at **Ø41.95 / Ø42.00 / Ø42.05**, three insert-boss hole
sizes and a seam sample. **Every feature is labelled on the part**: raised numerals on the
top strip, and 1 / 2 / 3 raised dots beside each feature that read the same way up or down.

Print it **with the profile above, unchanged**. That is the point — it measures your
machine running the settings you will use for the real parts, so changing anything
afterwards invalidates it.

> ### Plain PLA shrinks nearly 3× more, and it matters here
>
> | | shrink | on a Ø42 bore |
> | --- | --- | --- |
> | PLA+CF | 0.15 % | 0.06 mm |
> | **plain PLA** | **0.40 %** | **0.17 mm** |
>
> **The coupon brackets only 0.10 mm** (Ø41.95 → Ø42.05), and plain PLA's shrink is
> larger than that whole bracket. There is a real chance **all three pockets come out
> undersize** and none of them presses correctly.
>
> That is the coupon working, not failing. If all three are too tight, set XY compensation
> to about **−0.15 mm**, reprint the coupon, and read it again.
>
> **Budget two coupon prints, not one.** 0.9 h each, and it still gates 19 h of parts.

**Reading it:**

| result | means |
| --- | --- |
| firm thumb press, seats square | correct — use that diameter |
| drops in freely | pocket is oversize → set XY compensation **negative** by half the step |
| will not start | pocket is undersize → XY compensation **positive** |

Then set `BRG_FIT` in `cad/params.py` to the winning step, re-export, and print the
structural parts. If Ø42.00 wins, nothing changes and you print as-is.

**Do not skip to the real parts.** Roughly 19 of the 21 print hours are parts carrying a
Ø42 or Ø37 pocket. If the fit is wrong they are all scrap, and the coupon costs 0.9 h and
43 g to find out.

---

## 6. Filament budget

788 g of PLA+CF for the complete set at the infills above — **one 1 kg spool**, with about
210 g spare. That is not much margin for a failed print, so if you can, buy two.

---

## 7. Assembly notes that depend on the print

- **Install the heat-set inserts while the parts are fresh**, 200–220 °C, pressed slowly
  and square. The coupon's three boss holes tell you which diameter takes them without
  splitting the boss.
- The seam screws are **M3 × 20** (usable 18.0–22.0) and the tip ears **M2.5 × 18**
  (usable 16.9–19.5). Too short and they never reach the insert; too long and they bottom
  in the blind hole and jack the halves apart.
- Heads sit **proud on the outer face** — there is no counterbore, deliberately.
