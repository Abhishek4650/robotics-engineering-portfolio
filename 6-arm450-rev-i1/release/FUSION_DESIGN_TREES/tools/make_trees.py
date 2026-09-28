#!/usr/bin/env python3
"""
ARM-450 rev I -- the design tree of every printed part, from the generators.

1. Copies the generators (REV_H/*.py) to a scratch folder and runs them there
   with record_cq installed, so nothing in the released folders is written.
2. Checks that what was recorded IS the released part: the recorded solid vs
   the released STEP, boolean difference both ways (mm3).
3. Unfolds each part's recorded tree into a flat feature list -- the Fusion
   timeline: sketch + extrude / loft (new body), combine (join / cut /
   intersect), fillet, chamfer, pick one body. Moves and mirrors are carried
   down to the sketches, so every body is sketched where it ends up.
4. Writes _programs/<part>.json for emit_scripts.py.

Run:  python3 make_trees.py [--work DIR]
"""
import json
import os
import runpy
import shutil
import sys
import tempfile
import time

import numpy as np

TOOLS = os.path.dirname(os.path.abspath(__file__))
TREES = os.path.dirname(TOOLS)
PROJ = os.path.dirname(TREES)
REV = os.path.join(PROJ, "REV_H")
OUTCAD = os.path.join(PROJ, "out_cad")
PROG = os.path.join(TREES, "_programs")
sys.path.insert(0, TOOLS)
sys.setrecursionlimit(100000)

# (part, qty, generator run, released STEP, note) in the release's numbering
PARTS = [
    ("base", 1, "gen_base_collar.py", "REV_H"), ("spigot_collar", 1, "gen_base_collar.py", "REV_H"),
    ("j1_mount", 1, "gen_drive_j1.py", "REV_H"), ("j1_hub", 1, "gen_drive_j1.py", "REV_H"),
    ("J2_turret_p1", 1, "gen_drive_j2.py", "REV_H"), ("J2_turret_p2", 1, "gen_drive_j2.py", "REV_H"),
    ("J2_shaft", 1, "gen_drive_j2.py", "REV_H"), ("shaft_clamp", 4, "gen_clamp.py", "REV_H"),
    ("link_upper_groove", 1, "LINK_GROOVE", "out_cad"), ("link_upper_tongue", 1, "gen_upper_tongue.py", "REV_H"),
    ("collar_upper", 2, "spring_parts.py", "REV_H"), ("J3_p1", 1, "gen_drive_j3.py", "REV_H"),
    ("J3_p2", 1, "gen_drive_j3.py", "REV_H"), ("J3_shaft", 1, "gen_drive_j3.py", "REV_H"),
    ("link_fore_tongue", 1, "gen_forearm.py", "REV_H"), ("link_fore_groove", 1, "gen_forearm.py", "REV_H"),
    ("collar_fore", 2, "spring_parts.py", "REV_H"), ("j4_base", 1, "gen_drive_j4.py", "REV_H"),
    ("j4_cap", 1, "gen_drive_j4.py", "REV_H"), ("j4_hub", 1, "gen_drive_j4.py", "REV_H"),
    ("J5_p1", 1, "gen_wrist.py", "REV_H"), ("J5_p2", 1, "gen_wrist.py", "REV_H"),
    ("J5_shaft", 1, "gen_wrist.py", "REV_H"), ("J5_spacer", 2, "gen_wrist.py", "REV_H"),
    ("j6_body", 1, "gen_wrist.py", "REV_H"), ("j6_cap", 1, "gen_wrist.py", "REV_H"),
    ("j6_flange", 1, "gen_wrist.py", "REV_H"),
]
RUN_ORDER = ["gen_base_collar.py", "gen_clamp.py", "gen_drive_j1.py", "gen_drive_j2.py", "gen_upper_tongue.py",
             "spring_parts.py", "gen_drive_j3.py", "gen_forearm.py", "gen_drive_j4.py", "gen_wrist.py"]


