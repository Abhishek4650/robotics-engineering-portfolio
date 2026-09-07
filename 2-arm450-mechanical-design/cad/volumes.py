"""
Regenerate output/cad/volumes.json from the exported STEP files.

This table is the authority for part mass everywhere -- the pre-print mass gate,
the drawings, the URDF meshes and the BOM all read it. It has to come from STEP
rather than STL because trimesh reports the link shells as non-watertight, and
summing a non-watertight mesh's .volume silently drops it to zero.

Written 2026-08-21. Until now NOTHING regenerated this file: every script
read it and none wrote it, so it had been produced once by hand and then went
stale the moment a part changed. Adding the Ø10 tool pilot to wrist_j6_output
is exactly that case -- the drawing kept quoting the pre-pilot mass.

Run it after any CAD change:  python3 cad/volumes.py
"""
import os
import glob
import json
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "..", "output", "cad")
OUT = os.path.join(CAD, "volumes.json")


def main():
    old = {}
    if os.path.exists(OUT):
        old = json.load(open(OUT))
    vols = {}
    for p in sorted(glob.glob(os.path.join(CAD, "*.step"))):
        name = os.path.splitext(os.path.basename(p))[0]
        try:
            vols[name] = cq.importers.importStep(p).val().Volume()
        except Exception as e:                                # noqa: BLE001
            print(f"  SKIP {name}: {e}")
    json.dump(vols, open(OUT, "w"), indent=1, sort_keys=True)
    print(f"volumes.json — {len(vols)} parts\n")
    for k in sorted(vols):
        d = ""
        if k in old and abs(old[k] - vols[k]) > 1.0:
            d = f"   was {old[k]:9.1f}  ({vols[k]-old[k]:+.1f})"
        gone = "" if k in old else "   NEW"
        print(f"  {k:24s} {vols[k]:10.1f} mm3{d}{gone}")
    for k in sorted(set(old) - set(vols)):
        print(f"  {k:24s} {'—':>10s}      REMOVED (no STEP)")


if __name__ == "__main__":
    main()
