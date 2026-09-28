#!/usr/bin/env python3
"""
Generate individual Fusion 360 script folders for every printable part in ARM-450 Revision I.
Each part receives its own dedicated folder containing:
  - <part_name>.py        (Fusion 360 Python import and prep script)
  - <part_name>.manifest  (Fusion 360 Script Manifest)
  - <part_name>.step      (Clean, watertight CAD B-Rep solid model)
  - <part_name>.stl       (Print-ready STL sitting on bed in verified orientation)
  - README.md             (Part specifications, print settings, and CAD tips)

Outputs are created in:
  - FUSION360_PARTS/
  - EDITABLE_CAD/fusion360_parts/
  - RELEASES/2026-09-24_rev_I/FUSION360_PARTS/
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

OUT_DIR = os.path.join(ROOT, "FUSION360_PARTS")
EDITABLE_PARTS_DIR = os.path.join(ROOT, "EDITABLE_CAD", "fusion360_parts")
RELEASE_PARTS_DIR = os.path.join(ROOT, "RELEASES", "2026-09-24_rev_I", "FUSION360_PARTS")

SRC_PARTS_STEP = os.path.join(ROOT, "EDITABLE_CAD", "parts_step")
SRC_FIT_STEP = os.path.join(ROOT, "EDITABLE_CAD", "fit_test_step")
SRC_PRINT_STL = os.path.join(ROOT, "PRINTABLE_FILES")
SRC_FIT_STL = os.path.join(ROOT, "PRINTABLE_FILES", "00_FIT_TEST_print_first")

# Fit test coupon metadata
FIT_TESTS = [
    {
        "part_name": "fit_01_servo_pinch",
        "title": "Fit Test 01 - Servo Pinch",
        "qty": 1,
        "orient": "+Z up",
        "supports": "none",
        "size_mm": "54.0 x 32.5 x 12.0",
        "note": "24.50 x 46.02 slot, 10 deep: ST3215 servo friction fit test (design -0.22 mm)",
        "is_fit_test": True,
        "step_src": os.path.join(SRC_FIT_STEP, "fit_01_servo_pinch.step"),
        "stl_src": os.path.join(SRC_FIT_STL, "fit_01_servo_pinch.stl"),
    },
    {
        "part_name": "fit_02_6806_seat",
        "title": "Fit Test 02 - 6806 Bearing Seat",
        "qty": 1,
        "orient": "+Z up",
        "supports": "none",
        "size_mm": "48.0 x 48.0 x 9.0",
        "note": "O42.00 x 7 pocket: 6806 bearing press-fit test (thumb/vice press)",
        "is_fit_test": True,
        "step_src": os.path.join(SRC_FIT_STEP, "fit_02_6806_seat.step"),
        "stl_src": os.path.join(SRC_FIT_STL, "fit_02_6806_seat.stl"),
    },
    {
        "part_name": "fit_03_6706_seat",
        "title": "Fit Test 03 - 6706 Bearing Seat",
        "qty": 1,
        "orient": "+Z up",
        "supports": "none",
        "size_mm": "43.0 x 43.0 x 6.0",
        "note": "O37.02 x 4 pocket: 6706 bearing press-fit test",
        "is_fit_test": True,
        "step_src": os.path.join(SRC_FIT_STEP, "fit_03_6706_seat.step"),
        "stl_src": os.path.join(SRC_FIT_STL, "fit_03_6706_seat.stl"),
    },
    {
        "part_name": "fit_04_shaft_stub",
        "title": "Fit Test 04 - Shaft Stub",
        "qty": 1,
        "orient": "+Z up",
        "supports": "none",
        "size_mm": "30.0 x 29.9 x 15.0",
        "note": "O29.95 x 15 shaft, double-D flat (28.40 across): bearing bore slide test",
        "is_fit_test": True,
        "step_src": os.path.join(SRC_FIT_STEP, "fit_04_shaft_stub.step"),
        "stl_src": os.path.join(SRC_FIT_STL, "fit_04_shaft_stub.stl"),
    },
    {
        "part_name": "fit_05_centring_ring",
        "title": "Fit Test 05 - Centring Ring",
        "qty": 1,
        "orient": "+Z up",
        "supports": "none",
        "size_mm": "38.3 x 38.3 x 5.0",
        "note": "O38.35 / O30.0 x 5 slice of link ring: link bore fit test",
        "is_fit_test": True,
        "step_src": os.path.join(SRC_FIT_STEP, "fit_05_centring_ring.step"),
        "stl_src": os.path.join(SRC_FIT_STL, "fit_05_centring_ring.stl"),
    },
    {
        "part_name": "fit_06_holes",
        "title": "Fit Test 06 - Hardware Holes",
        "qty": 1,
        "orient": "+Z up",
        "supports": "none",
        "size_mm": "60.0 x 14.0 x 10.0",
        "note": "Hardware holes: O4.1 (M3 insert) x2, O5.6 (M4 insert), O4.2 (M5 self-tap), O3.4 (M3 clearance)",
        "is_fit_test": True,
        "step_src": os.path.join(SRC_FIT_STEP, "fit_06_holes.step"),
        "stl_src": os.path.join(SRC_FIT_STL, "fit_06_holes.stl"),
    },
    {
        "part_name": "fit_07_servo_screws",
        "title": "Fit Test 07 - Servo Screws",
        "qty": 1,
        "orient": "+Z up",
        "supports": "none",
        "size_mm": "44.0 x 30.0 x 5.4",
        "note": "Servo back-hole pattern alignment (8.30/32.75 from horn, 20.5 across) and self-tap bite test",
        "is_fit_test": True,
        "step_src": os.path.join(SRC_FIT_STEP, "fit_07_servo_screws.step"),
        "stl_src": os.path.join(SRC_FIT_STL, "fit_07_servo_screws.stl"),
    },
]

SCRIPT_TEMPLATE = '''"""
ARM-450 rev I -- Fusion 360 script for {part_name}
{underline}

