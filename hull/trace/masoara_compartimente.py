# Checks the blade compartments (asked: clean hatch / cutout lines, each blade set in its own compartment, no surface through
# another): (1) the cutout outline in at_brat_fata_S = edges between the original arm skin and the new compartment faces, and the
# hatch outline = boundary of the hatch's skin faces (closed state); per loop length, max / mean turning angle seen from below,
# kinks > 25 deg; (2) every new contact between the arm and the other hull pieces: is it only along the cut seam (the piece's
# surface cut exactly on the compartment wall, touching it) or a real crossing. Usage: blender -b <scene> --python
# masoara_compartimente.py -- <original scene (before the compartments)>
import bpy, bmesh, sys, numpy as np
from mathutils.bvhtree import BVHTree as BV
ORIG = sys.argv[sys.argv.index("--") + 1]; bpy.context.scene.frame_set(1)
with bpy.data.libraries.load(ORIG) as (a, b): b.meshes = [n for n in a.meshes if n in ("an_brat_fata_S.002", "g_PS.001", "g_PS_carena.001", "an_ureche_S.001", "an_PS_rama.001")]
O = {m.name.split(".")[0]: m for m in b.meshes}
def bvm(me): return BV.FromPolygons([v.co.copy() for v in me.vertices], [list(p.vertices) for p in me.polygons])
tArm0 = bvm(O["an_brat_fata_S"]); on0 = lambda t, p: (lambda r: r[0] is not None and r[3] < 2e-3)(t.find_nearest(p))
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
    return out
def stats(nm, P):
    d = np.diff(P[:, :2], axis=0); ln = np.linalg.norm(d, axis=1); d = d[ln > 1e-3]; ln = ln[ln > 1e-3]
    if len(d) < 3: return
    ang = np.degrees(np.abs(np.arctan2(d[:-1, 0] * d[1:, 1] - d[:-1, 1] * d[1:, 0], (d[:-1] * d[1:]).sum(1))))
    Pk = P[np.r_[True, np.linalg.norm(np.diff(P[:, :2], axis=0), axis=1) > 1e-3]]; kk = np.where(ang > 25)[0]
    print("MC contur %s: %.0f m, %d puncte, unghi max %.1f, mediu %.2f grade, %d frangeri > 25 grade%s" % (nm, ln.sum(), len(P), ang.max(), ang.mean(), len(kk), (" la " + ", ".join("(%.0f, %.0f, %.0f) %.0f" % (*Pk[k + 1], ang[k]) for k in kk[:6])) if len(kk) else ""))
arm = bpy.data.objects["at_brat_fata_S"]; bm = bmesh.new(); bm.from_mesh(arm.data); skin = {f: on0(tArm0, f.calc_center_median()) for f in bm.faces}
rim = [e for e in bm.edges if len(e.link_faces) == 2 and skin[e.link_faces[0]] != skin[e.link_faces[1]] and min(v.co.z for v in e.verts) < 280 and all(abs(f.normal.z) > .2 or not skin[f] for f in e.link_faces)]
und = [e for e in rim if any(skin[f] and f.normal.z < -.2 or skin[f] and f.normal.z > .2 for f in e.link_faces)]
for k, P in enumerate(sorted(loops(rim), key=len, reverse=True)[:4]): stats("decupaj brat S bucla %d" % k, P)
for gk in ("fata", "spate"):
    d = bpy.data.objects["at_usa_%s_S" % gk]; me = d.data; bd = bmesh.new(); bd.from_mesh(me)
    if me.shape_keys:
        kb = me.shape_keys.key_blocks[0]
        for v in bd.verts: v.co = kb.data[v.index].co
    sk = {f for f in bd.faces if on0(tArm0, f.calc_center_median())}
    be = [e for e in bd.edges if sum(1 for f in e.link_faces if f in sk) == 1]
    for k, P in enumerate(sorted(loops(be), key=len, reverse=True)[:2]): stats("trapa %s S bucla %d%s" % (gk, k, " (gaura coloanei)" if k else ""), P)
def bvo(o):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh(); V = [o.matrix_world @ v.co for v in m.vertices]; F = [list(p.vertices) for p in m.polygons]
    oe.to_mesh_clear(); return BV.FromPolygons(V, F), V, F
ta, VA, FA = bvo(arm); armF = list(bm.faces)
for hn, on in (("at_PS", "g_PS"), ("at_PS_carena", "g_PS_carena"), ("at_ureche_S", "an_ureche_S"), ("at_PS_rama", "an_PS_rama")):
    h = bpy.data.objects[hn]; th, VH, FH = bvo(h); bh = bmesh.new(); bh.from_mesh(h.data); bh.faces.ensure_lookup_table()
    tH0 = bvm(O[on]); pr = th.overlap(ta); new = [(i, j) for i, j in pr if not skin[armF[j]] or not on0(tH0, bh.faces[i].calc_center_median())]
    seam = 0
    for i, j in new:
        f = bh.faces[i]
        if any(e.is_boundary for e in f.edges) or not on0(tH0, f.calc_center_median()) or not skin[armF[j]] and any(e.is_boundary or not all(skin.get(x, True) for x in e.link_faces) for e in armF[j].edges): seam += 1
    print("MC %s x brat: %d perechi, %d cu fete noi (compartiment / taietura); dintre ele pe linia de taietura %d, altfel %d" % (hn[3:], len(pr), len(new), seam, len(new) - seam))
