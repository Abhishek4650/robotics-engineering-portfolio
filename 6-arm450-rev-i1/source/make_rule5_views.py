#!/usr/bin/env python3
"""
RULE 5 -- images sharp enough to judge every solid interface.

From the EXACT solids of the final assembly (the same shapes the checks use):
  * 3D (VTK, 2400 x 1800 px): every part opaque in its OWN colour, smooth
    shading, black feature edges; iso / side / front + a CUT-AWAY through
    the joint plane with the cut faces filled, so a servo is seen sitting in
    its housing, not hanging behind a translucent shell.
  * 2D exact section (OpenCascade section of each solid, vector PDF):
      flat colour per part, thin black outline;
      OVERLAP (solids intersecting) filled RED -- designed ones (the -0.22
      servo pinch, a screw cutting its own thread) ORANGE and labelled;
      CONTACT (faces touching) drawn as a thick GREEN line;
      every gap under 1 mm marked, its measured value written in the zooms.
  * zoom panels (+-4 mm) on each interface of the cut, each captioned with
    the two parts and the measured contact / gap / overlap.
"""
import os
import re
import sys

import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                 # noqa: E402
from matplotlib.patches import PathPatch        # noqa: E402
from matplotlib.path import Path                # noqa: E402
from shapely.geometry import LineString, Polygon, MultiPolygon, GeometryCollection   # noqa: E402
from shapely.ops import polygonize, unary_union, nearest_points                        # noqa: E402

from OCP.BRepAlgoAPI import BRepAlgoAPI_Section     # noqa: E402
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir           # noqa: E402
from OCP.TopExp import TopExp_Explorer              # noqa: E402
from OCP.TopAbs import TopAbs_EDGE                  # noqa: E402
from OCP.TopoDS import TopoDS                       # noqa: E402
from OCP.BRepAdaptor import BRepAdaptor_Curve       # noqa: E402
from OCP.GCPnts import GCPnts_QuasiUniformDeflection   # noqa: E402
from OCP.BRepMesh import BRepMesh_IncrementalMesh   # noqa: E402
from OCP.BRep import BRep_Tool                      # noqa: E402
from OCP.TopLoc import TopLoc_Location              # noqa: E402
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_final_assembly as BA   # noqa: E402
import verify_fasteners as VF       # noqa: E402
from make_final_pdf import JOINTS   # noqa: E402

OUT = os.path.join(HERE, "RULE5_VIEWS")
AX = {"x": 0, "y": 1, "z": 2}
PRINTED_PALETTE = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#46c7c7", "#f032e6", "#9a6324",
                   "#808000", "#008080", "#e6a800", "#800000", "#1f77b4", "#aa6e28", "#6a5acd", "#2e8b57",
                   "#c71585", "#b8860b", "#556b2f", "#8b4513"]
SCREW_RX = re.compile(r"^(split_J\d_\d|cap_J\d_\d|j4base_forearm_\d|j5fork_j4hub_\d|j3fork_link_\d|m4_base_foot_\d|"
                      r"collar_pinch|j5_grub|pin_J\d_\w+_[+-]\d|collar_clamp_\S+|seam_(upper|fore)_\d+|ear_bolt_\w+|"
                      r"link_set_\d_\d+|horn_screw_J\d_\d+|servo_scr_J\d_\d)$")
LINK_OF = {"1": "link_upper_groove", "2": "link_upper_tongue", "3": "link_fore_groove", "4": "link_fore_tongue"}


def kind(n):
    if re.match(r"^servo_J\d$", n):          # (not the servo screws: servo_scr_J..)
        return "servo"
    if n.startswith("brg"):
        return "bearing"
    if n.startswith("spring"):
        return "spring"
    if "nut" in n:
        return "nut"
    if "_ins" in n:
        return "insert"
    if SCREW_RX.match(n):
        return "screw"
    return "printed"


FIXED = {"servo": "#2b2b2b", "bearing": "#a7b0b8", "spring": "#8fc1e3", "nut": "#555555",
         "insert": "#d4a017", "screw": "#34495e"}


def colours(names):
    out, i = {}, 0
    for n in sorted(names):
        k = kind(n)
        if k == "printed":
            out[n] = PRINTED_PALETTE[i % len(PRINTED_PALETTE)]; i += 1
        else:
            out[n] = FIXED[k]
    return out


