#!/usr/bin/env python3

import rclpy
from rclpy.node import Node


class MyCobotController(Node):

    def __init__(self):
        super().__init__("mycobot_controller")

        self.get_logger().info("")
        self.get_logger().info("===================================")
        self.get_logger().info("   MyCobot Sine Project Started")
        self.get_logger().info("===================================")
        self.get_logger().info("Waiting for next implementation...")


def main(args=None):

    rclpy.init(args=args)

    node = MyCobotController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
