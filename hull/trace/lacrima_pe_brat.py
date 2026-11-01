# A teardrop decoration on the arm (asked: R031 012_S's equivalent on the new ship = a mix of R031 012_S and R100 001_S, teardrop
# shaped like the other decorations, sitting on the new pieces' surface): its path = the two details (already moved onto our arm)
# binned along the arm's spine and smoothed, kept on the surface; its width from the details' own spread (the widest = WMAX); the
# outline a teardrop - round head at the tip end, thin tail; the body bulged by H m (zero at the outline), LIFT m above the surface;
# closed (a flat bottom 1 m under the surface, joined at the outline). Left arm computed, the right mirrored.
# Usage: python lacrima_pe_brat.py <details npz (keys v_S ...)> <arm npz (brat_fata_S__v/f)> <guides npz> <out npz> ; env H=3 LIFT=0.4 N=220 M=17 HEAD=0.18
import sys, os, numpy as np, trimesh
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d
e = lambda k, d: float(os.environ.get(k, d)); OUT = sys.argv[4]
DV = np.vstack([np.load(p)["v_S"] for p in sys.argv[1].split(",")]); A = np.load(sys.argv[2]); G = np.load(sys.argv[3])
arm = trimesh.Trimesh(A["brat_fata_S__v"], A["brat_fata_S__f"], process=False); AV = arm.vertices; AN = arm.vertex_normals.copy()
SP = G["spinare_brat_fata_S"]; ks = cKDTree(SP); o_ = AV - SP[ks.query(AV)[1]]; AN[np.einsum("ij,ij->i", o_, AN) < 0] *= -1; ka = cKDTree(AV)
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]; dS = arclen(SP)
sD = dS[ks.query(DV)[1]]; bins = np.arange(sD.min(), sD.max() + 5, 5.0); C, Wd = [], []
for a, b in zip(bins[:-1], bins[1:]):
    m = (sD >= a) & (sD < b)
    if m.sum() < 3: continue
    c = DV[m].mean(0); C.append(c); Wd.append(np.linalg.norm(DV[m] - c, axis=1).max())
C = np.array(C); C = np.c_[[gaussian_filter1d(C[:, k], 3, mode="nearest") for k in range(3)]].T
def onsurf(P):                                                             # (points put on the arm's surface: nearest vertex, its plane)
    i = ka.query(P)[1]; return P - AN[i] * np.einsum("ij,ij->i", P - AV[i], AN[i])[:, None], AN[i]
d = arclen(C); N, M = int(e("N", "220")), int(e("M", "17")); t = np.linspace(0, 1, N)
Pc = np.c_[[np.interp(t * d[-1], d, C[:, k]) for k in range(3)]].T; Pc, Nc = onsurf(Pc)
if np.linalg.norm(Pc[0] - SP[-1]) < np.linalg.norm(Pc[-1] - SP[-1]): Pc, Nc = Pc[::-1], Nc[::-1]   # (t = 0 the tail, t = 1 the head at the tip end)
Tg = np.gradient(Pc, axis=0); Tg /= np.linalg.norm(Tg, axis=1)[:, None]; Bn = np.cross(Nc, Tg); Bn /= np.linalg.norm(Bn, axis=1)[:, None]
WM = float(os.environ.get("WMAX", "0")) or 0.9 * np.max(Wd); HD = e("HEAD", "0.18"); WMIN = e("WMIN", "0.5")   # (WMIN: the ends never collapse to a point)
w = np.where(t < 1 - HD, WM * np.sin(0.5 * np.pi * np.clip(t / (1 - HD), 0, 1)) ** 0.8, WM * np.sqrt(np.clip(1 - ((t - (1 - HD)) / HD) ** 2, 0, 1)))
w = np.maximum(w, WMIN); u = np.linspace(-1, 1, M); H, LI = e("H", "3"), e("LIFT", "0.4")
top, bot = [], []
for k in range(N):
    Q = Pc[k] + np.outer(u * w[k], Bn[k]); Q, Nq = onsurf(Q)
    g = np.sin(np.pi * np.clip(t[k], 0, 1)) ** 0.3
    top.append(Q + Nq * (LI + H * g * np.sqrt(np.clip(1 - u ** 2, 0, 1)))[:, None]); bot.append(Q - Nq * 1.0)
T_, B_ = np.array(top), np.array(bot); V = np.vstack([T_.reshape(-1, 3), B_.reshape(-1, 3)]); nb = N * M; F = []
for r in range(N - 1):
    for j in range(M - 1):
        a, b, c, dd = r * M + j, r * M + j + 1, (r + 1) * M + j + 1, (r + 1) * M + j
        F += [[a, b, c], [a, c, dd], [nb + a, nb + c, nb + b], [nb + a, nb + dd, nb + c]]
for r in range(N - 1):                                                     # (the two long sides)
    for j in (0, M - 1):
        a, dd = r * M + j, (r + 1) * M + j; F += [[a, dd, nb + dd], [a, nb + dd, nb + a]] if j == 0 else [[a, nb + a, nb + dd], [a, nb + dd, dd]]
for r in (0, N - 1):                                                       # (the two ends)
    for j in range(M - 1):
        a, b = r * M + j, r * M + j + 1; F += [[a, nb + b, b], [a, nb + a, nb + b]] if r == 0 else [[a, b, nb + b], [a, nb + b, nb + a]]
m = trimesh.Trimesh(V, np.array(F), process=True); trimesh.repair.fix_normals(m)
cn = np.unique(m.edges_sorted, axis=0, return_counts=True)[1]
np.savez(OUT, v_S=m.vertices, f_S=m.faces, v_D=m.vertices * [-1, 1, 1], f_D=m.faces[:, ::-1])
print("LACRIMA pe brat: lunga %.0f m, lata max %.1f m (cap rotund la varf), bombata %.1f m; %d fete, muchii libere %d, ne-manifold %d" % (
    d[-1], 2 * WM, H, len(m.faces), int((cn == 1).sum()), int((cn > 2).sum())))
