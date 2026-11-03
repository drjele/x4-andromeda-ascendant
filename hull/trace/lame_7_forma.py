# Hinge-7 blades: the shape nudged where the stowed blade still shows (asked: hinge at 7 for all, change their shape so extended they
# look like the reference, one turn if it can): for each blade's best single turn about 7 (lame_7_cauta.py), the stowed rows not
# hidden are pulled towards the nearest of the inner lines (front-arm spine, back-arm spine, PS middle line x=0 at z 305), raised 0.1
# at a time until hidden, the pulls smoothed along the blade (SM rows); the deployed = nudged stowed turned back. Prints the stowed
# exposure before / after and the deployed change (mean / max, over the visible part = outside the root extension).
# Writes piese/ghid_lama_<nr>_v4.npz + _v4_pliere.npz (hinge, axis, turn, slide 0). Usage: ... -- <cauta.npy> <piese dir> ; env SM=12 IT=5
import bpy, sys, os, json, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; BEST = np.load(a[0], allow_pickle=True); PD = a[1]; E = lambda k, d: float(os.environ.get(k, d)); X0 = -1600.0
SM, IT = E("SM", 12), int(E("IT", 5)); H = np.array([-59.6, 74.3, 292.7])
ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if o.type == "MESH" and not o.name.startswith("an_lama")]
V, F = [], []
for o in ship:
    k = len(V); V += [o.matrix_world @ v.co - Vector((X0, 0, 0)) for v in o.data.vertices]; F += [[k + i for i in p.vertices] for p in o.data.polygons]
T = BVHTree.FromPolygons(V, F); dirs = [Vector(d).normalized() for d in ((0, 0, 1), (0, 0, -1), (1, 0, 1), (-1, 0, 1), (0, 1, -1), (0, -1, -1))]
hid = lambda p: all(T.ray_cast(Vector(p) + d * .3, d, 4000)[0] is not None for d in dirs)
def line(obj, nm):
    o = bpy.data.objects[obj]; return np.array([o.matrix_world @ p.co.xyz for p in o.data.splines[json.loads(o["linii"]).index(nm)].points]) + [3100, 0, 0]
inner = np.r_[line("g_as_bf_sudat_S", "g_as_bf_spinare_brat_fata_S"), line("g_as_bo_sudat_S", "g_as_bo_spinare_brat_S"), np.c_[np.zeros(60), np.linspace(-50, 460, 60), np.full(60, 305.)]]
def gsm(A, sig):
    r = int(3 * sig); k = np.exp(-.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum(); P = np.r_[np.repeat(A[:1], r, 0), A, np.repeat(A[-1:], r, 0)]
    return np.c_[[np.convolve(P[:, j], k, mode="valid") for j in range(A.shape[1])]].T
def rot(ax, th):
    ax = np.array(ax) / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K
for tag, b1, b2 in BEST:
    ax, thd, _ = b1[1]; R = rot(ax, math.radians(thd)); G = np.load(os.path.join(PD, "ghid_lama_%s_v3.npz" % tag))
    RW = np.stack([G["lama_margine_sus"], G["lama_margine_jos"], G["lama_varf"]], 1); n = len(RW); stw = (RW - H) @ R.T + H
    ne = int(np.linalg.norm(RW[0].mean(0) - H)) - 1                       # rows of the root extension (hidden in PS, not compared)
    rowpts = lambda S, i: np.r_[S[i], [(S[i, 0] + S[i, 2]) / 2, (S[i, 1] + S[i, 2]) / 2]]
    exr = lambda S: np.array([not all(hid(p) for p in rowpts(S, i)) for i in range(n)])
    ex0 = exr(stw); D = np.zeros((n, 3)); S = stw.copy()
    for it in range(IT):
        ex = exr(S)
        if not ex.any(): break
        for i in np.where(ex)[0]:
            c = S[i].mean(0); tgt = inner[np.argmin(np.linalg.norm(inner - c, axis=1))]
            for t in np.arange(.1, 1.01, .1):
                if all(hid(p + (tgt - c) * t) for p in rowpts(S, i)): break
            D[i] += (tgt - c) * t
        D = gsm(D, SM) * 1.1; S = stw + D[:, None, :]
    ex1 = exr(S); dep = (S - H) @ R + H; dev = np.linalg.norm((dep - RW)[ne:].reshape(-1, 3), axis=1)
    np.savez(os.path.join(PD, "ghid_lama_%s_v4.npz" % tag), lama_margine_sus=dep[:, 0], lama_margine_jos=dep[:, 1], lama_varf=dep[:, 2])
    np.savez(os.path.join(PD, "ghid_lama_%s_v4_pliere.npz" % tag), hinge=H, axis=np.array(ax) / np.linalg.norm(ax), turn=float(thd), slide=np.zeros(3))
    print("F7 %s: o rotire %+d in jurul axei %s prin 7; randuri expuse stransa %d%% -> %d%%; deschisa schimbata fata de referinta (partea vizibila): medie %.1f m, max %.1f m" % (tag, thd, tuple(np.round(ax, 2)), 100 * ex0.mean(), 100 * ex1.mean(), dev.mean(), dev.max()))
