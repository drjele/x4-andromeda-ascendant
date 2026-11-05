# Guide lines faired along their length (asked standard: no kinks over 3 deg per 0.5 m): resampled every 0.5 m, gaussian SIG m with the ends held (contours wrapped), so a planar line stays in its plane. Reports kinks and distance to the piece before / after. Usage: python nt_ghid_neteda.py <p_dir> <SIG>
import sys, os, glob, numpy as np, trimesh
from scipy.ndimage import gaussian_filter1d as gf
D, SIG = sys.argv[1], float(sys.argv[2]); kb = []; ka = []; da = []
for gp in sorted(glob.glob(D + "/*_g.npz")):
    i = os.path.basename(gp)[:-6]; G = np.load(gp); Z = np.load(os.path.join(D, i + ".npz")); m = trimesh.Trimesh(Z["v"].astype(float), Z["f"], process=False); pq = trimesh.proximity.ProximityQuery(m); O = {}
    PARTS = []
    for k in G.files:                                                         # a cut across separate parts of a piece is several lines, not one bridging the gap
        L = G[k].astype(float); sg_ = np.linalg.norm(np.diff(L, axis=0), axis=1); lim = max(6.0, 5 * float(np.median(sg_)) if len(sg_) else 6.0); cuts = np.nonzero(sg_ > lim)[0]
        if "contur" in k: L = pq.on_surface(L)[0]; cuts = np.zeros(0, int)    # the plan outline read back onto the piece itself (its height was only an estimate)
        for t, q in enumerate(np.split(L, cuts + 1)):
            if len(q) >= 3 and np.linalg.norm(np.diff(q, axis=0), axis=1).sum() >= 20: PARTS.append(("%s_%d" % (k, t) if len(cuts) else k, q))   # crumbs out
    for k, L in PARTS:
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
        if s[-1] < 2: O[k] = L.astype(np.float32); continue
        u = np.arange(0, s[-1] + 0.25, 0.5); Q = np.stack([np.interp(u, s, L[:, a]) for a in range(3)], 1); sg = min(SIG / 0.5, len(u) / 8)
        cl = np.linalg.norm(L[0] - L[-1]) < 1e-3
        if cl: F = gf(Q[:-1], sg, axis=0, mode="wrap"); F = np.vstack([F, F[:1]])
        else:
            pad = Q[0] * 2 - Q[1:int(4 * sg) + 2][::-1]; pe = Q[-1] * 2 - Q[-int(4 * sg) - 2:-1][::-1]; F = gf(np.vstack([pad, Q, pe]), sg, axis=0, mode="nearest")[len(pad):len(pad) + len(Q)]; F[0], F[-1] = Q[0], Q[-1]
        def kink(A):
            d = np.diff(A, axis=0); n = np.linalg.norm(d, axis=1); ok = n > 1e-6; d = d[ok] / n[ok, None]; return np.degrees(np.arccos(np.clip(np.sum(d[1:] * d[:-1], 1), -1, 1)))
        kb.append(kink(Q)); ka.append(kink(F)); da.append(pq.on_surface(F[:: max(1, len(F) // 20)])[1]); O[k] = F[:: 2].astype(np.float32)
    np.savez(gp, **O)
kb, ka, da = np.concatenate(kb), np.concatenate(ka), np.concatenate(da)
print("FRANGERI >3 grade: inainte %.2f %%, dupa %.2f %%, p99 %.2f -> %.2f; ghidaj-piesa medie %.2f p95 %.2f max %.2f m" % (100 * (kb > 3).mean(), 100 * (ka > 3).mean(), np.percentile(kb, 99), np.percentile(ka, 99), da.mean(), np.percentile(da, 95), da.max()))
