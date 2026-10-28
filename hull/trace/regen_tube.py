# A long piece (arm, loop, strut) regenerated from scratch as one clean closed surface that follows its outer shape:
# the piece's surface sampled (the mirror piece of the other side folded onto it, so the result is exactly symmetric);
# a spine found through the points (slices by distance along a neighbour graph from one far end, centroids, then refined: points
# binned by their nearest spine station, station centroids smoothed by a spline); at each station the cross-section
# outline taken in the plane across the spine (rotation-minimising frame): per angle the outermost point (the outer
# envelope, so nothing of the inside is built); the radii smoothed across angles and along the spine (organic,
# laminar), lofted into a quad grid, the ends closed to a point; the other side made by mirroring. Writes an OBJ with
# both sides and prints the deviation from the original (metres, both ways).
# Usage: python regen_tube.py <pieces.npz> <piece> <mirror_piece|-> <out.obj> [stations] [angles] [smooth_ang] [smooth_len] [flare]
import sys, numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.interpolate import splprep, splev
from scipy.ndimage import gaussian_filter1d
a = sys.argv[1:]; Z = np.load(a[0]); P, MP, OUT = a[1], a[2], a[3]
NS = int(a[4]) if len(a) > 4 else 160; NA = int(a[5]) if len(a) > 5 else 48; SA = float(a[6]) if len(a) > 6 else 1.5; SL = float(a[7]) if len(a) > 7 else 4.0; FLARE = float(a[8]) if len(a) > 8 else 1.8
rng = np.random.default_rng(0)
def sample(v, t, n):
    T = v[t]; ar = np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1); i = rng.choice(len(t), n, p=ar / ar.sum())
    r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1); return T[i, 0] * (1 - s)[:, None] + T[i, 1] * (s * (1 - r2))[:, None] + T[i, 2] * (s * r2)[:, None]
v, t = Z["v|" + P].astype(float), Z["t|" + P]; pts = sample(v, t, 150000); side = np.sign(np.median(pts[:, 0]))
if MP != "-":
    m = sample(Z["v|" + MP].astype(float), Z["t|" + MP], 150000); m[:, 0] *= -1; pts = np.vstack([pts, m])   # mirror folded on (centre plane x = 0)
orig = pts.copy()
# spine: graph path between the two points farthest apart (approx. via double sweep)
sub = pts[rng.choice(len(pts), 6000, replace=False)]; tr = cKDTree(sub); d, j = tr.query(sub, 9)
G = coo_matrix((d[:, 1:].ravel(), (np.repeat(np.arange(len(sub)), 8), j[:, 1:].ravel())), shape=(len(sub),) * 2).tocsr(); G = G.maximum(G.T)
d0 = dijkstra(G, indices=0); a0 = int(np.argmax(np.where(np.isinf(d0), -1, d0))); da, pred = dijkstra(G, indices=a0, return_predecessors=True)
# spine = centroids of slices of equal distance along the piece from one far end (averaging across the ring: no zigzag)
ok = ~np.isinf(da); nb = np.clip((da / da[ok].max() * NS).astype(int), 0, NS - 1)
sp = np.array([sub[ok & (nb == k)].mean(0) for k in range(NS) if (ok & (nb == k)).any()])
def resample(c, n):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]; k = np.linspace(0, s[-1], n); return np.stack([np.interp(k, s, c[:, i]) for i in range(3)], 1)
spine = resample(sp, NS)
for it in range(6):                                                      # refine: stations = centroids of the points nearest to them
    lab = cKDTree(spine).query(pts)[1]; cen = np.array([pts[lab == k].mean(0) if (lab == k).any() else spine[k] for k in range(NS)])
    cen = np.vstack([cen[:1], gaussian_filter1d(cen, 3.0, axis=0, mode="nearest")[1:-1], cen[-1:]])   # smooth spine, ends kept
    spine = resample(cen, NS)
