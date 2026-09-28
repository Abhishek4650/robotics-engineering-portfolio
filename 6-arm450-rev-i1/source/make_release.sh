#!/bin/bash
# Assemble a release folder from the verified working tree (never touches an
# earlier release).  Usage: bash make_release.sh 2026-09-27_rev_I1 "rev I.1"
set -e
cd "$(dirname "$0")/.."
NAME="$1"; LABEL="$2"
OUT="RELEASES/$NAME"
[ -e "$OUT" ] && { echo "$OUT exists -- refusing to overwrite a release"; exit 1; }
mkdir -p "$OUT/PDF/RULE6_VIEWS" "$OUT/LOGS"
cp -r PRINTABLE_FILES "$OUT/PRINTABLE_FILES"
cp -r EDITABLE_CAD "$OUT/EDITABLE_CAD"
rsync -a --exclude __pycache__ --exclude '*.pyc' FUSION_DESIGN_TREES/ "$OUT/FUSION_DESIGN_TREES/"
for f in ARM450_AUDIT_REPORT.md ARM450_AUDIT_REPORT.pdf ARM450_REV_I_FINAL.pdf ARM450_REV_I.pdf ARM450_POSES.pdf \
         ARM450_PARTS.pdf LOG_SUMMARY.md LOG_SUMMARY.pdf; do cp "REV_H/$f" "$OUT/PDF/"; done
cp "$(ls -t $(find . -name ARM450_INTERFACES.pdf -not -path './RELEASES/*') | head -1)" "$OUT/PDF/"
cp ASSEMBLY_MANUAL/ARM450_ASSEMBLY_GUIDE_base_to_flange.pdf ASSEMBLY_MANUAL/ARM450_ASSEMBLY_MANUAL.pdf "$OUT/PDF/"
for p in cable_schematic head_clearance idler_compare idler_cut_J1 idler_cut_J4 idler_cut_J6 j1_drive_explained \
         j1_servo_hold servo_screws sockets_photo j3_lug_fix; do
    [ -f "REV_H/RULE6_VIEWS/$p.png" ] && cp "REV_H/RULE6_VIEWS/$p.png" "$OUT/PDF/RULE6_VIEWS/"
    [ -f "REV_H/RULE6_VIEWS/$p.pdf" ] && cp "REV_H/RULE6_VIEWS/$p.pdf" "$OUT/PDF/RULE6_VIEWS/"
done
for f in AUDIT_GAPS.log B2F_ORDER_CHECK.log CABLE_ROUTE.log CLAMP_CHECK.log DISASSEMBLY_CHECK.log \
         DISASSEMBLY_CHECK_OFFICIAL.log DOCS_RUN.log DOF6_CHECK.log FASTENER_CHECK.log FINAL_RUN.log HARDWARE_BOM.md \
         HEAD_CLEARANCE.log LOG_SUMMARY.pdf MATING_CHECK.log OFFICIAL_SERVO_CHECK.log PARAM_AUDIT.md PLUG_INSERT.log \
         REVI_CHECKS.log SECTION_MEASURE.md TOOL_ACCESS.log WIRING_CHECK.log UNION_JOINTS.log; do cp "REV_H/$f" "$OUT/LOGS/"; done
cp PRINTABLE_FILES/PRINT_STATUS.txt "$OUT/PRINT_STATUS.txt"
cp FINAL_PRINT/README.md "$OUT/README_hardware_and_build_order.md"
tar czf "$OUT/SOURCE_REV_H.tar.gz" --exclude=REV_H/_asm_meshes --exclude=REV_H/__pycache__ --exclude=REV_H/REVI_VIEWS \
    --exclude=REV_H/RULE5_VIEWS --exclude=REV_H/RULE6_VIEWS --exclude='*.pyc' REV_H
NST=$(grep -c "^=== " REV_H/REVI_CHECKS.log)
cat > "$OUT/READ_ME_FIRST.txt" <<EOF
ARM-450 $LABEL -- release ${NAME%%_*} -- PRINT VERDICT: see PRINT_STATUS.txt

What changed since rev I (2026-09-24): 12_J3_p1 only -- the two J3 spring lugs
were joined to the round cheek tops by a 0.1 mm sliver (your slicer view);
now sunk 1.5 mm and blended by R3 webs (joint 34 -> 136 mm2). All other print
files are byte-for-byte the same as rev I. PDF/RULE6_VIEWS/j3_lug_fix.png.

Open first:  PDF/ARM450_AUDIT_REPORT.pdf   (verdict, what was found and fixed, your questions answered)
Then:        PDF/LOG_SUMMARY.pdf           (every check in one table + which PDF is for what)
Building:    PDF/ARM450_ASSEMBLY_GUIDE_base_to_flange.pdf (START HERE to build: foot -> tool flange,
             24 steps, order proven by LOGS/B2F_ORDER_CHECK.log)
             PDF/ARM450_ASSEMBLY_MANUAL.pdf (fastener schedule for every screw, cable loops)
             README_hardware_and_build_order.md
Details:     PDF/ARM450_REV_I_FINAL.pdf (sections + all logs), ARM450_REV_I.pdf (one page per joint),
             ARM450_POSES.pdf, ARM450_PARTS.pdf, ARM450_INTERFACES.pdf
Print:       PRINTABLE_FILES/  -- 00_FIT_TEST_print_first FIRST; see PRINT_STATUS.txt
CAD:         EDITABLE_CAD/     -- STEP parts / assembly, Fusion joints script, SolidWorks macro, URDF
             FUSION_DESIGN_TREES/ -- one Fusion 360 script per part: builds it as an editable
             timeline and saves the .f3d (run 00_BUILD_ALL_f3d once); see its README.md
Logs:        LOGS/             -- REVI_CHECKS.log ($NST stages), FINAL_RUN.log, one log per check
EOF
( cd "$OUT" && find . -type f ! -name MANIFEST.sha256 | sort | xargs -d '\n' sha256sum > MANIFEST.sha256 && sha256sum -c --quiet MANIFEST.sha256 )
echo "release $OUT: $(wc -l < $OUT/MANIFEST.sha256) files, manifest checked"
