# A clean teardrop on a top surface (asked: decorations as clean teardrops like the others, on the new pieces' surface - the moved
# R131 came out lumpy): its footprint taken from a reference decoration seen from above (main axis by PCA, centre and half-width per
# bin along it, smoothed), the outline a teardrop (round head at the HEAD end: "miny" = towards the stern), laid on our surface
# (nearest vertex's plane, normals up), bulged H m, LIFT m above, closed with a flat bottom 1 m under. Left side; right mirrored.
# SCALE shrinks the footprint about its centre, DX moves it towards the axis (asked: smaller and closer together).
# Usage: python lacrima_pe_suprafata.py <decor npz (v or v_S)> <surface npz (v,n)> <out npz> ; env H=3 LIFT=0.4 HEAD=0.22 HEAD_END=miny N=120 M=15 SCALE=1 DX=0
import sys, os, numpy as np, trimesh
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d
e = lambda k, d: float(os.environ.get(k, d)); Z = np.load(sys.argv[1]); DV = Z["v"] if "v" in Z.files else Z["v_S"]
SU = np.load(sys.argv[2]); SV, SN = SU["v"], SU["n"] * np.where(SU["n"][:, 2:3] < 0, -1, 1); ks = cKDTree(SV); OUT = sys.argv[3]
c0 = DV[:, :2].mean(0); DV = DV.copy(); DV[:, :2] = c0 + e("SCALE", "1") * (DV[:, :2] - c0); c0 = c0 + [-np.sign(c0[0]) * e("DX", "0"), 0]; DV[:, 0] += -np.sign(DV[:, 0].mean()) * e("DX", "0"); U, Sg, Vt = np.linalg.svd(DV[:, :2] - c0); ax = Vt[0]; pr = (DV[:, :2] - c0) @ ax; pe = (DV[:, :2] - c0) @ np.array([-ax[1], ax[0]])
if os.environ.get("HEAD_END", "miny") == "miny" and ax[1] > 0: ax, pr, pe = -ax, -pr, -pe      # (t = 1 = the head, towards -y)
bins = np.linspace(pr.min(), pr.max(), 25); cen, hw = [], []
for a, b in zip(bins[:-1], bins[1:]):
    m = (pr >= a) & (pr < b); cen.append(((a + b) / 2, np.median(pe[m]) if m.any() else 0)); hw.append((pe[m].max() - pe[m].min()) / 2 if m.any() else 0)
cen = np.array(cen); off = gaussian_filter1d(cen[:, 1], 2, mode="nearest")
N, M = int(e("N", "120")), int(e("M", "15")); t = np.linspace(0, 1, N); L = np.interp(t, np.linspace(0, 1, len(cen)), cen[:, 0]); O = np.interp(t, np.linspace(0, 1, len(cen)), off)
nrm2 = np.array([-ax[1], ax[0]]); P2 = c0 + np.outer(L, ax) + np.outer(O, nrm2)
WM = 0.95 * max(hw); HD = e("HEAD", "0.22"); WMIN = e("WMIN", "0.4")
w = np.where(t < 1 - HD, WM * np.sin(0.5 * np.pi * np.clip(t / (1 - HD), 0, 1)) ** 0.8, WM * np.sqrt(np.clip(1 - ((t - (1 - HD)) / HD) ** 2, 0, 1))); w = np.maximum(w, WMIN)
def onsurf(xy):
    P = np.c_[xy, np.full(len(xy), SV[:, 2].max() + 50)]; i = ks.query(np.c_[xy, SV[ks.query(np.c_[xy, np.zeros(len(xy))] * [1, 1, 0] + [0, 0, 1e9])[1], 2]])[1] if False else None
    k2 = cKDTree(SV[:, :2]); i = k2.query(xy)[1]; n = SN[i]; p0 = SV[i]
    z = p0[:, 2] - (n[:, 0] * (xy[:, 0] - p0[:, 0]) + n[:, 1] * (xy[:, 1] - p0[:, 1])) / np.maximum(n[:, 2], 0.2); return np.c_[xy, z], n
u = np.linspace(-1, 1, M); H, LI = e("H", "3"), e("LIFT", "0.4"); top, bot = [], []
for k in range(N):
    xy = P2[k] + np.outer(u * w[k], nrm2); Q, Nq = onsurf(xy); g = np.sin(np.pi * t[k]) ** 0.3
    top.append(Q + Nq * (LI + H * g * np.sqrt(np.clip(1 - u ** 2, 0, 1)))[:, None]); bot.append(Q - Nq * 1.0)
T_, B_ = np.array(top), np.array(bot); V = np.vstack([T_.reshape(-1, 3), B_.reshape(-1, 3)]); nb = N * M; F = []
for r in range(N - 1):
    for j in range(M - 1):
        a, b, c, dd = r * M + j, r * M + j + 1, (r + 1) * M + j + 1, (r + 1) * M + j; F += [[a, b, c], [a, c, dd], [nb + a, nb + c, nb + b], [nb + a, nb + dd, nb + c]]
    for j in (0, M - 1):
        a, dd = r * M + j, (r + 1) * M + j; F += [[a, dd, nb + dd], [a, nb + dd, nb + a]]
for r in (0, N - 1):
    for j in range(M - 1):
        a, b = r * M + j, r * M + j + 1; F += [[a, nb + b, b], [a, nb + a, nb + b]]
m = trimesh.Trimesh(V, np.array(F), process=True); trimesh.repair.fix_normals(m); cn = np.unique(m.edges_sorted, axis=0, return_counts=True)[1]
np.savez(OUT, v_S=m.vertices, f_S=m.faces, v_D=m.vertices * [-1, 1, 1], f_D=m.faces[:, ::-1])
print("LACRIMA pe suprafata: lunga %.0f m, lata max %.1f m, capul spre %s; %d fete, libere %d, ne-manifold %d" % (
    L.max() - L.min(), 2 * WM, os.environ.get("HEAD_END", "miny"), len(m.faces), int((cn == 1).sum()), int((cn > 2).sum())))