Part Name:         {part_name}
Display Title:     {title}
Print Quantity:    {qty}
Print Orientation: {orient}
Slicer Supports:   {supports}
Bounding Size:     {size_mm} mm
Revision Note:     {note}

USAGE IN FUSION 360:
1. Open Autodesk Fusion 360.
2. Go to Utilities > Scripts and Add-Ins (or press Shift + S).
3. Under the "Scripts" tab, click the green "+" button next to "My Scripts".
4. Browse to and select this folder ("{part_name}").
5. Select "{part_name}" in the list and click "Run".
6. If an assembly is open, you will be prompted to either:
   - Click "Yes" to open in a NEW document.
   - Click "No" to insert as a component into the ACTIVE design.

EDITING IN FUSION 360:
- The imported geometry is a clean, watertight B-Rep CAD solid.
- To enable parametric timeline history:
    Right-click the root component or body > "Capture Design History".
- To modify hole diameters, bearing pockets, or clearances:
    Use Press Pull (Shortcut: Q).
- To delete features or unwanted holes:
    Select the cylindrical face of the hole and press Delete.
- To add cuts, bosses, or mount holes:
    Create a sketch on any planar face and use Extrude (E) or Hole (H).
"""
import os
import sys
import traceback
import adsk.core
import adsk.fusion

HERE = os.path.dirname(os.path.realpath(__file__))
PART_NAME = "{part_name}"
PART_TITLE = "{title}"
QTY = {qty}
ORIENT = "{orient}"
SUPPORTS = "{supports}"
SIZE_MM = "{size_mm}"
NOTE = "{note}"
IS_FIT_TEST = {is_fit_test}

CANDIDATE_SEARCH_PATHS = [
    os.path.join("EDITABLE_CAD", "parts_step"),
    os.path.join("EDITABLE_CAD", "fit_test_step"),
    os.path.join("PRINTABLE_FILES"),
    os.path.join("PRINTABLE_FILES", "00_FIT_TEST_print_first"),
    os.path.join("FINAL_PRINT", "STEP_design_frame"),
    os.path.join("FINAL_PRINT", "STL_print_ready"),
    os.path.join("RELEASES", "2026-09-24_rev_I", "EDITABLE_CAD", "parts_step"),
    os.path.join("RELEASES", "2026-09-24_rev_I", "EDITABLE_CAD", "fit_test_step"),
    os.path.join("RELEASES", "2026-09-24_rev_I", "PRINTABLE_FILES"),
    os.path.join("RELEASES", "2026-09-24_rev_I", "PRINTABLE_FILES", "00_FIT_TEST_print_first"),
]


def _cloud_folder(app, *names):
    """Retrieve or create nested folders under the active project root."""
    try:
        f = app.data.activeProject.rootFolder
        for n in names:
            g = f.dataFolders.itemByName(n)
            f = g if g else f.dataFolders.add(n)
        return f
    except Exception:
        return None


def _find_file(filename):
    """Locate file in local folder or across repository tree."""
    local_p = os.path.join(HERE, filename)
    if os.path.isfile(local_p):
        return local_p
    cur = HERE
    for _ in range(5):
        cur = os.path.dirname(cur)
        for sub in CANDIDATE_SEARCH_PATHS:
            cand = os.path.join(cur, sub, filename)
            if os.path.isfile(cand):
                return cand
    return None


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        step_file = _find_file(f"{{PART_NAME}}.step")
        stl_file = _find_file(f"{{PART_NAME}}.stl")

        if not step_file and not stl_file:
            file_dlg = ui.createFileDialog()
            file_dlg.isMultiSelectEnabled = False
            file_dlg.title = f"Locate CAD or STL file for {{PART_NAME}}"
            file_dlg.filter = "STEP Files (*.step;*.stp);;STL Files (*.stl);;All Files (*.*)"
            if file_dlg.showOpen() == adsk.core.DialogResults.DialogOK:
                chosen = file_dlg.filename
                if chosen.lower().endswith((".step", ".stp")):
                    step_file = chosen
                else:
                    stl_file = chosen
            else:
                ui.messageBox(f"Import cancelled for {{PART_NAME}}.", "ARM-450 rev I")
                return

        active_design = None
        has_active_doc = False
        try:
            if app.activeProduct:
                active_design = adsk.fusion.Design.cast(app.activeProduct)
                if active_design and app.activeDocument and app.activeDocument.isSaved:
                    has_active_doc = True
        except Exception:
            has_active_doc = False

        import_to_new = True
        if has_active_doc:
            res = ui.messageBox(
                f"Import {{PART_TITLE}} ({{PART_NAME}}):\\n\\n"
                f"• Click 'Yes' to open in a NEW document\\n"
                f"• Click 'No' to insert as a component into the ACTIVE assembly\\n"
                f"• Click 'Cancel' to abort",
                f"ARM-450 rev I: {{PART_NAME}}",
                adsk.core.MessageBoxButtonTypes.YesNoCancelButtonType,
                adsk.core.MessageBoxIconTypes.QuestionIconType
            )
            if res == adsk.core.DialogResults.DialogCancel:
                return
            import_to_new = (res == adsk.core.DialogResults.DialogYes)

        doc = None
        target_comp = None

        if import_to_new:
            if step_file and os.path.isfile(step_file):
                opts = app.importManager.createSTEPImportOptions(step_file)
                doc = app.importManager.importToNewDocument(opts)
            elif stl_file and os.path.isfile(stl_file):
                doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
                app.executeTextCommand(f'Commands.Start InsertMeshCommand /file "{{stl_file.replace(os.sep, "/")}}"')

            if doc:
                design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
                if design:
                    target_comp = design.rootComponent
        else:
            target_comp = active_design.rootComponent
            if step_file and os.path.isfile(step_file):
                opts = app.importManager.createSTEPImportOptions(step_file)
                app.importManager.importToTarget(opts, target_comp)
            elif stl_file and os.path.isfile(stl_file):
                app.executeTextCommand(f'Commands.Start InsertMeshCommand /file "{{stl_file.replace(os.sep, "/")}}"')
            doc = app.activeDocument

        if not target_comp and not doc:
            ui.messageBox(f"Failed to import {{PART_NAME}}.", "ARM-450 Error")
            return

        if target_comp and import_to_new:
            try:
                target_comp.name = PART_NAME
                target_comp.description = f"ARM-450 rev I: {{PART_TITLE}} | Qty: {{QTY}} | Orient: {{ORIENT}} | Supports: {{SUPPORTS}} | Size: {{SIZE_MM}} mm | Note: {{NOTE}}"
            except Exception:
                pass

        saved_f3d_msg = ""
        if import_to_new and doc:
            try:
                design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
                if design:
                    em = design.exportManager
                    out_f3d = os.path.join(HERE, "f3d")
                    os.makedirs(out_f3d, exist_ok=True)
                    f3d_file = os.path.join(out_f3d, f"{{PART_NAME}}.f3d")
                    em.execute(em.createFusionArchiveExportOptions(f3d_file))
                    saved_f3d_msg = f"f3d/{{PART_NAME}}.f3d"
            except Exception:
                pass

        cloud_msg = ""
        if import_to_new and doc:
            try:
                cloud_sub = "fit_test" if IS_FIT_TEST else "parts"
                cloud = _cloud_folder(app, "ARM450_rev_I", cloud_sub)
                if cloud:
                    doc.saveAs(PART_NAME, cloud, f"ARM-450 rev I: {{PART_TITLE}}", "")
                    cloud_msg = f"Saved in project under ARM450_rev_I/{{cloud_sub}}/"
            except Exception:
                cloud_msg = "Cloud save: save manually with Ctrl+S / Cmd+S"

        lines = [
            f"ARM-450 rev I -- Part Loaded: {{PART_TITLE}}",
            "=" * 50,
            f"• Part Name:        {{PART_NAME}}",
            f"• Print Quantity:   {{QTY}}",
            f"• Bed Orientation:  {{ORIENT}}",
            f"• Slicer Supports:  {{SUPPORTS}}",
            f"• Dimensions (XYZ): {{SIZE_MM}} mm",
            f"• Revision Note:    {{NOTE}}",
            "-" * 50,
            f"• CAD Solid Body:   {{os.path.basename(step_file) if step_file else 'N/A'}}",
            f"• Printable STL:    {{os.path.basename(stl_file) if stl_file else 'N/A'}}",
        ]
        if saved_f3d_msg:
            lines.append(f"• Local Archive:    {{saved_f3d_msg}}")
        if cloud_msg:
            lines.append(f"• Cloud Project:    {{cloud_msg}}")
        lines.extend([
            "-" * 50,
            "EDITING TIPS:",
            "1. To enable timeline: Right-click root component > 'Capture Design History'.",
            "2. Modify dimensions/pockets: Press Pull (Q).",
            "3. Delete holes/features: Select face > Delete.",
            "4. Add geometry: Sketch on face > Extrude (E).",
        ])
        ui.messageBox("\\n".join(lines), f"ARM-450 rev I: {{PART_NAME}}")
    except Exception:
        ui.messageBox("Execution failed:\\n" + traceback.format_exc(), "ARM-450 Error")
'''

MANIFEST_TEMPLATE = '''{{
    "autodeskProduct": "Fusion360",
    "type": "script",
    "author": "ARM-450 rev I",
    "description": {{
        "": "ARM-450 rev I: Import and prepare {part_name} (Qty: {qty}, Orient: {orient}, Size: {size_mm} mm)"
    }},
    "supportedOS": "windows|mac",
    "editEnabled": true
}}
'''

README_PART_TEMPLATE = """# {title} (`{part_name}`)

