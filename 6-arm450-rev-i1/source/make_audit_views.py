#!/usr/bin/env python3
"""Pictures for the audit report (Rule 5: sharp, unambiguous interfaces).

1. idler_compare.png -- the manufacturer's ST3215 next to our servo model
   (from Motor.stl), both in the servo frame, seen from the back: the rear
   idler horn exists only on the real servo.
2. idler_cut_J{1,4,6}.png -- exact OCC section through the servo axis of the
   three seats that had to be relieved, the MANUFACTURER'S servo seated in
   the final assembly. Blue lines = measured gaps, green = contact, red
   hatch = overlap (none expected beyond the designed -0.22 case pinch,
   orange).
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_rule5_views as R5        # noqa: E402
import verify_official_servo as VO   # noqa: E402
import verify_fasteners as VF        # noqa: E402

OUT = os.path.join(HERE, "RULE6_VIEWS")


def official_solids():
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TDocStd import TDocStd_Document
    from OCP.XCAFDoc import XCAFDoc_DocumentTool
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDF import TDF_LabelSequence, TDF_Label
    from OCP.TDataStd import TDataStd_Name
    from OCP.TopLoc import TopLoc_Location
    doc = TDocStd_Document(TCollection_ExtendedString("d")); r = STEPCAFControl_Reader(); r.SetNameMode(True)
    r.ReadFile(VO.OFF); r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    names = {"金属舵盘（驱动） v2": "drive_horn", "金属舵盘（从动） v2": "idler_horn"}
    out = []

    def nm(l):
        n = TDataStd_Name(); return str(n.Get().ToExtString()) if l.FindAttribute(TDataStd_Name.GetID_s(), n) else "?"

    def walk(lab, loc):
        ch = TDF_LabelSequence(); st.GetComponents_s(lab, ch)
        for i in range(1, ch.Length() + 1):
            c = ch.Value(i); l2 = loc.Multiplied(st.GetLocation_s(c)); ref = TDF_Label()
            t = ref if st.GetReferredShape_s(c, ref) else c
            if st.IsAssembly_s(t):
                walk(t, l2)
            else:
                out.append((names.get(nm(t), "case"), st.GetShape_s(t).Moved(l2)))
    top = TDF_LabelSequence(); st.GetFreeShapes(top)
    for i in range(1, top.Length() + 1):
        walk(top.Value(i), TopLoc_Location())
    return out


def seat_T(S, k):
    T = S["servo_J%d" % k][1].loc.wrapped.Transformation()
    Ts = np.eye(4)
    for a in range(3):
        for b in range(4):
            Ts[a, b] = T.Value(a + 1, b + 1)
    return Ts


COL = {"case": "#3a3a3a", "drive_horn": "#e08a00", "idler_horn": "#e0001b"}


def idler_compare(S, OFFI):
    Ti = np.linalg.inv(seat_T(S, 4))
    meshes, cols = {}, {}
    for i, (lab, sh) in enumerate(OFFI):             # manufacturer's servo at x = 0
        nm = "off_%d_%s" % (i, lab)
        meshes[nm] = R5.tess(VO.place(sh, VO.M_OFF), 0.02, 0.15); cols[nm] = COL[lab]
    ours = VO.place(S["servo_J4"][0], Ti)            # our model at x = +60 (servo frame)
    V, F = R5.tess(ours, 0.02, 0.15); V = V + np.array([60.0, 0, 0])
    meshes["ours"] = (V, F); cols["ours"] = "#6d6d6d"
    p = os.path.join(OUT, "idler_compare.png")
    R5.vtk_render(meshes, cols, p, ((50, 0, 10), (0.35, -0.55, 0.76), (0, 0, 1)), size=(3000, 1800), zoom=1.6)
    return p


def idler_cut(S, OFFI, k, cols):
    Ts = seat_T(S, k); Ti = np.linalg.inv(Ts)
    sv = [VO.place(sh, Ts @ VO.M_OFF) for _, sh in OFFI]
    box = None
    for w in sv:
        b = VF.bbox(w)
        box = b if box is None else (np.minimum(box[0], b[0]), np.maximum(box[1], b[1]))
    P = {}
    for i, (lab, _) in enumerate(OFFI):
        g = R5.section2d(VO.place(sv[i], Ti), (0, 0, 0), (0, 1, 0), 0, 2)
        if g is not None and not g.is_empty:
            key = "ST3215_" + lab
            P[key] = g.union(P[key]) if key in P else g
    for nm, (w, _) in S.items():
        if nm.startswith("servo_") or nm.startswith("spring") or not VF.overlap(box, VF.bbox(w), 12.0):
            continue
        g = R5.section2d(VO.place(w, Ti), (0, 0, 0), (0, 1, 0), 0, 2)
        if g is not None and not g.is_empty and g.area > 1e-3:
            P[nm] = g
    c = dict(cols); c.update({"ST3215_case": COL["case"], "ST3215_drive_horn": COL["drive_horn"],
                              "ST3215_idler_horn": COL["idler_horn"]})
    old = R5.designed

    def designed(a, b):                             # the official case gets the servo's designed pinch
        if "ST3215_drive_horn" in (a, b):
            return "the real drive horn stands 0.20 further out: its coupler rides 0.20 up (checked, >= 0.30 clear)"
        a2 = "servo_J%d" % k if a.startswith("ST3215_case") else a
        b2 = "servo_J%d" % k if b.startswith("ST3215_case") else b
        return old(a2, b2)
    R5.designed = designed
    IF = R5.interfaces(P)
    R5.designed = old
    fig, axs = plt.subplots(1, 2, figsize=(16, 8.3), gridspec_kw=dict(width_ratios=[1.25, 1]))
    R5.draw_section(axs[0], P, c, IF)
    axs[0].set_title("J%d seat, section through the servo axis (servo frame, mm)" % k, fontsize=11)
    R5.draw_section(axs[1], P, c, IF, window=(-18, 18, 24, 42), labels=True)
    axs[1].set_title("close-up: rear IDLER horn (red) and the pocket cut for it", fontsize=11)
    idl = [x for x in IF if "ST3215_idler_horn" in (x[0], x[1])]
    bad = [x for x in IF if x[2] == "OVERLAP"]
    gaps = sorted(x[3] for x in idl if x[2] == "gap")
    txt = "idler horn: %s   |   overlaps not designed: %d" % (
        ("smallest gap %.2f mm" % gaps[0]) if gaps else ("contacts/overlaps: %d" % len(idl)), len(bad))
    fig.text(0.5, 0.02, txt, ha="center", fontsize=11, color="#b00000" if bad else "#006000", fontweight="bold")
    for ax in axs:
        ax.grid(True, lw=0.3, alpha=0.5)
    p = os.path.join(OUT, "idler_cut_J%d.png" % k)
    fig.savefig(p, dpi=300, bbox_inches="tight"); fig.savefig(p[:-4] + ".pdf", bbox_inches="tight"); plt.close(fig)
    return p, (gaps[0] if gaps else None), len(bad)


def main():
    os.makedirs(OUT, exist_ok=True)
    S = {}
    A, _ = VO.BA.build()
    for ch in A.children:
        w = VF.world(ch)
        if w is not None:
            S[ch.name] = (w, ch)
    OFFI = official_solids()
    print("wrote", idler_compare(S, OFFI))
    cols = R5.colours(S.keys())
    res = []
    for k in (1, 4, 6):
        p, g, nb = idler_cut(S, OFFI, k, cols)
        res.append((k, g, nb))
        print("wrote %s  idler min gap %s  undesigned overlaps %d" % (p, g, nb))
    print("AUDIT VIEWS: %d undesigned overlap(s)" % sum(r[2] for r in res))


if __name__ == "__main__":
    main()
