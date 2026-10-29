# The PS's side between two vertebrae rebuilt as a smooth passage from one to the other (asked: between vertebra_14 and
# vertebra_15 dents on the side, the surface not smooth). The two vertebrae's side profiles (top attach -> guide point ->
# bottom attach, as vertebre_ps.py builds them; past the U the leg stub's outer side) are resampled by arc length and, every
# metre between them, mixed (smoothstep in y); the ends laid onto the PS's own section there (no seam with deck / belly).
# The ORIGINAL PS's side at that y is stretched onto it from O = (attach x, median z) (star-shaped: no folds); the stretch is
# then laid over the current mesh in the zone, blended over BL m at both ends. Both sides (|x|), same vertex order.
# Usage: python ps_zona_loft.py <pieces.npz> <current.npz v> <ghid_median.npz> <out.npz> <y_front> <y_back> ; env ZL_ATT=25 ZL_K=1.2 ZL_BL=3
import sys, os, numpy as np, trimesh
D = np.load(sys.argv[1]); C = np.load(sys.argv[2])["v"].astype(float); M = np.load(sys.argv[3]); OUT = sys.argv[4]
YF, YB = float(sys.argv[5]), float(sys.argv[6]); MX = -1700.0; e = lambda k, d: float(os.environ.get(k, d))
ATT, KT, BL, NS = e("ZL_ATT", "25"), e("ZL_K", "1.2"), e("ZL_BL", "3"), 120
v0 = D["PS__v"].astype(float) - [MX, 0, 0]; f0 = D["PS__f"]; ps = trimesh.Trimesh(v0, f0, process=False); cur = C - [MX, 0, 0]
Gm = M["contur_umar_median"]; ZM = Gm[0, 2]; R = Gm[Gm[:, 0] >= 0]; R = R[np.argsort(-R[:, 1])]; xg = lambda y: np.interp(-y, -R[:, 1], R[:, 0])
def herm(p0, t0, p1, t1, n=60):
    L = np.linalg.norm(p1 - p0) * KT; s = np.linspace(0, 1, n)[:, None]
    return (2*s**3 - 3*s**2 + 1) * p0 + (s**3 - 2*s**2 + s) * L * t0 + (-2*s**3 + 3*s**2) * p1 + (s**3 - s**2) * L * t1
def side(y):                                           # the PS's right outline at y, from deck round the outer side to belly
    s = ps.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    L = max([q[:, [0, 2]] for q in s.discrete], key=lambda q: q[:, 0].max()); L = L[:-1] if np.allclose(L[0], L[-1]) else L
    c = np.array([0.0, ZM]) if L[:, 0].min() < 1 else L.mean(0)
    H = L[(L[:, 0] >= -0.5) & (np.abs(np.arctan2(L[:, 1] - c[1], L[:, 0] - c[0])) < np.radians(100 if L[:, 0].min() >= 1 else 181))]
    H = H[np.argsort(-np.arctan2(H[:, 1] - c[1], H[:, 0] - c[0]))]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(H, axis=0), axis=1))]; u = np.arange(0, d[-1], 0.5)
    return np.c_[np.interp(u, d, H[:, 0]), np.interp(u, d, H[:, 1])]
def attach(H):
    xm = H[:, 0].max(); up = np.where((H[:, 0] >= xm - ATT) & (H[:, 1] > ZM))[0]; dn = np.where((H[:, 0] >= xm - ATT) & (H[:, 1] < ZM))[0]
    return up[0], dn[-1]
def profile(y):                                        # a vertebra's side profile (absolute x, z), resampled to NS points
    H = side(y); i, j = attach(H); G = np.array([xg(y), ZM])
    t_i = H[min(i + 4, len(H) - 1)] - H[i]; t_i /= np.linalg.norm(t_i); t_j = H[j] - H[max(j - 4, 0)]; t_j /= np.linalg.norm(t_j)
    P = np.vstack([herm(H[i], t_i, G, np.array([0.0, -1.0])), herm(G, np.array([0.0, -1.0]), H[j], t_j)[1:]])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.linspace(0, d[-1], NS)
    return np.c_[np.interp(u, d, P[:, 0]), np.interp(u, d, P[:, 1])]
