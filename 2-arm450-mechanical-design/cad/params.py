"""
ARM-450 CAD — single source of truth for every dimension.

Change a value here and re-run the part scripts; every STEP/STL updates.
All units mm. Every number traces back to a section of ARM450_REPORT.pdf.
"""

# ---------------------------------------------------------------------------
# SERVO — measured from the user's ST3215.stl
# ---------------------------------------------------------------------------
SERVO_L = 45.22         # along the link   (datasheet)
SERVO_W = 37.25         # across the link  (datasheet)
SERVO_T = 24.72         # along the output axis (datasheet)
SERVO_CLR = 0.20        # clearance per side in the collar bore   (report 9.6)

# ---------------------------------------------------------------------------
# COLLAR — replaces the bending brackets that snapped        (report 9.5, 9.6)
# Carries servo torque as shear around a CLOSED loop instead of bending a
# slender arm: tau = T/(2*Am*t) = 0.25 MPa vs 94 MPa in the old 4 mm bracket.
# ---------------------------------------------------------------------------
COLLAR_WALL = 3.0       # minimum wall
COLLAR_LUG_WALL = 4.0   # thickened through the lug region
COLLAR_H = 20.0         # height along the output axis
COLLAR_SPLIT = 1.1      # split gap so the clamp can actually close
LUG_T = 8.0             # lug thickness (each side of the split)
LUG_W = 12.0            # lug width
LUG_L = 14.0            # how far the lugs stand off the body
FILLET_MIN = 2.0        # every internal corner, r >= 0.5t min 2.0  (report 9.4)

# ---------------------------------------------------------------------------
# FASTENERS                                                    (report 10)
# ---------------------------------------------------------------------------
M3_CLEAR = 3.4          # clearance hole
M3_HEAD = 6.0           # socket head OD
M3_INSERT_D = 4.1       # heat-set insert hole (Ø4.6 insert) — print a coupon
M3_INSERT_L = 7.5       # blind depth: 5.8 insert + 1.7 relief, so the insert can
                        # be pressed SUB-FLUSH. A proud insert holds the rims apart
                        # and with 8 of them the gap is uniform down the whole link.
BOSS_OD = 9.5           # >= 9 so >= 2.2 mm wall around the insert

# ---------------------------------------------------------------------------
# BEARINGS — replaces the single Ø42 thrust washer            (report 8.5)
# 6806-2RS: 30 ID x 42 OD x 7. Keeps the 42 mm OD of the old thrust bearing,
# so the existing pocket diameter carries over.
# ---------------------------------------------------------------------------
BRG_OD = 42.0
BRG_ID = 30.0
BRG_W = 7.0
# MEASURED on the user's printer 2026-08-14: features come out only ~0.02 mm
# undersize -- a very well calibrated machine. The usual 0.1-0.4 mm FDM undersize
# assumption does NOT apply here. Modelling at OD + 0.15 would have left 0.13 mm
# of CLEARANCE = 1.17 mm of wobble at the tool. Model at nominal instead, so the
# 0.02 mm shrinkage itself becomes a light interference press fit.
# User clarified 2026-08-14: the 0.02 mm shrinkage is in XY only; Z is accurate.
# Consequence: ALWAYS print a bearing bore with its axis VERTICAL. Then the bore
# diameter is a circle in the XY plane and shrinks uniformly by 0.02 mm (which is
# exactly the light press fit we want). Printed on its side, the diameter would
# shrink in XY but not in Z and the bore would come out OVAL -- which reintroduces
# the tilt/wobble the whole bearing redesign exists to remove.
# Pocket DEPTH (7 mm) runs in Z and is accurate as-is.
PRINTER_SHRINK_XY = 0.02   # measured
PRINTER_SHRINK_Z = 0.00    # measured, good
BRG_FIT = 0.00          # pocket = OD + this -> 0.02 mm interference after shrink
BRG_CHAMFER = 0.5       # 0.5 x 45 at the pocket mouth so it starts square
BRG_SHOULDER = 2.0      # radial lip the outer race seats against
BRG_SPACING = 40.0      # face-to-face — moment stiffness goes as spacing^2

