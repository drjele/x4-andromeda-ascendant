# Copies a front arm beside the ship and rebuilds its mouth edge on the lip guide (asked: an_brat_fata_D does not follow
# g_as_bf_buze_gura_brat_fata_D, it sticks out past it - copy it beside, redo the surface by the guide, compare, the "ear" shows up).
# Beyond the lip = the side of the lip away from the arm body: per lip sample (0.25 m) the direction NIN from the arm body (its
# vertices 12..25 m off, in the plane normal to the lip) to the lip; a vertex within 25 m of the lip with (p - lip) . NIN > TOL is
# past the lip. Those vertices (and their faces) are removed, then the new open rim within MAXD m of the lip is snapped onto it
# (old rim vertices only within 3 m: the rim turns at the mouth ends are not the lip) and the move spread over R m (weights (1 - d/R)^2), as margine_pe_contur.py does.
# Two copies go beside the ship (collection COMPARATIE_URECHE): the piece as it is (x shift DX0) and the rebuilt one (DX1), each
# with a copy of the lip guide; with APPLY=1 the rebuilt mesh also replaces the piece in place.
# The moved (non-rim) vertices are then smoothed NETED times (the drag leaves a small crease next to the lip).
# Usage: blender -b <scene.blend> --python buza_fara_ureche.py -- <out.blend> <piece> <guide>
#        env X0=1600 GX=3100 TOL=0.3 MAXD=12 R=10 DX0=-5000 DX1=-5800 APPLY=0 UNESTE=0.5 NETED=3 NF=0.3 INEL=1 (smoothing the first ring too folds the thin faces at the rim)
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PIECE, GUIDE = a[0], a[1], a[2]
E_ = lambda k, d: float(os.environ.get(k, d))
X0, GX, TOL, MAXD, R, DX0, DX1 = E_("X0", 1600), E_("GX", 3100), E_("TOL", .3), E_("MAXD", 12), E_("R", 10), E_("DX0", -5000), E_("DX1", -5800)
gc = bpy.data.objects[GUIDE]; G = np.array([gc.matrix_world @ p.co.xyz + Vector((GX, 0, 0)) for s in gc.data.splines for p in s.points])
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(G, axis=0), axis=1))]; t = np.arange(0, s[-1], .25)
G = np.c_[tuple(np.interp(t, s, G[:, i]) for i in range(3))]
src = bpy.data.objects[PIECE]; mw = src.matrix_world; off = Vector((X0, 0, 0))
def kd(P):
    k = KDTree(len(P))
    for i, p in enumerate(P): k.insert(p, i)
    k.balance(); return k
kg = kd(G)
bm = bmesh.new(); bm.from_mesh(src.data); bm.verts.ensure_lookup_table()
V = np.array([mw @ v.co + off for v in bm.verts]); kv = kd(V)
NIN = np.zeros_like(G)
for j in range(len(G)):
    p = G[j]; T = G[min(j + 8, len(G) - 1)] - G[max(j - 8, 0)]; T /= np.linalg.norm(T)
    nb = np.array([V[i] for _, i, _ in kv.find_range(p, 25)])
    if not len(nb): continue
    D = nb - p; m = np.abs(D @ T) < 1.5; D = D[m] - np.outer(D[m] @ T, T); f = D[np.linalg.norm(D, axis=1) > 12]
    if len(f): n = -f.mean(0); NIN[j] = n / np.linalg.norm(n)
def excess(P):
    E = np.zeros(len(P))
    for i, p in enumerate(P):
        _, j, d = kg.find(p)
        if d < 25: E[i] = (p - G[j]) @ NIN[j]
    return E
E = excess(V); bad = [bm.verts[i] for i in np.where(E > TOL)[0]]
zone = V[E > TOL]
print("DINCOLO DE BUZA (%s): %d varfuri, exces max %.2f m, bbox %s .. %s" % (PIECE, len(bad), E.max(), zone.min(0).round(1), zone.max(0).round(1)))
rim0 = {v for e in bm.edges if not e.is_manifold for v in e.verts}
nf = len(bm.faces); bmesh.ops.delete(bm, geom=bad, context="VERTS")
loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context="VERTS")
print("SCOASE: %d fete" % (nf - len(bm.faces)))
# snap the new rim near the removed zone onto the lip, spread over R
bm.verts.ensure_lookup_table(); kz = kd(zone)
rim = {v for e in bm.edges if not e.is_manifold for v in e.verts}
disp = {}
for v in rim:
    p = mw @ v.co + off
    if kz.find(p)[2] > MAXD + R: continue
    q, _, d = kg.find(p)
    if d < (MAXD if v not in rim0 else 3): disp[v.index] = np.array(q - p)   # the old rim (mouth ends) only if already near the lip
big = np.array([mw @ bm.verts[i].co + off for i, d in disp.items() if np.linalg.norm(d) > 3])
if len(big): print("MUTARI > 3 m: %d varfuri de margine, bbox %s .. %s" % (len(big), big.min(0).round(1), big.max(0).round(1))); [print("   ", np.round(q_, 1), round(float(np.linalg.norm(d_)), 1)) for q_, d_ in ((mw @ bm.verts[i].co + off, d) for i, d in disp.items() if np.linalg.norm(d) > 3)]
idx = list(disp); kr = kd([mw @ bm.verts[i].co + off for i in idx]); inv = mw.inverted().to_3x3(); moved = 0; mv = []
for v in bm.verts:
    p = mw @ v.co + off
    if v.index in disp: dv = disp[v.index]
    else:
        nb = kr.find_n(p, 8); w = np.array([max(0, 1 - d / R) ** 2 for _, _, d in nb])
        if w.sum() == 0: continue
        dv = sum(wi * disp[idx[j]] for wi, (_, j, _) in zip(w, nb)) / w.sum() * max(0, 1 - nb[0][2] / R) ** 2
    v.co += inv @ Vector(dv); moved += 1
    if v.index not in disp and np.linalg.norm(dv) > 1e-6: mv.append(v)
