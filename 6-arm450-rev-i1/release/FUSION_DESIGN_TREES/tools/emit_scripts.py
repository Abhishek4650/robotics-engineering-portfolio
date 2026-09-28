#!/usr/bin/env python3
"""
Write one Fusion 360 script folder per part from _programs/*.json:

  parts/<NN_part_xQ>/<NN_part_xQ>.py        the script (engine + run())
  parts/<NN_part_xQ>/<NN_part_xQ>.manifest  Fusion's script registration
  parts/<NN_part_xQ>/<NN_part_xQ>.json      the part's feature list
  parts/<NN_part_xQ>/<NN_part_xQ>_released.step   the released solid, for comparison
  00_BUILD_ALL_f3d/                          one script that builds + saves every part
"""
import glob
import json
import os
import shutil

TOOLS = os.path.dirname(os.path.abspath(__file__))
TREES = os.path.dirname(TOOLS)
PROJ = os.path.dirname(TREES)
ENGINE = open(os.path.join(TOOLS, "fusion_engine.py")).read()

PART_DOC = '''"""
ARM-450 rev I -- %(part)s  (print %(qty)d)  --  Fusion 360 DESIGN-TREE script

WHAT IT DOES
  Builds this part in a NEW Fusion design as a parametric timeline --
  %(nsteps)d features: %(counts)s --
  the same sketches, extrudes, lofts, cuts, joins, fillets and chamfers the
  ARM-450 generator made it with, in the same order, each named after the
  generator line it came from (hover a timeline item to see it). Then it
  checks the result against the released part (volume and bounding box) and
  saves  %(file)s.f3d  and  %(file)s_BUILD_REPORT.txt  in this folder.

RUN IT
  Fusion 360 > UTILITIES > ADD-INS > Scripts and Add-Ins (Shift+S) >
  Scripts tab > the green "+" > pick THIS folder > select %(file)s > Run.
  (Or run ../../00_BUILD_ALL_f3d once to make every part's .f3d.)

EDIT IT
  Open %(file)s.f3d (File > Open > Open from my computer) -- or keep the
  design the script left open. Every timeline item can be edited: double-
  click a sketch to change its lines / circles, an extrude for its distance,
  a fillet for its radius; roll the timeline marker back to insert features.
  Bodies that are not square to the XY plane are sketched on XY and placed by
  a "move" feature right after their extrude.

  Frame: the part is built where it sits in the arm's design frame (the
  released STEP frame, mm) -- see ../../README.md for the print orientation.
  Released solid, for comparison: %(file)s_released.step
"""
'''

RUN = '''

HERE = os.path.dirname(os.path.realpath(__file__))


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        ok, report = build_part(app, os.path.join(HERE, "%(file)s.json"))
        ui.messageBox(report, "ARM-450 %(part)s")
    except Exception:
        ui.messageBox("ARM-450 %(part)s: the script failed\\n\\n" + traceback.format_exc())
'''

ALL_DOC = '''"""
ARM-450 rev I -- build EVERY part's Fusion design tree and save it as .f3d.

Runs each part script's feature list in turn (parts/ and fit_test/ next to
this folder), saves <part>.f3d + <part>_BUILD_REPORT.txt in that part's
folder, closes the document, and writes BUILD_ALL_REPORT.txt here.
Takes a while (%(n)d parts, %(steps)d features in all).

Fusion 360 > UTILITIES > ADD-INS > Scripts and Add-Ins > "+" > pick this
folder > Run.
"""
'''

ALL_RUN = '''

HERE = os.path.dirname(os.path.realpath(__file__))


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    top = os.path.dirname(HERE)
    jobs = sorted(glob.glob(os.path.join(top, "parts", "*", "*.json")) +
                  glob.glob(os.path.join(top, "fit_test", "*", "*.json")))
    lines, bad = [], 0
    for j in jobs:
        try:
            ok, rep = build_part(app, j, close=True)
        except Exception:
            ok, rep = False, traceback.format_exc()
        bad += 0 if ok else 1
        summ = next((x for x in rep.splitlines() if x.startswith(("bodies", "BUILD STOPPED"))), rep.splitlines()[-1])
        lines.append(("OK     " if ok else "CHECK  ") + os.path.basename(j)[:-5] + "   " + summ)
        adsk.doEvents()
    txt = "ARM-450 rev I -- build all: %d parts, %d to check\\n\\n" % (len(jobs), bad) + "\\n".join(lines)
    open(os.path.join(HERE, "BUILD_ALL_REPORT.txt"), "w").write(txt + "\\n")
    ui.messageBox(txt[:3000], "ARM-450 build all")
'''


def manifest(desc):
    return json.dumps({"autodeskProduct": "Fusion360", "type": "script", "author": "ARM-450 rev I",
                       "description": {"": desc}, "supportedOS": "windows|mac", "editEnabled": True}, indent=1)


def main():
    progs = sorted(glob.glob(os.path.join(TREES, "_programs", "*.json")))
    total = 0
    for sub in ("parts", "fit_test", "00_BUILD_ALL_f3d"):
        if os.path.isdir(os.path.join(TREES, sub)):
            shutil.rmtree(os.path.join(TREES, sub))
    for p in progs:
        P = json.load(open(p))
        sub = "fit_test" if P["file"].startswith("fit_") else "parts"
        d = os.path.join(TREES, sub, P["file"])
        os.makedirs(d)
        counts = ", ".join("%d %s" % (n, {"ext": "extrude", "bool": "combine", "sub": "pick",
                                          "group": "group"}.get(k, k)) for k, n in sorted(P["counts"].items()))
        info = dict(part=P["part"], qty=P["qty"], file=P["file"], nsteps=len(P["steps"]), counts=counts)
        total += len(P["steps"])
        open(os.path.join(d, P["file"] + ".py"), "w").write(PART_DOC % info + ENGINE + RUN % info)
        open(os.path.join(d, P["file"] + ".manifest"), "w").write(
            manifest("ARM-450 rev I %s: build the design tree, save %s.f3d" % (P["part"], P["file"])))
        shutil.copy(p, os.path.join(d, P["file"] + ".json"))
        shutil.copy(os.path.join(PROJ, P["released_step"]), os.path.join(d, P["file"] + "_released.step"))
    d = os.path.join(TREES, "00_BUILD_ALL_f3d")
    os.makedirs(d)
    open(os.path.join(d, "00_BUILD_ALL_f3d.py"), "w").write(
        ALL_DOC % dict(n=len(progs), steps=total) + "import glob\n" + ENGINE + ALL_RUN)
    open(os.path.join(d, "00_BUILD_ALL_f3d.manifest"), "w").write(
        manifest("ARM-450 rev I: build every part's design tree and save each as .f3d"))
    print("wrote %d part folders, %d features in all" % (len(progs), total))


if __name__ == "__main__":
    main()
