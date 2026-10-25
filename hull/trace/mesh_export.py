# Export a frozen version's parts (and grannyte's original mesh) as world triangles for overlay_check.py.
# Usage: blender -b --python mesh_export.py -- <version> <out.npz>
import bpy, sys, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; V, OUT = a; T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{T}/body/parts.json")); data = {}
def put(key, o):
    me = o.data; me.calc_loop_triangles(); M = np.array(o.matrix_world); v = np.array([x.co for x in me.vertices])
    data[f"v|{key}"] = (v @ M[:3, :3].T + M[:3, 3]).astype(np.float32); data[f"t|{key}"] = np.array([t.vertices for t in me.loop_triangles], np.int32)
with bpy.data.libraries.load(f"{T}/versions/{V}.blend") as (src, dst): dst.collections = [src.collections[0]]
for o in [o for c in bpy.data.collections for o in c.objects if o.name.startswith(V + "_")]:
    name = o.name[len(V) + 1:]; put(f"{P.get(name, ['?'])[0]}|{name}", o)
with bpy.data.libraries.load(f"{T}/vtop/v_scene.blend") as (src, dst): dst.objects = ["source"]
put("SRC|source", dst.objects[0]); np.savez_compressed(OUT, **data); print("EXPORT", V, len(data) // 2)
