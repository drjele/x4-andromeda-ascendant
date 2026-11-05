# Every reference mesh (world coords) to one npz: <safe name>_v / _f, triangulated, plus materials per face _m and the names list.
# Usage: blender -b <scene> --python nt_ref_export.py -- <out.npz>
import bpy, sys, numpy as np
OUT = sys.argv[sys.argv.index("--") + 1]; D = {}; names = []
for o in sorted(bpy.data.collections["REFERINTA"].objects, key=lambda q: q.name):
    if o.type != "MESH": continue
    m = o.data; m.calc_loop_triangles(); V = np.empty(3 * len(m.vertices)); m.vertices.foreach_get("co", V); V = V.reshape(-1, 3); M = np.array(o.matrix_world); V = V @ M[:3, :3].T + M[:3, 3]
    F = np.empty(3 * len(m.loop_triangles), int); m.loop_triangles.foreach_get("vertices", F); mi = np.empty(len(m.loop_triangles), int); m.loop_triangles.foreach_get("material_index", mi)
    k = o.name.replace(" ", "_"); names.append(o.name); D[k + "__v"] = V.astype(np.float32); D[k + "__f"] = F.reshape(-1, 3).astype(np.int32); D[k + "__m"] = np.array([(m.materials[i].name if m.materials[i] else "") for i in range(len(m.materials))])[mi] if len(m.materials) else np.array([])
np.savez_compressed(OUT, names=np.array(names), **D); print("EXPORT", len(names))
