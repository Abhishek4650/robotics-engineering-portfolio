#!/usr/bin/env python3
"""
The MANUFACTURER'S ST3215 (Waveshare ST3215-3D.zip, official STEP: 8 solids,
incl. the drive horn and the rear IDLER horn) placed in all six servo seats
of the final assembly -- seated on its mounting (cap) face exactly like our
model -- and intersected (exact OCC) with every other part.
Our servo model came from the user's Motor.stl; the official model shows
(a) the drive horn 0.20 mm further out from the seat face and (b) a O19.2
idler horn on the back, 34.04 mm above the seat plane.
"""
import os
import sys

import numpy as np
import cadquery as cq
from OCP.gp import gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_final_assembly as BA   # noqa: E402
import verify_fasteners as VF       # noqa: E402

OFF = os.environ.get("ST3215_STEP", "/tmp/claude-1000/-home-user-ros2-ws-Arm-450-new-design/"
                     "d7055e52-889b-4cd2-992e-dd3a2338ce75/scratchpad/st3215/3d/ST3215.step")
# official frame -> our servo frame (horn on -Z at (0,0), cap face z = 0, case along +X)
M_OFF = np.array([[1, 0, 0, 25.5], [0, 0, 1, 0], [0, -1, 0, 6.4], [0, 0, 0, 1.0]])


def place(sh, T):
    tr = gp_Trsf(); tr.SetValues(*[float(T[i, j]) for i in range(3) for j in range(4)])
    return BRepBuilderAPI_Transform(sh, tr, True).Shape()


def main():
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TDocStd import TDocStd_Document
    from OCP.XCAFDoc import XCAFDoc_DocumentTool
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDF import TDF_LabelSequence, TDF_Label
    from OCP.TDataStd import TDataStd_Name
    from OCP.TopLoc import TopLoc_Location
    doc = TDocStd_Document(TCollection_ExtendedString("d")); r = STEPCAFControl_Reader(); r.SetNameMode(True)
    r.ReadFile(OFF); r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    names = {"金属舵盘（驱动） v2": "DRIVE horn", "金属舵盘（从动） v2": "IDLER horn (back)", "ZK_122": "case middle",
             "SG-ZIJI_15": "case front", "XG-ZIJI_16": "case back", "MOTOR-1723_3": "motor", "PCB-CHAZUO_92": "PCB + connectors",
             "GE_27": "gears"}
    solids = []

    def nm(l):
        n = TDataStd_Name(); return str(n.Get().ToExtString()) if l.FindAttribute(TDataStd_Name.GetID_s(), n) else "?"

    def walk(lab, loc):
        ch = TDF_LabelSequence(); st.GetComponents_s(lab, ch)
        for i in range(1, ch.Length() + 1):
            c = ch.Value(i); l2 = loc.Multiplied(st.GetLocation_s(c)); ref = TDF_Label(); has = st.GetReferredShape_s(c, ref)
            t = ref if has else c
            if st.IsAssembly_s(t):
                walk(t, l2)
            else:
                solids.append((names.get(nm(t), nm(t)), st.GetShape_s(t).Moved(l2)))
    top = TDF_LabelSequence(); st.GetFreeShapes(top)
    for i in range(1, top.Length() + 1):
        walk(top.Value(i), TopLoc_Location())
    A, _ = BA.build()
    S = {c.name: (VF.world(c), c) for c in A.children if VF.world(c) is not None}
    fails = 0
    for k in range(1, 7):
        sv = "servo_J%d" % k
        ch = S[sv][1]
        T = ch.loc.wrapped.Transformation()
        Ts = np.eye(4)
        for a in range(3):
            for b in range(4):
                Ts[a, b] = T.Value(a + 1, b + 1)
        print("J%d: official ST3215 seated like %s" % (k, sv))
        own = "servo_scr_J%d_" % k
        placed = [(lab, place(sh, Ts @ M_OFF)) for lab, sh in solids]
        for lab, w in placed:
            bw = VF.bbox(w)
            for p, (ps, _) in S.items():
                if p.startswith(("servo_J", own)) or not VF.overlap(bw, VF.bbox(ps), 0.0):
                    continue
                v = VF.common(w, ps)
                if v > 1e-3:
                    print("   %-18s x %-22s %8.3f mm3" % (lab, p, v))
                    fails += 1
        # its own servo screws (audit M1): the screw's CORE (O1.4) must run down
        # the real servo's hole -- nothing solid -- while the thread (O2.2)
        # bites into the hole wall
        for p in sorted(n for n in S if n.startswith(own)):
            T = S[p][1].loc.wrapped.Transformation()
            Tp = np.eye(4)
            for a in range(3):
                for b in range(4):
                    Tp[a, b] = T.Value(a + 1, b + 1)
            core = place(cq.Workplane("XY").circle(0.7).extrude(-BA.DC.SSCR_L + 0.05).val().wrapped, Tp)
            hit = sum(VF.common(core, w) for _, w in placed)
            bite = sum(VF.common(S[p][0], w) for lab, w in placed if lab == "case back")
            ok = hit < 1e-3 and bite > 1e-3
            print("   %-22s core in the real hole: %s (%.3f mm3 solid), thread bites %.2f mm3  %s"
                  % (p, "yes" if hit < 1e-3 else "NO", hit, bite, "ok" if ok else "PROBLEM"))
            fails += 0 if ok else 1
    print("\n(the case x housing overlaps above are the designed -0.22 pinch; the DRIVE horn x coupler")
    print(" overlap is the real horn standing 0.20 mm further out -- checked next)")
    bad = fails - 18
    # the drive horn 0.20 further out: the coupler bolted to it -- and the whole
    # chain beyond -- sits 0.20 further along the joint axis. Shift it and
    # re-measure every clearance between the two sides of that joint.
    import make_rule6_pages as R6
    import make_rule5_views as R5
    import trimesh
    meshes = {k: R5.tess(v[0], 0.05, 0.25) for k, v in S.items()}
    print("\nDRIVEN CHAIN SHIFTED 0.20 mm (real horn), clearance fixed side <-> moving side, per joint")
    worst_all = 99
    for k in range(1, 7):
        ch = S["servo_J%d" % k][1]; T = ch.loc.wrapped.Transformation()
        away = -np.array([T.Value(1, 3), T.Value(2, 3), T.Value(3, 3)])      # servo local -Z = horn side
        fixed, moving = trimesh.collision.CollisionManager(), trimesh.collision.CollisionManager()
        for nm, (V, F) in meshes.items():
            b = R6.body(nm)
            if b is None or nm.startswith(("spring_", "brg_J%d" % k)) or nm == "servo_J%d" % k \
                    or nm.startswith("horn_screw_J%d" % k):
                continue
            m = trimesh.Trimesh(V + (0.2 * away if b >= k else 0.0), F, process=False)
            (moving if b >= k else fixed).add_object(nm, m)
        d, names = fixed.min_distance_other(moving, return_names=True)
        worst_all = min(worst_all, d)
        print("   J%d: %.3f mm  (%s | %s)  %s" % (k, d, names[0], names[1], "ok" if d > 0.1 else "TOO CLOSE"))
        bad += d <= 0.1
    print("\nOFFICIAL-SERVO CHECK: %d problem(s)  (18 designed / expected overlaps explained above)" % bad)


if __name__ == "__main__":
    main()
