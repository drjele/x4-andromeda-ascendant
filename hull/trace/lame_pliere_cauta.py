# Iteration search for the blades' fold (asked: blades = the reference ones cleaned; front set 007/008 open forward, back set
# 009/010/013/014 open backward; the back four equal in length; iterate until they animate right): the deployed blade = the cleaned
# reference (lame_ref_linii.py + lying V as in lame_toate.py; the back set scaled about its root to the same length LR); for hinges on
# the host arm's spine (front set: g_as_bf_spinare_brat_fata_S, back set: g_as_bo_spinare_brat_S; every HS m over the first HL m),
# axes (vertical, 20 deg tilted towards 4 azimuths, the blade normal) and turns (-90..90 by 10), the blade turned back (stowed) and
# its points tested by rays (up / down / 4 obliques must all hit the ship = hidden). Prints per blade the best few, with which way the
# tip moves when opening (dy > 0 = towards +y). Writes <out.npz> with the best per blade.
# Usage: blender -b <scene> --python lame_pliere_cauta.py -- <linii.npz> <out.npz> ; env OPEN=0.3 LR=754 HS=25 HLF=600 HLB=800 STEP=6
import bpy, sys, os, json, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; L = np.load(a[0]); OUT = a[1]; E = lambda k, d: float(os.environ.get(k, d)); X0 = -1600.0
OPEN, LR, HS, STEP = E("OPEN", .3), E("LR", 754), E("HS", 25), int(E("STEP", 6))
ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if o.type == "MESH" and not o.name.startswith("an_lama")]
V, F = [], []
for o in ship:
    k = len(V); V += [o.matrix_world @ v.co - Vector((X0, 0, 0)) for v in o.data.vertices]; F += [[k + i for i in p.vertices] for p in o.data.polygons]
T = BVHTree.FromPolygons(V, F); dirs = [Vector(d).normalized() for d in ((0, 0, 1), (0, 0, -1), (1, 0, 1), (-1, 0, 1), (0, 1, -1), (0, -1, -1))]
def line(obj, nm):
    o = bpy.data.objects[obj]; return np.array([o.matrix_world @ p.co.xyz for p in o.data.splines[json.loads(o["linii"]).index(nm)].points]) + [3100, 0, 0]
spines = {"fata": line("g_as_bf_sudat_S", "g_as_bf_spinare_brat_fata_S"), "spate": line("g_as_bo_sudat_S", "g_as_bo_spinare_brat_S")}
def dist(P): return np.mean([T.find_nearest(Vector(p), 2000)[3] for p in P[::10]])
def blade(nm):
    mid, w, ac, nn = L[nm + "_mid"], L[nm + "_w"], L[nm + "_across"], L[nm + "_n"]
    e_a, e_b = mid + ac * (w / 2)[:, None], mid - ac * (w / 2)[:, None]
    wide, apex = (e_a, e_b) if dist(e_a) < dist(e_b) else (e_b, e_a)
    if dist(wide[:20]) > dist(wide[-20:]): wide, apex, w, nn = wide[::-1], apex[::-1], w[::-1], nn[::-1]
    up = nn.copy(); up[up[:, 2] < 0] *= -1
    Ms, Mj = wide + up * (OPEN * w / 2)[:, None], wide - up * (OPEN * w / 2)[:, None]
    return Ms, Mj, apex, up[0]
res = {}
for nm in sorted({k.rsplit("_", 1)[0] for k in L.files}):
    tag = nm.split("_")[1]; st = "fata" if tag in ("007", "008") else "spate"
    Ms, Mj, Va, up = blade(nm)
    if st == "spate":                                                     # the back four: the same length, scaled about the root
        Ln = np.linalg.norm(np.diff((Ms + Mj) / 2, axis=0), axis=1).sum(); r0 = (Ms[0] + Mj[0]) / 2; f = LR / Ln
        Ms, Mj, Va = r0 + (Ms - r0) * f, r0 + (Mj - r0) * f, r0 + (Va - r0) * f
    pts = [Vector(p) for p in np.r_[Ms, Mj, Va][::STEP]]; tip = Vector(Va[-1].tolist())
    sp = spines[st]; d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(sp, axis=0), axis=1))]; HL = E("HLF", 600) if st == "fata" else E("HLB", 800)
    hinges = [sp[np.searchsorted(d, s)] for s in np.arange(0, HL, HS)]
    axes = [("vert", Vector((0, 0, 1))), ("normala", Vector(up.tolist()).normalized())] + [("t20_az%d" % az, Vector((math.sin(math.radians(20)) * math.cos(math.radians(az)), math.sin(math.radians(20)) * math.sin(math.radians(az)), math.cos(math.radians(20))))) for az in (0, 90, 180, 270)]
    rows = []
    for hi, H in enumerate(hinges):
        Hv = Vector(H.tolist())
        for axn, ax in axes:
            for th in range(-90, 91, 10):
                if th == 0: continue
                M = Matrix.Translation(Hv) @ Matrix.Rotation(math.radians(th), 4, ax) @ Matrix.Translation(-Hv)      # stowed = turned by th
                e = sum(1 for p in pts if any(T.ray_cast(M @ p + dd * .3, dd, 4000)[0] is None for dd in dirs)) / len(pts)
                rows.append((e, hi * HS, tuple(np.round(H, 1)), axn, th, (tip - M @ tip).y))
    rows.sort(key=lambda r: r[0]); res[tag] = rows[:10]
    print("PLIERE %s (set %s, %d puncte): cele mai bune:" % (tag, st, len(pts)))
    for r in rows[:5]: print("   expus %5.1f%% | balama la %4d m pe spinare %s | axa %-9s rotire %+4d | deschiderea muta varful dy %+.0f m" % (100 * r[0], r[1], r[2], r[3], r[4], r[5]))
np.save(OUT, np.array([(t, *r[:2], *r[2], r[3], r[4], r[5]) for t, rr in res.items() for r in rr], dtype=object), allow_pickle=True)
