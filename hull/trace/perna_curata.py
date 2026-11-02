# A pad decoration on a top surface rebuilt with clean lines (asked: clean lines on the decorations; 055 had a shaky outline - from
# marching cubes - and its front end cut straight): footprint read from the current piece seen from above - along its main axis
# (PCA), per 2 m its centre and half width; centre = a polynomial (DEG), half width = a linear wedge from the narrow end then a
# half ellipse closing the wide end (fitted where to turn), the narrow end a small round tip; height per station = a quadratic fit
# of the old piece's. Every grid point dropped vertically onto the host; the top raised along the grid
# normal, H(u)*sqrt(1-v^2)*e(u) - SINK (rim SINK m inside the host, no
# step), closed with a bottom 1 m under. Left piece built, the right = its mirror in x.
# Usage: blender -b <scene> --python perna_curata.py -- <piece S> <host,...> <out npz> ; env DEG=3 SINK=0.15 DS=1 M=21
import bpy, sys, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; PIECE, HOSTS, OUT = a[0], a[1].split(","), a[2]; E = lambda k, d: float(os.environ.get(k, d))
DEG, SINK, DS, M = int(E("DEG", 3)), E("SINK", .15), E("DS", 1), int(E("M", 21))
sh = lambda o: [o.matrix_world @ v.co + Vector((1600, 0, 0)) for v in o.data.vertices]
HV, HF = [], []
for n in HOSTS:
    o = bpy.data.objects[n]; b = len(HV); HV += sh(o); HF += [[b + i for i in p.vertices] for p in o.data.polygons]
bvh = BVHTree.FromPolygons(HV, HF)
def drop(x, y):
    h = bvh.ray_cast(Vector((x, y, 3000.0)), Vector((0, 0, -1)))
    if h[0] is None: raise SystemExit("ray miss %.1f %.1f" % (x, y))
    return np.array(h[0])
P = np.array(sh(bpy.data.objects[PIECE])); c0 = P[:, :2].mean(0); X = P[:, :2] - c0
ev, evec = np.linalg.eigh(np.cov(X.T)); ax = evec[:, -1]; nx = np.array([-ax[1], ax[0]]); U = X @ ax; W = X @ nx
Ph = P[::3]; hgt_ = np.array([p[2] - drop(*p[:2])[2] for p in Ph]); Uh = (Ph[:, :2] - c0) @ ax; hgt = hgt_
rows = []
for b in np.arange(U.min(), U.max(), 2.0):
    m = (U >= b) & (U < b + 2)
    if m.sum() >= 3: rows.append((b + 1, W[m].min(), W[m].max()))
rows = np.array(rows); u0, u1 = U.min(), U.max()
print("PERNA veche: lunga %.1f m, lata %.1f .. %.1f m, inaltime peste gazda max %.2f m" % (u1 - u0, 2 * ((rows[:, 2] - rows[:, 1]) / 2).min(), (rows[:, 2] - rows[:, 1]).max(), hgt.max()))
uu = np.linspace(u0, u1, int((u1 - u0) / DS) + 1)
cen, hwr = (rows[:, 1] + rows[:, 2]) / 2, (rows[:, 2] - rows[:, 1]) / 2
ccen = np.polyfit(rows[:, 0], cen, DEG); cc = np.polyval(ccen, uu)
# half width = a wedge (linear) from the narrow end, then a half ellipse closing the wide end - both ends rounded, clean lines
wide_hi = hwr[rows[:, 0] > (u0 + u1) / 2].max() > hwr[rows[:, 0] < (u0 + u1) / 2].max()
us = rows[:, 0] if wide_hi else (u0 + u1) - rows[:, 0]; ua, ub = u0, u1     # us: 0 side = narrow end
def wedge(um, x):
    m = x < um; A_ = np.c_[np.ones(m.sum()), x[m] - ua]; c = np.linalg.lstsq(A_, hwr[m], rcond=None)[0]; hm = c[0] + c[1] * (um - ua)
    f = np.where(x < um, c[0] + c[1] * (x - ua), hm * np.sqrt(np.clip(1 - ((x - um) / (ub - um)) ** 2, 0, 1))); return f, c, hm
best = min(((np.abs(wedge(um, us)[0] - hwr).max(), um) for um in np.arange(ua + 20, ub - 5, 1.0)))
UM = best[1]; _, CW, HM = wedge(UM, us)
x = uu if wide_hi else (u0 + u1) - uu
hw = np.where(x < UM, CW[0] + CW[1] * (x - ua), HM * np.sqrt(np.clip(1 - ((x - UM) / (ub - UM)) ** 2, 0, 1)))
r0 = max(CW[0], 1.0); ef = np.where(x - ua < r0, np.sqrt(np.clip(1 - ((r0 - (x - ua)) / r0) ** 2, 0, 1)), 1.0)   # the narrow end's round tip
hw = np.maximum(hw, 0); ew = np.where(x < UM, 1.0, np.sqrt(np.clip(1 - ((x - UM) / (ub - UM)) ** 2, 0, 1)))   # the wide end's dome closes with it
hmax = np.array([max(hgt_[np.abs(Uh - r) < 1]) if (np.abs(Uh - r) < 1).any() else np.nan for r in rows[:, 0]]); ok = ~np.isnan(hmax)
ch = np.polyfit(rows[ok, 0], hmax[ok], 2); Hu = np.clip(np.polyval(ch, uu), 0, None)
print("FORMA: centru cubic (abatere max %.2f m); latime pana %.2f -> %.2f m pana la %.0f m de la capatul ingust, apoi semielipsa %.0f m (abatere max %.2f m); inaltime %.2f .. %.2f m"
      % (np.abs(np.polyval(ccen, rows[:, 0]) - cen).max(), CW[0], HM, UM - ua, ub - UM, best[0], Hu.min(), Hu.max()))
v = np.linspace(-1, 1, M); N = len(uu)
XY = c0 + uu[:, None, None] * ax + (cc[:, None] + hw[:, None] * ef[:, None] * v[None, :])[..., None] * nx
Pg = np.array([[drop(*XY[i, j]) for j in range(M)] for i in range(N)])
du = np.gradient(Pg, axis=0); dv = np.gradient(Pg, axis=1); n = np.cross(du, dv); n /= np.maximum(np.linalg.norm(n, axis=2), 1e-9)[..., None]
n[np.linalg.norm(np.cross(du, dv), axis=2) < 1e-9] = (0, 0, 1)
if n[..., 2].mean() < 0: n = -n
hh = Hu[:, None] * np.sqrt(ef * ew)[:, None] * np.sqrt(np.clip(1 - v ** 2, 0, 1))[None, :] - SINK
TOP = Pg + hh[..., None] * n; BOT = Pg - 1.0 * n
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
np.savez(OUT, v_S=V, v_D=V * [-1, 1, 1], f=F, f_D=F[:, ::-1])
print("PERNA noua: lunga %.1f m, lata max %.1f m, inaltime max %.2f m, capete rotunde; %d v, %d f; muchii libere %d, ne-manifold %d"
      % (u1 - u0, 2 * hw.max(), Hu.max(), len(V), len(F), int((c_ == 1).sum()), int((c_ > 2).sum())))