def designed(a, b):
    for s, h in ((a, b), (b, a)):
        m = re.match(r"^servo_J(\d)$", s)
        if m and kind(h) == "printed":
            return "servo -0.22 pinch"
        m = re.match(r"^link_set_(\d)_\d+$", s)
        if m and h == LINK_OF[m.group(1)]:
            return "M5 thread formed in the link"
        m = re.match(r"^servo_scr_J(\d)_\d$", s)
        if m and h == "servo_J" + m.group(1):
            return "self-tapping thread in the servo's back hole"
        if s == "j5_grub" and h == "j6_body":
            return "grub thread formed"
    return None


# ---------------------------------------------------------------- geometry
def load():
    A, _ = BA.build()
    S = {}
    for ch in A.children:
        w = VF.world(ch)
        if w is not None:
            S[ch.name] = w
    return S


def _wire_ring(wire, face, i0, i1, defl):
    from OCP.BRepTools import BRepTools_WireExplorer
    from OCP.TopAbs import TopAbs_REVERSED as REV
    pts = []
    we = BRepTools_WireExplorer(wire, face)
    while we.More():
        ed = we.Current()
        c = BRepAdaptor_Curve(ed)
        d = GCPnts_QuasiUniformDeflection(c, defl)
        if d.IsDone() and d.NbPoints() >= 2:
            seg = [d.Value(i) for i in range(1, d.NbPoints() + 1)]
        else:
            seg = [c.Value(c.FirstParameter()), c.Value(c.LastParameter())]
        if we.Orientation() == REV:
            seg = seg[::-1]
        for p in seg:
            v = (p.X(), p.Y(), p.Z())
            q = (v[i0], v[i1])
            if not pts or (abs(pts[-1][0] - q[0]) + abs(pts[-1][1] - q[1])) > 1e-9:
                pts.append(q)
        we.Next()
    return pts


def section2d(shape, o, n, i0, i1, defl=0.002):
    """Exact section = the solid's boolean COMMON with the cutting plane (a
    face), read face by face, outer wire + holes in order. (Chaining loose
    section edges dropped whole parts when one edge failed to discretise.)"""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.BRepTools import BRepTools
    from OCP.TopAbs import TopAbs_WIRE
    pln = gp_Pln(gp_Pnt(*map(float, o)), gp_Dir(*map(float, n)))
    face = BRepBuilderAPI_MakeFace(pln, -2000, 2000, -2000, 2000).Face()
    c = BRepAlgoAPI_Common(shape, face); c.Build()
    if not c.IsDone():
        return None
    polys = []
    e = TopExp_Explorer(c.Shape(), TopAbs_FACE)
    while e.More():
        f = TopoDS.Face_s(e.Current())
        outer = BRepTools.OuterWire_s(f)
        ext = _wire_ring(outer, f, i0, i1, defl)
        holes = []
        w = TopExp_Explorer(f, TopAbs_WIRE)
        while w.More():
            ww = TopoDS.Wire_s(w.Current())
            if not ww.IsSame(outer):
                h = _wire_ring(ww, f, i0, i1, defl)
                if len(h) >= 3:
                    holes.append(h)
            w.Next()
        if len(ext) >= 3:
            p = Polygon(ext, holes).buffer(0)
            if not p.is_empty:
                polys.append(p)
        e.Next()
    return unary_union(polys) if polys else None


def tess(shape, lin=0.02, ang=0.12):
    BRepMesh_IncrementalMesh(shape, lin, False, ang, True)
    V, F = [], []
    e = TopExp_Explorer(shape, TopAbs_FACE)
    while e.More():
        f = TopoDS.Face_s(e.Current()); loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(f, loc)
        if tri is not None:
            T = loc.Transformation(); b = len(V)
            for i in range(1, tri.NbNodes() + 1):
                p = tri.Node(i).Transformed(T); V.append((p.X(), p.Y(), p.Z()))
            rev = f.Orientation() == TopAbs_REVERSED
            for i in range(1, tri.NbTriangles() + 1):
                a, bb, c = tri.Triangle(i).Get()
                F.append((b + a - 1, b + c - 1, b + bb - 1) if rev else (b + a - 1, b + bb - 1, b + c - 1))
        e.Next()
    return np.array(V, float), np.array(F, int)


