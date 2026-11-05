# Do the new pieces touch the ship? For each new D piece (or central): distance from its surface samples to any OTHER piece of NAVA_TERMINATA (rest pose). Floats = nearest > TOL m. Usage: blender -b f --python nt_plutitoare.py -- <out.txt>
import bpy, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree as BV
OUT = sys.argv[sys.argv.index("--") + 1]; NT = bpy.data.collections["NAVA_TERMINATA"]; A = {"nt_" + o.name[3:] for o in bpy.data.collections["ASAMBLAT_NOU"].objects}; bpy.context.scene.frame_set(1)
obs = [o for o in NT.objects if o.type == "MESH"]; TR = {}
for o in obs: W = o.matrix_world; TR[o.name] = BV.FromPolygons([W @ v.co for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons])
rows = []
for o in obs:
    if o.name in A or o.name.endswith("_S"): continue
    W = o.matrix_world; vs = o.data.vertices; st = max(1, len(vs) // 200); best = 1e9
    for i in range(0, len(vs), st):
        p = W @ vs[i].co
        for n, t in TR.items():
            if n == o.name: continue
            r = t.find_nearest(p, min(best, 200))
            if r[3] is not None and r[3] < best: best = r[3]
        if best < 0.5: break
    rows.append((best, o.name, o.get("metoda", "")))
rows.sort(reverse=True); open(OUT, "w").write("\n".join("%.1f %s %s" % r for r in rows)); print("PLUT", len(rows), "peste 3 m:", sum(r[0] > 3 for r in rows), rows[:8])
