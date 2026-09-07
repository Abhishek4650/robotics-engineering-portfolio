#!/usr/bin/env python3
"""Dependency-free STL inspector: for each STL report triangle count and the
axis-aligned bounding box (min/max/size/centre) in file units (usually mm).

Purpose: find out whether the individual part STLs are in a SHARED assembled
coordinate frame (their boxes stack along the arm at distinct positions) or
each in its own local frame (all centred near origin). That decides how we
derive the DH table."""
import sys, os, struct, glob
import numpy as np


def load_stl_vertices(path):
    with open(path, "rb") as f:
        data = f.read()
    size = len(data)
    # binary STL: 80-byte header + uint32 count + count*50 bytes
    if size >= 84:
        ntri = struct.unpack_from("<I", data, 80)[0]
        if 84 + ntri * 50 == size:
            # each tri: 12 floats (normal xyz + v1 v2 v3) + 2-byte attr
            arr = np.frombuffer(data, dtype=np.uint8, offset=84)
            arr = arr.reshape(ntri, 50)
            floats = arr[:, 12:48].copy().view("<f4").reshape(ntri, 3, 3)
            return floats.reshape(-1, 3), ntri
    # else ASCII
    verts = []
    for line in data.decode("ascii", "replace").splitlines():
        line = line.strip()
        if line.startswith("vertex"):
            parts = line.split()
            verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
    v = np.array(verts, float)
    return v, len(v) // 3


def report(path):
    v, ntri = load_stl_vertices(path)
    if len(v) == 0:
        print(f"{os.path.basename(path):32s} EMPTY/unreadable"); return None
    lo, hi = v.min(0), v.max(0)
    size = hi - lo
    ctr = (lo + hi) / 2
    name = os.path.basename(path)
    print(f"{name:34s} tri={ntri:7d}  "
          f"size=({size[0]:7.1f},{size[1]:7.1f},{size[2]:7.1f})  "
          f"ctr=({ctr[0]:8.1f},{ctr[1]:8.1f},{ctr[2]:8.1f})")
    return dict(name=name, lo=lo, hi=hi, size=size, ctr=ctr, ntri=ntri)


if __name__ == "__main__":
    folder = "/home/user/Desktop/Robotic_arm_design"
    args = sys.argv[1:]
    files = args if args else sorted(glob.glob(os.path.join(folder, "*.stl")))
    print(f"{'file':34s} {'tris':>11s}  size (x,y,z)                 centre (x,y,z)")
    print("-" * 104)
    infos = [report(f) for f in files]
    infos = [i for i in infos if i]
    if infos:
        allo = np.min([i["lo"] for i in infos], 0)
        ahi = np.max([i["hi"] for i in infos], 0)
        print("-" * 104)
        print(f"UNION bbox  min=({allo[0]:.1f},{allo[1]:.1f},{allo[2]:.1f})  "
              f"max=({ahi[0]:.1f},{ahi[1]:.1f},{ahi[2]:.1f})  "
              f"span=({ahi[0]-allo[0]:.1f},{ahi[1]-allo[1]:.1f},{ahi[2]-allo[2]:.1f})")
