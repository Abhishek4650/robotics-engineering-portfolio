"""
Orthographic three-view sheets — FRONT, TOP, RIGHT — with hidden-line detail.

Third-angle projection:

        TOP
         |
    FRONT --- RIGHT

Visible edges draw solid, hidden edges dashed, which is the whole point: the
bearing pockets, blind insert holes and internal webs of these parts are exactly
the features you cannot see from outside, and they are what the audit is about.

Axes per view (u = page right, v = page up, w = toward the viewer):
    FRONT   u=+X  v=+Z  w=-Y
    TOP     u=+X  v=+Y  w=+Z
    RIGHT   u=+Y  v=+Z  w=+X
"""
import numpy as np
from matplotlib.collections import LineCollection

INK, HID, DIMC = "#12202e", "#7c8b99", "#1b4f72"

VIEWS = {
    "FRONT": (np.array([1., 0, 0]), np.array([0, 0, 1.]), np.array([0, -1., 0])),
    "TOP":   (np.array([1., 0, 0]), np.array([0, 1., 0]), np.array([0, 0, 1.])),
    "RIGHT": (np.array([0, 1., 0]), np.array([0, 0, 1.]), np.array([1., 0, 0])),
}


class OrthoView:
    """Project, depth-sort and split edges into visible and hidden runs."""

    def __init__(self, mesh, name, px=1000):
        self.u, self.v, self.w = VIEWS[name]
        self.name = name
        self.m = mesh
        V = mesh.vertices
        p2 = self.proj(V)
        d = V @ self.w
        lo, hi = p2.min(axis=0), p2.max(axis=0)
        span = (hi - lo).max() * 1.02
        self.lo, self.span, self.px = lo - span * 0.01, span, px
        self.buf = np.full((px, px), -1e18)
        g = (p2 - self.lo) / self.span * (px - 1)
        for tri, dep in zip(g[mesh.faces], d[mesh.faces]):
            a, b, c = tri
            x0 = max(int(np.floor(min(a[0], b[0], c[0]))), 0)
            x1 = min(int(np.ceil(max(a[0], b[0], c[0]))), px - 1)
            y0 = max(int(np.floor(min(a[1], b[1], c[1]))), 0)
            y1 = min(int(np.ceil(max(a[1], b[1], c[1]))), px - 1)
            if x1 < x0 or y1 < y0:
                continue
            X, Y = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            den = ((b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1]))
            if abs(den) < 1e-12:
                continue
            w0 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den
            w1 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den
            w2 = 1.0 - w0 - w1
            msk = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
            if not msk.any():
                continue
            dd = w0 * dep[0] + w1 * dep[1] + w2 * dep[2]
            yy, xx, vv = Y[msk], X[msk], dd[msk]
            keep = vv > self.buf[yy, xx]
            self.buf[yy[keep], xx[keep]] = vv[keep]

    def proj(self, p):
        p = np.asarray(p, float)
        return np.stack([p @ self.u, p @ self.v], axis=-1)

    def visible(self, pts, bias):
        p2 = self.proj(pts)
        d = np.asarray(pts, float) @ self.w
        g = np.clip(np.rint((p2 - self.lo) / self.span * (self.px - 1)).astype(int),
                    0, self.px - 1)
        return d >= self.buf[g[:, 1], g[:, 0]] - bias

    def edges(self, sharp_deg=20.0, samples=16):
        """Return (visible_segments, hidden_segments) in page coordinates."""
        m = self.m
        n = m.face_normals
        fa, fae = m.face_adjacency, m.face_adjacency_edges
        ang = m.face_adjacency_angles
        keep, sil = {}, set()
        for k, (i, j) in enumerate(fa):
            e = tuple(sorted(fae[k]))
            if (n[i] @ self.w) * (n[j] @ self.w) < 0:
                keep[e] = True
                sil.add(e)
            elif np.degrees(ang[k]) >= sharp_deg:
                keep[e] = True
        V = m.vertices
        tol = m.extents.max() * 0.004
        big = m.extents.max() * 0.010
        vis, hid = [], []
        for e in keep:
            p0, p1 = V[e[0]], V[e[1]]
            if e in sil:
                mid = ((p0 + p1) / 2)[None, :]
                (vis if self.visible(mid, big)[0] else hid).append(
                    (self.proj(p0), self.proj(p1)))
                continue
            t = np.linspace(0, 1, samples)[:, None]
            pts = p0 * (1 - t) + p1 * t
            ok = self.visible(pts, tol)
            run, state = 0, ok[0]
            for k in range(1, samples):
                if ok[k] != state:
                    seg = (self.proj(pts[run]), self.proj(pts[k - 1]))
                    (vis if state else hid).append(seg)
                    run, state = k, ok[k]
            seg = (self.proj(pts[run]), self.proj(pts[-1]))
            (vis if state else hid).append(seg)
        return vis, hid


def draw_view(ax, mesh, name, origin=(0.0, 0.0), px=1000, show_hidden=True):
    """Draw one orthographic view, returning its page-space bounding box."""
    ov = OrthoView(mesh, name, px=px)
    vis, hid = ov.edges()
    off = np.array(origin, float)
    if show_hidden and hid:
        ax.add_collection(LineCollection([(a + off, b + off) for a, b in hid],
                                         colors=HID, linewidths=0.45,
                                         linestyles=(0, (3.2, 2.4))))
    ax.add_collection(LineCollection([(a + off, b + off) for a, b in vis],
                                     colors=INK, linewidths=0.95))
    p2 = ov.proj(mesh.vertices)
    return p2.min(axis=0) + off, p2.max(axis=0) + off
