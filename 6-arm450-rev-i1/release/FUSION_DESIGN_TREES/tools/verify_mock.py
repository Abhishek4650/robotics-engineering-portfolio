#!/usr/bin/env python3
"""
Run every emitted part script against the mock Fusion API (mock_adsk/:
OpenCascade under Fusion's calls) and compare what it builds with the
released STEP: boolean difference both ways (mm3), volume, bounding box,
one body. Proves the scripts + feature lists rebuild the released parts; it
cannot prove how Fusion itself evaluates each feature (no Fusion here).

Run:  python3 verify_mock.py [part-name-filter]
"""
import glob
import sys as _sys
_sys.dont_write_bytecode = True        # no __pycache__ inside the part folders
import importlib.util
import os
import sys
import tempfile
import time

TOOLS = os.path.dirname(os.path.abspath(__file__))
TREES = os.path.dirname(TOOLS)
sys.path.insert(0, os.path.join(TOOLS, "mock_adsk"))
import adsk.core                                   # noqa: E402  (the mock)
import cadquery as cq                              # noqa: E402
sys.path.insert(0, TOOLS)
import compare                                     # noqa: E402
from OCP.gp import gp_Trsf, gp_Pnt                 # noqa: E402
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform   # noqa: E402
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Common   # noqa: E402
from OCP.GProp import GProp_GProps                 # noqa: E402
from OCP.BRepGProp import BRepGProp                # noqa: E402


def vol(s):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(s, g)
    return g.Mass()


def main():
    flt = sys.argv[1] if len(sys.argv) > 1 else ""
    scripts = sorted(glob.glob(os.path.join(TREES, "parts", "*", "*.py")) +
                     glob.glob(os.path.join(TREES, "fit_test", "*", "*.py")))
    out = tempfile.mkdtemp(prefix="arm450_mock_")
    app = adsk.core.Application.get()
    rows, bad = [], 0
    for sc in scripts:
        name = os.path.basename(sc)[:-3]
        if flt not in name:
            continue
        spec = importlib.util.spec_from_file_location("part_" + name, sc)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        t = time.time()
        ok, rep = mod.build_part(app, os.path.join(os.path.dirname(sc), name + ".json"), out_dir=out)
        d = app._designs[-1]
        bodies = d.rootComponent.bodies
        ref = cq.importers.importStep(os.path.join(os.path.dirname(sc), name + "_released.step")).val().wrapped
        line = "%-30s " % name
        if bodies:
            tr = gp_Trsf(); tr.SetScale(gp_Pnt(0, 0, 0), 10.0)          # cm -> mm
            got = BRepBuilderAPI_Transform(bodies[0].shape, tr, True).Shape()
            a, b = compare.diff(ref, got)
            good = ok and len(bodies) == 1 and a < 0.01 and b < 0.01
            line += "bodies %d  timeline %4d  released-minus-built %.5f  built-minus-released %.5f mm3  %s" % (
                len(bodies), d.timeline.count, a, b, "OK" if good else "FAIL")
        else:
            good = False
            line += "NO BODY  " + rep.splitlines()[-1]
        if d.warnings:
            line += "  warnings: %d (%s)" % (len(d.warnings), d.warnings[0])
        if not good:
            line += "\n" + "\n".join("      " + x for x in rep.splitlines() if "STOPPED" in x or "failed" in x or "Error" in x)
        line += "  (%.0f s)" % (time.time() - t)
        bad += 0 if good else 1
        rows.append(line)
        print(line, flush=True)
    txt = ("MOCK-FUSION REBUILD of every part script vs the released STEP\n"
           "(OpenCascade under Fusion's API calls; boolean difference both ways)\n\n" + "\n".join(rows) +
           "\n\n%d scripts, %d FAIL\n" % (len(rows), bad))
    if not flt:
        strict = os.environ.get("MOCK_STRICT") == "1"
        txt = txt.replace("MOCK-FUSION REBUILD", "MOCK-FUSION REBUILD (%s mode: %s)" % (
            "STRICT" if strict else "normal",
            "a cut tool that misses its body, or a join of bodies that do not touch, is REFUSED" if strict else
            "Fusion accepts a cut tool that misses and a join of separate bodies"))
        open(os.path.join(TREES, "VERIFY_MOCK_FUSION%s.log" % ("_STRICT" if strict else "")), "w").write(txt)
    print("\n%d scripts, %d FAIL" % (len(rows), bad))
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
