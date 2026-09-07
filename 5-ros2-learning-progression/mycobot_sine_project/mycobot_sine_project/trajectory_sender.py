#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from trajectory_msgs.msg import JointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration


class TrajectorySender(Node):

    def __init__(self):

        super().__init__("trajectory_sender")

        self.publisher = self.create_publisher(
            JointTrajectory,
            "/arm_controller/joint_trajectory",
            50
        )

        self.timer = self.create_timer(
            0.02,
            self.send_trajectory
        )

        self.t = 0.0

        self.get_logger().info("Trajectory Sender Ready")

    def send_trajectory(self):

        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()

        msg.joint_names = [
            "link1_to_link2",
            "link2_to_link3",
            "link3_to_link4",
            "link4_to_link5",
            "link5_to_link6",
            "link6_to_link6_flange",
        ]

        point = JointTrajectoryPoint()

        amplitude = 0.5      # radians
        frequency = 0.2      # Hz

        joint1 = amplitude * math.sin(
            2.0 * math.pi * frequency * self.t
        )

        point.positions = [
            joint1,
            -0.30,
            0.40,
            -0.20,
            0.30,
            0.10,
        ]

        self.t += 0.02

        point.velocities = [0.0] * 6

        point.time_from_start = Duration(
            sec=0,
            nanosec=50000000
        )
        msg.points.append(point)

        self.publisher.publish(msg)

        self.get_logger().info(f"Joint1 = {joint1:.3f}")


def main(args=None):

    rclpy.init(args=args)

    node = TrajectorySender()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
