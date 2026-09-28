"""mock adsk.fusion on OpenCascade -- see adsk/__init__.py. Lengths in cm."""
import numpy as np
import cadquery as cq
from OCP.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Transform
from OCP.GC import GC_MakeArcOfCircle
from OCP.GeomAPI import GeomAPI_PointsToBSpline, GeomAPI_ProjectPointOnCurve
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.TopTools import TopTools_HSequenceOfShape, TopTools_IndexedMapOfShape, TopTools_ListOfShape
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet, BRepFilletAPI_MakeChamfer
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRep import BRep_Tool
from OCP.TopExp import TopExp, TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE, TopAbs_SOLID, TopAbs_IN
from OCP.TopoDS import TopoDS
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRepTools import BRepTools
from OCP.BRepClass import BRepClass_FaceClassifier
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.gp import gp_Pnt2d
from . import core


import os
STRICT = os.environ.get("MOCK_STRICT") == "1"


class DesignTypes:
    DirectDesignType, ParametricDesignType = 0, 1


class FeatureOperations:
    JoinFeatureOperation, CutFeatureOperation, IntersectFeatureOperation, NewBodyFeatureOperation, \
        NewComponentFeatureOperation = range(5)


class CalculationAccuracy:
    LowCalculationAccuracy, MediumCalculationAccuracy, HighCalculationAccuracy, VeryHighCalculationAccuracy = range(4)


class DistanceUnits:
    MillimeterDistanceUnits, CentimeterDistanceUnits = 0, 1


class OffsetStartDefinition:
    def __init__(self, v):
        self.offset = v

    @staticmethod
    def create(v):
        return OffsetStartDefinition(v)


def _coll(items):
    c = core.ObjectCollection.create()
    for i in items:
        c.add(i)
    return c


def _solids(shape):
    out, ex = [], TopExp_Explorer(shape, TopAbs_SOLID)
    while ex.More():
        out.append(ex.Current()); ex.Next()
    return out


def _merge(shape):
    """Fusion's kernel keeps faces that lie on one surface as one face after
    a combine (no seam lines on a flush join); OCC leaves them split until
    ShapeUpgrade_UnifySameDomain -- the same clean() CadQuery runs."""
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
    u = ShapeUpgrade_UnifySameDomain(shape, True, True, True)
    u.AllowInternalEdges(False)
    u.Build()
    return _solids(u.Shape())[0]


def _vol(shape):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(shape, g, 1e-11, False)
    return g.Mass(), g.CentreOfMass()


# ------------------------------------------------------------- design
class _Group:
    name = ""


class _TimelineGroups:
    def __init__(self, tl):
        self.tl = tl

    def add(self, a, b):
        if not (0 <= a <= b < self.tl.count):
            raise RuntimeError("timeline group %d..%d outside 0..%d" % (a, b, self.tl.count - 1))
        g = _Group(); self.tl.groups.append((a, b, g))
        return g


class _Timeline:
    def __init__(self):
        self.count, self.groups = 0, []
        self.timelineGroups = _TimelineGroups(self)


class _Units:
    distanceDisplayUnits = None


class _ExportManager:
    def __init__(self, d):
        self.d = d

    def createFusionArchiveExportOptions(self, path):
        return {"f3d": path}

    def execute(self, opts):
        self.d.exported = opts["f3d"]            # the mock writes no file
        return True


class Design:
    def __init__(self):
        self.designType = DesignTypes.DirectDesignType
        self.timeline = _Timeline()
        self.rootComponent = Component(self)
        self.exportManager = _ExportManager(self)
        self.fusionUnitsManager = _Units()
        self.exported = None
        self.warnings = []

    @staticmethod
    def cast(x):
        return x

    def tick(self):
        if self.designType != DesignTypes.ParametricDesignType:
            raise RuntimeError("not a parametric design: no timeline")
        self.timeline.count += 1


class _Plane:
    def __init__(self, z):
        self.z, self.isLightBulbOn = z, True


class _PlaneInput:
    def setByOffset(self, plane, v):
        self.z = plane.z + v.realValue
        return True


class _Planes:
    def __init__(self, d):
        self.d = d

    def createInput(self):
        return _PlaneInput()

    def add(self, inp):
        self.d.tick()
        return _Plane(inp.z)


