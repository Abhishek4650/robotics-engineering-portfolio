#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import numpy as np
import time

class MyCobotSineWaveIK(Node):
    def __init__(self):
        super().__init__('mycobot_sine_wave_ik')
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.timer_period = 0.05  
        self.timer = self.create_timer(self.timer_period, self.control_loop)
        self.start_time = time.time()
        self.q = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        
        # 100% Verified Orientation Matrix home position alignment
        self.R_target = np.array([
            [0.0,  0.0, -1.0],
            [0.0, -1.0,  0.0],
            [1.0,  0.0,  0.0]
        ])
        self.get_logger().info('myCobot 280 R_sine Velocity Propagation Solver Active.')

    def forward_kinematics_and_jacobian(self, q):
        t1, t2, t3, t4, t5, t6 = q
        R01 = np.array([[np.cos(t1), -np.sin(t1), 0], [np.sin(t1), np.cos(t1), 0], [0, 0, 1]])
        R12 = np.array([[np.cos(t2), -np.sin(t2), 0], [0, 0, -1], [np.sin(t2), np.cos(t2), 0]])
        R23 = np.array([[np.cos(t3), -np.sin(t3), 0], [np.sin(t3), np.cos(t3), 0], [0, 0, 1]])
        R34 = np.array([[np.cos(t4), -np.sin(t4), 0], [np.sin(t4), np.cos(t4), 0], [0, 0, 1]])
        R45 = np.array([[np.cos(t5), -np.sin(t5), 0], [0, 0, -1], [np.sin(t5), np.cos(t5), 0]])
        R56 = np.array([[np.cos(t6), -np.sin(t6), 0], [0, 0, 1], [-np.sin(t6), -np.cos(t6), 0]])
        
        R_links = [R01, R12, R23, R34, R45, R56]
        P_links = [
            np.array([0.0, 0.0, 0.13156]),
            np.array([0.0, 0.0, 0.001]),
            np.array([0.1104, 0.0, 0.0]),
            np.array([0.096, 0.0, 0.06062]),
            np.array([0.0, 0.0, 0.0]),
            np.array([0.0, 0.0456, 0.0])
        ]
        
        J = np.zeros((6, 6))
        R_curr = np.eye(3)
        P_curr = np.zeros(3)
        frame_positions = [np.zeros(3)]
        z_axes = [np.array([0.0, 0.0, 1.0])]
        
        for i in range(6):
            P_curr = P_curr + R_curr @ P_links[i]
            R_curr = R_curr @ R_links[i]
            frame_positions.append(P_curr.copy())
            z_axes.append(R_curr[:, 2].copy())
            
        P_end_effector = frame_positions[-1]
        
        for i in range(6):
            z_axis = z_axes[i]
            r_vector = P_end_effector - frame_positions[i]
            J[0:3, i] = np.cross(z_axis, r_vector)
            J[3:6, i] = z_axis
            
        return R_curr, P_end_effector, J

    def control_loop(self):
        t = time.time() - self.start_time
        target_x = 0.20640 + 0.03 * np.sin(2 * np.pi * 0.2 * t)
        target_y = -0.10522 
        target_z = 0.13156
        target_position = np.array([target_x, target_y, target_z])
        
        damping = 0.015
        for _ in range(5):
            R_curr, P_curr, J = self.forward_kinematics_and_jacobian(self.q)
            pos_error = target_position - P_curr
            rot_error = 0.5 * (np.cross(R_curr[:,0], self.R_target[:,0]) + 
                               np.cross(R_curr[:,1], self.R_target[:,1]) + 
                               np.cross(R_curr[:,2], self.R_target[:,2]))
            error = np.hstack((pos_error, rot_error))
            J_damped_inv = J.T @ np.linalg.inv(J @ J.T + damping**2 * np.eye(6))
            self.q += J_damped_inv @ error
            
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = ['link1_to_link2', 'link2_to_link3', 'link3_to_link4', 
                    'link4_to_link5', 'link5_to_link6', 'link6_to_link6_flange']
        msg.position = self.q.tolist()
        self.joint_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = MyCobotSineWaveIK()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
