#!/usr/bin/env python3
import os
import sys
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped

try:
    sys.path.insert(0, '/home/user/robotic_arm/scripts')
    from make_local_urdf import ensure_local_urdf
    from ikpy.chain import Chain
except ImportError:
    sys.path.insert(0, os.path.expanduser('~/robotic_arm/scripts'))
    from make_local_urdf import ensure_local_urdf
    from ikpy.chain import Chain

JOINT_NAMES = [
    "joint2_to_joint1",
    "joint3_to_joint2",
    "joint4_to_joint3",
    "joint5_to_joint4",
    "joint6_to_joint5",
    "joint6output_to_joint6",
]

class MyCobotPrecomputedSineIK(Node):
    def __init__(self):
        super().__init__('mycobot_sine_wave_ik')
        
        self.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, True)])
        
        self.rviz_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.gazebo_pub = self.create_publisher(Float64MultiArray, '/forward_position_controller/commands', 10)
        
        self.ee_path_pub = self.create_publisher(Path, '/end_effector_path', 10)
        self.j4_path_pub = self.create_publisher(Path, '/joint4_path', 10)
        
        self.ee_path = Path()
        self.j4_path = Path()
        
        self.get_logger().info("Initializing standalone URDF map and precomputing IK trajectory loop...")
        
        urdf_path = ensure_local_urdf()
        self.chain = Chain.from_urdf_file(urdf_path, base_elements=["g_base"], name="mycobot_280_m5")
        
        mask = [link.name in JOINT_NAMES for link in self.chain.links]
        self.chain.active_links_mask = mask
        
        xs = np.linspace(0.12, 0.22, 120)
        zs = 0.18 + 0.03 * np.sin(2.0 * np.pi * (xs - 0.12) / 0.10)
        ys = np.zeros_like(xs)
        targets = np.column_stack([xs, ys, zs])
        
        n_links = len(self.chain.links)
        q_full = np.zeros(n_links)
        active_idx = [i for i, a in enumerate(self.chain.active_links_mask) if a]
        
        joint_solutions = []
        self.full_solutions = []
        
        for p in targets:
            q_full = self.chain.inverse_kinematics(target_position=p, initial_position=q_full)
            self.full_solutions.append(q_full.copy())
            joint_solutions.append(q_full[active_idx].copy())
            
        self.traj_joints = np.vstack([joint_solutions, joint_solutions[-2:0:-1]])
        self.traj_full = np.vstack([self.full_solutions, self.full_solutions[-2:0:-1]])
        
        self.idx = 0
        self.publish_hz = 30.0
        self.timer = self.create_timer(1.0 / self.publish_hz, self.on_timer)
        self.get_logger().info(f"Hybrid Engine Active: {len(self.traj_joints)} seamless frames cached.")

    def on_timer(self):
        stamp = self.get_clock().now().to_msg()
        q_joints = self.traj_joints[self.idx]
        q_full = self.traj_full[self.idx]
        
        rviz_msg = JointState()
        rviz_msg.header.stamp = stamp
        rviz_msg.header.frame_id = 'g_base'
        rviz_msg.name = JOINT_NAMES
        rviz_msg.position = [float(v) for v in q_joints]
        self.rviz_pub.publish(rviz_msg)
        
        gazebo_msg = Float64MultiArray()
        gazebo_msg.data = [float(v) for v in q_joints]
        self.gazebo_pub.publish(gazebo_msg)
        
        # FIX: Removed full_output=True keyword argument since ikpy returns nodes directly now
        transforms = self.chain.forward_kinematics(q_full)
        
        ee_pos = transforms[-1][:3, 3]
        p_ee = PoseStamped()
        p_ee.header = rviz_msg.header
        p_ee.pose.position.x, p_ee.pose.position.y, p_ee.pose.position.z = ee_pos
        self.ee_path.poses.append(p_ee)
        self.ee_path.header = rviz_msg.header
        self.ee_path_pub.publish(self.ee_path)
        
        j4_pos = transforms[4][:3, 3]
        p_j4 = PoseStamped()
        p_j4.header = rviz_msg.header
        p_j4.pose.position.x, p_j4.pose.position.y, p_j4.pose.position.z = j4_pos
        self.j4_path.poses.append(p_j4)
        self.j4_path.header = rviz_msg.header
        self.j4_path_pub.publish(self.j4_path)
        
        self.idx = (self.idx + 1) % len(self.traj_joints)

def main(args=None):
    rclpy.init(args=args)
    node = MyCobotPrecomputedSineIK()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
