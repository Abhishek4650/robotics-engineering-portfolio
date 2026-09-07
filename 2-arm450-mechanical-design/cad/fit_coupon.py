"""
ARM-450 fit-test coupon — print this BEFORE committing to the full set.

A single pocket only tells you pass/fail. This brackets the fit: pockets
stepped 0.05 mm apart around each nominal diameter, so one print tells you which
diameter actually presses correctly on this machine with this filament.

THE ARM USES TWO BEARING SIZES, so the coupon carries two rows:
  * top row    Ø42.00 — 6806-2RS (30 x 42 x 7), J1 turret, J2 shoulder, J3 elbow
  * bottom row Ø37.00 — 6706-2RS (30 x 37 x 4), J4 roll, J5 pitch, J6 tool roll

The wrist row was missing until 2026-09-01. The wrist changed to the smaller
bearing on 2026-08-21 and the coupon was never followed through, so half the
bearings in the arm had no fit test at all -- and a 6706 offered up to a Ø42
pocket simply drops through, which reads as "the bearing is wrong" when in fact
the coupon had no station for it.

Also carries the other two fits that decide the build:
  * M3 heat-set insert bosses at three hole diameters
  * a tongue-and-groove seam sample, to check the lip engages
    before four link halves are committed to it

Prints in ~1.2 h, flat, no supports.
"""
import os, sys
import cadquery as cq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from params import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cad")

PLATE_T = 9.0                      # thicker than the 7 mm bearing so it seats
# Three steps, not five: the printer measures 0.02 mm XY shrink, so the fit is
# already close to nominal and +/-0.05 brackets it. Five made a 162 g, 4-hour
# coupon -- the point of a test print is that it is quick.
POCKET_STEPS = [-0.05, 0.00, +0.05]   # about Ø42.00  (6806, J1-J3)
WRIST_STEPS  = [-0.05, 0.00, +0.05]   # about Ø37.00  (6706, J4-J6)
INSERT_STEPS = [3.9, 4.1, 4.3]     # hole Ø for a Ø4.6 insert
PITCH = 50.0
RING_OD = 50.0          # just enough material round each pocket
RING_OD_W = 45.0        # the wrist pocket is 5 mm smaller, so its ring is too
SPINE_W = 16.0


# --- identification -------------------------------------------------------
# Printed, the three pockets are geometrically identical to the eye. You press
# a bearing in, it fits, and you have no way of knowing WHICH pocket it was --
# which makes the whole coupon useless, because its only output is "this
# diameter is the right one".
#
# Marks are RAISED, not engraved: in dark carbon-filled PLA an engraved
# character is nearly invisible, while a raised one catches light and throws a
# shadow. Strokes must clear two extrusion widths (1.24 mm at a 0.6 mm nozzle)
# or the slicer drops them, which is why the text is bold at 8 mm rather than
# neat at 4 mm.
#
# Every label is doubled: numerals AND a dot count. Numerals are ambiguous
# upside down -- "05" reads "50" and "95" reads "56" -- and this is a part
# whose entire job is to be unambiguous. Dots cannot be misread, the count
# always ascends left to right, and an arrow on the label strip fixes the
# direction.
MARK_H = 0.9            # how far a mark stands proud
TEXT_PT = 8.0           # bold at this size gives ~1.3 mm strokes
DOT_D = 2.2            # fits the 4 mm annulus round a Ø42 pocket
LABEL_STRIP = 16.0      # a band above the rings, purely to carry the numerals

