"""ARM-450 sine trace in RViz.

    ros2 launch arm450_sine sine.launch.py

Starts robot_state_publisher with the ARM-450 URDF, replays the pre-solved sine
trajectory on /joint_states, publishes the path as a Marker, and opens RViz.
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    desc = get_package_share_directory('arm450_description')
    # 2026-08-21: use the MESH urdf. arm450.urdf carries box/cylinder primitives
    # sized to the real section -- fine for collision and cheap for kinematics,
    # but in RViz it renders as a stack of blocks that looks nothing like the
    # designed arm. arm450_meshes.urdf references the exported STLs.
    urdf = os.path.join(desc, 'urdf', 'arm450_meshes.urdf')
    rviz = os.path.join(desc, 'rviz', 'arm450.rviz')
    with open(urdf) as f:
        robot_desc = f.read()

    traj = LaunchConfiguration('traj_file')
    return LaunchDescription([
        DeclareLaunchArgument(
            'traj_file',
            default_value=os.path.expanduser('~/ros2_ws/src/arm450_sine/sine_traj.npz'),
            description='pre-solved trajectory from plan_sine.py'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             output='screen', parameters=[{'robot_description': robot_desc}]),
        Node(package='arm450_sine', executable='sine_node', output='screen',
             parameters=[{'traj_file': traj}]),
        Node(package='rviz2', executable='rviz2', output='screen',
             arguments=['-d', rviz]),
    ])
