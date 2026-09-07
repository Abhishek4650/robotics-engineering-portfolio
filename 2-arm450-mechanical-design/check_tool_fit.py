"""
End-effector interface check — does the tool actually go on the arm?

Two couplings have to be right, and neither is verifiable by eye:
  J6 face  <-> tool_adapter     (3 bolts, one pilot)
  adapter  <-> gripper / dock   (three-lug bayonet)
  dock probe <-> dock_target    (the docking bayonet, driven by J6)

Read from the STEP B-rep like every other fit in this project.
"""
import math
import numpy as np
import sys
sys.path.insert(0, "cad")
from params import *          # noqa: F403,F401
import audit_parts as AP
from end_effector import (BAY_D, BAY_CLR, BAY_LUG_OUT, BAY_LUG_H, J6_BCD,
                          J6_BOLT_ANG, J6_PILOT, DOCK_THROAT, DOCK_MOUTH,
                          FLUID_BORE, SPG_R, SPG_H, SEAT_DZ, FLANGE_H,
                          DOCK_TWIST, DOCK_CONE_L, GRV_R, PARTS as TOOL_PARTS)

R = []


def chk(ok, name, det):
    R.append((bool(ok), name, det))


def holes(part, dia, tol=0.08):
    return [g for g in AP.cylinders(f"output/cad/{part}.step")
            if abs(g["dia"] - dia) < tol]


