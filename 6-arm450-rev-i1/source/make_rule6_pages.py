#!/usr/bin/env python3
"""
RULE 6 -- the whole design, shown the clear (Rule-5) way:
  1. the FULL ASSEMBLY in several POSES (all six joints moved together, by
     the measured joint axes, product of exponentials). Each pose is CHECKED
     before it is drawn: minimum distance between every pair of rigid bodies
     (FCL on the exact-solid meshes); neighbouring bodies are compared
     without the joint's own bearing / servo / spring (they are the joint).
  2. PART-WISE pages: every printed part alone, four views.
  3. ATTENTION TO DETAIL: close-ups of each part's features found from its
     own faces (bearing / insert pockets, holes, counterbores, pilots),
     labelled with the MEASURED diameter and depth.
"""
import os
import re
import sys

import numpy as np
import cadquery as cq
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402

from OCP.TopExp import TopExp_Explorer              # noqa: E402
from OCP.TopAbs import TopAbs_FACE                  # noqa: E402
from OCP.TopoDS import TopoDS                       # noqa: E402
from OCP.BRepAdaptor import BRepAdaptor_Surface     # noqa: E402
from OCP.GeomAbs import GeomAbs_Cylinder            # noqa: E402
from OCP.BRepGProp import BRepGProp_Face            # noqa: E402
from OCP.gp import gp_Pnt, gp_Vec                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_rule5_views as R5      # noqa: E402
import build_final_assembly as BA  # noqa: E402
import verify_mating as VM         # noqa: E402
import verify_6dof as V6           # noqa: E402
import spring_parts as SP          # noqa: E402

OUT = os.path.join(HERE, "RULE6_VIEWS")
POSES = [  # name, (J1..J6 deg) -- all inside the swept ranges
    ("home (straight up, as modelled)", (0, 0, 0, 0, 0, 0)),
    ("ready", (0, 30, -60, 0, 30, 0)),
    ("reach forward, low", (0, 50, 35, 0, 40, 0)),
    ("turned, elbow up, wrist rolled", (60, -30, -65, 45, -40, 90)),
    ("turned the other way, wrist pitched", (-70, 25, 50, -90, 46, -60)),
    ("folded back", (30, -54, 72, 90, -46, 45)),
]


# ------------------------------------------------------------------ kinematics
def joint_axes():
    M, TURW, J2J, J3W, J5W, ABC = BA.M, BA.TURW, BA.J2J, BA.J3W, BA.J5W, BA.ABC
    flipZ = BA.rot([1, 0, 0], 180)
    G1, G4, W, G3, TP = BA.G1, BA.G4, BA.W, BA.G3, BA.TP
    servoT = [M(t=(0, 0, G1.Z_CAP)) @ flipZ, TURW @ J2J @ M(t=(0, 0, TP.Z_BAY)), J3W @ M(t=(0, 0, G3.P)),
              M(t=(0, 0, G4.Z_CAP)) @ flipZ, J5W @ M(t=(0, 0, W.P5)), J5W @ ABC @ M(t=(0, 0, W.X6_CAP)) @ flipZ]
    return [(T[:3, 3].copy(), T[:3, 2] / np.linalg.norm(T[:3, 2])) for T in servoT]


def body_frames(axes, th_deg):
    """G[k] = pose of rigid body k (0 = ground)."""
    G = [np.eye(4)]
    for (q, w), t in zip(axes, np.radians(th_deg)):
        G.append(G[-1] @ V6.expm_screw(w, -np.cross(w, q), t))
    return G


def body(name):
    b = VM.body_of(name)
    if b is not None:
        return b
    m = re.match(r"^brg_J(\d)", name)
    if m:
        return int(m.group(1)) - 1                  # bearings drawn with their housing
    return None


def spring_meshes(G, cache):
    out = {}
    home = SP.springs_world(0.0, 0.0)
    for i, (jn, a, b) in enumerate(home):
        lo = 1 if jn == "J2" else 2
        A = (G[lo] @ np.r_[a, 1.0])[:3]; B = (G[lo + 1] @ np.r_[b, 1.0])[:3]
        s, T = BA.spring(A, B)
        sh = s.val().moved(BA.loc(T)).wrapped
        out["spring_%s_%+d" % (jn, 1 if a[1] > 0 else -1)] = R5.tess(sh, 0.05, 0.25)
    return out


def posed(meshes, G):
    out = {}
    for nm, (V, F) in meshes.items():
        if nm.startswith("spring_"):
            continue
        b = body(nm)
        T = G[b] if b is not None else np.eye(4)
        out[nm] = ((T[:3, :3] @ V.T).T + T[:3, 3], F)
    return out


