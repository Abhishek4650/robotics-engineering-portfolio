# 1) released meshes: merge duplicated edge vertices so they close
a=open('asm_meshes.py').read()
a=a.replace('''    return trimesh.Trimesh(vertices=np.array(V), faces=np.array(F),
                           process=False)''','''    m = trimesh.Trimesh(vertices=np.array(V), faces=np.array(F), process=False)
    # per-face tessellation duplicates every shared-edge vertex: merge them or
    # the mesh is open and contains() is unreliable (found by the closure audit)
    m.merge_vertices(digits_vertex=4)
    m.remove_unreferenced_vertices()
    return m''')
open('asm_meshes.py','w').write(a)
# 2) exact containment for parts whose mesh cannot be closed
v=open('verify_drive.py').read()
v=v.replace('''def contains(m, P, chunk=20000):
    return np.concatenate([m.contains(P[i:i + chunk]) for i in range(0, len(P), chunk)])''','''def contains(m, P, chunk=20000):
    """Point-in-solid. Uses OpenCascade's exact classifier when the part
    carries its BRep (m.occ) -- required where the mesh is not closed."""
    occ = getattr(m, "occ", None)
    if occ is not None:
        from OCP.BRepClass3d import BRepClass3d_SolidClassifier
        from OCP.gp import gp_Pnt
        from OCP.TopAbs import TopAbs_IN
        out = np.zeros(len(P), bool)
        clf = BRepClass3d_SolidClassifier(occ)
        for i, p in enumerate(P):
            clf.Perform(gp_Pnt(*map(float, p)), 1e-6)
            out[i] = clf.State() == TopAbs_IN
        return out
    return np.concatenate([m.contains(P[i:i + chunk]) for i in range(0, len(P), chunk)])''')
open('verify_drive.py','w').write(v)
# 3) full scene: attach the exact solid to the released upper tongue
f=open('full_scene.py').read()
f=f.replace('''    s["base"] = ld("base")          # rev I: lower 6806 pocket opens from underneath''','''    s["base"] = ld("base")          # rev I: lower 6806 pocket opens from underneath
    # the released upper tongue's mesh is non-manifold in every export; its
    # STEP is valid, so checks use the exact solid (verify_drive.contains)
    import cadquery as cq
    from OCP.gp import gp_Trsf
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    T = X["link_upper_tongue"]
    tr = gp_Trsf(); tr.SetValues(*[float(T[i, j]) for i in range(3) for j in range(4)])
    sh = cq.importers.importStep(os.path.join(HERE, "../out_cad/link_upper_tongue.step")).val().wrapped
    s["link_upper_tongue"].occ = BRepBuilderAPI_Transform(sh, tr, True).Shape()''')
open('full_scene.py','w').write(f)
print('patched')
