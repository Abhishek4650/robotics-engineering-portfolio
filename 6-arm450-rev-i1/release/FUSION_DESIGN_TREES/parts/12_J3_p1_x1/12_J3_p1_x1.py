"""
ARM-450 rev I -- J3_p1  (print 1)  --  Fusion 360 DESIGN-TREE script

WHAT IT DOES
  Builds this part in a NEW Fusion design as a parametric timeline --
  135 features: 65 combine, 67 extrude, 1 fillet, 2 loft --
  the same sketches, extrudes, lofts, cuts, joins, fillets and chamfers the
  ARM-450 generator made it with, in the same order, each named after the
  generator line it came from (hover a timeline item to see it). Then it
  checks the result against the released part (volume and bounding box) and
  saves  12_J3_p1_x1.f3d  and  12_J3_p1_x1_BUILD_REPORT.txt  in this folder.

RUN IT
  Fusion 360 > UTILITIES > ADD-INS > Scripts and Add-Ins (Shift+S) >
  Scripts tab > the green "+" > pick THIS folder > select 12_J3_p1_x1 > Run.
  (Or run ../../00_BUILD_ALL_f3d once to make every part's .f3d.)

EDIT IT
  Open 12_J3_p1_x1.f3d (File > Open > Open from my computer) -- or keep the
  design the script left open. Every timeline item can be edited: double-
  click a sketch to change its lines / circles, an extrude for its distance,
  a fillet for its radius; roll the timeline marker back to insert features.
  Bodies that are not square to the XY plane are sketched on XY and placed by
  a "move" feature right after their extrude.

  Frame: the part is built where it sits in the arm's design frame (the
  released STEP frame, mm) -- see ../../README.md for the print orientation.
  Released solid, for comparison: 12_J3_p1_x1_released.step
"""
# ======================================================================
# ARM-450 rev I -- design-tree builder for Fusion 360 (same in every part).
#
# Reads the part's feature list (<part>.json, next to this script) and
# builds it as a PARAMETRIC Fusion design -- a timeline you can edit:
#   Sketch + Extrude / Loft  -> a new body where the generator made one
#   Move                     -> when that body is not square to the XY plane
#   Combine (join/cut/intersect), Fillet, Chamfer -> as the generator did
# then checks the result against the released part (volume + bounding box)
# and saves <part>.f3d next to this script.
#
# Units: Fusion's API works in cm; the feature list is in mm (CM = 0.1).
# ======================================================================
import json
import math
import os
import time
import traceback

import adsk.core
import adsk.fusion

CM = 0.1
TOL_MM = 0.01                    # edge matching (fillets / chamfers)


def _P(x, y, z=0.0):
    return adsk.core.Point3D.create(x * CM, y * CM, z * CM)


def _V(mm):
    return adsk.core.ValueInput.createByReal(mm * CM)


def _mm(p):
    return (p.x / CM, p.y / CM, p.z / CM)


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    return math.sqrt(_dot(a, a))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _curve_dist(e, p):
    """distance (mm) from point p to a recorded edge (line / circle / arc / polyline)."""
    t = e["t"]
    if t == "line":
        a, b = e["p"]
        ab = _sub(b, a)
        L2 = _dot(ab, ab)
        u = 0.0 if L2 == 0 else max(0.0, min(1.0, _dot(_sub(p, a), ab) / L2))
        q = (a[0] + u * ab[0], a[1] + u * ab[1], a[2] + u * ab[2])
        return _norm(_sub(p, q))
    if t in ("circle", "arc"):
        c, r, n = e["c"], e["r"], e["n"]
        nn = _norm(n)
        n = (n[0] / nn, n[1] / nn, n[2] / nn)
        v = _sub(p, c)
        h = _dot(v, n)
        q = (v[0] - h * n[0], v[1] - h * n[1], v[2] - h * n[2])
        d = math.sqrt(h * h + (_norm(q) - r) ** 2)
        if t == "arc":
            # on the arc's span? angles about n, measured from the start point
            u = _sub(e["p"][0], c)
            u = (u[0] / _norm(u), u[1] / _norm(u), u[2] / _norm(u))
            w = _cross(n, u)
            ang = lambda x: math.atan2(_dot(x, w), _dot(x, u)) % (2 * math.pi)
            am, a1, ap = ang(_sub(e["p"][1], c)), ang(_sub(e["p"][2], c)), ang(q)
            if am > a1:                           # arc runs the other way round n
                a1, ap = 2 * math.pi - a1, (2 * math.pi - ap) % (2 * math.pi)
            if ap > a1 + 1e-6 and ap < 2 * math.pi - 1e-6:
                return max(d, 1e9)
        return d
    pts = e["p"]
    return min(_curve_dist(dict(t="line", p=[pts[i], pts[i + 1]]), p) for i in range(len(pts) - 1))


