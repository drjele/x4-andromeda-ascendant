# Every blade hinged at point 7 (asked: hinge at 7 for all; the extended blades must look like the reference; if one turn is not
# enough, add moves - slide forward / back, turn about another axis, go down): the deployed blade = the cleaned reference (lying V;
# the back four scaled to LR) with its root extended smoothly to hinge 7 (inside PS); stowed = turned about an axis through 7 and then
# slid by t. Search: axes on a sphere (NA), turns 15..165 by 15 both senses, slides t from a small grid (TS) - rays up / down / 4
# obliques decide hidden. Prints per blade: best single turn (t = 0), best turn + slide, and which way the tip moves when opening.
# Usage: blender -b <scene> --python lame_7_cauta.py -- <linii.npz> <out.npy> <piese dir> ; env OPEN=0.3 LR=754 NA=60 STEP=8 TS="0,0,0;0,0,-30;0,-60,0;0,60,0;0,-60,-30;0,60,-30;-40,0,-30;40,0,-30"
import bpy, sys, os, json, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; L = np.load(a[0]); OUT, PD = a[1], a[2]; E = lambda k, d: float(os.environ.get(k, d)); X0 = -1600.0
OPEN, LR, NA, STEP = E("OPEN", .3), E("LR", 754), int(E("NA", 60)), int(E("STEP", 8))
TS = [np.array([float(q) for q in s.split(",")]) for s in os.environ.get("TS", "0,0,0;0,0,-30;0,-60,0;0,60,0;0,-60,-30;0,60,-30;-40,0,-30;40,0,-30").split(";")]
H = np.array([-59.6, 74.3, 292.7])
ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if o.type == "MESH" and not o.name.startswith("an_lama")]
V, F = [], []
for o in ship:
    k = len(V); V += [o.matrix_world @ v.co - Vector((X0, 0, 0)) for v in o.data.vertices]; F += [[k + i for i in p.vertices] for p in o.data.polygons]
T = BVHTree.FromPolygons(V, F); dirs = [Vector(d).normalized() for d in ((0, 0, 1), (0, 0, -1), (1, 0, 1), (-1, 0, 1), (0, 1, -1), (0, -1, -1))]
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
    W0 = (Ms[0] + Mj[0]) / 2; tg = (Ms[5] + Mj[5]) / 2 - W0; tg /= np.linalg.norm(tg); dL = np.linalg.norm(W0 - H)
    s = np.linspace(0, 1, max(int(dL), 2))[:-1]; h00, h10, h01, h11 = 2 * s**3 - 3 * s**2 + 1, s**3 - 2 * s**2 + s, -2 * s**3 + 3 * s**2, s**3 - s**2
    tg0 = W0 - H; tg0 /= np.linalg.norm(tg0)
    ext = np.outer(h00, H) + np.outer(h10, tg0 * dL) + np.outer(h01, W0) + np.outer(h11, tg * dL)    # root extended to 7 (Hermite)
    sw = s[:, None]; dMs, dMj, dVa = Ms[0] - W0, Mj[0] - W0, Va[0] - W0
    return np.r_[ext + dMs * sw, Ms], np.r_[ext + dMj * sw, Mj], np.r_[ext + dVa * sw, Va], len(ext)
def sphere(n):
    i = np.arange(n) + .5; ph = np.arccos(1 - i / n); th = math.pi * (1 + 5 ** .5) * i
    return np.c_[np.cos(th) * np.sin(ph), np.sin(th) * np.sin(ph), np.cos(ph)]    # upper hemisphere (turns both senses)
AX = sphere(NA); out = []
for nm in sorted({k.rsplit("_", 1)[0] for k in L.files}):
    tag = nm.split("_")[1]; Ms, Mj, Va, ne = rows(nm, tag)
    np.savez(os.path.join(PD, "ghid_lama_%s_v3.npz" % tag), lama_margine_sus=Ms, lama_margine_jos=Mj, lama_varf=Va)
    pts = np.r_[Ms, Mj, Va][::STEP]; pts = [Vector(p) for p in pts]; tip = Vector(Va[-1].tolist()); Hv = Vector(H.tolist())
    best1, best2 = (2, None), (2, None)
    for ax in AX:
        axv = Vector(ax.tolist())
        for th in list(range(15, 166, 15)) + list(range(-165, -14, 15)):
            M = Matrix.Translation(Hv) @ Matrix.Rotation(math.radians(th), 4, axv) @ Matrix.Translation(-Hv)
            Q = [M @ p for p in pts]
            for t in TS:
                tv = Vector(t.tolist()); lim = (best1[0] if not t.any() else best2[0]) * len(Q); e = 0   # (early stop against the right best: the single-turn best was underestimated before)
                for q in Q:
                    if any(T.ray_cast(q + tv + d * .3, d, 4000)[0] is None for d in dirs):
                        e += 1
                        if e > lim: break
                f = e / len(Q)
                if not t.any() and f < best1[0]: best1 = (f, (tuple(ax.round(3)), th, tuple(t)))
                if f < best2[0] and e <= best2[0] * len(Q): best2 = (f, (tuple(ax.round(3)), th, tuple(t)))
    dy = lambda b: (tip - (Matrix.Translation(Hv) @ Matrix.Rotation(math.radians(b[1]), 4, Vector(b[0])) @ Matrix.Translation(-Hv) @ tip + Vector(b[2]))).y
    print("L7 %s (%s, %d puncte, radacina prelungita %d m pana la 7): o rotire -> expus %.1f%% %s (deschiderea muta varful dy %+.0f); rotire + alunecare -> expus %.1f%% %s (dy %+.0f)"
          % (tag, "fata" if tag in ("007", "008") else "spate", len(pts), ne, 100 * best1[0], best1[1], dy(best1[1]), 100 * best2[0], best2[1], dy(best2[1])))
    out.append((tag, best1, best2))
np.save(OUT, np.array(out, dtype=object), allow_pickle=True)
