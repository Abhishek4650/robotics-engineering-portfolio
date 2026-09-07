"""
Isometric dimensioned drawings — the pictorial sheet style, built from the real
STL geometry rather than sketched.

Three pieces:
  1. ISOMETRIC PROJECTION      standard 30 deg, +Z up, view along (1,1,1)
  2. HIDDEN-LINE REMOVAL       z-buffer rasterisation, so only visible edges draw
  3. DIMENSION PRIMITIVES      extension lines, arrow-terminated dimension lines
                               with text rotated to lie along the line, plus
                               leader-style Ø and R callouts

Every number on a sheet comes from cad/params.py or is measured off the mesh, so
a drawing cannot disagree with the part it describes.
"""
import numpy as np

# --- 1. projection ---------------------------------------------------------
C30, S30 = np.cos(np.pi / 6), np.sin(np.pi / 6)
VIEW = np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0)


def iso(p):
    """(...,3) world -> (...,2) sheet. +Z up, +X down-right, +Y down-left."""
    p = np.asarray(p, float)
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    return np.stack([(x - y) * C30, z - (x + y) * S30], axis=-1)


def depth(p):
    """Distance along the view axis. Larger = nearer the viewer."""
    return np.asarray(p, float) @ VIEW


# --- 2. hidden-line removal ------------------------------------------------
class ZBuffer:
    """Rasterise the projected mesh once, then query edge visibility cheaply."""

    def __init__(self, mesh, px=1400, pad=0.02):
        v2 = iso(mesh.vertices)
        vd = depth(mesh.vertices)
        lo, hi = v2.min(axis=0), v2.max(axis=0)
        span = (hi - lo).max()
        lo = lo - span * pad
        span = span * (1 + 2 * pad)
        self.lo, self.span, self.px = lo, span, px
        self.buf = np.full((px, px), -1e18)

        tri = v2[mesh.faces]                       # (F,3,2)
        trd = vd[mesh.faces]                       # (F,3)
        g = (tri - lo) / span * (px - 1)
        # bounding box per triangle, rasterise with barycentric coords
        for k in range(len(g)):
            a, b, c = g[k]
            d0, d1, d2 = trd[k]
            x0 = max(int(np.floor(min(a[0], b[0], c[0]))), 0)
            x1 = min(int(np.ceil(max(a[0], b[0], c[0]))), px - 1)
            y0 = max(int(np.floor(min(a[1], b[1], c[1]))), 0)
            y1 = min(int(np.ceil(max(a[1], b[1], c[1]))), px - 1)
            if x1 < x0 or y1 < y0:
                continue
            xs = np.arange(x0, x1 + 1)
            ys = np.arange(y0, y1 + 1)
            X, Y = np.meshgrid(xs, ys)
            den = ((b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1]))
            if abs(den) < 1e-12:
                continue
            w0 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den
            w1 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den
            w2 = 1.0 - w0 - w1
            m = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
            if not m.any():
                continue
            dd = w0 * d0 + w1 * d1 + w2 * d2
            sub = self.buf[Y[m], X[m]]
            keep = dd[m] > sub
            yy, xx = Y[m][keep], X[m][keep]
            self.buf[yy, xx] = dd[m][keep]

    def visible(self, pts3, bias=None):
        """Boolean per 3-D point: is it in front of what the buffer holds?"""
        p2 = iso(pts3)
        d = depth(pts3)
        g = np.rint((p2 - self.lo) / self.span * (self.px - 1)).astype(int)
        g = np.clip(g, 0, self.px - 1)
        if bias is None:
            # Generous on purpose. A silhouette edge sits exactly on the surface
            # it bounds, so a tight bias makes the outline break into dashes.
            bias = self.span / self.px * 4.0
        return d >= self.buf[g[:, 1], g[:, 0]] - bias


