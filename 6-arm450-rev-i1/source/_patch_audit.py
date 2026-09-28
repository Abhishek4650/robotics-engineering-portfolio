p='audit_pairs.py'; s=open(p).read()
s=s.replace('''        pts = np.vstack([pa, pb])
        t = thickness(pts)
        rows.append((a, b, len(pts), t, pts.min(0), pts.max(0)))
        print("   %-18s | %-18s %5d pts  t %.3f  %s" % (a, b, len(pts), t,
              "CLASH?" if t >= 0.15 else "face"), flush=True)''','''        pts = np.vstack([pa, pb])
        # PENETRATION DEPTH: how far each overlapping sample lies inside the
        # OTHER part. Seats, press fits, pinch walls and coincident faces are
        # ~0 everywhere; a clash has real depth. (The first version measured
        # the thickness of the contact cloud, which fails for a servo pinched
        # between TWO walls or a spigot in a round socket.)
        da = np.abs(trimesh.proximity.closest_point(B, pa)[1]) if len(pa) else np.zeros(0)
        db = np.abs(trimesh.proximity.closest_point(A, pb)[1]) if len(pb) else np.zeros(0)
        t = float(np.concatenate([da, db]).max())
        rows.append((a, b, len(pts), t, pts.min(0), pts.max(0)))
        print("   %-18s | %-18s %5d pts  depth %.3f  %s" % (a, b, len(pts), t,
              "CLASH" if t >= 0.15 else "surface"), flush=True)''')
s=s.replace('import numpy as np\n','import numpy as np\nimport trimesh\n',1)
s=s.replace('FACE contacts (thickness < 0.15 mm -- seats, bolted faces, pinch):','SURFACE contacts (penetration < 0.15 mm -- seats, bolted faces, pinch, fits):')
s=s.replace('VOLUMETRIC overlaps (thickness >= 0.15 mm) -- must each be explained:','CLASHES (penetration >= 0.15 mm) -- must each be explained:')
s=s.replace('%5d pts  t %.3f" % (a, b, n, t))','%5d pts  depth %.3f" % (a, b, n, t))')
s=s.replace('%5d pts  t %.2f  x','%5d pts  depth %.2f  x')
open(p,'w').write(s)
print('patched', s.count('PENETRATION DEPTH'))
