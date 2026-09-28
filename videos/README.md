# Videos: screen recordings and a print timelapse

These videos run in date order. They follow the work from the first Gazebo and RViz sessions
with the myCobot 280 to the ARM-450 design tracing a sine, and then to printed parts.

The screen recordings are cropped to the Gazebo and RViz windows, so the desktop does not
show. The long 30 June session is cut to 60 seconds. Nothing inside the windows is changed.

## myCobot 280: learning ROS 2 simulation (June 2026)

| Video | What it shows | Project |
|---|---|---|
| [2026-06-25_gazebo_rviz_mycobot_sim.mp4](2026-06-25_gazebo_rviz_mycobot_sim.mp4) | myCobot 280 in a Gazebo Sim scene with objects (left), with the same arm in RViz (right) | [5](../5-ros2-learning-progression) |
| [2026-06-25_gazebo_rviz_mycobot_gripper_scene.mp4](2026-06-25_gazebo_rviz_mycobot_gripper_scene.mp4) | The arm with its gripper moving in Gazebo and RViz, next to a box in the scene | [5](../5-ros2-learning-progression) |
| [2026-06-26_rviz_mycobot_end_effector_path.mp4](2026-06-26_rviz_mycobot_end_effector_path.mp4) | RViz Path displays: the end-effector path (red) and a joint path (green) drawn as the arm moves | [5](../5-ros2-learning-progression) |
| [2026-06-26_rviz_gazebo_sine_ik_paths.mp4](2026-06-26_rviz_gazebo_sine_ik_paths.mp4) | The first sine-wave IK node (`mycobot_sine_wave_ik`) driving RViz and Gazebo together; the red trail records every tool position | [5](../5-ros2-learning-progression) |
| [2026-06-26_gazebo_rviz_sine_ik_sync.mp4](2026-06-26_gazebo_rviz_sine_ik_sync.mp4) | The same node, RViz and Gazebo in step | [5](../5-ros2-learning-progression) |
| [2026-06-27_gazebo_rviz_trajectory_sender.mp4](2026-06-27_gazebo_rviz_trajectory_sender.mp4) | A `trajectory_sender` node streaming joint commands, logged in the terminal, to Gazebo and RViz (2 min) | [5](../5-ros2-learning-progression) |
| [2026-06-29_rviz_mycobot_gripper.mp4](2026-06-29_rviz_mycobot_gripper.mp4) | Close-up of the arm with its gripper in RViz | [5](../5-ros2-learning-progression) |
| [2026-06-29_rviz_mycobot_with_stand.mp4](2026-06-29_rviz_mycobot_with_stand.mp4) | The arm moving beside a stand fixture in RViz | [5](../5-ros2-learning-progression) |
| [2026-06-30_rviz_mycobot_ikpy_sine_60s.mp4](2026-06-30_rviz_mycobot_ikpy_sine_60s.mp4) | The ikpy demo: 238 precomputed frames streamed at 30 Hz to `robot_state_publisher` and RViz (60 s of a 19.5 min run) | [4](../4-mycobot-rviz-demo) |

## ARM-450, first design (August 2026)

| Video | What it shows | Project |
|---|---|---|
| [2026-08-20_rviz_arm450_design_sine.webm](2026-08-20_rviz_arm450_design_sine.webm) | The ARM-450 design tracing a sine (yellow) in RViz | [2](../2-arm450-mechanical-design) |
| [2026-08-21_rviz_arm450_first_model_sine.mp4](2026-08-21_rviz_arm450_first_model_sine.mp4) | An early simplified ARM-450 model tracing the same sine | [2](../2-arm450-mechanical-design) |
| [2026-08-22_rviz_arm450_detailed_model_sine.webm](2026-08-22_rviz_arm450_detailed_model_sine.webm) | The detailed ARM-450 meshes (servos, links, turret) tracing the sine | [2](../2-arm450-mechanical-design) |
| [2026-08-28_print_timelapse_arm450_j2_turret.mp4](2026-08-28_print_timelapse_arm450_j2_turret.mp4) | 3D-print timelapse of the first-design J2 turret, printed spigot-up on tree supports | [2](../2-arm450-mechanical-design) |

More ARM-450 motion, as GIFs: [the first design](../2-arm450-mechanical-design/figures) and
[rev I.1 tracing on a board and on a table](../6-arm450-rev-i1/kinematics/figures).
