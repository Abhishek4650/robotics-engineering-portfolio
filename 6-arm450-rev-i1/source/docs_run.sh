#!/bin/bash
# Documents from the verified geometry, strictly sequential
cd "$(dirname "$0")"
LOG=DOCS_RUN.log; : > $LOG
run() { echo "=== $1 ===" >> $LOG; shift; "$@" 2>&1 | grep -v -i "warning\|SetCells" >> $LOG; echo "--- exit ${PIPESTATUS[0]}" >> $LOG; }
run "LOGS + COVER from the release pass" sh -c "python3 -u split_logs.py && python3 -u make_final_docs.py"
run "FINAL PDF (Rule 5 pages)" python3 -u make_final_pdf.py
run "POSES + PARTS PDFs (Rule 6)" python3 -u make_rule6_pages.py
run "EDITABLE CAD folder (Rule 7)" python3 -u make_editable_cad.py
run "AUDIT PICTURES (servo screws, J1 drive, idler, Rule 8)" sh -c "python3 -u make_servo_screw_views.py && python3 -u make_j1_drive_view.py && python3 -u make_audit_views.py && python3 -u make_rule8_views.py"
run "AUDIT REPORT + README" sh -c "python3 -u make_final_readme.py && python3 -u make_audit_report.py"
echo "=== DONE ===" >> $LOG