class Component:
    def __init__(self, d):
        self.d = d
        self.xYConstructionPlane = _Plane(0.0)
        self.constructionPlanes = _Planes(d)
        self.sketches = _Sketches(d)
        self.features = Features(d, self)
        self.bodies = []

    @property
    def bRepBodies(self):
        return _coll(self.bodies)


# ------------------------------------------------------------- sketches
class _Sketches:
    def __init__(self, d):
        self.d = d

    def add(self, plane):
        self.d.tick()
        return Sketch(plane.z)


class SketchPoint:
    def __init__(self, g):
        self.geometry = g


def _sp(p):
    return p if isinstance(p, SketchPoint) else SketchPoint(p)


class _Curve:
    pass


class _Lines:
    def __init__(self, sk):
        self.sk = sk

    def addByTwoPoints(self, a, b):
        c = _Curve(); c.kind = "L"
        c.startSketchPoint, c.endSketchPoint = _sp(a), _sp(b)
        self.sk.curves.append(c)
        return c


class _Circles:
    def __init__(self, sk):
        self.sk = sk

    def addByCenterRadius(self, c0, r):
        c = _Curve(); c.kind = "C"; c.center, c.r = c0, r
        c.startSketchPoint = c.endSketchPoint = None
        self.sk.curves.append(c)
        return c


class _Arcs:
    def __init__(self, sk):
        self.sk = sk

    def addByThreePoints(self, a, m, b):
        a, b = _sp(a), _sp(b)
        c = _Curve(); c.kind = "A"; c.mid = m
        pa, pb = a.geometry, b.geometry
        cross = (m.x - pa.x) * (pb.y - pa.y) - (m.y - pa.y) * (pb.x - pa.x)
        # Fusion arcs run counter-clockwise from start to end: a clockwise
        # three-point arc comes back with its ends swapped
        c.startSketchPoint, c.endSketchPoint = (a, b) if cross < 0 else (b, a)
        c.a, c.b = a, b
        self.sk.curves.append(c)
        return c


class _Splines:
    def __init__(self, sk):
        self.sk = sk

    def add(self, pts):
        c = _Curve(); c.kind = "S"; c.pts = [p.geometry if isinstance(p, SketchPoint) else p for p in pts]
        c.startSketchPoint, c.endSketchPoint = SketchPoint(c.pts[0]), SketchPoint(c.pts[-1])
        self.sk.curves.append(c)
        return c


class _SketchCurves:
    def __init__(self, sk):
        self.sketchLines, self.sketchCircles = _Lines(sk), _Circles(sk)
        self.sketchArcs, self.sketchFittedSplines = _Arcs(sk), _Splines(sk)


class _AreaProps:
    def __init__(self, face):
        g = GProp_GProps(); BRepGProp.SurfaceProperties_s(face, g)
        self.area = g.Mass()
        c = g.CentreOfMass()
        self.centroid = core.Point3D(c.X(), c.Y(), c.Z())


class Profile:
    def __init__(self, face, nloops):
        self.face = face
        self.profileLoops = _coll([None] * nloops)

    def areaProperties(self, acc=None):
        return _AreaProps(self.face)


