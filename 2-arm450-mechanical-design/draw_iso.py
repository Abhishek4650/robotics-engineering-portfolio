"""
Isometric dimensioned drawing sheets — one per part, pictorial style.

Every sheet carries: the part in isometric with hidden lines removed, aligned
linear dimensions with extension lines and arrow terminators, leader callouts
for holes, radii, fillets and features, and a title block with material, mass,
print orientation and tolerance notes.

Dimensions are pulled from cad/params.py, so the drawing and the printed part
cannot disagree.
"""
import os, sys, json
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad"))
from params import *                                    # noqa: F403,F401
import isodraw
import audit_parts as _AUD
from isodraw import Sheet, INK, DIMC, NOTEC

CAD = "output/cad"
OUT = "figures/iso"
os.makedirs(OUT, exist_ok=True)
VOL = json.load(open(os.path.join(CAD, "volumes.json")))

PLA_CF = 1.29e-3
CLAMP_OD = BRG_OD - 2 * BRG_SHOULDER          # 38
CLAMP_BORE = SHAFT_OD + 0.2                   # 30.2
CLAMP_SPLIT_ = 1.2                            # split slot width
PIN_INSET_ = 12.0                             # roll-pin holes from each end
HALF_T = SEC_W / 2                            # 14.5


def load(name, center=True):
    m = trimesh.load(os.path.join(CAD, name + ".stl"), force="mesh")
    if center:
        m.vertices = m.vertices - m.bounds.mean(axis=0)
    return m


def block(ax, rows, x=0.012, y=0.012):
    """Stash the title block. It is DRAWN later, by save(), after space has been
    reserved for it -- placing it during layout put it on top of the part."""
    ax._tblock = ("\n".join(f"{k:<13s} {v}" for k, v in rows), x, y,
                  max(len(r) for r in
                      "\n".join(f"{k:<13s} {v}" for k, v in rows).split("\n")),
                  len("\n".join(f"{k:<13s} {v}" for k, v in rows).split("\n")))


def mass_of(name, qty=1, fill=MASS_FILL):
    """Prefer the exact STEP volume; fall back to the mesh for parts the
    volumes table does not carry (the coupon is a test piece, not an arm part).

    FILL. This used a hardcoded 0.55 while the mass budget, the pre-print gate
    and every report used MASS_FILL = 0.90 -- so each drawing sheet quoted its
    part 39 % lighter than the number the build is actually held to. 0.55 is
    the figure from before we noticed that a 2.4 mm wall at 4 perimeters and a
    0.6 mm nozzle prints SOLID, and that discounting for infill on top of
    geometry that is already modelled hollow counts the hollowing twice.
    """
    if name in VOL:
        return VOL[name] * PLA_CF * fill * qty
    return load(name, center=False).volume * PLA_CF * fill * qty


def newsheet(name, size=(11.5, 8.6), **kw):
    fig, ax = plt.subplots(figsize=size)
    m = load(name)
    return fig, ax, Sheet(ax, m, **kw), m


def save(fig, ax, stem):
    ax.autoscale()
    ax.margins(0.075)
    # BALANCE: pad the limits symmetrically about the part's own centre, so the
    # drawing sits in the middle of the sheet. Autoscale alone centres the
    # bounding box of everything drawn -- including leader text that reaches far
    # to one side -- which pushes the part visibly off to the other.
    pb = getattr(ax, "_part_box", None)
    if pb is not None:
        (px0, py0), (px1, py1) = pb
        cx, cy = (px0 + px1) / 2, (py0 + py1) / 2
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        hx = max(cx - x0, x1 - cx)
        hy = max(cy - y0, y1 - cy)
        ax.set_xlim(cx - hx, cx + hx)
        ax.set_ylim(cy - hy, cy + hy)
    tb = getattr(ax, "_tblock", None)
    if tb is not None:
        txt, bx, by, ncol, nrow = tb
        # Reserve a clear band BELOW the drawing and put the block in it, so the
        # legend can never sit on top of the geometry it is describing.
        y0, y1 = ax.get_ylim()
        x0, x1 = ax.get_xlim()
        ax.set_ylim(y0 - (y1 - y0) * (0.055 * nrow + 0.05), y1)
        # widen too if the block is wider than the drawing
        need = (x1 - x0) * (ncol / 118.0)
        if need > (x1 - x0):
            ax.set_xlim(x0, x0 + need)
        ax.text(bx, by, txt, transform=ax.transAxes, family="monospace",
                fontsize=7.6, color="#33414f", va="bottom", ha="left", zorder=8,
                bbox=dict(boxstyle="round,pad=0.5", fc="#f6f8fa",
                          ec="#c8d2dc", lw=0.7))
    fig.tight_layout()
    p = os.path.join(OUT, stem + ".png")
    fig.savefig(p, dpi=140, facecolor="white")
    plt.close(fig)
    print(f"  wrote {p}")


