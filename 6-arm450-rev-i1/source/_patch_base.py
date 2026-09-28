s=open('full_scene.py').read()
s=s.replace('''    for k in ("base", "shaft_clamp_1", "shaft_clamp_2", "shaft_clamp_3", "shaft_clamp_4",
              "link_upper_groove", "link_upper_tongue"):
        s[k] = rel[k]''','''    for k in ("shaft_clamp_1", "shaft_clamp_2", "shaft_clamp_3", "shaft_clamp_4",
              "link_upper_groove", "link_upper_tongue"):
        s[k] = rel[k]
    s["base"] = ld("base")          # rev I: lower 6806 pocket opens from underneath''')
open('full_scene.py','w').write(s)
v=open('verify_j1.py').read()
v=v.replace('''    base = trimesh.load(os.path.join(HERE, "../out_cad/base.stl"))''','''    base = trimesh.load(os.path.join(HERE, "base.stl"))      # rev I base''')
v=v.replace('''    fails = [r for r in RES if not r[1]]''','''    # collar pinch bolts: along +X from the -X side, at the wall mid-radius
    import gen_base_collar as GB
    import math
    for z in GB.BOLT_Z:
        run = None
        for d in np.arange(0.5, 70, 0.5):
            x = -GB.X_WALL - d
            ring = np.array([[x, GB.Y_BOLT + 1.25 * math.cos(t), z + 1.25 * math.sin(t)]
                             for t in np.linspace(0, 2 * np.pi, 12, endpoint=False)])
            if any(m.contains(ring).any() for m in (base, mount, turret, srv)):
                run = d; break
        rec("G collar pinch bolt z %.1f: hex-key run from outside" % z, run is None,
            ">70 mm clear" if run is None else "blocked at %.1f mm" % run)
    fails = [r for r in RES if not r[1]]''',1)
open('verify_j1.py','w').write(v)
