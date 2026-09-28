#!/usr/bin/env python3
"""
Record what the ARM-450 generators do in CadQuery as a feature tree.

Every solid the generators make is born in one of a few CadQuery calls
(extrude a face, loft two wires, box, cylinder) and then changed by booleans
(fuse / cut / common), fillets, chamfers and rigid moves. This module hooks
those calls and keeps, for every solid, HOW it was made:

    extrude  -- the face's loops (lines, circles, arcs; world mm) + the vector
    loft     -- the section wires
    fuse / cut / common -- the operand solids
    fillet / chamfer    -- radius + the selected edges (geometry)
    xform    -- a 4x4 rigid move / mirror of another solid
    sub      -- one solid picked out of a multi-solid result
    compound -- several solids held together
    import   -- a STEP file read from disk

make_trees.py turns that into a Fusion 360 timeline. Nothing here changes a
result: every hook calls the original CadQuery code and returns its answer.
"""
import os
import sys

import numpy as np
import cadquery as cq
from cadquery.occ_impl import shapes as S
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomAbs import GeomAbs_Line, GeomAbs_Circle
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_COMPOUND, TopAbs_WIRE
from OCP.TopoDS import TopoDS_Iterator, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.gp import gp_Ax2

NODES = []           # one dict per recorded solid-making step
EXPORTS = {}         # STEP basename (no extension) -> node id of what was written
_REG = {}            # hash(TopoDS) -> [(TopoDS copy, node id)]
_THIS = os.path.abspath(__file__)
_SKIP = ("site-packages", "/cadquery/", "multimethod", _THIS, "<frozen")


class Unsupported(Exception):
    pass


# ------------------------------------------------------------------ helpers
def _src():
    """file:function:line of the generator code that asked for this step."""
    f = sys._getframe(2)
    while f is not None:
        fn = f.f_code.co_filename
        if not any(s in fn for s in _SKIP):
            return "%s:%s:%d" % (os.path.basename(fn), f.f_code.co_name, f.f_lineno)
        f = f.f_back
    return "?"


def _topo(sh):
    return sh.wrapped if hasattr(sh, "wrapped") else sh


_MULTI = []          # (TopoDS copy, node id) of every registered non-solid (compounds): searched for sub-solids


def _reg(topo, nid):
    c = topo.Located(topo.Location())
    _REG.setdefault(hash(topo), []).append((c, nid))
    if topo.ShapeType() != TopAbs_SOLID:
        _MULTI.append((c, nid))
    return nid


def _find(topo):
    for t, nid in reversed(_REG.get(hash(topo), [])):
        if t.IsSame(topo):
            return nid
    return None


def _new(kind, topo, kids=(), **data):
    nid = len(NODES)
    NODES.append(dict(id=nid, kind=kind, kids=list(kids), data=data, src=_src(), topo=topo.Located(topo.Location())))
    return _reg(topo, nid)


def _props(topo):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(topo, g)
    c = g.CentreOfMass()
    return float(g.Mass()), [c.X(), c.Y(), c.Z()]


def _solids(topo):
    out, ex = [], TopExp_Explorer(topo, TopAbs_SOLID)
    while ex.More():
        out.append(ex.Current()); ex.Next()
    return out


def node_of(sh):
    """the node that made this solid (or compound of solids)."""
    topo = _topo(sh)
    nid = _find(topo)
    if nid is not None:
        return nid
    if topo.ShapeType() == TopAbs_COMPOUND:
        kids, it = [], TopoDS_Iterator(topo)
        while it.More():
            kids.append(node_of(it.Value())); it.Next()
        return _new("compound", topo, kids)
    if topo.ShapeType() == TopAbs_SOLID:
        for t, nid in reversed(_MULTI[-800:]):
            sols = _solids(t)
            for i, s in enumerate(sols):
                if s.IsSame(topo):
                    if len(sols) == 1:                  # the only solid of a compound result: same thing
                        return _reg(topo, nid)
                    v, c = _props(topo)
                    return _new("sub", topo, [nid], index=i, volume=v, centroid=c)
    raise KeyError("solid with no recorded history")