# ---------------------------------------------------------------- link halves
def sheet_link(kind="tongue"):
    name = f"link_half_{kind}"
    fig, ax, s, m = newsheet(name, size=(13.0, 8.2))
    ex = m.extents
    X, Y, Z = ex / 2                      # half extents, part is centred
    L = LINK_L                            # 119 joint-to-joint
    seam_h = Z                            # half-shell height

    # overall length across the two bosses
    s.dim([-X, Y, -Z], [X, Y, -Z], [0, 1, -0.5], text=f"{ex[0]:.2f} OVERALL")
    # joint-to-joint centre distance -- the number that sets the kinematics
    s.dim([-L / 2, -Y, Z], [L / 2, -Y, Z], [0, -1, 0.55],
          text=f"{L:.2f} JOINT-TO-JOINT")
    # section height
    s.dim([X * 0.90, -Y, -Z], [X * 0.90, Y, -Z], [0.55, 0, -0.8], text=f"{SEC_H:.2f}")
    # half-shell thickness
    s.dim([X * 0.62, -Y, -Z], [X * 0.62, -Y, Z], [0.4, -1, 0],
          text=f"{ex[2]:.2f}")

    s.rad([-L / 2, 0, 0], BOSS_R, [0, 0, 1], [-1, 0.15, 0.75],
          text=f"R{BOSS_R:.2f} BOSS (2×)")
    # AUDIT 2026-08-21: this part contains NO Ø42 pocket -- the hollowing cut
    # (Ø45.20 at the boss) swallowed it. Label what is really there, not what
    # was intended. A drawing must never assert a feature the part lacks.
    _has = any(abs(g["dia"] - BRG_OD) < 0.06
               for g in _AUD.cylinders(f"{CAD}/{name}.step"))
    if _has:
        s.dia([L / 2, 0, Z], BRG_OD / 2, [0, 0, 1], [0.9, -0.3, 0.8],
              text=f"Ø{BRG_OD:.2f} × {BRG_W:.2f} DP  BEARING POCKET (2×)")
    else:
        s.dia([L / 2, 0, Z], 45.20 / 2, [0, 0, 1], [0.9, -0.3, 0.8],
              text="Ø45.20 AS-BUILT — NO Ø42.00 POCKET\nSEE ARM450_AUDIT.pdf")
    s.leader([L / 2, 0, -Z], f"Ø{BRG_OD - 2*BRG_SHOULDER:.2f} THRU BORE",
             [0.85, -0.5, -0.85])
    s.leader([-L * 0.06, Y, -Z * 0.55], f"WALL {WALL:.2f}  (6 × 0.40 mm)", [-0.15, 1, -0.75])
    if kind == "tongue":
        s.leader([L * 0.24, Y * 0.92, Z], f"TONGUE {SEAM_LIP:.2f} HIGH "
                 f"(8 × 0.20 LAYERS)", [0.2, 0.9, 0.7])
    else:
        s.leader([L * 0.24, Y * 0.92, Z], f"GROOVE {SEAM_LIP + SEAM_GROOVE_EXTRA:.2f} DEEP "
                 f"({SEAM_LIP_CLR:.2f}/SIDE CLR)", [0.2, 0.9, 0.7])
    s.leader([-L * 0.30, Y * 0.55, Z * 0.1],
             f"Ø{M3_INSERT_D:.2f} × {M3_INSERT_L:.2f} DP  M3 INSERT\n"
             f"ON Ø{BOSS_OD:.2f} BOSS   PITCH {SEAM_PITCH:.0f}", [-0.5, 1, 0.2])
    s.leader([X * 0.97, 0, Z * 0.35], f"M2.5 TIP EAR\nØ{TIP_INSERT_D:.2f} × "
             f"{TIP_INSERT_L:.2f} DP", [1, -0.15, 0.35])

    s.title(f"LINK HALF — {kind.upper()} SIDE",
            "upper arm and forearm are identical parts")
    block(ax, [("PART", f"{name}.stl"),
               ("QTY", "2 off (4 halves = 2 links)"),
               ("MATERIAL", "PLA+CF"),
               ("MASS", f"{mass_of(name):.1f} g each"),
               ("SECTION", f"{SEC_H:.1f} × {SEC_W:.1f} stadium, tangent"),
               ("ORIENT", "split face DOWN on the bed, open side up"),
               ("INFILL", "10–15 % gyroid, 4 perimeters"),
               ("TOL", "bores ±0.05 · XY shrink 0.02 allowed for")])
    save(fig, ax, name)


# ---------------------------------------------------------------- shaft clamp
def sheet_clamp():
    fig, ax, s, m = newsheet("shaft_clamp", size=(10.4, 8.2))
    R, H = CLAMP_OD / 2, 14.0
    s.dia([0, 0, H / 2], R, [0, 0, 1], [0.35, -1, 0.85], text=f"Ø{CLAMP_OD:.2f} OD")
    s.dia([0, 0, H / 2], CLAMP_BORE / 2, [0, 0, 1], [-1, 0.35, 0.55],
          text=f"Ø{CLAMP_BORE:.2f} BORE")
    s.dim([R * 0.70, -R * 0.70, -H / 2], [R * 0.70, -R * 0.70, H / 2],
          [1, -1, 0], text=f"{H:.2f}")
    s.leader([0, R, 0], f"SPLIT {CLAMP_SPLIT_:.2f} WIDE", [0.25, 1, 0.75])
    s.leader([-R, 0, -H * 0.20], f"2 × Ø{CLAMP_PIN_D:.2f} ROLL PIN\n"
             f"AT {H*0.3:.1f} AND {H*0.7:.1f} FROM BASE", [-1, 0.1, 0.55])
    s.title("SHAFT CLAMP (SPLIT)", "seats in the Ø38 through-bore between the bearings")
    block(ax, [("PART", "shaft_clamp.stl"), ("QTY", "2 off"),
               ("MATERIAL", "PLA+CF"), ("MASS", f"{mass_of('shaft_clamp'):.1f} g each"),
               ("ORIENT", "bore axis VERTICAL"),
               ("INFILL", "100 %, 6 perimeters"),
               ("NOTE", "roll pin replaces grub screws — a\n"
                        "              grub on a 2 mm tube wall dents it")])
    save(fig, ax, "shaft_clamp")