# ----------------------------------------------------------------- geometry
def vol(topo):
    import compare
    return compare.vol(topo)


def xor(a, b):
    import compare
    return compare.diff(a, b)


def common_vol(a, b):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    ba, bb = Bnd_Box(), Bnd_Box()
    BRepBndLib.Add_s(a, ba); BRepBndLib.Add_s(b, bb)
    if ba.IsOut(bb):
        return 0.0
    return vol(BRepAlgoAPI_Common(a, b).Shape())


def bbox(topo):
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    b = Bnd_Box(); BRepBndLib.AddOptimal_s(topo, b, False, False)
    return [round(x, 4) for x in b.Get()]


def _solids(topo):
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_SOLID
    out, ex = [], TopExp_Explorer(topo, TopAbs_SOLID)
    while ex.More():
        out.append(ex.Current()); ex.Next()
    return out


def compound(topos):
    from OCP.TopoDS import TopoDS_Compound
    from OCP.BRep import BRep_Builder
    c, bld = TopoDS_Compound(), BRep_Builder()
    bld.MakeCompound(c)
    for t in topos:
        bld.Add(c, t)
    return c


# ------------------------------------------------------- tree -> timeline
class Unfold:
    """recorded node tree -> flat feature list. M (4x4, rigid or mirror)
    is carried down to the leaves; each use of a node is built on its own
    (a combine consumes its tool bodies, as in Fusion)."""

    def __init__(self, R):
        self.R, self.steps, self.notes = R, [], []
        self.noop_cache = {}
        self.stack, self.trace = [], []

    def add(self, step):
        step["id"] = len(self.steps)
        self.steps.append(step)
        self.trace.append(self.stack[-1])          # (node, M) this step stands for -- debugging only
        return step["id"]

    @staticmethod
    def P(M, p):
        return (M @ np.append(np.asarray(p, float), 1.0))[:3]

    @staticmethod
    def D(M, v):
        return M[:3, :3] @ np.asarray(v, float)

    def edge_world(self, M, e):
        t = e["t"]
        if t == "line":
            return dict(t="line", p=[self.P(M, q).tolist() for q in e["p"]])
        if t == "circle":
            return dict(t="circle", c=self.P(M, e["c"]).tolist(), r=e["r"], n=self.D(M, e["n"]).tolist())
        if t == "arc":
            return dict(t="arc", p=[self.P(M, q).tolist() for q in e["p"]], c=self.P(M, e["c"]).tolist(),
                        r=e["r"], n=self.D(M, e["n"]).tolist())
        return dict(t="curve", p=[self.P(M, q).tolist() for q in e["p"]])

    @staticmethod
    def frame(z, pts, hint=None):
        """right-handed frame with this z; None when z is +-world Z."""
        z = z / np.linalg.norm(z)
        if abs(abs(z[2]) - 1.0) < 1e-9:
            return None
        x = None
        if hint is not None:
            x = hint - (hint @ z) * z
            x = x / np.linalg.norm(x) if np.linalg.norm(x) > 1e-9 else None
        if x is None:
            for a in (np.array([1.0, 0, 0]), np.array([0, 1.0, 0])):
                x = a - (a @ z) * z
                if np.linalg.norm(x) > 1e-6:
                    x = x / np.linalg.norm(x); break
        y = np.cross(z, x)
        return np.column_stack([x, y, z])

    def loops2d(self, loops_w, o, F):
        """world loops -> 2D in the sketch frame (F None: world XY)."""
        def q(p):
            p = np.asarray(p) - o
            if F is None:
                return [float(p[0] + o[0]), float(p[1] + o[1])], float(p[2])
            l = F.T @ p
            return [float(l[0]), float(l[1])], float(l[2])
        out, off = [], 0.0
        for lp in loops_w:
            L = []
            for e in lp:
                if e["t"] == "line":
                    a, za = q(e["p"][0]); b, zb = q(e["p"][1])
                    L.append(["L"] + a + b); off = max(off, abs(za), abs(zb))
                elif e["t"] == "circle":
                    c, zc = q(e["c"]); L.append(["C"] + c + [e["r"]]); off = max(off, abs(zc))
                elif e["t"] == "arc":
                    a, za = q(e["p"][0]); m, zm = q(e["p"][1]); b, zb = q(e["p"][2])
                    L.append(["A"] + a + m + b); off = max(off, abs(za), abs(zm), abs(zb))
                else:
                    pts = [q(p) for p in e["p"]]
                    L.append(["S"] + [c for p, _ in pts for c in p]); off = max([off] + [abs(z) for _, z in pts])
                    self.notes.append("spline approximated at %s" % self.cur_src)
            out.append(chain(L))
        return out, off

    def leaf_extrude(self, n, M):
        d = n["data"]
        vec = self.D(M, d["vec"]); h = float(np.linalg.norm(vec)); z = vec / h
        lw = [[self.edge_world(M, e) for e in lp] for lp in d["loops"]]
        o = np.array(first_point(lw[0][0]))
        hint = None
        for e in lw[0]:
            if e["t"] == "line":
                hint = np.subtract(e["p"][1], e["p"][0]); break
        F = self.frame(z, None, hint)
        if F is None:
            loops, off = self.loops2d(lw, np.array([0.0, 0.0, o[2]]), None)
            z0 = o[2] - (h if z[2] < 0 else 0.0)
            T = None
        else:
            loops, off = self.loops2d(lw, o, F)
            z0, T = 0.0, np.column_stack([F, o]).tolist()
        if off > 1e-5:
            raise ValueError("profile not planar / not square to the extrusion (%.2e) at %s" % (off, n["src"]))
        return self.add(dict(k="ext", loops=loops, area=d["area"], h=h, z0=float(z0), T=T, src=n["src"]))

    def leaf_loft(self, n, M):
        d = n["data"]
        secs = [[self.edge_world(M, e) for e in w] for w in d["sections"]]
        c0 = np.mean([first_point(e) for e in secs[0]], axis=0)
        c1 = np.mean([first_point(e) for e in secs[-1]], axis=0)
        nrm = None
        for e in secs[0]:
            if e["t"] in ("circle", "arc"):
                nrm = np.array(e["n"]); break
        if nrm is None:
            raise ValueError("loft section without a plane at %s" % n["src"])
        if (c1 - c0) @ nrm < 0:
            nrm = -nrm
        F = self.frame(nrm, None)
        out, zs = [], []
        for w in secs:
            p = np.array(first_point(w[0]))
            if F is None:
                lp, off = self.loops2d([w], np.array([0.0, 0.0, 0.0]), None)
                zs.append(float(p[2])); out.append(lp[0])
            else:
                lp, _ = self.loops2d([w], c0, F)
                zs.append(float(F[:, 2] @ (p - c0))); out.append(lp[0])
        T = None if F is None else np.column_stack([F, c0]).tolist()
        return self.add(dict(k="loft", secs=out, z=zs, ruled=d["ruled"], T=T, src=n["src"]))

    def useful_tools(self, n):
        """cut / common tools that actually touch the operand (a cut by a
        solid that misses the part changes nothing -- Fusion would reject it)."""
        k = n["id"]
        if k in self.noop_cache:
            return self.noop_cache[k]
        R = self.R
        na = n["data"]["nargs"]
        args = [R.NODES[i]["topo"] for i in n["kids"][:na]]
        A = args[0] if len(args) == 1 else compound(args)
        keep = [i for i in n["kids"][na:] if common_vol(A, R.NODES[i]["topo"]) > 1e-6]
        self.noop_cache[k] = keep
        return keep

    def build_list(self, kids, M):
        """CadQuery re-wraps every solid of a multi-solid result one by one
        (_findType, Compound iteration): a list holding sub(P,0) .. sub(P,n-1)
        is just P again -- build P once instead of n picked copies."""
        R = self.R
        by_parent = {}
        for i in kids:
            c = R.NODES[i]
            if c["kind"] == "sub":
                by_parent.setdefault(c["kids"][0], set()).add(c["data"]["index"])
        whole = {p for p, ix in by_parent.items() if ix == set(range(len(_solids(R.NODES[p]["topo"]))))}
        ids, done = [], set()
        for i in kids:
            c = R.NODES[i]
            p = c["kids"][0] if c["kind"] == "sub" else None
            if p in whole:
                if p not in done:
                    ids.append(self.build(p, M)); done.add(p)
            else:
                ids.append(self.build(i, M))
        return ids

    def isolating_box(self, n):
        """an axis-aligned box (as an extrude leaf) around piece `index` of
        the parent that stays clear of every other piece, or None."""
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
        from OCP.BRepExtrema import BRepExtrema_DistShapeShape
        from OCP.gp import gp_Pnt
        sols = _solids(self.R.NODES[n["kids"][0]]["topo"])
        me = sols[n["data"]["index"]]
        x0, y0, z0, x1, y1, z1 = bbox(me)
        for pad in (0.5, 0.05):
            X0, Y0, Z0, X1, Y1, Z1 = x0 - pad, y0 - pad, z0 - pad, x1 + pad, y1 + pad, z1 + pad
            bx = BRepPrimAPI_MakeBox(gp_Pnt(X0, Y0, Z0), gp_Pnt(X1, Y1, Z1)).Shape()
            if all(BRepExtrema_DistShapeShape(bx, o).Value() > 0.02 for j, o in enumerate(sols)
                   if j != n["data"]["index"]):
                c = [[X0, Y0, Z0], [X1, Y0, Z0], [X1, Y1, Z0], [X0, Y1, Z0]]
                loop = [dict(t="line", p=[c[i], c[(i + 1) % 4]]) for i in range(4)]
                return dict(loops=[loop], vec=[0.0, 0.0, Z1 - Z0], area=(X1 - X0) * (Y1 - Y0))
        return None

    def build(self, nid, M):
        self.stack.append((nid, M))
        try:
            return self._build(nid, M)
        finally:
            self.stack.pop()

    def _build(self, nid, M):
        R = self.R
        n = R.NODES[nid]
        k = n["kind"]
        self.cur_src = n["src"]
        if k == "xform":
            T = np.array(n["data"]["M"])
            if abs(abs(np.linalg.det(T[:3, :3])) - 1.0) > 1e-9:
                raise ValueError("scaling move at %s" % n["src"])
            return self.build(n["kids"][0], M @ T)
        if k == "extrude":
            return self.leaf_extrude(n, M)
        if k == "loft":
            return self.leaf_loft(n, M)
        if k in ("fuse", "cut", "common"):
            na = n["data"]["nargs"]
            if n["data"]["fuzzy"] > 1e-6:
                self.notes.append("fuzzy boolean at %s" % n["src"])
            tools = n["kids"][na:] if k == "fuse" else self.useful_tools(n)
            a = self.build_list(n["kids"][:na], M)
            if not tools and k == "cut":
                return a[0] if len(a) == 1 else self.add(dict(k="group", of=a, src=n["src"]))
            if not tools and k == "common":
                raise ValueError("intersection with nothing at %s" % n["src"])
            t = self.build_list(tools, M)
            return self.add(dict(k="bool", op={"fuse": "join", "cut": "cut", "common": "common"}[k], a=a, t=t,
                                 src=n["src"]))
        if k in ("fillet", "chamfer"):
            i = self.build(n["kids"][0], M)
            e = [self.edge_world(M, x) for x in n["data"]["edges"]]
            return self.add(dict(k=k, of=i, r=n["data"].get("r_mm", n["data"].get("d_mm")), edges=e, src=n["src"]))
        if k == "sub":
            box = self.isolating_box(n)
            i = self.build(n["kids"][0], M)
            if box is not None:
                # one piece of a multi-piece result, cut out exactly by a box
                # that holds it and no other piece: works however Fusion
                # groups the pieces into bodies
                bid = self.leaf_extrude(dict(data=box, src=n["src"]), M)
                return self.add(dict(k="bool", op="common", a=[i], t=[bid], src=n["src"]))
            self.notes.append("body picked by centroid at %s" % n["src"])
            return self.add(dict(k="sub", of=i, c=self.P(M, n["data"]["centroid"]).tolist(),
                                 v=n["data"]["volume"], src=n["src"]))
        if k == "compound":
            ids = self.build_list(n["kids"], M)
            return ids[0] if len(ids) == 1 else self.add(dict(k="group", of=ids, src=n["src"]))
        raise ValueError("cannot unfold a %s node (%s)" % (k, n["src"]))


