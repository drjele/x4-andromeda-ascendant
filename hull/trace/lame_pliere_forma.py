# Iteration: the blade's shape nudged so it folds (asked: shape changed a little so they fold; iterate): for each blade's best fold
# (hinge, axis, turn) from lame_pliere_cauta.py, the stowed blade's cross rows that are not hidden are pulled towards the host arm's
# spine (the fraction raised 0.1 at a time until the row is hidden), the pulls smoothed along the blade (SM rows) and re-checked; the
# deployed blade = the nudged stowed one turned back. Prints the stowed exposure before / after and how far the deployed blade moved off
# the cleaned reference (mean / max). Writes piese/ghid_lama_<nr>_v2.npz (deployed rows) + _pliere.npz (hinge, axis, turn).
# Every candidate fold of the blade (the top ones from the search) is tried, keeping only the right opening sense (front set: tip to
# +y, back set: to -y); the chosen one = no row left exposed (or the fewest) with the smallest mean change of the deployed blade.
# Usage: blender -b <scene> --python lame_pliere_forma.py -- <linii.npz> <pliere.npy> <piese dir> ; env OPEN=0.3 LR=754 SM=15 IT=4
import bpy, sys, os, json, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; L = np.load(a[0]); BEST = np.load(a[1], allow_pickle=True); PD = a[2]
E = lambda k, d: float(os.environ.get(k, d)); X0 = -1600.0; OPEN, LR, SM, IT = E("OPEN", .3), E("LR", 754), E("SM", 15), int(E("IT", 4))
ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if o.type == "MESH" and not o.name.startswith("an_lama")]
V, F = [], []
for o in ship:
    k = len(V); V += [o.matrix_world @ v.co - Vector((X0, 0, 0)) for v in o.data.vertices]; F += [[k + i for i in p.vertices] for p in o.data.polygons]
T = BVHTree.FromPolygons(V, F); dirs = [Vector(d).normalized() for d in ((0, 0, 1), (0, 0, -1), (1, 0, 1), (-1, 0, 1), (0, 1, -1), (0, -1, -1))]
hid = lambda p: all(T.ray_cast(Vector(p) + d * .3, d, 4000)[0] is not None for d in dirs)
def line(obj, nm):
    o = bpy.data.objects[obj]; return np.array([o.matrix_world @ p.co.xyz for p in o.data.splines[json.loads(o["linii"]).index(nm)].points]) + [3100, 0, 0]
spines = {"fata": line("g_as_bf_sudat_S", "g_as_bf_spinare_brat_fata_S"), "spate": line("g_as_bo_sudat_S", "g_as_bo_spinare_brat_S")}
def dist(P): return np.mean([T.find_nearest(Vector(p), 2000)[3] for p in P[::10]])
def gsm(A, sig):
    r = int(3 * sig); k = np.exp(-.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum(); P = np.r_[np.repeat(A[:1], r, 0), A, np.repeat(A[-1:], r, 0)]
    return np.c_[[np.convolve(P[:, j], k, mode="valid") for j in range(A.shape[1])]].T
def axisv(name, up):
    if name == "vert": return np.array([0, 0, 1.])
    if name == "normala": return up / np.linalg.norm(up)
    az = math.radians(float(name.split("az")[1])); t = math.radians(20); return np.array([math.sin(t) * math.cos(az), math.sin(t) * math.sin(az), math.cos(t)])
def rot(ax, th):
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K
cands = {}
for r in BEST: cands.setdefault(r[0], []).append(r)
for nm in sorted({k.rsplit("_", 1)[0] for k in L.files}):
    tag = nm.split("_")[1]; st = "fata" if tag in ("007", "008") else "spate";
    mid, w, ac, nn = L[nm + "_mid"], L[nm + "_w"], L[nm + "_across"], L[nm + "_n"]
    e_a, e_b = mid + ac * (w / 2)[:, None], mid - ac * (w / 2)[:, None]
    wide, apex = (e_a, e_b) if dist(e_a) < dist(e_b) else (e_b, e_a)
    if dist(wide[:20]) > dist(wide[-20:]): wide, apex, w, nn = wide[::-1], apex[::-1], w[::-1], nn[::-1]
    up = nn.copy(); up[up[:, 2] < 0] *= -1
    Ms, Mj, Va = wide + up * (OPEN * w / 2)[:, None], wide - up * (OPEN * w / 2)[:, None], apex
    if st == "spate":
        Ln = np.linalg.norm(np.diff((Ms + Mj) / 2, axis=0), axis=1).sum(); r0 = (Ms[0] + Mj[0]) / 2; f = LR / Ln; Ms, Mj, Va = r0 + (Ms - r0) * f, r0 + (Mj - r0) * f, r0 + (Va - r0) * f
    RW = np.stack([Ms, Mj, Va], 1); sp = spines[st]; n = len(RW); results = []
    for b in cands[tag]:
      if (float(b[8]) > 0) != (st == "fata"): continue
      H = np.array([b[3], b[4], b[5]], float); axn, th = b[6], math.radians(float(b[7])); R = rot(axisv(axn, up[0]), th); stw = (RW - H) @ R.T + H
      def exposed_rows(S): return np.array([not all(hid(p) for p in np.r_[S[i], [(S[i, 0] + S[i, 2]) / 2, (S[i, 1] + S[i, 2]) / 2]]) for i in range(n)])
      ex0 = exposed_rows(stw); D = np.zeros((n, 3)); S = stw.copy()
      for it in range(IT):
          ex = exposed_rows(S)
          if not ex.any(): break
          for i in np.where(ex)[0]:
              c = S[i].mean(0); tgt = sp[np.argmin(np.linalg.norm(sp - c, axis=1))]
              for t in np.arange(.1, 1.01, .1):
                  if all(hid(p + (tgt - c) * t) for p in S[i]): break
              D[i] += (tgt - c) * t
          D = gsm(D, SM) * 1.15; S = stw + D[:, None, :]
      ex1 = exposed_rows(S)
      dep = (S - H) @ R + H                                                # turned back = the deployed rows
      dev = np.linalg.norm((dep - RW).reshape(-1, 3), axis=1); results.append((ex1.mean(), dev.mean(), dev.max(), ex0.mean(), H, axn, th, dep))
    results.sort(key=lambda q: (round(q[0], 2), q[1])); ex1m, devm, devx, ex0m, H, axn, th, dep = results[0]
    print("FORMA %s: %d variante incercate; aleasa: " % (tag, len(results)), end="")
    np.savez(os.path.join(PD, "ghid_lama_%s_v2.npz" % tag), lama_margine_sus=dep[:, 0], lama_margine_jos=dep[:, 1], lama_varf=dep[:, 2])
    np.savez(os.path.join(PD, "ghid_lama_%s_v2_pliere.npz" % tag), hinge=H, axis=axisv(axn, up[0]), turn=math.degrees(th))
    print("randuri expuse stransa %d%% -> %d%%; deschisa mutata fata de referinta curatata: medie %.1f m, max %.1f m; balama %s axa %s rotire %+.0f" % (100 * ex0m, 100 * ex1m, devm, devx, H.round(1), axn, math.degrees(th)))
