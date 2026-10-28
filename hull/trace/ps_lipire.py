# Sheet components (ps_banda103.py rings) laid onto the PS body: every point of a section is moved vertically so the
# sheet's centre line sits half its thickness above the body's top surface (the body = the deck section data, top over
# |x|), keeping the sheet's own shape across the section; the move is smoothed along the piece.
# Usage: python ps_lipire.py <rings.npz> <corp.npz> <out.npz>
import sys, os, numpy as np
R = dict(np.load(sys.argv[1])); B = np.load(sys.argv[2]); OUT = sys.argv[3]
X, C = R["X"], R["C"]; K, M = X.shape[:2]; NU = C.shape[1]; T = float(os.environ.get("B103_GROSIME", "2")); NE = (M - 2 * NU) // 2
ys, s, E, TP = B["ys"], B["s"], B["edge"], B["top"]
def ztop(x, y):
    k = int(np.clip(np.searchsorted(ys, y), 1, len(ys) - 1)); f = (y - ys[k - 1]) / (ys[k] - ys[k - 1])
    return (1 - f) * np.interp(abs(x), s * E[k - 1], TP[k - 1]) + f * np.interp(abs(x), s * E[k], TP[k])
dz = np.array([[ztop(C[k, i, 0], X[k, 0, 1]) + T / 2 - C[k, i, 1] for i in range(NU)] for k in range(K)])   # per centre-line point
n = 6; kk = np.exp(-0.5 * (np.arange(-3 * n, 3 * n + 1) / n) ** 2); kk /= kk.sum()
dz = np.apply_along_axis(lambda z: np.convolve(np.pad(z, 3 * n, mode="edge"), kk, "valid"), 0, dz)
u_of = np.r_[np.arange(NU), [NU - 1] * NE, np.arange(NU)[::-1], [0] * NE]  # ring index -> centre-line point
X = X.copy(); X[..., 2] += dz[:, u_of]
R["X"] = X; np.savez(OUT, **R)
print("LIPIT: mutare verticala %.1f..%.1f m (mediana %.1f)" % (dz.min(), dz.max(), np.median(dz)))
