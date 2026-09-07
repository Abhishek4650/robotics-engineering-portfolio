#!/usr/bin/env python3

import numpy as np


class MyCobotKinematics:

    def __init__(self):

        # URDF Joint Definitions
        self.joints = [

            {
                "xyz": [0.0, 0.0, 0.13156],
                "rpy": [0.0, 0.0, np.pi/2]
            },

            {
                "xyz": [0.0, 0.0, -0.001],
                "rpy": [0.0, np.pi/2, -np.pi/2]
            },

            {
                "xyz": [-0.1104, 0.0, 0.0],
                "rpy": [0.0, 0.0, 0.0]
            },

            {
                "xyz": [-0.096, 0.0, 0.06062],
                "rpy": [0.0, 0.0, -np.pi/2]
            },

            {
                "xyz": [0.0, -0.07318, 0.0],
                "rpy": [np.pi/2, -np.pi/2, 0.0]
            },

            {
                "xyz": [0.0, 0.0456, 0.0],
                "rpy": [-np.pi/2, 0.0, 0.0]
            }

        ]

    # ------------------------------------------------
    # Rotation about X
    # ------------------------------------------------
    def Rx(self, angle):

        c = np.cos(angle)
        s = np.sin(angle)

        return np.array([
            [1, 0, 0],
            [0, c, -s],
            [0, s,  c]
        ])

    # ------------------------------------------------
    # Rotation about Y
    # ------------------------------------------------
    def Ry(self, angle):

        c = np.cos(angle)
        s = np.sin(angle)

        return np.array([
            [ c, 0, s],
            [ 0, 1, 0],
            [-s, 0, c]
        ])

    # ------------------------------------------------
    # Rotation about Z
    # ------------------------------------------------
    def Rz(self, angle):

        c = np.cos(angle)
        s = np.sin(angle)

        return np.array([
            [c, -s, 0],
            [s,  c, 0],
            [0,  0, 1]
        ])

    # ------------------------------------------------
    # Homogeneous Transformation
    # ------------------------------------------------
    def transform(self, R, p):

        T = np.eye(4)

        T[:3, :3] = R
        T[:3, 3] = p

        return T

    # ------------------------------------------------
    # URDF Joint Transform
    # ------------------------------------------------
    def joint_transform(self, xyz, rpy, theta):

        R_joint = self.Rz(theta)

        R_fixed = (
            self.Rz(rpy[2])
            @ self.Ry(rpy[1])
            @ self.Rx(rpy[0])
        )

        R = R_joint @ R_fixed

        p = np.array(xyz)

        return self.transform(R, p)

    # ------------------------------------------------
    # Forward Kinematics
    # ------------------------------------------------
    def forward_kinematics(self, q):

        t1, t2, t3, t4, t5, t6 = q

        # Rotation matrices (from verified R_sine implementation)
        R01 = np.array([
            [np.cos(t1), -np.sin(t1), 0],
            [np.sin(t1),  np.cos(t1), 0],
            [0, 0, 1]
        ])

        R12 = np.array([
            [np.cos(t2), -np.sin(t2), 0],
            [0, 0, -1],
            [np.sin(t2), np.cos(t2), 0]
        ])

        R23 = np.array([
            [np.cos(t3), -np.sin(t3), 0],
            [np.sin(t3),  np.cos(t3), 0],
            [0, 0, 1]
        ])

        R34 = np.array([
            [np.cos(t4), -np.sin(t4), 0],
            [np.sin(t4),  np.cos(t4), 0],
            [0, 0, 1]
        ])

        R45 = np.array([
            [np.cos(t5), -np.sin(t5), 0],
            [0, 0, -1],
            [np.sin(t5), np.cos(t5), 0]
        ])

        R56 = np.array([
            [np.cos(t6), -np.sin(t6), 0],
            [0, 0, 1],
            [-np.sin(t6), -np.cos(t6), 0]
        ])

        R_links = [R01, R12, R23, R34, R45, R56]

        P_links = [

            np.array([0.0, 0.0, 0.13156]),

            np.array([0.0, 0.0, 0.001]),

            np.array([0.1104, 0.0, 0.0]),

            np.array([0.096, 0.0, 0.06062]),

            np.array([0.0, 0.0, 0.0]),

            np.array([0.0, 0.0456, 0.0])

        ]

        R_curr = np.eye(3)

        P_curr = np.zeros(3)

        frames = []

        T0 = np.eye(4)

        frames.append(T0.copy())

        for i in range(6):

            # Translate in current frame
            P_curr = P_curr + R_curr @ P_links[i]

            # Rotate into next frame
            R_curr = R_curr @ R_links[i]

            # Homogeneous transform
            T = np.eye(4)
            T[:3, :3] = R_curr
            T[:3, 3] = P_curr

            frames.append(T.copy())

        T_end = frames[-1]

        return T_end, frames

    # ------------------------------------------------
    # Geometric Jacobian
    # ------------------------------------------------
    def compute_jacobian(self, q):

        T, frames = self.forward_kinematics(q)

        p_end = T[:3, 3]

        J = np.zeros((6, 6))

        for i in range(6):

            T_i = frames[i]

            p_i = T_i[:3, 3]

            z_i = T_i[:3, 2]

            J[0:3, i] = np.cross(
                z_i,
                p_end - p_i
            )

            J[3:6, i] = z_i

        return J

    # ------------------------------------------------
    # End Effector Position
    # ------------------------------------------------
    def get_position(self, q):

        T, _ = self.forward_kinematics(q)

        return T[:3, 3]

    # ------------------------------------------------
    # End Effector Rotation
    # ------------------------------------------------
    def get_rotation(self, q):

        T, _ = self.forward_kinematics(q)

        return T[:3, :3]

    # ------------------------------------------------
    # Joint-1 Transform (Debug)
    # ------------------------------------------------
    def T01(self, theta1):

        R = self.Rz(theta1) @ self.Rz(np.pi/2)

        p = np.array([
            0.0,
            0.0,
            0.13156
        ])

        return self.transform(R, p)
