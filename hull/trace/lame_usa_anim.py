# Tram-door blades animated in the workshop (asked: down out from under the front arm, then slide forward and turn into place, no
# blade crossing another): per blade the deployed rows -> closed lying-V piece at_lama_<nr>_S / _D (origin on the deployed blade's
# centroid c); keyframes: frame 1 stowed (rotation R, location R c + t), frame FD the same dropped DZ, frame F deployed (identity at c);
# back in reverse to 2F. D = the mirror (S M S). Then every frame step K: triangle pairs shared between blades (should be 0).
# DROP=same: every blade dropped by the largest drop (the stack moves down whole); STAG=n: blade k starts its move n*k frames later
# (order = the tags' order) - the paths do not cross. At frame F also: where the blades touch, and whether that spot is hidden.
# Usage: blender -b <in.blend> --python lame_usa_anim.py -- <out.blend> <piese dir> <ver> <tag,...> ; env XB=-7000 F=60 FD=20 K=5
import bpy, bmesh, sys, os, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PD, VER, TAGS = a[0], a[1], a[2], a[3].split(","); E = lambda k, d: float(os.environ.get(k, d))
XB, F, FD, K = E("XB", -7000), int(E("F", 60)), int(E("FD", 20)), int(E("K", 5)); STAG = int(E("STAG", 0)); SAME = os.environ.get("DROP") == "same"
col = bpy.data.collections["ATELIER_LAME"]; mat = bpy.data.materials.get("lame_rosu"); sc = bpy.context.scene
for n in [o.name for o in col.objects if o.name.startswith("at_lama_")]: bpy.data.objects.remove(bpy.data.objects[n])
def build(name, R, mirror):
    bm = bmesh.new(); P = R * ([-1, 1, 1] if mirror else 1); n, m = P.shape[:2]
    vv = [[bm.verts.new(tuple(P[i, j])) for j in range(m)] for i in range(n)]
    for i in range(n - 1):
        for j in range(m):
            q = [vv[i][j], vv[i][(j + 1) % m], vv[i + 1][(j + 1) % m], vv[i + 1][j]]; bm.faces.new(q[::-1] if mirror else q)
    for row, rev in ((vv[0], not mirror), (vv[-1], mirror)):
        f = bm.faces.new(row[::-1] if rev else row); bmesh.ops.triangulate(bm, faces=[f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    at = me.attributes.new("sharp_edge", "BOOLEAN", "EDGE"); Kc = m // 3
    for e in me.edges:
        i0, i1 = sorted(e.vertices); at.data[e.index].value = (i1 - i0 == m and i0 % m in (0, Kc, 2 * Kc))
    for p in me.polygons: p.use_smooth = True
    if mat: me.materials.append(mat)
    return me
S = np.diag([-1, 1, 1, 1.])
DMAX = max(float(np.load(os.path.join(PD, "ghid_lama_%s_%s_usa.npz" % (t_, VER)))["drop"]) for t_ in TAGS)
for ki, tag in enumerate(TAGS):
    G = np.load(os.path.join(PD, "ghid_lama_%s_%s.npz" % (tag, VER))); U = np.load(os.path.join(PD, "ghid_lama_%s_%s_usa.npz" % (tag, VER)))
    Ms, Mj, Va = G["lama_margine_sus"], G["lama_margine_jos"], G["lama_varf"]; f_ = np.linspace(0, 1, 7)[:-1]
    R = np.stack([Ms + (Va - Ms) * t for t in f_] + [Va + (Mj - Va) * t for t in f_] + [Mj + (Ms - Mj) * t for t in f_], axis=1)
    c = R.reshape(-1, 3).mean(0); Mst = U["stowed"]; drop = DMAX if SAME else float(U["drop"]); f0 = FD + STAG * ki
    for sd, mir in (("S", False), ("D", True)):
        cc = c * ([-1, 1, 1] if mir else 1); Mx = S @ Mst @ S if mir else Mst
        me = build("at_lama_%s_%s" % (tag, sd), R, mir); me.transform(Matrix.Translation(Vector((-cc).tolist())))
        o = bpy.data.objects.new("at_lama_%s_%s" % (tag, sd), me); col.objects.link(o); o.rotation_mode = "QUATERNION"
        Rq = Matrix(Mx[:3, :3].tolist()).to_quaternion(); Ls = Vector((Mx[:3, :3] @ cc + Mx[:3, 3]).tolist()) + Vector((XB, 0, 0)); Ld = Vector(cc.tolist()) + Vector((XB, 0, 0))
        q0 = Matrix.Identity(3).to_quaternion()
        if Rq.dot(q0) < 0: Rq.negate()
        for fr, q, loc in ((1, Rq, Ls), (FD, Rq, Ls - Vector((0, 0, drop))), (f0, Rq, Ls - Vector((0, 0, drop))), (F + STAG * (len(TAGS) - 1), q0, Ld), (2 * F + 2 * STAG * (len(TAGS) - 1) - f0 + 1, Rq, Ls - Vector((0, 0, drop))), (2 * F + 2 * STAG * (len(TAGS) - 1) - FD + 1, Rq, Ls - Vector((0, 0, drop))), (2 * F + 2 * STAG * (len(TAGS) - 1), Rq, Ls)):
            o.rotation_quaternion = q; o.location = loc; o.keyframe_insert("rotation_quaternion", frame=fr); o.keyframe_insert("location", frame=fr)
    print("USA ANIM %s: coborare %.0f m (cadru %d), apoi inaintare + rotire pana la cadrul %d" % (tag, drop, FD, F))
FE = F + STAG * (len(TAGS) - 1); sc.frame_start, sc.frame_end = 1, 2 * FE
blades = [o for o in col.objects if o.name.startswith("at_lama_")]; worst = 0
for fr in list(range(1, FE + 1, K)) + [FE]:
    sc.frame_set(fr); bv = [BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices], [list(p.vertices) for p in o.data.polygons]) for o in blades]
    hits = [(blades[i].name, blades[j].name, len(bv[i].overlap(bv[j]))) for i in range(len(blades)) for j in range(i + 1, len(blades)) if bv[i].overlap(bv[j])]
    if hits: worst = max(worst, max(h[2] for h in hits)); print("USA cadru %3d: %d perechi de lame care se taie: %s" % (fr, len(hits), ", ".join("%s x %s (%d)" % (h[0][8:], h[1][8:], h[2]) for h in hits[:6])))