class Builder:
    def __init__(self, design, prog, log):
        self.design, self.prog, self.log = design, prog, log
        self.root = design.rootComponent
        self.f = self.root.features
        self.H = {}
        self.planes = {}
        self.marks = []

    # ------------------------------------------------------------ helpers
    @staticmethod
    def coll(items):
        c = adsk.core.ObjectCollection.create()
        for i in items:
            c.add(i)
        return c

    def label(self, s):
        src = s.get("src", "?").split(":")
        return "%s %s" % (src[0].replace(".py", ""), src[1] if len(src) > 1 else "")

    def name(self, obj, s, what):
        try:
            src = s.get("src", "?").split(":")
            obj.name = "%04d %s %s L%s" % (s["id"], what, src[1] if len(src) > 1 else "", src[-1])
        except Exception:
            pass

    def plane_at(self, z):
        if abs(z) < 1e-9:
            return self.root.xYConstructionPlane
        key = round(z, 6)
        if key not in self.planes:
            ci = self.root.constructionPlanes.createInput()
            ci.setByOffset(self.root.xYConstructionPlane, _V(z))
            pl = self.root.constructionPlanes.add(ci)
            try:
                pl.isLightBulbOn = False
            except Exception:
                pass
            self.planes[key] = pl
        return self.planes[key]

    def draw(self, sk, loops, z=0.0):
        """loops of edges (mm, the sketch plane at world z) as connected sketch loops."""
        S = sk.sketchCurves
        m2s = lambda x, y: sk.modelToSketchSpace(_P(x, y, z))

        def at(pt, x, y):
            if pt is None:
                return False
            g, q = pt.geometry, m2s(x, y)
            return abs(g.x - q.x) < 1e-7 and abs(g.y - q.y) < 1e-7

        def end_of(curve, x, y):
            for sp in (curve.startSketchPoint, curve.endSketchPoint):
                if at(sp, x, y):
                    return sp
            return None
        for lp in loops:
            first, last, x0, y0 = None, None, None, None
            for i, e in enumerate(lp):
                t = e[0]
                if t == "C":
                    S.sketchCircles.addByCenterRadius(m2s(e[1], e[2]), e[3] * CM)
                    continue
                xs, ys = e[1], e[2]
                xe, ye = (e[3], e[4]) if t == "L" else (e[5], e[6]) if t == "A" else (e[-2], e[-1])
                if x0 is None:
                    x0, y0 = xs, ys
                start = last if at(last, xs, ys) else m2s(xs, ys)
                end = first if (i == len(lp) - 1 and at(first, xe, ye)) else m2s(xe, ye)
                if t == "L":
                    c = S.sketchLines.addByTwoPoints(start, end)
                elif t == "A":
                    c = S.sketchArcs.addByThreePoints(start, m2s(e[3], e[4]), end)
                else:
                    pts = [m2s(e[k], e[k + 1]) for k in range(1, len(e), 2)]
                    c = S.sketchFittedSplines.add(self.coll(pts))
                if first is None:
                    first = end_of(c, x0, y0)
                last = end_of(c, xe, ye)

    @staticmethod
    def area_mm2(p):
        return p.areaProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy).area / (CM * CM)

    def pick(self, sk, area):
        best = None
        for i in range(sk.profiles.count):
            p = sk.profiles.item(i)
            err = abs(self.area_mm2(p) - area) if area is not None else -self.area_mm2(p)
            if best is None or err < best[0]:
                best = (err, p)
        if best is None:
            raise RuntimeError("the sketch has no closed profile")
        if area is not None and best[0] > max(1e-3 * area, 1e-3):
            raise RuntimeError("no profile of %.4f mm2 in the sketch (closest off by %.4f)" % (area, best[0]))
        return best[1]

    def move(self, bodies, T, s):
        m = adsk.core.Matrix3D.create()
        col = lambda j: (T[0][j], T[1][j], T[2][j])
        m.setWithCoordinateSystem(_P(*col(3)), adsk.core.Vector3D.create(*col(0)),
                                  adsk.core.Vector3D.create(*col(1)), adsk.core.Vector3D.create(*col(2)))
        mf = self.f.moveFeatures
        try:
            mi = mf.createInput2(self.coll(bodies))
            mi.defineAsFreeMove(m)
        except AttributeError:
            mi = mf.createInput(self.coll(bodies), m)
        self.name(mf.add(mi), s, "move")

    def combine(self, target, tools, op, keep, s):
        ci = self.f.combineFeatures.createInput(target, self.coll(tools))
        ci.operation = op
        ci.isKeepToolBodies = keep
        cf = self.f.combineFeatures.add(ci)
        self.name(cf, s, {adsk.fusion.FeatureOperations.JoinFeatureOperation: "join",
                          adsk.fusion.FeatureOperations.CutFeatureOperation: "cut",
                          adsk.fusion.FeatureOperations.IntersectFeatureOperation: "intersect"}.get(op, "combine"))
        return [cf.bodies.item(i) for i in range(cf.bodies.count)]

    def match_edges(self, bodies, targets):
        found, hit = [], [False] * len(targets)
        for b in bodies:
            for i in range(b.edges.count):
                e = b.edges.item(i)
                ev = e.evaluator
                ok, t0, t1 = ev.getParameterExtents()
                pts = [_mm(ev.getPointAtParameter(t0 + (t1 - t0) * k / 4.0)[1]) for k in range(5)]
                for j, tg in enumerate(targets):
                    if all(_curve_dist(tg, p) < TOL_MM for p in pts):
                        found.append(e); hit[j] = True
                        break
        for j, tg in enumerate(targets):                   # a target longer than any one edge
            if hit[j]:
                continue
            probe = tg["p"] if tg["t"] != "circle" else None
            if probe is None:
                continue
            for b in bodies:
                for i in range(b.edges.count):
                    e = b.edges.item(i)
                    ev = e.evaluator
                    close = True
                    for q in probe:
                        ok, par = ev.getParameterAtPoint(_P(*q))
                        if not ok or _norm(_sub(_mm(ev.getPointAtParameter(par)[1]), q)) > TOL_MM:
                            close = False; break
                    if close:
                        found.append(e); hit[j] = True
        if not all(hit):
            raise RuntimeError("%d of %d edges to round / chamfer not found on the body" % (hit.count(False), len(hit)))
        return found

    # -------------------------------------------------------------- steps
    def ext(self, s):
        sk = self.root.sketches.add(self.root.xYConstructionPlane)
        self.name(sk, s, "sketch")
        sk.isComputeDeferred = True
        self.draw(sk, s["loops"])
        sk.isComputeDeferred = False
        ei = self.f.extrudeFeatures.createInput(self.pick(sk, s["area"]),
                                                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ei.setDistanceExtent(False, _V(s["h"]))
        if abs(s["z0"]) > 1e-9:
            ei.startExtent = adsk.fusion.OffsetStartDefinition.create(_V(s["z0"]))
        ex = self.f.extrudeFeatures.add(ei)
        self.name(ex, s, "extrude %.2f" % s["h"])
        bodies = [ex.bodies.item(i) for i in range(ex.bodies.count)]
        if s["T"]:
            self.move(bodies, s["T"], s)
        return bodies

    def loft(self, s):
        li = self.f.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        for loops, z in zip(s["secs"], s["z"]):
            sk = self.root.sketches.add(self.plane_at(z))
            self.name(sk, s, "loft section")
            sk.isComputeDeferred = True
            self.draw(sk, [loops], z)
            sk.isComputeDeferred = False
            li.loftSections.add(self.pick(sk, None))
        li.isSolid = True
        lf = self.f.loftFeatures.add(li)
        self.name(lf, s, "loft")
        bodies = [lf.bodies.item(i) for i in range(lf.bodies.count)]
        if s["T"]:
            self.move(bodies, s["T"], s)
        return bodies

    def boolean(self, s):
        FO = adsk.fusion.FeatureOperations
        A = [b for i in s["a"] for b in self.H.pop(i)]
        T = [b for i in s["t"] for b in self.H.pop(i)]
        if s["op"] == "join":
            allb = A + T
            if len(allb) == 1:
                return allb
            try:
                return self.combine(allb[0], allb[1:], FO.JoinFeatureOperation, False, s)
            except Exception as e:
                self.log.append("step %d: join refused (%s) -- joining pair by pair" % (s["id"], e))
                return self.join_pairwise(allb, s)
        if s["op"] == "common" and len(T) > 1:
            T = self.combine(T[0], T[1:], FO.JoinFeatureOperation, False, s)
        op = FO.CutFeatureOperation if s["op"] == "cut" else FO.IntersectFeatureOperation
        out = []
        for j, a in enumerate(A):
            keep = j < len(A) - 1
            try:
                out += self.combine(a, T, op, keep, s)
            except Exception as e:
                if op != FO.CutFeatureOperation:
                    if len(A) > 1:                      # this piece lies outside the tool: it goes
                        self.log.append("step %d: piece outside the intersect tool removed" % s["id"])
                        self.name(self.f.removeFeatures.add(a), s, "remove piece")
                        if not keep:
                            for t in T:
                                self.name(self.f.removeFeatures.add(t), s, "remove tool")
                        continue
                    raise
                self.log.append("step %d: cut refused (%s) -- tools applied one by one" % (s["id"], e))
                out += self.cut_one_by_one(a, T, keep, s)
        if not out:
            raise RuntimeError("nothing left after the %s" % s["op"])
        return out

    def join_pairwise(self, bodies, s):
        """a join Fusion refuses as a whole (bodies that do not touch yet):
        join every pair that touches, again and again; bodies that touch
        nothing stay separate until a later join bridges them."""
        FO = adsk.fusion.FeatureOperations
        bodies = list(bodies)
        merged = True
        while merged and len(bodies) > 1:
            merged = False
            for i in range(len(bodies)):
                for j in range(i + 1, len(bodies)):
                    try:
                        r = self.combine(bodies[i], [bodies[j]], FO.JoinFeatureOperation, False, s)
                    except Exception:
                        continue
                    bodies = [b for k, b in enumerate(bodies) if k not in (i, j)] + r
                    merged = True
                    break
                if merged:
                    break
        return bodies

    def cut_one_by_one(self, a, T, keep, s):
        """a cut Fusion refuses as a whole (a tool that misses the body):
        each tool on its own; one that misses changes nothing and is removed."""
        FO = adsk.fusion.FeatureOperations
        cur = [a]
        for t in T:
            nxt = []
            for b in cur:
                try:
                    nxt += self.combine(b, [t], FO.CutFeatureOperation, True, s)
                except Exception:
                    nxt.append(b)
            cur = nxt
        if not keep:
            for t in T:
                try:
                    self.name(self.f.removeFeatures.add(t), s, "remove cut tool")
                except Exception:
                    pass
        return cur

    def rounding(self, s):
        bodies = self.H.pop(s["of"])
        edges = self.coll(self.match_edges(bodies, s["edges"]))
        if s["k"] == "fillet":
            fi = self.f.filletFeatures.createInput()
            try:
                fi.edgeSetInputs.addConstantRadiusEdgeSet(edges, _V(s["r"]), True)
            except AttributeError:
                fi.addConstantRadiusEdgeSet(edges, _V(s["r"]), True)
            fi.isRollingBallCorner = True
            ft = self.f.filletFeatures.add(fi)
        else:
            try:
                ci = self.f.chamferFeatures.createInput2()
                ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, _V(s["r"]), True)
            except AttributeError:
                ci = self.f.chamferFeatures.createInput(edges, True)
                ci.setToEqualDistance(_V(s["r"]))
            ft = self.f.chamferFeatures.add(ci)
        self.name(ft, s, "%s %.2f" % (s["k"], s["r"]))
        return bodies

    def pick_body(self, s):
        bodies = self.H.pop(s["of"])
        best = None
        for b in bodies:
            c = _mm(b.physicalProperties.centerOfMass)
            v = b.volume / CM ** 3
            err = _norm(_sub(c, s["c"])) + abs(v - s["v"]) / max(s["v"], 1.0)
            if best is None or err < best[0]:
                best = (err, b)
        for b in bodies:
            if b is not best[1]:
                rf = self.f.removeFeatures.add(b)
                self.name(rf, s, "remove unused piece")
        return [best[1]]

    def run(self):
        steps = self.prog["steps"]
        t0 = time.time()
        for s in steps:
            before = self.design.timeline.count
            k = s["k"]
            try:
                if k == "ext":
                    r = self.ext(s)
                elif k == "loft":
                    r = self.loft(s)
                elif k == "bool":
                    r = self.boolean(s)
                elif k in ("fillet", "chamfer"):
                    r = self.rounding(s)
                elif k == "sub":
                    r = self.pick_body(s)
                elif k == "group":
                    r = [b for i in s["of"] for b in self.H.pop(i)]
                else:
                    raise RuntimeError("unknown step " + k)
            except Exception as e:
                raise RuntimeError("step %d (%s, from %s) failed: %s" % (s["id"], k, s.get("src"), e))
            self.H[s["id"]] = r
            self.marks.append((self.label(s), before, self.design.timeline.count - 1))
            if s["id"] % 25 == 0:
                adsk.doEvents()
        self.log.append("%d steps in %.0f s" % (len(steps), time.time() - t0))
        return self.H[self.prog["root"]]

    def group_timeline(self):
        """one timeline group per stretch of steps from the same generator function."""
        runs = []
        for lab, a, b in self.marks:
            if b < a:
                continue
            if runs and runs[-1][0] == lab and runs[-1][2] == a - 1:
                runs[-1][2] = b
            else:
                runs.append([lab, a, b])
        n = 0
        for lab, a, b in reversed(runs):
            if b - a < 1:
                continue
            try:
                g = self.design.timeline.timelineGroups.add(a, b)
                g.name = lab
                n += 1
            except Exception:
                pass
        self.log.append("%d timeline groups" % n)


