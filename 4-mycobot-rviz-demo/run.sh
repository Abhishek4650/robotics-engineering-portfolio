#!/usr/bin/env bash
# Launch the myCobot 280 sine-path RViz demo.
# Assumes setup.sh has been run and a ROS 2 distro is sourced
# (source /opt/ros/<distro>/setup.bash). Activates the project venv if present.
set -e
cd "$(dirname "$0")"

if [ -z "$ROS_DISTRO" ]; then
    echo "ERROR: No ROS 2 environment sourced."
    echo "  Run e.g.:  source /opt/ros/jazzy/setup.bash"
    exit 1
fi

if [ -d venv ]; then
    # shellcheck disable=SC1091
    . venv/bin/activate
fi

ros2 launch launch/sine_demo.launch.py
