#!/usr/bin/env python3
"""
FIT TEST -- print these first (about 1.5 h, ~40 g). Every dimension below is
taken from the design constants, so a coupon that fits means the real parts
fit on YOUR printer. If a fit is tight or loose, set your slicer's XY hole /
contour compensation (or tell me the numbers and the parts are regenerated).

  fit_01_servo_pinch   24.50 x 46.02 slot, 10 deep: the ST3215 must slide in
                       with a firm push and hold by friction (design -0.22 mm)
  fit_02_6806_seat     O42.00 x 7 pocket: a 6806 presses in by thumb/vice
  fit_03_6706_seat     O37.02 x 4 pocket: a 6706 presses in
  fit_04_shaft_stub    O29.95 x 15 shaft, one double-D flat pair (28.40 across):
                       slides through a 6806 / 6706 bore
  fit_05_centring_ring O38.35 / O30.0 x 5 slice of the link ring: slides on the
                       stub and into your printed link's O38.4 bore
  fit_06_holes         O4.1 (M3 insert) x2, O5.6 (M4 insert), O4.2 (M5 self-tap),
                       O3.4 (M3 clearance): set an insert, run an M5 in
  fit_07_servo_screws  a copy of a servo cover's back: 4 pads + O3.4 holes on
                       the servo's back-hole pattern (Waveshare drawing: 8.30 /
                       32.75 from the output shaft, 20.5 across). Lay it on
                       the BACK of your servo (the pads on the flat around the
                       4 holes, the wire slot under the window) and drive the
                       4 self-tapping screws from the servo box: they must line
                       up, bite, and pull the plate down flat without bottoming
                       out (2.6 mm go into the servo). If the holes do not line
                       up, STOP and tell me -- every servo mount uses them.
"""
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import drive_common as DC   # noqa: E402
import gen_clamp as GC      # noqa: E402
import gen_drive_j4 as G4   # noqa: E402


def box(x, y, z):
    return cq.Workplane("XY").rect(x, y).extrude(z)


def parts():
    p = {}
    s = box(DC.BAY_L + 8, DC.PINCH + 8, 12)
    p["fit_01_servo_pinch"] = s.cut(box(DC.BAY_L, DC.PINCH, 11).translate((0, 0, 2)))
    r = cq.Workplane("XY").circle(24.0).extrude(9)
    p["fit_02_6806_seat"] = r.cut(cq.Workplane("XY").circle(42.00 / 2).extrude(8).translate((0, 0, 2))) \
        .cut(cq.Workplane("XY").circle(DC.BORE_CLR_D / 2).extrude(12).translate((0, 0, -1)))
    r = cq.Workplane("XY").circle(21.5).extrude(6)
    p["fit_03_6706_seat"] = r.cut(cq.Workplane("XY").circle(G4.BRG_OD / 2 + 0.01).extrude(5).translate((0, 0, 2))) \
        .cut(cq.Workplane("XY").circle(DC.BORE_CLR_D / 2).extrude(12).translate((0, 0, -1)))
    st = cq.Workplane("XY").circle(DC.SHAFT_OD / 2).extrude(15)
    for sgn in (-1, 1):
        st = st.cut(box(40, 10, 8).translate((0, sgn * (-DC.FLAT_Y + 5.0), 7)))
    p["fit_04_shaft_stub"] = st
    p["fit_05_centring_ring"] = cq.Workplane("XY").circle(GC.OD / 2).circle(GC.BORE / 2).extrude(5)
    h = box(60, 14, 10)
    for x, d in ((-22, 4.1), (-11, 4.1), (0, 5.6), (11, 4.2), (22, 3.4)):
        h = h.cut(cq.Workplane("XY").center(x, 0).circle(d / 2).extrude(12).translate((0, 0, -1)))
    p["fit_06_holes"] = h
    # the fork covers' servo-screw geometry exactly (drive_common), servo frame:
    # seat face z = 0, back up; plate = the cover wall BAY_T .. SSCR_HEAD
    pts = DC.SCREW_NEAR + DC.SCREW_FAR
    plate = box(44.0, 30.0, DC.SSCR_HEAD - DC.BAY_T).translate((20.5, 0, DC.BAY_T))
    plate = plate.union(DC.screw_pads(0.0, +1, pts, DC.BAY_T + 0.5, keep_to=DC.BAY_T + 0.5))
    plate = DC.screw_holes(plate, 0.0, +1, pts, DC.SSCR_HEAD + 1.0)
    plate = plate.cut(cq.Workplane("XY").center((DC.WIRE_WIN_X0 + DC.WIRE_WIN_X1) / 2, 0)
                      .rect(DC.WIRE_WIN_X, DC.WIRE_WIN_Y).extrude(10).translate((0, 0, DC.BAY_T - 1)))
    # print it plate-down: flip so the head face lies on the bed
    p["fit_07_servo_screws"] = plate.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, DC.SSCR_HEAD))
    return p


if __name__ == "__main__":
    out = os.path.join(ROOT, "PRINTABLE_FILES", "00_FIT_TEST_print_first")
    os.makedirs(out, exist_ok=True)
    for nm, s in parts().items():
        v = s.val()
        cq.exporters.export(s, os.path.join(out, nm + ".stl"), tolerance=0.01, angularTolerance=0.1)
        bb = v.BoundingBox()
        print("%-22s %6.1f cm3  %4.0f x %4.0f x %4.1f mm  solids %d" % (nm, v.Volume() / 1000, bb.xlen, bb.ylen, bb.zlen, len(v.Solids())))
    open(os.path.join(out, "README.txt"), "w").write(__doc__)
