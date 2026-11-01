# A clean trapezoid panel bent along the front arm (asked: R060 bent, longer, following the arm, centred on it seen from above, same
# trapezoid, clean lines): the arm's middle seen from above (centre of its silhouette per spine station, fitted by a quadratic offset
# from the spine), the panel = s in [S0, S0+LEN] along it, half-width linear WA/2 -> WB/2, ends square to the middle; every grid point
# dropped vertically onto the arm, the top raised H m along the grid's own normal (smoothstep to 0 over BEV m at the outline, so the
# outline sits exactly on the arm), closed with a bottom 1 m under. Left arm computed, the right one = its mirror in x.
# Usage: blender -b --python panou_pe_brat.py -- <arm npz (brat_fata_S__v/f, ship coords)> <guides npz> <out npz>
#        env S0=126 LEN=390 WA=125 WB=113 H=3 BEV=4 DS=2 M=31
#        env MARG=<m>: the panel's sides follow the arm's outline seen from above at MARG m from each edge (asked: follow the
#        contour of the arm, constant distance from the edges - no longer a trapezoid); edges = cubic fits, so the lines stay clean
import bpy, sys, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; A = np.load(a[0]); G = np.load(a[1]); OUT = a[2]
E = lambda k, d: float(os.environ.get(k, d))
S0, LEN, WA, WB, H, BEV, DS, M = E("S0", 126), E("LEN", 390), E("WA", 125), E("WB", 113), E("H", 3), E("BEV", 4), E("DS", 2), int(E("M", 31))
AV, AF = A["brat_fata_S__v"], A["brat_fata_S__f"]
bvh = BVHTree.FromPolygons([Vector(p) for p in AV], AF.tolist())
S = G["spinare_brat_fata_S"][:, :2]
seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))]
T = np.gradient(S, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]; N = np.c_[-T[:, 1], T[:, 0]]
# silhouette middle from above, per station
st = []
for s in np.arange(S0 - 20, S0 + LEN + 20, 10):
    j = np.searchsorted(seg, s); j = min(j, len(S) - 1)
    d = AV[:, :2] - S[j]; along = d @ T[j]; m = np.abs(along) < 3
    t = d[m] @ N[j]; st.append((s, (t.min() + t.max()) / 2))
st = np.array(st); cq = np.polyfit(st[:, 0], st[:, 1], 2)
print("mijloc de sus: offset fata de spinare %.1f .. %.1f m, abatere fit max %.2f" % (st[:, 1].min(), st[:, 1].max(), np.abs(np.polyval(cq, st[:, 0]) - st[:, 1]).max()))
def mid(s):
    x = np.interp(s, seg, S[:, 0]); y = np.interp(s, seg, S[:, 1])
    tx = np.interp(s, seg, T[:, 0]); ty = np.interp(s, seg, T[:, 1]); n = np.c_[-ty, tx] / np.hypot(tx, ty)[:, None]
    return np.c_[x, y] + np.polyval(cq, s)[:, None] * n, n
ss = np.linspace(S0, S0 + LEN, int(round(LEN / DS)) + 1)
tt = np.linspace(-1, 1, M)
MARG = os.environ.get("MARG")
if MARG is None:
    C, Nc = mid(ss)
    u = (ss - S0) / LEN; half = (WA + (WB - WA) * u) / 2
    XY = C[:, None, :] + (half[:, None] * tt[None, :])[..., None] * Nc[:, None, :]
