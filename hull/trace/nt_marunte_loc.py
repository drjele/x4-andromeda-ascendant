# Which bodies of the mixed scraps stand in the way of the blades / doors (asked: validated pieces never change, the new piece gives way): every animation frame step, triangle overlaps of the moving S pieces against nt_marunte_S; the touched loose bodies' centres (ship coordinates) listed. Usage: blender -b f --python nt_marunte_loc.py -- <out.npz>
import bpy, sys, numpy as np, bmesh
from mathutils.bvhtree import BVHTree as BV
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; M = bpy.data.objects["nt_marunte_S"]; dg = bpy.context.evaluated_depsgraph_get()
me = M.data; me.calc_loop_triangles(); Mw = M.matrix_world; tb = BV.FromPolygons([Mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
parent = list(range(len(me.vertices)))
def fnd(a):
    while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
    return a
for e in me.edges:
    a, b = fnd(e.vertices[0]), fnd(e.vertices[1])
    if a != b: parent[a] = b
hit = set(); mov = [o for o in bpy.data.collections["NAVA_TERMINATA"].objects if o.type == "MESH" and o.name.endswith("_S") and o.name.startswith(("nt_lama_", "nt_usa_fata", "nt_usa_spate", "nt_spinare_", "nt_usa_carena"))]
for f in sorted(set(list(range(1, 170, 3)))):
    sc.frame_set(f); dg.update()
    for o in mov:
        e = o.evaluated_get(dg); m = e.to_mesh(); W = o.matrix_world; t = BV.FromPolygons([W @ v.co for v in m.vertices], [tuple(p.vertices) for p in m.polygons]); e.to_mesh_clear()
        for _, b in t.overlap(tb):
            hit.add(fnd(me.polygons[b].vertices[0]))
P = np.empty(3 * len(me.vertices)); me.vertices.foreach_get("co", P); P = P.reshape(-1, 3); lab = np.array([fnd(i) for i in range(len(P))])
np.savez(OUT, lab=lab, hit=np.array(sorted(hit))); print("LOC corpuri lovite:", len(hit), "din", len(set(lab.tolist())), "varfuri lovite", int(np.isin(lab, list(hit)).sum()), "din", len(lab))
