# Fusion 360 script - extract kinematics for DH derivation.
# Runs INSIDE Fusion 360 (Utilities > ADD-INS > Scripts and Add-Ins).
# Writes ~/Desktop/arm_kinematics.json with:
#   - every Joint (name, type, origin, axis)  [if any are defined]
#   - every component occurrence (name, 4x4 transform, bbox) [always]
#   - a servo shortlist (ST3215-sized parts) = the 6 joint frames
# Send that JSON back to me and I'll derive + verify the DH table.
import adsk.core, adsk.fusion, traceback, json, os

JT = {0: "Rigid", 1: "Revolute", 2: "Slider", 3: "Cylindrical",
      4: "PinSlot", 5: "Planar", 6: "Ball"}


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Open the assembled arm design first, then run this.")
            return
        root = design.rootComponent
        out = {"units": "mm", "design": design.parentDocument.name,
               "joints": [], "occurrences": [], "servos": []}

        # ---- Joints (if the design has any) ----
        try:
            for j in root.allJoints:
                jm = j.jointMotion
                rec = {"name": j.name, "type": JT.get(jm.jointType, jm.jointType),
                       "origin_mm": None, "axis": None,
                       "occ1": None, "occ2": None}
                try:
                    p = j.geometryOrOriginOne.origin
                    rec["origin_mm"] = [round(p.x*10, 4), round(p.y*10, 4),
                                        round(p.z*10, 4)]
                except Exception:
                    pass
                try:
                    v = jm.rotationAxisVector          # revolute axis
                    rec["axis"] = [round(v.x, 6), round(v.y, 6), round(v.z, 6)]
                except Exception:
                    pass
                try:
                    rec["occ1"] = j.occurrenceOne.fullPathName if j.occurrenceOne else None
                    rec["occ2"] = j.occurrenceTwo.fullPathName if j.occurrenceTwo else None
                except Exception:
                    pass
                out["joints"].append(rec)
        except Exception as e:
            out["joints_error"] = str(e)

        # ---- Occurrences (component placements) - ALWAYS available ----
        for occ in root.allOccurrences:
            m = occ.transform2.asArray()               # row-major, lengths in cm
            trans_mm = [round(m[3]*10, 4), round(m[7]*10, 4), round(m[11]*10, 4)]
            # rotation basis columns (unitless)
            R = [[round(m[0], 6), round(m[1], 6), round(m[2], 6)],
                 [round(m[4], 6), round(m[5], 6), round(m[6], 6)],
                 [round(m[8], 6), round(m[9], 6), round(m[10], 6)]]
            size_mm = None
            try:
                bb = occ.boundingBox
                size_mm = [round((bb.maxPoint.x-bb.minPoint.x)*10, 2),
                           round((bb.maxPoint.y-bb.minPoint.y)*10, 2),
                           round((bb.maxPoint.z-bb.minPoint.z)*10, 2)]
            except Exception:
                pass
            cname = occ.component.name
            rec = {"name": occ.fullPathName, "component": cname,
                   "translation_mm": trans_mm, "R": R, "bbox_mm": size_mm}
            out["occurrences"].append(rec)
            # servo shortlist: by name or by ST3215-ish bbox (~45x38x25 mm)
            nm = (occ.fullPathName + " " + cname).lower()
            is_servo = ("st3215" in nm or "servo" in nm or
                        (cname.lower().startswith("motor") and "mount" not in nm
                         and "fixer" not in nm and "housing" not in nm))
            if size_mm:
                s = sorted(size_mm)
                if abs(s[0]-24.7) < 6 and abs(s[1]-37.8) < 8 and abs(s[2]-45.2) < 8:
                    is_servo = True
            if is_servo:
                out["servos"].append(rec)

        path = os.path.join(os.path.expanduser("~"), "Desktop", "arm_kinematics.json")
        with open(path, "w") as f:
            json.dump(out, f, indent=2)
        ui.messageBox(
            "Extracted:\n  {} joints\n  {} occurrences\n  {} servo(s)\n\n"
            "Saved to:\n{}\n\nSend this file back.".format(
                len(out["joints"]), len(out["occurrences"]),
                len(out["servos"]), path))
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
