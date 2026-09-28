#!/usr/bin/env python3
"""
DISASSEMBLY / ASSEMBLY PATHS on the exact solids (Rule 3 item 8): each unit is
slid along its real path in 1 mm steps and intersected (exact OCC common
volume) with every part that stays. A sliding fit stays at 0 mm3; a unit that
is blocked shows a growing volume.
  J2 / J3 / J5  servo + shaft (+ horn screws) out of p1 along the axis, towards
                the servo's back (p2 and the link set screws / axle grub off)
  J4 / J6       servo out along its channel (+x) once cap, bearing, hub and
                all above are off
  J1            servo out along its channel from the foot (hub off), and the
                whole arm lifted off the base once the spigot collar is off
"""
import os
import sys

import numpy as np
from OCP.gp import gp_Trsf, gp_Vec
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audit_gaps as AG            # noqa: E402
import make_rule6_pages as R6      # noqa: E402
import verify_fasteners as VF      # noqa: E402


def moved(sh, v):
    tr = gp_Trsf(); tr.SetTranslation(gp_Vec(*map(float, v)))
    return BRepBuilderAPI_Transform(sh, tr, True).Shape()


def axis_of(C, nm, col):
    T = C[nm].loc.wrapped.Transformation()
    return np.array([T.Value(1, col), T.Value(2, col), T.Value(3, col)])


CORE = {}      # servo name -> the servo without its two pinched side strips (servo frame |y| > 12.15)


def servo_core(S, C, m):
    """A servo sliding in its channel keeps the designed -0.22 pinch on both
    long sides, and that overlap SHRINKS as it slides out -- which hid a real
    snag (the J6 servo's rear boss on the new bridge, 6.5 mm3) inside the
    baseline. Judge the servo by its core instead: everything but the pinched
    strips, which must never overlap anything."""
    import cadquery as cq
    T = C[m].loc.wrapped.Transformation()
    Tm = np.eye(4)
    for a in range(3):
        for b in range(4):
            Tm[a, b] = T.Value(a + 1, b + 1)
    box = cq.Workplane("XY").center(12.5, 0).rect(120.0, 24.30).extrude(60.0).translate((0, 0, -15.0)).val().wrapped
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    c = BRepAlgoAPI_Common(S[m], moved_T(box, Tm)); c.Build()
    return c.Shape()


def moved_T(sh, T):
    from OCP.gp import gp_Trsf
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    tr = gp_Trsf(); tr.SetValues(*[float(T[i, j]) for i in range(3) for j in range(4)])
    return BRepBuilderAPI_Transform(sh, tr, True).Shape()


def sweep(S, moving, removed, direction, length, label, step=1.0):
    stay = {k: v for k, v in S.items() if k not in moving and k not in removed and not k.startswith("spring_")}
    S = dict(S)
    for m in moving:
        if m in CORE:
            S[m] = CORE[m]
    # baseline: the overlap each pair already has in place (the designed -0.22
    # servo pinch); sliding in that fit is free -- only an INCREASE blocks
    base = {}
    for m in moving:
        bm = VF.bbox(S[m])
        for k, sh in stay.items():
            if VF.overlap(bm, VF.bbox(sh), 0.0):
                base[(m, k)] = VF.common(S[m], sh)
    worst, at = 0.0, None
    for s_ in np.arange(step, length + 1e-6, step):
        v = direction * s_
        for m in moving:
            w = moved(S[m], v); bw = VF.bbox(w)
            for k, sh in stay.items():
                if VF.overlap(bw, VF.bbox(sh), 0.0):
                    vol = VF.common(w, sh) - base.get((m, k), 0.0)
                    if vol > worst + 1e-3:
                        worst, at = vol, (s_, m, k)
    ok = worst < 1e-2
    print("   %-58s %s" % (label, "FREE (no overlap beyond the fit it starts in)" if ok else
          "BLOCKED: +%.2f mm3 at %.0f mm (%s | %s)" % (worst, at[0], at[1], at[2])))
    return ok, worst, at


