v=open('verify_drive.py').read()
if 'def attach_occ' not in v:
    v=v.replace('''def contains(m, P, chunk=20000):''','''def attach_occ(mesh, step_path, T=None):
    """Give a mesh its exact BRep for containment (see contains()).
    Needed where the mesh is open, or so slender and finely tessellated that
    trimesh's fallback ray test exhausts memory (link_fore_groove: 57 M rows)."""
    import cadquery as cq
    from OCP.gp import gp_Trsf
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    sh = cq.importers.importStep(step_path).val().wrapped
    if T is not None:
        tr = gp_Trsf(); tr.SetValues(*[float(T[i, j]) for i in range(3) for j in range(4)])
        sh = BRepBuilderAPI_Transform(sh, tr, True).Shape()
    mesh.occ = sh
    return mesh


def contains(m, P, chunk=20000):''')
    open('verify_drive.py','w').write(v)
f=open('full_scene.py').read()
f=f.replace('''    for k in ("link_fore_tongue", "link_fore_groove"):
        s[k] = ld(k, X[k])''','''    for k in ("link_fore_tongue", "link_fore_groove"):
        s[k] = ld(k, X[k])
        VD.attach_occ(s[k], os.path.join(HERE, k + ".step"), X[k])   # exact, memory-safe''')
open('full_scene.py','w').write(f)
j=open('verify_j4.py').read()
j=j.replace('''        m = trimesh.load(os.path.join(HERE, k + ".stl")); m.apply_transform(X[k]); fore[k] = m''','''        m = trimesh.load(os.path.join(HERE, k + ".stl")); m.apply_transform(X[k])
        from verify_drive import attach_occ
        fore[k] = attach_occ(m, os.path.join(HERE, k + ".step"), X[k])''')
open('verify_j4.py','w').write(j)
print('full_scene occ:', f.count('attach_occ'), ' verify_j4 occ:', j.count('attach_occ'))
