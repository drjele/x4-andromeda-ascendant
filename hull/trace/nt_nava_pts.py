# Validated ship's static pieces as points (ship coordinates, D side too). Usage: blender -b f --python nt_nava_pts.py -- <out.npz>
import bpy, sys, numpy as np
P = []; bpy.context.scene.frame_set(60)
for o in bpy.data.collections["ASAMBLAT_NOU"].objects:
    if o.type != "MESH" or "_lama_" in o.name or "_usa_" in o.name: continue
    V = np.empty(3 * len(o.data.vertices)); o.data.vertices.foreach_get("co", V); V = V.reshape(-1, 3); M = np.array(o.matrix_world); P.append(V @ M[:3, :3].T + M[:3, 3] + [2400, 0, 0])
np.savez(sys.argv[sys.argv.index("--") + 1], p=np.vstack(P).astype(np.float32))
