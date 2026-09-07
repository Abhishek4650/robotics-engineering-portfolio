# myCobot 280 — Sinusoidal End-Effector Path (RViz demo)

Drives the end-effector of an **Elephant Robotics myCobot 280 (M5)** along a
**vertical sine wave** (a wave in the X–Z plane) and visualizes it in **RViz 2**.

Joint angles are computed offline with inverse kinematics (`ikpy`) from the
official `mycobot_280_m5` URDF + meshes, then streamed as `/joint_states`;
`robot_state_publisher` broadcasts TF and RViz renders the moving arm. No MoveIt,
ros2_control, or hardware required — it's a pure visualization/kinematics demo.

![EE path](results/sine_path_results.png)

## Requirements

- **ROS 2** (tested on **Jazzy**; Humble should also work) with `rviz2` and
  `robot_state_publisher` (both in a standard desktop install).
- **Python 3.10+** with `venv` (`sudo apt install python3-venv` if missing).
- Internet access on first setup (to `pip install ikpy scipy numpy matplotlib`).

## Setup (one time)

```bash
cd mycobot_280_sine          # this folder
./setup.sh                   # creates ./venv, installs deps, generates local URDF
```

`setup.sh` makes a virtualenv with `--system-site-packages` so it can see ROS's
`rclpy` while also providing `ikpy`. It is safe to re-run.

## Run

```bash
source /opt/ros/jazzy/setup.bash   # use your ROS 2 distro (jazzy / humble / ...)
./run.sh
```

RViz opens with the myCobot 280 tracing the sine wave on a loop. (`run.sh` just
sources the venv and calls `ros2 launch launch/sine_demo.launch.py`.)

## Generate results (optional, no ROS needed)

```bash
. venv/bin/activate
python scripts/generate_results.py   # writes results/ : plots + trajectory.csv
python scripts/preview_path.py       # quick X–Z preview + IK error report
```

## Customizing the wave

Edit the defaults of `make_sine_path(...)` in
[`scripts/kinematics.py`](scripts/kinematics.py):

| param | meaning | default |
|---|---|---|
| `x0`, `x1` | start/end of the forward sweep along X (m) | 0.10, 0.20 |
| `z0` | center height of the wave (m) | 0.18 |
| `amplitude` | wave height (m) | 0.03 |
| `wavelength` | spatial period along X (m) | 0.10 |
| `n_points` | waypoints per sweep | 120 |

Publish rate is `PUBLISH_HZ` in
[`scripts/sine_trajectory_node.py`](scripts/sine_trajectory_node.py).
After changing the path, re-run `generate_results.py` to re-validate reachability
(keep the EE within the arm's ~0.28 m reach and joint limits).

## Layout

```
launch/sine_demo.launch.py   robot_state_publisher + trajectory node + rviz2
rviz/sine.rviz               RViz config (RobotModel + TF, fixed frame g_base)
scripts/kinematics.py        ikpy chain, sine-path generator, IK, FK
scripts/sine_trajectory_node.py  rclpy node publishing /joint_states @ 30 Hz
scripts/make_local_urdf.py   generates machine-local URDF (absolute mesh paths)
scripts/preview_path.py      offline IK/workspace check (matplotlib)
scripts/generate_results.py  result plots + CSV export
urdf/mycobot_280_m5/         official M5 URDF + .dae meshes + textures
urdf/mycobot_280.urdf        simplified fallback URDF (primitive shapes, no meshes)
requirements.txt             Python deps
setup.sh / run.sh            one-command setup / launch
```

## Notes & troubleshooting

- **`mycobot_280_m5_local.urdf` is generated**, not shipped — it holds absolute
  mesh paths for *your* machine and is created by `setup.sh` (and auto-regenerated
  by the scripts/launch). This is what makes the package relocatable.
- **ikpy warnings** at startup (`fixed ... axis attribute`, `Base link ... set as
  active`) are harmless — they refer to the non-moving base frames and don't
  affect the kinematics.
- **Arm not visible / no meshes**: ensure `setup.sh` finished and that you sourced
  ROS 2 before `./run.sh`. Re-generate the URDF with
  `python scripts/make_local_urdf.py`.
- **Model credit**: URDF + meshes are from Elephant Robotics'
  [`mycobot_ros2`](https://github.com/elephantrobotics/mycobot_ros2)
  (`mycobot_description`).
