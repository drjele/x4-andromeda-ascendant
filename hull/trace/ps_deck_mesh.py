# The PS deck with its rear junction (ps_deck.py) as one surface beside the ship (x + DX). Per section, one half is a
# closed loop: the top from the inner wall out to the rounded edge, the bottom back, then the inner wall (a half-ellipse
# bulging DEPTH into the U's gap; flat in x = 0 on the deck). The other half is its mirror. On the deck the two walls lie
# in the plane x = 0, inside the solid: those faces are removed and the halves welded there, so the deck is one closed
# surface that opens in a U into the two arms. The nose rows collapse into the tip (triangle fan); the YEND end stays
# open for the tubes. Collection PS_NOU, one _C object.
# Usage: blender -b <in.blend> --python ps_deck_mesh.py -- <punte.npz> <out.blend> <dx>
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; D = np.load(a[0]); OUT, DX = a[1], float(a[2])
ys, s, E, X0, DEP, T, B = D["ys"], D["s"], D["edge"], D["x0"], D["depth"], D["top"], D["bot"]; K, M = T.shape; NI = 16
loops = []
for k in range(K):
    x = X0[k] + s * (E[k] - X0[k]); y = np.full(M, ys[k])
    top = np.stack([x, y, T[k]], 1); bot = np.stack([x, y, B[k]], 1)[::-1][1:]          # bottom: edge -> inner, edge shared
    th = np.linspace(-np.pi / 2, np.pi / 2, NI + 2)[1:-1]; mid, hh = (T[k, 0] + B[k, 0]) / 2, (T[k, 0] - B[k, 0]) / 2
    wall = np.stack([X0[k] - DEP[k] * np.cos(th), np.full(NI, ys[k]), mid + hh * np.sin(th)], 1)   # bottom -> top
    loops.append(np.vstack([top, bot[:-1], [bot[-1]], wall]))
L = np.array(loops); N = L.shape[1]
TIP = np.ptp(L[-1], 0).max() < 0.01; Kq = K - 1 if TIP else K
verts, faces = [], []
for side in (-1, 1):                                                    # _S half (x < 0) and its mirror
    V = L[:Kq].copy(); V[..., 0] *= side; base = len(verts); verts += V.reshape(-1, 3).tolist()
    F = [(base + k * N + i, base + (k + 1) * N + i, base + (k + 1) * N + (i + 1) % N, base + k * N + (i + 1) % N) for k in range(Kq - 1) for i in range(N)]
    if TIP: verts.append([0.0, ys[-1], L[-1, 0, 2]]); F += [(base + (Kq - 1) * N + i, len(verts) - 1, base + (Kq - 1) * N + (i + 1) % N) for i in range(N)]
    faces += F if side < 0 else [f[::-1] for f in F]
V = np.array(verts); V[:, 0] += DX
name = "ps_punte"
if name in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[name])
me = bpy.data.meshes.new(name); me.from_pydata(V.tolist(), [], faces)
bm = bmesh.new(); bm.from_mesh(me)
inner = [f for f in bm.faces if all(abs(v.co.x - DX) < 1e-4 for v in f.verts)]   # the two walls inside the deck (x = 0)
bmesh.ops.delete(bm, geom=inner, context="FACES")
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01); bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.01)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS"); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bnd = sum(1 for e in bm.edges if e.is_boundary); nm = sum(1 for e in bm.edges if len(e.link_faces) > 2); bm.to_mesh(me); bm.free()
mt = bpy.data.materials.get("brat_gri") or bpy.data.materials.new("brat_gri"); me.materials.append(mt)
for p in me.polygons: p.use_smooth = True
col = bpy.data.collections.get("PS_NOU") or bpy.data.collections.new("PS_NOU")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
o = bpy.data.objects.new(name, me); col.objects.link(o)
Vw = np.array([v.co for v in me.vertices]); Mr = Vw.copy(); Mr[:, 0] = 2 * DX - Mr[:, 0]
from mathutils import kdtree
kd = kdtree.KDTree(len(Vw)); [kd.insert(v, i) for i, v in enumerate(Vw)]; kd.balance()
sym = max(kd.find(p)[2] for p in Mr[::7])
print("OBIECT %s: %d varfuri, %d fete (%d fete interioare scoase), muchii libere %d (capetele spre brate), nemanifold %d, simetrie max %.4f m" % (name, len(me.vertices), len(me.polygons), len(inner), bnd, nm, sym))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
