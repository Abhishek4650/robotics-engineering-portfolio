#!/usr/bin/env python3
"""
Print orientation for EVERY part in the final print list, chosen by
measurement, written to PRINT_ORIENTATION.json (read by make_final_print.py).

For each of the six 'which face down' orientations:
  findings   layer-slice gate (ISLAND / SUB-LAYER / UNPRINTABLE), slice_check
  overhang   area of downward faces steeper than 45 deg, not on the bed (mm2)
  bed        first-layer contact area (mm2)
Best = fewest findings, then least overhang, then most bed.
Supports: none < 150 mm2 of overhang and no islands; advised < 1500;
REQUIRED above, or whenever an island remains.
"""
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "PRINT_GATE"))
sys.path.insert(0, HERE)
import orient_gate as OG         # noqa: E402
import make_final_print as MF    # noqa: E402


def overhang(m):
    n = m.face_normals
    c = m.triangles_center
    sel = (n[:, 2] < -np.cos(np.radians(45))) & (c[:, 2] > 0.3)
    return float(m.area_faces[sel].sum())


def main(names=None):
    plan = {}
    for nm, q, src, note in MF.PARTS:
        if names and nm not in names:
            continue
        path = os.path.join(src, nm + ".stl")
        res = OG.gate(path)
        m0 = trimesh.load(path)
        rows = []
        for k, (n, bed, out) in res.items():
            mm = m0.copy(); mm.apply_transform(OG.ORIENTS[k]); mm.apply_translation([0, 0, -mm.bounds[0][2]])
            isl = sum(1 for ln in out.splitlines() if ln.strip().startswith("ISLAND"))
            rows.append((n, overhang(mm), -bed, k, isl))
        rows.sort()
        n, oh, nb, k, isl = rows[0]
        sup = "REQUIRED" if (isl or oh >= 1500) else ("advised" if oh >= 150 else "none")
        plan[nm] = {"orient": k, "islands": isl, "findings": n, "overhang_mm2": int(round(oh)),
                    "bed_mm2": int(round(-nb)), "supports": sup}
        print("%-18s %-6s findings %d  islands %d  overhang %5.0f mm2  bed %5.0f mm2  supports %-8s | %s"
              % (nm, k, n, isl, oh, -nb, sup, "  ".join("%s:%d/%.0f" % (r[3], r[0], r[1]) for r in sorted(rows, key=lambda r: r[3]))))
    return plan


if __name__ == "__main__":
    plan = main(sys.argv[1:] or None)
    fn = os.path.join(HERE, "PRINT_ORIENTATION.json")
    old = json.load(open(fn)) if os.path.exists(fn) else {}
    old.update(plan)
    json.dump(old, open(fn, "w"), indent=1)
    print("written", fn)
