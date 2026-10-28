# A long piece rebuilt as a mathematically smooth sweep: a smooth spine (spline with few control points) and a cross-section
# whose size/orientation also change along it as smooth splines, so the surface has no dents, holes or bumps and its slope
# runs continuously from one end to the other (laminar). The section is an ellipse (arms) or a rounded rectangle (bands).
# Spine: points ordered along the piece (graph distance from the chosen end for a connected piece, or a nearest-neighbour
# chain of part centroids for a row of separate parts such as slats), averaged in slices, fitted with a smoothing spline.
# Sections: per station the points around it, PCA in the plane across the spine (centre, half-width, half-thickness,
# angle), then each quantity fitted along the spine with a smoothing spline. Ends: a pointed tip, a flat cap, or cut where
# the piece flares (root widening into another piece). Exactly symmetric: built on one side, mirrored. UVs: u along, v round.
# Usage: python regen_sweep.py <pieces.npz> <out.obj> <mode: arm|band> <piece[/mirror]>... [--stations N] [--knots K]
import sys, numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.interpolate import splprep, splev, UnivariateSpline
args = sys.argv[1:]; Z = np.load(args[0]); OUT, MODE = args[1], args[2]
opt = {k: float(v) for k, v in zip(args[3::1], args[4::1]) if k.startswith("--")}; names = [x for x in args[3:] if not x.startswith("--") and not x.replace(".", "").isdigit()]
NS = int(opt.get("--stations", 200)); NK = int(opt.get("--knots", 7)); NA = 64; FLARE = opt.get("--flare", 1.7)
rng = np.random.default_rng(0)
def sample(v, t, n):
    T = v[t]; ar = np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1); i = rng.choice(len(t), n, p=ar / ar.sum())
    r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1); return T[i, 0] * (1 - s)[:, None] + T[i, 1] * (s * (1 - r2))[:, None] + T[i, 2] * (s * r2)[:, None]
pts = []; parts = []
for spec in names:
    for k, nm in enumerate(spec.split("/")):
        v = Z["v|" + nm].astype(float); t = Z["t|" + nm]; p = sample(v, t, 120000)
        if k == 1: p[:, 0] *= -1
        pts.append(p)
        if MODE == "band":                                                  # separate slats: their centroids (connected components)
            from scipy.sparse.csgraph import connected_components
            e = np.vstack([t[:, [0, 1]], t[:, [1, 2]]]); A = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(v),) * 2)
            n, lab = connected_components(A, directed=False); vv = v.copy()
            if k == 1: vv[:, 0] *= -1
            parts += [vv[lab == i].mean(0) for i in range(n) if (lab == i).sum() > 6]
P = np.vstack(pts); side = np.sign(np.median(P[:, 0])) or 1.0; P[:, 0] = np.abs(P[:, 0]) * side
def smooth_curve(c, n, knots):  # least-squares cubic spline, `knots` inner knots, sampled at n points
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]; u = s / s[-1]
    t = np.linspace(0, 1, knots + 2)[1:-1]; from scipy.interpolate import make_lsq_spline
    tt = np.r_[[0] * 4, t, [1] * 4]; spl = [make_lsq_spline(u, c[:, i], tt, k=3) for i in range(3)]
    q = np.linspace(0, 1, n); return np.stack([f(q) for f in spl], 1), spl
if MODE == "arm":
    sub = P[rng.choice(len(P), 8000, replace=False)]; tr = cKDTree(sub); d, j = tr.query(sub, 10)
    G = coo_matrix((d[:, 1:].ravel(), (np.repeat(np.arange(len(sub)), 9), j[:, 1:].ravel())), shape=(len(sub),) * 2).tocsr(); G = G.maximum(G.T)
    end = int(np.argmax(sub[:, 1])); da = dijkstra(G, indices=end); ok = ~np.isinf(da)
    nb = np.clip((da / da[ok].max() * 60).astype(int), 0, 59); c = np.array([sub[ok & (nb == k)].mean(0) for k in range(60) if (ok & (nb == k)).any()])