def pose_clearance(pm):
    """min distance between every pair of rigid bodies in this pose."""
    groups = {}
    for nm, (V, F) in pm.items():
        b = body(nm)
        if b is None or nm.startswith("spring_"):
            continue
        groups.setdefault(b, []).append((nm, trimesh.Trimesh(V, F, process=False)))
    res = []
    for i in range(7):
        for j in range(i + 1, 7):
            joint = j if j == i + 1 else None

            def keep(nm):
                return not (joint and (nm.startswith("brg_J%d" % joint) or nm == "servo_J%d" % joint
                                       or nm.startswith("horn_screw_J%d" % joint)))
            ma, mb = trimesh.collision.CollisionManager(), trimesh.collision.CollisionManager()
            for nm, m in groups.get(i, []):
                if keep(nm):
                    ma.add_object(nm, m)
            for nm, m in groups.get(j, []):
                if keep(nm):
                    mb.add_object(nm, m)
            d, names = ma.min_distance_other(mb, return_names=True)
            res.append((i, j, d, names))
    return res


# ------------------------------------------------------------------ features
CLASSES = [(42.02, "6806 bearing pocket"), (37.02, "6706 bearing pocket"), (38.4, "link clamp bore"),
           (34.0, "6706 outer-race shoulder bore"), (33.5, "6706 inner-ring relief"), (38.0, "6806 outer-race recess"),
           (24.0, "horn clearance / socket"), (46.0, "collar OD"),
           (31.0, "shaft clearance bore"), (30.0, "shaft / race bore"), (30.15, "collar bore"),
           (22.0, "spigot / shaft bore"), (8.0, "cable exit"), (6.2, "M3 head counterbore"),
           (6.0, "M3 head counterbore"), (5.6, "M4 insert pocket"), (5.4, "M5 set-screw clearance"),
           (5.0, "M2.5 head counterbore"), (4.8, "horn-screw counterbore"), (4.5, "M4 clearance"),
           (4.2, "M5 self-tap pilot / relief"), (4.1, "M3 insert pocket"), (3.5, "M2.5 insert pocket"),
           (3.4, "M3 clearance"), (2.7, "M2.5 clearance"), (2.6, "M3 grub pilot"), (2.52, "horn-screw hole"),
           (2.5, "M3 self-tap pilot")]


def classify(d):
    best = min(CLASSES, key=lambda c: abs(c[0] - d))
    return best[1] if abs(best[0] - d) < 0.06 else "hole O%.2f" % d


def features(shape):
    feats = {}
    e = TopExp_Explorer(shape, TopAbs_FACE)
    while e.More():
        f = TopoDS.Face_s(e.Current())
        s = BRepAdaptor_Surface(f)
        if s.GetType() == GeomAbs_Cylinder:
            c = s.Cylinder(); r = c.Radius()
            a = c.Axis(); d = np.array([a.Direction().X(), a.Direction().Y(), a.Direction().Z()])
            o = np.array([a.Location().X(), a.Location().Y(), a.Location().Z()])
            u0, u1, v0, v1 = s.FirstUParameter(), s.LastUParameter(), s.FirstVParameter(), s.LastVParameter()
            p, n = gp_Pnt(), gp_Vec()
            BRepGProp_Face(f).Normal((u0 + u1) / 2, (v0 + v1) / 2, p, n)
            P = np.array([p.X(), p.Y(), p.Z()]); N = np.array([n.X(), n.Y(), n.Z()])
            rel = P - o; radial = rel - (rel @ d) * d
            hole = (N @ radial) < 0                      # normal points to the axis: a hole
            if hole and r < 25:
                if d[np.argmax(np.abs(d))] < 0:
                    d = -d
                foot = o - (o @ d) * d
                key = (tuple(np.round(foot, 1)), tuple(np.round(d, 3)), round(2 * r, 3))
                # axial extent in ABSOLUTE axial coordinates (along d from the
                # world origin), from the face's own vertices
                from OCP.TopExp import TopExp_Explorer as _E
                from OCP.TopAbs import TopAbs_VERTEX
                from OCP.BRep import BRep_Tool
                zs = []
                ev = _E(f, TopAbs_VERTEX)
                while ev.More():
                    pv = BRep_Tool.Pnt_s(TopoDS.Vertex_s(ev.Current())); zs.append(np.array([pv.X(), pv.Y(), pv.Z()]) @ d)
                    ev.Next()
                if len(zs) < 2:
                    bb = R5.VF.bbox(f)
                    zs = list(np.array([[x, y, zz] for x in bb[:, 0] for y in bb[:, 1] for zz in bb[:, 2]]) @ d)
                feats.setdefault(key, [foot, d, 2 * r, []])[3].append((min(zs), max(zs)))
        e.Next()
    out = []
    for k, (foot, d, D, ivs) in feats.items():
        # merge only intervals that actually adjoin: two pockets on either side
        # of a gap stay two features
        ivs.sort(); merged = [list(ivs[0])]
        for lo_, hi_ in ivs[1:]:
            if lo_ <= merged[-1][1] + 0.05:
                merged[-1][1] = max(merged[-1][1], hi_)
            else:
                merged.append([lo_, hi_])
        for lo_, hi_ in merged:
            out.append(dict(centre=foot + d * (lo_ + hi_) / 2, axis=d, dia=D, depth=hi_ - lo_, cls=classify(D)))
    return out


