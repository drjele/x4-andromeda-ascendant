# Surface samples of every mesh in the given collections (world coordinates, area-weighted, ~DENS points per m2, capped),
# one array per object, for drawing guide outlines (ghid_contur.py).
# Usage: blender -b <file.blend> --python ghid_export.py -- <out.npz> <collection1,collection2,...>
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; COLS = a[1].split(","); rng = np.random.default_rng(0); res = {}
for cn in COLS:
    for o in bpy.data.collections[cn].objects:
        F_ = [f for f in __import__("os").environ.get("GHID_NUME", "").split(";") if f]
        if F_ and not any(f in o.name for f in F_): continue
        if o.type != "MESH" or not o.data.polygons: continue
        me = o.data; me.calc_loop_triangles(); M = np.array(o.matrix_world)
        v = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", v); v = v.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        t = np.zeros(len(me.loop_triangles) * 3, int); me.loop_triangles.foreach_get("vertices", t); t = t.reshape(-1, 3)
        A, B, C = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]; ar = np.linalg.norm(np.cross(B - A, C - A), axis=1) / 2
        n = int(min(max(ar.sum() * 2, 2000), 600000)); i = rng.choice(len(t), n, p=ar / ar.sum()); r1, r2 = rng.random(n), rng.random(n); sw = r1 + r2 > 1; r1[sw], r2[sw] = 1 - r1[sw], 1 - r2[sw]
        res[o.name] = A[i] + (B[i] - A[i]) * r1[:, None] + (C[i] - A[i]) * r2[:, None]
np.savez(OUT, **res); print("EXPORT", len(res), "obiecte:", ", ".join(sorted(res)))
