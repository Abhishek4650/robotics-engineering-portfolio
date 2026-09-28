"""
ARM-450 rev I -- Fusion 360 script: EVERY file of this folder into Fusion.
(Utilities > Scripts and Add-Ins > + > this folder > ARM450_import_all > Run)

For every STEP in ../parts_step (the 27 printed parts), ../fit_test_step (the
7 fit-test coupons) and ../assembly_step (the whole arm + the 7 rigid bodies):
  * imports it into its own new Fusion design,
  * saves that design in your active project, in a folder of the same name
    under "ARM450_rev_I" (parts_step / fit_test_step / assembly_step),
  * and exports a local .f3d next to this script, in f3d/<folder>/.
The joints assembly with draggable revolute joints is the other script,
ARM450_joints.py. NOT RUN HERE (no Fusion on the build machine): the message
box at the end lists every file and whether it worked.
Editing an imported part: Press Pull / Delete / Extrude / Move on faces, or
right-click the body > Capture Design History to get a timeline.
"""
import os
import traceback
import adsk.core
import adsk.fusion

HERE = os.path.dirname(os.path.realpath(__file__))
FOLDERS = ["parts_step", "fit_test_step", "assembly_step"]


def _cloud_folder(app, *names):
    f = app.data.activeProject.rootFolder
    for n in names:
        g = f.dataFolders.itemByName(n)
        f = g if g else f.dataFolders.add(n)
    return f


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    log, ok, bad = [], 0, 0
    try:
        for sub in FOLDERS:
            src = os.path.join(HERE, "..", sub)
            if not os.path.isdir(src):
                log.append("(no folder %s)" % sub)
                continue
            try:
                cloud = _cloud_folder(app, "ARM450_rev_I", sub)
            except Exception:
                cloud = None
            out = os.path.join(HERE, "f3d", sub)
            os.makedirs(out, exist_ok=True)
            for fn in sorted(os.listdir(src)):
                if not fn.lower().endswith((".step", ".stp")):
                    continue
                name = os.path.splitext(fn)[0]
                try:
                    opts = app.importManager.createSTEPImportOptions(os.path.join(src, fn))
                    doc = app.importManager.importToNewDocument(opts)
                    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
                    em = design.exportManager
                    em.execute(em.createFusionArchiveExportOptions(os.path.join(out, name + ".f3d")))
                    if cloud is not None:
                        doc.saveAs(name, cloud, "ARM-450 rev I " + sub, "")
                    doc.close(False)
                    ok += 1
                    log.append("ok   %s/%s" % (sub, name))
                except Exception:
                    bad += 1
                    log.append("FAIL %s/%s: %s" % (sub, name, traceback.format_exc().splitlines()[-1]))
        ui.messageBox("ARM-450: %d imported and saved, %d failed\n\n%s" % (ok, bad, "\n".join(log[-60:])))
    except Exception:
        ui.messageBox("Failed:\n" + traceback.format_exc())
