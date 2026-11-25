# World triangles of the board's ships (block offset removed), one npz per collection: v, t, object index per triangle, names.
# Usage: blender -b <scene> --python corelare_export.py -- <out_dir> <collection>=<x_offset> ...
import bpy, sys, numpy as np
A = sys.argv[sys.argv.index("--") + 1:]
for s in A[1:]:
    c, off = s.split("="); V, T, O, N = [], [], [], []; b = 0
    for o in bpy.data.collections[c].all_objects:
        if o.type != "MESH": continue
        me = o.data; me.calc_loop_triangles(); M = np.array(o.matrix_world)
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); v = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]; v[:, 0] -= float(off)
        t = np.empty(len(me.loop_triangles) * 3, int); me.loop_triangles.foreach_get("vertices", t); t = t.reshape(-1, 3)
        V.append(v); T.append(t + b); O.append(np.full(len(t), len(N))); N.append(o.name); b += len(v)
    np.savez(f"{A[0]}/{c}.npz", v=np.vstack(V), t=np.vstack(T), o=np.concatenate(O), n=np.array(N)); print("EXP", c, len(N), sum(map(len, T)))
