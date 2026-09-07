#!/usr/bin/env python3
"""
ARM-450 sine tracer — publishes /joint_states so RViz animates the real arm,
plus a /sine_path Marker so the traced curve is visible on the board.

The joint trajectory is solved OFFLINE by the same IK used in the design study
(bounded least-squares with the continuity term that suppresses the J4/J6 wrist
singularity), then replayed at a fixed rate.
"""
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point

JOINTS = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']


class SineTracer(Node):
    def __init__(self):
        super().__init__('arm450_sine')
        self.declare_parameter('board_x', 0.30)
        self.declare_parameter('amplitude', 0.04)
        self.declare_parameter('length', 0.14)
        self.declare_parameter('rate', 25.0)
        self.declare_parameter('traj_file', '')
        self.declare_parameter('loop_mode', 'pingpong')
        # HARDWARE SAFETY. On real servos the arm starts wherever it was left.
        # Jumping straight to waypoint 0 is a full-speed slam; approach_time
        # ramps there instead. Set 0.0 only in simulation.
        self.declare_parameter('approach_time', 3.0)
        self.declare_parameter('start_pose', [0.0] * 6)

        bx = self.get_parameter('board_x').value
        amp = self.get_parameter('amplitude').value
        ln = self.get_parameter('length').value
        rate = self.get_parameter('rate').value

        f = self.get_parameter('traj_file').value
        if f:
            d = np.load(f)
            self.Q, self.P = d['Q'], d['P']
            self.get_logger().info(f'loaded {len(self.Q)} waypoints from {f}')
        else:
            self.get_logger().error(
                'no traj_file given. Generate one with plan_sine.py — solving IK '
                'inside the node would block the executor.')
            raise SystemExit(1)

        # Velocity check against the actuator, done once, out loud. The ST3215
        # is 4.6 rad/s no-load; under load assume half. Exceeding it does not
        # error -- the servo simply lags and the traced path is not the solved
        # path.
        step = np.abs(np.diff(self.Q, axis=0)).max()
        vmax = step * rate
        lim = 4.6 * 0.5
        self.get_logger().info(
            f'peak joint rate {vmax:.2f} rad/s ({np.degrees(vmax):.0f} deg/s) '
            f'vs ~{lim:.1f} rad/s loaded ST3215 -> '
            f'{"OK" if vmax < lim else "TOO FAST, lower rate"}')
        if vmax >= lim:
            self.get_logger().warn(
                f'reduce rate to below {lim/step:.0f} Hz for this trajectory')

        self.pub = self.create_publisher(JointState, 'joint_states', 10)
        # A real controller wants a trajectory, not a stream of states. Publish
        # the whole solved path once, latched, so a FollowJointTrajectory action
        # or any controller can consume it directly.
        self.traj_pub = self.create_publisher(
            JointTrajectory, 'arm450/trajectory',
            rclpy.qos.QoSProfile(depth=1,
                                 durability=rclpy.qos.DurabilityPolicy.TRANSIENT_LOCAL))
        self.mk = self.create_publisher(Marker, 'sine_path', 1)
        self.i = 0
        self.dir = 1
        # approach phase: interpolate from start_pose to Q[0]
        self.approach_t = float(self.get_parameter('approach_time').value)
        self.q_start = np.array(self.get_parameter('start_pose').value, float)
        self.approach_n = int(self.approach_t * rate)
        self.approach_k = 0
        self.loop_mode = self.get_parameter('loop_mode').value
        self.rate = rate
        self.timer = self.create_timer(1.0 / rate, self.tick)
        # LIVE SPEED. create_timer() fixes the period at construction, so a plain
        # `ros2 param set ... rate` would be accepted and then silently ignored.
        # Rebuild the timer on change so the speed really does follow the param.
        self.add_on_set_parameters_callback(self._on_param)
        self.publish_path()
        self.publish_trajectory()
        if self.approach_n > 0:
            self.get_logger().info(
                f'approach: {self.approach_t:.1f} s ramp from the start pose to '
                f'waypoint 0 before tracing begins')
        self.get_logger().info(
            f'tracing: board x={bx*1000:.0f} mm, amplitude {amp*1000:.0f} mm, '
            f'span {ln*1000:.0f} mm')
        self.get_logger().info(
            f'{rate:.0f} Hz -> {len(self.Q)/rate:.1f} s per pass, '
            f'loop mode {self.loop_mode}. '
            f'change live:  ros2 param set /arm450_sine rate <hz>')

    def _on_param(self, params):
        from rcl_interfaces.msg import SetParametersResult
        for p in params:
            if p.name == 'rate':
                if not 0.5 <= p.value <= 500.0:
                    return SetParametersResult(
                        successful=False,
                        reason='rate must be between 0.5 and 500 Hz')
                self.rate = float(p.value)
                self.timer.cancel()
                self.timer = self.create_timer(1.0 / self.rate, self.tick)
                self.get_logger().info(
                    f'rate -> {self.rate:.1f} Hz '
                    f'({len(self.Q)/self.rate:.1f} s per pass)')
        return SetParametersResult(successful=True)

    def publish_path(self):
        m = Marker()
        m.header.frame_id = 'world'
        m.ns = 'sine'; m.id = 0
        m.type = Marker.LINE_STRIP; m.action = Marker.ADD
        m.scale.x = 0.002
        m.color.r, m.color.g, m.color.b, m.color.a = 1.0, 0.85, 0.2, 1.0
        m.pose.orientation.w = 1.0
        m.points = [Point(x=float(p[0]), y=float(p[1]), z=float(p[2]))
                    for p in self.P]
        self.mk.publish(m)

    def tick(self):
        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = JOINTS
        if self.approach_k < self.approach_n:
            # APPROACH: ease from the start pose to waypoint 0. Cosine ramp, so
            # it leaves and arrives at zero velocity instead of stepping.
            a = 0.5 * (1 - np.cos(np.pi * self.approach_k / self.approach_n))
            q = self.q_start * (1 - a) + self.Q[0] * a
            self.approach_k += 1
            if self.approach_k == self.approach_n:
                self.get_logger().info('approach complete, tracing')
            js.position = [float(v) for v in q]
            self.pub.publish(js)
            return
        js.position = [float(v) for v in self.Q[self.i]]
        self.pub.publish(js)
        if self.i == 0:
            self.publish_path()          # keep the marker alive
        self.advance()

    def publish_trajectory(self):
        """Publish the whole solved path once as a JointTrajectory.

        /joint_states is a VISUALISATION stream -- it says where the arm is, and
        a real controller will not follow it. A controller wants the path with
        timestamps, which is what this is. Latched (TRANSIENT_LOCAL) so a
        controller that starts later still receives it.
        """
        t = JointTrajectory()
        t.header.frame_id = 'base_link'
        t.joint_names = JOINTS
        dt = 1.0 / self.rate
        for k, q in enumerate(self.Q):
            pt = JointTrajectoryPoint()
            pt.positions = [float(v) for v in q]
            if k == 0:
                pt.velocities = [0.0] * 6
            elif k == len(self.Q) - 1:
                pt.velocities = [0.0] * 6
            else:
                pt.velocities = [float(v) for v in (self.Q[k + 1] - self.Q[k - 1]) / (2 * dt)]
            tt = (k + 1) * dt
            pt.time_from_start = Duration(sec=int(tt), nanosec=int((tt % 1) * 1e9))
            t.points.append(pt)
        self.traj_pub.publish(t)
        self.get_logger().info(
            f'published {len(t.points)}-point JointTrajectory on '
            f'/arm450/trajectory (latched) for a real controller')

    def advance(self):
        """Step the playback index.

        PING-PONG (default): trace forward, then BACK along the same waypoints,
        the way a pen actually retraces a line. This is how Rsine behaves.

        The old code did `self.i = (self.i + 1) % len(self.Q)`, which wraps from
        the last waypoint straight to the first. That is a discontinuity, not a
        loop: J4 jumps 43.3 deg and J1 32.2 deg in a single 40 ms tick -- 21x the
        largest step anywhere else on the path -- and the tool teleports 139.8 mm,
        the whole span. On screen the arm reaches the end of the sine, snaps back
        to the start and carries on. On real servos it would be a full-speed slam
        against the trajectory, twice per pass.

        Ping-pong has no discontinuity anywhere: the fastest step stays the 2.09
        deg the solver already guarantees between adjacent waypoints.
        """
        n = len(self.Q)
        if self.loop_mode == "wrap":
            self.i = (self.i + 1) % n
            return
        self.i += self.dir
        if self.i >= n:                  # bounce off the far end
            self.i, self.dir = n - 2, -1
        elif self.i < 0:                 # bounce off the near end
            self.i, self.dir = 1, 1
        # never emit the endpoint twice in a row, which would read as a stutter


def main():
    rclpy.init()
    n = SineTracer()
    try:
        rclpy.spin(n)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        # ExternalShutdownException is what arrives on SIGTERM (a launch-file
        # shutdown, or `timeout`). Without catching it the node exits with a
        # traceback that looks like a crash but is a clean stop.
        pass
    finally:
        n.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
