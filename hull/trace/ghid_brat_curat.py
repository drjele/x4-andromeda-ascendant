# Clean lines for the front arm's guides (asked: lines still not clean -> redo the guides separately, clean, then the surfaces):
# every main line resampled at 1 m and faired - minimise the change of curvature (3rd differences) while staying within DMAX m of the
# old line (lambda found by bisection) - ends held (position + direction, 3 points), the tip lobe held (points past the spine station
# of rib SECT_B, where the surface is not rebuilt), the lips' V kept as a corner (each lip faired on its own). Lines: spine,
# exterior / interior contours, lips, nacelle contours (capat1 / capat2 / varf). Ribs unchanged. Report: max move, max kink, turn
# direction changes seen from above, before / after. Usage: python ghid_brat_curat.py <in npz (exporta_ghidaje_brat)> <out npz>
#   env DMAX=0.6 SECT_B=46
import sys, os, numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sl
from scipy.spatial import cKDTree
G = dict(np.load(sys.argv[1], allow_pickle=True)); OUT = sys.argv[2]; DMAX = float(os.environ.get("DMAX", .6)); SB = int(os.environ.get("SECT_B", 46))
def rs(P, h=1.0):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; n = max(int(round(d[-1] / h)), 3); u = np.linspace(0, d[-1], n + 1)
    return np.c_[[np.interp(u, d, P[:, k]) for k in range(3)]].T
def stats(P):
    d = np.diff(P, axis=0); d /= np.linalg.norm(d, axis=1)[:, None]; ang = np.degrees(np.arccos(np.clip((d[:-1] * d[1:]).sum(1), -1, 1)))
    cr = d[:-1, 0] * d[1:, 1] - d[:-1, 1] * d[1:, 0]; sg = np.sign(cr[np.abs(cr) > 2e-4]); return ang.max(), np.percentile(ang, 99), int((np.diff(sg) != 0).sum())
def fair(P, hold):                                                       # hold: bool mask of points kept in place
    n = len(P); D3 = sp.diags([-1, 3, -3, 1], [0, 1, 2, 3], shape=(n - 3, n)); A3 = (D3.T @ D3).tocsc()
    def solve(lam):
        w = np.where(hold, 1e8, 1.0); M = (lam * A3 + sp.diags(w)).tocsc(); return np.c_[[sl.spsolve(M, w * P[:, k]) for k in range(3)]].T
    lo, hi = 0.0, 1e9
    for _ in range(60):
        mid = np.sqrt(max(lo, 1e-3) * hi); X = solve(mid)
        if np.linalg.norm(X - P, axis=1).max() > DMAX: hi = mid
        else: lo = mid
    return solve(lo) if lo > 0 else P.copy()
SP0 = rs(G["g_as_bf_spinare_brat_fata_S"]); kds = cKDTree(SP0); sS = np.r_[0, np.cumsum(np.linalg.norm(np.diff(SP0, axis=0), axis=1))]
sB = sS[kds.query(G["g_as_bf_sectiune_brat_fata_S_%02d" % SB].mean(0))[1]]
def lobe(P): return sS[kds.query(P)[1]] > sB                             # points along the arm past rib SB (the lobe)
def ends(n, k=3): m = np.zeros(n, bool); m[:k] = m[-k:] = True; return m
OUTD = dict(G); REP = []
def do(key, P, extra=None):
    hold = ends(len(P)) | lobe(P) | (extra if extra is not None else False); X = fair(P, hold); a, b = stats(P), stats(X)
    REP.append("%-44s %5d m  mutat max %.2f m | frangere max %5.2f -> %5.2f, p99 %.2f -> %.2f grade | schimbari sens sus %3d -> %3d" % (key[5:], len(P), np.linalg.norm(X - P, axis=1).max(), a[0], b[0], a[1], b[1], a[2], b[2])); return X
for k in ("g_as_bf_spinare_brat_fata_S", "g_as_bf_contur_exterior_brat_fata_S", "g_as_bf_contur_interior_brat_fata_S", "g_as_nac_contur_nacela_capat1_S", "g_as_nac_contur_nacela_capat2_S", "g_as_nac_contur_nacela_varf_S"):
    OUTD[k] = do(k, rs(G[k]))
BZ = rs(G["g_as_bf_buze_gura_brat_fata_S"]); iv = int(np.argmax([np.linalg.norm(BZ[i] - BZ[0]) + np.linalg.norm(BZ[i] - BZ[-1]) for i in range(len(BZ))]))
L1, L2 = do("g_as_bf_buze_gura_jos", BZ[:iv + 1]), do("g_as_bf_buze_gura_sus", BZ[iv:]); OUTD["g_as_bf_buze_gura_brat_fata_S"] = np.r_[L1, L2[1:]]
np.savez(OUT, **OUTD); print("\n".join("CURAT " + r for r in REP)); print("CURAT -> %s (DMAX %.2f m, lobul de la s %.0f tinut)" % (OUT, DMAX, sB))
