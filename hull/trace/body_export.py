# Export the body-group parts of a frozen version (world vertices) for body_fit.py.
# Usage: blender -b --python body_export.py -- <version> <out.npz>
import bpy, sys, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; V, OUT = a; T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{T}/body/parts.json")); data = {}
with bpy.data.libraries.load(f"{T}/versions/{V}.blend") as (src, dst): dst.collections = [src.collections[0]]
for o in [o for c in bpy.data.collections for o in c.objects if o.name.startswith(V + "_")]:
    name = o.name.split("_", 1)[1]; label = P.get(name, ["?"])[0]
    if not label.startswith("C"): continue
    M = np.array(o.matrix_world); v = np.array([x.co for x in o.data.vertices]); data[name] = (v @ M[:3, :3].T + M[:3, 3]).astype(np.float32)
np.savez_compressed(OUT, **data); print("BODY", sorted(data))
