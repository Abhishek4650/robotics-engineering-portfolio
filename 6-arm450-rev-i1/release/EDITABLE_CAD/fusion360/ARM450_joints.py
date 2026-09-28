"""
ARM-450 rev I -- Fusion 360 script (Utilities > Scripts and Add-Ins > + > this
folder > Run). Imports the seven rigid bodies from ../assembly_step, grounds
the base, creates the six REVOLUTE joints on the measured axes with their
limits, and saves the design (.f3d) in your Fusion project.
Then: drag any link with the pointer -- it turns about its joint, like the
revolute-joint preview. NOT RUN HERE (no Fusion on the build machine); if a
joint fails, the message box says which -- make it by hand:
Assemble > Joint > Revolute, pick the two bodies, snap to the bearing-pocket
circle of that joint (axis table: ../JOINT_AXES.csv).
"""
import os
import math
import traceback
import adsk.core
import adsk.fusion

HERE = os.path.dirname(os.path.realpath(__file__))
BODIES = ['ground', 'turret', 'upper_link', 'forearm', 'j4_hub', 'blade', 'flange']
JOINTS = [('J1_base_yaw', 'ground', 'turret', [0.0, 0.0, -14.311], [0.0, -0.0, -1.0], 90.0), ('J2_shoulder', 'turret', 'upper_link', [0.0, -28.5, 90.0], [0.0, -1.0, 0.0], 54.0), ('J3_elbow', 'upper_link', 'forearm', [0.0, 28.5, 209.0], [0.0, 1.0, 0.0], 72.0), ('J4_forearm_roll', 'forearm', 'j4_hub', [0.0, 0.0, 378.589], [0.0, -0.0, -1.0], 90.0), ('J5_wrist_pitch', 'j4_hub', 'blade', [0.0, 26.0, 430.369], [0.0, 1.0, 0.0], 46.5), ('J6_tool_roll', 'blade', 'flange', [0.0, 0.0, 494.958], [-0.0, -0.0, -1.0], 90.0)]      # name, parent, child, point (mm), axis, limit (deg)


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    log = []
    try:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        im = app.importManager
        occ = {}
        for b in BODIES:
            n0 = root.occurrences.count
            opts = im.createSTEPImportOptions(os.path.join(HERE, "..", "assembly_step", "body_" + b + ".step"))
            im.importToTarget(opts, root)
            if root.occurrences.count > n0:
                o = root.occurrences.item(root.occurrences.count - 1)
                o.component.name = b
                occ[b] = o
                log.append("imported " + b)
            else:
                log.append("IMPORT FAILED " + b)
        if "ground" in occ:
            occ["ground"].isGrounded = True
        for name, parent, child, p, a, lim in JOINTS:
            try:
                comp = occ[child].component
                sk = comp.sketches.add(comp.xYConstructionPlane)
                sk.name = name + "_axis"
                P0 = adsk.core.Point3D.create(p[0] / 10.0, p[1] / 10.0, p[2] / 10.0)          # mm -> cm
                P1 = adsk.core.Point3D.create((p[0] + 20 * a[0]) / 10.0, (p[1] + 20 * a[1]) / 10.0,
                                              (p[2] + 20 * a[2]) / 10.0)
                line = sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(P0), sk.modelToSketchSpace(P1))
                lp = line.createForAssemblyContext(occ[child])
                geo = adsk.fusion.JointGeometry.createByPoint(lp.startSketchPoint)
                ji = root.asBuiltJoints.createInput(occ[child], occ[parent], geo)
                ji.setAsRevoluteJointMotion(adsk.fusion.JointDirections.CustomJointDirection, lp)
                j = root.asBuiltJoints.add(ji)
                j.name = name
                lims = j.jointMotion.rotationLimits
                lims.isMinimumValueEnabled = True; lims.minimumValue = -math.radians(lim)
                lims.isMaximumValueEnabled = True; lims.maximumValue = math.radians(lim)
                log.append("joint " + name + " ok")
            except Exception:
                log.append("JOINT FAILED " + name + ": " + traceback.format_exc().splitlines()[-1])
        try:
            folder = app.data.activeProject.rootFolder
            doc.saveAs("ARM450_rev_I", folder, "ARM-450 rev I with six revolute joints", "")
            log.append("saved ARM450_rev_I.f3d in project " + app.data.activeProject.name)
        except Exception:
            log.append("save by hand: File > Save (" + traceback.format_exc().splitlines()[-1] + ")")
        ui.messageBox("\n".join(log))
    except Exception:
        ui.messageBox("Failed:\n" + traceback.format_exc())
