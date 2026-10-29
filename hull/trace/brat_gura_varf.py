# The front arm's mouth slit cleaned where it looks odd from below (asked: near the end, by the red nacelle, it looks
# strange): towards the slit's tip the top lip dropped under the bottom one and they crossed before meeting (a crumpled
# flap); the bottom lip had a step by the nacelle's front end. Top lip past y Y0: kept at least the bottom lip's height +
# a gap that closes smoothly (smoothstep) to 0 at the tip; bottom lip's height smoothed along itself (SB m) on y B0..B1.
# The lip moves spread over the surface (harmonic: lips pinned to their targets, everything farther than L m along the
# surface pinned in place). D only, S = mirror about x MX (same vertex order). World coordinates.
# Usage: python brat_gura_varf.py <npz with brat_fata_D__v/f> <out.npz v_d,v_s> ; env Y0=470 GAP=-1 (=the gap at Y0) B0=110 B1=210 SB=12 L=70
import sys, os, numpy as np, trimesh, networkx as nx
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import spsolve
from scipy.sparse.csgraph import dijkstra
from scipy.ndimage import gaussian_filter1d
D = np.load(sys.argv[1]); OUT = sys.argv[2]; e = lambda k, d: float(os.environ.get(k, d)); MX = -1700.0
Y0, B0, B1, SB, L = e("Y0", "470"), e("B0", "110"), e("B1", "210"), e("SB", "12"), e("L", "70")
v = D["brat_fata_D__v"].astype(float); f = D["brat_fata_D__f"]; t = trimesh.Trimesh(v, f, process=False); n = len(v)
E = np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]; eu, ec = np.unique(np.sort(E, axis=1), axis=0, return_counts=True); be = eu[ec == 1]
G = nx.Graph(); G.add_edges_from(be.tolist()); cyc = np.array([q[0] for q in nx.find_cycle(G)])
up = t.vertex_normals[cyc, 2] > 0; top, bot = cyc[up], cyc[~up]
tgt = v.copy()
ob = np.argsort(v[bot, 1]); yb, zb = v[bot, 1][ob], v[bot, 2][ob]                       # bottom lip z(y)
m = (v[bot, 1] > B0 - 3 * SB) & (v[bot, 1] < B1 + 3 * SB); seq = bot[np.argsort(v[bot, 1])]; zz = v[seq, 2].copy()
zs = gaussian_filter1d(zz, SB / max(np.median(np.diff(v[seq, 1])), 0.3), mode="nearest")
w = np.clip(np.minimum(v[seq, 1] - (B0 - 2 * SB), (B1 + 2 * SB) - v[seq, 1]) / (2 * SB), 0, 1); tgt[seq, 2] = zz + w * (zs - zz)
ob = np.argsort(tgt[bot, 1]); yb, zb = tgt[bot, 1][ob], tgt[bot, 2][ob]
ytip = v[cyc, 1].max(); ztop = v[top, 2]; ytop = v[top, 1]
gap_ref = np.interp(Y0, ytop[np.argsort(ytop)], ztop[np.argsort(ytop)]) - np.interp(Y0, yb, zb)
s_ = np.clip((ytop - Y0) / (ytip - Y0), 0, 1); GP = e("GAP", "-1"); gap_ref = gap_ref if GP < 0 else GP   # GAP=m: that gap instead
g = gap_ref * (1 - s_ * s_ * (3 - 2 * s_))     # the gap closing to 0 at the tip
zmin = np.interp(ytop, yb, zb) + g; sel = ytop > Y0; tgt[top[sel], 2] = np.maximum(ztop[sel], zmin[sel])
moved = np.where(np.linalg.norm(tgt - v, axis=1) > 1e-6)[0]
w_ = np.linalg.norm(v[eu[:, 0]] - v[eu[:, 1]], axis=1); Gs = coo_matrix((w_, (eu[:, 0], eu[:, 1])), shape=(n, n)).tocsr()
dist = dijkstra(Gs, directed=False, indices=moved, min_only=True, limit=L) if len(moved) else np.full(n, np.inf)
free = np.isfinite(dist) & (dist > 0) & ~np.isin(np.arange(n), cyc)
A = coo_matrix((np.ones(len(eu) * 2), (np.r_[eu[:, 0], eu[:, 1]], np.r_[eu[:, 1], eu[:, 0]])), shape=(n, n)).tocsr()
Lp = (diags(np.asarray(A.sum(1)).ravel()) - A).tocsr(); fi = np.where(free)[0]; xi = np.where(~free)[0]
Dsp = tgt - v; X = v.copy(); X[~free] = tgt[~free]
if len(fi):
    Lff = Lp[fi][:, fi].tocsc(); Lfx = Lp[fi][:, xi]
    for k in range(3): X[fi, k] = v[fi, k] + spsolve(Lff, -Lfx @ Dsp[xi, k])
t2 = trimesh.Trimesh(X, f, process=False)
def cr(tt): a = np.degrees(tt.face_adjacency_angles); return (a > 30).sum(), (a > 45).sum(), (a > 60).sum()
nn = np.cross(X[f[:, 1]] - X[f[:, 0]], X[f[:, 2]] - X[f[:, 0]]); no = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
cross_after = (np.interp(X[top, 1], np.sort(X[bot, 1]), X[bot, 2][np.argsort(X[bot, 1])]) - X[top, 2])
print("GURA VARF: buza sus de la y %.0f tinuta peste buza jos (golul %.1f m inchis lin la varf y %.0f), treapta buzei jos y %.0f..%.0f netezita; %d varfuri de margine mutate (max %.1f m), %d varfuri de suprafata urmand (pe %.0f m)" % (
    Y0, gap_ref, ytip, B0, B1, len(moved), np.linalg.norm(Dsp, axis=1).max(), len(fi), L))
print("   buza sus sub buza jos: inainte max %.1f m, acum max %.1f m; cute >30/45/60 %d/%d/%d -> %d/%d/%d; fete intoarse %d" % (
    max(0, (np.interp(v[top, 1], yb, zb) - v[top, 2])[v[top, 1] > Y0].max()), max(0, cross_after[X[top, 1] > Y0].max()), *cr(t), *cr(t2), ((nn * no).sum(1) < 0).sum()))
S = X.copy(); S[:, 0] = 2 * MX - S[:, 0]; np.savez(OUT, v_d=X, v_s=S)
