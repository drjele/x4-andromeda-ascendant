# Plan-view warp of the body to the flat guide line (ghid_plan2.py): the piece's rows (ps_corp_mesh.py CORP_DUMP, _S half)
# seen from above with their mirror; its outline (raster 1 m, outer contour); each outline point's move = to the nearest
# point of the guide; every row point moved by the weighted mean of the outline moves around it (weights 1/d^3: a point on
# the edge follows the edge, a point between two edges takes from both), only x, y. Repeated (the outline re-read after each
# pass). Writes the total move per row point (d) for CORP_PLAN_D, and an overlay: reference grey, guide black, piece blue.
# Usage: python plan_field.py <L.npy> <ghid.npz> <out.npz> <esantion_punte.npz> <overlay.png> [passes]
import sys, numpy as np, cv2
from scipy.spatial import cKDTree
Z_ = np.load(sys.argv[1]); L, NDK = Z_["L"], int(Z_["n_punte"]) + int(Z_["n_trecere"]); G = np.load(sys.argv[2]); OUT, REF, PNG = sys.argv[3], sys.argv[4], sys.argv[5]; NP = int(sys.argv[6]) if len(sys.argv) > 6 else 3
DMAX = float(__import__("os").environ.get("PLAN_DMAX", "80")); OPEN = "B_int" in G.files                                               # open guides (ghid_drept.py): outer B + inner B_int, each
if OPEN:                                                                # pulls only its own edge of the piece, only along its length
    def dense(Q):
        s_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]; u_ = np.arange(0, s_[-1], 0.5); return np.stack([np.interp(u_, s_, Q[:, i]) for i in range(2)], 1)
    FADE = float(__import__("os").environ.get("PLAN_ESTOMPARE", "150"))   # past each guide's end: its straight line continued and
    def run_on(Q):                                                     # its pull faded out over FADE m (no step where it ends)
        out = [Q]
        for e0, e1 in ((Q[0], Q[1]), (Q[-1], Q[-2])):
            d_ = (e0 - e1) / np.linalg.norm(e0 - e1); out.append(e0 + np.outer(np.arange(1, FADE * 1.5), d_))
        return np.vstack([out[1][::-1], Q, out[2]])
    ye, yi = G["B"][:, 1].min(), G["B_int"][:, 1].min()
    ge, gi = dense(run_on(G["B"])), dense(run_on(G["B_int"])); kge, kgi = cKDTree(ge), cKDTree(gi)
    fw = lambda y, y0: np.clip((y - (y0 - FADE)) / FADE, 0, 1) ** 2 * (3 - 2 * np.clip((y - (y0 - FADE)) / FADE, 0, 1))
    g = np.vstack([G["B"], G["B_int"][::-1]])
else: g = G["contur"]
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([g, g[:1]]), axis=0), axis=1))]; u = np.arange(0, s[-1], 0.5)
gd = np.stack([np.interp(u, s, np.vstack([g, g[:1]])[:, i]) for i in range(2)], 1); kg = cKDTree(gd)
P0 = L[..., :2].reshape(-1, 2); D = np.zeros_like(P0); PX = 1.0; XM, Y0, Y1 = 900.0, -1700.0, 700.0
def outline(P):
    A = np.vstack([P, P * [-1, 1]]); m = np.zeros((int((Y1 - Y0) / PX), int(2 * XM / PX)), np.uint8)
    m[((A[:, 1] - Y0) / PX).astype(int), ((A[:, 0] + XM) / PX).astype(int)] = 1
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    c = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0].astype(float)
    outline.mask = m; return np.stack([c[:, 0] * PX - XM, c[:, 1] * PX + Y0], 1)
def moves(o):                                                          # each outline point -> its guide point (or 0: held)
    if not OPEN: return gd[kg.query(o)[1]] - o, np.ones(len(o), bool)
    m = outline.mask; H_, W_ = m.shape; px = lambda x, y: m[np.clip(((y - Y0) / PX).astype(int), 0, H_ - 1), np.clip(((x + XM) / PX).astype(int), 0, W_ - 1)]
    sx = np.sign(o[:, 0]); toward = px(o[:, 0] - 4 * sx, o[:, 1]) == 0; below = (px(o[:, 0], o[:, 1] - 4) == 0) & (np.abs(o[:, 0]) < 80) & (o[:, 1] < 60)
    inner = (toward & (np.abs(o[:, 0]) > 2)) | below
    mv = np.zeros_like(o); ok = np.zeros(len(o), bool)
    di, ii = kgi.query(o); de, ie = kge.query(o)
    a = inner & (o[:, 1] >= yi - FADE) & (di < DMAX); mv[a] = (gi[ii[a]] - o[a]) * fw(o[a, 1], yi)[:, None]; ok[a] = o[a, 1] >= yi   # other edges (the
    b = ~inner & (o[:, 1] >= ye - FADE) & (de < DMAX); mv[b] = (ge[ie[b]] - o[b]) * fw(o[b, 1], ye)[:, None]; ok[b] = o[b, 1] >= ye   # far loop branches) stay
    return mv, ok
def dist(P):
    o = outline(P); mv, ok = moves(o); return np.linalg.norm(mv[ok], axis=1), o
K, N = L.shape[:2]; SR = float(__import__("os").environ.get("PLAN_NET", "4")); DMP = float(__import__("os").environ.get("PLAN_AMORT", "0.6"))
YF0, YF1 = float(__import__("os").environ.get("PLAN_BUCLA_Y0", "-1100")), float(__import__("os").environ.get("PLAN_BUCLA_Y1", "-1200"))
def gsm(v):                                                            # smooth a per-row parameter along the rows
    n = int(3 * SR); k = np.exp(-0.5 * (np.arange(-n, n + 1) / SR) ** 2); k /= k.sum(); return np.convolve(np.pad(v, n, mode="edge"), k, "valid")
