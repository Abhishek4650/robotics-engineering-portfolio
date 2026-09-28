#!/usr/bin/env python3
"""
RULE 7 -- EDITABLE_CAD/: the design in a form you can open, change and move
in your own CAD tool.

  parts_step/           every printed part, STEP AP214 (mm), one solid each
  assembly_step/        ARM450_ASSEMBLY.step: one component per RIGID BODY
                        (ground, turret, upper link, forearm, J4 hub, blade,
                        flange), every part and bought item inside, placed;
                        + one STEP per body (used by the Fusion script)
  fusion360/            ARM450_joints.py: Fusion 360 script -- imports the 7
                        bodies, grounds the base, creates the 6 REVOLUTE joints
                        on the measured axes with their limits, saves .f3d
  solidworks/           ARM450_to_solidworks.swb: macro -- opens every part
                        STEP and saves .SLDPRT, opens the assembly, saves
                        .SLDASM; JOINT_AXES.csv for concentric mates
  urdf/                 arm450.urdf + meshes + display.launch.py: drag the six
                        joints with sliders in RViz (ROS 2 Jazzy, checked here)
  JOINT_AXES.csv        joint point / axis / limits (world, mm) -- measured
  PARAMETERS.csv        169 key dimensions, generator value vs measured file
"""
import csv
import os
import re
import shutil
import sys

import numpy as np
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_final_assembly as BA   # noqa: E402
import verify_mating as VM          # noqa: E402
import make_rule6_pages as R6       # noqa: E402
import make_final_print as MF       # noqa: E402

OUT = os.path.join(ROOT, "EDITABLE_CAD")
BODY_NAMES = ["ground", "turret", "upper_link", "forearm", "j4_hub", "blade", "flange"]
LIMITS = [90.0, 54.0, 72.0, 90.0, 46.5, 90.0]          # swept without a clash (REVI_CHECKS SWEEP)
JOINT_NAMES = ["J1_base_yaw", "J2_shoulder", "J3_elbow", "J4_forearm_roll", "J5_wrist_pitch", "J6_tool_roll"]


def body_assemblies(A):
    # node names must be unique in the whole tree: "j4_hub" is also a part
    subs = [cq.Assembly(name="BODY_" + b) for b in BODY_NAMES]
    for ch in A.children:
        b = R6.body(ch.name)
        if b is None:
            b = 1 if ch.name.startswith("spring_J2") else 2          # springs ride with their lower body
        subs[b].add(ch.obj, name=ch.name, loc=ch.loc, color=ch.color)
    return subs


def urdf(axes, meshes_dir, subs):
    """link k frame at the joint-k axis point, world-aligned at home."""
    import trimesh
    pts = [np.zeros(3)] + [q for q, w in axes]
    lines = ['<?xml version="1.0"?>', '<robot name="arm450_rev_i">',
             '  <!-- generated from the verified rev-I assembly; mm -> m; home = arm straight up -->']
    mats = {}
    for k, b in enumerate(BODY_NAMES):
        # one mesh per body, in that body's link frame
        parts = []
        for ch in subs[k].children:
            obj = ch.obj.val() if hasattr(ch.obj, "val") else ch.obj
            V, F = R6.R5.tess(obj.moved(ch.loc).wrapped, 0.1, 0.3)
            if len(F):
                parts.append(trimesh.Trimesh(V - pts[k], F, process=False))
        m = trimesh.util.concatenate(parts)
        m.apply_scale(0.001)
        m.export(os.path.join(meshes_dir, b + ".stl"))
        col = ["0.55 0.55 0.6 1", "0.85 0.25 0.25 1", "0.2 0.6 0.3 1", "0.25 0.4 0.85 1",
               "0.9 0.55 0.1 1", "0.6 0.2 0.7 1", "0.3 0.7 0.75 1"][k]
        lines += ['  <material name="m_%s"><color rgba="%s"/></material>' % (b, col),
                  '  <link name="%s">' % b,
                  '    <visual><geometry><mesh filename="package://arm450_rev_i_view/meshes/%s.stl"/></geometry>'
                  '<material name="m_%s"/></visual>' % (b, b),
                  '  </link>']
    for k in range(1, 7):
        q, w = axes[k - 1]
        o = (q - pts[k - 1]) / 1000.0
        lim = np.radians(LIMITS[k - 1])
        lines += ['  <joint name="%s" type="revolute">' % JOINT_NAMES[k - 1],
                  '    <parent link="%s"/><child link="%s"/>' % (BODY_NAMES[k - 1], BODY_NAMES[k]),
                  '    <origin xyz="%.6f %.6f %.6f" rpy="0 0 0"/>' % tuple(o),
                  '    <axis xyz="%.6f %.6f %.6f"/>' % tuple(w),
                  '    <limit lower="%.5f" upper="%.5f" effort="2.9" velocity="4.0"/>' % (-lim, lim),
                  '  </joint>']
    lines.append('</robot>')
    return "\n".join(lines)


