# The hatches' guides drawn separately next to the clean arm guides (asked: guides separately, clean lines): from the closed state,
# per S hatch its outline (boundary of its skin faces, yellow) and the arm's cutout outline (edges between the arm skin and the new
# compartment faces, orange), as curves in GHIDAJ_TRAPE at x XS; with each one's length / max kink / turn-direction changes seen
# from below. Usage: blender -b <scene> --python deseneaza_ghidaje_trape.py -- <scene before the hatches> <out.blend>   env XS=-13000
import bpy, bmesh, sys, os, numpy as np
from mathutils.bvhtree import BVHTree as BV
a = sys.argv[sys.argv.index("--") + 1:]; ORIG, OUT = a[0], a[1]; XS = float(os.environ.get("XS", -13000)); bpy.context.scene.frame_set(1)
with bpy.data.libraries.load(ORIG) as (lf, lt): lt.meshes = ["an_brat_fata_S.002"]
m0 = lt.meshes[0]; t0 = BV.FromPolygons([v.co.copy() for v in m0.vertices], [list(p.vertices) for p in m0.polygons]); on0 = lambda p: (lambda r: r[0] is not None and r[3] < 2e-3)(t0.find_nearest(p))
def loops(edges):
    adj = {}
    for e in edges:
        for v in e.verts: adj.setdefault(v, []).append(e)
    seen, out = set(), []
    for e0 in edges:
        if e0 in seen: continue
        v = e0.verts[0]; e = e0; L = [v]
        while e not in seen:
            seen.add(e); v = e.other_vert(v); L.append(v); nx = [x for x in adj[v] if x not in seen]
            if not nx: break
            e = nx[0]
        out.append(np.array([tuple(p.co) for p in L]))
    return sorted(out, key=len, reverse=True)
col = bpy.data.collections.get("GHIDAJ_TRAPE") or bpy.data.collections.new("GHIDAJ_TRAPE")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
def draw(nm, P, rgb):
    d = np.diff(P[:, :2], axis=0); ln = np.linalg.norm(d, axis=1); d = d[ln > 1e-3]; ang = np.degrees(np.abs(np.arctan2(d[:-1, 0] * d[1:, 1] - d[:-1, 1] * d[1:, 0], (d[:-1] * d[1:]).sum(1))))
    cu = bpy.data.curves.new(nm, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; sp = cu.splines.new("POLY"); sp.points.add(len(P) - 1)
    for p, q in zip(sp.points, P): p.co = (q[0] + XS, q[1], q[2], 1)
    o = bpy.data.objects.new(nm, cu); o.color = rgb; col.objects.link(o)
    m = bpy.data.materials.new(nm); m.diffuse_color = rgb; cu.materials.append(m)
    print("TRAPE %-28s %6.0f m, %5d puncte, unghi mediu %.2f, %d frangeri > 25 grade" % (nm, ln.sum(), len(P), ang.mean(), (ang > 25).sum()))
for gk in ("fata", "spate"):
    me = bpy.data.objects["at_usa_%s_S" % gk].data; bm = bmesh.new(); bm.from_mesh(me)
    kb = me.shape_keys.key_blocks[0] if me.shape_keys else None
    if kb:
        for v in bm.verts: v.co = kb.data[v.index].co
    sk = {f for f in bm.faces if on0(f.calc_center_median())}; be = [e for e in bm.edges if sum(1 for f in e.link_faces if f in sk) == 1]
    for k, P in enumerate(loops(be)[:2]): draw("gt_trapa_%s_S%s" % (gk, "_gaura_coloana" if k else ""), P, (1, .85, 0, 1))
arm = bpy.data.objects["at_brat_fata_S"].data; bm = bmesh.new(); bm.from_mesh(arm); skin = {f: on0(f.calc_center_median()) for f in bm.faces}
rim = [e for e in bm.edges if len(e.link_faces) == 2 and skin[e.link_faces[0]] != skin[e.link_faces[1]] and min(v.co.z for v in e.verts) < 280]
for k, P in enumerate([L for L in loops(rim) if len(L) > 200][:2]): draw("gt_decupaj_S_%d" % k, P, (1, .45, 0, 1))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
