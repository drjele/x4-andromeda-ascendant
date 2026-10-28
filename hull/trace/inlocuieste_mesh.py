# A piece's mesh replaced in place for every object that shows it (the scene's piece and its linked separate copy): new mesh
# from an npz (ship coordinates, centred), same material, UVs from above, smooth shading under 25 degrees.
# Usage: blender -b <f.blend> --python inlocuieste_mesh.py -- <out.blend> <piece.npz> <object> [object ...]
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, Z, NAMES = a[0], np.load(a[1]), a[2:]
v = Z["v"].astype(float); me = bpy.data.meshes.new(NAMES[0]); me.from_pydata(v.tolist(), [], Z["f"].tolist()); me.validate()
old = bpy.data.objects[NAMES[0]].data
for m in old.materials: me.materials.append(m)
L = me.uv_layers.new(name="UVMap"); li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", li); L.data.foreach_set("uv", (v[li][:, :2] / 256.0).ravel())
for n in NAMES:
    o = bpy.data.objects[n]; o.data = me
    for s in bpy.context.selected_objects: s.select_set(False)
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.shade_smooth_by_angle(angle=0.436); o.select_set(False)
    print("INLOCUIT %s: %d fete" % (n, len(me.polygons)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