def first_point(e):
    if e["t"] == "circle":
        c, r, nv = np.array(e["c"]), e["r"], np.array(e["n"])
        a = np.array([1.0, 0, 0]) - nv[0] * nv
        if np.linalg.norm(a) < 1e-6:
            a = np.array([0, 1.0, 0]) - nv[1] * nv
        return (c + r * a / np.linalg.norm(a)).tolist()
    return e["p"][0]


def chain(L):
    """order + orient a loop's edges end to start, so the sketch is one
    connected loop (the recorder gives edges in order, not in direction)."""
    def ends(e):
        if e[0] == "L":
            return e[1:3], e[3:5]
        if e[0] == "A":
            return e[1:3], e[5:7]
        if e[0] == "S":
            return e[1:3], e[-2:]
        return None, None

    def rev(e):
        if e[0] == "L":
            return ["L"] + e[3:5] + e[1:3]
        if e[0] == "A":
            return ["A"] + e[5:7] + e[3:5] + e[1:3]
        if e[0] == "S":
            pts = [e[1:][i:i + 2] for i in range(0, len(e) - 1, 2)][::-1]
            return ["S"] + [c for p in pts for c in p]
        return e
    if len(L) < 2 or any(x[0] == "C" for x in L):
        return L
    out = [L[0]]
    rest = L[1:]
    close = lambda a, b: abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6
    if not (close(ends(L[0])[1], ends(L[1])[0]) or close(ends(L[0])[1], ends(L[1])[1])):
        out = [rev(L[0])]
    for e in rest:
        end = ends(out[-1])[1]
        s, t = ends(e)
        out.append(e if close(end, s) else rev(e) if close(end, t) else e)
    return out