else:
    C = np.array(parts); C[:, 0] = np.abs(C[:, 0]) * side; order = [int(np.argmax(C[:, 1]))]; left = set(range(len(C))) - set(order)
    while left:
        j = min(left, key=lambda i: np.linalg.norm(C[i] - C[order[-1]])); order.append(j); left.remove(j)
    c = C[order]
    # outlier slats (off the row: a stray piece at an end twists the band) dropped: far from a smooth fit of the row
    for _ in range(2):
        f, _s = smooth_curve(c, len(c), max(3, NK // 2)); r = np.linalg.norm(c - f, axis=1); c = c[r < max(3 * np.median(r), 8)]
spine, spl = smooth_curve(c, NS, NK)
tg = np.gradient(spine, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
u0 = np.cross(tg[0], [0, 0, 1.0]); u0 /= np.linalg.norm(u0); U = [u0]
for k in range(1, NS):
    u = U[-1] - tg[k] * np.dot(U[-1], tg[k]); U.append(u / np.linalg.norm(u))
U = np.array(U); V = np.cross(tg, U)
lab = cKDTree(spine).query(P)[1]; S = np.full((NS, 5), np.nan)
for k in range(NS):
    q = P[lab == k] - spine[k]
    if len(q) < 40: continue                                             # thin end stations: too few points for a section
    x, y = q @ U[k], q @ V[k]; c2 = np.array([np.median(x), np.median(y)]); w = np.stack([x, y], 1) - c2
    ev, evec = np.linalg.eigh(np.cov(w.T)); ax = evec[:, 1]; ang = np.arctan2(ax[1], ax[0]); pr = w @ evec
    S[k] = [c2[0], c2[1], np.percentile(np.abs(pr[:, 1]), 96), np.percentile(np.abs(pr[:, 0]), 96), ang]
okk = ~np.isnan(S[:, 0]); S[:, 4] = np.where(okk, S[:, 4], 0)
S[okk, 4] = np.unwrap(2 * S[okk, 4]) / 2
lo, hi = 0, NS
if MODE == "arm":                                                         # the root where the arm flares into the next piece: cut
    big = np.where(okk & (np.maximum(S[:, 2], S[:, 3]) > FLARE * np.nanmedian(np.maximum(S[:, 2], S[:, 3]))))[0]
    big = big[big > NS // 2]
    if len(big): hi = int(big.min())
if MODE == "band":                                                        # the band's ends trimmed where its stations turn sharply (a twisted cap)
    curv = np.degrees(np.arccos(np.clip((tg[1:] * tg[:-1]).sum(1), -1, 1))); sharp = np.where(curv > 3.0)[0]
    lo = int(sharp[sharp < NS // 5].max()) + 2 if (sharp < NS // 5).any() else 0
    hi = int(sharp[sharp > 4 * NS // 5].min()) - 1 if (sharp > 4 * NS // 5).any() else NS
    print("BANDA capete taiate: %d..%d (cotituri > 3 grade/statie)" % (lo, hi))
x = np.arange(NS)[lo:hi]; m = okk[lo:hi]
def fit(col, kn=NK):
    t = np.linspace(x[0], x[-1], kn + 2)[1:-1]; from scipy.interpolate import LSQUnivariateSpline
    return LSQUnivariateSpline(x[m], col[lo:hi][m], t, k=3)(x)
cx, cy, A, B = (fit(S[:, i]) for i in range(4)); PH = fit(S[:, 4], 3);                       # the twist: only 3 control points (no flips at the ends)
A = np.maximum(A, 1.0); B = np.maximum(B, 0.5)
sp, U2, V2, T2 = spine[lo:hi], U[lo:hi], V[lo:hi], tg[lo:hi]; n = len(sp)
if MODE == "arm":                                                         # pointed tip at the start: the section closes smoothly
    taper = np.clip(np.arange(n) / max(n * 0.04, 1), 0, 1) ** 0.5; A *= taper; B *= taper
th = np.linspace(0, 2 * np.pi, NA, endpoint=False)
if MODE == "band":                                                        # rounded rectangle (superellipse) section
    e = 0.25; ct, st = np.cos(th), np.sin(th); sx, sy = np.sign(ct) * np.abs(ct) ** e, np.sign(st) * np.abs(st) ** e
else: sx, sy = np.cos(th), np.sin(th)
lx = A[:, None] * sx[None]; ly = B[:, None] * sy[None]; cp, sp_ = np.cos(PH)[:, None], np.sin(PH)[:, None]
ex = cx[:, None] + lx * cp - ly * sp_; ey = cy[:, None] + lx * sp_ + ly * cp
X = sp[:, None, :] + ex[..., None] * U2[:, None, :] + ey[..., None] * V2[:, None, :]
verts = list(X.reshape(-1, 3)); faces = []; uvs = []
L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(sp, axis=0), axis=1))]
for k in range(n):
    for i in range(NA + 1): uvs.append((L[k] / L[-1], i / NA))
for k in range(n - 1):
    for i in range(NA):
        a_, b_ = k * NA + i, k * NA + (i + 1) % NA; ua, ub = k * (NA + 1) + i, k * (NA + 1) + i + 1
        faces.append(((a_, ua), (b_, ub), (b_ + NA, ub + NA + 1), (a_ + NA, ua + NA + 1)))
for k, sgn in ((0, -1), (n - 1, 1)):                                       # end caps (a point at a tip, flat elsewhere)
    cen = sp[k] + cx[k] * U2[k] + cy[k] * V2[k]; verts.append(cen); ci = len(verts) - 1; uvs.append((L[k] / L[-1], 0.5)); cu = len(uvs) - 1
    for i in range(NA):
        a_, b_ = k * NA + i, k * NA + (i + 1) % NA; ua, ub = k * (NA + 1) + i, k * (NA + 1) + i + 1
        faces.append(((ci, cu), (b_, ub), (a_, ua)) if sgn < 0 else ((ci, cu), (a_, ua), (b_, ub)))
V_ = np.array(verts)
if np.sign(np.median(V_[:, 0])) != side: V_[:, 0] *= -1
M = V_.copy(); M[:, 0] *= -1; nv, nu = len(V_), len(uvs)
with open(OUT, "w") as f:
    f.write("".join("v %.3f %.3f %.3f\n" % tuple(p) for p in np.vstack([V_, M]))); f.write("".join("vt %.5f %.5f\n" % uv for uv in uvs + uvs))
    for fc in faces: f.write("f " + " ".join("%d/%d" % (a + 1, b + 1) for a, b in fc) + "\n")
    for fc in faces: f.write("f " + " ".join("%d/%d" % (a + 1 + nv, b + 1 + nu) for a, b in fc[::-1]) + "\n")
tri = []
for fc in faces:
    ids = [a for a, _ in fc]; tri += [(ids[0], ids[i], ids[i + 1]) for i in range(1, len(ids) - 1)]
newp = sample(V_, np.array(tri), 100000); src = P
d1 = cKDTree(newp).query(src)[0]; d2 = cKDTree(src).query(newp)[0]
pc = lambda d: " ".join("%d%%:%.1f" % (p, np.percentile(d, p)) for p in (50, 90, 99))
print("SWEEP %s %s: %d statii pastrate din %d, %d puncte de control, lungime %.0f m, %d fete/parte, sectiune %.0fx%.0f m (mediana)" % (MODE, " ".join(names), n, NS, NK, L[-1], len(faces), 2 * np.median(A), 2 * np.median(B)))
print("ABATERE original->nou m", pc(d1), "| nou->original m", pc(d2))