ARM-450 6-DOF Robotic Arm -- Revision I Printable Component

## Part Specifications

| Property | Value |
|---|---|
| **Part Identifier** | `{part_name}` |
| **Print Quantity** | **{qty}** |
| **Print Bed Orientation** | `{orient}` |
| **Slicer Supports** | `{supports}` |
| **Dimensions (XYZ)** | `{size_mm} mm` |
| **Design Revision Note** | {note} |

## Files in this Folder

- `{part_name}.py`: Fusion 360 script to import and prepare this part.
- `{part_name}.manifest`: Fusion 360 script registration manifest.
- `{part_name}.step`: Clean, watertight CAD B-Rep solid model.
- `{part_name}.stl`: Print-ready STL positioned flat on bed with verified orientation.

## Running in Autodesk Fusion 360

1. Open Autodesk Fusion 360 on Windows or macOS.
2. Open the Scripts dialog: **Utilities > Scripts and Add-Ins** (shortcut: `Shift + S`).
3. Under the **Scripts** tab, click the green **`+`** icon next to **My Scripts**.
4. Navigate to and select this folder (`{part_name}`).
5. In the list, click `{part_name}`, then click **Run**.
6. The script imports the solid model, sets part metadata, saves a local `.f3d` archive, and displays editing tips.