# ------------------------------------------------------------------ pages
def pose_pages(pdf, S, cols, cache):
    import build_final_assembly as BA_
    axes = joint_axes()
    meshes = {k: cache.setdefault(k, R5.tess(S[k], 0.05, 0.25)) for k in S}
    rows = []
    for name, th in POSES:
        G = body_frames(axes, th)
        pm = posed(meshes, G)
        pm.update(spring_meshes(G, cache))
        clr = pose_clearance(pm)
        worst = min(clr, key=lambda r: r[2])
        rows.append((name, th, worst))
        fig = plt.figure(figsize=(16.5, 11.7))
        fig.suptitle("Pose: %s   J1..J6 = %s deg" % (name, ", ".join("%+g" % t for t in th)), fontsize=14, fontweight="bold")
        views = (("isometric", (1, -1, 0.7)), ("side (from -y)", (0, -1, 0)), ("front (from +x)", (1, 0, 0)),
                 ("from above", (0.001, 0, 1)))
        allV = np.vstack([V for V, F in pm.values() if len(V)])
        fp = (allV.min(0) + allV.max(0)) / 2
        for i, (lab, d) in enumerate(views):
            png = os.path.join(OUT, "pose_%d_%d.png" % (POSES.index((name, th)), i))
            R5.vtk_render(pm, {**cols, **{k: "#8fc1e3" for k in pm if k.startswith("spring")}}, png,
                          (fp, np.asarray(d, float) / np.linalg.norm(d), (0, 0, 1) if i < 3 else (1, 0, 0)),
                          size=(1500, 1900))
            ax = fig.add_axes([0.005 + 0.25 * i, 0.12, 0.245, 0.80]); ax.imshow(R5.trimmed(png) if "R5" in globals() else trimmed(png), interpolation="none"); ax.axis("off")
            ax.set_title(lab, fontsize=10)
        body_n = ["ground", "turret", "upper link", "forearm", "J4 hub", "blade", "flange"]
        txt = "clearance between rigid bodies in this pose (FCL, exact-solid meshes; a joint's own bearing / servo / horn screws excluded):\n"
        txt += "   ".join("%s-%s %.2f" % (body_n[i], body_n[j], d) for i, j, d, _ in clr if j == i + 1)
        txt += "\nclosest non-neighbours: " + "   ".join("%s-%s %.1f" % (body_n[i], body_n[j], d)
                                                        for i, j, d, _ in sorted([r for r in clr if r[1] > r[0] + 1], key=lambda r: r[2])[:4])
        txt += "\nWORST: %s <-> %s  %.3f mm  (%s | %s)  -> %s" % (body_n[worst[0]], body_n[worst[1]], worst[2],
                                                                worst[3][0], worst[3][1],
                                                                "CLEAR" if worst[2] > 0.1 else "TOUCHING / COLLISION")
        fig.text(0.02, 0.015, txt, fontsize=8.5, family="monospace", va="bottom",
                 color="#006000" if worst[2] > 0.1 else "#b00000")
        pdf.savefig(fig, dpi=300); plt.close(fig)
        print("pose %-38s worst %.3f mm between bodies %d-%d (%s | %s)" % (name, worst[2], worst[0], worst[1], *worst[3]))
    return rows