# ---------------------------------------------------------------------------
# WRIST BEARINGS — 6706 (30 x 37 x 4)                          2026-08-21
# ---------------------------------------------------------------------------
# The wrist carries almost nothing. Worst case at J4, arm horizontal with a
# 300 g payload: 3.3 N radial and 390 N.mm of moment, which is a 9.7 N couple
# across the 40 mm bearing spacing. Against a static rating of order 1000 N that
# is SF 103. A 6806 there is enormously oversized.
#
# 6706 keeps the SAME 30 mm bore, so the tube, the clamp and the horn adapter
# are untouched -- only the three wrist parts' pockets change. Saves 92.6 g,
# which is 6 % of the whole arm.
#
# Moment stiffness is NOT affected: it goes as bearing SPACING squared, and the
# spacing stays 40 mm. What does change is pocket depth, 7 -> 4 mm, so 43 % less
# axial engagement holding the outer race square. That is tolerable only because
# the fit is a light interference press, not a clearance fit -- a race that
# cannot move radially cannot tilt either.
#
# COST OF THIS CHOICE: the arm now has TWO bearing part numbers instead of one.
# J1/J2/J3 stay 6806, J4/J5/J6 are 6706. They are visibly different sizes, but
# label the bags.
WRIST_BRG_OD = 37.0
WRIST_BRG_ID = 30.0
WRIST_BRG_W = 4.0
WRIST_BRG_SHOULDER = 2.0

# ---------------------------------------------------------------------------
# LINK SHELL                                                   (report 3, 6)
# ---------------------------------------------------------------------------
# 2026-08-18: 145 -> 119. The interference sweep proved the 3-axis wrist needs
# 152 mm from J4 to the TCP but the 450 mm chain only left it 70 mm, so EVERY
# pose collided. Shortening both links frees that room at ZERO cost in reach:
# reach = 450 - base 50 - shoulder 40 = 360 mm regardless of the link split.
# L2 = L3 is preserved, so the workspace still has no dead zone.
LINK_L = 119.0          # joint-to-joint — MUST equal the other link
# 2026-08-17: raised 47.5 -> 50.0 after the first print showed seam misalignment
# at the corner where the straight section meets the end boss.
# ROOT CAUSE: with SEC_H/2 = 23.75 but BOSS_R = 25, the boss circle BULGES past
# the rectangle edge instead of being tangent to it, leaving a sharp vertex at
# x = 7.81 mm where the two curves meet at a shallow 18.2 deg included angle.
# At a shallow vertex an offset amplifies: the 0.15 mm tongue/groove clearance
# moves the intersection point by 0.15/sin(18.2) = 0.48 mm ALONG the profile.
# Setting SEC_H/2 = BOSS_R = 25 makes it a TRUE STADIUM -- the arc is tangent to
# the edge, there is no vertex, and the offset is exact everywhere.
# Bonus: I goes from 101,992 to 115,853 mm^4, 13.6 % stiffer.
SEC_H = 50.0            # vertical bending depth = 2 x BOSS_R, tangent stadium
SEC_W = 29.0            # along the joint axis; also the split normal
WALL = 2.4              # 6 passes of a 0.4 mm nozzle           (report 11.2)
BOSS_R = 25.0           # end boss radius, from the existing parts
SEAM_PITCH = 25.0       # fastener pitch along the seam          (report 10)
# 2026-08-17 rev: first bolted assembly showed a persistent seam gap.
# 1.5 mm is 7.5 layers at 0.20 mm -- NOT an integer, so the slicer rounds up to
# 8 layers = 1.60 mm, which exactly equalled the 1.60 mm groove depth and made
# the tongue BOTTOM OUT before the rims could touch. Now an integer 8 layers,
# and the groove is cut deeper so there is real axial margin.
SEAM_LIP = 1.6          # tongue height = 8 x 0.20 mm layers, integer
SEAM_LIP_CLR = 0.25     # per-side clearance -- raised from 0.15. A 2.0 mm tongue
                        # is 4.4 passes at 0.45 mm width, so FDM prints it 0.05-0.10
                        # mm over and 0.15 left only ~0.05 mm/side: it WEDGED.