def feature_edges(mesh, sharp_deg=22.0, want_flags=False):
    """Edges worth drawing: sharp creases, silhouettes and open boundaries.

    With want_flags, also returns which of them are SILHOUETTE edges. Those need
    separate treatment: a silhouette lies exactly on the surface it bounds, so a
    plain depth test against the z-buffer is a coin flip and the outline comes
    out dashed."""
    eu = mesh.edges_unique
    fa = mesh.face_adjacency
    fae = mesh.face_adjacency_edges
    n = mesh.face_normals
    keep = set()
    sil = set()
    ang = mesh.face_adjacency_angles
    for k, (i, j) in enumerate(fa):
        e = tuple(sorted(fae[k]))
        if (n[i] @ VIEW) * (n[j] @ VIEW) < 0:      # silhouette
            keep.add(e)
            sil.add(e)
            continue
        if np.degrees(ang[k]) >= sharp_deg:
            keep.add(e)
    # open boundaries
    cnt = {}
    for f in mesh.faces:
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            cnt[tuple(sorted((a, b)))] = cnt.get(tuple(sorted((a, b))), 0) + 1
    for e, c in cnt.items():
        if c == 1:
            keep.add(e)
    _ = eu
    order = sorted(keep)
    arr = np.array(order, dtype=int)
    if want_flags:
        return arr, np.array([e in sil for e in order], dtype=bool)
    return arr


def visible_segments(mesh, zb, edges, samples=20, sil=None):
    """Split each edge into the runs that are actually visible.

    A silhouette edge is decided ALL-OR-NOTHING from its midpoint, not sampled
    along its length. Per-sample testing is what produced dashed outlines: along
    a silhouette the surface is nearly tangent to the view, so rasterised depth
    swings steeply within one pixel and samples flicker in and out. Silhouette
    edges are only one facet long, so judging each by its midpoint gives a clean
    continuous outline and still hides an edge that is genuinely behind material.

    (Nudging silhouette samples toward the viewer in 3-D was tried first and is
    wrong: it lifted the tube's HIDDEN inner-bore silhouette into view in
    patches, which is what produced the broken diagonal lines across the shaft.)"""
    V = mesh.vertices
    out = []
    big = mesh.extents.max() * 0.010
    for idx, (a, b) in enumerate(edges):
        p0, p1 = V[a], V[b]
        if sil is not None and sil[idx]:
            mid = ((p0 + p1) / 2)[None, :]
            if zb.visible(mid, bias=big)[0]:
                out.append((p0, p1))
            continue
        t = np.linspace(0, 1, samples)[:, None]
        pts = p0 * (1 - t) + p1 * t
        vis = zb.visible(pts)
        run = None
        for k, ok in enumerate(vis):
            if ok and run is None:
                run = k
            elif not ok and run is not None:
                if k - run > 1:
                    out.append((pts[run], pts[k - 1]))
                run = None
        if run is not None and samples - run > 1:
            out.append((pts[run], pts[-1]))
    return out


# --- 3. dimension primitives ----------------------------------------------
import matplotlib.pyplot as _plt
from matplotlib.collections import LineCollection as _LC
from matplotlib.patches import Polygon as _Poly

INK = "#12202e"        # part outline
DIMC = "#1b4f72"       # dimension lines and text
NOTEC = "#7d4b12"      # notes / callouts


def _ang(d):
    """Text angle in degrees for a projected direction, kept readable."""
    a = np.degrees(np.arctan2(d[1], d[0]))
    if a > 90:
        a -= 180
    if a < -90:
        a += 180
    return a


