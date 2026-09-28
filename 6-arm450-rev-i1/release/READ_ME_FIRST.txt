ARM-450 rev I.1 -- release 2026-09-27 -- PRINT VERDICT: see PRINT_STATUS.txt

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
Logs:        LOGS/             -- REVI_CHECKS.log (26 stages), FINAL_RUN.log, one log per check
