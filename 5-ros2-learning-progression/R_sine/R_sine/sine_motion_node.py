#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
import math
import time

class SineMotionNode(Node):
    def __init__(self):
        super().__init__('sine_motion_node')
        
        # Original publisher
        self.publisher_ = self.create_publisher(
            JointTrajectory, 
            '/arm_controller/joint_trajectory', 
            10
        )
        
        # New publisher for drawing the line path
        self.path_pub = self.create_publisher(Path, '/end_effector_path', 10)
        self.path = Path()
        self.path.header.frame_id = 'base_link'
        
        # TF Listener to track link6_flange location natively
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        self.joint_names = [
            'link1_to_link2', 'link2_to_link3', 'link3_to_link4', 
            'link4_to_link5', 'link5_to_link6', 'link6_to_link6_flange'
        ]
        
        self.start_time = time.time()
        self.timer = self.create_timer(0.02, self.timer_callback)
        self.get_logger().info('Sinusoidal Motion and Path Tracer Node Started!')

    def timer_callback(self):
        # --- 1. YOUR ORIGINAL UNTOUCHED MOTION CODE ---
        t = time.time() - self.start_time
        amplitude = 0.5  
        frequency = 1.5  
        
        joint1_pos = amplitude * math.sin(frequency * t)
        joint2_pos = amplitude * math.sin(frequency * t + (math.pi / 4))
        
        msg = JointTrajectory()
        msg.joint_names = self.joint_names
        
        point = JointTrajectoryPoint()
        point.positions = [joint1_pos, joint2_pos, 0.0, 0.0, 0.0, 0.0]
        point.time_from_start.sec = 0
        point.time_from_start.nanosec = 20000000  
        
        msg.points.append(point)
        self.publisher_.publish(msg)
        
        # --- 2. AUTOMATIC TRACE LINE GENERATOR ---
        try:
            now = rclpy.time.Time()
            trans = self.tf_buffer.lookup_transform('base_link', 'link6_flange', now)
            
            pose = PoseStamped()
            pose.header = trans.header
            pose.pose.position.x = trans.transform.translation.x
            pose.pose.position.y = trans.transform.translation.y
            pose.pose.position.z = trans.transform.translation.z
            pose.pose.orientation = trans.transform.rotation
            
            self.path.poses.append(pose)
            if len(self.path.poses) > 500: # Keeps trailing line length looking clean
                self.path.poses.pop(0)
                
            self.path.header.stamp = self.get_clock().now().to_msg()
            self.path_pub.publish(self.path)
        except TransformException:
            pass

def main(args=None):
    rclpy.init(args=args)
    node = SineMotionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()