def official_servos(S, C):
    """replace each servo by the manufacturer's model (idler horn included),
    seated on its cap face exactly like ours"""
    import verify_official_servo as VO
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TDocStd import TDocStd_Document
    from OCP.XCAFDoc import XCAFDoc_DocumentTool
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TopoDS import TopoDS_Compound
    from OCP.BRep import BRep_Builder
    doc = TDocStd_Document(TCollection_ExtendedString("d")); r = STEPCAFControl_Reader(); r.ReadFile(VO.OFF); r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    from OCP.TDF import TDF_LabelSequence
    top = TDF_LabelSequence(); st.GetFreeShapes(top)
    shape = st.GetShape_s(top.Value(1))
    for k in range(1, 7):
        T = C["servo_J%d" % k].loc.wrapped.Transformation()
        Ts = np.eye(4)
        for a in range(3):
            for b in range(4):
                Ts[a, b] = T.Value(a + 1, b + 1)
        S["servo_J%d" % k] = VO.place(shape, Ts @ VO.M_OFF)
    return S


def main():
    S, C = AG.load()
    if "--official" in sys.argv:
        S = official_servos(S, C)
        print("(servos = the MANUFACTURER'S ST3215 model, rear idler horn included)")
    for k in range(1, 7):
        CORE["servo_J%d" % k] = servo_core(S, C, "servo_J%d" % k)
    res = []
    for k, p2, shaft in ((2, "J2_turret_p2", "J2_shaft"), (3, "J3_p2", "J3_shaft"), (5, "J5_p2", "J5_shaft")):
        back = axis_of(C, "servo_J%d" % k, 3)
        moving = {"servo_J%d" % k, shaft} | {n for n in S if n.startswith("horn_screw_J%d" % k)}
        removed = {p2} | {n for n in S if n.startswith(("split_J%d" % k, "servo_scr_J%d" % k))} | \
            {n for n in S if n.startswith("link_set")} | {"j5_grub"}
        res.append(sweep(S, moving, removed, back, 45.0, "J%d servo + shaft out of p1, towards the servo back" % k))
    for k, cap, top in ((4, "j4_cap", "j4_hub"), (6, "j6_cap", "j6_flange")):
        xdir = axis_of(C, "servo_J%d" % k, 1)
        above = {n for n in S if (R6.body(n) or 0) >= k}
        removed = ({cap, "brg_J%d" % k, top} | {n for n in S if n.startswith(("cap_J%d" % k, "horn_screw_J%d" % k,
                                                                               "servo_scr_J%d" % k))} | above) - {"servo_J%d" % k}
        res.append(sweep(S, {"servo_J%d" % k}, removed, xdir, 50.0, "J%d servo out along its channel (+x), cap/hub off" % k, 2.0))
    xdir = axis_of(C, "servo_J1", 1)
    above = {n for n in S if (R6.body(n) or 0) >= 1}
    res.append(sweep(S, {"servo_J1"}, above | {"brg_J1_z3", "brg_J1_z43", "base"} |
                     {n for n in S if n.startswith(("m4_base_foot", "servo_scr_J1"))},
                     xdir, 50.0, "J1 servo out of the foot along its channel (+x), base/hub off", 2.0))
    turret = {n for n in S if (R6.body(n) or 0) >= 1} - {"spigot_collar", "collar_pinch", "collar_ins", "j1_hub"} \
        - {n for n in S if n.startswith("horn_screw_J1")}
    heavy = {n for n in turret if R6.body(n) in (1,)}                 # the parts that pass the bearings
    res.append(sweep(S, heavy, {"spigot_collar", "collar_pinch", "collar_ins"} | (turret - heavy), np.array([0, 0, 1.0]),
                     70.0, "J1 turret lifted off the base (collar off)", 2.0))
    n_bad = sum(1 for ok, _, _ in res if not ok)
    print("\nDISASSEMBLY PATHS: %d blocked" % n_bad)
    return n_bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
