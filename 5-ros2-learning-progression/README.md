# How I learned ROS 2 — the working record

I started ROS 2 from zero. These are the packages I built on the way to the verified
solver in [`1-ros2-sine-tracing`](../1-ros2-sine-tracing), kept **in order and unedited**,
because the path matters as much as the destination.

| # | Package | What I was learning | What it does |
| --- | --- | --- | --- |
| 1 | [`my_first_pkg`](my_first_pkg) | The ROS 2 graph | A publisher and a subscriber. Nodes, topics, `setup.py`, `colcon build` — day one. |
| 2 | [`fk_robot`](fk_robot) | Forward kinematics | First transform chain: joint angles → end-effector pose, and checking it against the URDF instead of trusting it. |
| 3 | [`R_sine`](R_sine) | Closing the loop | First attempt at the real task — a sine path, an IK node, and a path tracer to see what the arm *actually* did. |
| 4 | [`R_sine_2`](R_sine_2) | Debugging my own maths | A rewrite after the first version drifted. Includes the `debug/fk_test.py` I wrote to find out why. |
| 5 | [`mycobot_sine_project`](mycobot_sine_project) | Structure | Split into `jacobian.py`, `ik_solver.py`, `trajectory.py`, `publisher.py` — one responsibility per module, so failures became locatable. |
| 6 | **[`Rsine`](../1-ros2-sine-tracing)** | Verification | The finished package: analytical Jacobian by velocity propagation, DLS IK, and every stage checked numerically against the URDF and against `ikpy`. |

## What the progression shows

Steps 3 and 4 exist because step 3 was wrong. The arm drifted off the plane and I did not
know why, so I wrote a separate FK test to isolate whether the error was in the kinematics
or in the solver. It was in the kinematics.

That is the habit worth showing: when something is off, build the smaller test that tells
you *where* it is off, rather than adjusting numbers until the picture looks right. The
1e-15 m agreement in the final package is a direct consequence of having been burned here.

These packages are kept for the record. **For working code, use
[`1-ros2-sine-tracing`](../1-ros2-sine-tracing)** — it supersedes all of them.
