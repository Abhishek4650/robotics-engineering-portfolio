p='build_final_assembly.py'; s=open(p).read()
s=s.replace('''    out = os.path.join(HERE, "ARM450_REV_I_ASSEMBLY.step")
    A.save(out)
    print("written", out, "(%d components)" % len(A.children))''','''    out = os.path.join(HERE, "ARM450_REV_I_ASSEMBLY.step")
    A.save(out)
    print("written", out, "(%d components)" % len(A.children))
    # every component as a WORLD-placed mesh, so the PDF sections slice exactly
    # what the STEP assembly contains
    md = os.path.join(HERE, "_asm_meshes")
    os.makedirs(md, exist_ok=True)
    for ch in A.children:
        obj = ch.obj.val() if hasattr(ch.obj, "val") else ch.obj
        sh = obj.moved(ch.loc)
        cq.exporters.export(cq.Workplane().add(sh), os.path.join(md, ch.name + ".stl"),
                            tolerance=0.05, angularTolerance=0.3)
    print("component meshes in", md)''')
open(p,'w').write(s)
print('patched')