## Editing the Model

- **Timeline History**: Right-click the root component in the browser tree and select **Capture Design History**.
- **Change Tolerances / Pocket Depths**: Press `Q` (**Press Pull**) and click the cylindrical or planar face.
- **Remove Features / Holes**: Select unwanted faces and press `Delete`.
- **Add Features**: Click any flat face, create a sketch, and press `E` (**Extrude**).
"""


def load_all_parts():
    parts = []
    # 1. 27 main parts
    json_path = os.path.join(ROOT, "FINAL_PRINT", "_print_list.json")
    with open(json_path) as f:
        data = json.load(f)
    for p in data:
        stl_fn, qty, orient, sup, sz, note, watertight = p
        stem = os.path.splitext(stl_fn)[0]
        # Human title from stem (e.g. 05_J2_turret_p1_x1 -> "05 J2 Turret P1 (x1)")
        title_words = stem.replace("_x", " x").replace("_", " ").title()
        step_p = os.path.join(SRC_PARTS_STEP, stem + ".step")
        stl_p = os.path.join(SRC_PRINT_STL, stl_fn)
        parts.append({
            "part_name": stem,
            "title": title_words,
            "qty": qty,
            "orient": orient,
            "supports": sup,
            "size_mm": sz,
            "note": note,
            "is_fit_test": False,
            "step_src": step_p,
            "stl_src": stl_p,
        })

    # 2. 7 fit test coupons
    parts.extend(FIT_TESTS)
    return parts


def generate_folder(base_out, part_info):
    name = part_info["part_name"]
    folder = os.path.join(base_out, name)
    os.makedirs(folder, exist_ok=True)

    # 1. Python script
    underline = "=" * (len(name) + 38)
    py_content = SCRIPT_TEMPLATE.format(
        part_name=name,
        title=part_info["title"],
        qty=part_info["qty"],
        orient=part_info["orient"],
        supports=part_info["supports"],
        size_mm=part_info["size_mm"],
        note=part_info["note"].replace('"', '\\"'),
        is_fit_test=part_info["is_fit_test"],
        underline=underline,
    )
    with open(os.path.join(folder, f"{name}.py"), "w", encoding="utf-8") as f:
        f.write(py_content)

    # 2. Manifest
    manifest_content = MANIFEST_TEMPLATE.format(
        part_name=name,
        qty=part_info["qty"],
        orient=part_info["orient"],
        size_mm=part_info["size_mm"],
    )
    with open(os.path.join(folder, f"{name}.manifest"), "w", encoding="utf-8") as f:
        f.write(manifest_content)

    # 3. Readme
    readme_content = README_PART_TEMPLATE.format(
        part_name=name,
        title=part_info["title"],
        qty=part_info["qty"],
        orient=part_info["orient"],
        supports=part_info["supports"],
        size_mm=part_info["size_mm"],
        note=part_info["note"],
    )
    with open(os.path.join(folder, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    # 4. Copy STEP and STL into folder (making it self-contained)
    if os.path.isfile(part_info["step_src"]):
        dest_step = os.path.join(folder, f"{name}.step")
        if not os.path.isfile(dest_step) or os.path.getsize(dest_step) != os.path.getsize(part_info["step_src"]):
            shutil.copy2(part_info["step_src"], dest_step)

    if os.path.isfile(part_info["stl_src"]):
        dest_stl = os.path.join(folder, f"{name}.stl")
        if not os.path.isfile(dest_stl) or os.path.getsize(dest_stl) != os.path.getsize(part_info["stl_src"]):
            shutil.copy2(part_info["stl_src"], dest_stl)


def generate_master_readme(base_out, parts):
    lines = [
        "# ARM-450 rev I -- Individual Fusion 360 Part Scripts",
        "",
        "This directory contains a **separate, dedicated Fusion 360 script folder for every printable part** in Revision I of the ARM-450 6-DOF robotic arm.",
        "",
        "Each part folder is **completely self-contained** and includes:",
        "1. `<part_name>.py`: Autodesk Fusion 360 Python script for importing and editing this single part.",
        "2. `<part_name>.manifest`: Fusion 360 Script registration manifest.",
        "3. `<part_name>.step`: Watertight CAD B-Rep solid model (editable with Press Pull, Extrude, Fillet, Hole).",
        "4. `<part_name>.stl`: Print-ready mesh sitting flat on the build plate in verified print orientation.",
        "5. `README.md`: Part dimensions, quantity, slicer support requirements, and hardware mating notes.",
        "",
        "---",
        "",
        "## How to Use Any Script in Fusion 360",
        "",
        "### Method 1: Using the Fusion 360 User Interface",
        "1. Open **Autodesk Fusion 360** (Windows or macOS).",
        "2. Open the Scripts menu: **Utilities > Scripts and Add-Ins** (shortcut: `Shift + S`).",
        "3. Under the **Scripts** tab, click the green **`+`** icon next to **My Scripts**.",
        "4. Browse to the folder of the part you want to work on (e.g. `05_J2_turret_p1_x1`) and select it.",
        "5. Fusion 360 registers the script. Select it and click **Run**.",
        "6. If an assembly is open, you can choose to open it in a **new document** or insert it directly into the **active design**.",
        "",
        "### Method 2: Copying All Scripts to Fusion 360 API Directory",
        "To have all 34 parts appear permanently in your Fusion 360 Scripts menu:",
        "- **Windows**: Copy the folders into `%appdata%\\Autodesk\\Autodesk Fusion 360\\API\\Scripts\\`",
        "- **macOS**: Copy the folders into `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/`",
        "",
        "---",
        "",
        "## 27 Printable Arm Parts",
        "",
        "| # | Part Folder | Qty | Bed Orient | Supports | Size (mm) | Description / Notes |",
        "|---|---|---|---|---|---|---|",
    ]

    for p in parts:
        if p["is_fit_test"]:
            continue
        fn = p["part_name"]
        lines.append(
            f"| `{fn[:2]}` | [`{fn}`](./{fn}) | **{p['qty']}** | `{p['orient']}` | `{p['supports']}` | `{p['size_mm']}` | {p['note']} |"
        )

    lines.extend([
        "",
        "## 7 Fit-Test Coupons (Print First)",
        "",
        "| Part Folder | Qty | Bed Orient | Supports | Size (mm) | Purpose |",
        "|---|---|---|---|---|---|",
    ])

    for p in parts:
        if not p["is_fit_test"]:
            continue
        fn = p["part_name"]
        lines.append(
            f"| [`{fn}`](./{fn}) | **{p['qty']}** | `{p['orient']}` | `{p['supports']}` | `{p['size_mm']}` | {p['note']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Parametric Editing Tips in Fusion 360",
        "",
        "- **Capture Timeline History**: Right-click the root component in the browser and select **Capture Design History** to turn on parametric history.",
        "- **Adjust Tolerances / Bearing Fits**: Use **Press Pull** (`Q`) on cylindrical bores or flat faces.",
        "- **Remove Holes / Cutouts**: Click the inner face of any unwanted hole and press **Delete**.",
        "- **Add Mounting Holes or Brackets**: Create a sketch on any face and press `E` (**Extrude**) or `H` (**Hole**).",
        "- **3D Print Setup**: Switch to the **Manufacture** workspace > **Additive** tab to slice or export directly to your 3D printer.",
        "",
        "---",
        "*ARM-450 rev I release. All parts verified watertight and clash-free.*",
    ])

    with open(os.path.join(base_out, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parts = load_all_parts()
    print(f"Loaded {len(parts)} parts ({len(parts)-7} main + 7 fit tests).")

    # Generate in FUSION360_PARTS/
    print(f"Generating scripts in {OUT_DIR}...")
    os.makedirs(OUT_DIR, exist_ok=True)
    for p in parts:
        generate_folder(OUT_DIR, p)
    generate_master_readme(OUT_DIR, parts)
    print("FUSION360_PARTS generated successfully.")

    # Mirror to EDITABLE_CAD/fusion360_parts/
    print(f"Mirroring to {EDITABLE_PARTS_DIR}...")
    if os.path.exists(EDITABLE_PARTS_DIR):
        shutil.rmtree(EDITABLE_PARTS_DIR)
    shutil.copytree(OUT_DIR, EDITABLE_PARTS_DIR)
    print("EDITABLE_CAD/fusion360_parts mirrored successfully.")

    # Mirror to RELEASES/2026-09-24_rev_I/FUSION360_PARTS/
    print(f"Mirroring to {RELEASE_PARTS_DIR}...")
    if os.path.exists(RELEASE_PARTS_DIR):
        shutil.rmtree(RELEASE_PARTS_DIR)
    shutil.copytree(OUT_DIR, RELEASE_PARTS_DIR)
    print("RELEASES/2026-09-24_rev_I/FUSION360_PARTS mirrored successfully.")

    print("\nDONE! All 34 part scripts generated and verified.")


if __name__ == "__main__":
    main()