class Sheet:
    """One isometric drawing: the part, then dimensions added on top."""

    def __init__(self, ax, mesh, px=1300, sharp=22.0, lw=0.8):
        self.ax = ax
        m = mesh.copy()
        self.mesh = m
        self.zb = ZBuffer(m, px=px)
        ed, sil = feature_edges(m, sharp, want_flags=True)
        segs = visible_segments(m, self.zb, ed, sil=sil)
        ax.add_collection(_LC([(iso(a), iso(b)) for a, b in segs],
                              colors=INK, linewidths=lw, capstyle="round"))
        s = m.extents.max()
        self.s = s
        # Remember where the PART is, so the sheet can be balanced around the
        # object rather than around the annotation. Long leaders on one side
        # otherwise drag the autoscale box off and the part sits off-centre.
        _p2 = iso(m.vertices)
        ax._part_box = (_p2.min(axis=0), _p2.max(axis=0))
        self.tick = s * 0.018          # arrowhead length
        self.fs = 8.4
        ax.set_aspect("equal")
        ax.axis("off")

    # -- helpers ------------------------------------------------------------
    def _arrow(self, tip2, dir2, color=DIMC):
        d = dir2 / (np.linalg.norm(dir2) + 1e-12)
        n = np.array([-d[1], d[0]])
        L, W = self.tick, self.tick * 0.32
        self.ax.add_patch(_Poly([tip2, tip2 - d * L + n * W, tip2 - d * L - n * W],
                                closed=True, facecolor=color, edgecolor="none",
                                zorder=5))

    def _line(self, a2, b2, color=DIMC, lw=0.6, ls="-"):
        self.ax.plot([a2[0], b2[0]], [a2[1], b2[1]], color=color, lw=lw,
                     ls=ls, solid_capstyle="butt", zorder=4)

    def _text(self, p2, txt, rot, color=DIMC, fs=None, ha="center", va="center"):
        self.ax.text(p2[0], p2[1], txt, rotation=rot, ha=ha, va=va,
                     fontsize=fs or self.fs, color=color, zorder=6,
                     rotation_mode="anchor",
                     bbox=dict(boxstyle="round,pad=0.13", fc="white",
                               ec="none", alpha=0.92))

    # -- public -------------------------------------------------------------
    def dim(self, p0, p1, off, text=None, gap=0.20, ext=0.14, fs=None,
            fmt="{:.2f}", flip=False):
        """Aligned linear dimension. `off` is a 3-D direction to offset by;
        its length scales with the part so sheets stay consistent."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        o = np.asarray(off, float)
        o = o / (np.linalg.norm(o) + 1e-12) * self.s * gap
        a2, b2 = iso(p0), iso(p1)
        A2, B2 = iso(p0 + o), iso(p1 + o)
        e = (np.asarray(iso(p0 + o * (1 + ext))) - A2)
        # extension lines, with the customary small gap off the part
        for base, top, far in ((a2, A2, e), (b2, B2, e)):
            d = top - base
            n = np.linalg.norm(d)
            if n > 1e-9:
                st = base + d / n * (self.s * 0.012)
                self._line(st, top + far * 0.28, lw=0.5)
        self._line(A2, B2)
        d2 = B2 - A2
        self._arrow(A2, -d2)
        self._arrow(B2, d2)
        val = np.linalg.norm(p1 - p0)
        t = text if text is not None else fmt.format(val)
        mid = (A2 + B2) / 2
        nrm = np.array([-d2[1], d2[0]])
        nrm = nrm / (np.linalg.norm(nrm) + 1e-12)
        self._text(mid + nrm * self.s * (0.030 if not flip else -0.030), t,
                   _ang(d2), fs=fs)
        return self

    def leader(self, p3, text, out, color=NOTEC, fs=None, ha=None):
        """Callout with a leader: arrow at the feature, short shoulder, text."""
        p3 = np.asarray(p3, float)
        o = np.asarray(out, float)
        o = o / (np.linalg.norm(o) + 1e-12) * self.s * 0.22
        a2, b2 = iso(p3), iso(p3 + o)
        sh = np.array([np.sign(b2[0] - a2[0]) or 1.0, 0.0]) * self.s * 0.07
        c2 = b2 + sh
        self._line(a2, b2, color=color, lw=0.6)
        self._line(b2, c2, color=color, lw=0.6)
        self._arrow(a2, a2 - b2, color=color)
        h = ha or ("left" if sh[0] > 0 else "right")
        pad = self.s * 0.015 * (1 if sh[0] > 0 else -1)
        self._text(c2 + np.array([pad, 0]), text, 0, color=color, fs=fs, ha=h)
        return self

    def dia(self, center, radius, axis, out, fmt="Ø{:.2f}", text=None, fs=None):
        """Diameter callout: arrow lands on the circle, like a real drawing."""
        c = np.asarray(center, float)
        a = np.asarray(axis, float)
        a = a / np.linalg.norm(a)
        r = np.asarray(out, float)
        r = r - a * (r @ a)
        r = r / (np.linalg.norm(r) + 1e-12)
        self.leader(c + r * radius, text or fmt.format(2 * radius), out,
                    fs=fs)
        return self

    def rad(self, center, radius, axis, out, fmt="R{:.2f}", text=None, fs=None):
        return self.dia(center, radius, axis, out, text=text or fmt.format(radius),
                        fs=fs)

    def title(self, name, sub=""):
        self.ax.set_title(name, fontsize=11.5, color=INK, fontweight="bold",
                          pad=14)
        if sub:
            self.ax.text(0.5, 1.005, sub, transform=self.ax.transAxes,
                         ha="center", va="bottom", fontsize=8.2, color="#5b6b7a")
        return self
