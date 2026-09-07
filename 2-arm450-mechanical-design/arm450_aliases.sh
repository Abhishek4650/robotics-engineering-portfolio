# ARM-450 shell aliases
# ---------------------------------------------------------------------------
# Install once:
#     echo 'source ~/ros2_ws/arm450_design/arm450_aliases.sh' >> ~/.bashrc
#     source ~/.bashrc
# Then `a450help` lists everything.
# ---------------------------------------------------------------------------

export ARM450_WS=~/ros2_ws
export ARM450_DIR=~/ros2_ws/arm450_design
export ARM450_TRAJ=~/ros2_ws/src/arm450_sine/sine_traj.npz

# --- environment -----------------------------------------------------------
alias a450src='source /opt/ros/jazzy/setup.bash && source $ARM450_WS/install/setup.bash && echo "ARM-450 env ready (ROS 2 jazzy)"'
alias a450build='cd $ARM450_WS && source /opt/ros/jazzy/setup.bash && colcon build --packages-select arm450_description arm450_sine && source $ARM450_WS/install/setup.bash && echo "built + sourced"'
alias a450cd='cd $ARM450_DIR'

# --- run / stop ------------------------------------------------------------
alias a450run='ros2 launch arm450_sine sine.launch.py'
alias a450jog='ros2 launch arm450_description display.launch.py'
alias a450stop='pkill -f sine_node; pkill -f robot_state_publisher; pkill -f rviz2; echo "ARM-450 nodes stopped"'
# NOTE: a450stop names each executable on purpose. A bare `pkill -f ros2`
# matches your own shell and kills the terminal you are typing in.

# --- speed (live, while it is running) -------------------------------------
a450speed() {            # a450speed 60      -> 60 Hz
  [ -z "$1" ] && { echo "usage: a450speed <hz>   (0.5-500, default 25)"; return 1; }
  ros2 param set /arm450_sine rate "$1"
}
alias a450slow='ros2 param set /arm450_sine rate 8.0'
alias a450normal='ros2 param set /arm450_sine rate 25.0'
alias a450fast='ros2 param set /arm450_sine rate 75.0'
alias a450rate='ros2 param get /arm450_sine rate'

# --- shape (needs a re-solve, then relaunch) -------------------------------
# --tool matters. The trajectory drives the J6 FLANGE; the fitted tool's
# working point is further out (gripper 42 mm), so the board the TIP traces is
# 42 mm beyond --board-x. Passing --tool also moves the RViz path marker onto
# the tip, which is why the yellow curve used to float behind the fingers.
# ARM450_TOOL follows whatever a450tool last fitted.
export ARM450_TOOL=gripper
a450plan() {             # a450plan --amplitude 0.04 --cycles 4 --points 300
  ( cd $ARM450_DIR && python3 plan_sine.py --tool "${ARM450_TOOL:-none}" "$@" )
}
# a450cycles2 removed 2026-08-22: it was --cycles 2 --points 240, which is the
# shipped default, so it did exactly what a450reset does. Two names for one
# thing is how they drift apart.
alias a450cycles4='a450plan --cycles 4 --points 300'
alias a450cycles6='a450plan --cycles 6 --points 400'
# z-center is 0.22, NOT 0.20. At 0.20 the exact-mesh check found the upper arm
# grazing the base pedestal on 30 % of waypoints. This alias still said 0.20
# long after plan_sine.py was fixed, so `a450reset` would have quietly written
# a COLLIDING trajectory over the good one.
alias a450reset='a450plan --amplitude 0.04 --cycles 2 --span 0.14 --board-x 0.30 --z-center 0.22 --points 240'
# board fixed and cannot move? drive the TIP onto --board-x instead of the
# flange. Harder solve -- the flange ends up 42 mm nearer the base, on a poorer
# IK branch -- so it wants a higher trace and a stronger orientation weight.
alias a450tipik='a450plan --board-x 0.30 --z-center 0.26 --w-ori 0.2 --tip-ik'

# --- inspect ---------------------------------------------------------------
alias a450joints='ros2 topic echo /joint_states --once'
alias a450hz='ros2 topic hz /joint_states'
# tcp is the J6 FLANGE, not the working point. With a tool fitted that is the
# frame that hid the 42 mm gap, so it is labelled and a450tip is the one to use.
alias a450tcp='ros2 run tf2_ros tf2_echo base_link tcp'
alias a450tip='ros2 run tf2_ros tf2_echo base_link tool_tip'
alias a450nodes='ros2 node list'
alias a450params='ros2 param list /arm450_sine'

