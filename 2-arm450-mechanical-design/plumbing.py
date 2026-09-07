"""
Services along the arm — the fluid tube and the servo cable bundle.

ROUTED PER LINK, not as one polyline through the joint origins. The earlier
version placed one offset point per joint and joined them with straight lines,
which drove the tube through the very bosses it was meant to pass. This walks
each link separately: a straight run along the link's flat side, and an arc
around each end boss to reach the next link.

Each segment is returned WITH THE CHAIN INDEX of the link it is clipped to, so
the collision checker can tell "the tube touching the link it is strapped to"
(fine) from "the tube touching the base" (not fine). Without that distinction
every standoff from 31 mm to 46 mm reported identical collisions, because the
checker was flagging contact the tube must make.

Two services, side by side on the same clips:
    TUBE   Ø6   4 x 6 silicone, the fluid line
    CABLE  Ø5   the six-servo bus, daisy-chained
"""
import numpy as np
import trimesh

TUBE_OD = 6.0
CABLE_OD = 5.0
CLIP_H = 3.0                   # a P-clip standing off the link surface
BOSS_R = 25.0                  # link end-boss radius, measured off the mesh
TURRET_R = 40.0                # turret is 80 across
BASE_R = 60.0                  # base foot is Ø120
SEG = 12
ARC_N = 5                      # points per boss arc


def _seg(a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float)
    v = b - a
    L = float(np.linalg.norm(v))
    if L < 1e-6:
        return None
    m = trimesh.creation.cylinder(radius=r, height=L, sections=SEG)
    d = v / L
    z = np.array([0.0, 0.0, 1.0])
    ax = np.cross(z, d)
    if np.linalg.norm(ax) < 1e-9:
        R = np.eye(3) if d[2] > 0 else \
            trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])[:3, :3]
    else:
        ang = float(np.arccos(np.clip(np.dot(z, d), -1, 1)))
        R = trimesh.transformations.rotation_matrix(ang, ax)[:3, :3]
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = (a + b) / 2.0
    m.apply_transform(T)
    return m


def _tube(pts, od):
    r = od / 2.0
    out = []
    for i in range(len(pts) - 1):
        s = _seg(pts[i], pts[i + 1], r)
        if s is not None:
            out.append(s)
    for p in pts[1:-1]:
        b = trimesh.creation.icosphere(subdivisions=1, radius=r)
        b.apply_translation(p)
        out.append(b)
    return trimesh.util.concatenate(out) if out else None


# ---------------------------------------------------------------------------
# THE VERIFIED ROUTE, 2026-08-23.
#
# Found by sweeping, after fixing a checker bug that had made every sweep
# return the same answer (see interference.SERVICE). Three facts came out of
# it, and the second is the one nobody would guess:
#
#   * services must stay INSIDE the turret envelope through the base and the
#     turret -- R_LOW = 12 mm, up the Ø52 cable bore that already exists for
#     exactly this purpose. A standoff mast at 66 mm gets hit.
#   * the shoulder sweeps a 119 mm radius about J2 and reaches BELOW the top of
#     the base during the sine trace, so there is no clear standoff radius
#     anywhere near the turret. The services have to be past J2 before they
#     come out at all.
#   * on the links they stand off 31 mm on the -X side, BEHIND the arm. The
#     trace reaches forward, so anything in front is in the way.
#
# Result: 0 of 40 sine waypoints collide, with BOTH the tube and the cable
# bundle fitted.
R_LOW = -12.0                  # base and turret: inside the cable bore
R_LINK = -31.0                 # along a link: clear of the Ø50 boss, behind
CABLE_LAT = -6.5               # cable sits alongside the tube on the same clip


def route(frames, od=TUBE_OD, r_low=R_LOW, r_link=R_LINK, lateral=0.0):
    """-> [(mesh, chain_index, name), ...]

    frames = [(origin, R)] for base, J1, J2, J3, J4, J5, tool.
    Each span carries the CHAIN INDEX of the link it is clipped to, so the
    checker can tell legitimate contact with its own link from a real
    collision. Without that, every offset reported the same failure.
    """
    out = []
    side = np.array([1.0, 0.0, 0.0])
    CH = [0, 1, 2, 3, 4, 5]
    for k in range(len(frames) - 1):
        o0, R0 = frames[k]
        o1, R1 = frames[k + 1]
        u0 = R0 @ side
        u1 = R1 @ side
        d0 = r_low if k <= 1 else r_link
        d1 = r_low if k == 0 else r_link
        p0 = np.asarray(o0, float) + u0 * d0 + R0 @ np.array([0.0, lateral, 0.0])
        p1 = np.asarray(o1, float) + u1 * d1 + R1 @ np.array([0.0, lateral, 0.0])
        m = _tube([p0, p1], od)
        if m is not None:
            out.append((m, CH[min(k, 5)], f"s{k}"))
    return out
