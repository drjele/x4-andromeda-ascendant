# Guide lines on the arms' outline of the new body (asked: continuous lines, no abrupt change of direction - like a C, a
# U, an orbit): along the tube (tub.npz rings from K0 to the open end, through the loop), on each ring the two side points
# (farthest left/right of the tube's own direction, side = tangent x up, flipped to stay continuous where the tube turns
# down), then the two rails smoothed hard along the tube (gaussian + twicing) so they read as one smooth curve each. Placed
# like the exploded piece (its offset to the built one) and mirrored for _D. Collection GHIDAJE_BRATE_169_C.
# Usage: blender -b <file.blend> --python ghid_brate.py -- <tub.npz> <out.blend> <dx> [piece]
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; T = np.load(a[0]); OUT, DX = a[1], float(a[2]); NAME = a[3] if len(a) > 3 else "piesa_comp_169_C"
K0, SG = int(os.environ.get("CORP_TUB_K0", "30")), float(os.environ.get("GHID_BRAT_NET", "10"))
X, C = T["X"][K0:], T["C"][K0:]
off = np.array(bpy.data.objects["expl_" + NAME].location - bpy.data.objects[NAME].location)
tg = np.gradient(C, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
side = np.cross(tg, [0, 0, 1.0]); side /= np.maximum(np.linalg.norm(side, axis=1), 1e-9)[:, None]
for k in range(1, len(side)):                                          # keep the side vector's sense continuous
    if side[k] @ side[k - 1] < 0: side[k] *= -1
d = np.einsum("kij,kj->ki", X - C[:, None], side); A = X[np.arange(len(X)), d.argmax(1)]; B = X[np.arange(len(X)), d.argmin(1)]
def gs(P, s):
    n = int(3 * s); k = np.exp(-0.5 * (np.arange(-n, n + 1) / s) ** 2); k /= k.sum()
    Z = np.vstack([2 * P[:1] - P[n:0:-1], P, 2 * P[-1:] - P[-2:-n - 2:-1]]); return np.stack([np.convolve(Z[:, i], k, "valid") for i in range(3)], 1)
A, B = [2 * gs(P, SG) - gs(gs(P, SG), SG) for P in (A, B)]
def turn(P):                                                           # largest change of direction between 2 m steps (deg)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.arange(0, s[-1], 2.0); Q = np.stack([np.interp(u, s, P[:, i]) for i in range(3)], 1)
    t = np.diff(Q, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]; return np.degrees(np.arccos(np.clip(np.sum(t[1:] * t[:-1], 1), -1, 1))).max()
from mathutils.kdtree import KDTree                                     # start where both rails lie on the piece's surface (before
me = bpy.data.objects[NAME].data; kd = KDTree(len(me.vertices))         # that the tube is inside the deck's blend)
for v in me.vertices: kd.insert(v.co, v.index)
kd.balance(); on = lambda P: np.array([kd.find((p[0] + DX, p[1], p[2]))[2] for p in P]) < 2.0
snap = lambda P: np.array([np.array(kd.find((p[0] + DX, p[1], p[2]))[0]) - [DX, 0, 0] for p in P])
for it in range(3):                                                    # the relaxation moved the surface off the raw tube: each
    A, B = [2 * gs(snap(P), SG) - gs(gs(snap(P), SG), SG) for P in (A, B)]   # rail snapped onto the piece, smoothed again
dmax = max(np.array([kd.find((p[0] + DX, p[1], p[2]))[2] for p in P]).max() for P in (A, B))
print("GHID BRAT: lipit de suprafata piesei, departare maxima %.2f m, de la y %.0f pana la capatul tubului" % (dmax, A[0, 1]))
col = bpy.data.collections.get("GHIDAJE_BRATE_169_C") or bpy.data.collections.new("GHIDAJE_BRATE_169_C")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for ob in list(col.objects): bpy.data.objects.remove(ob)
mg = bpy.data.materials.get("ghidaj") or bpy.data.materials.new("ghidaj"); mg.diffuse_color = (1.0, 0.85, 0.0, 1)
for nm, P in (("a", A), ("b", B)):
    for sd, sg in (("S", 1), ("D", -1)):
        Q = P.copy(); Q[:, 0] *= sg; Q[:, 0] += DX; Q += off
        cu = bpy.data.curves.new(nm, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.2; sp = cu.splines.new("POLY"); sp.points.add(len(Q) - 1)
        for p, q in zip(sp.points, Q): p.co = (*q, 1)
        cu.materials.append(mg); col.objects.link(bpy.data.objects.new("ghid_brat_%s_%s" % (nm, sd), cu))
    print("GHID BRAT %s: %d puncte, cea mai mare schimbare de directie %.2f grade la 2 m" % (nm, len(P), turn(P)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
