#!/bin/bash
# Full release pass, strictly sequential (memory): every check, then the
# assembly, the section (slice) manual check, the print folder and the slicer
# on the print-ready files.
cd "$(dirname "$0")"
bash run_all_checks.sh
LOG=FINAL_RUN.log; : > $LOG
run() { echo "=== $1 ===" >> $LOG; shift; "$@" 2>&1 | grep -v -i "warning" >> $LOG; echo "--- exit ${PIPESTATUS[0]}" >> $LOG; }
run "ASSEMBLY" python3 -u build_final_assembly.py
run "SECTION MEASURE (manual check by slicing)" python3 -u section_measure.py
run "FINAL PRINT FOLDER" python3 -u make_final_print.py
run "PRINT SLICER on the print-ready files" python3 -u -c "
import sys,glob,os; sys.path.insert(0,'../PRINT_GATE')
from slice_check import check
for f in sorted(glob.glob('../FINAL_PRINT/STL_print_ready/*.stl')): check(f, os.path.basename(f)[:-4], verbose=True)
"
echo "=== DONE ===" >> $LOG
