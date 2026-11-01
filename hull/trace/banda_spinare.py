# A smooth band through three guide lines that lie in one plane across the arm (asked: contur_interior, spinare and contur_exterior
# joined by one band with a smooth surface). Every PAS m along the spine, the section plane (normal = the spine's tangent) cuts the
# interior and the exterior lines; the row across = the quadratic curve interior -> spine -> exterior (a straight line when the three
# are in line), NU points across; rows only where all three lines reach. Open band (a sheet), faces as quads split into triangles.
# Usage: python banda_spinare.py <guides npz> <side D|S> <out.npz> ; env PAS=2 NU=17
import sys, os, numpy as np
G = np.load(sys.argv[1]); SD = sys.argv[2]; OUT = sys.argv[3]; PAS = float(os.environ.get("PAS", "2")); NU = int(os.environ.get("NU", "17"))
SP, IN, EX = (G["%s_brat_fata_%s" % (k, SD)] for k in ("spinare", "contur_interior", "contur_exterior"))
d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(SP, axis=0), axis=1))]
def cross(L, p, n):                                                         # where the line L crosses the plane (p, n), nearest p
    sd = (L - p) @ n; k = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    if not len(k): return None
    X = L[k] + (L[k + 1] - L[k]) * (sd[k] / (sd[k] - sd[k + 1]))[:, None]; X = X[np.linalg.norm(X - p, axis=1) < 300]
    return X[np.argmin(np.linalg.norm(X - p, axis=1))] if len(X) else None
rows, dev = [], []
u = np.linspace(0, 1, NU)
for s0 in np.arange(0, d[-1], PAS):
    i = int(np.searchsorted(d, s0)); i = min(max(i, 1), len(SP) - 2); p = SP[i]; n = SP[i + 1] - SP[i - 1]; n /= np.linalg.norm(n)
    a, b = cross(IN, p, n), cross(EX, p, n)
    if a is None or b is None: continue
    c = 2 * p - (a + b) / 2                                                 # quadratic through a (u 0), p (u 0.5), b (u 1)
    rows.append(np.outer((1 - u) ** 2, a) + np.outer(2 * u * (1 - u), c) + np.outer(u ** 2, b))
    dev.append(np.linalg.norm(np.cross(b - a, p - a)) / np.linalg.norm(b - a))   # the spine off the interior-exterior line
R = np.array(rows); nr = len(R); V = R.reshape(-1, 3); F = []
for r in range(nr - 1):
    for j in range(NU - 1):
        q = [r * NU + j, r * NU + j + 1, (r + 1) * NU + j + 1, (r + 1) * NU + j]; F += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
F = np.array(F)
w = np.array([np.linalg.norm(rw[-1] - rw[0]) for rw in R])
print("BANDA %s: %d randuri x %d, %d fete; latime %.0f..%.0f m; spinarea fata de dreapta interior-exterior medie %.2f, max %.2f m" % (
    SD, nr, NU, len(F), w.min(), w.max(), np.mean(dev), np.max(dev)))
np.savez(OUT, v=V, f=F)