# ---------------------------------------------------------------- servo collar
def sheet_collar():
    fig, ax, s, m = newsheet("servo_collar", size=(11.2, 8.4))
    ex = m.extents; X, Y, Z = ex / 2
    s.dim([-X, Y, -Z], [X, Y, -Z], [0, 1, -0.45], text=f"{ex[0]:.2f}")
    s.dim([X, -Y, -Z], [X, Y, -Z], [1, 0, -0.45], text=f"{ex[1]:.2f}")
    s.dim([X, -Y, -Z], [X, -Y, Z], [1, -1, 0], text=f"{ex[2]:.2f}", gap=0.26)
    s.leader([0, 0, Z], f"SERVO POCKET {SERVO_L:.2f} × {SERVO_W:.2f} × "
             f"{SERVO_T:.2f}\n+{SERVO_CLR:.2f} CLEARANCE PER SIDE", [0, -0.8, 1])
    s.leader([-X * 0.80, -Y * 0.55, 0],
             f"OUTPUT AXIS {SERVO_AXIS_OFFSET:.2f} OFF CENTRE\n(FROM DATASHEET — NOT CENTRED)",
             [-1, -0.35, 0.5])
    # 2026-08-27. This leader used to read "4 x M3 on 35.0 x 20.0", describing a
    # servo bolt pattern. The collar has no such pattern: it carries TWO M3 clamp
    # screws through the split lugs, counterbored on the -X side, and that is all.
    # A drawing that names a feature the part does not have is the J6-pilot error
    # again, and it survived because nothing compared the note to the geometry.
    s.leader([X * 0.55, Y * 0.85, Z * 0.4],
             f"2 × M3 CLAMP SCREWS THROUGH THE LUGS\nC'BORE Ø{M3_HEAD:.1f} ON THE −X SIDE",
             [0.4, 1, 0.55])
    s.title("SERVO COLLAR", "full-perimeter clamp — closed loop, not a cantilever")
    block(ax, [("PART", "servo_collar.stl"), ("QTY", "2 off"),
               ("MATERIAL", "PLA+CF"), ("MASS", f"{mass_of('servo_collar'):.1f} g each"),
               ("ORIENT", "collar axis VERTICAL"),
               ("INFILL", "100 %, 6 perimeters"),
               ("NOTE", "carries stall torque as shear flow\n"
                        "              around a closed loop: 0.25 MPa")])
    save(fig, ax, "servo_collar")


# ---------------------------------------------------------------- wrist parts
def sheet_wrist(part, title, sub, notes):
    fig, ax, s, m = newsheet(part, size=(11.2, 8.4))
    ex = m.extents; X, Y, Z = ex / 2
    s.dim([-X, Y, -Z], [X, Y, -Z], [0, 1, -0.45], text=f"{ex[0]:.2f}")
    s.dim([X, -Y, -Z], [X, Y, -Z], [1, 0, -0.45], text=f"{ex[1]:.2f}")
    s.dim([X, -Y, -Z], [X, -Y, Z], [1, -1, 0], text=f"{ex[2]:.2f}", gap=0.26)
    for p3, txt, out in notes:
        s.leader(np.array(p3) * np.array([X, Y, Z]), txt, out)
    s.title(title, sub)
    block(ax, [("PART", f"{part}.stl"), ("QTY", "1 off"),
               ("MATERIAL", "PLA+CF"), ("MASS", f"{mass_of(part):.1f} g"),
               ("ORIENT", "bearing bore axis VERTICAL"),
               ("INFILL", "50–60 % gyroid, 6 perimeters"),
               ("TOL", "bearing bore ±0.05")])
    save(fig, ax, part)


