# Validation of the assembled pieces (asked: when everything is done, validate): per object of ASAMBLAT_NOU - free edges, non-manifold
# edges, degenerate faces, loose parts, dihedral angles (95 %, count > 60 deg), and the symmetry of every _S piece against its _D
# mirrored (max / mean distance of S vertices to the mirrored D set). Exports nothing; prints a table.
# Usage: blender -b <f.blend> --python valideaza_ansamblu.py
import bpy, numpy as np, bmesh
from mathutils.kdtree import KDTree
col = bpy.data.collections["ASAMBLAT_NOU"]; rows = []; verts = {}
for o in sorted(col.objects, key=lambda q: q.name):
    if o.type != "MESH": continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.edges.ensure_lookup_table()
    free = sum(1 for e in bm.edges if len(e.link_faces) == 1); nm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    deg = sum(1 for f in bm.faces if f.calc_area() < 1e-6)
    ang = np.degrees(np.array([e.calc_face_angle(0.0) for e in bm.edges if len(e.link_faces) == 2]))
    parts = len(bmesh.ops.find_doubles(bm, verts=bm.verts, dist=0.0)["targetmap"]) * 0
    seen = set(); comp = 0
    for v in bm.verts:
        if v.index in seen: continue
        comp += 1; st = [v]; seen.add(v.index)
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
    M = o.matrix_world; verts[o.name] = np.array([(M @ v.co)[:] for v in bm.verts]) + np.array([1600.0, 0, 0])
    rows.append((o.name, len(bm.faces), free, nm, deg, comp, np.percentile(ang, 95) if len(ang) else 0, int((ang > 60).sum())))
    bm.free()
print("VALID %-26s %8s %6s %6s %5s %5s %7s %6s" % ("piesa", "fete", "libere", "nemanf", "degen", "comp", "diedr95", ">60"))
for r in rows: print("VALID %-26s %8d %6d %6d %5d %5d %7.1f %6d" % r)
for n, V in verts.items():
    if not n.endswith("_S"): continue
    d = n[:-2] + "_D"
    if d not in verts: continue
    kd = KDTree(len(verts[d])); [kd.insert((-p[0], p[1], p[2]), i) for i, p in enumerate(verts[d])]; kd.balance()
    dist = np.array([kd.find(p)[2] for p in verts[n][::max(1, len(verts[n]) // 3000)]])
    print("SIMETRIE %-24s max %.2f, medie %.3f m" % (n[:-2], dist.max(), dist.mean()))
