# All the blades from the reference blades' clean lines, with their fold (asked: our blades follow the reference blades' angles; make
# them all, with animation, open front and back to see them). Per blade (lame_ref_linii.py output): wide side of the lying V on the
# edge nearer the ship (mean distance to the ship pieces), open OPEN x width along the blade normal, the sharp apex on the other edge;
# closed piece (all rows down to the narrow ends), smooth with the 3 long edges sharp, lame_rosu; an_lama_<nr>_S / _D (D mirrored).
# Hinge = the wide side at the end nearer the ship; stow = one turn about the vertical or the blade normal through it, the angle with
# the fewest vertices exposed (rays up / down / 4 obliques must hit the ship); keyframes frame 1 stowed, F open, 2F stowed.
# Removes an_lama_S / an_lama_D (the old 007). Usage: blender -b <in> --python lame_toate.py -- <out.blend> <linii.npz> ; env OPEN=0.3 F=60 STEP=4
import bpy, bmesh, sys, os, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, L = a[0], np.load(a[1]); OPEN, F, STEP = float(os.environ.get("OPEN", .3)), int(os.environ.get("F", 60)), int(os.environ.get("STEP", 4)); X0 = -1600.0
for n in [o.name for o in bpy.data.objects if o.name.startswith("an_lama")]: bpy.data.objects.remove(bpy.data.objects[n])
col = bpy.data.collections["ASAMBLAT_NOU"]; mat = bpy.data.materials.get("lame_rosu")
ship = [o for o in col.objects if o.type == "MESH"]; V, Fc = [], []
for o in ship:
    k = len(V); V += [o.matrix_world @ v.co - Vector((X0, 0, 0)) for v in o.data.vertices]; Fc += [[k + i for i in p.vertices] for p in o.data.polygons]
T = BVHTree.FromPolygons(V, Fc)                                           # ship in ship coords
dirs = [Vector(d).normalized() for d in ((0, 0, 1), (0, 0, -1), (1, 0, 1), (-1, 0, 1), (0, 1, -1), (0, -1, -1))]
def dist(P): return np.mean([T.find_nearest(Vector(p), 2000)[3] for p in P[::10]])
def build(name, R, mirror):
    bm = bmesh.new(); P = R * ([-1, 1, 1] if mirror else 1); n, m = P.shape[:2]
    vv = [[bm.verts.new(tuple(P[i, j])) for j in range(m)] for i in range(n)]
    for i in range(n - 1):
        for j in range(m):
            q = [vv[i][j], vv[i][(j + 1) % m], vv[i + 1][(j + 1) % m], vv[i + 1][j]]; bm.faces.new(q[::-1] if mirror else q)
    for row, rev in ((vv[0], not mirror), (vv[-1], mirror)):
        f = bm.faces.new(row[::-1] if rev else row); bmesh.ops.triangulate(bm, faces=[f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    at = me.attributes.new("sharp_edge", "BOOLEAN", "EDGE"); K = m // 3; cols = {0, K, 2 * K}
    for e in me.edges:
        i0, i1 = sorted(e.vertices); at.data[e.index].value = (i1 - i0 == m and i0 % m in cols)
    for p in me.polygons: p.use_smooth = True
    if mat: me.materials.append(mat)
    return me
names = sorted({k.rsplit("_", 1)[0] for k in L.files})
sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, 2 * F
for nm in names:
    mid, w, ac, nn = L[nm + "_mid"], L[nm + "_w"], L[nm + "_across"], L[nm + "_n"]; tag = nm.split("_")[1]
    e_a, e_b = mid + ac * (w / 2)[:, None], mid - ac * (w / 2)[:, None]
    wide, apex = (e_a, e_b) if dist(e_a) < dist(e_b) else (e_b, e_a)
    if dist(wide[:20]) > dist(wide[-20:]): wide, apex, w, nn = wide[::-1], apex[::-1], w[::-1], nn[::-1]   # row 0 = the root (nearer the ship)
    up = nn.copy(); up[up[:, 2] < 0] *= -1
    Ms, Mj = wide + up * (OPEN * w / 2)[:, None], wide - up * (OPEN * w / 2)[:, None]; Kc = 6; f_ = np.linspace(0, 1, Kc + 1)[:-1]
    R = np.stack([Ms + (apex - Ms) * t for t in f_] + [apex + (Mj - apex) * t for t in f_] + [Mj + (Ms - Mj) * t for t in f_], axis=1)
    np.savez(os.path.join(os.path.dirname(a[1]), "ghid_lama_%s.npz" % tag), lama_varf=apex, lama_margine_sus=Ms, lama_margine_jos=Mj)
    H = Vector(((Ms[0] + Mj[0]) / 2).tolist()); pts = [Vector(p) for p in R.reshape(-1, 3)[::STEP]]
    def exposed(ax, th):
        M = Matrix.Translation(H) @ Matrix.Rotation(math.radians(th), 4, ax) @ Matrix.Translation(-H)
        return sum(1 for p in pts if any(T.ray_cast(M @ p + d * .3, d, 4000)[0] is None for d in dirs)) / len(pts)
    best = (exposed(Vector((0, 0, 1)), 0), "vert", 0.0)
    for axn, ax in (("vert", Vector((0, 0, 1))), ("normala", Vector(up[0].tolist()).normalized())):
        for th in range(-90, 91, 10):
            if th == 0: continue
            e = exposed(ax, th)
            if e < best[0]: best = (e, axn, float(th))
    axn, th = best[1], best[2]
    for k in (-5, -2.5, 2.5, 5):                                          # refine
        ax = Vector((0, 0, 1)) if axn == "vert" else Vector(up[0].tolist()).normalized(); e = exposed(ax, th + k)
        if e < best[0]: best = (e, axn, th + k)
    e, axn, th = best; axv = Vector((0, 0, 1)) if axn == "vert" else Vector(up[0].tolist()).normalized()
    print("LAMA %s: %.0f m, latime max %.1f; balama %s; strangere: rotire %+.1f in jurul axei %s -> expus %.1f%% (deschisa %.0f%%)" % (tag, np.linalg.norm(np.diff(mid, axis=0), axis=1).sum(), w.max(), tuple(round(c, 1) for c in H), th, axn, 100 * e, 100 * exposed(axv, 0)))
    for sd, mir in (("S", False), ("D", True)):
        me = build("an_lama_%s_%s" % (tag, sd), R, mir); Hs = Vector((-H.x, H.y, H.z)) if mir else H.copy()
        me.transform(Matrix.Translation(-Hs)); o = bpy.data.objects.new("an_lama_%s_%s" % (tag, sd), me); col.objects.link(o)
        o.location = Hs + Vector((X0, 0, 0)); o.rotation_mode = "QUATERNION"
        ax = axv.copy()
        if mir: ax = Vector((ax.x, -ax.y, -ax.z))                         # mirrored in x: the axis' y, z flip with the turn
        q_st = Matrix.Rotation(math.radians(th), 4, ax).to_quaternion(); q_op = Matrix.Identity(4).to_quaternion()
        for fr, q in ((1, q_st), (F, q_op), (2 * F, q_st)):
            o.rotation_quaternion = q; o.keyframe_insert("rotation_quaternion", frame=fr)
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "BEZIER"
sc.frame_set(F); bpy.ops.wm.save_as_mainfile(filepath=OUT)