def main():
    print("=" * 76)
    print("END-EFFECTOR INTERFACE CHECK")
    print("=" * 76)

    # --- J6 face <-> adapter
    j6 = holes("wrist_j6_output", M3_CLEAR)
    ad = holes("tool_adapter", M3_CLEAR)
    chk(len(ad) == 3, "adapter has 3 bolt holes", f"{len(ad)} found")
    a_j6 = sorted(round(np.degrees(np.arctan2(g["perp"][1], g["perp"][0])) % 360)
                  for g in j6)
    a_ad = sorted(round(np.degrees(np.arctan2(g["perp"][1], g["perp"][0])) % 360)
                  for g in ad)
    chk(a_j6 == a_ad, "bolt angles match the J6 face",
        f"J6 {a_j6} vs adapter {a_ad}")
    r_j6 = np.mean([np.hypot(*g["perp"][:2]) for g in j6])
    r_ad = np.mean([np.hypot(*g["perp"][:2]) for g in ad])
    chk(abs(r_j6 - r_ad) < 0.05, "bolt circle matches",
        f"Ø{2*r_j6:.2f} vs Ø{2*r_ad:.2f}")
    pil = holes("tool_adapter", J6_PILOT - 0.30, tol=0.2)
    sp = [g for g in AP.cylinders("output/cad/tool_adapter.step")
          if abs(g["dia"] - (J6_PILOT - 0.30)) < 0.2]
    chk(len(sp) >= 1, "adapter has the Ø9.70 pilot spigot",
        f"{len(sp)} found; J6 bore is Ø{J6_PILOT:.2f}, "
        f"clearance {J6_PILOT-(J6_PILOT-0.30):.2f} mm total")

    # --- bayonet, adapter <-> tools
    print(f"\n  BAYONET  male Ø{BAY_D:.1f} + {BAY_LUG_OUT:.1f} lugs, "
          f"{BAY_CLR:.2f} mm/side clearance")
    for tool in ("tool_gripper", "tool_dock"):
        soc = [g for g in AP.cylinders(f"output/cad/{tool}.step")
               if abs(g["dia"] - (BAY_D + 2 * BAY_CLR)) < 0.1]
        chk(len(soc) >= 1, f"{tool} has the bayonet socket",
            f"Ø{soc[0]['dia']:.2f} vs male Ø{BAY_D:.2f} -> "
            f"{(soc[0]['dia']-BAY_D)/2:.2f} mm/side" if soc else "not found")
        lock = [g for g in AP.cylinders(f"output/cad/{tool}.step")
                if abs(g["dia"] - 3.4) < 0.08]
        chk(len(lock) >= 1, f"{tool} has the lock screw", f"{len(lock)} × Ø3.40")

    # --- docking interface
    print(f"\n  DOCKING  cone Ø{DOCK_MOUTH:.0f} mouth over a Ø{DOCK_THROAT:.0f} throat")
    cap = (DOCK_MOUTH - DOCK_THROAT) / 2
    chk(cap > 6.0, "capture tolerance exceeds arm error",
        f"±{cap:.1f} mm vs ~1.4 mm expected arm precision "
        f"({cap/1.4:.1f}× margin)")
    fb_p = holes("tool_dock", FLUID_BORE)
    fb_t = holes("dock_target", FLUID_BORE)
    chk(fb_p and fb_t, "fluid pass-through on both halves",
        f"Ø{FLUID_BORE:.1f} through the probe and the target")
    thr = [g for g in AP.cylinders("output/cad/dock_target.step")
           if abs(g["dia"] - 2 * SPG_R) < 0.15]
    chk(len(thr) >= 1, "target spigot fits the probe throat",
        f"spigot Ø{thr[0]['dia']:.2f} into throat Ø{DOCK_THROAT:.2f} -> "
        f"{(DOCK_THROAT-thr[0]['dia'])/2:.2f} mm/side" if thr else "not found")
    # The groove must be a groove, not a parting cut: what is left between its
    # root and the fluid bore is the only thing holding the spigot tip on.
    wall = GRV_R - FLUID_BORE / 2
    chk(wall >= 2.0, "spigot wall survives the capture groove",
        f"{wall:.2f} mm between the groove root Ø{2*GRV_R:.2f} and the "
        f"Ø{FLUID_BORE:.1f} fluid bore")
    # The cone is a lead-in. If it is deeper than the spigot is long, the mouth
    # grounds on the target flange before the latch can reach.
    chk(SPG_H > DOCK_CONE_L, "the spigot out-reaches the capture cone",
        f"spigot {SPG_H:.1f} mm vs cone {DOCK_CONE_L:.1f} mm deep, "
        f"{-SEAT_DZ-DOCK_CONE_L:.1f} mm standoff when latched")

    # --- rack and pinion: does it actually mesh, and what is the stroke?
    from end_effector import (PINION_PCD, TOOTH, JAW_T, GRIP_STROKE,
                              RACK_OFFSET, TOOTH_DEPTH)
    # teeth face the pinion, cut TOOTH_DEPTH into the bar, so the pitch line is
    # half a tooth inside the near face of the bar
    pitch_gap = RACK_OFFSET - JAW_T / 2 + TOOTH_DEPTH / 2
    want = PINION_PCD / 2
    chk(abs(pitch_gap - want) < 1.0, "rack meshes the pinion",
        f"pitch line {pitch_gap:.2f} mm from the pinion axis vs PCD/2 "
        f"{want:.2f} -> {pitch_gap-want:+.2f} mm")
    # stroke: half a pinion revolution moves each rack pi*PCD/2
    stroke = math.pi * PINION_PCD / 2.0
    chk(stroke >= GRIP_STROKE * 0.9, "stroke reaches the design opening",
        f"{stroke:.1f} mm per jaw over half a turn vs {GRIP_STROKE:.0f} mm wanted")
    body_w = 54.0
    jaw_l = 46.0
    chk(jaw_l + stroke / 2 < body_w + 12.0, "racks stay in their channels",
        f"jaw {jaw_l:.0f} mm + {stroke/2:.0f} mm travel inside a {body_w:.0f} mm body")
    # MEASURED tooth depth, off the exported mesh.
    # The check above computes the pitch line from RACK_OFFSET, JAW_T and
    # TOOTH_DEPTH -- three parameters -- and it passed with +0.00 mm while the
    # teeth on the actual part were 1.20 mm deep instead of 2.40, because the
    # cutter was centred on the bar face and half of it cut air. A parameter
    # check cannot see that. Section the jaw and measure the teeth.
    import trimesh as _tm
    _j = _tm.load("output/cad/gripper_jaw.stl", force="mesh")
    _sec = _j.section(plane_origin=[0, 0, 3.0], plane_normal=[0, 0, 1])
    _p2, _ = _sec.to_2D()
    _v = np.vstack([np.asarray(e.discrete(_p2.vertices)) for e in _p2.entities])
    _prof = []
    for _x in np.linspace(-20, 20, 41):
        _n = _v[np.abs(_v[:, 0] - _x) < 0.35]
        if len(_n):
            _prof.append(_n[:, 1].min())
    _depth = (max(_prof) - min(_prof)) if _prof else 0.0
    chk(abs(_depth - TOOTH_DEPTH) < 0.15, "rack teeth are cut to full depth",
        f"measured {_depth:.2f} mm off the mesh vs {TOOTH_DEPTH:.2f} design")

    # the rack channel must not break out of the gripper body
    _wall = 38.0 / 2 - (RACK_OFFSET + (JAW_T + 0.5) / 2)
    chk(_wall >= 1.24, "rack channel stays inside the body",
        f"{_wall:.2f} mm of outer wall (floor 1.24 mm = two 0.62 lines); "
        f"below zero the jaws sit in an open slot")

    # V-groove present on the jaw
    import trimesh
    jm = trimesh.load("output/cad/gripper_jaw.stl", force="mesh")
    chk(jm.volume < 5.0e3 * 1.06, "jaw has the V-groove in the gripping face",
        f"{jm.volume/1000:.2f} cm3 (a flat-faced jaw is larger)")

    # --- every tool part must be ONE fused solid
    # A cadquery .union() of two shapes that do not touch still succeeds; it
    # just returns a compound. That is how the three dock latch lugs were
    # modelled, rendered, drawn and mass-budgeted while floating 5.5 mm clear
    # of the bore they were supposed to grow out of. Count the solids.
    print("\n  SOLID COUNT  (a union that did not touch is still a 'success')")
    # rebuilt from source, not read from the STL: this must catch a stale
    # export as well as a bad boolean
    for name, fn in TOOL_PARTS:
        n = len(fn().val().Solids())
        chk(n == 1, f"{name} is one fused solid",
            f"{n} solid{'' if n == 1 else 's'}")

    # --- does the docking bayonet actually work?
    print("\n  DOCKING MATE  (exact mesh, probe against target)")
    import trimesh as _tm
    P = _tm.load("output/cad/tool_dock.stl", force="mesh")
    T = _tm.load("output/cad/dock_target.stl", force="mesh")

    def mate(rot, gap, dx=0.0):
        """gap = how far short of fully seated the probe still is."""
        t = T.copy()
        t.apply_transform(_tm.transformations.rotation_matrix(
            np.radians(rot), [0, 0, 1]))
        t.apply_translation([dx, 0, SEAT_DZ - FLANGE_H - gap])
        mg = _tm.collision.CollisionManager()
        mg.add_object("probe", P); mg.add_object("target", t)
        return mg.in_collision_internal()

    chk(not mate(0.0, 6.0), "probe slides on — half inserted", "clear at 6 mm short")
    chk(not mate(0.0, 0.0), "probe seats, slots aligned", "clear at full depth")
    chk(not mate(DOCK_TWIST, 0.0), f"J6 can roll {DOCK_TWIST:.0f}° to latch",
        "lugs turn into the groove without binding")
    chk(mate(DOCK_TWIST, 2.0), "latched, it CATCHES on withdrawal",
        "2 mm of pull is blocked by the lugs — this is the latch working")
    chk(not mate(0.0, 6.0) and not mate(0.0, 12.0),
        "rolled back, it RELEASES", "withdraws freely at 0°")

    # capture envelope, measured rather than asserted
    tipz = SEAT_DZ + SPG_H
    lim = 0.0
    for dx in np.arange(0.0, 14.01, 0.25):
        if mate(0.0, tipz + DOCK_CONE_L, dx):
            break
        lim = dx
    chk(lim >= 8.0, "measured capture at the cone mouth",
        f"±{lim:.2f} mm of lateral error still enters "
        f"({lim/1.4:.1f}× the ~1.4 mm the arm can make)")

    print()
    for ok, name, det in R:
        print(f"  [{' PASS ' if ok else ' FAIL '}] {name:42s} {det}")
    bad = [r for r in R if not r[0]]
    print("\n" + "=" * 76)
    print(f"  {len(R)-len(bad)} passed, {len(bad)} failed")
    print("=" * 76)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
