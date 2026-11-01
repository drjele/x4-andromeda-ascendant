# A reference detail copied onto our arm (asked: R031 012_S replicated on the front arms): every vertex of the detail - its nearest
# point on the reference arm and its height along that point's normal - put at the same height above the nearest point of our arm
# to that reference point. Both arms (the detail's mirror on the other side). Writes the detail mesh per side.
# Usage: python detaliu_pe_brat.py <detail npz (v,f,uv; world = ship coords)> <reference arm npz (brat_fata_D__v/f)> <our piece npz> <out npz> <side of the detail S|D>
import sys, numpy as np, trimesh
from scipy.spatial import cKDTree
D = np.load(sys.argv[1]); RA = np.load(sys.argv[2]); NA = np.load(sys.argv[3]); OUT = sys.argv[4]; SD = sys.argv[5]
sg = -1 if SD == "S" else 1
ref = trimesh.Trimesh(RA["brat_fata_D__v"] * [sg, 1, 1], RA["brat_fata_D__f"] if sg > 0 else RA["brat_fata_D__f"][:, ::-1], process=False)
our = trimesh.Trimesh(NA["brat_fata_%s__v" % SD], NA["brat_fata_%s__f" % SD], process=False)
def vn(m):
    n = np.zeros_like(m.vertices); fn = m.face_normals * m.area_faces[:, None]
    for k in range(3): np.add.at(n, m.faces[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1), 1e-9)[:, None]
rn, on = vn(ref), vn(our); kr, ko = cKDTree(ref.vertices), cKDTree(our.vertices)
if len(sys.argv) > 6:                                                      # (normals turned outwards: away from the arm's spine)
    SPd = np.load(sys.argv[6])["spinare_brat_fata_D"] * [sg, 1, 1]; ks_ = cKDTree(SPd)
    for M_, N_ in ((ref.vertices, rn), (our.vertices, on)):
        o_ = M_ - SPd[ks_.query(M_)[1]]; N_[np.einsum("ij,ij->i", o_, N_) < 0] *= -1
V = D["v"]; i = kr.query(V)[1]; P0 = ref.vertices[i]; h = np.einsum("ij,ij->i", V - P0, rn[i]); tang = (V - P0) - rn[i] * h[:, None]
j = ko.query(P0)[1]; LIFT = float(__import__("os").environ.get("RIDICARE", "0.6"))   # (just above our surface: its own height + LIFT)
V2 = our.vertices[j] + on[j] * (np.maximum(h, 0) + LIFT)[:, None]
out = {"v_" + SD: V2, "f": D["f"], "uv": D["uv"], "li": D["li"]}
osd = "D" if SD == "S" else "S"; out["v_" + osd] = V2 * [-1, 1, 1]
np.savez(OUT, **out)
print("DETALIU pe brat: %d varfuri; inaltimea fata de brat %.1f..%.1f m; mutat fata de referinta medie %.1f, max %.1f m" % (
    len(V), h.min(), h.max(), np.linalg.norm(V2 - V, axis=1).mean(), np.linalg.norm(V2 - V, axis=1).max()))
