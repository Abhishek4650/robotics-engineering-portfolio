"""Solid-vs-solid difference in mm3, robust to OCC's trouble with identical
shapes: Cut(a, b) of a solid by an exact copy sometimes returns all of a,
and Common sometimes returns nothing (seen on J3_p2 / J5_p2). Every failure
mode reads HIGH (a false alarm), so three estimates are made and the
smallest is kept per side:
  1. Cut(a, b)
  2. V(a) - V(Common(a, b))
  3. shift b by e and 2e (e = 1 um, oblique): the sliver grows linearly,
     X(e) = D + k.e, so D = 2.X(e) - X(2e) -- no coincident faces involved."""
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.gp import gp_Trsf, gp_Vec


def vol(s):
    """adaptive integration: the default Gauss rule is off by ~1 mm3 on some
    faces (the same forearm solid read 30084.48 or 30085.51 depending on how
    its faces were split; both 30085.0429 adaptively), and even eps 1e-7 was
    0.26 mm3 off on merged faces of j6_body (65220.4124 vs 65220.1475 at 1e-11,
    where a 2 um mesh of both agrees to 1e-10)."""
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(s, g, 1e-11, False)
    return g.Mass()


def _shift(s, e):
    t = gp_Trsf(); t.SetTranslation(gp_Vec(e * 0.8018, e * 0.5345, e * 0.2673))
    return BRepBuilderAPI_Transform(s, t, True).Shape()


def diff(a, b, tol=1e-3):
    """(a minus b, b minus a) mm3. A pair of estimates is only believed if it
    balances: (a-b) - (b-a) must equal V(a) - V(b); of the balanced pairs the
    smallest is kept. If none balances, the plain Cut pair is returned (a
    failed Cut reads high)."""
    va, vb = vol(a), vol(b)
    vc = vol(BRepAlgoAPI_Common(a, b).Shape())
    cands = [(vol(BRepAlgoAPI_Cut(a, b).Shape()), vol(BRepAlgoAPI_Cut(b, a).Shape()))]
    if vc <= min(va, vb) + 1e-6:
        cands.append((va - vc, vb - vc))
    e = 1e-3
    b1, b2 = _shift(b, e), _shift(b, 2 * e)
    cands.append((2 * vol(BRepAlgoAPI_Cut(a, b1).Shape()) - vol(BRepAlgoAPI_Cut(a, b2).Shape()),
                  2 * vol(BRepAlgoAPI_Cut(b1, a).Shape()) - vol(BRepAlgoAPI_Cut(b2, a).Shape())))
    bal = lambda d: abs((d[0] - d[1]) - (va - vb)) <= max(tol, 1e-7 * max(va, vb))
    ok = [d for d in cands if bal(d) and min(d) > -tol]
    d = min(ok, key=max) if ok else cands[0]
    return max(d[0], 0.0), max(d[1], 0.0)
