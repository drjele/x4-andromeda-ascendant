# The graph of the red nacelle's ribs: on every copied rib its 3 corners (its section is a triangle: the point farthest
# from the centre, the point farthest from that one, the point farthest from the line through both), matched from rib to
# rib (the corner order kept by nearest position in the rib's own plane), and the matching corners joined rib to rib: 3
# rails along the band. Drawn beside the untouched reference (DX) with the copied ribs: rails as thin tubes, corners as small
# spheres (colour per rail). The corners are saved (JSON) for filling in the new ribs once confirmed. One side, mirrored.
# Usage: blender -b <ship.blend> --python rib_graph.py -- <out.blend> <corners.json> <dx>
import bpy, bmesh, sys, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, CJ, DX = a[0], a[1], float(a[2]); sc = bpy.context.scene
imgs = {}
def red_share(o):
    me = o.data
    if not me.materials or not me.uv_layers: return 0
    uv = me.uv_layers.active.data; n = 0
    for p in me.polygons:
        m = me.materials[p.material_index]; tl = [x for x in m.node_tree.nodes if x.type == "TEX_IMAGE"] if m and m.node_tree else []
        if not tl or not tl[0].image: return 0
        t = tl[0].image
        if t.name not in imgs: imgs[t.name] = np.array(t.pixels[:], np.float32).reshape(t.size[1], t.size[0], t.channels)
        A = imgs[t.name]; u, v = uv[p.loop_start].uv; c = A[int((v % 1) * (A.shape[0] - 1)), int((u % 1) * (A.shape[1] - 1)), :3]
        n += c[0] > 0.25 and c[0] > 1.8 * max(c[1], c[2])
    return n / len(me.polygons)
def inbk(o): return any(c.name == "BACKUP_sterse" for c in o.users_collection)
ribs = [o for o in sc.objects if o.type == "MESH" and not inbk(o) and o.name.endswith("_S") and len(o.data.polygons) < 400 and red_share(o) > 0.95]
data = [(o, np.array([o.matrix_world @ v.co for v in o.data.vertices])) for o in ribs]
C = np.array([P.mean(0) for _, P in data]); order = [int(np.argmax(C[:, 1]))]; left = set(range(len(C))) - set(order)
while left:
    j = min(left, key=lambda i: np.linalg.norm(C[i] - C[order[-1]])); order.append(j); left.remove(j)
data = [data[i] for i in order]; C = C[order]
T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
def corners(P, c, t):
    q = P - c; q2 = q - np.outer(q @ t, t)                                 # the rib flattened onto its plane
    A = int(np.argmax(np.linalg.norm(q2, axis=1))); B = int(np.argmax(np.linalg.norm(q2 - q2[A], axis=1)))
    ab = q2[B] - q2[A]; ab /= np.linalg.norm(ab); off = (q2 - q2[A]) - np.outer((q2 - q2[A]) @ ab, ab); Cc = int(np.argmax(np.linalg.norm(off, axis=1)))
    return np.array([P[A], P[B], P[Cc]])
K = []
for k, (o, P) in enumerate(data):
    cs = corners(P, C[k], T[k])
    if K:                                                                   # same order as the previous rib (nearest match)
        prev = K[-1] - C[k - 1]; cur = cs - C[k]; import itertools
        best = min(itertools.permutations(range(3)), key=lambda pm: sum(np.linalg.norm(cur[pm[i]] - prev[i]) for i in range(3))); cs = cs[list(best)]
    K.append(cs)
K = np.array(K)                                                             # (ribs, 3, xyz)
json.dump({"corners": K.tolist(), "centres": C.tolist()}, open(CJ, "w"))
out = bpy.data.collections.new("GRAF_NERVURI"); sc.collection.children.link(out)
cols = [(0.1, 0.9, 0.2, 1), (0.1, 0.5, 1.0, 1), (1.0, 0.85, 0.1, 1)]
def mat(n, c): m = bpy.data.materials.new(n); m.diffuse_color = c; m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = c; return m
mats = [mat("sina_%d" % i, c) for i, c in enumerate(cols)]; rmat = mat("nervura_copiata", (0.35, 0.03, 0.04, 1))
for side in (1, -1):
    for k, (o, P) in enumerate(data):                                       # the copied ribs
        V = P.copy(); V[:, 0] *= side; me = bpy.data.meshes.new("n"); f = [tuple(p.vertices)[::side] for p in o.data.polygons]
        me.from_pydata((V + [DX, 0, 0]).tolist(), [], f); me.materials.append(rmat); ob = bpy.data.objects.new("nervura_copiata_%02d%s" % (k, "_S" if side > 0 else "_D"), me); out.objects.link(ob)
    for i in range(3):                                                      # the rails
        cu = bpy.data.curves.new("sina", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.2; sp = cu.splines.new("POLY"); sp.points.add(len(K) - 1)
        for k in range(len(K)): p = K[k, i] * [side, 1, 1] + [DX, 0, 0]; sp.points[k].co = (*p, 1)
        ob = bpy.data.objects.new("sina_%d%s" % (i + 1, "_S" if side > 0 else "_D"), cu); cu.materials.append(mats[i]); out.objects.link(ob)
        for k in range(len(K)):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=2.5, location=tuple(K[k, i] * [side, 1, 1] + [DX, 0, 0])); s_ = bpy.context.active_object
            for c in s_.users_collection: c.objects.unlink(s_)
            out.objects.link(s_); s_.data.materials.append(mats[i]); s_.name = "varf_%d_%02d" % (i + 1, k)
print("GRAF: %d nervuri, 3 sine; lungimi sine m: %s" % (len(K), " ".join("%.0f" % np.sum(np.linalg.norm(np.diff(K[:, i], axis=0), axis=1)) for i in range(3))))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
