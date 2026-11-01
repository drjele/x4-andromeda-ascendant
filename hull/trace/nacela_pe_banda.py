# The nacelle's V point put exactly on the band (asked: contur_nacela_varf in the plane of the band and the green lines): each point
# moved, within its section across the new spine, onto the line spine -> interior (the band's interior side, carried on past the
# interior), its distance from the interior kept; the V (where all three meet) kept. Then the ribs redrawn as before: equal width
# along the V point's line, light / dark alternating, a dark rib's V pushed out by RELIEF m in its middle (along the band, outwards).
# Usage: python nacela_pe_banda.py <guides npz> <trei_linii npz> <out npz> ; env LATIME=5.25 RELIEF=1.0
import sys, os, numpy as np
from scipy.spatial import cKDTree
G = dict(np.load(sys.argv[1])); K = np.load(sys.argv[2]); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d))
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
S1, I1 = K["_kor_spinare_noua"], K["_kor_interior_nou"]; ok = np.isfinite(I1).all(1); S1, I1 = S1[ok], I1[ok]
d1 = arclen(S1); dn = np.linspace(0, d1[-1], 40 * len(S1)); at = lambda A: np.c_[[np.interp(dn, d1, A[:, k]) for k in range(3)]].T
SD, ID = at(S1), at(I1); TD = np.gradient(SD, axis=0); TD /= np.linalg.norm(TD, axis=1)[:, None]
A, TIP, B = G["contur_nacela_capat1_D"], G["contur_nacela_varf_D"].copy(), G["contur_nacela_capat2_D"]
for i in range(len(TIP) - 1):
    p = TIP[i]; j = int(np.argmin(np.abs(np.einsum("ij,ij->i", p - SD, TD)) + 1e-3 * np.linalg.norm(SD - p, axis=1)))   # its section
    u = ID[j] - SD[j]; u -= TD[j] * (u @ TD[j]); u /= np.linalg.norm(u); q = p - TD[j] * ((p - SD[j]) @ TD[j])
    TIP[i] = SD[j] + u * ((q - SD[j]) @ u)
G["contur_nacela_varf_D"] = TIP
for k in [k for k in G if k.startswith("nacela_nervura")]: G.pop(k)
LAT, REL = e("LATIME", "5.25"), e("RELIEF", "1.0"); dT = arclen(TIP); nr = int(dT[-1] // LAT); edg = np.linspace(0, dT[-1], nr + 1)
kd = cKDTree(SD)
for i in range(nr):
    jm = int(np.argmin(np.abs(dT - (edg[i] + edg[i + 1]) / 2))); j2 = min(jm, len(A) - 1)
    seg = np.vstack([np.linspace(A[j2], TIP[jm], 30)[:-1], np.linspace(TIP[jm], B[j2], 30)])
    if i % 2 == 0 and REL > 0:
        jj = kd.query(TIP[jm])[1]; o = TIP[jm] - ID[jj]; o -= TD[jj] * (o @ TD[jj]); o /= max(np.linalg.norm(o), 1e-9)
        seg = seg + np.outer(np.sin(np.linspace(0, np.pi, len(seg))), o) * REL
    G["nacela_nervura_%s_%03d_D" % ("inchisa" if i % 2 == 0 else "deschisa", i)] = seg
for k in [k for k in G if k.startswith("nacela_nervura") and k.endswith("_S")] + ["contur_nacela_varf_S"]: G.pop(k, None)
for k in list(G):
    if ("nacela" in k) and k.endswith("_D"): G[k.replace("_D", "_S")] = G[k] * [-1, 1, 1]
print("NACELA pe banda: varful pe linia spinare-interior a fiecarei sectiuni, %d nervuri de %.2f m (inchise bombate %.1f m)" % (nr, dT[-1] / nr, REL))
np.savez(OUT, **G)
