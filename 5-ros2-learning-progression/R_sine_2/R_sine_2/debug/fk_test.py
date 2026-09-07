#!/usr/bin/env python3

import numpy as np

# -------------------------------
# Forward Kinematics Only
# -------------------------------

def forward_kinematics(q):

    t1, t2, t3, t4, t5, t6 = q

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

    R = np.eye(3)
    P = np.zeros(3)

    print("\nFrame Positions")
    print("---------------------------")

    for i in range(6):

        P = P + R @ P_links[i]
        R = R @ R_links[i]

        print(f"Frame {i+1}: {P}")

    return P, R


# -------------------------------
# Main
# -------------------------------

q = np.zeros(6)

position, rotation = forward_kinematics(q)

print("\n=================================")
print("End Effector Position")
print(position)

print("\nRotation Matrix")
print(rotation)
print("=================================")