# --------------------------------------------------------------- 3D (VTK)
# Render resolution multiplier (the user: "the pdf has poor image quality"): every
# render is made QUALITY x larger with lines QUALITY x thicker, and the PDFs embed
# the pictures at their native resolution (imshow interpolation="none").
QUALITY = 2.0


def vtk_render(meshes, cols, out_png, view, clip=None, size=(2400, 1800), title=None, scale=None, zoom=1.35):
    import vtk
    from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
    ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
    for nm, (V, F) in meshes.items():
        if not len(F):
            continue
        pd = vtk.vtkPolyData()
        pts = vtk.vtkPoints(); pts.SetData(numpy_to_vtk(V.astype(np.float64), deep=True)); pd.SetPoints(pts)
        cells = np.hstack([np.full((len(F), 1), 3), F]).astype(np.int64).ravel()
        ca = vtk.vtkCellArray(); ca.SetCells(len(F), numpy_to_vtkIdTypeArray(cells, deep=True)); pd.SetPolys(ca)
        # merge the per-face duplicate vertices: the cut outline must close
        # into loops, or the cap is not filled and a cut part looks hollow
        cln = vtk.vtkCleanPolyData(); cln.SetInputData(pd); cln.SetTolerance(1e-6); cln.Update()
        pd = cln.GetOutput()
        src = pd
        col = tuple(int(cols[nm][i:i + 2], 16) / 255.0 for i in (1, 3, 5))
        if clip is not None:
            plane = vtk.vtkPlane(); plane.SetOrigin(*clip[0]); plane.SetNormal(*clip[1])
            cl = vtk.vtkClipPolyData(); cl.SetInputData(pd); cl.SetClipFunction(plane); cl.Update()
            src = cl.GetOutput()
            # cap: the cut outline, triangulated, in a darker shade of the part colour
            cut = vtk.vtkCutter(); cut.SetInputData(pd); cut.SetCutFunction(plane); cut.Update()
            strip = vtk.vtkStripper(); strip.SetInputConnection(cut.GetOutputPort()); strip.Update()
            tri = vtk.vtkContourTriangulator(); tri.SetInputConnection(strip.GetOutputPort()); tri.Update()
            if tri.GetOutput().GetNumberOfCells():
                m2 = vtk.vtkPolyDataMapper(); m2.SetInputConnection(tri.GetOutputPort())
                a2 = vtk.vtkActor(); a2.SetMapper(m2)
                a2.GetProperty().SetColor(*[c * 0.55 for c in col]); a2.GetProperty().LightingOff()
                ren.AddActor(a2)
                m3 = vtk.vtkPolyDataMapper(); m3.SetInputConnection(strip.GetOutputPort())
                a3 = vtk.vtkActor(); a3.SetMapper(m3); a3.GetProperty().SetColor(0, 0, 0)
                a3.GetProperty().SetLineWidth(2.0 * QUALITY); ren.AddActor(a3)
        nrm = vtk.vtkPolyDataNormals(); nrm.SetInputData(src); nrm.SetFeatureAngle(35); nrm.SplittingOn()
        nrm.ConsistencyOn(); nrm.Update()
        m = vtk.vtkPolyDataMapper(); m.SetInputConnection(nrm.GetOutputPort())
        a = vtk.vtkActor(); a.SetMapper(m)
        p = a.GetProperty(); p.SetColor(*col); p.SetAmbient(0.25); p.SetDiffuse(0.75); p.SetSpecular(0.15)
        ren.AddActor(a)
        fe = vtk.vtkFeatureEdges(); fe.SetInputData(src); fe.BoundaryEdgesOn(); fe.FeatureEdgesOn()
        fe.SetFeatureAngle(35); fe.ManifoldEdgesOff(); fe.NonManifoldEdgesOff(); fe.ColoringOff()
        me = vtk.vtkPolyDataMapper(); me.SetInputConnection(fe.GetOutputPort())
        ae = vtk.vtkActor(); ae.SetMapper(me); ae.GetProperty().SetColor(0, 0, 0); ae.GetProperty().SetLineWidth(1.3 * QUALITY)
        ren.AddActor(ae)
    lk = vtk.vtkLightKit(); lk.AddLightsToRenderer(ren)
    cam = ren.GetActiveCamera(); cam.ParallelProjectionOn()
    fp, d, up = view
    cam.SetFocalPoint(*fp); cam.SetPosition(*(np.asarray(fp) + 1000 * np.asarray(d))); cam.SetViewUp(*up)
    if scale is None:
        ren.ResetCamera(); cam.Zoom(zoom)
    else:                                   # close-up: fixed half-height in mm around the focal point
        cam.SetParallelScale(scale); ren.ResetCameraClippingRange()
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.AddRenderer(ren)
    win.SetSize(int(size[0] * QUALITY), int(size[1] * QUALITY)); win.SetMultiSamples(8); win.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(out_png); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()
    return out_png


