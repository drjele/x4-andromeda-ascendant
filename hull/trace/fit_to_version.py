# A frozen version with new vertex positions from a mesh npz (same parts, same vertex order): writes versions/<new>.blend.
# Usage: blender -b --python fit_to_version.py -- <source_version> <mesh.npz> <new_version>
import bpy, sys, json, numpy as np
from mathutils import Matrix
a = sys.argv[sys.argv.index("--") + 1:]; SRC, NPZ, NEW = a; D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{D}/body/parts.json")); Z = np.load(NPZ)
with bpy.data.libraries.load(f"{D}/versions/{SRC}.blend") as (src, dst): dst.collections = [src.collections[0]]
col = bpy.data.collections.new(NEW); n = 0
for o in dst.collections[0].objects:
    name = o.name[len(SRC) + 1:]; key = f"v|{P.get(name, ['?'])[0]}|{name}"
    c = o.copy(); c.data = o.data.copy(); c.name = f"{NEW}_{name}"; c.data.name = c.name; col.objects.link(c)
    if key in Z.files and len(Z[key]) == len(c.data.vertices):
        Mi = np.array(c.matrix_world.inverted()); w = Z[key].astype(np.float64); loc = w @ Mi[:3, :3].T + Mi[:3, 3]
        c.data.vertices.foreach_set("co", loc.ravel()); c.data.update(); n += 1
bpy.data.libraries.write(f"{D}/versions/{NEW}.blend", {col}, fake_user=True); print("VERSION", NEW, "parts moved", n, "of", len(col.objects))
