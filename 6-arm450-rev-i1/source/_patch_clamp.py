a=open('asm_meshes.py').read()
if 'REV_I_CLAMP' not in a:
    a=a.replace('''    top = TDF_LabelSequence()
    st.GetFreeShapes(top)
    for i in range(1, top.Length() + 1):
        walk(top.Value(i), TopLoc_Location())
    return out''','''    top = TDF_LabelSequence()
    st.GetFreeShapes(top)
    for i in range(1, top.Length() + 1):
        walk(top.Value(i), TopLoc_Location())
    # REV_I_CLAMP: the released O38 ring cannot enter the links' D-shaped
    # bores (the seam ear). Substitute the rev-I clamp, seated in each link
    # half's own frame (the released clamps sit at its bore centre, z 0..14).
    import asm_xforms as AX
    X = AX.xforms()
    here = os.path.dirname(os.path.abspath(__file__))
    for ck, lk in (("shaft_clamp_1", "link_upper_groove"), ("shaft_clamp_2", "link_upper_tongue"),
                   ("shaft_clamp_3", "link_fore_groove"), ("shaft_clamp_4", "link_fore_tongue")):
        if ck in out or ck in skip:
            if ck in skip:
                continue
            m = trimesh.load(os.path.join(here, "shaft_clamp.stl"))
            m.apply_transform(X[lk])
            out[ck] = m
    return out''')
    open('asm_meshes.py','w').write(a)
g=open('gen_forearm.py').read()
if 'recut the seam groove' not in g:
    g=g.replace('''        s = build(t, LP.FORE_FACE_X, "socket")''','''        s = build(t, LP.FORE_FACE_X, "socket")
        if not t:
            # recut the seam groove AFTER the bosses: carrying the boss 0.5 mm
            # into the wall also refilled part of the groove band, and the
            # tongue's lip met it (0.27 mm, static all-pairs audit)
            h, clr = LP.SEC_H / 2.0, LP.SEAM_LIP_CLR
            depth = LP.SEAM_LIP + LP.SEAM_GROOVE_EXTRA + clr
            go = LP.capsule(LP.FORE_FACE_X, h - 0.2 + clr, LP.BOSS_R - 0.2 + clr, depth + 0.2)
            gi = LP.capsule(LP.FORE_FACE_X, h - 0.2 - 2.0 - clr, LP.BOSS_R - 0.2 - 2.0 - clr,
                            depth + 2.2).translate((0, 0, -1))
            s = s.cut(go.cut(gi).translate((0, 0, LP.HALF_D - depth)))''')
    open('gen_forearm.py','w').write(g)
print('patched')