else:
    MARG = float(MARG); ed = []
    for s_ in np.arange(S0 - 10, S0 + LEN + 10.1, 5):
        j = min(np.searchsorted(seg, s_), len(S) - 1); d = AV[:, :2] - S[j]; m = np.abs(d @ T[j]) < 3; t = d[m] @ N[j]; ed.append((s_, t.min(), t.max()))
    ed = np.array(ed); clo, chi = np.polyfit(ed[:, 0], ed[:, 1], 3), np.polyfit(ed[:, 0], ed[:, 2], 3)
    print("margini brat: abatere fit max %.2f / %.2f m, latime brat %.0f .. %.0f m" % (np.abs(np.polyval(clo, ed[:, 0]) - ed[:, 1]).max(), np.abs(np.polyval(chi, ed[:, 0]) - ed[:, 2]).max(), (ed[:, 2] - ed[:, 1]).min(), (ed[:, 2] - ed[:, 1]).max()))
    lo, hi = np.polyval(clo, ss) + MARG, np.polyval(chi, ss) - MARG; half = (hi - lo) / 2
    x_ = np.interp(ss, seg, S[:, 0]); y_ = np.interp(ss, seg, S[:, 1]); tx = np.interp(ss, seg, T[:, 0]); ty = np.interp(ss, seg, T[:, 1])
    Nc = np.c_[-ty, tx] / np.hypot(tx, ty)[:, None]; off_ = lo[:, None] + (hi - lo)[:, None] * (tt[None, :] + 1) / 2
    XY = np.c_[x_, y_][:, None, :] + off_[..., None] * Nc[:, None, :]; C = XY[:, M // 2]
    print("panou: latime %.0f .. %.0f m, margine %.1f m" % (2 * half.min(), 2 * half.max(), MARG))
P = np.zeros((len(ss), M, 3))
for i in range(len(ss)):
    for j in range(M):
        hit = bvh.ray_cast(Vector((XY[i, j, 0], XY[i, j, 1], 2000.0)), Vector((0, 0, -1)))
        if hit[0] is None: raise SystemExit("ray miss at s %.1f t %.2f" % (ss[i], tt[j]))
        P[i, j] = hit[0]
du = np.gradient(P, axis=0); dv = np.gradient(P, axis=1); n = np.cross(dv, du); n /= np.linalg.norm(n, axis=2)[..., None]
if n[..., 2].mean() < 0: n = -n
# distance to the outline (m): across = half*(1-|t|), along = to either end
dist = np.minimum(half[:, None] * (1 - np.abs(tt[None, :])), np.minimum(ss - S0, S0 + LEN - ss)[:, None])
x = np.clip(dist / BEV, 0, 1); hgt = H * x * x * (3 - 2 * x)
TOP = P + hgt[..., None] * n; BOT = P - 1.0 * n
ni, nj = TOP.shape[:2]; V = np.r_[TOP.reshape(-1, 3), BOT.reshape(-1, 3)]; off = ni * nj
F = []
for i in range(ni - 1):
    for j in range(nj - 1):
        p = i * nj + j; F += [[p, p + nj, p + nj + 1], [p, p + nj + 1, p + 1]]
        q = off + p; F += [[q, q + nj + 1, q + nj], [q, q + 1, q + nj + 1]]
ring = [i * nj for i in range(ni)] + [(ni - 1) * nj + j for j in range(1, nj)] + [i * nj + nj - 1 for i in range(ni - 2, -1, -1)] + [j for j in range(nj - 2, 0, -1)]
for k in range(len(ring)):
    p0, p1 = ring[k], ring[(k + 1) % len(ring)]; F += [[p1, p0, off + p0], [p1, off + p0, off + p1]]
F = np.array(F)
# orient outward: signed volume positive
vol = np.einsum("ij,ij->i", V[F[:, 0]], np.cross(V[F[:, 1]], V[F[:, 2]])).sum()
if vol < 0: F = F[:, ::-1]
VD = V * [-1, 1, 1];
np.savez(OUT, v_S=V, v_D=VD, f=F, f_D=F[:, ::-1], contur_S=P[[*range(ni)], 0], mijloc_S=np.c_[C, P[:, nj // 2, 2]])
print("panou: %d x %d, %d v, %d f, lungime %.0f m, latimi %.0f -> %.0f m, H %.1f m" % (ni, nj, len(V), len(F), LEN, WA, WB, H))
