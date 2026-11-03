# Fills the small holes left by curata_compartimente.py (asked: two darker stripes on at_PS_carena at the fixed strip between the
# two blade sets, small defects on at_brat_fata_S in the compartments). It dropped a face when only its CENTRE lay on another
# piece, so slivers (carena side, arm walls / ceilings) went and the other piece's coplanar face shows through instead - with
# its own texture: the darker stripes / ticks. Per small boundary loop (<= NMAX edges, < PMAX m) of a piece A: the faces lying in
# the hole's plane around it (radius = hole size + RAD) are summed per piece; if A owns more of that plane than any other piece,
# the hole is filled in A (winding / smooth / material / UV from the neighbours) and the other pieces' faces lying on the new
# faces (all corners within COV) are removed; otherwise the hole is meant (the other piece owns the surface) and is left.
# Usage: blender -b <scene> --python umple_gauri.py -- <out.blend> <obj,obj,...>   env NMAX=12 PMAX=120 COV=.03 RAD=10
import bpy, bmesh, sys, os, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree as BV
a = sys.argv[sys.argv.index("--") + 1:]; OUT, NAMES = a[0], a[1].split(",")
E = lambda k, d: float(os.environ.get(k, d)); NMAX, PMAX, COV, RAD = int(E("NMAX", 12)), E("PMAX", 120), E("COV", .03), E("RAD", 10)
sc = bpy.context.scene; sc.frame_set(1)
STATIC = [o for o in bpy.data.collections["ATELIER_LAME"].objects if o.type == "MESH" and not o.name.startswith(("at_lama_", "at_spinare_", "at_usa_"))]
assert all(o.matrix_world == STATIC[0].matrix_world for o in STATIC)       # all hull pieces share the atelier offset: local coords comparable
BM = {}
for o in STATIC: b = bmesh.new(); b.from_mesh(o.data); b.faces.ensure_lookup_table(); BM[o.name] = b
def loops(bm):
    bd = [e for e in bm.edges if e.is_boundary]; adj = {}
    for e in bd:
        for v in e.verts: adj.setdefault(v, []).append(e)
    seen, out = set(), []
    for e0 in bd:
        if e0 in seen: continue
        L = []; st = [e0]; seen.add(e0)
        while st:
            e = st.pop(); L.append(e)
            for v in e.verts:
                for f in adj[v]:
                    if f not in seen: seen.add(f); st.append(f)
        out.append(L)
    return out
def newell(vs_ordered):
    n = Vector()
    for i, p in enumerate(vs_ordered):
        q = vs_ordered[(i + 1) % len(vs_ordered)]; n += Vector(((p.y - q.y) * (p.z + q.z), (p.z - q.z) * (p.x + q.x), (p.x - q.x) * (p.y + q.y)))
    return n.normalized()
def order(L):
    adj = {}
    for e in L:
        for v in e.verts: adj.setdefault(v, []).append(e)
    v = L[0].verts[0]; e = L[0]; out = [v]
    for _ in range(len(L) - 1):
        v = e.other_vert(v); out.append(v); e = next(x for x in adj[v] if x is not e)
    return [p.co.copy() for p in out]
def plane_area(b, c, n, r):                                               # area of b's faces lying in the plane (c, n) within r of c
    s = 0.0
    for f in b.faces:
        p = f.calc_center_median()
        if (p - c).length < r and abs(f.normal.dot(n)) > .98 and all(abs((v.co - c).dot(n)) < COV for v in f.verts): s += f.calc_area()
    return s
TREE = {k: BV.FromBMesh(b) for k, b in BM.items()}
for nm in NAMES:
    bm = BM[nm]; uvl = bm.loops.layers.uv.active; nf = nskip = 0
    for L in loops(bm):
        per = sum(e.calc_length() for e in L)
        if len(L) > NMAX or per > PMAX: continue
        P = order(L); c = sum(P, Vector()) / len(P); n = newell(P); size = max((p - c).length for p in P); r = size + RAD
        flat = max(abs((p - c).dot(n)) for p in P)
        own = {k: plane_area(b, c, n, r) for k, b in BM.items() if k == nm or (lambda q: q[0] is not None and q[3] < r)(TREE[k].find_nearest(c))}
        best = max(own, key=own.get)
        tag = ", ".join("%s %.0f" % (k[3:], v) for k, v in own.items() if v > 0)
        if best != nm:
            nskip += 1; print("GAURA %s lasata la %s (%d muchii, %.1f m): planul e al lui %s [%s]" % (nm, tuple(round(x, 1) for x in c), len(L), per, best, tag)); continue
        old = {e: e.link_faces[0] for e in L}
        res = bmesh.ops.contextual_create(bm, geom=L) if len(L) <= 4 else bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=L)
        new = [f for f in res.get("faces", []) + res.get("geom", []) if isinstance(f, bmesh.types.BMFace)]
        for f in new:
            e = next(x for x in f.edges if x in old); lf = next(l for l in f.loops if l.edge == e); lo = next(l for l in old[e].loops if l.edge == e)
            if lf.vert == lo.vert: f.normal_flip()
            f.smooth = old[e].smooth; f.material_index = old[e].material_index
            if uvl:
                for l in f.loops:
                    src = next((k for k in l.vert.link_loops if k.face not in new), None)
                    if src: l[uvl].uv = src[uvl].uv.copy()
        for f in new:
            f.normal_update()
            for e in f.edges:
                if len(e.link_faces) == 2: e.smooth = e.calc_face_angle(0) < math.radians(30)
        cut = 0
        for k, b in BM.items():                                          # the other pieces' faces lying on the filled faces go
            if k == nm: continue
            dead = [g for g in b.faces if (g.calc_center_median() - c).length < r and abs(g.normal.dot(n)) > .98
                    and all(abs((v.co - c).dot(n)) < COV for v in g.verts)
                    and all(any(bmesh.geometry.intersect_face_point(f, v.co) or (v.co - min((w.co for w in f.verts), key=lambda w: (w - v.co).length)).length < COV for f in new) for v in g.verts)]
            if dead: bmesh.ops.delete(b, geom=dead, context="FACES"); cut += len(dead); TREE[k] = BV.FromBMesh(b)
        nf += 1; print("GAURA %s umpluta la %s: %d muchii, %.1f m, plan %.2f m, %d fete noi, %d fete coplanare scoase din alte piese [%s]" % (nm, tuple(round(x, 1) for x in c), len(L), per, flat, len(new), cut, tag))
    TREE[nm] = BV.FromBMesh(bm); print("UMPLE %s: %d umplute, %d lasate" % (nm, nf, nskip))
for k, b in BM.items():
    me = bpy.data.objects[k].data; b.normal_update(); b.to_mesh(me); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
