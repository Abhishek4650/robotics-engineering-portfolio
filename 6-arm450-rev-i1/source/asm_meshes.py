#!/usr/bin/env python3
"""Every part of the released assembly as a WORLD-placed trimesh.

dump_assembly returns bounding boxes only. Swing clearance and interference
need the real triangles at the real orientation, so this tessellates each
placed shape straight out of the STEP.
"""
import os

import numpy as np
import trimesh
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool

ASM = "/home/user/ros2_ws/Arm_450_new_design/ARM450_FINAL_ASSEMBLY.step"


def _name(lab):
    n = TDataStd_Name()
    if lab.FindAttribute(TDataStd_Name.GetID_s(), n):
        return str(n.Get().ToExtString())
    return "?"


def _to_mesh(shape, lin=0.4):
    BRepMesh_IncrementalMesh(shape, lin, False, 0.5, True)
    V, F = [], []
    e = TopExp_Explorer(shape, TopAbs_FACE)
    while e.More():
        f = TopoDS.Face_s(e.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(f, loc)
        if tri is not None:
            tr = loc.Transformation()
            base = len(V)
            for i in range(1, tri.NbNodes() + 1):
                p = tri.Node(i).Transformed(tr)
                V.append((p.X(), p.Y(), p.Z()))
            for i in range(1, tri.NbTriangles() + 1):
                a, b, c = tri.Triangle(i).Get()
                F.append((base + a - 1, base + b - 1, base + c - 1))
        e.Next()
    if not F:
        return None
    m = trimesh.Trimesh(vertices=np.array(V), faces=np.array(F), process=False)
    # per-face tessellation duplicates every shared-edge vertex: merge them or
    # the mesh is open and contains() is unreliable (found by the closure audit)
    m.merge_vertices(digits_vertex=4)
    m.remove_unreferenced_vertices()
    return m


def load(skip=()):
    """{name: placed trimesh}. `skip` drops parts being replaced."""
    doc = TDocStd_Document(TCollection_ExtendedString("d"))
    r = STEPCAFControl_Reader()
    r.SetNameMode(True)
    r.ReadFile(ASM)
    r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    out = {}

    def walk(lab, loc):
        ch = TDF_LabelSequence()
        st.GetComponents_s(lab, ch)
        for i in range(1, ch.Length() + 1):
            c = ch.Value(i)
            l2 = loc.Multiplied(st.GetLocation_s(c))
            ref = TDF_Label()
            has = st.GetReferredShape_s(c, ref)
            tgt = ref if has else c
            nm = _name(c)
            if nm in ("?", ""):
                nm = _name(tgt)
            if st.IsAssembly_s(tgt):
                walk(tgt, l2)
            else:
                if nm in skip:
                    continue
                mv = st.GetShape_s(tgt).Moved(l2)
                m = _to_mesh(mv)
                if m is not None:
                    key = nm
                    k = 2
                    while key in out:
                        key = "%s#%d" % (nm, k)
                        k += 1
                    out[key] = m
    top = TDF_LabelSequence()
    st.GetFreeShapes(top)
    for i in range(1, top.Length() + 1):
        walk(top.Value(i), TopLoc_Location())
    # REV_I_CLAMP: the released O38 ring cannot enter the links' D-shaped
    # bores (the seam ear). Substitute the rev-I clamp, seated in each link
    # half's own frame (the released clamps sit at its bore centre, z 0..14).
    import asm_xforms as AX
    X = AX.xforms()
    here = os.path.dirname(os.path.abspath(__file__))
    for ck, lk in (("shaft_clamp_1", "link_upper_groove"), ("shaft_clamp_2", "link_upper_tongue"),
                   ("shaft_clamp_3", "link_fore_groove"), ("shaft_clamp_4", "link_fore_tongue")):
        if ck in out or ck in skip:
            if ck in skip:
                continue
            m = trimesh.load(os.path.join(here, "shaft_clamp.stl"))
            m.apply_transform(X[lk])
            out[ck] = m
    return out


if __name__ == "__main__":
    ms = load()
    print("%d placed parts" % len(ms))
    for k, m in sorted(ms.items()):
        b = m.bounds
        print("  %-22s x %8.2f..%8.2f  y %8.2f..%8.2f  z %8.2f..%8.2f"
              % (k, b[0][0], b[1][0], b[0][1], b[1][1], b[0][2], b[1][2]))


# ---------------------------------------------------------------------------
# rev-I neighbours for the drive-train checks: the CURRENT file of each part
# (rev-I where one exists), placed by the released assembly's transform and
# then mapped by F (world -> the joint frame being checked). Link halves also
# carry their exact BRep under the SAME transform (verify_drive.contains uses
# it: the forearm meshes are too fine for trimesh's ray fallback).
# ---------------------------------------------------------------------------
REL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out_cad")
_SRC = {"link_upper_groove": REL_DIR}
_CLAMP_LINK = {"shaft_clamp_1": "link_upper_groove", "shaft_clamp_2": "link_upper_tongue",
               "shaft_clamp_3": "link_fore_groove", "shaft_clamp_4": "link_fore_tongue"}


def neighbour(k, F=np.eye(4)):
    import asm_xforms as AX
    here = os.path.dirname(os.path.abspath(__file__))
    X = AX.xforms()
    if k in _CLAMP_LINK:
        fn, T = os.path.join(here, "shaft_clamp"), X[_CLAMP_LINK[k]]
    elif k == "base":
        fn, T = os.path.join(here, "base"), np.eye(4)
    else:
        fn, T = os.path.join(_SRC.get(k, here), k), X[k]
    m = trimesh.load(fn + ".stl")
    m.merge_vertices(digits_vertex=4)
    m.apply_transform(F @ T)
    if k.startswith("link_"):
        import cadquery as cq
        from OCP.gp import gp_Trsf
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        G = F @ T
        tr = gp_Trsf(); tr.SetValues(*[float(G[i, j]) for i in range(3) for j in range(4)])
        m.occ = BRepBuilderAPI_Transform(cq.importers.importStep(fn + ".step").val().wrapped, tr, True).Shape()
    return m