print("USA verificare intersectii intre lame: %s" % ("niciuna" if worst == 0 else "max %d perechi de triunghiuri" % worst))
sc.frame_set(FE); hosts = [o for o in col.objects if o.type == "MESH" and not o.name.startswith(("at_lama", "ref_lama"))]; Vh, Fh = [], []
for o in hosts:
    k = len(Vh); Vh += [o.matrix_world @ v.co for v in o.data.vertices]; Fh += [[k + i for i in p.vertices] for p in o.data.polygons]
Th = BVHTree.FromPolygons(Vh, Fh); dirs = [Vector(d).normalized() for d in ((0, 0, 1), (0, 0, -1), (1, 0, 1), (-1, 0, 1), (0, 1, -1), (0, -1, -1))]
bv = [BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices], [list(p.vertices) for p in o.data.polygons]) for o in blades]
for i in range(len(blades)):
    for j in range(i + 1, len(blades)):
        ov = bv[i].overlap(bv[j])
        if not ov: continue
        oi = blades[i]; P = [oi.matrix_world @ (sum((oi.data.vertices[v].co for v in oi.data.polygons[a_].vertices), Vector()) / len(oi.data.polygons[a_].vertices)) for a_, b_ in ov[::max(1, len(ov) // 40)]]
        h = sum(1 for p in P if all(Th.ray_cast(p + d * .3, d, 4000)[0] is not None for d in dirs)) / len(P)
        c_ = sum(P, Vector()) / len(P) - Vector((XB, 0, 0)); print("USA deschise: %s x %s se taie (%d), in jurul %s, ascuns %.0f%%" % (blades[i].name[8:], blades[j].name[8:], len(ov), tuple(round(x) for x in c_), 100 * h))
sc.frame_set(FE); bpy.ops.wm.save_as_mainfile(filepath=OUT)