def edge_data(e):
    """one edge as geometry: line (2 points), circle (centre, radius, normal)
    or arc (3 points) -- world mm, location applied."""
    c = BRepAdaptor_Curve(TopoDS.Edge_s(_topo(e)))
    t0, t1 = c.FirstParameter(), c.LastParameter()
    P = lambda t: [c.Value(t).X(), c.Value(t).Y(), c.Value(t).Z()]
    typ = c.GetType()
    if typ == GeomAbs_Line:
        return dict(t="line", p=[P(t0), P(t1)])
    if typ == GeomAbs_Circle:
        ci = c.Circle(); ax = ci.Axis()
        cen = [ci.Location().X(), ci.Location().Y(), ci.Location().Z()]
        n = [ax.Direction().X(), ax.Direction().Y(), ax.Direction().Z()]
        if abs((t1 - t0) - 2 * np.pi) < 1e-9:
            return dict(t="circle", c=cen, r=ci.Radius(), n=n)
        return dict(t="arc", p=[P(t0), P((t0 + t1) / 2), P(t1)], c=cen, r=ci.Radius(), n=n)
    return dict(t="curve", p=[P(t0 + (t1 - t0) * k / 48.0) for k in range(49)], gtype=int(typ))


def wire_data(w):
    from OCP.BRepTools import BRepTools_WireExplorer
    out = []
    we = BRepTools_WireExplorer(TopoDS.Wire_s(_topo(w)))
    while we.More():
        out.append(edge_data(we.Current())); we.Next()
    return out


def _mat(trsf):
    return [[trsf.Value(i, j) for j in range(1, 5)] for i in range(1, 4)] + [[0.0, 0.0, 0.0, 1.0]]


def _loc_mat(loc):
    return np.array(_mat(loc.Transformation()))


# -------------------------------------------------------------------- hooks
_orig = {}


def _hook(owner, name, make):
    _orig[(owner, name)] = getattr(owner, name)
    setattr(owner, name, make(_orig[(owner, name)]))


def _extrude(orig):
    def f(cls, *a, **k):
        r = orig(*a, **k)
        if isinstance(a[0], S.Face):
            face, vec = a[0], cq.Vector(a[1] if len(a) > 1 else k["vecNormal"])
            taper = a[2] if len(a) > 2 else k.get("taper", 0)
            if taper:
                raise Unsupported("tapered extrude at %s" % _src())
            _new("extrude", r.wrapped, loops=_face_loops(face), vec=list(vec.toTuple()), area=face.Area())
        return r
    return classmethod(f)


def _loft(orig):
    def f(cls, listOfWire, ruled=False, *a, **k):
        r = orig(listOfWire, ruled, *a, **k)
        _new("loft", r.wrapped, sections=[wire_data(w) for w in listOfWire], ruled=bool(ruled))
        return r
    return classmethod(f)


def _loft_free(orig):
    """cq.Workplane.loft -> shapes.loft(wires, cap=True, ruled=...)"""
    def f(sections, *a, **k):
        r = orig(sections, *a, **k)
        if not k.get("cap", False):
            raise Unsupported("uncapped loft at %s" % _src())
        _new("loft", r.wrapped, sections=[wire_data(w) for w in sections], ruled=bool(k.get("ruled", False)))
        return r
    return f


def _box(orig):
    def f(cls, length, width, height, pnt=cq.Vector(0, 0, 0), dir=cq.Vector(0, 0, 1), *a, **k):
        r = orig(length, width, height, pnt, dir, *a, **k)
        ax = gp_Ax2(cq.Vector(pnt).toPnt(), cq.Vector(dir).toDir())
        X = np.array([ax.XDirection().X(), ax.XDirection().Y(), ax.XDirection().Z()])
        Y = np.array([ax.YDirection().X(), ax.YDirection().Y(), ax.YDirection().Z()])
        p0 = np.array(cq.Vector(pnt).toTuple())
        c = [p0, p0 + length * X, p0 + length * X + width * Y, p0 + width * Y]
        loop = [dict(t="line", p=[list(c[i]), list(c[(i + 1) % 4])]) for i in range(4)]
        vec = np.array(cq.Vector(dir).normalized().toTuple()) * height
        _new("extrude", r.wrapped, loops=[loop], vec=list(vec), area=length * width)
        return r
    return classmethod(f)


def _cyl(orig):
    def f(cls, radius, height, pnt=cq.Vector(0, 0, 0), dir=cq.Vector(0, 0, 1), angleDegrees=360, *a, **k):
        r = orig(radius, height, pnt, dir, angleDegrees, *a, **k)
        if abs(angleDegrees - 360) > 1e-9:
            raise Unsupported("partial cylinder at %s" % _src())
        d = np.array(cq.Vector(dir).normalized().toTuple())
        loop = [dict(t="circle", c=list(cq.Vector(pnt).toTuple()), r=radius, n=list(d))]
        _new("extrude", r.wrapped, loops=[loop], vec=list(d * height), area=np.pi * radius ** 2)
        return r
    return classmethod(f)


