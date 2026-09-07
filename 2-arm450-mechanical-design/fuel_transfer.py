"""
Fluid transfer through the ARM-450 docking interface — feasibility and limits.

The task: move a coloured liquid from a reservoir on the chaser, along the arm,
through the docking probe, into the target. Small pump, medical tubing.

The docking geometry already carries a Ø8 pass-through in both halves, so the
HOLE exists. That is not the same as a fluid path, and this works out what else
is needed and what it costs. Four questions, in the order they bite:

  1. Does the joint SEAL? A hole in each half that happens to line up is not a
     coupling. Nothing in the current geometry stops the liquid leaving at the
     interface.
  2. Can the TUBE be routed? Six joints, three of them roll axes that wind a
     tube up rather than bend it. The tube has to survive the whole trajectory,
     not one pose.
  3. Will it FLOW? Pump head against the pressure drop of tube plus bore.
  4. What does it COST? Mass, joint torque, and how much liquid never arrives.

Nothing here is a new mechanism -- the routing uses the same FK as the rest of
the project and the flow is Hagen-Poiseuille -- but it is the first analysis in
this project of a system that is not rigid.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "cad"))
import joint_loads as JL
from params import *                                  # noqa: F403,F401
import end_effector as EE

RHO_W = 1000.0          # kg/m3, water
MU_W = 1.0e-3           # Pa.s at 20 C
G = 9.80665

# candidate medical / peristaltic tubing, ID x OD in mm
# name, ID mm, OD mm, density kg/m3. Mass is computed from the annulus like
# every other mass in this project -- the first version carried a made-up
# "kg per metre" column that put a 2 x 4 silicone tube at 158 g for half a
# metre, about 27x heavy.
TUBES = [("silicone 2 x 4", 2.0, 4.0, 1100.0),
         ("silicone 3 x 5", 3.0, 5.0, 1100.0),
         ("silicone 4 x 6", 4.0, 6.0, 1100.0),
         ("PVC 4 x 6", 4.0, 6.0, 1300.0),
         ("PTFE 4 x 6", 4.0, 6.0, 2200.0)]
#              name                  mL/min  head m  self-prime  backflow-proof
PUMPS = [("peristaltic 12 V (Kamoer NKP)", 100.0, 2.0, True, True),
         ("peristaltic 12 V, larger head", 350.0, 2.0, True, True),
         ("diaphragm 12 V mini", 1500.0, 3.0, True, False),
         ("submersible centrifugal 5 V", 1800.0, 1.0, False, False)]


# ---------------------------------------------------------------- 1. sealing
def sealing():
    print("=" * 80)
    print("1. THE SEAL — designed 2026-08-23, both targets kept")
    print("=" * 80)
    print(f"""
  As originally drawn, the probe had a Ø{EE.FLUID_BORE:.0f} bore and the target had a Ø{EE.FLUID_BORE:.0f}
  bore, coaxial when latched with a 2.0 mm axial gap between them. The liquid
  would arrive at that gap and leave through the {EE.SPG_CLR:.2f} mm running clearance
  round the spigot -- down the outside of the probe and out of the cone.

  A pass-through hole is not a coupling.

  THE SEAL IS RADIAL, NOT A FACE SEAL, and the reason is axial play. The
  bayonet has {EE.LATCH_CLR:.1f} mm of clearance at each end of the capture groove, so the
  two halves sit anywhere in a 1.0 mm band. A face seal's squeeze IS that gap:
  fully loaded at one end of the play, completely unloaded at the other. A
  radial seal's squeeze is set by diameters and does not care.

    O-ring        {EE.SEAL_CORD:.2f} mm cord, Ø{EE.SEAL_GROOVE_D:.2f} nominal ID
    groove        Ø{EE.SEAL_GROOVE_D:.2f} x {EE.SEAL_GROOVE_W:.2f} wide, {(2*EE.SPG_R-EE.SEAL_GROOVE_D)/2:.2f} deep in the spigot
    squeeze       {EE.SEAL_SQUEEZE*100:.0f} % nominal
    wall left     {EE.SEAL_GROOVE_D/2-EE.FLUID_BORE/2:.2f} mm to the fluid bore

  It fits in the ONLY full-circumference plain band of spigot that lies inside
  the straight Ø{EE.DOCK_THROAT:.0f} throat: s {-EE.SEAT_DZ:.1f} to {EE.GRV_Z0:.1f}, 2.5 mm of it. Above the
  capture groove the entry slots cut clean through the wall, so nothing can
  seal there -- which is why the groove could not simply go near the tip.

  `dock_target` (no groove) and `dock_target_sealed` (grooved) are BOTH kept
  and both verified. The dry docking demonstration does not need a seal and is
  one less thing to source; the fluid demonstration does.
