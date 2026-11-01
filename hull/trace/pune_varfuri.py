# New vertex positions put into existing objects (same topology - e.g. a piece smoothed or moved onto a model), the object kept with
# its place, materials and links. Usage: blender -b <f.blend> --python pune_varfuri.py -- <out.blend> <npz> <object:key> ...
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, Z = a[0], np.load(a[1])
for spec in a[2:]:
    on, key = spec.split(":"); o = bpy.data.objects[on]; V = Z[key + "__v"]
    if len(o.data.vertices) != len(V): print("NEPOTRIVIT", on, len(o.data.vertices), len(V)); continue
    o.data.vertices.foreach_set("co", V.astype(np.float32).ravel()); o.data.update(); print("PUS", on, len(V))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
