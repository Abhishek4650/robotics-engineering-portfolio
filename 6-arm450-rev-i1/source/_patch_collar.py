p='gen_base_collar.py'; s=open(p).read()
old='''        # heat-set insert on +X
        s = s.cut(cq.Workplane("YZ").center(Y_BOLT, z).circle(4.1 / 2)
                  .extrude(6.0).translate((SLOT_W / 2 + 0.5, 0, 0)))'''
new='''        # heat-set insert pressed in from the +X OUTER face, 6 deep, then a
        # clearance hole on to the slot so the bolt reaches it. (First cut it
        # from the slot outward to x 7.1: a SEALED cavity -- no insert can be
        # fitted into it; the mesh showed it as a separate body.)
        s = s.cut(cq.Workplane("YZ").center(Y_BOLT, z).circle(4.1 / 2)
                  .extrude(-7.0).translate((X_WALL + 1.0, 0, 0)))
        s = s.cut(cq.Workplane("YZ").center(Y_BOLT, z).circle(3.4 / 2)
                  .extrude(X_WALL + 1.0).translate((0.0, 0, 0)))'''
assert old in s
s=s.replace(old,new)
open(p,'w').write(s)
print('patched')
