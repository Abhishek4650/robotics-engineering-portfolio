"""Exact 4x4 world placement of each named part in the released assembly."""
import numpy as np
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location

ASM = "/home/user/ros2_ws/Arm_450_new_design/ARM450_FINAL_ASSEMBLY.step"


def xforms():
    doc = TDocStd_Document(TCollection_ExtendedString("d"))
    r = STEPCAFControl_Reader(); r.SetNameMode(True); r.ReadFile(ASM); r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def nm(l):
        n = TDataStd_Name()
        return str(n.Get().ToExtString()) if l.FindAttribute(TDataStd_Name.GetID_s(), n) else "?"
    out = {}

    def walk(lab, loc):
        ch = TDF_LabelSequence(); st.GetComponents_s(lab, ch)
        for i in range(1, ch.Length() + 1):
            c = ch.Value(i); l2 = loc.Multiplied(st.GetLocation_s(c))
            ref = TDF_Label(); has = st.GetReferredShape_s(c, ref); tgt = ref if has else c
            n = nm(c)
            if n in ("?", ""):
                n = nm(tgt)
            if st.IsAssembly_s(tgt):
                walk(tgt, l2)
            else:
                T = l2.Transformation()
                M = np.eye(4)
                for a in range(3):
                    for b in range(4):
                        M[a, b] = T.Value(a + 1, b + 1)
                k = n; j = 2
                while k in out:
                    k = "%s#%d" % (n, j); j += 1
                out[k] = M
    top = TDF_LabelSequence(); st.GetFreeShapes(top)
    for i in range(1, top.Length() + 1):
        walk(top.Value(i), TopLoc_Location())
    return out
