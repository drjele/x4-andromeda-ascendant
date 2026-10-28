# The PS tube rings (ps_tube.py) as one mesh per side beside the ship (x + DX): quads between rings, the last ring closed
# into the tip, the first ring left open (the deck junction comes there); _D = mirror of _S. Collection PS_NOU.
# Usage: blender -b <in.blend> --python ps_tube_mesh.py -- <tub_ps.npz> <out.blend> <dx>
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; D = np.load(a[0]); OUT, DX = a[1], float(a[2])
X, tip = D["X"], D["tip"]; L, NA = X.shape[:2]
OPEN = np.isnan(tip).any()                                              # open at both ends: no tip
V = X.reshape(-1, 3) if OPEN else np.vstack([X.reshape(-1, 3), tip[None]])
F = [(k * NA + i, k * NA + (i + 1) % NA, (k + 1) * NA + (i + 1) % NA, (k + 1) * NA + i) for k in range(L - 1) for i in range(NA)]
if not OPEN: F += [((L - 1) * NA + i, (L - 1) * NA + (i + 1) % NA, L * NA) for i in range(NA)]
col = bpy.data.collections.get("PS_NOU") or bpy.data.collections.new("PS_NOU")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
mt = bpy.data.materials.get("brat_gri") or bpy.data.materials.new("brat_gri")
for s, nm in ((1, "ps_tub_S"), (-1, "ps_tub_D")):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm])
    W = V.copy(); W[:, 0] *= s; W[:, 0] += DX
    me = bpy.data.meshes.new(nm); me.from_pydata(W.tolist(), [], F if s > 0 else [f[::-1] for f in F]); me.materials.append(mt)
    for p in me.polygons: p.use_smooth = True
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bnd = sum(1 for e in bm.edges if e.is_boundary); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nm, me); col.objects.link(o)
    print("OBIECT %s: %d varfuri, %d fete, muchii libere %d (capetele deschise)" % (nm, len(me.vertices), len(me.polygons), bnd))
dj = np.gradient(X, axis=0); di = np.roll(X, -1, 1) - np.roll(X, 1, 1); nn = np.cross(di, dj); nn /= np.maximum(np.linalg.norm(nn, axis=2), 1e-9)[:, :, None]
turn = np.degrees(np.arccos(np.clip(np.sum(nn[1:] * nn[:-1], axis=2), -1, 1)))
print("rotire normala intre inele: max %.2f, p99 %.2f" % (turn.max(), np.percentile(turn, 99)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
