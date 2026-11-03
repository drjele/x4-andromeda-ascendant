# The blade piece from its confirmed guides (asked: draw the surface): a closed lying-V prism - top face between lama_margine_sus and
# lama_varf, bottom face between lama_margine_jos and lama_varf, the wide face (towards the arm) between the two edges, a triangle
# cap at the root; everything closes to the tip point. Faces ruled straight between the guide lines (the guides lie on the piece),
# ACROSS rows per face, the three long edges and the root rim marked sharp, the rest smooth shaded. Objects an_lama_S / an_lama_D
# (D = mirror) in ASAMBLAT_NOU at x X0 (ship coords mesh), material lame_rosu; plus copies beside the separate guides at x XSEP.
# NUME=lama: the objects are an_<NUME>_S / an_<NUME>_D and <NUME>_separat_S (another variant gets its own name).
# CAP_END=1: the last station is a cut, not the tip - closed by a triangle cap like the root (for a blade split in parts).
# Usage: blender -b <in.blend> --python lama_piesa.py -- <out.blend> <guides npz> ; env ACROSS=6 STEP=2 X0=-1600 XSEP=-5200 NUME=lama
import bpy, bmesh, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, G = a[0], np.load(a[1]); E = lambda k, d: float(os.environ.get(k, d))
K, STEP, X0, XSEP = int(E("ACROSS", 6)), E("STEP", 2), E("X0", -1600), E("XSEP", -5200); NM = os.environ.get("NUME", "lama"); CAPE = os.environ.get("CAP_END") == "1"
Va, Ms, Mj = G["lama_varf"], G["lama_margine_sus"], G["lama_margine_jos"]
idx = np.r_[np.arange(0, len(Va) - 1, int(STEP)), len(Va) - 1]; Va, Ms, Mj = Va[idx], Ms[idx], Mj[idx]; n = len(Va)
f = np.linspace(0, 1, K + 1)
ring = [Ms + (Va - Ms) * t for t in f[:-1]] + [Va + (Mj - Va) * t for t in f[:-1]] + [Mj + (Ms - Mj) * t for t in f[:-1]]   # one closed loop per station
R = np.stack(ring, axis=1)                                               # n x 3K x 3
m = R.shape[1]; sharp_cols = {0, K, 2 * K}                                # columns on margine_sus, varf, margine_jos
def build(name, mirror):
    bm = bmesh.new(); P = R * ([-1, 1, 1] if mirror else 1)
    if CAPE: vv = [[bm.verts.new(tuple(P[i, j])) for j in range(m)] for i in range(n)]; tipv = None
    else:
        tipv = bm.verts.new(tuple(P[-1, K]))                              # all columns meet at the tip
        vv = [[bm.verts.new(tuple(P[i, j])) for j in range(m)] for i in range(n - 1)] + [[tipv] * m]
    for i in range(n - 1):
        for j in range(m):
            q = [vv[i][j], vv[i][(j + 1) % m], vv[i + 1][(j + 1) % m], vv[i + 1][j]]
            if i == n - 2 and not CAPE: q = [vv[i][j], vv[i][(j + 1) % m], tipv]
            bm.faces.new(q[::-1] if mirror else q)
    cap = bm.faces.new(vv[0][::-1] if not mirror else vv[0]); bmesh.ops.triangulate(bm, faces=[cap])
    if CAPE: cap2 = bm.faces.new(vv[-1] if not mirror else vv[-1][::-1]); bmesh.ops.triangulate(bm, faces=[cap2])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    shp = set()
    for i in range(n - 1):
        for j in sharp_cols: shp.add(frozenset((vv[i][j], vv[i + 1][j])))
    for j in range(m): shp.add(frozenset((vv[0][j], vv[0][(j + 1) % m])))
    if CAPE:
        for j in range(m): shp.add(frozenset((vv[-1][j], vv[-1][(j + 1) % m])))
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    at = me.attributes.new("sharp_edge", "BOOLEAN", "EDGE"); vi = {v.index for v in bm.verts}
    ids = {frozenset((a_.index, b_.index)) for a_, b_ in (tuple(e) for e in shp)}
    for e in me.edges: at.data[e.index].value = frozenset(e.vertices) in ids
    for p in me.polygons: p.use_smooth = True
    free = sum(1 for e in bm.edges if len(e.link_faces) != 2); bm.free()
    mat = bpy.data.materials.get("lame_rosu")
    if mat: me.materials.append(mat)
    return me, free
col = bpy.data.collections["ASAMBLAT_NOU"]; sep = bpy.data.collections.get("GHIDAJ_LAMA_SEPARAT")
for nm in ("an_%s_S" % NM, "an_%s_D" % NM, "%s_separat_S" % NM):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm])
for nm, mir in (("an_%s_S" % NM, False), ("an_%s_D" % NM, True)):
    me, free = build(nm, mir); o = bpy.data.objects.new(nm, me); col.objects.link(o); o.location.x = X0
    print("LAMA PIESA %s: %d fete, muchii libere / ne-manifold %d, volum %.0f m3" % (nm, len(me.polygons), free, sum(abs(p.area) for p in me.polygons) * 0))
me, _ = build("%s_separat_S" % NM, False); o = bpy.data.objects.new("%s_separat_S" % NM, me); (sep or col).objects.link(o); o.location.x = XSEP
bm = bmesh.new(); bm.from_mesh(bpy.data.objects["an_%s_S" % NM].data); print("LAMA volum S %.0f m3, aria %.0f m2" % (bm.calc_volume(signed=True), sum(f_.calc_area() for f_ in bm.faces))); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
