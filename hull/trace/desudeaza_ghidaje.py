# The welded guides taken apart again (asked: the welded guides in parts, still assembled, exactly as before welding): every
# spline of the joined curve object becomes its own curve object - same points, place, bevel, material - named after the
# guide it came from, found by matching its shape (points relative to its first one) against the guide npz files given as
# prefix=file; unmatched ones get a number. The welded object is removed. Nothing is moved or changed.
# Usage: blender -b <in> --python desudeaza_ghidaje.py -- <out.blend> <welded object> <new prefix> <pre=file.npz> ...
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, N, NP = a[0], a[1], a[2]
cand = []
for s in a[3:]:
    p, f = s.split("=", 1); G = np.load(f)
    for k in G.files:
        q = np.asarray(G[k], float)
        if q.ndim == 2 and q.shape[1] == 3 and len(q) > 1: cand.append((p + "_" + k, q - q[0], len(q)))
o = bpy.data.objects[N]; d = o.data; col = o.users_collection[0]; used = {}; nm_ = 0; npt = 0
for i, sp in enumerate(d.splines):
    P = np.array([pt.co[:3] for pt in sp.points]); rel = P - P[0]; name = None
    for key, q, n in cand:
        if n == len(P) and np.abs(q - rel).max() < 1e-3: name = key; break
    if name is None: name = "linie_%03d" % i; nm_ += 1
    used[name] = used.get(name, 0) + 1
    if used[name] > 1: name += "_%d" % used[name]
    cu = bpy.data.curves.new(NP + name, "CURVE"); cu.dimensions = d.dimensions; cu.bevel_depth = d.bevel_depth; cu.bevel_resolution = d.bevel_resolution
    cu.fill_mode = d.fill_mode
    for m in d.materials: cu.materials.append(m)
    s2 = cu.splines.new(sp.type); s2.points.add(len(sp.points) - 1); s2.use_cyclic_u = sp.use_cyclic_u; s2.material_index = sp.material_index
    for p2, p1 in zip(s2.points, sp.points): p2.co = p1.co
    k = bpy.data.objects.new(NP + name, cu); col.objects.link(k); k.matrix_world = o.matrix_world.copy(); npt += len(P)
ns = len(d.splines); bpy.data.objects.remove(o)
print("DESUDATE: %d linii din %s -> %d obiecte separate (%d puncte, toate la locul lor); cu nume regasit %d, fara nume %d" % (ns, N, ns, npt, ns - nm_, nm_))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