SEAM_GROOVE_EXTRA = 0.5 # groove cut this much deeper than the tongue is tall,
                        # so the tongue can never bottom before the rims meet

# ---------------------------------------------------------------------------
# PRINT
# ---------------------------------------------------------------------------
# 2026-08-23. These were 0.4 / 0.45 and used by NOTHING -- no CAD module reads
# them -- while every document in the project specified a 0.6 mm nozzle, and the
# 2.4 mm wall is sized for exactly four 0.62 mm perimeters. A dead parameter
# that contradicts the documents is worse than no parameter: the first person to
# grep for the nozzle size finds the wrong answer.
#
# 2026-09-02. The machine in use has a 0.4 mm nozzle -- stated on 2026-08-13 --
# and this file still said 0.6, which is the number a slicer profile would have
# been built from. On a 0.4 nozzle the line width is ~0.48, so the FOUR
# perimeters below give 4 x 0.48 = 1.92 mm against a 2.4 mm wall: every
# structural wall in the arm would print with a 0.48 mm void up its middle,
# filled with sparse infill, and look perfect from outside. FIVE perimeters at
# 0.48 consume the wall exactly.
#
# NOZZLE is therefore the machine's real bore, and line width and perimeter
# count are DERIVED from it rather than written down beside it.
#
# For PLA+CF later: carbon fill is abrasive and eats a brass nozzle inside a
# spool, and it bridges and clogs a 0.4 mm bore. That filament needs a 0.6 mm
# HARDENED nozzle -- change NOZZLE here and the wall arithmetic follows.
NOZZLE = 0.4
_LINE_W = {0.4: 0.48, 0.6: 0.62}
EXTRUSION_W = _LINE_W[NOZZLE]
# LAYER HEIGHT IS NOT A PREFERENCE. SEAM_LIP must be an integer number of
# layers or the slicer rounds the tongue up and it bottoms out in the groove
# before the two rims can touch -- which already happened once, at 1.5 mm.
# 1.6 / 0.20 = 8 exactly. 0.16 and 0.32 also divide it; 0.25 and 0.28 do not.
LAYER_H = 0.20
import math as _math
# enough perimeters to consume the wall SOLID: 5 x 0.48 = 2.40 at a 0.4 nozzle,
# 4 x 0.62 = 2.48 at a 0.6. Derived, so it cannot disagree with the nozzle.
PERIMETERS = int(_math.ceil(WALL / EXTRUSION_W - 1e-9))
assert abs(SEAM_LIP / LAYER_H - round(SEAM_LIP / LAYER_H)) < 1e-9
assert PERIMETERS * EXTRUSION_W >= WALL - 1e-9

# --- tip fasteners at the end bosses (user request, 2026-08-17) -------------
# The seam had NO fastener at the end bosses because the insert-boss loop skips
# that region -- and that is precisely where the bearing sits and where seam
# clamping matters most. A small ear at each boss tip carries an M2.5.
TIP_EAR = True
TIP_SCREW = 2.5         # M2.5
TIP_CLEAR = 2.7         # clearance hole
TIP_INSERT_D = 3.5      # heat-set insert hole (Ø4.0 insert) -- verify on a coupon
TIP_INSERT_L = 5.0
EAR_W = 11.0            # across the link (y)
EAR_OUT = 7.0           # how far it stands proud of the boss (x)

# --- wrist servos (2026-08-19) ---------------------------------------------
# The 60k-pose sweep gives J4 0.296, J5 0.297, J6 0.088 N.m worst case. At the
# 30 % continuous rule that needs 10.1, 10.1 and 3.0 kgf.cm -- so an ST3215
# (30 kgf.cm) is 3-10x oversized at the wrist. It is the SIZE that does not fit,
# not the torque. J4/J5 keep the ST3215 (one part number for five joints);
# J6 takes a micro servo, the only way it fits the 26 mm J6->TCP budget.
SERVO_MICRO_L = 29.0    # REQUIREMENT: >= 3 kgf.cm in this envelope. Verify your part.
SERVO_MICRO_W = 13.0
SERVO_MICRO_T = 30.0

