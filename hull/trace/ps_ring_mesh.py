# A ring-built component (rings of points along its length, closed around) as one object per side: quads between rings,
# both ends closed with a fan to the ring's centre; _S as built, _D its mirror (x -> -x, faces reversed). Placed in ship
# coordinates (x + DX) then moved by the exploded offsets; the material taken from a reference piece; the reference-
# equivalent patches it replaces hidden. Collection PS_NOU_EXPLODAT.
# Usage: blender -b <file.blend> --python ps_ring_mesh.py -- <rings.npz> <out.blend> <dx> <name> <material_from> <offS> <offD> [hide,...]
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; D = np.load(a[0]); OUT, DX, NAME, MSRC = a[1], float(a[2]), a[3], a[4]
OFF = {"S": Vector([float(v) for v in a[5].split(",")]), "D": Vector([float(v) for v in a[6].split(",")])}; HIDE = a[7].split(";") if len(a) > 7 else []
X = D["X"]; K, M = X.shape[:2]
col = bpy.data.collections.get(os.environ.get("COLECTIE", "PS_NOU_EXPLODAT")) or bpy.data.collections.new(os.environ.get("COLECTIE", "PS_NOU_EXPLODAT"))
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
src = bpy.data.objects[MSRC]; mi = src.data.polygons[0].material_index; mat = src.material_slots[mi].material
for side, sg in (("S", 1), ("D", -1)):
    V = X.reshape(-1, 3).copy(); V[:, 0] *= sg; V = np.vstack([V, X[0].mean(0) * [sg, 1, 1], X[-1].mean(0) * [sg, 1, 1]]); V[:, 0] += DX
    F = [(k * M + i, k * M + (i + 1) % M, (k + 1) * M + (i + 1) % M, (k + 1) * M + i) for k in range(K - 1) for i in range(M)]
    F += [(K * M, (i + 1) % M, i) for i in range(M)] + [(K * M + 1, (K - 1) * M + i, (K - 1) * M + (i + 1) % M) for i in range(M)]
    if sg < 0: F = [f[::-1] for f in F]
    nm = "%s_%s" % (NAME, side)
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm])
    me = bpy.data.meshes.new(nm); me.from_pydata(V.tolist(), [], F); me.materials.append(mat)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bnd = sum(1 for e in bm.edges if e.is_boundary); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(nm, me); col.objects.link(o); o.location = OFF[side]
    print("OBIECT %s: %d varfuri, %d fete, muchii libere %d" % (nm, len(me.vertices), len(me.polygons), bnd))
for h in HIDE:
    o = bpy.data.objects.get(h)
    if o:
        o.hide_render = True
        try: o.hide_set(True)
        except RuntimeError: pass                                       # in an excluded collection
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
