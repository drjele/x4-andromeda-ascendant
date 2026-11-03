# UVs from above for pieces rebuilt without them (asked: clean surfaces pass - the PS frame rebuilt from its guide lost its UVMap):
# per object a UVMap = (x, y) / 256 of the vertex in ship coordinates, as adauga_decor.py does for the decorations.
# Usage: blender -b <in.blend> --python uv_de_sus.py -- <out.blend> <obj,...>
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
for n in a[1].split(","):
    me = bpy.data.objects[n].data
    for u in list(me.uv_layers): me.uv_layers.remove(u)
    uv = me.uv_layers.new(name="UVMap"); V = np.array([v.co[:] for v in me.vertices]); li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", li)
    uv.data.foreach_set("uv", (V[li][:, :2] / 256.0).ravel().astype(np.float32)); print("UV", n, len(me.loops))
bpy.ops.wm.save_as_mainfile(filepath=a[0])
