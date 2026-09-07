#!/usr/bin/env python3
"""
ROS2 node: drive the myCobot 280 end-effector along a vertical (X-Z) sine path
and publish the resulting joint angles as sensor_msgs/JointState on /joint_states.

robot_state_publisher consumes /joint_states + the URDF and broadcasts TF, which
RViz renders. The full joint trajectory is precomputed once via IK (kinematics.py),
mirrored forward+back so it loops seamlessly, then streamed on a timer.

Run (after sourcing ROS + venv):
    python scripts/sine_trajectory_node.py
"""

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

import kinematics as k

PUBLISH_HZ = 30.0


class SineTrajectoryNode(Node):
    def __init__(self):
        super().__init__("sine_trajectory_node")
        self.pub = self.create_publisher(JointState, "joint_states", 10)

        self.get_logger().info("Building IK chain and precomputing sine trajectory...")
        chain = k.build_chain()
        targets = k.make_sine_path()
        joints, _ = k.solve_path(chain, targets)

        # Mirror forward + reverse (drop duplicate endpoints) for a seamless loop.
        loop = np.vstack([joints, joints[-2:0:-1]])
        self.traj = loop
        self.idx = 0
        self.get_logger().info(
            f"Trajectory ready: {len(self.traj)} frames, publishing at {PUBLISH_HZ:.0f} Hz."
        )

        self.timer = self.create_timer(1.0 / PUBLISH_HZ, self.on_timer)

    def on_timer(self):
        q = self.traj[self.idx]
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = k.JOINT_NAMES
        msg.position = [float(v) for v in q]
        self.pub.publish(msg)
        self.idx = (self.idx + 1) % len(self.traj)


def main():
    rclpy.init()
    node = SineTrajectoryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