# ---------------------------------------------------------------- turret / base
def sheet_turret():
    fig, ax, s, m = newsheet("turret_j1", size=(10.6, 8.8))
    ex = m.extents; X, Y, Z = ex / 2
    s.dim([-X, Y, -Z], [X, Y, -Z], [0, 1, -0.45], text=f"{ex[0]:.2f}")
    s.dim([X, -Y, -Z], [X, -Y, Z], [1, -1, 0], text=f"{ex[2]:.2f}", gap=0.26)
    s.dia([0, 0, -Z], BRG_OD / 2, [0, 0, 1], [-0.9, 0.3, -0.6],
          text=f"Ø{BRG_OD:.2f} × {BRG_W:.2f} DP  J1 BEARING SEAT")
    s.leader([0, 0, Z], f"SERVO POCKET {SERVO_L:.2f} × {SERVO_W:.2f}", [0.2, -0.9, 1])
    s.leader([X * 0.8, Y * 0.5, 0], f"Ø{HORN_BCD:.2f} HORN BCD, 4 × M2.5", [1, 0.4, 0.5])
    s.title("J1 TURRET", "carries the shoulder; rotates on the base bearing")
    block(ax, [("PART", "turret_j1.stl"), ("QTY", "1 off"),
               ("MATERIAL", "PLA+CF"), ("MASS", f"{mass_of('turret_j1'):.1f} g"),
               ("ORIENT", "bearing seat DOWN, axis vertical"),
               ("INFILL", "50–60 % gyroid, 6 perimeters")])
    save(fig, ax, "turret_j1")


def sheet_base():
    fig, ax, s, m = newsheet("base", size=(11.0, 8.8))
    ex = m.extents; X, Y, Z = ex / 2
    s.dia([0, 0, -Z], 120.0 / 2, [0, 0, 1], [0.55, 0.9, -0.5], text="Ø120.00 FOOT")
    q = 60.0 * 0.707
    s.dim([q, -q, -Z], [q, -q, Z], [1, -1, 0],
          text=f"{ex[2]:.2f} OVERALL", gap=0.26)
    s.leader([-60.0 * 0.72, 60.0 * 0.72, -Z + 3.5], "FOOT PLATE\n7.00 THK", [-0.8, 0.45, -0.35])
    s.dia([0, 0, Z], 52.0 / 2, [0, 0, 1], [-0.85, 0.4, 0.7], text="Ø52.00 CABLE BORE")
    # AUDIT: the Ø52 cable bore is cut through first, so the Ø42 seat cut is a
    # no-op and this part has no J1 bearing seat at all.
    s.leader([0, 0, Z], "NO Ø42.00 J1 SEAT — the Ø52 cable bore\n"
             "swallowed it.  SEE ARM450_AUDIT.pdf", [0.9, -0.25, 0.75])
    s.leader([104 / 2 * 0.707, 104 / 2 * 0.707, -Z], "4 × Ø4.50 M4 ON Ø104.00 BCD",
             [0.9, 0.6, -0.5])
    s.leader([-X * 0.62, Y * 0.30, 0], "PEDESTAL Ø96 → Ø80 TAPER\n3.00 SHELL (HOLLOW)",
             [-1, 0.25, 0.45])
    s.title("BASE PEDESTAL", "hollow — solid it was 166 g, 14 % of the whole budget")
    block(ax, [("PART", "base.stl"), ("QTY", "1 off"),
               ("MATERIAL", "PLA+CF"), ("MASS", f"{mass_of('base'):.1f} g"),
               ("ORIENT", "foot DOWN, upright"),
               ("INFILL", "50–60 % gyroid, 6 perimeters"),
               ("NOTE", "longest print at ~5.6 h — run overnight")])
    save(fig, ax, "base")


# ---------------------------------------------------------------- shaft (tube)
def tube_mesh():
    """The shaft is now a BOUGHT aluminium tube, not a printed part. Modelled by
    cad/shaft_tube.py so the drawing, the assembly and the mass budget agree."""
    m = trimesh.load(os.path.join(CAD, "shaft_tube.stl"), force="mesh")
    m.vertices = m.vertices - m.bounds.mean(axis=0)
    return m


def sheet_shaft():
    """Drawn with the axis along +X. A 72 x 30 tube stood upright wastes most of
    the sheet and collides with the title block; laid along X it runs diagonally
    across the page, which is also how a shaft is conventionally drawn."""
    fig, ax = plt.subplots(figsize=(12.2, 7.6))
    m = tube_mesh()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    m.vertices = m.vertices - m.bounds.mean(axis=0)
    s = Sheet(ax, m, px=1300)
    ro, L = SHAFT_OD / 2, SHAFT_L
    q = ro * 0.707
    s.dim([-L / 2, 0, ro], [L / 2, 0, ro], [0, -0.6, 1], text=f"{L:.2f} CUT LENGTH")
    s.dim([-L / 2, 0, -ro], [-L / 2 + PIN_INSET_, 0, -ro], [0, 0.5, -1],
          text=f"{PIN_INSET_:.2f}")
    s.dia([L / 2, 0, 0], ro, [1, 0, 0], [0.55, -0.85, 0.5], text=f"Ø{SHAFT_OD:.2f} OD")
    s.dia([L / 2, 0, 0], ro - SHAFT_WALL, [1, 0, 0], [0.9, -0.4, 0.9],
          text=f"Ø{SHAFT_OD - 2*SHAFT_WALL:.2f} BORE ({SHAFT_WALL:.2f} WALL)")
    s.leader([-L / 2 + PIN_INSET_, ro, 0], f"2 × Ø{CLAMP_PIN_D:.2f} THRU\nROLL PIN",
             [-0.45, 1, 0.55])
    s.leader([-L / 2, 0, 0], f"M{PRELOAD_BOLT:.0f} × {PRELOAD_BOLT_L:.0f} "
             f"THROUGH-BOLT + NYLOC\nDOWN THE BORE — PRELOADS THE BEARINGS",
             [-1, 0.35, -0.55])
    s.title("JOINT SHAFT — ALUMINIUM TUBE",
            "BOUGHT PART: cut and drill only, do not print")
    im = np.pi / 4 * (SHAFT_OD ** 2 - (SHAFT_OD - 2 * SHAFT_WALL) ** 2)
    block(ax, [("PART", "shaft_tube.stl (bought stock)"), ("QTY", "6 off"),
               ("MATERIAL", "AL6061 / 6060 tube"),
               ("STOCK", f"Ø{SHAFT_OD:.0f} × {SHAFT_WALL:.0f} wall, ~500 mm"),
               ("MASS", f"{im*SHAFT_L*SHAFT_RHO:.1f} g each · "
                        f"{6*im*SHAFT_L*SHAFT_RHO:.0f} g total"),
               ("CHECK", "MEASURE OD before cutting:\n"
                         "              29.98–30.01 use as-is\n"
                         "              to 29.92 Loctite 603/638\n"
                         "              below   turn or buy drawn tube"),
               ("NOTE", "printing fails on the preload thread\n"
                        "              and press-fit creep, not strength")])

    save(fig, ax, "joint_shaft_tube")


