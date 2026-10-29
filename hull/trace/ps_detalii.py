# A smoothing pass over the whole PS (top and bottom) that also brings its details out (asked: smooth it and accentuate the
# details; the channels / dents on the bottom a bit more 3D, pushed in a bit). Taubin smoothing (no shrinking) takes off the
# small noise; detail = the offset from a heavily smoothed copy, along the normal; everywhere it is raised by DT_K, and on the
# bottom (z < median - 2 m) the channels (detail below -DT_PRAG m) are pushed further in by DT_CANAL x their depth (at most
# DT_MAX m). Same faces, same vertex order. Usage: python ps_detalii.py <faces.npz:key> <ps.npz v> <ghid_median.npz> <out.npz>
# env DT_TAUBIN=8 DT_BAZA=40 DT_K=0.15 DT_CANAL=0.5 DT_PRAG=0.3 DT_MAX=2
import sys, os, numpy as np, trimesh
from scipy.sparse import coo_matrix, diags
fn, k = sys.argv[1].split(":"); f = np.load(fn)[k]; V = np.load(sys.argv[2])["v"].astype(float); ZM = np.load(sys.argv[3])["contur_umar_median"][0, 2]
e = lambda k, d: float(os.environ.get(k, d)); NT, NB, KD, KC, PR, MXD = int(e("DT_TAUBIN", "8")), int(e("DT_BAZA", "40")), e("DT_K", "0.15"), e("DT_CANAL", "0.5"), e("DT_PRAG", "0.3"), e("DT_MAX", "2")
n = len(V); E = np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]
A = coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr(); A.data[:] = 1
W = diags(1 / np.asarray(A.sum(1)).ravel()) @ A                                   # neighbour average
def lap(X, lam): return X + lam * (W @ X - X)
X = V.copy()
for _ in range(NT): X = lap(lap(X, 0.5), -0.53)                                   # Taubin: smooth without shrinking
B = X.copy()
for _ in range(NB): B = lap(B, 0.5)                                               # the broad shape
nv = trimesh.Trimesh(X, f, process=False).vertex_normals; D = np.einsum("ij,ij->i", X - B, nv)   # detail along the normal (+ out)
jos = X[:, 2] < ZM - 2; w = np.clip((ZM - 2 - X[:, 2]) / 3, 0, 1)                  # bottom, eased in over 3 m under the median
canal = jos & (D < -PR)
wm = np.clip((np.abs(X[:, 2] - ZM) - 2) / 4, 0, 1)                               # off the median band (the side stays on its guide)
push = KD * D * wm + w * np.where(canal, np.clip(KC * (D + PR), -MXD, 0), 0)         # raised detail + channels pushed in
for _ in range(2): push = W @ push * 0.5 + push * 0.5                              # no single-vertex steps
Y = X + nv * push[:, None]
t0 = trimesh.Trimesh(V, f, process=False); t1 = trimesh.Trimesh(Y, f, process=False)
def cr(t): a = np.degrees(t.face_adjacency_angles); return (a > 30).sum(), (a > 45).sum(), (a > 60).sum()
print("DETALII PS: netezire Taubin %d, detaliu x%.2f, canale jos (detaliu < -%.1f m) %d varfuri, adancite cu pana la %.1f m (medie %.2f); netezire max %.1f m; etans %s" % (
    NT, 1 + KD, PR, canal.sum(), -push[canal].min() if canal.any() else 0, -push[canal].mean() if canal.any() else 0, np.linalg.norm(X - V, axis=1).max(), t1.is_watertight))
print("   cute >30/>45/>60 grd: inainte %d/%d/%d, acum %d/%d/%d" % (cr(t0) + cr(t1)))
print("   adancimea canalelor jos (detaliu): inainte medie %.2f m, max %.2f m; acum medie %.2f, max %.2f" % (
    -D[canal].mean(), -D[canal].min(), -(D[canal] + push[canal]).mean(), -(D[canal] + push[canal]).min()))
np.savez(sys.argv[4], v=Y.astype(np.float32))