LAUNCH = '''"""Drag the six ARM-450 joints with sliders: ros2 launch <this file>"""
import os
from launch import LaunchDescription
from launch_ros.actions import Node

HERE = os.path.dirname(os.path.realpath(__file__))


def generate_launch_description():
    urdf = open(os.path.join(HERE, "arm450.urdf")).read().replace(
        "package://arm450_rev_i_view/meshes/", "file://" + os.path.join(HERE, "meshes") + "/")
    return LaunchDescription([
        Node(package="robot_state_publisher", executable="robot_state_publisher",
             parameters=[{"robot_description": urdf}]),
        Node(package="joint_state_publisher_gui", executable="joint_state_publisher_gui"),
        Node(package="rviz2", executable="rviz2"),
    ])
'''

FUSION = r'''"""
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
BODIES = %(bodies)s
JOINTS = %(joints)s      # name, parent, child, point (mm), axis, limit (deg)


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
'''

FUSION_ALL = r'''"""
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
'''

SW_MACRO = r'''' ARM-450 rev I -- SolidWorks macro (Tools > Macro > Run > this .swb).
' Opens every STEP in ..\parts_step and saves it as .SLDPRT in this folder,
' then opens ..\assembly_step\ARM450_ASSEMBLY.step and saves .SLDASM (+ its
' parts). NOT RUN HERE (no SolidWorks on the build machine).
' Mates: Insert > Mate > Concentric on the bearing pocket of each joint, or
' use the axis table ..\JOINT_AXES.csv; add a Limit Angle mate for the range.
' For editable FEATURES (extrude / cut / fillet) run Insert > FeatureWorks >
' Recognize Features on a part.
Dim swApp As Object
Sub main()
    Set swApp = Application.SldWorks
    Dim here As String, src As String, f As String, errs As Long, warn As Long
    here = swApp.GetCurrentMacroPathFolder() & "\"
    src = here & "..\parts_step\"
    f = Dir(src & "*.step")
    Do While f <> ""
        Dim m As Object
        Set m = swApp.LoadFile4(src & f, "r", Nothing, errs)
        If Not m Is Nothing Then
            m.Extension.SaveAs here & Replace(f, ".step", ".SLDPRT"), 0, 1, Nothing, errs, warn
            swApp.CloseDoc m.GetTitle
        End If
        f = Dir()
    Loop
    Dim a As Object
    Set a = swApp.LoadFile4(here & "..\assembly_step\ARM450_ASSEMBLY.step", "r", Nothing, errs)
    If Not a Is Nothing Then
        a.Extension.SaveAs here & "ARM450_ASSEMBLY.SLDASM", 0, 1 + 4, Nothing, errs, warn
    End If
    MsgBox "ARM-450: parts saved as .SLDPRT, assembly as .SLDASM in " & here
End Sub
'''


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for d in ("parts_step", "fit_test_step", "assembly_step", "fusion360", "solidworks", "urdf/meshes"):
        os.makedirs(os.path.join(OUT, d))
    # 1. parts
    for i, (nm, q, src, note) in enumerate(MF.PARTS, 1):
        shutil.copy(os.path.join(src, nm + ".step"), os.path.join(OUT, "parts_step", "%02d_%s_x%d.step" % (i, nm, q)))
    # 1b. the fit-test coupons as editable STEP too
    import gen_fit_coupon as GFC
    for nm, sh in GFC.parts().items():
        cq.exporters.export(sh, os.path.join(OUT, "fit_test_step", nm + ".step"))
    # 2. assembly by rigid body
    A, _ = BA.build()
    subs = body_assemblies(A)
    top = cq.Assembly(name="ARM450_rev_I")
    for s in subs:
        top.add(s, name=s.name)
        s.save(os.path.join(OUT, "assembly_step", "body_%s.step" % s.name[5:]))
    top.save(os.path.join(OUT, "assembly_step", "ARM450_ASSEMBLY.step"))
    # 3. joint table (measured axes, as verify_6dof)
    axes = R6.joint_axes()
    with open(os.path.join(OUT, "JOINT_AXES.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["joint", "parent body", "child body", "point x mm", "y", "z", "axis x", "y", "z", "range +- deg"])
        for k, (q, a) in enumerate(axes):
            w.writerow([JOINT_NAMES[k], BODY_NAMES[k], BODY_NAMES[k + 1], *np.round(q, 3), *np.round(a, 6), LIMITS[k]])
    # 4. Fusion script
    joints = [(JOINT_NAMES[k], BODY_NAMES[k], BODY_NAMES[k + 1], [float(x) for x in np.round(q, 4)],
               [float(x) for x in np.round(a, 6)], LIMITS[k]) for k, (q, a) in enumerate(axes)]
    with open(os.path.join(OUT, "fusion360", "ARM450_joints.py"), "w") as f:
        f.write(FUSION % dict(bodies=repr(BODY_NAMES), joints=repr(joints)))
    with open(os.path.join(OUT, "fusion360", "ARM450_import_all.py"), "w") as f:
        f.write(FUSION_ALL)
    with open(os.path.join(OUT, "fusion360", "ARM450_import_all.manifest"), "w") as f:
        f.write('{"autodeskProduct": "Fusion360", "type": "script", "author": "ARM-450", '
                '"description": {"": "ARM-450 rev I: every STEP of the folder into Fusion, saved + local .f3d"}, '
                '"supportedOS": "windows|mac", "editEnabled": true}\n')
    with open(os.path.join(OUT, "fusion360", "ARM450_joints.manifest"), "w") as f:
        f.write('{"autodeskProduct": "Fusion360", "type": "script", "author": "ARM-450", '
                '"description": {"": "ARM-450 rev I: import + six revolute joints"}, "supportedOS": "windows|mac", '
                '"editEnabled": true}\n')
    # 5. SolidWorks macro
    with open(os.path.join(OUT, "solidworks", "ARM450_to_solidworks.swb"), "w", newline="\r\n") as f:
        f.write(SW_MACRO)
    # 6. URDF + launch
    with open(os.path.join(OUT, "urdf", "arm450.urdf"), "w") as f:
        f.write(urdf(axes, os.path.join(OUT, "urdf", "meshes"), subs))
    with open(os.path.join(OUT, "urdf", "display.launch.py"), "w") as f:
        f.write(LAUNCH)
    # 7. parameters, measured
    pa = os.path.join(HERE, "PARAM_AUDIT.md")
    with open(os.path.join(OUT, "PARAMETERS.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["part", "parameter", "design value", "measured in file", "result"])
        for ln in open(pa):
            c = [x.strip() for x in ln.strip().strip("|").split("|")]
            if len(c) == 5 and c[0] not in ("part", "---"):
                w.writerow(c)
    shutil.copy(os.path.join(HERE, "EDITABLE_CAD_README.md"), os.path.join(OUT, "README.md"))
    print("written", OUT)


if __name__ == "__main__":
    main()
