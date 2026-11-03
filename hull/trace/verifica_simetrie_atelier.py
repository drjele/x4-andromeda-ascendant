# Left / right symmetry of the animated workshop (asked: keep symmetry; left and right blades did not fold alike): for every
# <name>_S object in ATELIER_LAME with a <name>_D partner, at every K-th frame, the S object's evaluated vertices mirrored about the
# workshop's x (XB) vs the D object's (nearest-vertex distance, max) - prints the worst pairs. Usage: ... -- [XB=-7000] ; env K=6
import bpy, sys, os, numpy as np
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []; XB = float(a[0]) if a else -7000.0; K = int(os.environ.get("K", 6))
sc = bpy.context.scene; col = bpy.data.collections["ATELIER_LAME"]
pairs = [(o, col.objects.get(o.name[:-2] + "_D")) for o in col.objects if o.name.endswith("_S") and col.objects.get(o.name[:-2] + "_D") and o.type == "MESH"]
def ev(o):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh(); P = np.array([o.matrix_world @ v.co for v in m.vertices]); oe.to_mesh_clear(); return P
worst = {}
for fr in range(1, sc.frame_end + 1, K):
    sc.frame_set(fr)
    for s_, d_ in pairs:
        if not (s_.animation_data or (s_.data.shape_keys and s_.data.shape_keys.animation_data)) and fr > 1: continue
        P, Q = ev(s_), ev(d_); P[:, 0] = 2 * XB - P[:, 0]; t = KDTree(len(Q))
        for i, q in enumerate(Q): t.insert(q, i)
        t.balance(); d = max(t.find(p)[2] for p in P[::max(1, len(P) // 2000)])
        if d > worst.get(s_.name, (0, 0))[0]: worst[s_.name] = (d, fr)
bad = {k: v for k, v in worst.items() if v[0] > .05}
print("SIMETRIE: %d perechi S/D verificate; %s" % (len(pairs), "toate oglindite exact (< 5 cm)" if not bad else "; ".join("%s %.2f m (cadrul %d)" % (k, *v) for k, v in sorted(bad.items(), key=lambda x: -x[1][0])[:10])))