class Sketch:
    def __init__(self, z):
        self.z, self.curves, self.name, self.isComputeDeferred = z, [], "", False
        self.sketchCurves = _SketchCurves(self)

    def modelToSketchSpace(self, p):
        return core.Point3D(p.x, p.y, p.z - self.z)

    def _g(self, p):
        return gp_Pnt(p.x, p.y, p.z + self.z)

    def _edges(self):
        out = []
        for c in self.curves:
            if c.kind == "L":
                out.append(BRepBuilderAPI_MakeEdge(self._g(c.startSketchPoint.geometry),
                                                   self._g(c.endSketchPoint.geometry)).Edge())
            elif c.kind == "C":
                ci = gp_Circ(gp_Ax2(self._g(c.center), gp_Dir(0, 0, 1)), c.r)
                out.append(BRepBuilderAPI_MakeEdge(ci).Edge())
            elif c.kind == "A":
                arc = GC_MakeArcOfCircle(self._g(c.a.geometry), self._g(c.mid), self._g(c.b.geometry)).Value()
                out.append(BRepBuilderAPI_MakeEdge(arc).Edge())
            else:
                arr = TColgp_Array1OfPnt(1, len(c.pts))
                for i, p in enumerate(c.pts, 1):
                    arr.SetValue(i, self._g(p))
                out.append(BRepBuilderAPI_MakeEdge(GeomAPI_PointsToBSpline(arr).Curve()).Edge())
        return out

    @property
    def profiles(self):
        """every closed region: a loop minus the loops directly inside it."""
        if self.isComputeDeferred:
            raise RuntimeError("profiles read while the sketch compute is deferred")
        seq = TopTools_HSequenceOfShape()
        for e in self._edges():
            seq.Append(e)
        wires = TopTools_HSequenceOfShape()
        ShapeAnalysis_FreeBounds.ConnectEdgesToWires_s(seq, 1e-7, False, wires)
        W = [TopoDS.Wire_s(wires.Value(i)) for i in range(1, wires.Length() + 1)]
        faces = [BRepBuilderAPI_MakeFace(w, True).Face() for w in W]
        areas = [_AreaProps(f).area for f in faces]
        for w in W:
            if not BRep_Tool.IsClosed_s(w) and not w.Closed():
                raise RuntimeError("open sketch loop")

        def inside(i, j):                     # loop i inside loop j
            if areas[i] >= areas[j]:
                return False
            ex = TopExp_Explorer(W[i], TopAbs_EDGE)
            c = BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current()))
            p = c.Value((c.FirstParameter() + c.LastParameter()) / 2)
            u, v = p.X(), p.Y()
            cl = BRepClass_FaceClassifier(faces[j], gp_Pnt(u, v, p.Z()), 1e-7)
            return cl.State() == TopAbs_IN
        parent = []
        for i in range(len(W)):
            cands = [j for j in range(len(W)) if j != i and inside(i, j)]
            parent.append(min(cands, key=lambda j: areas[j]) if cands else None)
        out = []
        for j in range(len(W)):
            kids = [i for i in range(len(W)) if parent[i] == j]
            f = cq.Face.makeFromWires(cq.Wire(W[j]), [cq.Wire(W[i]) for i in kids]).wrapped
            out.append(Profile(f, 1 + len(kids)))
        return _coll(out)


# ------------------------------------------------------------- bodies
class _Evaluator:
    def __init__(self, edge):
        self.c = BRepAdaptor_Curve(edge)
        self.edge = edge

    def getParameterExtents(self):
        return True, self.c.FirstParameter(), self.c.LastParameter()

    def getPointAtParameter(self, t):
        p = self.c.Value(t)
        return True, core.Point3D(p.X(), p.Y(), p.Z())

    def getParameterAtPoint(self, p):
        """nearest parameter: coarse samples, then golden-section refinement."""
        t0, t1 = self.c.FirstParameter(), self.c.LastParameter()
        q = np.array([p.x, p.y, p.z])
        d = lambda t: np.linalg.norm(np.array(self.c.Value(t).Coord()) - q)
        ts = np.linspace(t0, t1, 201)
        i = int(np.argmin([d(t) for t in ts]))
        a, b = ts[max(i - 1, 0)], ts[min(i + 1, 200)]
        g = (np.sqrt(5) - 1) / 2
        for _ in range(60):
            c1, c2 = b - g * (b - a), a + g * (b - a)
            if d(c1) < d(c2):
                b = c2
            else:
                a = c1
        return True, (a + b) / 2


class BRepEdge:
    def __init__(self, e, body):
        self.topo, self.body = e, body
        self.evaluator = _Evaluator(e)


class _Phys:
    def __init__(self, body):
        v, c = _vol(body.shape)
        self.centerOfMass = core.Point3D(c.X(), c.Y(), c.Z())
        self.volume = v


class _BB:
    def __init__(self, shape):
        b = Bnd_Box(); BRepBndLib.AddOptimal_s(shape, b, False, False)
        x0, y0, z0, x1, y1, z1 = b.Get()
        self.minPoint, self.maxPoint = core.Point3D(x0, y0, z0), core.Point3D(x1, y1, z1)


