# The PS arm tube (_S: V -> back loop -> outer branch) as rings on its centre curve: planes perpendicular to the curve
# every STEP m, frames carried without twist (parallel transport); in each plane the reference shell (densely sampled
# surface points in a thin slab) as the OUTER radius per angle around the centre (inner bits and the view through holes
# ignored), empty angles (holes) interpolated around the ring; smoothed around and along with twicing (no shrinking);
# the free end closed by rings shrinking on a quarter circle into the tip.
# Usage: python ps_tube.py <ps_v.npy> <ps_f.json> <centru_ps.npy> <out.npz> [y_start]
import sys, json, numpy as np
V = np.load(sys.argv[1]); F = json.load(open(sys.argv[2])); C = np.load(sys.argv[3]); OUT = sys.argv[4]; Y0 = float(sys.argv[5]) if len(sys.argv) > 5 else -300
NA, STEP, SLAB, RMAX, TRIM = 96, 2.0, 1.5, 70.0, 15
T = np.array([[f[0], f[i], f[i + 1]] for f in F for i in range(1, len(f) - 1)]); A = V[T[:, 0]]; B = V[T[:, 1]]; Cc = V[T[:, 2]]
ar = np.linalg.norm(np.cross(B - A, Cc - A), axis=1) / 2; rng = np.random.default_rng(1); N = int(ar.sum() * 3)
idx = rng.choice(len(T), N, p=ar / ar.sum()); r1, r2 = rng.random(N), rng.random(N); sw = r1 + r2 > 1; r1[sw], r2[sw] = 1 - r1[sw], 1 - r2[sw]
P = A[idx] + (B[idx] - A[idx]) * r1[:, None] + (Cc[idx] - A[idx]) * r2[:, None]; P = P[P[:, 0] < 5]
i0 = np.argmin(np.abs(C[:, 1] - Y0) + 1e3 * (np.arange(len(C)) > len(C) // 3)); C = C[i0:len(C) - TRIM]
seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]; u = np.arange(0, seg[-1], STEP)
C = np.array([np.interp(u, seg, C[:, i]) for i in range(3)]).T; K = len(C)
SC = float(__import__("os").environ.get("PS_NET_CENTRU", "0"))           # the centre only carries the planes: smoothing it
if SC > 0:                                                              # removes kinks, the radii still follow the shell
    n_ = int(3 * SC); kc = np.exp(-0.5 * (np.arange(-n_, n_ + 1) / SC) ** 2); kc /= kc.sum()
    Gc = lambda Z: np.array([np.convolve(np.r_[2 * Z[0, i] - Z[n_:0:-1, i], Z[:, i], 2 * Z[-1, i] - Z[-2:-n_ - 2:-1, i]], kc, "valid") for i in range(3)]).T
    C = 2 * Gc(C) - Gc(Gc(C))
t = np.gradient(C, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
e1 = np.zeros_like(C); e1[0] = np.cross(t[0], [0, 0, 1.0]); e1[0] /= np.linalg.norm(e1[0])
for k in range(1, K):                                                   # parallel transport
    v = e1[k - 1] - (e1[k - 1] @ t[k]) * t[k]; e1[k] = v / np.linalg.norm(v)
e2 = np.cross(t, e1)
from collections import defaultdict
cell = np.floor(P / 40).astype(int); grid = defaultdict(list)
for i, c in enumerate(map(tuple, cell)): grid[c].append(i)
ang = np.linspace(0, 2 * np.pi, NA, endpoint=False); Rr = np.full((K, NA), np.nan)
for k in range(K):
    c0 = tuple(np.floor(C[k] / 40).astype(int)); ids = [i for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2) for dz in (-2, -1, 0, 1, 2) for i in grid.get((c0[0] + dx, c0[1] + dy, c0[2] + dz), ())]
    d = P[ids] - C[k]; m = np.abs(d @ t[k]) < SLAB; d = d[m]; x, y = d @ e1[k], d @ e2[k]; r = np.hypot(x, y); ok = r < RMAX
    b = (np.round(np.arctan2(y[ok], x[ok]) / (2 * np.pi) * NA).astype(int)) % NA
    for j in range(NA):
        s = r[ok][b == j]
        if len(s): Rr[k, j] = s.max()
cov = np.isnan(Rr).mean(1); kend = K - 1 - int(np.argmax(cov[::-1] < 0.4))   # the shell ends obliquely: last well-covered ring
LREM = seg[-1] - u[kend]; Rr, C, t, e1, e2 = Rr[:kend + 1], C[:kend + 1], t[:kend + 1], e1[:kend + 1], e2[:kend + 1]; K = kend + 1
holes = np.isnan(Rr).mean(); fill = Rr.copy()
for k in range(K):                                                      # holes: interpolated around the ring
    g = ~np.isnan(fill[k])
    if g.sum() < 4: fill[k] = np.nan; continue
    jj = np.arange(NA); fill[k] = np.interp(jj, np.r_[jj[g] - NA, jj[g], jj[g] + NA], np.tile(fill[k][g], 3))
bad = np.isnan(fill).any(1)
for j in range(NA): fill[bad, j] = np.interp(np.nonzero(bad)[0], np.nonzero(~bad)[0], fill[~bad, j])
def gs(X, sg, axis, wrap):
    n = int(3 * sg); kk = np.exp(-0.5 * (np.arange(-n, n + 1) / sg) ** 2); kk /= kk.sum()
    if wrap: Y = np.concatenate([X[:, -n:], X, X[:, :n]], 1); return np.apply_along_axis(lambda z: np.convolve(z, kk, "valid"), 1, Y)
    Y = np.concatenate([2 * X[:1] - X[n:0:-1], X, 2 * X[-1:] - X[-2:-n - 2:-1]], 0); return np.apply_along_axis(lambda z: np.convolve(z, kk, "valid"), 0, Y)
# decorations on the shell (bumps) and inner bits seen through holes (dents): angles more than TOL off a strongly
# smoothed tube (~60 m along) are dropped and filled again from their neighbours, twice
TOL = 3.0; base = Rr.copy()
for it in range(3):
    ref_ = gs(gs(fill, 4.0, 1, True), 30.0, 0, False); out_ = np.isnan(base) | (np.abs(fill - ref_) > TOL)
    fill = np.where(out_, np.nan, base)
    for k in range(K):
        g = ~np.isnan(fill[k]); jj = np.arange(NA)
        fill[k] = np.interp(jj, np.r_[jj[g] - NA, jj[g], jj[g] + NA], np.tile(fill[k][g], 3)) if g.sum() >= 4 else ref_[k]
    print("  trecerea %d: %.1f%% unghiuri respinse (decoratiuni/goluri)" % (it + 1, 100 * out_.mean()))
SA, SL = float(__import__("os").environ.get("PS_NET_INEL", "3")), float(__import__("os").environ.get("PS_NET_LUNG", "8"))
G = lambda X: gs(gs(X, SA, 1, True), SL, 0, False)                      # SA bins around, SL rings (x STEP m) along
Rs = 2 * G(fill) - G(G(fill))
X = C[:, None, :] + Rs[:, :, None] * (np.cos(ang)[None, :, None] * e1[:, None, :] + np.sin(ang)[None, :, None] * e2[:, None, :])
rc = min(Rs[-1].mean(), max(LREM, 10.0)); nc = 16; cap = []            # rounded closed end, as long as the shell went on
for i in range(1, nc + 1):
    a = i / nc * np.pi / 2; cap.append(C[-1] + t[-1] * rc * np.sin(a) + np.cos(a) * (X[-1] - C[-1]))
X = np.vstack([X, np.array(cap)[:-1]]); tip = C[-1] + t[-1] * rc
if __import__("os").environ.get("PS_CAPAT_DESCHIS"): X = X[:K]; tip = np.full(3, np.nan)   # both ends left open
np.savez(OUT, X=X, tip=tip, C=C, R=Rs, raw=Rr)
print("capat: ultimul inel bun %d, inca %.0f m de coaja dupa el" % (kend, LREM)); print("TUB PS: %d inele (%.0f m), %d pe inel, goluri %.0f%% din unghiuri, raza %.1f..%.1f m (medie %.1f), capat rotunjit r %.1f m" % (K, seg[-1], NA, 100 * holes, Rs.min(), Rs.max(), Rs.mean(), rc))