def trimmed(png, margin=12):
    """the rendered image without its white border (the part fills the panel)."""
    im = plt.imread(png)
    nonwhite = np.where(im[:, :, :3].min(axis=2) < 0.985)
    if not len(nonwhite[0]):
        return im
    r0, r1 = max(nonwhite[0].min() - margin, 0), min(nonwhite[0].max() + margin, im.shape[0])
    c0, c1 = max(nonwhite[1].min() - margin, 0), min(nonwhite[1].max() + margin, im.shape[1])
    return im[r0:r1, c0:c1]


# --------------------------------------------------------------- 2D sections
def patch(ax, geom, **kw):
    geoms = geom.geoms if isinstance(geom, (MultiPolygon, GeometryCollection)) else [geom]
    for g in geoms:
        if not isinstance(g, Polygon) or g.is_empty:
            continue
        verts, codes = [], []
        for ring in [g.exterior] + list(g.interiors):
            c = np.asarray(ring.coords)
            verts += c.tolist(); codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), **kw))


def lines_of(g):
    if g.is_empty:
        return []
    if g.geom_type in ("LineString", "LinearRing"):
        return [g]
    if hasattr(g, "geoms"):
        return [x for x in g.geoms if x.geom_type in ("LineString", "LinearRing")]
    return []


def interfaces(P):
    """every pair: (a, b, type, measure, anchor xy)."""
    out = []
    names = sorted(P)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pa, pb = P[a], P[b]
            d = pa.distance(pb)
            if d > 1.0:
                continue
            inter = pa.intersection(pb)
            if inter.area > 1e-4:
                why = designed(a, b)
                c = inter.representative_point()
                out.append((a, b, "designed" if why else "OVERLAP", inter.area, (c.x, c.y), why, inter))
                continue
            if d < 0.01:
                cl = pa.boundary.intersection(pb.buffer(0.01))
                segs = [s for s in lines_of(cl) if s.length > 0.02]
                L = sum(s.length for s in segs)
                if L > 0.05:
                    m = max(segs, key=lambda s: s.length).interpolate(0.5, normalized=True)
                    out.append((a, b, "contact", L, (m.x, m.y), None, segs))
                continue
            p1, p2 = nearest_points(pa, pb)
            out.append((a, b, "gap", d, ((p1.x + p2.x) / 2, (p1.y + p2.y) / 2), None, (p1, p2)))
    return out


def draw_section(ax, P, cols, IF, window=None, labels=False):
    for nm, g in sorted(P.items(), key=lambda kv: kind(kv[0]) in ("screw", "insert", "nut")):
        patch(ax, g, facecolor=cols[nm], edgecolor="k", lw=0.25, alpha=1.0, zorder=2)
    for a, b, t, v, xy, why, geo in IF:
        if t in ("OVERLAP", "designed"):
            patch(ax, geo, facecolor="#ff0000" if t == "OVERLAP" else "#ff9900", edgecolor="#7a0000", lw=0.3,
                  hatch="xxxx" if t == "OVERLAP" else "////", zorder=4)
        elif t == "contact":
            for s in geo:
                c = np.asarray(s.coords); ax.plot(c[:, 0], c[:, 1], color="#00c000", lw=1.6, zorder=5, solid_capstyle="butt")
        elif t == "gap":
            p1, p2 = geo
            ax.plot([p1.x, p2.x], [p1.y, p2.y], color="#0050ff", lw=0.8, zorder=5)
            if labels and window is not None:
                ax.annotate("gap %.2f" % v, (xy[0], xy[1]), xytext=(4, 4), textcoords="offset points",
                            fontsize=6.5, color="#0030c0", zorder=6,
                            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="#0030c0", lw=0.4))
    if window is not None:
        ax.set_xlim(window[0], window[1]); ax.set_ylim(window[2], window[3])
    ax.set_aspect("equal")


