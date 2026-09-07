#!/usr/bin/env bash
# One-time setup for the myCobot 280 sine-path RViz demo.
# Creates a Python venv (sharing system/ROS packages), installs deps, and
# generates the machine-local URDF. Re-runnable.
set -e
cd "$(dirname "$0")"

echo "[1/3] Creating Python venv (./venv) with access to system ROS packages..."
if [ ! -d venv ]; then
    python3 -m venv --system-site-packages venv
fi

echo "[2/3] Installing Python dependencies (ikpy, scipy, numpy, matplotlib)..."
# shellcheck disable=SC1091
. venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "[3/3] Generating machine-local URDF (absolute mesh paths)..."
python scripts/make_local_urdf.py

echo
echo "Setup complete. To run the demo:"
echo "    source /opt/ros/<distro>/setup.bash   # e.g. jazzy / humble"
echo "    ./run.sh"