# ---------------------------------------------------------------- fit coupon
def sheet_horn():
    fig, ax, s, m = newsheet("horn_adapter", size=(10.6, 8.4))
    ex = m.extents; X, Y, Z = ex / 2
    s.dia([0, 0, Z], 36.0 / 2, [0, 0, 1], [0.35, -1, 0.85], text="Ø36.00 OD")
    s.dia([0, 0, -Z], (SHAFT_OD + 0.2) / 2, [0, 0, 1], [-1, 0.3, -0.7],
          text=f"Ø{SHAFT_OD + 0.2:.2f} BORE — SLIP FIT ON THE TUBE")
    s.dim([X * 0.72, -Y * 0.72, -Z], [X * 0.72, -Y * 0.72, Z], [1, -1, 0],
          text=f"{ex[2]:.2f}", gap=0.26)
    s.leader([0, 0, Z], f"{HORN_N} × Ø1.90 ON Ø{HORN_BCD:.0f} BCD\n"
             f"M2 SELF-TAP INTO THE HORN", [0.2, -0.9, 1.0])
    s.leader([0, 0, Z - 1.0], f"Ø{HORN_DISC_D + 0.4:.1f} × 1.60 HORN RECESS",
             [-0.9, -0.35, 0.8])
    s.leader([0, Y, 0], f"Ø{CLAMP_PIN_D:.2f} ROLL PIN THRU\n"
             "USES THE TUBE'S EXISTING HOLE", [0.25, 1, 0.5])
    s.title("SERVO HORN ADAPTER", "closes the torque path — servo horn to shaft")
    block(ax, [("PART", "horn_adapter.stl"), ("QTY", "6 off — one per joint"),
               ("MATERIAL", "PLA+CF"),
               ("MASS", f"{mass_of('horn_adapter'):.1f} g each"),
               ("ORIENT", "horn face DOWN on the bed"),
               ("INFILL", "100 %, 6 perimeters"),
               ("SIZED ON", "servo STALL 2.94 N·m:\n"
                            "              horn screws 105 N, SF 4.6\n"
                            "              roll pin 196 N, SF 7.3"),
               ("NOTE", "reuses the pin hole the tube already\n"
                        "              has 12 mm from each end")])
    save(fig, ax, "horn_adapter")


