# The ear piece from its confirmed guides (ureche_ghidaje.py): at every section of the 103 piece (one per metre) the same
# profile - top Hermite curve from the inner top edge (leaving along the PS's surface there; level where there is no PS),
# rounded blade MARGINE m thick at the outer edge, bottom curve back to the inner bottom edge, closed straight through the PS
# (hidden); the attach tangents smoothed along the length (no ripples); sections joined by quads, both ends capped (fan).
# One watertight, separate piece (ship coordinates, centred); the left one = its mirror.
# Usage: python ureche_piesa.py <103_D.npz> <pieces.npz> <out_D.npz> <out_S.npz> ; env UR_MARGINE=4 UR_NET=8 UR_N=16
import sys, os, numpy as np, trimesh
from scipy.ndimage import gaussian_filter1d
R = np.load(sys.argv[1])["v"].astype(float).reshape(-1, 4, 3); D = np.load(sys.argv[2]); OD, OS = sys.argv[3], sys.argv[4]
MG, NET, N = float(os.environ.get("UR_MARGINE", "4")), float(os.environ.get("UR_NET", "8")), int(os.environ.get("UR_N", "16"))
ps = trimesh.Trimesh(D["PS__v"] + [1700, 0, 0], D["PS__f"], process=False)
def tangent(p):
    s = ps.section(plane_origin=[0, p[1], 0], plane_normal=[0, 1, 0])
    if s is None: return np.array([1.0, 0])
    best = None
    for e in s.discrete:
        e = e[:, [0, 2]]; d = np.linalg.norm(e - p[[0, 2]], axis=1); i = np.argmin(d)
        if d[i] < 4 and (best is None or d[i] < best[0]): best = (d[i], e, i)
    if best is None: return np.array([1.0, 0])
    _, e, i = best; t = e[min(i + 3, len(e) - 1)] - e[max(i - 3, 0)]; t /= np.linalg.norm(t)
    return t if t[0] > 0 else -t
TS = np.array([tangent(r[0]) for r in R]); TB = np.array([tangent(r[3]) for r in R])
TS, TB = [gaussian_filter1d(T_, NET, axis=0, mode="nearest") for T_ in (TS, TB)]
TS /= np.linalg.norm(TS, axis=1)[:, None]; TB /= np.linalg.norm(TB, axis=1)[:, None]
s_ = np.linspace(0, 1, N)[:, None]; H = (2 * s_**3 - 3 * s_**2 + 1, s_**3 - 2 * s_**2 + s_, -2 * s_**3 + 3 * s_**2, s_**3 - s_**2)
def herm(p0, t0, p1, t1):
    L = np.linalg.norm(p1 - p0); return H[0] * p0 + H[1] * L * 0.6 * t0 + H[2] * p1 + H[3] * L * 0.6 * t1
loops = []; ang = np.linspace(0, np.pi, 9)[1:-1]
for i, r in enumerate(R):
    e = (r[1] + r[2]) / 2; et, eb = e + [0, 0, MG / 2], e - [0, 0, MG / 2]; o = np.array([1.0, 0, 0])
    up = herm(r[0], np.array([TS[i, 0], 0, TS[i, 1]]), et, o); dn = herm(r[3], np.array([TB[i, 0], 0, TB[i, 1]]), eb, o)
    tip = e + np.c_[(MG / 2) * np.sin(ang), np.zeros(len(ang)), (MG / 2) * np.cos(ang)]
    loops.append(np.vstack([up, tip, dn[::-1]]))
L = np.array(loops); n, m = L.shape[:2]; V = L.reshape(-1, 3); F = []
for i in range(n - 1):
    a = i * m + np.arange(m); b = a + m; F += [np.c_[a, np.roll(a, -1), np.roll(b, -1)], np.c_[a, np.roll(b, -1), b]]
c0, c1 = L[0].mean(0), L[-1].mean(0); V = np.vstack([V, c0, c1]); i0, i1 = len(V) - 2, len(V) - 1
a = np.arange(m); F.append(np.c_[np.roll(a, -1), a, np.full(m, i0)]); b = (n - 1) * m + a; F.append(np.c_[b, np.roll(b, -1), np.full(m, i1)])
F = np.vstack(F); t = trimesh.Trimesh(V, F, process=True); trimesh.repair.fix_winding(t); trimesh.repair.fix_normals(t)
V, F = np.asarray(t.vertices), np.asarray(t.faces)
print("URECHE: %d sectiuni x %d puncte, %d triunghiuri, etans %s, volum %.0f m3, x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f" % (
    n, m, len(F), t.is_watertight, t.volume, V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max()))
np.savez(OD, v=V.astype(np.float32), f=F.astype(np.int32)); np.savez(OS, v=(V * [-1, 1, 1]).astype(np.float32), f=F[:, ::-1].astype(np.int32))
