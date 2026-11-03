# Blades stowed inside the front arm, deployed like tram doors (asked: front and back blades hinged about the same place, never
# intersecting; they come down out from under the front arms, then move into place by sliding forward and turning - like tram /
# train doors). Deployed = the cleaned reference blade (lying V, back four at LR). Stowed = a rigid placement fitting the blade's
# middle line onto a stretch of the front-arm spine (Kabsch, both directions, start every DS m), lowered/raised by a stack offset ZK
# so the blades do not overlap; the best = most hidden (rays up / down / 4 obliques hit the ship) with no overlap with the blades
# already placed (BVH overlap). Writes piese/ghid_lama_<nr>_v5.npz (deployed rows) + _v5_usa.npz (stowed 4x4, drop DZ).
# Usage: blender -b <scene> --python lame_usa_tren.py -- <linii.npz> <piese dir> ; env OPEN=0.3 LR=754 DS=40 ZK="0,-14,14,-28,28" ORDER=007,008,010,009,014,013
import bpy, sys, os, json, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; L = np.load(a[0]); PD = a[1]; E = lambda k, d: float(os.environ.get(k, d)); X0 = -1600.0
OPEN, LR, DS = E("OPEN", .3), E("LR", 754), E("DS", 40); ZK = [float(q) for q in os.environ.get("ZK", "0,-14,14,-28,28").split(",")]
ORDER = os.environ.get("ORDER", "007,008,010,009,014,013").split(",")
ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if o.type == "MESH" and not o.name.startswith("an_lama")]
V, F = [], []
for o in ship:
    k = len(V); V += [o.matrix_world @ v.co - Vector((X0, 0, 0)) for v in o.data.vertices]; F += [[k + i for i in p.vertices] for p in o.data.polygons]
T = BVHTree.FromPolygons(V, F); dirs = [Vector(d).normalized() for d in ((0, 0, 1), (0, 0, -1), (1, 0, 1), (-1, 0, 1), (0, 1, -1), (0, -1, -1))]
o = bpy.data.objects["g_as_bf_sudat_S"]; Sp = np.array([o.matrix_world @ p.co.xyz for p in o.data.splines[json.loads(o["linii"]).index("g_as_bf_spinare_brat_fata_S")].points]) + [3100, 0, 0]
dS = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Sp, axis=0), axis=1))]; spat = lambda s: np.c_[[np.interp(s, dS, Sp[:, k]) for k in range(3)]].T
def dist(P): return np.mean([T.find_nearest(Vector(p), 2000)[3] for p in P[::10]])
def rows(nm, tag):
    mid, w, ac, nn = L[nm + "_mid"], L[nm + "_w"], L[nm + "_across"], L[nm + "_n"]
    e_a, e_b = mid + ac * (w / 2)[:, None], mid - ac * (w / 2)[:, None]
    wide, apex = (e_a, e_b) if dist(e_a) < dist(e_b) else (e_b, e_a)
    if dist(wide[:20]) > dist(wide[-20:]): wide, apex, w, nn = wide[::-1], apex[::-1], w[::-1], nn[::-1]
    up = nn.copy(); up[up[:, 2] < 0] *= -1
    Ms, Mj, Va = wide + up * (OPEN * w / 2)[:, None], wide - up * (OPEN * w / 2)[:, None], apex
    if tag not in ("007", "008"):
        Ln = np.linalg.norm(np.diff((Ms + Mj) / 2, axis=0), axis=1).sum(); r0 = (Ms[0] + Mj[0]) / 2; f = LR / Ln; Ms, Mj, Va = r0 + (Ms - r0) * f, r0 + (Mj - r0) * f, r0 + (Va - r0) * f
    return Ms, Mj, Va
def kabsch(A, B):                                                         # R, t minimising |R A + t - B|
    ca, cb = A.mean(0), B.mean(0); U, _, Vt = np.linalg.svd((A - ca).T @ (B - cb)); d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T; return R, cb - R @ ca
def tri_bvh(P):                                                           # blade surface from its rows (for overlap tests)
    n = len(P); m = 3; verts = [Vector(p) for p in P.reshape(-1, 3)]; faces = []
    for i in range(n - 1):
        for j in range(m): faces.append([i * m + j, i * m + (j + 1) % m, (i + 1) * m + (j + 1) % m, (i + 1) * m + j])
    return BVHTree.FromPolygons(verts, faces)
placed = []; tags = {k.rsplit("_", 1)[0].split("_")[1]: k.rsplit("_", 1)[0] for k in L.files}
for tag in ORDER:
    Ms, Mj, Va = rows(tags[tag], tag); RW = np.stack([Ms, Mj, Va], 1); mid = (Ms + Mj + Va) / 3; dm = np.r_[0, np.cumsum(np.linalg.norm(np.diff(mid, axis=0), axis=1))]
    pts = RW.reshape(-1, 3)[::6]; best = None
    for s0 in np.arange(0, dS[-1] - dm[-1], DS):
        tgt = spat(s0 + dm)
        for rev in (False, True):
            A = mid if not rev else mid[::-1]
            R, t = kabsch(A[::5], tgt[::5])
            for zk in ZK:
                M = lambda P: P @ R.T + t + [0, 0, zk]
                Q = M(pts); e = sum(1 for q in Q if any(T.ray_cast(Vector(q) + d * .3, d, 4000)[0] is None for d in dirs)) / len(Q)
                if best is not None and e > best[0] + .02: continue
                bt = tri_bvh(M(RW)); ov = sum(len(bt.overlap(pb)) for pb in placed)
                key = (ov > 0, e)
                if best is None or key < (best[1] > 0, best[0]): best = (e, ov, s0, rev, zk, R, t)
    e, ov, s0, rev, zk, R, t = best; Mx = np.eye(4); Mx[:3, :3] = R; Mx[:3, 3] = t + [0, 0, zk]
    stw = RW @ R.T + t + [0, 0, zk]; placed.append(tri_bvh(stw))
    need = []                                                             # per point: down to below the last ship surface under it
    for q in stw.reshape(-1, 3)[::4]:
        p, lastz = Vector(q), None
        for _ in range(20):
            h = T.ray_cast(p, Vector((0, 0, -1)), 400)
            if h[0] is None: break
            lastz = h[0].z; p = h[0] - Vector((0, 0, .01))
            if q[2] - lastz > 120: break
        need.append(q[2] - lastz if lastz is not None else 0)
    drop = float(max(need) + (stw[:, :, 2].max() - stw[:, :, 2].min()) * 0 + 15)
    np.savez(os.path.join(PD, "ghid_lama_%s_v5.npz" % tag), lama_margine_sus=Ms, lama_margine_jos=Mj, lama_varf=Va)
    np.savez(os.path.join(PD, "ghid_lama_%s_v5_usa.npz" % tag), stowed=Mx, drop=drop)
    print("USA %s: stransa pe spinarea bratului din fata de la %.0f m (%s), etaj %+.0f m -> expus %.1f%%, suprapuneri cu lamele deja puse %d; coborare %.0f m" % (tag, s0, "inversata" if rev else "in sens", zk, 100 * e, ov, drop))