def part_pages(pdf, parts, cols_fn=None):
    rows = []
    for idx, (nm, q, src, note) in enumerate(parts):
        sh = cq.importers.importStep(os.path.join(src, nm + ".step")).val().wrapped
        V, F = R5.tess(sh, 0.02, 0.12)
        col = R5.PRINTED_PALETTE[idx % len(R5.PRINTED_PALETTE)]
        mesh = {nm: (V, F)}
        fp = (V.min(0) + V.max(0)) / 2
        ext = V.max(0) - V.min(0)
        fig = plt.figure(figsize=(16.5, 11.7))
        fig.suptitle("Part %d of %d:  %s   (print %d)   %.0f x %.0f x %.0f mm" % (idx + 1, len(parts), nm, q, *ext),
                     fontsize=14, fontweight="bold")
        for i, (lab, d, up) in enumerate((("isometric", (1, -1, 0.8), (0, 0, 1)), ("isometric, from behind", (-1, 1, 0.8), (0, 0, 1)),
                                          ("front (-y)", (0.0, -1, 0.001), (0, 0, 1)), ("side (+x)", (1, 0.0, 0.001), (0, 0, 1)))):
            png = os.path.join(OUT, "part_%02d_%d.png" % (idx, i))
            R5.vtk_render(mesh, {nm: col}, png, (fp, np.asarray(d, float) / np.linalg.norm(d), up), size=(1400, 1050), zoom=0.95)
            ax = fig.add_axes([0.01 + 0.33 * (i % 2), 0.50 - 0.46 * (i // 2), 0.32, 0.42])
            ax.imshow(R5.trimmed(png) if "R5" in globals() else trimmed(png), interpolation="none"); ax.axis("off"); ax.set_title(lab, fontsize=10)
        feats = features(sh)
        summ = {}
        for f_ in feats:
            k = (f_["cls"], round(f_["dia"], 2))
            summ.setdefault(k, []).append(f_["depth"])
        tx = "%s\n\nfeatures found on its own faces\n(cylindrical holes, measured):\n\n" % note
        for (c, dd), deps in sorted(summ.items(), key=lambda kv: -kv[0][1]):
            tx += "  %2d x %-26s O%6.2f  %s\n" % (len(deps), c, dd, "depth %.1f" % np.median(deps))
        fig.text(0.68, 0.93, tx, fontsize=8, family="monospace", va="top")
        pdf.savefig(fig, dpi=300); plt.close(fig)
        # attention to detail: one close-up per feature class (largest first), up to 6
        pick, seen = [], set()
        # one per class: the DEEPEST instance (a bearing's seat, not its lead-in)
        for f_ in sorted(feats, key=lambda f: (-round(f["dia"]), -f["depth"])):
            if f_["cls"] not in seen:
                seen.add(f_["cls"]); pick.append(f_)
            if len(pick) == 6:
                break
        if pick:
            fig = plt.figure(figsize=(16.5, 11.7))
            fig.suptitle("%s -- attention to detail: section through each feature's axis (cut face darker), measured on the part's own faces" % nm,
                         fontsize=13, fontweight="bold")
            for i, f_ in enumerate(pick):
                d = f_["axis"]; perp = np.cross(d, [0, 0, 1.0])
                if np.linalg.norm(perp) < 0.1:
                    perp = np.cross(d, [1.0, 0, 0])
                perp /= np.linalg.norm(perp)
                # DETAIL SECTION: cut through the feature's own axis, cut face
                # filled, seen square-on -- diameter and depth read directly
                png = os.path.join(OUT, "detail_%02d_%d.png" % (idx, i))
                R5.vtk_render(mesh, {nm: col}, png, (f_["centre"], perp, d),
                              clip=(f_["centre"], -perp), size=(900, 900),
                              scale=max(0.75 * max(f_["dia"], f_["depth"]) + 2.0, 4.0))
                ax = fig.add_subplot(2, 3, i + 1); ax.imshow(R5.trimmed(png) if "R5" in globals() else trimmed(png), interpolation="none"); ax.axis("off")
                ax.set_title("%s\nO%.2f x %.1f deep  (%d on this part)" % (f_["cls"], f_["dia"], f_["depth"],
                             sum(1 for g in feats if g["cls"] == f_["cls"] and abs(g["dia"] - f_["dia"]) < 0.01)), fontsize=10)
            pdf.savefig(fig, dpi=300); plt.close(fig)
        rows.append((nm, len(feats)))
        print("part %-20s %3d hole features" % (nm, len(feats)))
    return rows


def main():
    from matplotlib.backends.backend_pdf import PdfPages
    import make_final_print as MF
    os.makedirs(OUT, exist_ok=True)
    S = R5.load(); cols = R5.colours(S); cache = {}
    with PdfPages(os.path.join(HERE, "ARM450_POSES.pdf")) as pdf:
        pose_pages(pdf, S, cols, cache)
    with PdfPages(os.path.join(HERE, "ARM450_PARTS.pdf")) as pdf:
        part_pages(pdf, MF.PARTS)
    print("written ARM450_POSES.pdf, ARM450_PARTS.pdf")


if __name__ == "__main__":
    main()
