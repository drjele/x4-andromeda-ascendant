# A piece's surface cleaned (asked: apply the clean-surface rules to sep_brat_fata_S - continuous smooth surfaces, no
# dents, bumps or creases). Taubin smoothing (no shrinking), NT passes, boundary vertices fixed; then the creases still
# left (faces at more than PRAG deg) get extra local passes. Same vertex order (written back with varfuri_din_npz.py).
# ZONA_Y=y: only below that y (blended over 30 m); BORD=1: the open edges smoothed along themselves too.
# Usage: python piesa_neteda.py <in.npz v,f> <out.npz> ; env NT=15 PRAG=30 NL=30 ZONA_Y=
import sys, os, numpy as np, trimesh
from scipy.sparse import coo_matrix, diags
D = np.load(sys.argv[1]); V = D["v"].astype(float); f = D["f"]; NT, PRAG, NL = int(os.environ.get("NT", "15")), float(os.environ.get("PRAG", "30")), int(os.environ.get("NL", "30"))
t0 = trimesh.Trimesh(V, f, process=False); n = len(V)
E = np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]; A = coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr(); A.data[:] = 1
W = diags(1 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)) @ A
eu, ec = np.unique(np.sort(E, axis=1), axis=0, return_counts=True); fixed = np.zeros(n, bool); fixed[eu[ec == 1].ravel()] = True   # open edges
BORD = os.environ.get("BORD", "0") == "1"             # the open edges smoothed too - each along its own edge line only
be = eu[ec == 1]; Ab = coo_matrix((np.ones(len(be) * 2), (np.r_[be[:, 0], be[:, 1]], np.r_[be[:, 1], be[:, 0]])), shape=(n, n)).tocsr()
Wb = diags(1 / np.maximum(np.asarray(Ab.sum(1)).ravel(), 1)) @ Ab
def taubin(X, mask, k):
    for _ in range(k):
        for lam in (0.5, -0.53):
            Y = X + lam * (W @ X - X)
            if BORD: Yb = X + lam * (Wb @ X - X); Y = np.where(fixed[:, None], Yb, Y)
            X = np.where(mask[:, None], Y, X)
    return X
ZY = os.environ.get("ZONA_Y")                          # only zones of y: "hi" (below hi) or "lo:hi,lo:hi"; faded over 30 m
if ZY:
    rng = [(-1e9, float(q)) if ":" not in q else tuple(float(z) for z in q.split(":")) for q in ZY.split(",")]
    w_ = np.zeros(n)
    for lo, hi in rng: w_ = np.maximum(w_, np.clip(np.minimum(V[:, 1] - lo, hi - V[:, 1]) / 30, 0, 1))
    w_ = w_ * w_ * (3 - 2 * w_); zona = w_ > 0
else: zona = np.ones(n, bool); w_ = np.ones(n)
X = taubin(V.copy(), (~fixed | BORD) & zona, NT); X = V + w_[:, None] * (X - V)   # the zones' edges blended back
t1 = trimesh.Trimesh(X, f, process=False); a = np.degrees(t1.face_adjacency_angles); bad = np.zeros(n, bool); bad[t1.face_adjacency_edges[a > PRAG].ravel()] = True
for _ in range(3): bad = bad | (A @ bad.astype(float) > 0)                                  # the creases' neighbourhood
X = taubin(X, bad & (~fixed | BORD) & zona, NL)
t2 = trimesh.Trimesh(X, f, process=False)
def cr(t): a = np.degrees(t.face_adjacency_angles); return (a > 30).sum(), (a > 45).sum(), (a > 60).sum()
print("SUPRAFATA CURATA: Taubin %d treceri (+%d pe cele %d varfuri din jurul cutelor), %d varfuri de margine fixe; cute >30/45/60: %d/%d/%d -> %d/%d/%d; mutat max %.2f m (medie %.2f), volum/arie %+.2f%%" % (
    NT, NL, bad.sum(), fixed.sum(), *cr(t0), *cr(t2), np.linalg.norm(X - V, axis=1).max(), np.linalg.norm(X - V, axis=1).mean(), 100 * (t2.area / t0.area - 1)))
np.savez(sys.argv[2], v=X.astype(np.float32))