class BRepBody:
    def __init__(self, shape, comp):
        self.shape, self.comp, self.name, self.isLightBulbOn = shape, comp, "", True
        comp.bodies.append(self)
        if len(_solids(shape)) != 1:
            raise RuntimeError("a body must be one solid, got %d" % len(_solids(shape)))

    @property
    def alive(self):
        return self in self.comp.bodies

    @property
    def volume(self):
        return _vol(self.shape)[0]

    @property
    def physicalProperties(self):
        return _Phys(self)

    def getPhysicalProperties(self, accuracy=None):
        return _Phys(self)

    @property
    def boundingBox(self):
        return _BB(self.shape)

    @property
    def edges(self):
        m = TopTools_IndexedMapOfShape()
        TopExp.MapShapes_s(self.shape, TopAbs_EDGE, m)
        return _coll([BRepEdge(TopoDS.Edge_s(m.FindKey(i)), self) for i in range(1, m.Extent() + 1)])


def _need(body):
    if not body.alive:
        raise RuntimeError("body '%s' was already consumed or removed" % body.name)


# ------------------------------------------------------------- features
class _Feature:
    def __init__(self, bodies):
        self.bodies, self.name = _coll(bodies), ""


class _ExtInput:
    def __init__(self, prof, op):
        self.profile, self.op, self.h, self.startExtent = prof, op, None, None

    def setDistanceExtent(self, sym, v):
        if sym:
            raise RuntimeError("mock: symmetric extent not used")
        self.h = v.realValue
        return True


class _Extrudes:
    def __init__(self, d, comp):
        self.d, self.comp = d, comp

    def createInput(self, prof, op):
        return _ExtInput(prof, op)

    def add(self, inp):
        if inp.op != FeatureOperations.NewBodyFeatureOperation or inp.h is None or inp.h <= 0:
            raise RuntimeError("mock extrude: new body with a positive distance only")
        f = inp.profile.face
        if inp.startExtent is not None:
            t = gp_Trsf(); t.SetTranslation(gp_Vec(0, 0, inp.startExtent.offset.realValue))
            f = BRepBuilderAPI_Transform(f, t, True).Shape()
        s = BRepPrimAPI_MakePrism(f, gp_Vec(0, 0, inp.h), True).Shape()
        self.d.tick()
        return _Feature([BRepBody(_solids(s)[0], self.comp)])


class _Sections:
    def __init__(self):
        self.items = []

    def add(self, p):
        self.items.append(p)
        return p


class _LoftInput:
    def __init__(self, op):
        self.op, self.loftSections, self.isSolid = op, _Sections(), False


class _Lofts:
    def __init__(self, d, comp):
        self.d, self.comp = d, comp

    def createInput(self, op):
        return _LoftInput(op)

    def add(self, inp):
        ts = BRepOffsetAPI_ThruSections(inp.isSolid, False)
        for p in inp.loftSections.items:
            ts.AddWire(BRepTools.OuterWire_s(TopoDS.Face_s(p.face)))
        ts.Build()
        self.d.tick()
        return _Feature([BRepBody(_solids(ts.Shape())[0], self.comp)])


class _MoveInput:
    def __init__(self, bodies, m=None):
        self.bodies, self.m = list(bodies), m

    def defineAsFreeMove(self, m):
        self.m = m
        return True


class _Moves:
    def __init__(self, d):
        self.d = d

    def createInput2(self, coll):
        return _MoveInput(coll)

    def add(self, inp):
        M = inp.m.m
        t = gp_Trsf()
        t.SetValues(*[M[i, j] for i in range(3) for j in range(4)])
        for b in inp.bodies:
            _need(b)
            b.shape = BRepBuilderAPI_Transform(b.shape, t, True).Shape()
        self.d.tick()
        return _Feature(inp.bodies)


class _CombInput:
    def __init__(self, target, tools):
        self.target, self.tools = target, list(tools)
        self.operation, self.isKeepToolBodies, self.isNewComponent = None, False, False


