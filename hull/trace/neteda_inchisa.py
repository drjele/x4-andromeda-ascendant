# A closed piece smoothed keeping its shape (asked: an_comp_055 - keep the form, but through our clean lines / surfaces standard):
# Taubin rounds (no shrinking) on the whole surface, the faces that look down (DOWN_DOT, its base moulded on the PS) held where they
# are so it stays sitting on the PS. Reports the move and the dihedral angles before / after.
# Usage: python neteda_inchisa.py <in npz (v,f)> <out npz> ; env ITER=60 DOWN_DOT=-0.6
import sys, os, numpy as np, trimesh
Z = np.load(sys.argv[1]); OUT = sys.argv[2]; e = lambda k, d: float(os.environ.get(k, d))
m = trimesh.Trimesh(Z["v"], Z["f"], process=False); V0 = m.vertices.copy()
vn = m.vertex_normals; fixed = np.where(vn[:, 2] < e("DOWN_DOT", "-0.6"))[0]
L = trimesh.smoothing.laplacian_calculation(m, equal_weight=True); V = V0.copy()
for _ in range(int(e("ITER", "60"))):
    for f in (0.5, -0.53):
        V = V + f * (L.dot(V) - V); V[fixed] = V0[fixed]
if len(sys.argv) > 3:                                                      # (the base's outline smoothed too, then put back on the surface)
    from scipy.spatial import cKDTree
    SU = np.load(sys.argv[3]); SV, SF = SU["v"] + np.array([float(q) for q in os.environ.get("SURF_OFF", "0,0,0").split(",")]), SU["f"]
    sm_ = trimesh.Trimesh(SV, SF, process=False); sn = sm_.vertex_normals; ks = cKDTree(SV)
    isf = np.zeros(len(V), bool); isf[fixed] = True; E_ = m.edges_unique; E_ = E_[isf[E_[:, 0]] & isf[E_[:, 1]]]
    import scipy.sparse as sp_
    A_ = sp_.coo_matrix((np.ones(2 * len(E_)), (np.r_[E_[:, 0], E_[:, 1]], np.r_[E_[:, 1], E_[:, 0]])), shape=(len(V), len(V))).tocsr()
    dg = np.asarray(A_.sum(1)).ravel(); dg[dg == 0] = 1; Lb = sp_.diags(1 / dg) @ A_
    B = V.copy()
    for _ in range(int(e("ITER_BAZA", "30"))):
        for f in (0.5, -0.53): B[fixed] = B[fixed] + f * (Lb.dot(B)[fixed] - B[fixed])
    q = ks.query(B[fixed])[1]; B[fixed] = B[fixed] - sn[q] * np.einsum("ij,ij->i", B[fixed] - SV[q], sn[q])[:, None]   # (onto the surface)
    V = B
    for _ in range(int(e("ITER_DUPA", "10"))):
        for f in (0.5, -0.53):
            V = V + f * (L.dot(V) - V); V[fixed] = B[fixed]
m2 = trimesh.Trimesh(V, Z["f"], process=False)
ang = lambda mm: np.degrees(mm.face_adjacency_angles)
a0, a1 = ang(m), ang(m2); mv = np.linalg.norm(V - V0, axis=1)
print("NETEDA inchisa: %d varfuri (%d pe baza, fixe); mutare medie %.2f, max %.2f m; diedre 95%% %.1f -> %.1f grd, >30 grd %d -> %d; volum %.0f -> %.0f" % (
    len(V), len(fixed), mv.mean(), mv.max(), np.percentile(a0, 95), np.percentile(a1, 95), (a0 > 30).sum(), (a1 > 30).sum(), m.volume, m2.volume))
np.savez(OUT, v=V, f=Z["f"])