def rows_fit(P, F):                                                    # per row: the point moves -> one move of the whole row: deck /
    P, F = P.reshape(K, N, 2), F.reshape(K, N, 2); out = P.copy()      # blend rows only stretched in x (the wall on x = 0 kept); tube
    cen = np.stack([gsm(P.mean(1)[:, i]) for i in range(2)], 1); tg = np.gradient(cen, axis=0); nt = np.linalg.norm(tg, axis=1)   # rings:
    dive = nt < 0.3 * np.median(nt)                                    # where the tube dives (no direction from above): left as built
    for k in range(1, K):
        if dive[k]: tg[k] = tg[k - 1]; nt[k] = np.linalg.norm(tg[k])
    tg /= np.maximum(nt, 1e-9)[:, None]                                # their middle
    sd = np.stack([-tg[:, 1], tg[:, 0]], 1); sd[:NDK] = [1.0, 0.0]; sh, sc_, tt = np.zeros(K), np.ones(K), np.zeros(K)   # moved, widened
    for k in range(NDK, K):                                            # one sense, continuous from ring to ring (the first one as +x)
        if sd[k] @ (sd[k - 1] if k > NDK else np.array([1.0, 0.0])) < 0: sd[k] *= -1
    for j in range(30):                                                # the stretch direction turns from x to the tube's side gradually
        k = NDK + j; w = (j + 1) / 31.0; v = (1 - w) * np.array([1.0, 0.0]) + w * sd[k]; sd[k] = v / np.linalg.norm(v)
    for k in range(K):                                                 # across the tube's own direction (shape kept)
        a = P[k] @ sd[k]; lo, hi = int(a.argmin()), int(a.argmax()); dlo, dhi = F[k, lo] @ sd[k], F[k, hi] @ sd[k]
        if k < NDK: dhi = 0.0 if abs(P[k, hi, 0]) < 1e-6 else dhi
        w0 = a[hi] - a[lo]; sc_[k] = (w0 + dhi - dlo) / max(w0, 1e-6); sh[k] = (a[lo] + dlo) - a[lo] * sc_[k]
        if k >= NDK: tt[k] = 0.5 * (F[k, lo] + F[k, hi]) @ tg[k]
    sc_[dive] = 1.0; sh[dive] = 0.0
    sc_ = np.clip(sc_, 0.6, 1.8); sc_, sh, tt = gsm(sc_), gsm(sh), gsm(tt) * 0.0   # no slide along the tube (it diverged)
    sc_ = 1 + DMP * (sc_ - 1); sh = DMP * sh
    for k in range(K):
        a = P[k] @ sd[k]; out[k] += ((a * sc_[k] + sh[k]) - a)[:, None] * sd[k] + tt[k] * tg[k]
    out = out.reshape(-1, 2); onx = np.abs(P.reshape(-1, 2)[:, 0]) < 1e-6; out[onx, 0] = 0.0; return out
for it in range(NP):
    P = P0 + D; o = outline(P)[::2]; mv, ok = moves(o)
    kd = cKDTree(o); dd, ii = kd.query(P, k=48); w = 1.0 / (dd ** 3 + 1.0); step = np.einsum("nk,nkj->nj", w, mv[ii]) / w.sum(1)[:, None]
    D = rows_fit(P, step) - P0; d_, _ = dist(P0 + D)
    if it == 0 or d_.mean() < best[0]: best = (d_.mean(), D.copy(), it + 1)
    print("TRECERE %d: conturul piesei fata de ghidaj medie %.2f / 95%% %.2f / max %.2f m" % (it + 1, d_.mean(), np.percentile(d_, 95), d_.max()))
D = best[1]                                                           # the loop's bottom (tight turn, no folds before, close already):
yr = L.mean(1)[:, 1]; wr = np.clip((yr - YF1) / (YF0 - YF1), 0, 1); wr = wr * wr * (3 - 2 * wr)   # warp faded out there
D = (D.reshape(K, N, 2) * wr[:, None, None]).reshape(-1, 2); d_, _ = dist(P0 + D)
print("ESTOMPAT sub y %.0f..%.0f: conturul fata de ghidaj medie %.2f / 95%% %.2f / max %.2f m" % (YF0, YF1, d_.mean(), np.percentile(d_, 95), d_.max()))
print("PASTRAT: trecerea %d (medie %.2f m)" % (best[2], best[0])); np.savez(OUT, d=D.reshape(L[..., :2].shape))
Q = np.load(REF)["ps"][:, :2] - [float(G["centru"]), 0]; o = outline(P0 + D); o0 = outline(P0)
sc = 0.5; im = np.full((int((Y1 - Y0) * sc) + 20, int(2 * XM * sc) + 20, 3), 255, np.uint8)
f = lambda Q: np.stack([(Q[:, 0] + XM) * sc + 10, (Y1 - Q[:, 1]) * sc + 10], 1).astype(np.int32)
im[((Y1 - Q[::7, 1]) * sc + 10).astype(int), ((Q[::7, 0] + XM) * sc + 10).astype(int)] = (190, 190, 190)
cv2.polylines(im, [f(o0)], True, (120, 200, 255), 1); [cv2.polylines(im, [f(q)], False, (0, 0, 0), 1) for q in ((G["B"], G["B_int"]) if OPEN else (g,))]; cv2.polylines(im, [f(o)], True, (220, 80, 0), 1)
cv2.imwrite(PNG, im); print("SUPRAPUNERE", PNG)
