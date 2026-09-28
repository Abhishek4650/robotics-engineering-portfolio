#!/bin/bash
# Re-run every drive-train, motion and print check on the current REV_H parts.
cd "$(dirname "$0")"
LOG=REVI_CHECKS.log
: > $LOG
echo "=== J1 ===" >> $LOG; python3 -u verify_j1.py 2>&1 | grep -v Warning >> $LOG
echo "=== J2 ===" >> $LOG; python3 -u -c "
import sys; sys.path.insert(0,'.')
import numpy as np, trimesh, verify_drive as VD, asm_meshes as AM
SH=40.0; T=np.eye(4); T[2,3]=-50.0-SH
Rx=trimesh.transformations.rotation_matrix(np.radians(-90),[1,0,0]); W2J=Rx@T
T2=np.eye(4); T2[2,3]=-SH; TU2J=Rx@T2
def lt(f): m=trimesh.load(f); m.apply_transform(TU2J); return m
nb={k:AM.neighbour(k,W2J) for k in ('link_upper_groove','link_upper_tongue','shaft_clamp_1','shaft_clamp_2','base')}
VD.verify('J2',lt('J2_turret_p1.stl'),lt('J2_turret_p2.stl'),lt('J2_shaft.stl'),28.5,nb,-25.0)
print('FAILURES: %d'%sum(1 for r in VD.RES if not r[1]))
" 2>&1 | grep -v Warning >> $LOG
echo "=== J3 ===" >> $LOG; python3 -u -c "
import sys; sys.path.insert(0,'.')
import numpy as np, trimesh, verify_drive as VD, gen_drive_j3 as G, asm_meshes as AM
R=np.array([[0.,1.,0.],[0.,0.,1.],[1.,0.,0.]]); M=np.eye(4); M[:3,:3]=R; M[:3,3]=[0,0,209.]; Mi=np.linalg.inv(M)
nb={k:AM.neighbour(k,Mi) for k in ('link_fore_groove','link_fore_tongue','shaft_clamp_3','shaft_clamp_4','link_upper_groove','link_upper_tongue')}
VD.verify('J3',trimesh.load('J3_p1.stl'),trimesh.load('J3_p2.stl'),trimesh.load('J3_shaft.stl'),G.P,nb,G.Z_IDLE_END)
print('FAILURES: %d'%sum(1 for r in VD.RES if not r[1]))
" 2>&1 | grep -v Warning >> $LOG
echo "=== J4 ===" >> $LOG; python3 -u verify_j4.py 2>&1 | grep -v Warning >> $LOG
echo "=== WRIST ===" >> $LOG; python3 -u verify_wrist.py 2>&1 | grep -v Warning >> $LOG
echo "=== HARDWARE (bearings + bolts as solids) ===" >> $LOG; python3 -u verify_hw.py 2>&1 | grep -v Warning >> $LOG
echo "=== LINK LOCK (J2/J3 set screws, centring rings) ===" >> $LOG; python3 -u verify_clamp.py 2>&1 | grep -v Warning >> $LOG
echo "=== FASTENERS (every screw, insert, nut) ===" >> $LOG; python3 -u verify_fasteners.py 2>&1 | grep -v Warning >> $LOG
echo "=== PARAMETER AUDIT ===" >> $LOG; python3 -u param_audit.py 2>&1 | grep -v Warning >> $LOG
echo "=== TOOL ACCESS (hex key to every screw at its build step) ===" >> $LOG; python3 -u verify_tool_access.py 2>&1 | grep -v Warning >> $LOG
echo "=== RULE 4 (mate, never overlap; pathways; attached) ===" >> $LOG; python3 -u verify_mating.py 2>&1 | grep -v Warning >> $LOG
echo "=== SPRINGS ===" >> $LOG; python3 -u verify_springs.py 2>&1 | grep -v Warning >> $LOG
echo "=== SWEEP ===" >> $LOG; python3 -u sweep_arm.py 2>&1 | grep -v Warning >> $LOG
echo "=== 6-DOF (axes two ways, Jacobian rank) ===" >> $LOG; python3 -u verify_6dof.py 2>&1 | grep -v Warning >> $LOG
echo "=== OFFICIAL ST3215 (manufacturer's model, rear idler horn) ===" >> $LOG; python3 -u verify_official_servo.py 2>&1 | grep -v Warning >> $LOG
echo "=== DISASSEMBLY PATHS (our servo model) ===" >> $LOG; python3 -u verify_disassembly.py 2>&1 | grep -v Warning >> $LOG
echo "=== DISASSEMBLY PATHS (official servo) ===" >> $LOG; python3 -u verify_disassembly.py --official 2>&1 | grep -v Warning >> $LOG
echo "=== AUDIT GAPS (joints together, tipping, walls, bed) ===" >> $LOG; python3 -u audit_gaps.py 2>&1 | grep -v -i "warning\|Axes3D" >> $LOG
echo "=== GATES (each part in its chosen PRINT orientation) ===" >> $LOG; python3 -u -c "
import sys,os,json; sys.path.insert(0,'../PRINT_GATE')
import trimesh
from slice_check import check
import orient_gate as OG
plan=json.load(open('PRINT_ORIENTATION.json'))
for f in ('j1_mount','j1_hub','J2_turret_p1','J2_turret_p2','J2_shaft','J3_p1','J3_p2','J3_shaft','j4_base','j4_cap','j4_hub','J5_p1','J5_p2','J5_shaft','J5_spacer','j6_body','j6_cap','j6_flange','collar_upper','collar_fore','base','spigot_collar','link_fore_tongue','link_fore_groove','link_upper_tongue','shaft_clamp'):
    k=plan[f]['orient']; m=trimesh.load(f+'.stl'); m.apply_transform(OG.ORIENTS[k]); m.apply_translation([0,0,-m.bounds[0][2]])
    p='/tmp/claude-1000/-home-user-ros2-ws-Arm-450-new-design/d7055e52-889b-4cd2-992e-dd3a2338ce75/scratchpad/_gate.stl'; m.export(p)
    check(p,f+' ['+k+']',verbose=True)
" 2>&1 | grep -v Warning >> $LOG
echo "=== PAIRS (static all-pairs) ===" >> $LOG; python3 -u audit_pairs.py 2>&1 | grep -v Warning | sed -n '/STATIC ALL-PAIRS/,$p' >> $LOG
echo "=== WIRING (both bus plugs in every servo, way out) ===" >> $LOG; python3 -u verify_wiring.py 2>&1 | grep -v -i warn | tee WIRING_CHECK.log >> $LOG
echo "=== HEAD CLEARANCE (screw heads vs turning parts, contact angle) ===" >> $LOG; python3 -u verify_head_clearance.py 2>&1 | grep -v -i warn | tee HEAD_CLEARANCE.log >> $LOG
echo "=== CABLE ROUTE (one joint per cable, path change, loops) ===" >> $LOG; python3 -u cable_route.py 2>&1 | grep -v -i warn | tee CABLE_ROUTE.log >> $LOG
echo "=== PLUG INSERTION (bus plugs in and out with the arm assembled) ===" >> $LOG; python3 -u verify_plug_insert.py 2>&1 | grep -v -i warn | tee PLUG_INSERT.log >> $LOG
echo "=== UNION JOINTS (every glued feature joined over its full section) ===" >> $LOG; rm -f UNION_JOINTS.log; python3 -u verify_union_joints.py > /dev/null 2>&1; cat UNION_JOINTS.log >> $LOG 2>/dev/null || echo "Traceback: the union-joint audit did not finish" >> $LOG
echo "=== DONE ===" >> $LOG
