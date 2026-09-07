#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from trajectory_msgs.msg import JointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

from builtin_interfaces.msg import Duration


class JointSender(Node):

    def __init__(self):
        super().__init__("joint_sender")

        self.publisher = self.create_publisher(
            JointTrajectory,
            "/arm_controller/joint_trajectory",
            10
        )

        self.timer = self.create_timer(2.0, self.send_command)

        self.sent = False

    def send_command(self):

        if self.sent:
            return

        msg = JointTrajectory()

        msg.joint_names = [
            "link1_to_link2",
            "link2_to_link3",
            "link3_to_link4",
            "link4_to_link5",
            "link5_to_link6",
            "link6_to_link6_flange",
        ]

        point = JointTrajectoryPoint()

        point.positions = [
            0.5,   # Move Joint 1
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]

        point.time_from_start = Duration(sec=3)

        msg.points.append(point)

        self.publisher.publish(msg)

        self.get_logger().info("Trajectory sent!")

        self.sent = True


def main(args=None):

    rclpy.init(args=args)

    node = JointSender()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
