#!/usr/bin/env python3
"""Rule 8 pictures: (1) clearance of the screw heads the user asked about vs
joint angle, working range shaded; (2) the bus cable route through every
joint, drawn on the arm in two poses (straight spans from exit to exit; the
loop to leave at each joint is in CABLE_ROUTE.log)."""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                 # noqa: E402
import trimesh                                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "RULE6_VIEWS")
BEFORE = {"j3fork_link_0": "before: 1.28 mm at 72 deg, touching at 81 deg (heads on the floor)",
          "j5fork_j4hub_0": "before: 4.30 mm, touching at 100 deg",
          "cap_J4_0": "before: 0.80 mm (counterbore 3.3 deep)", "cap_J6_0": "before: 0.80 mm (counterbore 3.3 deep)"}


def head_plot():
    C = json.load(open(os.path.join(HERE, "HEAD_CLEARANCE.json")))
    want = [("J3", 3, "j3fork_link_0", "J3 fork floor bolt heads vs the forearm (4 alike)"),
            ("J5", 5, "j5fork_j4hub_0", "J5 fork floor bolt heads vs the blade (4 alike)"),
            ("J4", 4, "cap_J4_0", "J4 cap bolt heads vs the J4 hub flange"),
            ("J6", 6, "cap_J6_0", "J6 cap bolt heads vs the tool flange")]
    fig, axs = plt.subplots(2, 2, figsize=(16.5, 11.0))
    for ax, (jn, k, s, ttl) in zip(axs.ravel(), want):
        c = next((x for x in C if x["joint"] == k and x["screw"] == s), None)
        if c is None:
            ax.set_title(ttl + " (no data)"); continue
        a, d, R = np.array(c["angles"]), np.array(c["dist"]), c["range"]
        ax.axvspan(-R, R, color="#d9f2d9", zorder=0, label="working range +-%.1f deg" % R)
        ax.plot(a, np.clip(d, 0, None), color="#1f4e99", lw=1.6, label="clearance (mm)")
        ax.axhline(1.0, color="#b00000", lw=0.8, ls="--", label="1.0 mm minimum")
        inr = np.abs(a) <= R
        i = int(np.argmin(np.where(inr, d, 1e9)))
        ax.plot(a[i], d[i], "o", color="#b00000")
        ax.annotate("%.2f mm at %+.0f deg" % (d[i], a[i]), (a[i], d[i]), xytext=(10, 18), textcoords="offset points",
                    fontsize=9, arrowprops=dict(arrowstyle="-", lw=0.6))
        t = [x for x, y in zip(a, d) if y <= 0]
        if t:
            pos = [x for x in t if x >= 0]; neg = [x for x in t if x <= 0]
            txt = "would touch at %s / %s" % ("%+.0f" % max(neg) if neg else "never", "%+.0f deg" % min(pos) if pos else "never")
        else:
            txt = "never touches in +-180 deg"
        ax.set_title("%s\n%s   |   %s" % (ttl, txt, BEFORE.get(s, "")), fontsize=9.5)
        ax.set_xlim(-180, 180); ax.set_ylim(0, max(12, min(40, d.max() * 1.05)))
        ax.set_xlabel("joint angle (deg)"); ax.set_ylabel("head clearance (mm)"); ax.grid(True, lw=0.3)
        ax.legend(fontsize=8, loc="upper right")
    fig.suptitle("Screw heads beside a turning part: clearance vs joint angle (each joint alone, exact solids)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    p = os.path.join(OUT, "head_clearance.png"); fig.savefig(p, dpi=200); fig.savefig(p[:-4] + ".pdf"); plt.close(fig)
    return p


def cable_pictures():
    import make_rule5_views as R5
    import make_rule6_pages as R6
    import make_audit_views as MV
    import cable_route as CR
    import verify_fasteners as VF
    A, _ = R6.BA.build()
    S = {c.name: (VF.world(c), c) for c in A.children if VF.world(c) is not None}
    meshes = {k: R5.tess(v[0], 0.1, 0.3) for k, v in S.items()}
    axes = R6.joint_axes()
    E = {k: (MV.seat_T(S, k) @ np.append(CR.exit_point(k), 1.0))[:3] for k in range(1, 7)}
    body_of_servo = {k: R6.body("servo_J%d" % k) for k in range(1, 7)}
    cols = R5.colours(meshes.keys())
    pngs = []
    for tag, th in (("home", (0, 0, 0, 0, 0, 0)), ("folded", (60, -40, 65, 80, -40, 0))):
        G = R6.body_frames(axes, th)
        M = {}
        for nm, (V, F) in meshes.items():
            b = R6.body(nm)
            if b is None:
                continue
            V2 = (G[b][:3, :3] @ V.T).T + G[b][:3, 3]
            M[nm] = (V2, F)
        c2 = dict(cols)
        for k in range(1, 6):
            a = G[body_of_servo[k]] @ np.append(E[k], 1.0)
            b = G[body_of_servo[k + 1]] @ np.append(E[k + 1], 1.0)
            seg = trimesh.creation.cylinder(radius=1.6, segment=[a[:3], b[:3]], sections=16)
            M["cable_%d" % k] = (np.asarray(seg.vertices), np.asarray(seg.faces))
            c2["cable_%d" % k] = "#ffd000"
        p = os.path.join(OUT, "cable_route_%s.png" % tag)
        R5.vtk_render(M, c2, p, ((0, 0, 220), (0.8, -1.0, 0.45), (0, 0, 1)), size=(1800, 2400), zoom=1.2)
        pngs.append(p)
    return pngs




def cable_schematic():
    """How the bus cables connect: the daisy chain, the one joint each cable
    crosses, and the loop / length for it (numbers from CABLE_ROUTE.log)."""
    import re
    rows = {}
    for ln in open(os.path.join(HERE, "CABLE_ROUTE.log")):
        m = re.match(r"\s*J(\d) -> J(\d)\s+J\d\s+\+-([\d.]+)\s+([\d.]+) mm.*?([\d.]+) \.\. ([\d.]+)\s+([\d.]+) mm\s+(\d+) / (\d+) mm", ln)
        if m:
            rows[int(m.group(1))] = m.groups()
    body = ["foot (ground)", "turret", "upper link", "forearm", "J4 hub + J5 fork", "blade"]
    joint = ["J1 base yaw", "J2 shoulder", "J3 elbow", "J4 forearm roll", "J5 wrist pitch", "J6 tool roll"]
    fig, ax = plt.subplots(figsize=(11.7, 16.5)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(-0.5, 13.5)
    ax.text(5, 13.1, "ARM-450 bus cables: a daisy chain, ONE joint per cable", ha="center", fontsize=15, fontweight="bold")
    ax.text(5, 12.6, "controller -> J1 -> J2 -> J3 -> J4 -> J5 -> J6 (each ST3215 has an IN and an OUT socket)",
            ha="center", fontsize=10)
    y = 11.6
    ax.add_patch(plt.Rectangle((0.6, y - 0.35), 2.6, 0.7, fc="#dddddd", ec="k"))
    ax.text(1.9, y, "controller\n(on the table)", ha="center", va="center", fontsize=9)
    ax.annotate("", xy=(4.0, y), xytext=(3.2, y), arrowprops=dict(arrowstyle="->", lw=1.5, color="#c8a000"))
    ax.text(3.6, y + 0.25, "no joint", ha="center", fontsize=8)
    for k in range(1, 7):
        yk = y - (k - 1) * 1.85
        ax.add_patch(plt.Rectangle((4.0, yk - 0.4), 3.2, 0.8, fc="#2b2b2b", ec="k"))
        ax.text(5.6, yk + 0.1, "servo J%d" % k, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        ax.text(5.6, yk - 0.22, "fixed to the %s" % body[k - 1], ha="center", va="center", color="white", fontsize=8)
        if k < 6:
            r = rows.get(k)
            ax.add_patch(plt.Circle((5.6, yk - 0.93), 0.22, fc="white", ec="#0050ff", lw=1.5))
            ax.text(5.6, yk - 0.93, "J%d" % k, ha="center", va="center", fontsize=7, color="#0050ff")
            ax.text(5.95, yk - 0.93, "%s  (servo J%d's own output axis)" % (joint[k - 1], k), fontsize=8, va="center",
                    color="#0050ff")
            ax.annotate("", xy=(3.9, yk - 1.45), xytext=(3.9, yk - 0.3),
                        arrowprops=dict(arrowstyle="->", lw=2.0, color="#c8a000", connectionstyle="arc3,rad=-0.5"))
            if r:
                ax.text(0.2, yk - 0.9, "cable J%d -> J%d crosses %s (+-%s deg)\nleaves J%d %s mm from that axis\n"
                        "path changes %s mm over the range\nloop %s mm, cable >= %s mm"
                        % (k, k + 1, joint[k - 1].split()[0], r[2], k, r[3], r[6], r[7], r[8]),
                        fontsize=8.5, va="center",
                        bbox=dict(boxstyle="round,pad=0.3", fc="#fff8d6", ec="#c8a000"))
        else:
            ax.text(7.4, yk, "last on the bus: no cable leaves J6", fontsize=9, va="center")
    ax.text(5, -0.2, "No joint turns more than 180 deg in total (the ST3215 is not continuous): a cable can only flex back "
            "and forth,\nit can never wind up. Tie each cable down on both sides of its joint and leave the loop shown.",
            ha="center", fontsize=10)
    p = os.path.join(OUT, "cable_schematic.png"); fig.savefig(p, dpi=200, bbox_inches="tight"); fig.savefig(p[:-4] + ".pdf", bbox_inches="tight"); plt.close(fig)
    return p


if __name__ == "__main__":
    print("wrote", head_plot())
    print("wrote", cable_schematic())
