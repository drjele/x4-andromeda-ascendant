# Snaps a piece's open rim onto its guide contours (asked: the arm does not follow the guides at the nacelle mouth, seen from
# below there is a small "ear" / step between the arm and the nacelle): every boundary vertex of the piece (an edge with one face)
# within MAXD m of a guide curve is moved onto the curve (nearest point of the densely resampled curve); the displacement is
# spread over the vertices within R m of the rim (weight (1 - d/R)^2 over the nearest rim vertices' displacements), so the
# surface follows without a crease. Guides are in the assembled-guides block (world + GX on x = ship), pieces in ASAMBLAT_NOU
# (world + X0 = ship).
# Usage: blender -b <scene.blend> --python margine_pe_contur.py -- <out.blend> <piece> <guide[,guide...]> [<piece> <guides>]...
#        env X0=1600 GX=3100 MAXD=3 R=10 K=8 ENDS=8 (m left alone at each end of a curve)
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; jobs = list(zip(a[1::2], a[2::2]))
E = lambda k, d: float(os.environ.get(k, d))
X0, GX, MAXD, R, K, ENDS = E("X0", 1600), E("GX", 3100), E("MAXD", 3), E("R", 10), int(E("K", 8)), E("ENDS", 8)
def curve_pts(g):
    c = bpy.data.objects[g]; P = np.array([c.matrix_world @ p.co.xyz + Vector((GX, 0, 0)) for s in c.data.splines for p in s.points])
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; t = np.linspace(0, s[-1], int(s[-1] / 0.05) + 2)
    Q = np.c_[tuple(np.interp(t, s, P[:, i]) for i in range(3))]
    return Q[(t > ENDS) & (t < s[-1] - ENDS)]                       # the rim turns at the curve's ends: left alone there
for piece, guides in jobs:
    C = np.vstack([curve_pts(g) for g in guides.split(",")]); kc = KDTree(len(C))
    for i, p in enumerate(C): kc.insert(p, i)
    kc.balance()
    o = bpy.data.objects[piece]; me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    mw = o.matrix_world; off = Vector((X0, 0, 0))
    rim = {v for e in bm.edges if not e.is_manifold for v in e.verts}
    disp = {}
    for v in rim:
        p = mw @ v.co + off; q, _, d = kc.find(p)
        if d < MAXD: disp[v.index] = np.array(q - p)
    if not disp: print("MARGINE %s: nimic de mutat" % piece); continue
    D0 = np.array([np.linalg.norm(d) for d in disp.values()])
    kr = KDTree(len(disp)); idx = list(disp)
    bm.verts.ensure_lookup_table()
    for j, i in enumerate(idx): kr.insert(mw @ bm.verts[i].co + off, j)
    kr.balance()
    inv = mw.inverted().to_3x3(); moved = 0
    for v in bm.verts:
        p = mw @ v.co + off
        if v.index in disp: dv = disp[v.index]
        else:
            nb = kr.find_n(p, K); w = np.array([max(0, 1 - d / R) ** 2 for _, _, d in nb])
            if w.sum() == 0: continue
            dv = sum(wi * disp[idx[j]] for wi, (_, j, _) in zip(w, nb)) / w.sum() * max(0, 1 - nb[0][2] / R) ** 2
        v.co += inv @ Vector(dv); moved += 1
    nd = len(bm.faces); bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4); nd -= len(bm.faces)   # faces closed up by the snap
    bm.to_mesh(me); bm.free(); me.update()
    print("MARGINE %s: %d varfuri de margine pe %s (abatere max %.2f m, medie %.2f m), %d varfuri mutate in total (raza %.0f m), %d fete degenerate scoase"
          % (piece, len(disp), guides, D0.max(), D0.mean(), moved, R, nd))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