# --------------------------------------------------------------------- main
def run_generators(work):
    import record_cq as R
    wr = os.path.join(work, "REV_H")
    os.makedirs(wr); os.makedirs(os.path.join(work, "out_cad"))
    for f in os.listdir(REV):
        if f.endswith((".py", ".json")):
            shutil.copy(os.path.join(REV, f), wr)
    for f in ("link_upper_tongue.step", "link_upper_groove.step", "j1_pod.step"):
        shutil.copy(os.path.join(OUTCAD, f), os.path.join(work, "out_cad"))
    sys.path.insert(0, wr)
    os.chdir(wr)
    R.install()
    # the released upper link (out_cad, 2026-09-11) is link_pro.build(.., "socket")
    # -- proven equal below; gen_upper_tongue reads it back from STEP, so give it
    # the rebuilt (recorded) solid instead of the file
    sys.path.insert(0, "/home/user/ros2_ws/arm450_design/verify_pro/parts")
    import link_pro as LP
    import cadquery as cq
    subst = {}
    orig_import = cq.importers.importStep

    def importStep(fn, *a, **k):
        key = os.path.basename(fn)
        if key in ("link_upper_tongue.step", "link_upper_groove.step"):
            w = LP.build(tongue=key.startswith("link_upper_tongue"), face_x=LP.UPPER_FACE_X, end="socket")
            ref = orig_import(fn, *a, **k).val().wrapped
            d = xor(ref, w.val().wrapped)
            subst[key] = d
            if max(d) > 1e-3:
                raise RuntimeError("link_pro rebuild differs from %s by %s mm3" % (key, d))
            return w
        return orig_import(fn, *a, **k)
    cq.importers.importStep = importStep
    log = []
    for g in RUN_ORDER:
        t = time.time()
        try:
            runpy.run_path(os.path.join(wr, g), run_name="__main__")
        except SystemExit:
            pass
        log.append("%-22s %.1f s" % (g, time.time() - t))
        print("ran", log[-1], flush=True)
    # j1_mount is written by gen_drive_j1.build_mount() (not by its __main__)
    import gen_drive_j1 as G1m
    G1m.build_mount()
    grv = LP.build(tongue=False, face_x=LP.UPPER_FACE_X, end="socket")
    R.EXPORTS["link_upper_groove"] = R.node_of(grv.val())
    import gen_fit_coupon as GFC
    coupons = {}
    for nm, sh in GFC.parts().items():
        coupons[nm] = R.node_of(sh.val() if hasattr(sh, "val") else sh)
    cq.importers.importStep = R._orig[(cq.importers, "importStep")]     # plain reader for the references
    return R, coupons, subst, log


