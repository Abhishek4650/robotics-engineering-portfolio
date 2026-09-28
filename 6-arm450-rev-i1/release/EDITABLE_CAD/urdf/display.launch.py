"""Drag the six ARM-450 joints with sliders: ros2 launch <this file>"""
import os
from launch import LaunchDescription
from launch_ros.actions import Node

HERE = os.path.dirname(os.path.realpath(__file__))


def generate_launch_description():
    urdf = open(os.path.join(HERE, "arm450.urdf")).read().replace(
        "package://arm450_rev_i_view/meshes/", "file://" + os.path.join(HERE, "meshes") + "/")
    return LaunchDescription([
        Node(package="robot_state_publisher", executable="robot_state_publisher",
             parameters=[{"robot_description": urdf}]),
        Node(package="joint_state_publisher_gui", executable="joint_state_publisher_gui"),
        Node(package="rviz2", executable="rviz2"),
    ])
