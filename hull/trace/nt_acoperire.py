# Coverage of every reference piece by a block: share of its surface samples within TOL m of the block's meshes. Usage: blender -b f --python nt_acoperire.py -- <out.txt> <COL> <xoff> [TOL ...]
import bpy, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, COL, XO = a[0], a[1], float(a[2]); TL = [float(t) for t in a[3:]] or [5, 20]; bpy.context.scene.frame_set(60)
tr = []; dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.collections[COL].objects:
    if o.type != "MESH" or "_lama_" in o.name or "_usa_" in o.name: continue
    M = o.matrix_world; tr.append(BVHTree.FromPolygons([M @ v.co - Vector((XO, 0, 0)) for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons]))
out = open(OUT, "w")
for o in sorted(bpy.data.collections["REFERINTA"].objects, key=lambda q: q.name):
    if o.type != "MESH": continue
    M = o.matrix_world; vs = o.data.vertices; st = max(1, len(vs) // 150); N = 0; C = [0] * len(TL); mx = max(TL)
    for i in range(0, len(vs), st):
        p = M @ vs[i].co; N += 1; d = 1e9
        for t in tr:
            r = t.find_nearest(p, min(d, mx))
            if r[3] is not None: d = min(d, r[3])
        for k, tl in enumerate(TL):
            if d < tl: C[k] += 1
    bb = [M @ Vector(b) for b in o.bound_box]
    out.write("%s|%d|%s|x%.0f..%.0f y%.0f..%.0f z%.0f..%.0f\n" % (o.name, len(o.data.polygons), "|".join("%.0f" % (100 * c / max(N, 1)) for c in C), min(b.x for b in bb), max(b.x for b in bb), min(b.y for b in bb), max(b.y for b in bb), min(b.z for b in bb), max(b.z for b in bb)))