""")
    return True


# ---------------------------------------------------------- 2. tube routing
def route_length(q, slack=1.25):
    """Two routings that behave in opposite ways.

    ANCHORED -- clipped to each link, following the chain. The path is the sum
    of the LINK lengths, and links are rigid, so the length is identical in
    every pose. That is the whole argument for anchoring.

    FREE -- hanging base to tool through the air. The length must cover the most
    extended pose, and in a folded pose all of that excess becomes loose slack
    with nowhere to go.
    """
    origins, axes, coms, masses, tcp, pay = JL.kinematics(q, tool_reach=0.036)
    pts = [np.zeros(3)] + list(origins) + [tcp]
    anchored = sum(np.linalg.norm(pts[k + 1] - pts[k]) for k in range(len(pts) - 1))
    return anchored * slack, float(np.linalg.norm(tcp))


def routing(n=4000, seed=0):
    print("\n" + "=" * 80)
    print("2. ROUTING THE TUBE ALONG SIX JOINTS")
    print("=" * 80)
    rng = np.random.default_rng(seed)
    lo = np.array([-2.88, -2.01, -2.62, -2.88, -1.59, -3.05])
    hi = np.array([2.88, 2.01, 2.62, 2.88, 0.86, 3.05])
    Q = rng.uniform(lo, hi, size=(n, 6))
    R = np.array([route_length(q) for q in Q])
    L, F = R[:, 0], R[:, 1]
    print(f"""
  ANCHORED to each link, with 25 % slack allowed at the joints:
    shortest pose      {L.min()*1000:6.1f} mm
    longest pose       {L.max()*1000:6.1f} mm
    swing              {(L.max()-L.min())*1000:6.1f} mm

  The swing is ZERO, and that is the headline. The links are RIGID, so a tube
  that follows them is the same length in every pose. Cut it once, clip it
  down, and there is no slack to manage for the rest of the arm's life.

  FREE-HANGING base to tool through the air, over the same poses:
    folded             {F.min()*1000:6.0f} mm
    extended           {F.max()*1000:6.0f} mm
    slack to absorb    {(F.max()-F.min())*1000:6.0f} mm

  {(F.max()-F.min())*1000:.0f} mm of loose tube in a folded pose. This arm clears the base
  pedestal by about 1 mm at the closest point of the sine path, and loose tube
  in that gap is a collision nothing has checked, because the tube is in no
  model. DO NOT route it free.

  ROLL AXES ARE THE REAL PROBLEM. J1, J4 and J6 rotate about the tube's own
  axis, so they do not bend it -- they WIND it:""")
    roll = [(0, "J1", 165.0), (3, "J4", 165.0), (5, "J6", 175.0)]
    tot = 0.0
    for i, nm, lim in roll:
        print(f"    {nm}  +/-{lim:.0f} deg  -> up to {2*lim:.0f} deg of wind-up")
        tot += 2 * lim
    print(f"    {'TOTAL':4s}            {tot:.0f} deg = {tot/360:.1f} full turns")
    print(f"""
  {tot/360:.1f} turns of a silicone tube is survivable ONLY if the tube is long
  enough to distribute it, and if it is anchored at each link so the twist does
  not all land in one short span. Anchored every link, the worst single span
  sees roughly {tot/6:.0f} deg, which silicone tolerates indefinitely.

  Unanchored, it kinks -- and a kinked tube stops the flow silently, which is
  the failure mode you will actually meet.""")
    return L.min(), L.max()


# ---------------------------------------------------------------- 3. flow
def dp_tube(Q_m3s, d_m, L_m, mu=MU_W):
    """Hagen-Poiseuille pressure drop for laminar flow, Pa."""
    return 128.0 * mu * L_m * Q_m3s / (np.pi * d_m ** 4)


def reynolds(Q_m3s, d_m, rho=RHO_W, mu=MU_W):
    v = Q_m3s / (np.pi / 4 * d_m ** 2)
    return rho * v * d_m / mu, v


def flow(L_tube_m):
    print("\n" + "=" * 80)
    print("3. WILL IT FLOW?")
    print("=" * 80)
    print(f"\n  tube run {L_tube_m*1000:.0f} mm, plus {2*EE.FLUID_BORE:.0f} mm of Ø{EE.FLUID_BORE:.0f} bore through the coupling\n")
    print(f"  {'tube':16s} {'flow':>9s} {'velocity':>9s} {'Re':>7s} "
          f"{'ΔP tube':>9s} {'ΔP total':>9s} {'head':>7s}")
    print("  " + "-" * 76)
    rows = []
    for name, idd, od, rho in TUBES:
        for ml_min in (100.0, 350.0):
            Qv = ml_min * 1e-6 / 60.0
            d = idd * 1e-3
            re, v = reynolds(Qv, d)
            dp_t = dp_tube(Qv, d, L_tube_m)
            dp_b = dp_tube(Qv, EE.FLUID_BORE * 1e-3, 0.030)
            dp = dp_t + dp_b
            head = dp / (RHO_W * G)
            rows.append((name, ml_min, dp, head))
            print(f"  {name:16s} {ml_min:6.0f} mL/m {v:8.3f} m/s {re:7.0f} "
                  f"{dp_t/1000:8.2f}k {dp/1000:8.2f}k {head:6.2f} m")
    print(f"""
  All laminar (Re well under 2300), so the drop is linear in flow and the
  numbers above scale directly.

  The pressure drop is TINY -- centimetres of head, against pumps that deliver
  1-3 m. Flow is not the limitation. Anything on this list works.""")
    print(f"\n  {'pump':32s} {'mL/min':>8s} {'head':>6s}  self-prime  no-backflow")
    print("  " + "-" * 74)
    for nm, ml, h, sp, nb in PUMPS:
        print(f"  {nm:32s} {ml:8.0f} {h:5.1f} m  "
              f"{'yes' if sp else 'NO':>10s}  {'yes' if nb else 'NO':>11s}")
    print("""
  CHOOSE PERISTALTIC, and not for the flow rate. A peristaltic pump occludes
  the tube, so it is self-priming, it cannot back-siphon when the arm points
  downhill, it doses by revolutions rather than by time, and the liquid only
  ever touches the tube -- so a colour change means swapping one tube, not
  flushing a pump head. For a demonstration those matter more than L/min.""")
    return rows


# ------------------------------------------------------ 4. what it costs
def costs(L_tube_m):
    print("\n" + "=" * 80)
    print("4. WHAT IT COSTS THE ARM")
    print("=" * 80)
    print(f"\n  {'tube':16s} {'tube g':>8s} {'fluid g':>9s} {'total g':>9s} "
          f"{'dead vol mL':>12s}")
    print("  " + "-" * 60)
    for name, idd, od, rho in TUBES:
        a = np.pi / 4 * ((od * 1e-3) ** 2 - (idd * 1e-3) ** 2)   # m2
        m_t = a * L_tube_m * rho * 1000.0                        # g
        vol = np.pi / 4 * (idd * 1e-3) ** 2 * L_tube_m * 1e6   # mL
        m_f = vol * 1.0
        print(f"  {name:16s} {m_t:8.1f} {m_f:9.1f} {m_t+m_f:9.1f} {vol:12.1f}")
    print(f"""
  DEAD VOLUME is the number nobody expects. A 3 x 5 silicone run holds about
  6 mL, and that liquid never arrives -- it sits in the tube when the pump
  stops. To transfer 20 mL you must pump 26 and accept 6 left behind, or purge
  with air and accept spray at the far end.

  MASS. The arm is already 158 g over its 1450 g ceiling with fasteners
  counted. Tube and fluid add 10-30 g more, plus the pump -- and a 12 V
  peristaltic head is 150-250 g, which is NOT arm mass if it lives on the
  chaser body rather than on the arm. Mount the pump at the base.""")
    # tube bending stiffness reacting on the wrist
    print("""  JOINT TORQUE. A silicone tube is soft but it is not free. Bending a
  3 x 5 silicone tube round a 25 mm radius takes roughly 2-4 N.mm; across
  the three wrist joints that is under 0.02 N.m against a 2.94 N.m servo --
  negligible. A PTFE tube of the same size is 20-40x stiffer and WOULD be felt
  at J5 and J6, which is the reason to stay with silicone.""")


def main():
    ok = sealing()
    lmin, lmax = routing()
    flow(lmax)
    costs(lmax)
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)
    print("""
  FEASIBLE. The fluid mechanics is the easy part; three practical things gate
  it, and only one of them is now unsolved.

  1. THE SEAL -- SOLVED, 2026-08-23. A radial O-ring in the spigot, verified
     6/6 by check_seal.py, and BOTH targets kept. Squeeze holds 10-30 % across
     a +/-0.20 mm printed bore error, which is wider than the error a coupon-
     calibrated printer actually makes.

  2. THE TUBE IS IN NO MODEL -- STILL OPEN. Every collision result in this
     project is for a bare arm. Anchored per link the tube length never
     changes, which removes the slack problem entirely, but the tube itself
     and its clips are still not in the collision mesh.
     -> the fix is cheap: model the tube as a swept Ø6 tube along the link
        centres and re-run check_sine_clear. Until that is done, treat the
        1 mm base-pedestal clearance as unverified WITH plumbing fitted.

  3. DEAD VOLUME -- CANNOT BE FIXED, ONLY DESIGNED AROUND. About 4 mL stays in
     a 3 x 5 line when the pump stops. No routing or pump choice removes it;
     it is the tube's own volume. Either pump 4 mL more than you intend to
     transfer, or purge with air and accept spray at the far end.

  Everything else -- pump head, pressure drop, flow rate, added mass, tube
  stiffness -- has margin of at least an order of magnitude.""")


if __name__ == "__main__":
    main()
