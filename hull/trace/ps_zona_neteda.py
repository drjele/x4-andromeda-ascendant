# A zone of the PS's side remade as the smoothest surface fitting its frame (asked: dents on the side between vertebra_14 and
# vertebra_15, not a smooth surface; the ray stretch could not handle the old corner curling back). Free vertices: the side
# (|x| >= X0) for y in [y_back, y_front]; everything else fixed as it is. Solved as a thin plate: minimise |L x|^2 (L the
# uniform graph Laplacian) with the frame fixed - smooth, no bumps or dents, continuous slope into the frame. Both sides.
# ZN_GHID=b ZN_W=w: the side's median strip pulled softly onto the median guide (b m in from the zone's ends).
# ZN_ADANC=d free zone = the side d m in from the guide (x0 ignored); ZN_PASTREAZA=w light hold on the current shape.
# ZN_PRINDE=y_a,y_b,k soft clamp in plan onto the guide after the plate.
# Usage: python ps_zona_neteda.py <faces.npz:key> <current.npz v> <ghid_median.npz> <out.npz> <y_front> <y_back> <x0>
import sys, os, numpy as np, trimesh
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import spsolve
fn, k = sys.argv[1].split(":"); f = np.load(fn)[k]; V = np.load(sys.argv[2])["v"].astype(float); M = np.load(sys.argv[3]); OUT = sys.argv[4]
YF, YB, X0 = float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7]); MX = -1700.0
P = V - [MX, 0, 0]; lo, hi = min(YF, YB), max(YF, YB)
Gm = M["contur_umar_median"]; R = Gm[Gm[:, 0] >= 0]; R = R[np.argsort(-R[:, 1])]; xg = lambda y: np.interp(-y, -R[:, 1], R[:, 0])
AD = os.environ.get("ZN_ADANC")                        # free = the side down to ADANC m in from the guide (follows the PS's width)
free = (P[:, 1] >= lo) & (P[:, 1] <= hi) & ((np.abs(P[:, 0]) >= xg(P[:, 1]) - float(AD)) if AD else (np.abs(P[:, 0]) >= X0))
E = np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]; n = len(P)
A = coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr(); A.data[:] = 1
L = diags(np.asarray(A.sum(1)).ravel()) - A; Q = (L.T @ L).tocsr()
GH = os.environ.get("ZN_GHID"); WS = float(os.environ.get("ZN_W", "0.05"))   # soft pull of the side's median strip onto the
T = P.copy(); wv = np.zeros(len(P))                    # median guide (x = guide at z = median), weight ZN_W - not nailed
if GH:
    gb = float(GH); ZM = Gm[0, 2]; yy = P[:, 1]
    band = free & (np.abs(P[:, 2] - ZM) < 2.5) & (yy >= lo + gb) & (yy <= hi - gb)
    T[band, 0] = np.sign(P[band, 0]) * xg(yy[band]); wv[band] = WS * (1 - (np.abs(P[band, 2] - ZM) / 2.5) ** 2)
    print("TRASE SPRE GHIDAJ: %d puncte din fasia mediana (|z - median| < 2,5 m), greutate %.2f" % (band.sum(), WS))
fi, xi = np.where(free)[0], np.where(~free)[0]
WK = float(os.environ.get("ZN_PASTREAZA", "0"))        # light hold on the current shape (a smoothing pass, not a rebuild)
Qff = (Q[fi][:, fi] + diags(wv[fi] + WK)).tocsc(); Qfx = Q[fi][:, xi]; X = P.copy()
for c in range(3): X[fi, c] = spsolve(Qff, -Qfx @ P[xi, c] + wv[fi] * T[fi, c] + WK * P[fi, c])
PR = os.environ.get("ZN_PRINDE")                       # y_a,y_b,k: there whatever still sticks out past the guide in plan (at any
if PR:                                                 # height) brought back inside - a smooth min, k m soft
    ya, yb, kc = [float(q) for q in PR.split(",")]; w = np.clip(np.minimum(X[:, 1] - ya, yb - X[:, 1]) / 6, 0, 1); w = w * w * (3 - 2 * w)
    xx = np.abs(X[:, 0]); g_ = xg(X[:, 1]); h = np.clip(kc - np.abs(xx - g_), 0, None) / kc; sm = np.minimum(xx, g_) - h * h * kc / 4
    m = (w > 0) & (xx > g_ - kc); X[m, 0] = np.sign(X[m, 0]) * (xx[m] + w[m] * (sm[m] - xx[m]))
t0 = trimesh.Trimesh(V - [MX, 0, 0], f, process=False); t1 = trimesh.Trimesh(X, f, process=False)
def creases(t):
    a = np.degrees(t.face_adjacency_angles); cz = t.triangles_center[t.face_adjacency[:, 0]]; z = (cz[:, 1] > lo - 6) & (cz[:, 1] < hi + 6)
    return (a[z] > 30).sum(), (a[z] > 45).sum(), (a[z] > 60).sum()
print("ZONA NETEDA y %.0f..%.0f, |x| >= %.0f: %d varfuri libere (ambele parti), mutate max %.1f m; etans %s" % (lo, hi, X0, len(fi), np.linalg.norm(X - P, axis=1).max(), t1.is_watertight))
print("   cute in zona (>30/>45/>60 grd): inainte %d/%d/%d, acum %d/%d/%d" % (creases(t0) + creases(t1)))
for y in np.arange(hi + 4, lo - 4.1, -4 if hi - lo < 80 else -20):
    P0 = V - [MX, 0, 0]; q0 = P0[(np.abs(P0[:, 1] - y) < 1) & (P0[:, 0] > 0)]; q1 = X[(np.abs(X[:, 1] - y) < 1) & (X[:, 0] > 0)]
    print("   y %4.0f: cel mai lat %.1f (era %.1f, ghidaj %.1f)" % (y, q1[:, 0].max(), q0[:, 0].max(), xg(y)))
np.savez(OUT, v=(X + [MX, 0, 0]).astype(np.float32))
