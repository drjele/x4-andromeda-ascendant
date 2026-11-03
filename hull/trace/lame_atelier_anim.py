# The workshop blades built and animated from an iteration (asked: iterate until they animate right): for each blade tag the deployed
# rows (piese/ghid_lama_<tag>_<ver>.npz) -> closed lying-V piece (sharp long edges, lame_rosu) at_lama_<tag>_S / _D in ATELIER_LAME at
# x XB, origin on its hinge, quaternion keyframes from _pliere.npz: frame 1 stowed (turned), F open, 2F stowed. D mirrored.
# With a slide in _pliere.npz (stowed = turned, then slid): frame 1 turned + slid, F/2 turned (slid back out), F open; and back.
# Usage: blender -b <in.blend> --python lame_atelier_anim.py -- <out.blend> <piese dir> <ver> <tag,...> ; env XB=-7000 F=60
import bpy, bmesh, sys, os, math, numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PD, VER, TAGS = a[0], a[1], a[2], a[3].split(","); XB, F = float(os.environ.get("XB", -7000)), int(os.environ.get("F", 60))
col = bpy.data.collections["ATELIER_LAME"]; mat = bpy.data.materials.get("lame_rosu"); sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, 2 * F
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
    at = me.attributes.new("sharp_edge", "BOOLEAN", "EDGE"); K = m // 3
    for e in me.edges:
        i0, i1 = sorted(e.vertices); at.data[e.index].value = (i1 - i0 == m and i0 % m in (0, K, 2 * K))
    for p in me.polygons: p.use_smooth = True
    if mat: me.materials.append(mat)
    return me
for tag in TAGS:
    G = np.load(os.path.join(PD, "ghid_lama_%s_%s.npz" % (tag, VER))); Pl = np.load(os.path.join(PD, "ghid_lama_%s_%s_pliere.npz" % (tag, VER)))
    Ms, Mj, Va = G["lama_margine_sus"], G["lama_margine_jos"], G["lama_varf"]; Kc = 6; f_ = np.linspace(0, 1, Kc + 1)[:-1]
    R = np.stack([Ms + (Va - Ms) * t for t in f_] + [Va + (Mj - Va) * t for t in f_] + [Mj + (Ms - Mj) * t for t in f_], axis=1)
    H, ax, th = Vector(Pl["hinge"].tolist()), Vector(Pl["axis"].tolist()), float(Pl["turn"])
    for sd, mir in (("S", False), ("D", True)):
        me = build("at_lama_%s_%s" % (tag, sd), R, mir); Hs = Vector((-H.x, H.y, H.z)) if mir else H.copy(); axs = Vector((ax.x, -ax.y, -ax.z)) if mir else ax.copy()
        me.transform(Matrix.Translation(-Hs)); o = bpy.data.objects.new("at_lama_%s_%s" % (tag, sd), me); col.objects.link(o); o.location = Hs + Vector((XB, 0, 0)); o.rotation_mode = "QUATERNION"
        qs = Matrix.Rotation(math.radians(th), 4, axs).to_quaternion(); q0 = Matrix.Identity(4).to_quaternion()
        sl = Vector(Pl["slide"].tolist()) if "slide" in Pl.files else Vector((0, 0, 0)); sl = Vector((-sl.x, sl.y, sl.z)) if mir else sl
        base = Hs + Vector((XB, 0, 0))
        keys = [(1, qs, base + sl), (F, q0, base), (2 * F, qs, base + sl)] if sl.length < 1e-6 else [(1, qs, base + sl), (F // 2, qs, base), (F, q0, base), (F + F // 2, qs, base), (2 * F, qs, base + sl)]
        for fr, q, loc in keys:
            o.rotation_quaternion = q; o.location = loc; o.keyframe_insert("rotation_quaternion", frame=fr); o.keyframe_insert("location", frame=fr)
    print("ATELIER lama %s: balama %s, axa %s, rotire %+.0f" % (tag, tuple(round(c, 1) for c in H), tuple(round(c, 2) for c in ax), th))
sc.frame_set(F); bpy.ops.wm.save_as_mainfile(filepath=OUT)
