#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

class PathTracer(Node):
    def __init__(self):
        super().__init__('path_tracer')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.path_pub = self.create_publisher(Path, '/end_effector_path', 10)
        self.path = Path()
        self.path.header.frame_id = 'base_link'
        
        # Poll coordinates at 50Hz
        self.timer = self.create_timer(0.02, self.timer_callback)

    def timer_callback(self):
        try:
            # Look up the transform from base to gripper flange
            now = rclpy.time.Time()
            trans = self.tf_buffer.lookup_transform('base_link', 'link6_flange', now)
            
            # Create a point in the path history
            pose = PoseStamped()
            pose.header = trans.header
            pose.pose.position.x = trans.transform.translation.x
            pose.pose.position.y = trans.transform.translation.y
            pose.pose.position.z = trans.transform.translation.z
            pose.pose.orientation = trans.transform.rotation
            
            self.path.poses.append(pose)
            
            # Keep the path length manageable (last 300 points)
            if len(self.path.poses) > 300:
                self.path.poses.pop(0)
                
            self.path.header.stamp = self.get_clock().now().to_msg()
            self.path_pub.publish(self.path)
        except TransformException:
            pass

def main(args=None):
    rclpy.init(args=args)
    node = PathTracer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()