# --- row geometry, module level so the drawing uses the SAME numbers -------
# draw_iso.py placed its pocket callouts at y = 0 because that happened to be
# the main row's centre when the coupon had one row. Adding the wrist row moved
# the part centroid and silently pointed every leader at empty plate.
_H0 = RING_OD + 34.0
Y_MAIN  = _H0 / 2 - RING_OD / 2 - 2.0                       # 6806 row centre
Y_INS   = Y_MAIN - RING_OD / 2 - SPINE_W / 2 + 1.0          # spine centre
Y_WRIST = Y_INS - SPINE_W / 2 - RING_OD_W / 2 + 1.0         # 6706 row centre
Y_STRIP   = Y_MAIN + RING_OD / 2 + LABEL_STRIP / 2 - 1.0    # top label strip
Y_STRIP_W = Y_WRIST - RING_OD_W / 2 - LABEL_STRIP / 2 + 1.0  # bottom strip
Y_CENTRE  = ((Y_STRIP + LABEL_STRIP / 2) + (Y_STRIP_W - LABEL_STRIP / 2)) / 2



def _dots(c, x, y, n, z):
    """n raised dots in a row, centred on x."""
    for k in range(n):
        dx = (k - (n - 1) / 2.0) * (DOT_D + 1.6)
        c = c.union(cq.Workplane("XY").workplane(offset=z)
                    .center(x + dx, y).circle(DOT_D / 2).extrude(MARK_H))
    return c


def _label(c, x, y, txt, z, pt=TEXT_PT):
    """Raised text. Falls back silently to nothing rather than killing the
    build -- the dot counts carry the same information."""
    try:
        return c.union(cq.Workplane("XY").workplane(offset=z)
                       .center(x, y)
                       .text(txt, pt, MARK_H, combine=True, kind="bold"))
    except Exception:                                    # noqa: BLE001
        return c