def _unsupported(what):
    def make(orig):
        def f(*a, **k):
            raise Unsupported("%s at %s" % (what, _src()))
        return f
    return make


def _bool(orig):
    def f(self, args, tools, op, *a, **k):
        args, tools = list(args), list(tools)
        r = orig(self, args, tools, op, *a, **k)
        kind = ("fuse" if isinstance(op, BRepAlgoAPI_Fuse) else "cut" if isinstance(op, BRepAlgoAPI_Cut)
                else "common" if isinstance(op, BRepAlgoAPI_Common) else None)
        if kind is None:
            raise Unsupported("boolean %s at %s" % (type(op).__name__, _src()))
        na = [node_of(x) for x in args]
        nt = [node_of(x) for x in tools]
        _new(kind, r.wrapped, na + nt, nargs=len(na), fuzzy=float(op.FuzzyValue()))
        return r
    return f


def _alias(orig):
    def f(self, *a, **k):
        r = orig(self, *a, **k)
        if r is not self:
            try:
                _reg(r.wrapped, node_of(self))
            except KeyError:
                pass
        return r
    return f


def _xform(get_T):
    def make(orig):
        def f(self, *a, **k):
            r = orig(self, *a, **k)
            try:
                nid = node_of(self)
            except KeyError:
                return r                                  # a wire / face being placed: not a solid
            _new("xform", r.wrapped, [nid], M=get_T(self, r, *a, **k))
            return r
        return f
    return make


def _moved(orig):
    """moved / located (same TShape, new location): T = L_new * L_old^-1;
    moved() with several locations returns a compound of copies."""
    def f(self, *a, **k):
        r = orig(self, *a, **k)
        try:
            nid = node_of(self)
        except KeyError:
            return r
        L0 = _loc_mat(self.wrapped.Location())
        topo = r.wrapped
        if topo.ShapeType() == TopAbs_COMPOUND and self.wrapped.ShapeType() != TopAbs_COMPOUND:
            kids, it = [], TopoDS_Iterator(topo)
            while it.More():
                c = it.Value()
                kids.append(_new("xform", c, [nid], M=(_loc_mat(c.Location()) @ np.linalg.inv(L0)).tolist()))
                it.Next()
            _new("compound", topo, kids)
        else:
            _new("xform", topo, [nid], M=(_loc_mat(topo.Location()) @ np.linalg.inv(L0)).tolist())
        return r
    return f


def _inplace(orig):
    """move / locate change self: register self's new placement."""
    def f(self, *a, **k):
        try:
            nid = node_of(self)
        except KeyError:
            nid = None
        L0 = _loc_mat(self.wrapped.Location())
        r = orig(self, *a, **k)
        if nid is not None:
            _new("xform", self.wrapped, [nid], M=(_loc_mat(self.wrapped.Location()) @ np.linalg.inv(L0)).tolist())
        return r
    return f


def _fillet(orig):
    def f(self, radius, edgeList, *a, **k):
        edges = list(edgeList)
        r = orig(self, radius, edges, *a, **k)
        _new("fillet", r.wrapped, [node_of(self)], r_mm=float(radius), edges=[edge_data(e) for e in edges])
        return r
    return f


def _chamfer(orig):
    def f(self, length, length2, edgeList, *a, **k):
        edges = list(edgeList)
        r = orig(self, length, length2, edges, *a, **k)
        if length2 is not None and abs(length2 - length) > 1e-12:
            raise Unsupported("unequal chamfer at %s" % _src())
        _new("chamfer", r.wrapped, [node_of(self)], d_mm=float(length), edges=[edge_data(e) for e in edges])
        return r
    return f


def _face_loops(face):
    outer = BRepTools.OuterWire_s(face.wrapped)
    loops, ex = [wire_data(outer)], TopExp_Explorer(face.wrapped, TopAbs_WIRE)
    while ex.More():
        if not ex.Current().IsSame(outer):
            loops.append(wire_data(ex.Current()))
        ex.Next()
    return loops


