# The PS split into its 2 components (asked: break sep_PS into its two components): the top face and the bottom face of the
# original (ps_orig11: built as "sus" + "jos", met on the outline at mid-thickness). A face is top / bottom by the sign of
# its normal's z, the normals first averaged over neighbours (NM passes, so channel walls and small steps do not flip);
# islands smaller than MIN_A m2 of one label are given to the other - the seam runs along the outline, one line.
# Usage: python ps_sus_jos.py <faces.npz:key> <ps.npz v> <out.npz> ; env SJ_NM=6 SJ_MIN_A=400
import sys, os, numpy as np, trimesh
from scipy.sparse import coo_matrix, diags
from scipy.sparse.csgraph import connected_components
fn, k = sys.argv[1].split(":"); f = np.load(fn)[k]; V = np.load(sys.argv[2])["v"].astype(float); OUT = sys.argv[3]
NM, MA = int(os.environ.get("SJ_NM", "6")), float(os.environ.get("SJ_MIN_A", "400"))
t = trimesh.Trimesh(V, f, process=False); fa = t.face_adjacency; nf = len(f)
A = coo_matrix((np.ones(len(fa) * 2), (np.r_[fa[:, 0], fa[:, 1]], np.r_[fa[:, 1], fa[:, 0]])), shape=(nf, nf)).tocsr()
W = diags(1 / np.asarray(A.sum(1)).ravel()) @ A; N = t.face_normals * t.area_faces[:, None]
for _ in range(NM): N = 0.5 * N + 0.5 * (W @ N)
sus = N[:, 2] > 0
for _ in range(3):                                     # small islands go to the other side
    ch = 0
    for lab in (True, False):
        m = sus == lab; idx = np.where(m)[0]; sub = A[idx][:, idx]; nc, cc = connected_components(sub, directed=False)
        ar = np.bincount(cc, t.area_faces[idx]); small = ar < MA
        if small.any(): sus[idx[small[cc]]] = not lab; ch += small.sum()
    if not ch: break
def info(m):
    p = trimesh.Trimesh(V, f[m], process=False); return "%d fete, arie %.0f m2, z %.0f..%.0f, %d bucati" % (m.sum(), p.area, p.bounds[0, 2], p.bounds[1, 2], len(p.split(only_watertight=False)))
print("PS SUS: " + info(sus)); print("PS JOS: " + info(~sus))
e = t.edges_unique[[i for i in range(len(fa)) if sus[fa[i, 0]] != sus[fa[i, 1]]]] if False else None
cut = sus[fa[:, 0]] != sus[fa[:, 1]]; ce = t.face_adjacency_edges[cut]; z = V[ce].mean(1)[:, 2]
print("CUSATURA sus|jos: %d muchii, z %.1f..%.1f (medie %.1f)" % (cut.sum(), z.min(), z.max(), z.mean()))
np.savez(OUT, sus=np.where(sus)[0], jos=np.where(~sus)[0])