class _Combines:
    def __init__(self, d, comp):
        self.d, self.comp = d, comp

    def createInput(self, target, tools):
        return _CombInput(target, tools)

    def add(self, inp):
        _need(inp.target)
        for t in inp.tools:
            _need(t)
            if t is inp.target:
                raise RuntimeError("a body cannot be its own tool")
        FO = FeatureOperations
        if STRICT:
            # the stricter reading of Fusion: a cut / intersect tool must meet
            # its target, a join tool must at least touch it
            from OCP.BRepExtrema import BRepExtrema_DistShapeShape
            for b in inp.tools:
                if inp.operation == FO.JoinFeatureOperation:
                    if BRepExtrema_DistShapeShape(inp.target.shape, b.shape).Value() > 1e-7:
                        raise RuntimeError("join: the bodies do not touch")
                elif _vol(BRepAlgoAPI_Common(inp.target.shape, b.shape).Shape())[0] < 1e-9:
                    raise RuntimeError("the tool body does not intersect the target")
        op = {FO.JoinFeatureOperation: BRepAlgoAPI_Fuse, FO.CutFeatureOperation: BRepAlgoAPI_Cut,
              FO.IntersectFeatureOperation: BRepAlgoAPI_Common}[inp.operation]()
        a, t = TopTools_ListOfShape(), TopTools_ListOfShape()
        a.Append(inp.target.shape)
        for b in inp.tools:
            t.Append(b.shape)
        op.SetArguments(a); op.SetTools(t); op.Build()
        if not op.IsDone():
            raise RuntimeError("combine failed")
        sols = _solids(op.Shape())
        if not sols:
            raise RuntimeError("combine left nothing")
        if inp.operation != FO.JoinFeatureOperation:
            for b in inp.tools:
                cm = BRepAlgoAPI_Common(inp.target.shape, b.shape).Shape()
                if _vol(cm)[0] < 1e-9:
                    self.d.warnings.append("combine tool does not touch its target")
        sols = [_merge(x) for x in sols]
        inp.target.shape = sols[0]
        out = [inp.target] + [BRepBody(s, self.comp) for s in sols[1:]]
        if not inp.isKeepToolBodies:
            for b in inp.tools:
                self.comp.bodies.remove(b)
        self.d.tick()
        return _Feature(out)


class _EdgeSets:
    def __init__(self):
        self.sets = []

    def addConstantRadiusEdgeSet(self, edges, v, chain):
        self.sets.append((list(edges), v.realValue))
        return True

    def addEqualDistanceChamferEdgeSet(self, edges, v, chain):
        self.sets.append((list(edges), v.realValue))
        return True


class _FilletInput:
    def __init__(self):
        self.edgeSetInputs, self.isRollingBallCorner = _EdgeSets(), False


class _ChamferInput:
    def __init__(self):
        self.chamferEdgeSets = _EdgeSets()


def _round(d, sets, builder, add):
    by_body = {}
    for edges, r in sets:
        for e in edges:
            by_body.setdefault(id(e.body), (e.body, []))[1].append((e, r))
    out = []
    for body, lst in by_body.values():
        _need(body)
        mk = builder(body.shape)
        for e, r in lst:
            add(mk, r, e.topo)
        mk.Build()
        if not mk.IsDone():
            raise RuntimeError("fillet / chamfer failed")
        body.shape = _solids(mk.Shape())[0]
        out.append(body)
    d.tick()
    return _Feature(out)


class _Fillets:
    def __init__(self, d):
        self.d = d

    def createInput(self):
        return _FilletInput()

    def add(self, inp):
        return _round(self.d, inp.edgeSetInputs.sets, BRepFilletAPI_MakeFillet, lambda mk, r, e: mk.Add(r, e))


class _Chamfers:
    def __init__(self, d):
        self.d = d

    def createInput2(self):
        return _ChamferInput()

    def add(self, inp):
        return _round(self.d, inp.chamferEdgeSets.sets, BRepFilletAPI_MakeChamfer, lambda mk, r, e: mk.Add(r, e))


class _Removes:
    def __init__(self, d, comp):
        self.d, self.comp = d, comp

    def add(self, body):
        _need(body)
        self.comp.bodies.remove(body)
        self.d.tick()
        return _Feature([])


class Features:
    def __init__(self, d, comp):
        self.extrudeFeatures, self.loftFeatures = _Extrudes(d, comp), _Lofts(d, comp)
        self.moveFeatures, self.combineFeatures = _Moves(d), _Combines(d, comp)
        self.filletFeatures, self.chamferFeatures = _Fillets(d), _Chamfers(d)
        self.removeFeatures = _Removes(d, comp)
