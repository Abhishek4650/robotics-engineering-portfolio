#!/usr/bin/env python3

import math


class CartesianTrajectory:
    """
    Generates a sinusoidal Cartesian trajectory
    for the end-effector.
    """

    def __init__(self):

        # Home position (from verified FK)
        self.x0 = 0.2064
        self.y0 = -0.10622
        self.z0 = 0.13256

        # Sine parameters
        self.amplitude = 0.03      # 3 cm
        self.frequency = 0.20      # Hz

    def evaluate(self, t):

        x = self.x0 + self.amplitude * math.sin(
            2 * math.pi * self.frequency * t
        )

        y = self.y0

        z = self.z0

        return x, y, z
