# The front arm's mouth in one plane (asked: the outline of brat_fata's mouth in a plane, the bottom surface - the longer one -
# as reference): the bottom already ends in the nacelle-end plane the arm was cut to; the top surface is stretched along the
# plane's normal until its edge lies in that plane. Each vertex takes the gap of its nearest mouth-edge vertex (along the
# surface, Dijkstra over the edges), moved by gap * w, w = smoothstep from 1 on the edge to 0 at L m along the surface (L
# about twice the largest gap, so nothing folds); vertices nearer the bottom's edge do not move. D only, S = its mirror
# (same vertex order). Usage: python brat_gura_plan.py <pieces.npz> <out.npz> [L]
import sys, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
D = np.load(sys.argv[1]); OUT = sys.argv[2]; L = float(sys.argv[3]) if len(sys.argv) > 3 else 180.0; MX = -1700.0
v = D["brat_fata_D__v"].astype(float); f = D["brat_fata_D__f"]
n = np.array([-0.975, 0.219, -0.027]); n /= np.linalg.norm(n); p0 = np.array([-1568., 216., 288.])   # arm_full BRAT_CAPAT_PLAN
E = np.sort(np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]], 1); E, c = np.unique(E, axis=0, return_counts=True)
R = np.unique(E[c == 1]); R = R[v[R, 0] - MX < 200]                      # the mouth's edge (inner end)
gap = (v[R] - p0) @ (-n); top, bot = R[gap > 2], R[gap <= 2]
w_ = np.linalg.norm(v[E[:, 0]] - v[E[:, 1]], axis=1); G = coo_matrix((w_, (E[:, 0], E[:, 1])), shape=(len(v),) * 2).tocsr()
dt, _, st = dijkstra(G, directed=False, indices=top, min_only=True, limit=L, return_predecessors=True)
db = dijkstra(G, directed=False, indices=bot, min_only=True, limit=L)
B = float(__import__("os").environ.get("GURA_TRECERE", "40"))          # top -> bottom handover blended over B m
ok = np.isfinite(dt); g = np.zeros(len(v)); g[ok] = ((v[st[ok]] - p0) @ (-n))
db = np.where(np.isfinite(db), db, L * 4); hb = np.clip((db - dt) / B + 0.5, 0, 1); hb = hb * hb * (3 - 2 * hb)
t = np.clip(dt / L, 0, 1); w = np.where(ok, (1 - (3 * t ** 2 - 2 * t ** 3)) * hb, 0); d = g * w
A = coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(len(v),) * 2).tocsr()
deg = np.asarray(A.sum(1)).ravel(); fix = np.zeros(len(v), bool); fix[R] = True; dfix = d.copy(); dfix[top] = gap[gap > 2]
dfix[bot] = 0
vn = np.zeros_like(v); fn_ = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
for k in range(3): np.add.at(vn, f[:, k], fn_)
vn /= np.linalg.norm(vn, axis=1)[:, None] + 1e-12; jos = (vn[:, 2] < -0.5) & ~(dt < 15)   # the bottom surface (facing down) stays put, not the top edge's curl
fix |= jos; dfix[jos] = 0; d = dfix.copy()
for _ in range(int(__import__("os").environ.get("GURA_NETEZIRE", "300"))):   # the displacement smoothed over the surface
    d = np.where(fix, dfix, (A @ d) / np.maximum(deg, 1))                    # (edge pinned: top on the plane, bottom still)
V = v + d[:, None] * n
o1 = v[f[:, 1]] - v[f[:, 0]]; o2 = v[f[:, 2]] - v[f[:, 0]]; no = np.cross(o1, o2)
for r_ in range(30):                                   # faces still flipped: their neighbourhood relaxed (positions), edge kept
    nn = np.cross(V[f[:, 1]] - V[f[:, 0]], V[f[:, 2]] - V[f[:, 0]]); bad = np.unique(f[(nn * no).sum(1) < 0])
    if not len(bad): break
    zone = np.zeros(len(v), bool); zone[bad] = True
    for _ in range(3): zone |= (A @ zone.astype(float)) > 0
    zone &= ~np.isin(np.arange(len(v)), R)
    for _ in range(20): V[zone] = ((A @ V) / np.maximum(deg, 1)[:, None])[zone]
gap2 = (V[top] - p0) @ (-n)
print("GURA: %d varfuri pe margine sus mutate pe plan (inainte max %.1f m, acum max %.3f m), %d varfuri mutate in total, L %.0f m"
      % (len(top), gap[gap > 2].max(), np.abs(gap2).max(), (g * w > 0.01).sum(), L))
e1 = V[f[:, 1]] - V[f[:, 0]]; e2 = V[f[:, 2]] - V[f[:, 0]]; nn = np.cross(e1, e2)
o1 = v[f[:, 1]] - v[f[:, 0]]; o2 = v[f[:, 2]] - v[f[:, 0]]; no = np.cross(o1, o2)
flip = ((nn * no).sum(1) < 0).sum(); print("fete intoarse dupa intindere: %d; aria min %.3f m2" % (flip, 0.5 * np.linalg.norm(nn, axis=1).min()))
S = V.copy(); S[:, 0] = 2 * MX - S[:, 0]
np.savez(OUT, v_d=V, v_s=S)