def sheet_coupon():
    fig, ax, s, m = newsheet("fit_coupon", size=(12.5, 7.4))
    ex = m.extents; X, Y, Z = ex / 2
    s.dim([-X, Y, -Z], [X, Y, -Z], [0, 1, -0.5], text=f"{ex[0]:.2f}")
    s.dim([X, -Y, -Z], [X, Y, -Z], [1, 0, -0.5], text=f"{ex[1]:.2f}")
    s.dim([X, -Y, -Z], [X, -Y, Z], [1, -1, 0], text=f"{ex[2]:.2f}", gap=0.26)
    # Rows are placed from the coupon's OWN constants, re-centred the way the
    # mesh is. Hardcoding y = 0 for the main row worked only while the coupon
    # had one row; the wrist row moved the centroid and orphaned every leader.
    import fit_coupon as FC
    y_main  = FC.Y_MAIN - FC.Y_CENTRE
    y_wrist = FC.Y_WRIST - FC.Y_CENTRE
    # ONE callout per row, not one per pocket. Six leaders on a part this size
    # collided into an unreadable stack -- and the per-pocket identity is
    # already carried ON the part, by the raised numerals and the dot counts,
    # which is the entire reason those marks exist.
    s.leader([0.0, y_main, Z],
             "6806 ROW  (J1 / J2 / J3)\n"
             "Ø41.95 / Ø42.00 / Ø42.05  × 7.00 DP\n"
             "•• 2 dots = Ø42.00 = DESIGN",
             [0.35, -0.9, 1.5])
    s.leader([0.0, y_wrist, Z],
             "6706 ROW  (J4 / J5 / J6)\n"
             "Ø36.95 / Ø37.00 / Ø37.05  × 4.00 DP\n"
             "•• 2 dots = Ø37.00 = DESIGN",
             [0.35, -0.9, -1.5])
    s.leader([-X * 0.86, Y * 0.06, Z], "INSERT TEST\nØ3.90 / 4.10 / 4.30", [-1.0, 0.3, 0.5])
    s.leader([X * 0.80, Y * 0.06, Z], "SEAM SAMPLE: 1.60 TONGUE + GROOVE", [1.0, 0.5, 0.2])
    s.title("FIT-TEST COUPON", "PRINT THIS FIRST — it gates every part with a bearing pocket")
    block(ax, [("PART", "fit_coupon.stl"), ("QTY", "1 off"),
               ("MATERIAL", "same filament as the parts it gates"),
               ("MASS", f"{mass_of('fit_coupon'):.1f} g · ~2.3 h"),
               ("ORIENT", "flat, pockets facing UP"),
               ("ROWS", "top Ø42 = 6806, J1/J2/J3\n"
                        "              bottom Ø37 = 6706, J4/J5/J6"),
               ("PURPOSE", "2.3 h spent here protects the 19 h\n"
                           "              of parts that carry a bearing pocket"),
               ("READ IT", "firm thumb press and sits square = right\n"
                           "              drops in free = too big\n"
                           "              will not start = too small")])
    save(fig, ax, "fit_coupon")


# ------------------------------------------------------------- end effectors
import end_effector as EE   # noqa: E402  (the tool geometry constants; cad/ is on sys.path)


def sheet_tool(part, title, sub, notes, rows, size=(11.4, 8.6), fill=MASS_FILL):
    """Generic dimensioned isometric for an end-effector part.

    Same machinery as sheet_wrist. The tools differ only in that some of them
    print at 100 % infill -- the pinion and the jaw racks, whose teeth are 2 mm
    and would come out hollow at the 55 % the arm parts use -- so the fill used
    for the quoted mass is an argument rather than a constant.
    """
    fig, ax, sh, m = newsheet(part, size=size)
    ex = m.extents; X, Y, Z = ex / 2
    sh.dim([-X, Y, -Z], [X, Y, -Z], [0, 1, -0.45], text=f"{ex[0]:.2f}")
    sh.dim([X, -Y, -Z], [X, Y, -Z], [1, 0, -0.45], text=f"{ex[1]:.2f}")
    sh.dim([X, -Y, -Z], [X, -Y, Z], [1, -1, 0], text=f"{ex[2]:.2f}", gap=0.26)
    for p3, txt, out in notes:
        sh.leader(np.array(p3) * np.array([X, Y, Z]), txt, out)
    sh.title(title, sub)
    g = mass_of(part, fill=fill)
    block(ax, [("PART", f"{part}.stl")] + rows +
              [("MASS", f"{g:.1f} g at {fill*100:.0f} % fill")])
    save(fig, ax, part)


