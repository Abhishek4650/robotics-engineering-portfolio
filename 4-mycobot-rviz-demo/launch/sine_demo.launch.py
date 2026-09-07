#!/usr/bin/env python3
"""
Launch the myCobot 280 sinusoidal-path RViz demo:
  * robot_state_publisher  -- loads the URDF, broadcasts TF from /joint_states
  * sine_trajectory_node   -- streams the sine-path joint angles to /joint_states
  * rviz2                  -- visualizes the arm (RobotModel + TF)

Run (after `source /opt/ros/jazzy/setup.bash`):
    ros2 launch <this_package>/launch/sine_demo.launch.py

Note: the trajectory node needs ikpy. If a project venv exists (./venv, created
by setup.sh) its python is used; otherwise the current interpreter is used. All
paths are derived from this file's location, so the package is relocatable.
"""

import os
import sys
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PKG_DIR, "scripts"))
from make_local_urdf import ensure_local_urdf  # noqa: E402

URDF_PATH = ensure_local_urdf()  # regenerate mesh paths for this machine
RVIZ_CONFIG = os.path.join(PKG_DIR, "rviz", "sine.rviz")
TRAJ_SCRIPT = os.path.join(PKG_DIR, "scripts", "sine_trajectory_node.py")

_venv_python = os.path.join(PKG_DIR, "venv", "bin", "python")
PYTHON = _venv_python if os.path.exists(_venv_python) else sys.executable


def generate_launch_description():
    with open(URDF_PATH, "r") as f:
        robot_description = f.read()

    return LaunchDescription([
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            parameters=[{"robot_description": robot_description}],
        ),
        ExecuteProcess(
            cmd=[PYTHON, TRAJ_SCRIPT],
            output="screen",
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", RVIZ_CONFIG],
            output="screen",
        ),
    ])