PF, PB = profile(YF), profile(YB)
TH = np.radians(np.linspace(-90, 90, 361))
def polar(curve, O):
    q = curve - O; th = np.arctan2(q[:, 1], q[:, 0]); r = np.hypot(q[:, 0], q[:, 1]); o = np.argsort(th); return np.interp(TH, th[o], r[o])
V = cur.copy(); ys = np.arange(YF, YB - 0.1, -1.0) if YF > YB else np.arange(YF, YB + 0.1, 1.0); rows = []
for y in ys:
    t = (YF - y) / (YF - YB); t = t * t * (3 - 2 * t); P = (1 - t) * PF + t * PB          # mixed profile
    H = side(y); i, j = attach(H)                                                           # its ends onto this section
    s_ = np.linspace(0, 1, NS)[:, None]; P = P + (1 - s_) * (H[i] - P[0]) * (1 - s_) + s_ * (H[j] - P[-1]) * s_
    O = np.array([min(H[i, 0], H[j, 0]), ZM]); rows.append((y, O[0], polar(H[i:j + 1], O), polar(P, O)))
ry = np.array([r[0] for r in rows]); RX = np.array([r[1] for r in rows]); F = np.array([r[3] / np.maximum(r[2], 1e-6) for r in rows])
o = np.argsort(ry); ry, RX, F = ry[o], RX[o], F[o]
ax_ = np.abs(v0[:, 0]); xa = np.interp(v0[:, 1], ry, RX); th = np.arctan2(v0[:, 2] - ZM, ax_ - xa)
sel = (v0[:, 1] >= ry.min()) & (v0[:, 1] <= ry.max()) & (ax_ >= xa) & (np.abs(th) <= np.pi / 2)
ky = np.interp(v0[:, 1], ry, np.arange(len(ry))); k0 = np.clip(np.floor(ky).astype(int), 0, len(ry) - 1); k1 = np.minimum(k0 + 1, len(ry) - 1); a = ky - k0
kt = np.interp(th, TH, np.arange(len(TH))); t0 = np.clip(np.floor(kt).astype(int), 0, len(TH) - 1); t1 = np.minimum(t0 + 1, len(TH) - 1); b = kt - t0
fac = (1 - a) * ((1 - b) * F[k0, t0] + b * F[k0, t1]) + a * ((1 - b) * F[k1, t0] + b * F[k1, t1])
r = np.hypot(ax_ - xa, v0[:, 2] - ZM); rn = r * fac; Z = v0.copy()
Z[:, 0] = np.sign(v0[:, 0]) * (xa + rn * np.cos(th)); Z[:, 2] = ZM + rn * np.sin(th)
y_ = v0[:, 1]; lo, hi = min(YF, YB), max(YF, YB); w = np.clip(np.minimum(y_ - lo, hi - y_) / BL, 0, 1); w = w * w * (3 - 2 * w); w[~sel] = 0
V = (1 - w)[:, None] * cur + w[:, None] * Z
tm = trimesh.Trimesh(V, f0, process=False); ang = np.degrees(tm.face_adjacency_angles); cz = tm.triangles_center[tm.face_adjacency[:, 0]]
zone = (cz[:, 1] > lo - 6) & (cz[:, 1] < hi + 6)
print("ZONA y %.0f..%.0f refacuta (trecere intre vertebre): %d varfuri, etans %s; in zona: cute >30 grd %d, >45 grd %d, >60 grd %d" % (
    lo, hi, (w > 0.01).sum(), tm.is_watertight, (ang[zone] > 30).sum(), (ang[zone] > 45).sum(), (ang[zone] > 60).sum()))
for y in np.arange(hi, lo - 0.1, -4):
    q = V[(np.abs(V[:, 1] - y) < 1) & (V[:, 0] > 0)]; print("   y %4.0f: cel mai lat %.1f (ghidaj %.1f)" % (y, q[:, 0].max(), xg(y)))
np.savez(OUT, v=(V + [MX, 0, 0]).astype(np.float32))
