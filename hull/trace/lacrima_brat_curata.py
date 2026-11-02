# The arm teardrop rebuilt with clean lines (asked: clean lines on the decorations, one at a time; measured before: wavy outline,
# a 1 m step at the edge): it sits on the front arm's tip, where the arm drops steeply, so it is laid on the arm's TUBE, not dropped
# from above. Footprint read from the current teardrop: per 5 m of the arm spine, its centre angle around the spine and its half
# width (arc); the centre angle = flat, one quintic smoothstep turn, flat (+ a small slope) - clean line, fitted, the width = the teardrop formula of lacrima_pe_brat.py
# (thin tail, round head at the tip end) with the measured max. Every grid point = a ray from the spine outward at that angle onto
# the arm, so the outline lies exactly on the arm; the top raised H m along the grid normal, H*sqrt(1-u^2)*g(t) - SINK: the rim
# SINK m inside the arm (flush on it the edge zigzags with the arm's facets), no step; closed with a bottom 1 m inside. Left side built, the right = its mirror in x.
# Usage: blender -b <scene.blend> --python lacrima_brat_curata.py -- <out npz> ; env H=3 N=480 M=17 SINK=0.15 HEAD=0.18 WMIN=0.5
import bpy, sys, os, json, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]; E = lambda k, d: float(os.environ.get(k, d))
H, N, M, HD, WMIN, SINK = E("H", 3), int(E("N", 480)), int(E("M", 17)), E("HEAD", .18), E("WMIN", .5), E("SINK", .15)
g = bpy.data.objects["g_as_bf_sudat_S"]; sp = g.data.splines[json.loads(g["linii"]).index("g_as_bf_spinare_brat_fata_S")]
SP = np.array([g.matrix_world @ p.co.xyz + Vector((3100, 0, 0)) for p in sp.points])
ds = np.r_[0, np.cumsum(np.linalg.norm(np.diff(SP, axis=0), axis=1))]
arm = bpy.data.objects["an_brat_fata_S"]; AV = [arm.matrix_world @ v.co + Vector((1600, 0, 0)) for v in arm.data.vertices]
bvh = BVHTree.FromPolygons(AV, [list(p.vertices) for p in arm.data.polygons])
lac = bpy.data.objects["an_lacrima_brat_S"]; LV = np.array([lac.matrix_world @ v.co + Vector((1600, 0, 0)) for v in lac.data.vertices])
def frame(s):                                                          # spine point, tangent, "up" and "side" around it
    P = np.array([np.interp(s, ds, SP[:, k]) for k in range(3)])
    T = np.array([np.interp(s + 2, ds, SP[:, k]) for k in range(3)]) - np.array([np.interp(s - 2, ds, SP[:, k]) for k in range(3)]); T /= np.linalg.norm(T)
    up = np.array([0, 0, 1.]) - T[2] * T; up /= np.linalg.norm(up); return P, T, up, np.cross(T, up)
# footprint of the current teardrop, around the spine
dense = np.linspace(0, ds[-1], int(ds[-1] / .5)); DP = np.array([[np.interp(s, ds, SP[:, k]) for k in range(3)] for s in dense])
sL = dense[np.argmin(((LV[:, None, :] - DP[None, ::4, :]) ** 2).sum(2), axis=1) * 4]
rows = []
for b in np.arange(sL.min(), sL.max(), 5.0):
    m = (sL >= b) & (sL < b + 5)
    if m.sum() < 4: continue
    P, T, up, sd = frame(b + 2.5); R = LV[m] - P; ang = np.arctan2(R @ sd, R @ up); rad = np.linalg.norm(R - np.outer(R @ T, T), axis=1)
    rows.append((b + 2.5, (ang.max() + ang.min()) / 2, (ang.max() - ang.min()) / 2 * rad.mean()))
rows = np.array(rows); s0, s1 = sL.min(), sL.max()
def sstep(x): x = np.clip(x, 0, 1); return x * x * x * (x * (6 * x - 15) + 10)      # quintic smoothstep
best = None                                                            # centre angle = a + b*s + D*smoothstep((s - sa)/L): flat, one smooth turn, flat
for sa in np.arange(s0, s1, 5.0):
    for Lt in np.arange(40, 400, 5.0):
        A_ = np.c_[np.ones(len(rows)), rows[:, 0] - s0, sstep((rows[:, 0] - sa) / Lt)]; c = np.linalg.lstsq(A_, rows[:, 1], rcond=None)[0]
        r_ = np.abs(A_ @ c - rows[:, 1]) * rows[:, 2] / np.maximum(rows[:, 2], 1)
        if best is None or r_.max() < best[0]: best = (r_.max(), sa, Lt, c)