def build_part(app, json_path, out_dir=None, close=False):
    """build one part from its feature list; returns (ok, report text)."""
    prog = json.load(open(json_path))
    out_dir = out_dir or os.path.dirname(json_path)
    log = ["ARM-450 rev I -- %s (%s)" % (prog["part"], prog["file"]), "print qty %d" % prog["qty"]]
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    try:
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    except Exception:
        pass
    b = Builder(design, prog, log)
    ok = True
    try:
        bodies = b.run()
        body = bodies[0]
        body.name = prog["part"]
        for j, x in enumerate(bodies[1:], 2):
            x.name = "%s_%d" % (prog["part"], j)
        ex = prog["expected"]

        def volume(x):
            try:
                return x.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy).volume
            except Exception:
                return x.volume
        v = sum(volume(x) for x in bodies) / CM ** 3
        bb = body.boundingBox                      # not always tight in Fusion: a gross check only
        got = list(_mm(bb.minPoint)) + list(_mm(bb.maxPoint))
        dbb = max(abs(g - e) for g, e in zip(got, ex["bbox_mm"]))
        dv = abs(v - ex["volume_mm3"]) / ex["volume_mm3"]
        ok = len(bodies) == 1 and dv < 5e-5 and dbb < 1.0
        log.append("bodies %d   volume %.2f mm3 (released %.2f, off %.4f %%)   bounding box within %.3f mm   -> %s"
                   % (len(bodies), v, ex["volume_mm3"], 100 * dv, dbb, "MATCHES THE RELEASED PART" if ok else "CHECK"))
        b.group_timeline()
    except Exception:
        ok = False
        log.append("BUILD STOPPED:\n" + traceback.format_exc())
    f3d = os.path.join(out_dir, prog["file"] + ".f3d")
    try:
        em = design.exportManager
        em.execute(em.createFusionArchiveExportOptions(f3d))
        log.append("saved " + f3d)
    except Exception:
        log.append("could not save the .f3d:\n" + traceback.format_exc())
    try:
        open(os.path.join(out_dir, prog["file"] + "_BUILD_REPORT.txt"), "w").write("\n".join(log) + "\n")
    except Exception:
        pass
    if close:
        doc.close(False)
    return ok, "\n".join(log)


HERE = os.path.dirname(os.path.realpath(__file__))


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        ok, report = build_part(app, os.path.join(HERE, "12_J3_p1_x1.json"))
        ui.messageBox(report, "ARM-450 J3_p1")
    except Exception:
        ui.messageBox("ARM-450 J3_p1: the script failed\n\n" + traceback.format_exc())
