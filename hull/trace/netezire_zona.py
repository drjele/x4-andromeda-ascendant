# Local smoothing (asked: no bumps or sudden turns left): only the vertices of a chosen zone move, Taubin passes (no
# shrinking) with the zone's edge eased; the rest of the piece held. ZONA_BIHARMONIC=1: libigl biharmonic fairing instead
# (bends least between the held rest - on a tube it pulls the section in). Zones: boxes y in [ya, yb] (both sides), |x| in [xa, xb].
# Usage: python netezire_zona.py <in.npz> <out.npz> <ya,yb,xa,xb>[;...]
import sys, numpy as np, igl
Z = np.load(sys.argv[1]); OUT = sys.argv[2]; V = Z["v"].astype(np.float64); F = Z["f"].astype(np.int64)
free = np.zeros(len(V), bool)
for zone in sys.argv[3].split(";"):
    ya, yb, xa, xb = [float(t) for t in zone.split(",")]
    free |= (V[:, 1] >= ya) & (V[:, 1] <= yb) & (np.abs(V[:, 0]) >= xa) & (np.abs(V[:, 0]) <= xb)
import os
if os.environ.get("ZONA_BIHARMONIC"):                                   # (on a tube this pulls the section in - kept as an option)
    b = np.nonzero(~free)[0]; W = igl.harmonic(V, F, b, V[b], 2)
else:                                                                   # Taubin passes on the zone only (no shrinking), weight eased
    E = np.unique(np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0); deg = np.bincount(E.ravel(), minlength=len(V)).astype(float)[:, None]
    def avg(P):
        S = np.zeros_like(P); np.add.at(S, E[:, 0], P[E[:, 1]]); np.add.at(S, E[:, 1], P[E[:, 0]]); return S / np.maximum(deg, 1)
    w = free.astype(float)[:, None]
    for _ in range(8): w = 0.5 * w + 0.5 * avg(w)                         # soft edge of the zone
    W = V.copy()
    for _ in range(int(os.environ.get("ZONA_PASI", "150"))): W = W + w * 0.5 * (avg(W) - W); W = W + w * -0.53 * (avg(W) - W)
d = np.linalg.norm(W - V, axis=1)
np.savez(OUT, v=W.astype(np.float32), f=F.astype(np.int32))
print("NETEZIRE locala: %d varfuri libere din %d; mutare medie %.2f / max %.2f m" % (free.sum(), len(V), d[free].mean(), d.max()))