def main():
    work = sys.argv[sys.argv.index("--work") + 1] if "--work" in sys.argv else tempfile.mkdtemp(prefix="arm450_tree_")
    cwd = os.getcwd()
    R, coupons, subst, log = run_generators(work)
    os.chdir(cwd)
    import cadquery as cq
    os.makedirs(PROG, exist_ok=True)
    todo = [("%02d_%s_x%d" % (i, nm, q), nm, q, R.EXPORTS[nm],
             os.path.join(OUTCAD if src == "out_cad" else REV, nm + ".step"))
            for i, (nm, q, g, src) in enumerate(PARTS, 1)]
    todo += [(nm, nm, 1, nid, os.path.join(PROJ, "EDITABLE_CAD", "fit_test_step", nm + ".step"))
             for nm, nid in sorted(coupons.items())]
    summary = []
    for fname, nm, q, nid, ref in todo:
        t = time.time()
        topo = R.NODES[nid]["topo"]
        refs = cq.importers.importStep(ref).val().wrapped
        d = xor(refs, topo)
        U = Unfold(R)
        root = U.build(nid, np.eye(4))
        kinds = {}
        for s in U.steps:
            kinds[s["k"]] = kinds.get(s["k"], 0) + 1
        prog = dict(part=nm, file=fname, qty=q, root=root, steps=U.steps, notes=sorted(set(U.notes)),
                    expected=dict(volume_mm3=vol(refs), bbox_mm=bbox(refs)),
                    recorded_vs_released_mm3=d, counts=kinds, released_step=os.path.relpath(ref, PROJ))
        json.dump(prog, open(os.path.join(PROG, fname + ".json"), "w"))
        line = "%-28s steps %4d  %s  recorded-vs-released %.4f / %.4f mm3  %.1f s%s" % (
            fname, len(U.steps), " ".join("%s %d" % kv for kv in sorted(kinds.items())), d[0], d[1],
            time.time() - t, ("  NOTES: " + "; ".join(prog["notes"])) if prog["notes"] else "")
        print(line, flush=True)
        summary.append(line)
    open(os.path.join(PROG, "_RECORD.log"), "w").write(
        "generator runs (scratch copy %s)\n  %s\nlink_pro rebuild vs released out_cad links (mm3): %s\n\n%s\n"
        % (work, "\n  ".join(log), subst, "\n".join(summary)))


if __name__ == "__main__":
    main()