def _dprism(orig):
    """cutThruAll / BRepFeat_MakeDPrism: recorded as a boolean with a prism
    through everything (both normal directions), checked against the real
    result right here."""
    def f(self, basis, profiles, depth=None, taper=0, upToFace=None, thruAll=True, additive=True):
        r = orig(self, basis, profiles, depth, taper, upToFace, thruAll, additive)
        if basis is not None or taper or upToFace is not None or not (thruAll or depth is None):
            raise Unsupported("dprism (%s) at %s" % ("blind" if depth else "basis/taper/upTo", _src()))
        profiles = list(profiles)
        if profiles and isinstance(profiles[0], S.Wire):
            faces = [S.Face.makeFromWires(p[0], p[1:]) for p in S.sortWiresByBuildOrder(profiles)]
        else:
            faces = profiles
        bb = self.BoundingBox()
        L = 2.0 * (bb.DiagonalLength + max(abs(bb.xmin), abs(bb.xmax), abs(bb.ymin), abs(bb.ymax),
                                           abs(bb.zmin), abs(bb.zmax))) + 10.0
        from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
        base = node_of(self)
        tools, cur = [], self.wrapped
        for fc in faces:
            n = fc.normalAt()
            f0 = fc.translate(n * (-L))
            vec = n * (2 * L)
            pr = BRepPrimAPI_MakePrism(f0.wrapped, vec.wrapped, True).Shape()
            tools.append(_new("extrude", pr, loops=_face_loops(f0), vec=list(vec.toTuple()), area=fc.Area()))
            op = BRepAlgoAPI_Fuse(cur, pr) if additive else BRepAlgoAPI_Cut(cur, pr)
            cur = op.Shape()
        v_real, v_emul = _props(r.wrapped)[0], _props(cur)[0]
        if abs(v_real - v_emul) > 1e-6 * max(v_real, 1.0) + 1e-6:
            raise Unsupported("dprism emulation off by %.4f mm3 at %s" % (v_real - v_emul, _src()))
        _new("fuse" if additive else "cut", r.wrapped, [base] + tools, nargs=1, fuzzy=0.0)
        return r
    return f


def _import_step(orig):
    def f(fileName, *a, **k):
        w = orig(fileName, *a, **k)
        for v in w.vals():
            if isinstance(v, S.Shape):
                _new("import", v.wrapped, path=os.path.abspath(fileName))
        return w
    return f


def _export(orig):
    def f(w, fname, *a, **k):
        r = orig(w, fname, *a, **k)
        if str(fname).lower().endswith((".step", ".stp")):
            vals = w.vals() if isinstance(w, cq.Workplane) else [w]
            vals = [v for v in vals if isinstance(v, S.Shape)]
            nid = node_of(vals[0]) if len(vals) == 1 else _new("compound", S.Compound.makeCompound(vals).wrapped,
                                                                [node_of(v) for v in vals])
            EXPORTS[os.path.splitext(os.path.basename(fname))[0]] = nid
        return r
    return f


def install():
    _hook(S.Solid, "extrudeLinear", _extrude)
    _hook(S.Solid, "makeLoft", _loft)
    import cadquery.cq as CQ
    _hook(CQ, "loft", _loft_free)
    _hook(S.Solid, "makeBox", _box)
    _hook(S.Solid, "makeCylinder", _cyl)
    for nm in ("makeCone", "makeSphere", "makeTorus", "makeWedge", "revolve", "sweep", "sweep_multi",
               "extrudeLinearWithRotation"):
        if hasattr(S.Solid, nm):
            _hook(S.Solid, nm, _unsupported("Solid." + nm))
    _hook(cq.Workplane, "shell", _unsupported("Workplane.shell"))
    _hook(S.Shape, "split", _unsupported("split"))
    _hook(S.Shape, "transformGeometry", _unsupported("transformGeometry"))
    _hook(S.Shape, "_bool_op", _bool)
    _hook(S.Mixin3D, "fillet", _fillet)
    _hook(S.Mixin3D, "chamfer", _chamfer)
    _hook(S.Mixin3D, "dprism", _dprism)
    _hook(S.Shape, "_apply_transform", _xform(lambda self, r, Tr: _mat(Tr)))
    _hook(S.Shape, "transformShape", _xform(lambda self, r, m: _mat(m.wrapped.Trsf())))
    _hook(S.Shape, "moved", _moved)
    _hook(S.Shape, "located", _moved)
    _hook(S.Shape, "move", _inplace)
    _hook(S.Shape, "locate", _inplace)
    for nm in ("clean", "fix", "copy"):
        _hook(S.Shape, nm, _alias)
    _hook(cq.importers, "importStep", _import_step)
    _hook(cq.exporters, "export", _export)


def props(topo):
    return _props(topo)