TOOL_NOTES = {
 "tool_adapter": ("TOOL ADAPTER — ARM SIDE",
   "bolts to J6 ONCE and stays there; every tool bayonets onto this",
   [((0.0, 0.0, -1.0), f"Ø{EE.J6_PILOT - 0.3:.2f} PILOT SPIGOT\ninto the J6 Ø10.00 bore", (-0.5, -0.8, -0.8)),
    ((0.8, 0.45, -0.3), f"3 × Ø{M3_CLEAR:.2f} ON Ø{EE.J6_BCD:.2f} BCD\nAT 160° / 250° / 340°\nC'BORE Ø6.20 — HEADS FLUSH", (1, 0.5, -0.4)),
    ((0.0, 0.0, 1.0), f"Ø{EE.BAY_D:.2f} BAYONET SPIGOT\n3 LUGS × {EE.BAY_LUG_ARC:.0f}° ARC, {EE.BAY_LUG_OUT:.2f} PROUD", (0.2, -0.9, 1.0)),
    ((-0.85, 0.3, 0.4), "COUNTERBORES MATTER:\na proud M3 head fouls the tool", (-1, 0.35, 0.5))],
   [("QTY", "1 off"), ("MATERIAL", "PLA+CF"),
    ("ORIENT", "spigot UP, flat face on the bed"),
    ("INFILL", "60 %, 6 perimeters"),
    ("TOL", "lug thickness ±0.10 — it sets the\n              bayonet preload")]),

 "tool_gripper": ("GRIPPER BODY", "parallel jaws, rack and pinion, one SG90",
   [((0.0, 0.0, 1.0), f"BAYONET SOCKET Ø{EE.BAY_D + 2*EE.BAY_CLR:.2f}\nENTRY SLOTS + {EE.BAY_TWIST:.0f}° LOCK GROOVE", (0.25, -0.9, 1.0)),
    ((0.0, -0.9, 0.2), f"SG90 POCKET {EE.SG90_L:.1f} × {EE.SG90_W:.1f} × {EE.SG90_H:.1f}", (0.15, -1, 0.55)),
    ((0.9, 0.55, -0.6), f"2 × RACK CHANNEL {EE.JAW_T + 0.5:.2f} WIDE\nAT ±{EE.RACK_OFFSET:.2f} FROM CENTRE", (1, 0.55, -0.5)),
    ((-0.9, 0.0, 0.35), f"M{EE.LOCK_SCREW - 0.4:.0f} THUMBSCREW\nstops the bayonet twisting back", (-1, -0.25, 0.5))],
   [("QTY", "1 off"), ("MATERIAL", "PLA+CF"),
    ("ORIENT", "socket face UP"),
    ("INFILL", "40 %, 4 perimeters"),
    ("NOTE", "RACK_OFFSET is NOT PCD/2 + JAW_T/2:\n"
             "              the teeth are cut 2.40 into the bar,\n"
             "              so the pitch line sits that much in")]),

 "gripper_jaw": ("GRIPPER JAW", "print two — mirror the second in the slicer",
   [((-0.55, -0.9, -0.6), f"RACK TEETH {EE.TOOTH:.2f} PITCH × {EE.TOOTH_DEPTH:.2f} DEEP\nON THE FACE TOWARDS THE PINION", (-0.6, -1, -0.5)),
    ((-0.75, 0.0, -0.9), "90° V-GROOVE, 3.00 DEEP\nfull height of the finger", (-0.9, 0.4, -0.9)),
    ((0.9, 0.0, 0.7), f"STROKE {EE.GRIP_STROKE:.0f}.00 TOTAL OPENING", (1, 0.3, 0.6))],
   [("QTY", "2 off (one mirrored)"), ("MATERIAL", "PLA+CF"),
    ("ORIENT", "rack bar FLAT on the bed, teeth sideways"),
    ("INFILL", "100 % — 2.00 teeth print hollow otherwise"),
    ("WHY THE V", "a flat jaw touches a cylinder on ONE\n"
                  "              line and it rolls out under load;\n"
                  "              a 90° V touches on four")], (11.8, 7.6), 1.0),

 "gripper_pinion": ("GRIPPER PINION", "one turn of the SG90 drives both racks together",
   [((0.0, 0.0, 1.0), f"Ø{EE.PINION_PCD:.2f} PITCH CIRCLE", (0.25, -0.9, 1.0)),
    ((-0.85, 0.35, 0.0), "Ø5.00 SG90 SHAFT BORE", (-1, 0.35, 0.45)),
    ((0.85, -0.35, 0.5), "4 × Ø1.90 HORN SCREWS ON Ø14.00", (1, -0.35, 0.6))],
   [("QTY", "1 off"), ("MATERIAL", "PLA+CF"),
    ("ORIENT", "flat, teeth in the XY plane"),
    ("INFILL", "100 % — small teeth, high tooth load"),
    ("NOTE", "PCD raised 16 → 20 on 2026-08-22:\n"
             "              at 16 the rack pitch line sat 1.20\n"
             "              outside the PCD and never touched")], (10.6, 8.2), 1.0),

 "tool_dock": ("DOCKING PROBE", "latched by J6 itself — no seventh actuator",
   [((0.0, 0.0, 1.0), f"BAYONET SOCKET Ø{EE.BAY_D + 2*EE.BAY_CLR:.2f}", (0.25, -0.9, 1.0)),
    ((0.0, 0.0, -1.0), f"CAPTURE CONE Ø{EE.DOCK_MOUTH:.2f} MOUTH\nOVER A Ø{EE.DOCK_THROAT:.2f} THROAT\n= ±9.00 CAPTURE, 6× THE ARM ERROR", (-0.35, -0.9, -1.0)),
    ((0.8, 0.4, -0.55), f"3 LATCH LUGS × {EE.DOCK_LUG_ARC:.0f}° IN THE THROAT\nROLL J6 {EE.DOCK_TWIST:.0f}° TO LATCH", (1, 0.45, -0.5)),
    ((-0.85, -0.2, 0.3), f"Ø{EE.FLUID_BORE:.2f} FLUID PASS-THROUGH\nfull depth, out the back", (-1, -0.3, 0.5))],
   [("QTY", "1 off"), ("MATERIAL", "PLA+CF"),
    ("ORIENT", "cone DOWN on the bed, socket up"),
    ("INFILL", "40 %, 4 perimeters"),
    ("NOTE", "the cone is the whole point: it turns a\n"
             "              ±1.4 mm arm into a ±9 mm target")]),

 "dock_target_sealed": ("DOCKING TARGET PORT — SEALED",
   "the same port with an O-ring groove, for fluid transfer",
   [((0.0, 0.0, 1.0), f"Ø{EE.DOCK_THROAT - 0.7:.2f} SPIGOT", (0.25, -0.9, 1.0)),
    ((0.85, 0.35, 0.30), f"O-RING GROOVE Ø{EE.SEAL_GROOVE_D:.2f}\n"
                         f"{EE.SEAL_GROOVE_W:.2f} WIDE × "
                         f"{(2*EE.SPG_R-EE.SEAL_GROOVE_D)/2:.2f} DEEP\n"
                         f"{EE.SEAL_CORD:.2f} CORD AT {EE.SEAL_SQUEEZE*100:.0f} % SQUEEZE",
     (1, 0.45, 0.5)),
    ((-0.85, 0.3, -0.5), f"3 × Ø{M3_CLEAR:.2f} BOLT-DOWN ON Ø27.00", (-1, 0.35, -0.5)),
    ((0.0, 0.0, -1.0), f"Ø{EE.FLUID_BORE:.2f} FLUID BORE", (-0.3, -0.9, -0.9))],
   [("QTY", "1 off — ALTERNATIVE to dock_target"),
    ("MATERIAL", "PLA+CF"),
    ("ORIENT", "flat face on the bed, SPIGOT UP"),
    ("INFILL", "40 %, 4 perimeters"),
    ("WHY UP", "the groove must be a HORIZONTAL feature.\n"
               "              Printed on its side it is a stack of\n"
               "              stair-steps and the O-ring cannot seal"),
    ("SEAL", "radial, not a face seal — the bayonet has\n"
             "              0.5 mm of axial play at each end")]),

 "dock_target": ("DOCKING TARGET PORT", "the passive side — bolt it to the bench, no arm needed",
   [((0.0, 0.0, 1.0), f"Ø{EE.DOCK_THROAT - 0.7:.2f} SPIGOT\nCHAMFERED LEAD-IN", (0.25, -0.9, 1.0)),
    ((0.8, 0.4, 0.35), f"CAPTURE GROOVE + {EE.BAY_N} ENTRY SLOTS", (1, 0.45, 0.45)),
    ((-0.85, 0.3, -0.5), f"3 × Ø{M3_CLEAR:.2f} BOLT-DOWN ON Ø27.00", (-1, 0.35, -0.5)),
    ((0.0, 0.0, -1.0), f"Ø{EE.FLUID_BORE:.2f} FLUID BORE", (-0.3, -0.9, -0.9))],
   [("QTY", "1 off"), ("MATERIAL", "PLA+CF"),
    ("ORIENT", "flat face on the bed, spigot up"),
    ("INFILL", "40 %, 4 perimeters"),
    ("NOT ARM", "bench fixture — NOT in the 1450 g budget"),
    ("PRINT IT", "FIRST of the tools: it proves the docking\n"
                 "              interface with no arm, no fuel, no\n"
                 "              flight software")]),
}