def coupon():
    """Rings on a spine rather than a solid plate: same fits, a third of the mass."""
    n = len(POCKET_STEPS)
    W = PITCH * n
    H = _H0
    y_brg = Y_MAIN
    # spine
    c = (cq.Workplane("XY").center(0, y_brg - RING_OD / 2 - SPINE_W / 2 + 1)
         .box(W, SPINE_W, PLATE_T, centered=(True, True, False)))
    # a ring at each pocket
    for i, d in enumerate(POCKET_STEPS):
        x = -W / 2 + PITCH * (i + 0.5)
        c = c.union(cq.Workplane("XY").center(x, y_brg)
                    .circle(RING_OD / 2).extrude(PLATE_T))
    # no fillet here: filleting the unioned spine/ring blend crashed OCCT.

    for i, d in enumerate(POCKET_STEPS):
        x = -W / 2 + PITCH * (i + 0.5)
        dia = BRG_OD + d
        # bearing pocket, blind, exactly as in the real parts
        c = c.cut(cq.Workplane("XY").workplane(offset=PLATE_T - BRG_W)
                  .center(x, y_brg).circle(dia / 2).extrude(BRG_W + 1))
        # Ø38 seat shoulder through, same as the joints
        c = c.cut(cq.Workplane("XY").center(x, y_brg)
                  .circle((BRG_OD - 2 * BRG_SHOULDER) / 2).extrude(PLATE_T + 2)
                  .translate((0, 0, -1)))
        # Lead-in chamfer at the mouth, cut as a CONE.
        # This was a .chamfer() inside a try/except and it threw every time --
        # a STEP audit for conical faces found ZERO on this part. The coupon
        # measures the fit; if the real parts have a chamfer and the coupon does
        # not, the coupon is measuring a different hole from the one it gates.
        c = c.cut(cq.Workplane("XY").center(x, y_brg)
                  .circle(dia / 2 + BRG_CHAMFER)
                  .workplane(offset=-BRG_CHAMFER)
                  .circle(dia / 2).loft(combine=False)
                  .translate((0, 0, PLATE_T)))

    # --- insert bosses, on the spine -----------------------------------
    y_ins = Y_INS
    for i, hd in enumerate(INSERT_STEPS):
        x = -W / 2 + 16.0 + 26.0 * i
        c = c.union(cq.Workplane("XY").center(x, y_ins)
                    .circle(BOSS_OD / 2).extrude(PLATE_T + 3.0))
        c = c.cut(cq.Workplane("XY").workplane(offset=PLATE_T + 3.0 - M3_INSERT_L)
                  .center(x, y_ins).circle(hd / 2).extrude(M3_INSERT_L + 1))

    # --- seam sample: tongue on one side, groove on the other ----------
    xs = W / 2 - 18.0
    c = c.union(cq.Workplane("XY").workplane(offset=PLATE_T)
                .center(xs, y_ins + 4.0).rect(20.0, 2.0).extrude(SEAM_LIP))
    c = c.cut(cq.Workplane("XY")
              .workplane(offset=PLATE_T - (SEAM_LIP + SEAM_GROOVE_EXTRA))
              .center(xs, y_ins - 4.0)
              .rect(24.0 + 2 * SEAM_LIP_CLR, 2.0 + 2 * SEAM_LIP_CLR)
              .extrude(SEAM_LIP + SEAM_GROOVE_EXTRA + 1))
    # --- label strip along the top, carrying the numerals ---------------
    y_strip = Y_STRIP
    c = c.union(cq.Workplane("XY").center(0, y_strip)
                .box(W, LABEL_STRIP, PLATE_T, centered=(True, True, False)))

    for i, d in enumerate(POCKET_STEPS):
        x = -W / 2 + PITCH * (i + 0.5)
        # the real diameter, above its own pocket
        c = _label(c, x, y_strip, f"{BRG_OD + d:.2f}", PLATE_T)
        # and a dot count on the ring itself, which cannot be read upside down
        # centred in the 4 mm annulus between the pocket edge and the ring
        # edge: at +4.5 the dots landed ON the pocket lip and would have been
        # cut away by it
        c = _dots(c, x, y_brg - RING_OD / 2 + 2.0, i + 1, PLATE_T)

    # direction arrow: the convention everywhere on this part is that the
    # count ASCENDS left to right
    ax = -W / 2 + 6.0
    c = c.union(cq.Workplane("XY").workplane(offset=PLATE_T)
                .center(ax, y_strip)
                .polyline([(-3.5, -3.0), (3.5, 0.0), (-3.5, 3.0)]).close()
                .extrude(MARK_H))

    # --- insert bosses: same dot convention ------------------------------
    for i, hd in enumerate(INSERT_STEPS):
        x = -W / 2 + 16.0 + 26.0 * i
        # -2.6 put the dots 0.65 mm over the spine's bottom edge
        c = _dots(c, x, y_ins - BOSS_OD / 2 - 1.7, i + 1, PLATE_T)

    # --- orientation: clip the top-left corner ---------------------------
    # so the strip can only be read one way up, belt and braces with the arrow
    c = c.cut(cq.Workplane("XY").workplane(offset=-1)
              .center(-W / 2, y_strip + LABEL_STRIP / 2)
              .polyline([(0, 0), (9, 0), (0, -9)]).close()
              .extrude(PLATE_T + MARK_H + 2))

    # =====================================================================
    # WRIST ROW — Ø37 pockets for the 6706, below the spine
    # =====================================================================
    # Same construction as the main row, at the wrist bearing's diameter and
    # its 4 mm width. Overlaps the spine by 1 mm so the union is one solid.
    y_wrist = Y_WRIST
    for i, d in enumerate(WRIST_STEPS):
        x = -W / 2 + PITCH * (i + 0.5)
        c = c.union(cq.Workplane("XY").center(x, y_wrist)
                    .circle(RING_OD_W / 2).extrude(PLATE_T))

    for i, d in enumerate(WRIST_STEPS):
        x = -W / 2 + PITCH * (i + 0.5)
        dia = WRIST_BRG_OD + d
        # blind pocket, WRIST_BRG_W deep — the real wrist pocket is 4 mm, not 7
        c = c.cut(cq.Workplane("XY").workplane(offset=PLATE_T - WRIST_BRG_W)
                  .center(x, y_wrist).circle(dia / 2).extrude(WRIST_BRG_W + 1))
        # seat shoulder through
        c = c.cut(cq.Workplane("XY").center(x, y_wrist)
                  .circle((WRIST_BRG_OD - 2 * WRIST_BRG_SHOULDER) / 2)
                  .extrude(PLATE_T + 2).translate((0, 0, -1)))
        # lead-in chamfer, cut as a cone exactly as the main row
        c = c.cut(cq.Workplane("XY").center(x, y_wrist)
                  .circle(dia / 2 + BRG_CHAMFER)
                  .workplane(offset=-BRG_CHAMFER)
                  .circle(dia / 2).loft(combine=False)
                  .translate((0, 0, PLATE_T)))

    # --- bottom label strip ---------------------------------------------
    y_strip_w = Y_STRIP_W
    c = c.union(cq.Workplane("XY").center(0, y_strip_w)
                .box(W, LABEL_STRIP, PLATE_T, centered=(True, True, False)))
    for i, d in enumerate(WRIST_STEPS):
        x = -W / 2 + PITCH * (i + 0.5)
        c = _label(c, x, y_strip_w, f"{WRIST_BRG_OD + d:.2f}", PLATE_T)
        c = _dots(c, x, y_wrist - RING_OD_W / 2 + 2.0, i + 1, PLATE_T)

    # --- row tags --------------------------------------------------------
    # Two rows of near-identical pockets on one part is exactly the situation
    # the dot counts cannot resolve on their own: "two dots" now means two
    # different diameters depending on which row it is in. The part number
    # settles it, and it is the number written on the bearing itself.
    c = _label(c, W / 2 - 22.0, y_strip, "6806", PLATE_T, pt=7.0)
    c = _label(c, W / 2 - 22.0, y_strip_w, "6706", PLATE_T, pt=7.0)

    H = H + LABEL_STRIP
    return c, W, H


