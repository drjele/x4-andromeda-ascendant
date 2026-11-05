# Validated pieces with no guides on the board, as ship-coordinate meshes (rest pose, frame 1). Usage: blender -b f --python nt_piese_val_export.py -- <out.npz>
import bpy, sys, numpy as np
HAS = ("brat_fata", "brat_spate", "nacela", "ureche_", "PS_carena", "PS_rama", "capac", "urechiusa")
D = {}; bpy.context.scene.frame_set(1)
for o in bpy.data.collections["ASAMBLAT_NOU"].objects:
    n = o.name[3:]
    if o.type != "MESH" or n == "PS" or any(h in n for h in HAS): continue
    m = o.data; m.calc_loop_triangles(); V = np.empty(3 * len(m.vertices)); m.vertices.foreach_get("co", V); V = V.reshape(-1, 3); M = np.array(o.matrix_world); V = V @ M[:3, :3].T + M[:3, 3] + [2400, 0, 0]
    F = np.empty(3 * len(m.loop_triangles), int); m.loop_triangles.foreach_get("vertices", F); D[n + "__v"] = V.astype(np.float32); D[n + "__f"] = F.reshape(-1, 3).astype(np.int32); print("VAL", n, len(F) // 3)
np.savez(sys.argv[sys.argv.index("--") + 1], **D)
