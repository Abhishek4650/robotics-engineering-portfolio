#!/usr/bin/env python3

import numpy as np

from mycobot_sine_project.kinematics import MyCobotKinematics


class MyCobotIKSolver:
    """
    Damped Least Squares Inverse Kinematics Solver
    """

    def __init__(self):

        self.robot = MyCobotKinematics()

        self.lambda_ = 0.02

        self.max_iterations = 5

        print("IK Solver Initialized")

    def solve(self, target_position, q_current):

        q = np.array(q_current, dtype=float)

        for _ in range(self.max_iterations):

            # Current end-effector position
            p = self.robot.get_position(q)

            # Position error
            error = target_position - p

            # Stop if converged
            if np.linalg.norm(error) < 1e-4:
                break

            # Jacobian
            J = self.robot.compute_jacobian(q)

            # Position Jacobian only
            Jv = J[0:3, :]

            # Damped Least Squares
            damping = (self.lambda_ ** 2) * np.eye(3)

            dq = (
                Jv.T
                @ np.linalg.inv(Jv @ Jv.T + damping)
                @ error
            )

            q += dq

        return q
