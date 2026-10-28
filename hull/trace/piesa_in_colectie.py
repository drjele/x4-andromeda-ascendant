# A built piece added as its own object (pieces stay separate for the export) to one or more collections, each copy at
# its x offset: mesh from an npz (ship coordinates, centred), material, UVs from above, smooth shading under 25 degrees.
# Usage: blender -b <f.blend> --python piesa_in_colectie.py -- <out.blend> <piece.npz> <material> <name:collection:x> ...
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, Z, MAT = a[0], np.load(a[1]), a[2]
v = Z["v"].astype(float); me = bpy.data.meshes.new(a[3].split(":")[0]); me.from_pydata(v.tolist(), [], Z["f"].tolist()); me.validate()
me.materials.append(bpy.data.materials[MAT]); L = me.uv_layers.new(name="UVMap")
li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", li); L.data.foreach_set("uv", (v[li][:, :2] / 256.0).ravel())
for spec in a[3:]:
    nm, col, x = spec.split(":")
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm])
    o = bpy.data.objects.new(nm, me); bpy.data.collections[col].objects.link(o); o.location.x = float(x); o.color = (0.75, 0.75, 0.78, 1)
    for s in bpy.context.selected_objects: s.select_set(False)
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.shade_smooth_by_angle(angle=0.436); o.select_set(False)
    print("PIESA %s in %s la x %s: %d fete" % (nm, col, x, len(me.polygons)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
