# A rebuilt piece put next to the original's copies (ORIGINAL_ANALIZA) for comparison: verts / faces from an npz (ship
# coordinates, centred) placed at x = XP, smooth shaded, the given material, UVs projected from above; checks it is closed.
# Usage: blender -b <f.blend> --python piesa_langa.py -- <out.blend> <name> <piece.npz> <xp> [material]
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, NAME, Z, XP = a[0], a[1], np.load(a[2]), float(a[3]); MAT = a[4] if len(a) > 4 else "Material_8"
col = bpy.data.collections["ORIGINAL_ANALIZA"]
if NAME in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[NAME])
v = Z["v"].astype(float); me = bpy.data.meshes.new(NAME); me.from_pydata(v.tolist(), [], Z["f"].tolist()); me.validate()
b = bmesh.new(); b.from_mesh(me); fb = sum(1 for e in b.edges if e.is_boundary); nm = sum(1 for e in b.edges if not e.is_manifold); b.free()
for p in me.polygons: p.use_smooth = True
me.materials.append(bpy.data.materials[MAT]); L = me.uv_layers.new(name="UVMap")
li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", li); L.data.foreach_set("uv", (v[li][:, :2] / 256.0).ravel())
o = bpy.data.objects.new(NAME, me); col.objects.link(o); o.location.x = XP
print("PIESA %s la x %.0f: %d fete, muchii libere %d, nemanifold %d" % (NAME, XP, len(me.polygons), fb, nm))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
