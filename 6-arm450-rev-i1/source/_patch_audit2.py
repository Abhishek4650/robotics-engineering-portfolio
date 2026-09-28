p='audit_pairs.py'; s=open(p).read()
s=s.replace('''        da = np.abs(trimesh.proximity.closest_point(B, pa)[1]) if len(pa) else np.zeros(0)
        db = np.abs(trimesh.proximity.closest_point(A, pb)[1]) if len(pb) else np.zeros(0)''','''        da, db = depth(B, pa), depth(A, pb)''')
s=s.replace('''def audit(s, n=4000, label=""):''','''def depth(M, P, cap=400, chunk=50):
    """Distance of each inside point to M's surface. Capped + chunked: a
    whole tongue-and-groove seam in one closest_point call exhausted 62 GB."""
    if not len(P):
        return np.zeros(0)
    if len(P) > cap:
        P = P[np.random.default_rng(0).choice(len(P), cap, replace=False)]
    out = [np.abs(trimesh.proximity.closest_point(M, P[i:i + chunk])[1]) for i in range(0, len(P), chunk)]
    return np.concatenate(out)


def audit(s, n=4000, label=""):''')
open(p,'w').write(s)
print('patched', s.count('def depth'))
