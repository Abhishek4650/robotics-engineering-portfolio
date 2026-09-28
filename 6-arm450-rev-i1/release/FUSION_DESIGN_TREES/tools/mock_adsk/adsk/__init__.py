"""Stand-in for Fusion 360's `adsk` API, for testing the part scripts on a
machine without Fusion. It implements only the calls fusion_engine.py makes,
with the documented Fusion behaviour, on OpenCascade solids (units: cm, as
Fusion's API). It is a test harness, not Fusion: it cannot prove how Fusion
itself will evaluate a feature, only that the scripts ask for the right ones."""
from . import core, fusion      # noqa: F401


def doEvents():
    pass