# --- design / docs ---------------------------------------------------------
# Rebuilds BOTH urdfs. It used to rebuild only arm450.urdf (the box-primitive
# one); the mesh urdf RViz actually loads was left stale, which is how RViz came
# to be showing a model that did not match the design.
a450urdf() {
  ( cd $ARM450_DIR \
    && python3 generate_urdf.py \
    && EMIT=1 TOOL="${1:-gripper}" python3 generate_urdf_meshes.py \
    && cp arm450.urdf arm450_meshes.urdf $ARM450_WS/src/arm450_description/urdf/ \
    && cp meshes/*.stl $ARM450_WS/src/arm450_description/meshes/ \
    && echo "URDF (primitive + mesh, tool=${1:-gripper}) regenerated + copied — now run a450build" )
}
# swap the fitted end effector and rebuild in one go
a450tool() {             # a450tool gripper | dock | none
  [ -z "$1" ] && { echo "usage: a450tool gripper|dock|none"; return 1; }
  a450urdf "$1" && ( cd $ARM450_WS && source /opt/ros/jazzy/setup.bash \
    && colcon build --packages-select arm450_description --symlink-install >/dev/null \
    && source $ARM450_WS/install/setup.bash ) || return 1
  export ARM450_TOOL="$1"
  a450reset >/dev/null && echo "fitted: $1 — trajectory re-solved, path marker on the tip"
}
# camera parked on the wrist, so the tool is actually visible
alias a450wrist='rviz2 -d $ARM450_WS/install/arm450_description/share/arm450_description/rviz/arm450_tool.rviz'
# rviz2 dies instantly in a VS Code snap terminal with
#   libpthread.so.0: undefined symbol: __libc_pthread_init, GLIBC_PRIVATE
# The cause is GTK_PATH, which the snap points at its own GTK module directory.
# rviz2's Qt/GTK integration loads a module from there and that module drags in
# the snap's core20 glibc alongside the system one. Nothing else matters --
# LD_LIBRARY_PATH, PATH and LOCPATH are all red herrings; unsetting this one
# variable is the whole fix.
a450unsnap() {
  unset GTK_PATH
  echo "GTK_PATH unset — rviz2 will start now"
}

alias a450gate='( cd $ARM450_DIR && python3 preprint_check.py )'
alias a450flight='( cd $ARM450_DIR && python3 preflight.py )'
alias a450cad='( cd $ARM450_DIR/cad && for f in *.py; do [ "$f" = params.py ] && continue; python3 "$f"; done )'
alias a450docs='ls -lh $ARM450_DIR/output/*.pdf'
# regenerate the command reference. It is PARSED from this file and from
# plan_sine.py --help, so editing an alias and re-running this keeps the PDF
# honest -- which is the whole reason it is generated rather than typed.
alias a450cmds='( cd $ARM450_DIR && python3 make_commands.py && python3 build_pdf.py COMMANDS.md )'
alias a450open='xdg-open $ARM450_DIR/output'

a450help() {
cat <<'EOF'
ARM-450 commands
────────────────────────────────────────────────────────────────────────
  ENVIRONMENT
    a450src        source ROS 2 jazzy + this workspace
    a450build      colcon build the two ARM-450 packages, then source
    a450cd         cd to the design directory

  RUN / STOP
    a450run        launch the sine trace in RViz (gripper fitted)
    a450jog        launch RViz + joint sliders (no motion)
    a450wrist      RViz with the camera parked on the wrist/tool
    a450stop       stop all ARM-450 nodes
    a450unsnap     fix rviz2 refusing to start in a VS Code snap terminal

  END EFFECTOR
    a450tool gripper   fit the parallel-jaw gripper (default)
    a450tool dock      fit the docking probe
    a450tool none      bare J6 face
    Rebuilds the URDF and colcon-builds it. Relaunch with a450run.

  SPEED — live, no restart
    a450speed 60   set playback to 60 Hz
    a450slow       8 Hz   (30 s per pass, good for inspecting)
    a450normal     25 Hz  (9.6 s per pass, the default)
    a450fast       75 Hz  (3.2 s per pass)
    a450rate       show the current rate

  SHAPE — re-solves IK, then relaunch with a450run
    NOTE the board distance. The path drives the J6 flange, so with a
    gripper on, the TIP traces 42 mm further out than --board-x.
    plan_sine prints "PUT THE BOARD AT x = ..." — use that number.
    a450tipik  drive the TIP onto --board-x instead (board cannot move)
    a450plan --amplitude 0.04 --cycles 4 --points 300
    a450cycles4 / a450cycles6
    a450reset      back to the shipped default
    KEEP AMPLITUDE AT 0.04. Past 40 mm the shoulder J2 hits its
    +115 deg stop and path error goes 0.19 -> 1.35 mm. Cycles are
    free: raise --points to about 60 x cycles and error does not move.

  INSPECT
    a450joints     one /joint_states message
    a450hz         publishing rate
    a450tip        live TOOL TIP pose — the point that traces
    a450tcp        live J6 flange pose (42 mm behind the tip)
    a450nodes      running nodes
    a450params     parameters of the sine node

  DESIGN / DOCS
    a450urdf       regenerate BOTH urdfs from cad/params.py and install them
    a450gate       run the pre-print parts gate
    a450flight     run the full 8-stage pre-print flight check
    a450cad        rebuild every CAD part (STEP + STL)
    a450docs       list the PDFs
    a450cmds       regenerate ARM450_COMMANDS.pdf from this file
    a450open       open the output folder
────────────────────────────────────────────────────────────────────────
EOF
}
