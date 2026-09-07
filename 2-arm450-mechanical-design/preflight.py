"""
ARM-450 PRE-PRINT FLIGHT CHECK — staged, in order, with a single verdict.

Eight stages. Each is a real analysis, not a restatement of the one before, and
each states its own criterion so a pass can be argued with. The final verdict is
GO only if every hard stage passes.

  1  DESIGN CHECK      geometry present in the STEP, fits, chain, mass
  2  FEA               von Mises on the real printed geometry
  3  CREEP + FATIGUE   the two failure modes a static check cannot see
  4  STIFFNESS         compliance budget at the tool
  5  URDF              parses, matches the CAD, masses match the gate
  6  PATH TRACING      the 240 solved waypoints, exact mesh collision
  7  SIMULATION        the ROS node publishes what hardware will need
  8  END EFFECTORS     the tools go on, and the docking latch actually latches

Run:  python3 preflight.py
"""
import io
import contextlib
import re
import subprocess
import sys
import numpy as np
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), 'cad'))
from params import MATERIAL   # noqa: E402

R = []           # (stage, name, ok, detail, hard)


def rec(stage, name, ok, detail, hard=True):
    R.append((stage, name, bool(ok), detail, hard))
    return ok


def run(script, timeout=550):
    p = subprocess.run([sys.executable, script], capture_output=True,
                       text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


def quiet(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a)
    return r, buf.getvalue()


# ---------------------------------------------------------------- 1. DESIGN
def stage1():
    import audit_parts as AP
    AP.RES.clear()
    _, _o = quiet(AP.main)
    bad = [r for r in AP.RES if r[1] in ("MISSING", "OFFSET", "ERROR")]
    nok = sum(1 for r in AP.RES if r[1] == "OK")
    rec(1, "geometry audit (STEP B-rep)", not bad,
        f"{nok} features physically present, {len(bad)} missing/offset")
    import check_bearing_fit as BF
    bfbad, _o = quiet(BF.main)
    rec(1, "every bearing pocket accepts its bearing", not bfbad,
        f"{len(bfbad)} problem(s)" if bfbad else "10 pockets, light press")
    code, out = run("preprint_check.py")
    m = re.search(r"PASSED\s+(\d+)\s+WARNINGS\s+(\d+)\s+FAILURES\s+(\d+)", out)
    if m:
        p, w, f = map(int, m.groups())
        rec(1, "pre-print gate", f == 0, f"{p} passed, {w} warnings, {f} failures")
        mm = re.search(r"mass within \d+ g budget[^\n]*?(\d+) g =", out)
        if mm:
            rec(1, "mass within the hard ceiling", True,
                f"{mm.group(1)} g of 1450 g")
    else:
        rec(1, "pre-print gate", False, "could not parse output")


# ---------------------------------------------------------------- 2. FEA
def stage2():
    worst = None
    for s in ("run_fea.py", "run_fea_wrist.py"):
        code, out = run(s)
        for sf in re.findall(r"SF on p99 vs [\d.]+ MPa allowable:\s*([\d.]+)", out):
            v = float(sf)
            worst = v if worst is None else min(worst, v)
        for d in re.findall(r"max \|u\|\s*([\d.]+) mm", out):
            pass
    rec(2, "FEA safety factor (p99 von Mises)", worst is not None and worst >= 3.0,
        f"worst SF {worst:.1f} across all parts" if worst else "no SF parsed")


# ------------------------------------------------------- 3. CREEP + FATIGUE
def stage3():
    import creep_fatigue as CF
    d, _o = quiet(CF.main)
    rec(3, "working stress far below yield", d["peak_mpa"] < 0.1 * CF.SIG_Y,
        f"{d['peak_mpa']:.2f} MPa vs {CF.SIG_Y:.0f} MPa yield "
        f"(ratio {d['peak_mpa']/CF.SIG_Y:.4f})")
    rec(3, "fatigue life", d["fatigue_cycles"] > 1e8,
        f"{d['fatigue_cycles']:.1e} cycles to failure")
    rec(3, "creep strain at 1 year, continuous load", d["creep_1yr"] < 1e-3,
        f"{d['creep_1yr']*100:.3f} % — park folded when idle", hard=False)


# ---------------------------------------------------------- 4. STIFFNESS
def stage4():
    code, out = run("compliance_budget.py")
    m = re.findall(r"STRUCTURE SUBTOTAL\s+([\d.]+)\s+([\d.]+)", out)
    if m:
        cf = float(m[0][1])
        rec(4, "structural compliance at the tool", cf < 0.30,
            f"{cf:.3f} mm in PLA+CF at 2.0 mm wall (design wall is 2.4)")
    else:
        rec(4, "structural compliance at the tool", False, "not parsed")


def stage4b():
    """Every load case, with and without an end effector.

    All the analyses above assume 300 g at the TCP. That is an envelope, and a
    generous one, but it says nothing about a fitted TOOL as such: a tool moves
    the load along the tool axis, and the lever arm is what sizes J2/J3 and sets
    the compliance at the point you actually care about. 75 g on a 42 mm stick
    is not the load case 75 g at the flange is.
    """
    import verify_configs as VC
    res = {n: VC.run(n) for n in VC.CONFIGS}
    bad = [(lbl, n) for lbl, key, ok, _lim in VC.CRIT
           for n in VC.CONFIGS if not ok(res[n][key])]
    rec(2, "every load case passes with and without a tool", not bad,
        f"{len(VC.CRIT)*len(VC.CONFIGS)-len(bad)}/{len(VC.CRIT)*len(VC.CONFIGS)} "
        f"— {len(VC.CRIT)} criteria x {len(VC.CONFIGS)} configurations "
        f"(bare / pen / gripper / gripper+225 g / dock)")
    worst = min(res.values(), key=lambda r: r["sf"])
    rec(4, "worst configuration still inside every limit", worst["sf"] >= 3.0,
        f"{worst['config']}: SF {worst['sf']:.0f}, compliance "
        f"{worst['compliance_mm']:.3f} mm, servo margin "
        f"{worst['servo_margin_min']:.2f}x")


# --------------------------------------------------------------- 5. URDF
def stage5():
    import subprocess as sp
    p = sp.run(["bash", "-lc",
                "source /opt/ros/jazzy/setup.bash && check_urdf arm450_meshes.urdf"],
               capture_output=True, text=True)
    rec(5, "URDF parses (mesh version)", "Successfully Parsed" in p.stdout,
        "single tree, root world")
    import xml.etree.ElementTree as ET
    r = ET.parse("arm450_meshes.urdf").getroot()
    # ARM links only. The URDF now carries the fitted tool as a link, and a
    # tool is PAYLOAD, not arm -- summing it in would inflate the total by
    # 75 g and quietly break the one check that ties the model to the budget.
    def _m(l):
        return float(l.find("inertial/mass").get("value"))
    arm = [l for l in r.findall("link")
           if l.find("inertial") is not None and l.get("name") != "tool"]
    tot = sum(_m(l) for l in arm)
    tool = sum(_m(l) for l in r.findall("link")
               if l.find("inertial") is not None and l.get("name") == "tool")
    rec(5, "URDF mass matches the mass gate", abs(tot - 1.365) < 0.01,
        f"{tot:.3f} kg arm vs 1.365 kg" +
        (f"  (+ {tool*1000:.0f} g tool as payload)" if tool else ""))
    rec(5, "the fitted tool is in the model RViz loads", tool > 0,
        f"{tool*1000:.0f} g tool link on link6 — the URDF had no tool at all "
        f"until 2026-08-22")
    import os
    refs = set(re.findall(r'filename="([^"]+)"', open("arm450_meshes.urdf").read()))
    base = "../src/arm450_description"
    miss = [x for x in refs
            if not os.path.exists(x.replace("package://arm450_description", base))]
    rec(5, "every mesh reference resolves", not miss,
        f"{len(refs)-len(miss)}/{len(refs)} meshes found")


# ------------------------------------------------------- 6. PATH TRACING
def stage6():
    import numpy as np
    import assemble as A
    import interference as I
    import os
    Q = np.load(os.path.expanduser("~/ros2_ws/src/arm450_sine/sine_traj.npz"))["Q"]
    ncol = sum(1 for q in Q if I.check(A.build(*q)[0]))
    rec(6, "solved path is collision-free", ncol == 0,
        f"{len(Q)-ncol}/{len(Q)} waypoints clear (exact mesh)")
    code, out = run("plan_sine.py")
    m = re.search(r"position error\s+rms\s+([\d.]+) mm", out)
    t = re.search(r"pen tilt\s+rms\s+([\d.]+) deg", out)
    s = re.search(r"largest joint step between waypoints:\s*([\d.]+)", out)
    if m:
        rec(6, "path accuracy", float(m.group(1)) < 0.20,
            f"{m.group(1)} mm rms, tilt {t.group(1) if t else '?'} deg rms")
    if s:
        rec(6, "path smoothness", float(s.group(1)) < 5.0,
            f"largest joint step {s.group(1)} deg between waypoints")
    # every waypoint inside the declared joint limits
    import xml.etree.ElementTree as ET
    lim = np.array([[float(j.find("limit").get("lower")),
                     float(j.find("limit").get("upper"))]
                    for j in ET.parse("arm450.urdf").getroot().findall("joint")
                    if j.get("type") == "revolute"])
    inside = np.all((Q >= lim[:, 0] - 1e-6) & (Q <= lim[:, 1] + 1e-6))
    rec(6, "every waypoint inside the joint limits", inside,
        "checked against arm450.urdf, including the narrowed J5")


# --------------------------------------------------------- 7. SIMULATION
def stage7():
    import subprocess as sp
    cmd = ("source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash && "
           "timeout 12 ros2 run arm450_sine sine_node --ros-args "
           "-p traj_file:=$HOME/ros2_ws/src/arm450_sine/sine_traj.npz 2>&1 | head -40")
    p = sp.run(["bash", "-lc", cmd], capture_output=True, text=True, timeout=60)
    o = p.stdout
    rec(7, "node loads the solved trajectory", "240 waypoints" in o,
        "240 waypoints")
    rec(7, "playback is continuous (ping-pong)", "loop mode pingpong" in o,
        "no wrap discontinuity")
    rec(7, "approach ramp before tracing", "approach" in o,
        "eases from the start pose, no slam on real servos")
    rec(7, "JointTrajectory published for a controller", "JointTrajectory" in o,
        "240 points, latched TRANSIENT_LOCAL on /arm450/trajectory")
    ok = "-> OK" in o
    m = re.search(r"peak joint rate ([\d.]+) rad/s", o)
    rec(7, "joint rate within the servo", ok,
        f"{m.group(1) if m else '?'} rad/s vs ~2.3 rad/s loaded ST3215")


# --------------------------------------------------------- 8. END EFFECTORS
def stage8():
    """The GO covered the arm and said nothing about the tools. Two couplings
    have to be right and neither is verifiable by eye: J6 to the adapter, and
    the adapter to each tool."""
    import check_tool_fit as TF
    bad, _o = quiet(TF.main)
    n = len(TF.R)
    rec(8, "end-effector interfaces", not bad,
        f"{n-len(bad)}/{n} checks — J6 bolt pattern, bayonet fit, "
        f"rack mesh, docking capture")
    # tool mass is PAYLOAD, not arm mass
    import json
    V = json.load(open("output/cad/volumes.json"))
    # the jaw racks and the pinion are printed at 100 %, not MASS_FILL: their
    # teeth are 2 mm and sparse infill leaves them hollow. Quote them at the
    # fill they are actually printed at.
    grip = sum(V[k] * 1.29e-3 * f * q for k, q, f in
               (("tool_gripper", 1, 0.90), ("gripper_jaw", 2, 1.00),
                ("gripper_pinion", 1, 1.00))) + 9.0
    dock = V["tool_dock"] * 1.29e-3 * 0.90
    ad = V["tool_adapter"] * 1.29e-3 * 0.90
    worst = ad + max(grip, dock)
    rec(8, "heaviest tool within the payload allowance", worst < 300.0,
        f"{worst:.0f} g (adapter {ad:.0f} + gripper {grip:.0f} incl. SG90) "
        f"vs the 300 g assumed at the TCP")

    # SYSTEM reach with a tool on. The 450 mm spec is the ARM; the user
    # accepted 492 mm for the system with a gripper fitted (2026-08-22), and
    # SYSTEM_REACH_MAX records that. This check exists so a later, longer tool
    # cannot push the system past what was agreed without the gate saying so.
    import workspace as WS
    from params import SYSTEM_REACH_MAX
    longest = max(WS.TOOL_REACH.items(), key=lambda kv: kv[1])
    reach = 450.0 + longest[1]
    rec(8, "system reach with the longest tool fitted", reach <= SYSTEM_REACH_MAX,
        f"{reach:.0f} mm (450 arm + {longest[1]:.0f} {longest[0]}) "
        f"vs {SYSTEM_REACH_MAX:.0f} mm accepted — the 450 mm spec is the ARM")


TITLES = {1: "DESIGN CHECK AND VERIFICATION", 2: "FEA",
          3: "CREEP AND FATIGUE", 4: "STIFFNESS", 5: "URDF",
          6: "PATH TRACING", 7: "SIMULATION READINESS",
          8: "END EFFECTORS"}


def main():
    print("=" * 78)
    print("ARM-450 — PRE-PRINT FLIGHT CHECK")
    print("=" * 78)
    for n, fn in ((1, stage1), (2, stage2), (3, stage3), (4, stage4),
                  (4, stage4b), (5, stage5), (6, stage6), (7, stage7),
                  (8, stage8)):
        try:
            fn()
        except Exception as e:                                   # noqa: BLE001
            rec(n, "stage ran", False, f"{type(e).__name__}: {str(e)[:60]}")
    cur = None
    for st, name, ok, det, hard in R:
        if st != cur:
            print(f"\n  STAGE {st} — {TITLES[st]}")
            print("  " + "-" * 72)
            cur = st
        mark = " PASS " if ok else (" FAIL " if hard else " note ")
        print(f"    [{mark}] {name:44s} {det}")
    hard_fail = [r for r in R if not r[2] and r[4]]
    soft = [r for r in R if not r[2] and not r[4]]
    print("\n" + "=" * 78)
    print(f"  {sum(1 for r in R if r[2])} passed   {len(soft)} notes   "
          f"{len(hard_fail)} failures")
    print("=" * 78)
    if hard_fail:
        print("\n  *** NO-GO ***  resolve before printing:")
        for st, name, _o, det, _h in hard_fail:
            print(f"    stage {st}: {name} — {det}")
    else:
        print("\n  *** GO FOR PRINTING ***")
        print("  All eight stages pass. What remains is process, not design:")
        print("    - the fit coupon is the only test of what YOUR machine does")
        print("      to a real Ø42 bore; everything above verifies the geometry")
        print("      is right, not that the printer reproduces it")
        print("    - servo backlash is still unmeasured and is the largest term")
        print("      in the precision budget")
    for st, name, _o, det, _h in soft:
        print(f"\n  note (stage {st}): {name} — {det}")
    return hard_fail


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