def kink(vs):                                                          # sharpest crease among the moved vertices' edges (deg)
    es = {e for v in vs for e in v.link_edges if len(e.link_faces) == 2}
    return max((np.degrees(e.calc_face_angle(0)) for e in es), default=0)
rimn = {v for e in bm.edges if not e.is_manifold for v in e.verts}
near = {w for v in rimn for e in v.link_edges for w in e.verts} if E_("INEL", 1) else set(rimn)   # the rim stays put (INEL=1: its first ring too)
zn = [w for v in rimn for e in v.link_edges for w in e.verts]; zn = [v for v in zn if kz.find(mw @ v.co + off)[2] < MAXD + R]
ez = sorted(((np.degrees(e.calc_face_angle(0)), tuple(np.round(mw @ e.verts[0].co + off, 1))) for v in zn for e in v.link_edges if len(e.link_faces) == 2), reverse=True)[:6]
print("CUTE langa margine:", ez)
mv = [v for v in mv if v not in near]
NS = int(E_("NETED", 3)); k0 = kink(mv)
for _ in range(NS): bmesh.ops.smooth_vert(bm, verts=mv, factor=E_("NF", .3), use_axis_x=True, use_axis_y=True, use_axis_z=True)   # the snapped rim stays
ez2 = max((np.degrees(e.calc_face_angle(0)) for v in zn for e in v.link_edges if len(e.link_faces) == 2), default=0)
print("CUTE langa margine dupa netezire: max %.1f grade" % ez2)
print("NETEZIT: %d varfuri mutate, %d treceri; cuta max %.1f -> %.1f grade" % (len(mv), NS, k0, kink(mv)))
zr = [bm.verts[i] for i in disp]; nv = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=zr, dist=E_("UNESTE", .5))         # snapped rim points bunched on the lip cross over: merged
print("UNITE pe buza: %d varfuri de margine (sub %.1f m)" % (nv - len(bm.verts), E_("UNESTE", .5)))
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4); bm.normal_update()
# folds left by the snap, near the removed zone only (a thin face turned over at the rim): its free vertex goes to its neighbours' mean; all-rim faces dropped
nfix = ndel = 0
for _ in range(10):
    rimn = {v for e in bm.edges if not e.is_manifold for v in e.verts}
    fold = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > np.pi / 2 and kz.find(mw @ e.verts[0].co + off)[2] < MAXD + R]
    if not fold: break
    for e in fold:
        for f in e.link_faces:
            if not f.is_valid: continue
            free = [v for v in f.verts if v not in rimn]
            if not free: bmesh.ops.delete(bm, geom=[f], context="FACES_ONLY"); ndel += 1; continue
            for v in free: v.co = sum((w.co for ed in v.link_edges for w in ed.verts if w is not v), Vector()) / sum(1 for _ in v.link_edges); nfix += 1
    bm.normal_update()
print("PLIURI reparate: %d varfuri mutate la media vecinilor, %d fete scoase, ramase %d" % (nfix, ndel, sum(1 for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > np.pi / 2 and kz.find(mw @ e.verts[0].co + off)[2] < MAXD + R)))
nd = len(bm.faces); bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4); nd -= len(bm.faces)
bm.normal_update()
V2 = np.array([mw @ v.co + off for v in bm.verts]); E2 = excess(V2)
nm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
print("REFACUT: %d varfuri de margine pe buza (mutare max %.2f m), %d varfuri mutate, %d fete degenerate scoase; exces dupa: max %.2f m; muchii cu >2 fete %d"
      % (len(disp), max(np.linalg.norm(d) for d in disp.values()), moved, nd, E2.max(), nm))
me_new = bpy.data.meshes.new(PIECE + "_refacut"); bm.to_mesh(me_new); bm.free()
for m in src.data.materials: me_new.materials.append(m)
col = bpy.data.collections.get("COMPARATIE_URECHE") or bpy.data.collections.new("COMPARATIE_URECHE")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for n_ in (PIECE + "_langa_original", PIECE + "_langa_refacut", GUIDE + "_langa_original", GUIDE + "_langa_refacut"):
    if n_ in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n_])
for nm_, me, dx in ((PIECE + "_langa_original", src.data.copy(), DX0), (PIECE + "_langa_refacut", me_new, DX1)):
    o = bpy.data.objects.new(nm_, me); o.matrix_world = mw; o.location.x += dx; col.objects.link(o)
    g = gc.copy(); g.data = gc.data.copy(); g.name = GUIDE + ("_langa_original" if "orig" in nm_ else "_langa_refacut")
    g.location.x += dx + GX - X0; col.objects.link(g)
if os.environ.get("APPLY") == "1":
    old = src.data; src.data = me_new.copy(); src.data.name = PIECE
    if old.users == 0: bpy.data.meshes.remove(old)
    print("APLICAT pe %s" % PIECE)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