_, SA, LT, CC = best
phi = lambda s: CC[0] + CC[1] * (np.asarray(s) - s0) + CC[2] * sstep((np.asarray(s) - SA) / LT)
print("UNGHI centru: trecere s %.0f .. %.0f (%.0f m), rotire %.1f grade, panta %.3f grade/100 m" % (SA, SA + LT, LT, np.degrees(CC[2]), np.degrees(CC[1]) * 100))
res = np.degrees(np.abs(phi(rows[:, 0]) - rows[:, 1]))
print("LACRIMA veche: s %.0f .. %.0f m pe spinare (%.0f m), unghi centru %.1f .. %.1f grade, abatere fit %.2f grade (max), semilatime max %.1f m"
      % (s0, s1, s1 - s0, np.degrees(rows[:, 1].min()), np.degrees(rows[:, 1].max()), res.max(), rows[:, 2].max()))
for r_, e_ in zip(rows, phi(rows[:, 0]) - rows[:, 1]):
    if int(r_[0]) % 30 < 5: print("  s %5.0f  unghi %6.1f  abatere %5.1f grade (%4.1f m)  semilatime %4.1f" % (r_[0], np.degrees(r_[1]), np.degrees(e_), abs(e_) * 30, r_[2]))
headtip = abs(s1 - ds[-1]) < abs(s0 - ds[-1])                           # the round head at the end nearer the arm tip
t = np.linspace(0, 1, N); WM = rows[:, 2].max()
w = np.where(t < 1 - HD, WM * np.sin(.5 * np.pi * np.clip(t / (1 - HD), 0, 1)) ** .8, WM * np.sqrt(np.clip(1 - ((t - (1 - HD)) / HD) ** 2, 0, 1)))
w = np.maximum(w, WMIN); ss = s0 + (s1 - s0) * (t if headtip else 1 - t)
wold = np.interp(ss, rows[:, 0], rows[:, 2]); print("LATIME noua fata de veche: medie %.2f m, max %.2f m" % (np.abs(w - wold).mean(), np.abs(w - wold).max()))
u = np.linspace(-1, 1, M); Pg = np.zeros((N, M, 3))
def cast(P, d):
    h = bvh.ray_cast(Vector(P), Vector(d), 500.0)
    if h[0] is None: raise SystemExit("ray miss s %.1f" % s)
    return np.array(h[0])
for i, s in enumerate(ss):
    P, T, up, sd = frame(s); a0 = float(phi(s))
    rr = np.linalg.norm(cast(P, np.cos(a0) * up + np.sin(a0) * sd) - P)
    for j, uu in enumerate(u):
        a = a0 + uu * w[i] / rr; Pg[i, j] = cast(P, np.cos(a) * up + np.sin(a) * sd)
du = np.gradient(Pg, axis=0); dv = np.gradient(Pg, axis=1); n = np.cross(du, dv); n /= np.linalg.norm(n, axis=2)[..., None]
Pc = np.array([frame(s)[0] for s in ss]); 
if (np.einsum("ijk,ijk->ij", n, Pg - Pc[:, None, :]) < 0).mean() > .5: n = -n
gt = np.sin(np.pi * t) ** .3; hgt = H * gt[:, None] * np.sqrt(np.clip(1 - u ** 2, 0, 1))[None, :] - SINK   # the rim SINK m inside the arm: the seen edge = a clean cut with it
TOP = Pg + hgt[..., None] * n; BOT = Pg - 1.0 * n
ni, nj = N, M; V = np.r_[TOP.reshape(-1, 3), BOT.reshape(-1, 3)]; off = ni * nj; F = []
for i in range(ni - 1):
    for j in range(nj - 1):
        p = i * nj + j; F += [[p, p + nj, p + nj + 1], [p, p + nj + 1, p + 1]]; q = off + p; F += [[q, q + nj + 1, q + nj], [q, q + 1, q + nj + 1]]
ring = [i * nj for i in range(ni)] + [(ni - 1) * nj + j for j in range(1, nj)] + [i * nj + nj - 1 for i in range(ni - 2, -1, -1)] + [j for j in range(nj - 2, 0, -1)]
for k in range(len(ring)):
    p0, p1 = ring[k], ring[(k + 1) % len(ring)]; F += [[p1, p0, off + p0], [p1, off + p0, off + p1]]
F = np.array(F)
if np.einsum("ij,ij->i", V[F[:, 0]], np.cross(V[F[:, 1]], V[F[:, 2]])).sum() < 0: F = F[:, ::-1]
e_, c_ = np.unique(np.sort(np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], axis=1), axis=0, return_counts=True)
oc = np.array([np.linalg.norm(np.array(bvh.find_nearest(Vector(p))[0]) - p) for p in np.r_[Pg[:, 0], Pg[:, -1]]])
L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pg[:, M // 2], axis=0), axis=1))]
np.savez(OUT, v_S=V, v_D=V * [-1, 1, 1], f=F, f_D=F[:, ::-1], contur_S=np.r_[Pg[:, 0], Pg[::-1, -1]])
print("LACRIMA noua: lunga %.0f m, lata max %.1f m, bombata %.1f m; %d v, %d f; muchii libere %d, ne-manifold %d; contur pe brat max %.3f m"
      % (L[-1], 2 * WM, H, len(V), len(F), int((c_ == 1).sum()), int((c_ > 2).sum()), oc.max()))
