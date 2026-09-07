#!/bin/bash
# Run every ARM-450 alias that can be tested without side effects and report.
shopt -s expand_aliases          # aliases are OFF in non-interactive bash
source /home/user/ros2_ws/arm450_design/arm450_aliases.sh
a450unsnap >/dev/null 2>&1
source /opt/ros/jazzy/setup.bash >/dev/null 2>&1
source $ARM450_WS/install/setup.bash >/dev/null 2>&1
export DISPLAY=:0
pass=0; fail=0
chk() {  # chk <name> <command...>
  local n="$1"; shift
  # source the alias file INSIDE the subshell, or the aliases under test are
  # simply not defined there and every one of them "fails" for the wrong reason
  if timeout 90 bash -c "shopt -s expand_aliases
      source /home/user/ros2_ws/arm450_design/arm450_aliases.sh
      source /opt/ros/jazzy/setup.bash 2>/dev/null
      source \$ARM450_WS/install/setup.bash 2>/dev/null
      $*" >/dev/null 2>&1; then
    echo "  OK    $n"; pass=$((pass+1))
  else
    echo "  FAIL  $n     -> $*"; fail=$((fail+1))
  fi
}
echo "--- static / offline ---"
chk_defined() { for a in "$@"; do
    if [ -n "$(type -t $a 2>/dev/null)" ]; then echo "  OK    $a defined"; pass=$((pass+1));
    else echo "  GONE  $a"; fail=$((fail+1)); fi; done; }
chk_defined a450src a450build a450cd a450run a450jog a450stop a450speed a450slow \
            a450normal a450fast a450rate a450plan a450cycles4 a450cycles6 a450reset \
            a450tipik a450joints a450hz a450tcp a450tip a450nodes a450params \
            a450urdf a450tool a450wrist a450unsnap a450gate a450flight a450cad \
            a450docs a450cmds a450open a450help
chk a450cd     'cd $ARM450_DIR'
chk a450docs   'ls $ARM450_DIR/output/*.pdf'
chk a450help   'true'
chk a450plan   'cd $ARM450_DIR && python3 plan_sine.py --tool gripper --points 20 --out /tmp/x.npz'
chk a450tipik  'cd $ARM450_DIR && python3 plan_sine.py --tool gripper --board-x 0.30 --z-center 0.26 --w-ori 0.2 --tip-ik --points 20 --out /tmp/x.npz'
chk a450gate   'a450gate'
chk a450docs2  'a450docs'
echo "--- ROS, node running ---"
ros2 run robot_state_publisher robot_state_publisher --ros-args \
  -p robot_description:="$(cat $ARM450_WS/install/arm450_description/share/arm450_description/urdf/arm450_meshes.urdf)" >/dev/null 2>&1 &
RSP=$!
ros2 run arm450_sine sine_node --ros-args -p traj_file:=$ARM450_TRAJ -p approach_time:=1.0 >/dev/null 2>&1 &
SN=$!
sleep 8
chk a450nodes  'ros2 node list | grep -q arm450_sine'
chk a450params 'ros2 param list /arm450_sine | grep -q rate'
chk a450rate   'ros2 param get /arm450_sine rate'
chk a450slow   'ros2 param set /arm450_sine rate 8.0'
chk a450normal 'ros2 param set /arm450_sine rate 25.0'
chk a450fast   'ros2 param set /arm450_sine rate 75.0'
chk a450speed  'ros2 param set /arm450_sine rate 30'
chk a450joints 'ros2 topic echo /joint_states --once'
chk a450tcp    'timeout 6 ros2 run tf2_ros tf2_echo base_link tcp; true'
chk a450tip    'timeout 6 ros2 run tf2_ros tf2_echo base_link tool_tip; true'
kill $RSP $SN 2>/dev/null
echo
echo "  $pass passed, $fail failed"