# ---------------------------------------------------------------------- main
WRIST_NOTES = {
 "wrist_j4_housing": ("J4 ROLL HOUSING", "forearm roll — carries the J4 servo",
   [((0.0, 0.0, 1.0), f"Ø{BRG_OD:.2f} × {BRG_W:.2f} DP BEARING POCKET", (0.2, -0.9, 1.0)),
    ((0.75, 0.45, 0.25), f"SERVO POCKET {SERVO_L:.2f} × {SERVO_W:.2f} × {SERVO_T:.2f}", (1, 0.5, 0.5)),
    ((-0.85, 0.0, -0.3), f"Ø{BRG_OD - 2*BRG_SHOULDER:.2f} THRU BORE", (-1, 0.2, -0.4))]),
 "wrist_j5_yoke": ("J5 PITCH YOKE", "the fork that carries the wrist pitch axis",
   [((0.0, 0.0, 1.0), f"Ø{BRG_OD:.2f} × {BRG_W:.2f} DP  BOTH CHEEKS", (0.2, -0.9, 1.0)),
    ((0.0, 0.95, 0.0), f"CHEEK SPACING {BRG_SPACING:.2f}\nMOMENT STIFFNESS ∝ SPACING²", (0.3, 1, 0.5)),
    ((-0.9, -0.3, 0.2), f"Ø{BRG_OD - 2*BRG_SHOULDER:.2f} THRU", (-1, -0.3, 0.35))]),
 "wrist_j6_output": ("J6 OUTPUT / TOOL FLANGE", "tool roll — the pen or gripper bolts here",
   [((0.0, 0.0, -1.0), f"Ø{BRG_OD:.2f} × {BRG_W:.2f} DP BEARING POCKET", (-0.9, 0.25, -0.7)),
    ((0.85, 0.35, 0.15), "TOOL FACE  3 × Ø3.40 ON Ø30.00 BCD\nAT 160° / 250° / 340°", (1, 0.4, 0.45)),
    ((0.0, 0.0, 1.0), "Ø10.00 CENTRE PILOT\nlocates the tool + cable route", (0.15, -0.95, 0.9)),
    ((-0.85, 0.0, -0.35), f"Ø{HORN_BCD:.2f} HORN BCD", (-1, 0.2, -0.4))]),
}


def main():
    print("ISOMETRIC DIMENSIONED DRAWINGS")
    for k in ("tongue", "groove"):
        sheet_link(k)
    sheet_clamp()
    sheet_collar()
    for p, (t, sub, notes) in WRIST_NOTES.items():
        sheet_wrist(p, t, sub, notes)
    sheet_turret()
    sheet_base()
    sheet_horn()
    sheet_shaft()
    sheet_coupon()
    for p, args in TOOL_NOTES.items():
        sheet_tool(p, *args)
    print("done")


if __name__ == "__main__":
    main()