# ---------------------------------------------------------------------------
# SERVO MOUNTING AND HORN  —  *** PLACEHOLDER VALUES, MEASURE YOUR SERVO ***
# ---------------------------------------------------------------------------
# Every part had a servo POCKET but nothing to bolt the servo into, and no horn
# bolt pattern on the driven side. Both are added now. The ST3215.stl on the
# user's Desktop is an OUTER SHELL ONLY -- it does not model the mounting holes,
# so these came from the standard-servo class, NOT from a datasheet.
# MEASURE YOUR SERVO AND CORRECT THESE FOUR NUMBERS. Everything regenerates.
SERVO_BOLT_D = 2.7      # M2.5 clearance for the case mounting screws
SERVO_BOLT_X = 35.0     # mounting hole pitch ALONG the servo    <-- NOT on the outline sheet
SERVO_BOLT_Y = 20.0     # mounting hole pitch ACROSS the servo   <-- NOT on the outline sheet
                        # The outline drawing dimensions the case and the horn but NOT the
                        # four case screws. Y reduced from 30 -> 20 because the case is only
                        # 24.72 mm across, so a 30 mm pitch was geometrically impossible.

# *** THE OUTPUT AXIS IS NOT CENTRED ON THE CASE ***
# Datasheet: the output shaft sits 10.11 mm from one end of a 45.22 mm case,
# i.e. 12.50 mm off the case centre. Every servo pocket in this project was cut
# CENTRED on its joint axis, which would have put every servo 12.5 mm out of
# position and left the horn nowhere near the bearing bore.
SERVO_AXIS_OFFSET = 45.22 / 2 - 10.11      # 12.50 mm, shift the pocket by this
SERVO_HORN_FROM_END = 10.11
SERVO_CABLE_D = 8.0     # cable exit bore out of every servo pocket

HORN_BCD = 14.0         # servo output-horn bolt circle (datasheet, was 16.0)
HORN_N = 4              # number of horn screws
# HORN_SCREW_D was 2.4, described as "M2 clearance into the horn", and NOTHING
# read it. horn_adapter.py defines its own HORN_PILOT_D = 1.9 -- a self-tapping
# pilot, because the M2 screws come UP through the servo horn and thread into the
# printed adapter. A dead parameter carrying the opposite intent is how the next
# person sizes the hole wrong.
HORN_PILOT_D = 1.9      # M2 self-tapper into plastic — the value actually used
HORN_DISC_D = 19.2      # horn disc outer diameter (datasheet)
HORN_BOSS_D = 26.0      # material around the horn pattern on driven parts

# ---------------------------------------------------------------------------
# JOINT SHAFT — material and construction            (revised 2026-08-20)
# ---------------------------------------------------------------------------
# The BUY list called for steel tube Ø30 x 5 while the mass gate carried a
# "2 x 93 g" shaft line. Both were wrong and they hid each other: there are
# SIX joints (12 bearings = 6 pairs), and six Ø30 x 5 steel tubes weigh 1332 g
# -- more than the entire 1.2 kg budget on their own. Caught by the user
# asking the obvious question: "won't that make it heavy?"
#
# Printing the shaft is NOT excluded by strength -- at servo stall it sees only
# 0.55 MPa shear (SF 32) and 0.57 MPa bending (SF 104). It is excluded by two
# LOCAL effects: the M5 preload thread strips (threads run across layer lines,
# ~18 MPa, and preload needs ~16 MPa), and the press fit creeps away because
# plastic relaxes under the sustained elastic strain a press fit depends on.
# So: metal only where metal is needed.
SHAFT_MATERIAL = "AL6061"
SHAFT_OD = 30.0          # = BRG_ID
SHAFT_WALL = 2.0         # Ø26 bore -> 34 g each, 205 g for six. Only spec that fits.
SHAFT_L = 72.0
SHAFT_RHO = 2.70e-3      # g/mm3
# Preload is now a THROUGH-BOLT down the Ø26 bore with a nyloc on the far side,
# replacing the M5 tapped end (you cannot tap a 2 mm wall).
PRELOAD_BOLT = 5.0
PRELOAD_BOLT_L = 90.0
# Roll pin through the tube replaces the grub screws + machined D-flat.
# Double shear 4241 N vs the 196 N the joint torque needs, SF 22. An M3 grub
# on a 2 mm wall would put 170 MPa on the wall and simply dent it.
CLAMP_PIN_D = 3.0


