# The lobe's tip made more conical and a little sharper (asked: the tip of an_brat_fata's lobe more conical, a bit sharper; the whole
# arm smoothed): over the last LUNG m of the spine every vertex's place across its section is scaled from the round snout's profile
# (the section's own size, falling like a sphere) to a cone's (falling linearly to a point), and the last part is stretched along the
# spine's end tangent by EXTRA m. Then Taubin smoothing of the whole arm (ITER rounds, the free edges held). Both arms.
# Usage: python varf_conic.py <piece npz> <guides npz> <out npz> ; env LUNG=40 EXTRA=10 ITER=20
import sys, os, numpy as np, trimesh
from scipy.spatial import cKDTree
Z = np.load(sys.argv[1]); G = np.load(sys.argv[2]); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d)); sm = lambda w: w * w * (3 - 2 * w)
V = Z["brat_fata_D__v"].copy(); F = Z["brat_fata_D__f"]; SP = G["spinare_brat_fata_D"]
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]; dS = arclen(SP); TS = np.gradient(SP, axis=0); TS /= np.linalg.norm(TS, axis=1)[:, None]
LU, EX = e("LUNG", "40"), e("EXTRA", "10")
kd = cKDTree(SP); j = kd.query(V)[1]; s = dS[j] + np.einsum("ij,ij->i", V - SP[j], TS[j])
send = max(s.max(), dS[-1]); s0 = send - LU; tE = TS[-1]
def frame(sq):
    i = np.clip(np.searchsorted(dS, sq), 1, len(SP) - 1); f = np.clip((sq - dS[i - 1]) / (dS[i] - dS[i - 1]), 0, 1)
    p = SP[i - 1] + (SP[i] - SP[i - 1]) * f[:, None]; p = np.where((sq > dS[-1])[:, None], SP[-1] + np.outer(sq - dS[-1], tE), p)
    t = TS[i - 1] + (TS[i] - TS[i - 1]) * f[:, None]; t /= np.linalg.norm(t, axis=1)[:, None]; return p, t
m = s > s0; sq = s[m]; P, T = frame(sq); off = V[m] - P; off = off - T * np.einsum("ij,ij->i", off, T)[:, None]   # (across the section)
u = np.clip((sq - s0) / LU, 0, 1); rr = np.linalg.norm(off, axis=1)
bins = np.linspace(0, 1, 41); Rb = np.array([rr[(u >= a) & (u < b)].max() if ((u >= a) & (u < b)).any() else np.nan for a, b in zip(bins[:-1], bins[1:])])
uc = (bins[:-1] + bins[1:]) / 2; okb = np.isfinite(Rb); Rs = np.interp(u, uc[okb], np.maximum.accumulate(Rb[okb][::-1])[::-1])   # (the section's real size)
R0 = Rs[u < 0.05].max() if (u < 0.05).any() else Rs.max(); Rt = R0 * (1 - u) ** float(os.environ.get("PUTERE", "1"))   # (a cone's)
fac = np.minimum(Rt / np.maximum(Rs, 1e-3), 1.0); w = sm(np.clip(u / 0.3, 0, 1)); fac = (1 - w) + fac * w
s_new = s0 + (sq - s0) * (LU + EX) / LU; P2, T2 = frame(s_new)
V[m] = P2 + off * fac[:, None]
mesh = trimesh.Trimesh(V, F, process=False); ed, cn = np.unique(mesh.edges_sorted, axis=0, return_counts=True); fixed = np.unique(ed[cn == 1])
L = trimesh.smoothing.laplacian_calculation(mesh, equal_weight=True); V0 = V.copy()
for _ in range(int(e("ITER", "20"))):
    for f in (0.5, -0.53):
        V = V + f * (L.dot(V) - V); V[fixed] = V0[fixed]
np.savez(OUT, brat_fata_D__v=V, brat_fata_D__f=F, brat_fata_S__v=V * [-1, 1, 1], brat_fata_S__f=F[:, ::-1])
print("VARF conic: ultimii %.0f m, varful prelungit cu %.0f m (de la s %.0f la %.0f); %d varfuri in zona; netezit %d runde" % (LU, EX, send, send + EX, m.sum(), int(e("ITER", "20"))))