if __name__ == "__main__":
    c, W, H = coupon()
    bb = c.val().BoundingBox()
    cq.exporters.export(c, os.path.join(OUT, "fit_coupon.step"))
    cq.exporters.export(c, os.path.join(OUT, "fit_coupon.stl"),
                        tolerance=0.01, angularTolerance=0.1)
    v = c.val().Volume()
    print("FIT-TEST COUPON")
    print(f"  envelope   {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
    print(f"  volume     {v/1000:.1f} cm3   ~{v*1.29e-3*0.55:.0f} g")
    print(f"\n  TOP row — 6806-2RS (30x42x7), J1/J2/J3, pocket {BRG_W} mm deep:")
    for i, d in enumerate(POCKET_STEPS):
        print(f"     {'•'*(i+1):4s} Ø{BRG_OD+d:.2f}   ({d:+.2f} from nominal)"
              f"{'   <- DESIGN' if abs(d) < 1e-9 else ''}")
    print(f"  BOTTOM row — 6706-2RS (30x37x4), J4/J5/J6, pocket "
          f"{WRIST_BRG_W} mm deep:")
    for i, d in enumerate(WRIST_STEPS):
        print(f"     {'•'*(i+1):4s} Ø{WRIST_BRG_OD+d:.2f}   ({d:+.2f} from nominal)"
              f"{'   <- DESIGN' if abs(d) < 1e-9 else ''}")
    print(f"  insert holes, left to right:")
    for i, h in enumerate(INSERT_STEPS):
        print(f"     {'•'*(i+1):4s} Ø{h}")
    print(f"\n  ID marks: raised {MARK_H} mm — numerals on the top strip, dot")
    print(f"  counts beside every feature, arrow and clipped corner for")
    print(f"  orientation. Counts always ASCEND left to right.")
    print(f"  seam sample: {SEAM_LIP} mm tongue + matching groove "
          f"({SEAM_LIP_CLR} mm/side)")
    print(f"\n  wrote fit_coupon.step / .stl")
