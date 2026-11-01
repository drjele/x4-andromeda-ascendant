# A piece's surface smoothed (asked: smooth the new arms' surfaces): Taubin smoothing (no shrinking) on the mesh, its free edges
# (the mouth, the head) held where they are, ITER rounds; the move per vertex and the guide ribs' distance to the surface reported.
# Usage: python neteda_piesa.py <piece npz (brat_fata_D__v/__f)> <out npz> [guides npz] ; env ITER=30 LAMB=0.5 NU=-0.53
import sys, os, numpy as np, trimesh
from scipy.spatial import cKDTree
Z = np.load(sys.argv[1]); OUT = sys.argv[2]; e = lambda k, d: float(os.environ.get(k, d))
m = trimesh.Trimesh(Z["brat_fata_D__v"], Z["brat_fata_D__f"], process=False); V0 = m.vertices.copy()
ed, cn = np.unique(m.edges_sorted, axis=0, return_counts=True); fixed = np.unique(ed[cn == 1])
L = trimesh.smoothing.laplacian_calculation(m, equal_weight=True); V = V0.copy(); lamb, nu = e("LAMB", "0.5"), e("NU", "-0.53")
SPN = os.environ.get("SPINARE", "")                                        # (asked again - waves across the arm: smoothing only along
if SPN:                                                                    # the arm, each vertex with its neighbours along the spine)
    import scipy.sparse as sp_
    from scipy.spatial import cKDTree as KD_
    pth, key = SPN.split(":"); SPL = np.load(pth)[key]; TS = np.gradient(SPL, axis=0); TS /= np.linalg.norm(TS, axis=1)[:, None]
    Tv = TS[KD_(SPL).query(V0)[1]]; E_ = m.edges_unique; dv = V0[E_[:, 1]] - V0[E_[:, 0]]; dv /= np.linalg.norm(dv, axis=1)[:, None]
    al = np.abs(np.einsum("ij,ij->i", dv, Tv[E_[:, 0]])) > float(os.environ.get("ALONG", "0.8")); E_ = E_[al]
    A_ = sp_.coo_matrix((np.ones(2 * len(E_)), (np.r_[E_[:, 0], E_[:, 1]], np.r_[E_[:, 1], E_[:, 0]])), shape=(len(V0), len(V0))).tocsr()
    deg = np.asarray(A_.sum(1)).ravel(); deg[deg == 0] = 1; L = sp_.diags(1 / deg) @ A_
    L = L + sp_.diags((np.asarray(A_.sum(1)).ravel() == 0).astype(float))  # (vertices with no such neighbour stay)
    print("NETEDA in lungul bratului: %d muchii pe directia spinarii" % len(E_))
for _ in range(int(e("ITER", "30"))):
    for f in (lamb, nu):
        V = V + f * (L.dot(V) - V); V[fixed] = V0[fixed]
mv = np.linalg.norm(V - V0, axis=1)
np.savez(OUT, brat_fata_D__v=V, brat_fata_D__f=Z["brat_fata_D__f"], brat_fata_S__v=V * [-1, 1, 1], brat_fata_S__f=Z["brat_fata_D__f"][:, ::-1])
msg = "NETEDA: %d varfuri, %d pe margini fixe; mutare medie %.2f, max %.2f m" % (len(V), len(fixed), mv.mean(), mv.max())
if len(sys.argv) > 3:
    G = np.load(sys.argv[3]); kd0, kd1 = cKDTree(V0), cKDTree(V)
    ks = [k for k in G.files if k.startswith("sectiune_brat_fata_D")]
    msg += "; vertebrele pe piesa max %.2f -> %.2f m" % (max(kd0.query(G[k])[0].max() for k in ks), max(kd1.query(G[k])[0].max() for k in ks))
print(msg)
