#!/usr/bin/env python3
"""
Generate a machine-local copy of the myCobot 280 M5 URDF with absolute mesh
paths, so the model renders in RViz without a colcon-built ROS package.

The shipped base URDF (mycobot_280_m5.urdf) references its meshes with
`package://mycobot_description/urdf/mycobot_280_m5/...`. RViz can only resolve
that if the package is built+sourced, so instead we rewrite those references to
absolute `file://` paths pointing at this repo's actual location on *this* PC.

The generated file (mycobot_280_m5_local.urdf) is therefore machine-specific and
is regenerated on demand -- it is git-ignored. `ensure_local_urdf()` is called
automatically by kinematics.py and the launch file, so a fresh checkout self-heals.

Run standalone:  python scripts/make_local_urdf.py
"""

import os

PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M5_DIR = os.path.join(PKG_DIR, "urdf", "mycobot_280_m5")
BASE_URDF = os.path.join(M5_DIR, "mycobot_280_m5.urdf")
LOCAL_URDF = os.path.join(M5_DIR, "mycobot_280_m5_local.urdf")

PACKAGE_PREFIX = "package://mycobot_description/urdf/mycobot_280_m5/"


def ensure_local_urdf(force: bool = False) -> str:
    """Generate (if needed) and return the path to the machine-local URDF."""
    if force or not os.path.exists(LOCAL_URDF) or (
        os.path.getmtime(LOCAL_URDF) < os.path.getmtime(BASE_URDF)
    ):
        local_mesh_prefix = "file://" + M5_DIR.rstrip("/") + "/"
        with open(BASE_URDF, "r") as f:
            text = f.read()
        text = text.replace(PACKAGE_PREFIX, local_mesh_prefix)
        with open(LOCAL_URDF, "w") as f:
            f.write(text)
    return LOCAL_URDF


if __name__ == "__main__":
    path = ensure_local_urdf(force=True)
    print(f"generated {path}")