def joint_pages(pdf, jn, jd, S, cols, meshes_cache, notes=None):
    o, n = np.array(jd["plane"][0], float), np.array(jd["plane"][1], float)
    i0, i1 = AX[jd["axes"][0]], AX[jd["axes"][1]]
    lo, hi = np.array(jd["box"][0]), np.array(jd["box"][1])
    inbox = [k for k, v in S.items() if VF.overlap(VF.bbox(v), np.array([lo, hi]), 0)]
    tag = jn.split()[0]
    # ---- 3D page
    meshes = {k: meshes_cache.setdefault(k, tess(S[k])) for k in inbox}
    fp = (lo + hi) / 2
    up_sec = (0, 0, 1) if i1 == 2 else (0, 1, 0)
    front = np.cross(n, (0, 0, 1)) if abs(n[2]) < 0.9 else np.array([1.0, 0, 0])
    views = [("isometric", (1, -1, 0.8), (0, 0, 1)), ("side (along the cut normal)", tuple(n), up_sec),
             ("front", tuple(front), (0, 0, 1)),
             ("CUT-AWAY through the joint plane", tuple(n), (0, 0, 1) if i1 == 2 else (0, 1, 0))]
    os.makedirs(OUT, exist_ok=True)
    fig = plt.figure(figsize=(16.5, 11.7))
    fig.suptitle("%s -- every part opaque in its own colour, black edges (3D, exact solids)" % jn, fontsize=15, fontweight="bold")
    for i, (lab, d, up) in enumerate(views):
        png = os.path.join(OUT, "%s_%d.png" % (tag, i))
        vtk_render(meshes, cols, png, (fp, np.asarray(d, float) / np.linalg.norm(d), up),
                   clip=((o, -n) if lab.startswith("CUT") else None), size=(2000, 1500))
        ax = fig.add_axes([0.01 + 0.5 * (i % 2), 0.49 - 0.47 * (i // 2), 0.48, 0.44])
        ax.imshow(R5.trimmed(png) if "R5" in globals() else trimmed(png), interpolation="none"); ax.axis("off"); ax.set_title(lab, fontsize=11)
    if notes:
        fig.text(0.02, 0.012, notes, fontsize=8.5, family="monospace", va="bottom")
    pdf.savefig(fig, dpi=300); plt.close(fig)
    # ---- exact section page
    P = {}
    for k in inbox:
        g = section2d(S[k], o, n, i0, i1)
        if g is not None and not g.is_empty and g.area > 1e-4:
            P[k] = g
    IF = interfaces(P)
    fig = plt.figure(figsize=(16.5, 11.7))
    fig.suptitle("%s -- EXACT SECTION (OpenCascade): red = solids intersecting, orange = designed (pinch / thread), "
                 "green = faces touching, blue = gap < 1 mm" % jn, fontsize=11.5, fontweight="bold")
    ax = fig.add_axes([0.04, 0.05, 0.66, 0.88])
    draw_section(ax, P, cols, IF)
    ax.set_xlim(lo[i0], hi[i0]); ax.set_ylim(lo[i1], hi[i1])
    ax.set_xlabel("%s (mm)" % jd["axes"][0]); ax.set_ylabel("%s (mm)" % jd["axes"][1]); ax.grid(alpha=0.15, lw=0.3)
    axl = fig.add_axes([0.72, 0.05, 0.27, 0.88]); axl.axis("off")
    from matplotlib.patches import Patch
    hand = [Patch(facecolor=cols[k], edgecolor="k", lw=0.4, label=k) for k in sorted(P)]
    axl.legend(handles=hand, loc="upper left", fontsize=7.5, frameon=False, ncol=1 if len(hand) < 38 else 2)
    nov = sum(1 for x in IF if x[2] == "OVERLAP")
    axl.text(0.0, 0.0, "in this cut: %d parts, %d touching pairs, %d gaps < 1 mm,\n%d designed overlaps, %d UNDESIGNED OVERLAPS"
             % (len(P), sum(1 for x in IF if x[2] == "contact"), sum(1 for x in IF if x[2] == "gap"),
                sum(1 for x in IF if x[2] == "designed"), nov), fontsize=9, va="bottom",
             color="#b00000" if nov else "#006000", fontweight="bold")
    pdf.savefig(fig); plt.close(fig)
    # ---- zoom panels: overlaps first, then the smallest gaps, then contacts across different parts
    pri = {"OVERLAP": 0, "designed": 1, "gap": 2, "contact": 3}
    chosen, used = [], []
    for x in sorted(IF, key=lambda x: (pri[x[2]], x[3] if x[2] == "gap" else -x[3])):
        if all(np.hypot(x[4][0] - u[0], x[4][1] - u[1]) > 3.0 for u in used):
            chosen.append(x); used.append(x[4])
        if len(chosen) == 12:
            break
    if chosen:
        fig = plt.figure(figsize=(16.5, 11.7))
        fig.suptitle("%s -- interfaces zoomed (+-4 mm): measured on the exact section" % jn, fontsize=13, fontweight="bold")
        for i, (a, b, t, v, xy, why, geo) in enumerate(chosen):
            ax = fig.add_subplot(3, 4, i + 1)
            draw_section(ax, P, cols, IF, window=(xy[0] - 4, xy[0] + 4, xy[1] - 4, xy[1] + 4), labels=True)
            cap = {"OVERLAP": "OVERLAP %.3f mm2" % v, "designed": "designed overlap %.3f mm2\n(%s)" % (v, why),
                   "gap": "gap %.3f mm" % v, "contact": "faces touch over %.2f mm" % v}[t]
            ax.set_title("%s | %s\n%s" % (a, b, cap), fontsize=7.5,
                         color="#b00000" if t == "OVERLAP" else "#000000")
            ax.tick_params(labelsize=6)
        fig.tight_layout(rect=(0, 0, 1, 0.95))
        pdf.savefig(fig); plt.close(fig)
    return IF


def full_arm_page(pdf, S, cols, meshes_cache):
    meshes = {k: meshes_cache.setdefault(k, tess(S[k], 0.05, 0.2)) for k in S}
    fp = np.array([0, 0, 260.0])
    fig = plt.figure(figsize=(16.5, 11.7))
    fig.suptitle("ARM-450 rev I -- whole arm, every part and every screw, opaque", fontsize=15, fontweight="bold")
    for i, (lab, d, up) in enumerate((("isometric", (1, -1, 0.7), (0, 0, 1)), ("side (from -y)", (0, -1, 0), (0, 0, 1)),
                                      ("front (from +x)", (1, 0, 0), (0, 0, 1)),
                                      ("CUT-AWAY at y = 0", (0, -1, 0), (0, 0, 1)))):
        png = os.path.join(OUT, "arm_%d.png" % i)
        vtk_render(meshes, cols, png, (fp, np.asarray(d, float) / np.linalg.norm(d), up),
                   clip=(((0, 0, 0), (0, 1, 0)) if lab.startswith("CUT") else None), size=(1800, 2400))
        ax = fig.add_subplot(1, 4, i + 1); ax.imshow(R5.trimmed(png) if "R5" in globals() else trimmed(png), interpolation="none"); ax.axis("off"); ax.set_title(lab, fontsize=11)
    pdf.savefig(fig, dpi=300); plt.close(fig)


def main():
    from matplotlib.backends.backend_pdf import PdfPages
    S = load()
    cols = colours(S)
    os.makedirs(OUT, exist_ok=True)
    cache = {}
    summary = []
    with PdfPages(os.path.join(OUT, "ARM450_INTERFACES.pdf")) as pdf:
        if len(sys.argv) == 1:
            full_arm_page(pdf, S, cols, cache)
        for jn, jd in JOINTS.items():
            if len(sys.argv) > 1 and not any(jn.startswith(a) for a in sys.argv[1:]):
                continue
            IF = joint_pages(pdf, jn, jd, S, cols, cache)
            nov = [x for x in IF if x[2] == "OVERLAP"]
            summary.append((jn, len(IF), nov))
            print("%-16s interfaces %3d   undesigned overlaps %d %s" % (jn, len(IF), len(nov),
                  "; ".join("%s|%s %.3f" % (x[0], x[1], x[3]) for x in nov)))
    print("written", os.path.join(OUT, "ARM450_INTERFACES.pdf"))
    return sum(len(x[2]) for x in summary)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