print("SPINE initial %.0f m, final %.0f m" % (np.sum(np.linalg.norm(np.diff(resample(sp, NS), axis=0), axis=1)), np.sum(np.linalg.norm(np.diff(spine, axis=0), axis=1))))
# rotation-minimising frames
tg = np.gradient(spine, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
u = np.cross(tg[0], [0, 0, 1.0]); u = u if np.linalg.norm(u) > 1e-3 else np.cross(tg[0], [1.0, 0, 0]); u /= np.linalg.norm(u); U = [u]
for k in range(1, NS):
    u = U[-1] - tg[k] * np.dot(U[-1], tg[k]); u /= np.linalg.norm(u); U.append(u)
U = np.array(U); V = np.cross(tg, U)
# sections: an ellipse per station (PCA of the section's outer points: centre offset, axes, orientation), smoothed along
# the spine (laminar, no bumps from decorations); where the section flares far beyond the tube (the root widening into a
# wing/body) the tube stops: that part belongs to the next piece
lab = cKDTree(spine).query(pts)[1]; ang = np.linspace(-np.pi, np.pi, NA, endpoint=False); E = np.full((NS, 5), np.nan)
for k in range(NS):
    q = pts[lab == k] - spine[k]
    if len(q) < 12: continue
    x, y = q @ U[k], q @ V[k]; c = np.array([np.median(x), np.median(y)]); w = np.stack([x, y], 1) - c
    ev, evec = np.linalg.eigh(np.cov(w.T)); ph = np.arctan2(evec[1, 1], evec[0, 1])
    pr = w @ evec; aa, bb = np.percentile(np.abs(pr[:, 1]), 95), np.percentile(np.abs(pr[:, 0]), 95)
    E[k] = [c[0], c[1], aa, bb, ph]
ok = ~np.isnan(E[:, 0])
for j in range(5): E[:, j] = np.interp(np.arange(NS), np.where(ok)[0], E[ok, j])
E[:, 4] = np.unwrap(2 * E[:, 4]) / 2                                     # orientation continuous (an ellipse is symmetric by pi)
size = np.maximum(E[:, 2], E[:, 3]); med = np.median(size)
flare = np.where(size > FLARE * med)[0]
lo, hi = 0, NS
if len(flare):                                                            # cut the tube before the flared end(s)
    first_half = flare[flare < NS // 2]; second_half = flare[flare >= NS // 2]
    if len(first_half): lo = int(first_half.max()) + 2
    if len(second_half): hi = int(second_half.min()) - 2
spine, U, V, E = spine[lo:hi], U[lo:hi], V[lo:hi], E[lo:hi]; NS = len(spine)
E = gaussian_filter1d(E, SL, axis=0, mode="nearest")
tipA, tipB = E[0, 2] < med * 0.6, E[-1, 2] < med * 0.6
R = None
c_, a_, b_, ph_ = E[:, :2], E[:, 2], E[:, 3], E[:, 4]
cosd = np.cos(ang[None, :] - ph_[:, None]); sind = np.sin(ang[None, :] - ph_[:, None])
loc = np.stack([a_[:, None] * cosd, b_[:, None] * sind], -1)              # ellipse points in its own axes
rotc, rots = np.cos(ph_)[:, None], np.sin(ph_)[:, None]
ex = c_[:, 0:1] + loc[..., 0] * rotc - loc[..., 1] * rots; ey = c_[:, 1:2] + loc[..., 0] * rots + loc[..., 1] * rotc
print("TUB pastrat statiile %d..%d (latiri de la capete taiate), sectiune mediana %.0f m" % (lo, hi, med))
X = spine[:, None, :] + ex[:, :, None] * U[:, None, :] + ey[:, :, None] * V[:, None, :]
cap = []                                                                  # ends: a pointed tip, or a flat cap at a cut
for k, tip in ((0, tipA), (NS - 1, tipB)):
    cap.append(spine[k] + (c_[k, 0] * U[k] + c_[k, 1] * V[k]) + (tg[min(k + lo, len(tg) - 1)] * (-1 if k == 0 else 1) * (a_[k] if tip else 0)))
verts = np.vstack([X.reshape(-1, 3), cap]); faces = []; c0, c1 = NS * NA, NS * NA + 1
for k in range(NS - 1):
    for i in range(NA):
        p_, q_ = k * NA + i, k * NA + (i + 1) % NA; faces.append((p_, q_, q_ + NA, p_ + NA))
for i in range(NA): faces.append((c0, (i + 1) % NA, i, i)); faces.append((c1, (NS - 1) * NA + i, (NS - 1) * NA + (i + 1) % NA, (NS - 1) * NA + (i + 1) % NA))
# side check: the piece built on its own side, mirrored to the other
if np.sign(np.median(verts[:, 0])) != side: verts[:, 0] *= -1
mv = verts.copy(); mv[:, 0] *= -1; off = len(verts)
allv = np.vstack([verts, mv]); allf = faces + [tuple(off + x for x in f[::-1]) for f in faces]
with open(OUT, "w") as f:
    f.write("".join("v %.3f %.3f %.3f\n" % tuple(p) for p in allv)); f.write("".join(("f %d %d %d\n" % (fc[0] + 1, fc[1] + 1, fc[2] + 1)) if fc[2] == fc[3] else ("f %d %d %d %d\n" % tuple(x + 1 for x in fc)) for fc in allf))
# deviation on this side
tri = np.array([(f[0], f[1], f[2]) for f in faces] + [(f[0], f[2], f[3]) for f in faces]); newp = sample(verts, tri, 100000)
src = orig[np.sign(orig[:, 0]) == side] if MP != "-" else orig
d1 = cKDTree(newp).query(src)[0]; d2 = cKDTree(src).query(newp)[0]
pc = lambda d: " ".join("%d%%:%.1f" % (p, np.percentile(d, p)) for p in (50, 90, 99))
print("TUB %s: %d statii x %d unghiuri -> %d fete/parte; lungime %.0f m" % (P, NS, NA, len(faces), np.sum(np.linalg.norm(np.diff(spine, axis=0), axis=1))))
print("ABATERE original->nou m", pc(d1), "| nou->original m", pc(d2))
