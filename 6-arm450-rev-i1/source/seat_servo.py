#!/usr/bin/env python3
"""
Seat the REAL ST3215 in a generated fork half and measure the result.

Every number here is measured from the meshes. The traps this walked into,
each of which produced a wrong answer earlier, are guarded:

  * The horn disc centre must come from a slab that contains ONLY the disc.
    A slab 2 mm up already includes the O40 shoulder and reports a centre
    0.368 mm off, which then shifts the whole servo.
  * rotation_matrix(+pi/2,[1,0,0]) maps +Y -> +Z. The horn is at mesh +Y and
    must end at -Z (pointing down through the floor), so the angle is -pi/2.
  * contains() == False also means "outside the part", so the pinch result is
    cross-checked against positive and negative controls.
"""
import sys
import os

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import servo_geom as SG        # noqa: E402

MOTOR = SG.MOTOR_STL


def servo_in_joint_frame():
    """ST3215 with its output axis on +Z->-Z and the horn axis at (0,0).

    Returns (mesh, z_face) where z_face is the local z of the mounting face.
    """
    m = trimesh.load(MOTOR)
    m.apply_translation(-m.bounds.mean(axis=0))
    # horn at mesh +Y must point to -Z
    m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2,
                                                              [1, 0, 0]))
    zmin = m.bounds[0][2]
    # --- horn centre from a slab that is ONLY the disc --------------------
    cx = cy = None
    for dz in (0.3, 0.8, 1.3):
        sl = m.section(plane_origin=[0, 0, zmin + dz], plane_normal=[0, 0, 1])
        if sl is None:
            continue
        v = np.asarray(sl.vertices)
        if abs(np.ptp(v[:, 0]) - SG.HORN_DISC_D) > 0.4:
            continue                      # contaminated by the shoulder
        cx = (v[:, 0].max() + v[:, 0].min()) / 2
        cy = (v[:, 1].max() + v[:, 1].min()) / 2
        break
    if cx is None:
        raise RuntimeError("no clean horn-disc slab found")
    # --- mounting face: first slab at full case length --------------------
    z_face = None
    for z in np.linspace(zmin, zmin + 8.0, 400):
        sl = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if sl is None:
            continue
        if np.ptp(np.asarray(sl.vertices)[:, 0]) > SG.CASE_L - 0.6:
            z_face = z
            break
    if z_face is None:
        raise RuntimeError("mounting face not found")
    m.apply_translation([-cx, -cy, 0.0])
    return m, z_face - 0.0


def seat(jn, z_floor, n=40000):
    srv, z_face = servo_in_joint_frame()
    srv.apply_translation([0, 0, z_floor - z_face])
    host = trimesh.load(os.path.join(HERE, "%s_p2.stl" % jn))
    bb = srv.bounds

    # horn axis, re-measured after placement
    zmin = bb[0][2]
    sl = srv.section(plane_origin=[0, 0, zmin + 0.8], plane_normal=[0, 0, 1])
    v = np.asarray(sl.vertices)
    hx = (v[:, 0].max() + v[:, 0].min()) / 2
    hy = (v[:, 1].max() + v[:, 1].min()) / 2

    P = srv.sample(n)
    ins = host.contains(P)
    c = P[ins]
    out = dict(
        joint=jn, z0=bb[0][2], z1=bb[1][2],
        floor=z_floor, top=z_floor + SG.BAY_T_Z,
        horn_off=float(np.hypot(hx, hy)),
        horn_below=bool(bb[0][2] < z_floor),
        back_ok=bool(bb[1][2] <= z_floor + SG.BAY_T_Z + 0.01),
        n_contact=int(ins.sum()), n=n,
    )
    if ins.sum():
        out["pen"] = float(np.abs(c[:, 1]).max() - SG.PINCH / 2)
        out["contact_y_min"] = float(np.abs(c[:, 1]).min())
        out["contact_x"] = (float(c[:, 0].min()), float(c[:, 0].max()))
    return out, srv, host


def controls(jn, z_floor):
    """The seating test must read clean at nominal and detect a real clash."""
    srv, z_face = servo_in_joint_frame()
    host = trimesh.load(os.path.join(HERE, "%s_p2.stl" % jn))
    res = {}
    for label, d in (("nominal", (0, 0, 0)),
                     ("+6 into back wall", (0, 0, 6.0)),
                     ("-14 into -X wall", (-14.0, 0, 0)),
                     ("+9 into +Y wall", (0, 9.0, 0))):
        s = srv.copy()
        s.apply_translation([d[0], d[1], z_floor - z_face + d[2]])
        res[label] = int(host.contains(s.sample(8000)).sum())
    return res


if __name__ == "__main__":
    # J5 withdrawn -- see WITHDRAWN/README.md
    for jn, zf in (("J3", 28.50),):
        r, _, _ = seat(jn, zf)
        print("%s" % jn)
        print("   horn offset from joint axis   %.4f mm" % r["horn_off"])
        print("   servo z %.2f .. %.2f   bay %.2f .. %.2f"
              % (r["z0"], r["z1"], r["floor"], r["top"]))
        print("   horn through floor            %s" % r["horn_below"])
        print("   back of case inside bay       %s" % r["back_ok"])
        print("   contact %d / %d" % (r["n_contact"], r["n"]))
        if r["n_contact"]:
            print("   pinch penetration             %.3f mm per side" % r["pen"])
            print("   nearest contact to centreline |y| %.3f" % r["contact_y_min"])
            print("   contact x span                %.2f .. %.2f" % r["contact_x"])
        print("   controls:", controls(jn, zf))
        print()