# ---------------------------------------------------------------------------
# MASS — accepted budget                              (user decision 2026-08-21)
# ---------------------------------------------------------------------------
# As-built 1437 g: 604 printed + 360 servos + 268 bearings + 205 shafts.
# The original 1.2 kg target was set against a mass model that multiplied every
# part by 0.55 for "sparse infill". That is valid for a part modelled SOLID.
# These parts are modelled HOLLOW -- 2.4 mm link walls, a 3.0 mm base shell --
# so the STEP volume IS the wall material and 4 perimeters on a 0.6 nozzle
# prints it essentially solid. The factor was discounting the hollowing twice
# and concealed about 240 g.
# Accepted rather than thinning the link walls (bending goes as t^3) or moving
# to a Ø37 bearing that is harder to source.
# HARD CEILING — the user has stated this cannot be raised again.
# preprint_check.py FAILS on it, it does not warn. Headroom is 13 g.
MASS_BUDGET = 1450.0     # g, hard ceiling
MASS_FILL = 0.90         # thin walls print near-solid; 1.00 is the ceiling

# ---------------------------------------------------------------------------
# SYSTEM REACH WITH A TOOL FITTED
# The 450 mm specification is the ARM: base to the J6 tool face. A tool is
# payload hanging off that face, and the quick-change adapter plus a gripper
# adds 42 mm, so the SYSTEM reaches 492 mm.
#
# 2026-08-22: the user was asked whether 450 mm is a hard the capture project stowage
# envelope or a target for the arm itself, and answered that **492 mm with a
# gripper is acceptable**. So 450 mm binds the arm, not the system, and this is
# the recorded system ceiling.
#
# It is checked (preflight stage 8) so that a LATER, longer tool cannot push the
# system past what was actually agreed without the gate saying so. If a future
# tool needs more, that is a decision to re-make, not a number to edit quietly.
SYSTEM_REACH_MAX = 495.0   # mm, arm + longest fitted tool

# ---------------------------------------------------------------------------
# MATERIAL — ONE definition, read by everything
# ---------------------------------------------------------------------------
# 2026-08-27. E, density and yield were hardcoded as literals in TWELVE files:
# 7000.0 in fea.py, stress_analysis.py, compliance_budget.py, bearing_clearance.py
# and verify_configs.py; 1.29e-3 in preprint_check.py, generate_urdf.py,
# preflight.py, draw_iso.py, draw_2d.py, mass_options.py and two cad modules.
# Switching material meant finding all twelve, and missing one would have left
# the gate quietly reporting a mix of two materials.
#
# The user has plain PLA, not carbon-filled. Set MATERIAL and everything follows.
MATERIAL = "PLA"

_MATS = {
    #            E MPa   rho g/mm3   yield MPa  G/E    Tg C   shrink %
    "PLA":    dict(E=3500.0, rho=1.24e-3, Sy=55.0, Gr=0.36, Tg=60.0, shrink=0.40),
    "PLA+CF": dict(E=7000.0, rho=1.29e-3, Sy=60.0, Gr=0.36, Tg=62.0, shrink=0.15),
}
_M = _MATS[MATERIAL]
E_MOD      = _M["E"]        # MPa
RHO_SOLID  = _M["rho"]      # g/mm3
YIELD_MPA  = _M["Sy"]       # MPa
G_RATIO    = _M["Gr"]
TG_C       = _M["Tg"]
SHRINK_PCT = _M["shrink"]
# Plain PLA is 4 % less dense than carbon-filled, so the printed structure gets
# LIGHTER by about 24 g on the switch -- the one thing that improves.
