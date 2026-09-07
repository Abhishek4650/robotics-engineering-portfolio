"""
Kinematics core for the myCobot 280 sinusoidal-path demo.

Provides:
  * build_chain()      -> ikpy Chain for the 6-DOF arm (root link1, EE gripper_base)
  * make_sine_path()   -> Nx3 array of Cartesian targets tracing a vertical (X-Z) sine
  * solve_path()       -> per-waypoint IK with warm-starting for smooth joint motion
  * fk_position()      -> forward-kinematics EE position for a joint vector

Uses the official Elephant Robotics myCobot 280 M5 description
(mycobot_ros2/mycobot_description). Root link = g_base, end-effector frame =
joint6_flange. Only the 6 revolute joints are active; the fixed base joint is
masked out so IK solves over exactly 6 DOF.

JOINT_NAMES is the ordered list of the 6 revolute joints, matching the URDF and
the order ikpy returns them in (used by the ROS JointState publisher).
"""

import os
import numpy as np
from ikpy.chain import Chain
from make_local_urdf import ensure_local_urdf

# Official M5 URDF with mesh paths rewritten to absolute file:// for *this* PC
# (generated on demand so the package is relocatable; see make_local_urdf.py).
URDF_PATH = ensure_local_urdf()

# Revolute joints in chain order (official mycobot_280_m5 naming).
JOINT_NAMES = [
    "joint2_to_joint1",
    "joint3_to_joint2",
    "joint4_to_joint3",
    "joint5_to_joint4",
    "joint6_to_joint5",
    "joint6output_to_joint6",
]


def build_chain(urdf_path: str = URDF_PATH) -> Chain:
    """Build the ikpy Chain. Active links = the 6 revolute joints only."""
    urdf_path = os.path.abspath(urdf_path)
    chain = Chain.from_urdf_file(
        urdf_path,
        base_elements=["g_base"],
        name="mycobot_280_m5",
    )
    # Activate only links whose joint is one of the 6 revolute joints.
    mask = [link.name in JOINT_NAMES for link in chain.links]
    chain.active_links_mask = mask
    return chain


def make_sine_path(
    x0: float = 0.10,
    x1: float = 0.20,
    y: float = 0.0,
    z0: float = 0.18,
    amplitude: float = 0.03,
    wavelength: float = 0.10,
    n_points: int = 120,
) -> np.ndarray:
    """Vertical sine in the X-Z plane: sweep X from x0->x1 at fixed y,
    with z = z0 + amplitude * sin(2*pi*(x-x0)/wavelength). Returns (N,3)."""
    xs = np.linspace(x0, x1, n_points)
    zs = z0 + amplitude * np.sin(2.0 * np.pi * (xs - x0) / wavelength)
    ys = np.full_like(xs, y)
    return np.column_stack([xs, ys, zs])


def solve_path(chain: Chain, points: np.ndarray, seed: np.ndarray | None = None):
    """Solve IK for each Cartesian point, warm-starting from the previous
    solution for continuity. Returns (joint_solutions, full_solutions):
      joint_solutions : (N,6) active-joint angles in JOINT_NAMES order
      full_solutions  : (N, n_links) full ikpy vectors (for FK)."""
    n_links = len(chain.links)
    q_full = np.zeros(n_links) if seed is None else np.asarray(seed, float)
    active_idx = [i for i, a in enumerate(chain.active_links_mask) if a]

    full_solutions = []
    for p in points:
        q_full = chain.inverse_kinematics(target_position=p, initial_position=q_full)
        full_solutions.append(q_full.copy())

    full_solutions = np.array(full_solutions)
    joint_solutions = full_solutions[:, active_idx]
    return joint_solutions, full_solutions


def fk_position(chain: Chain, q_full: np.ndarray) -> np.ndarray:
    """Forward kinematics: EE (gripper_base) position for a full ikpy vector."""
    return chain.forward_kinematics(q_full)[:3, 3]
