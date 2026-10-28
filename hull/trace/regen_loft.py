# A band made of many thin slats (the red nacelle: ribs + plates) rebuilt as ONE smooth object that passes exactly through
# the real outline of every slat: the slats split apart (connected pieces), ordered along the band (nearest-neighbour chain
# from the end farthest forward), each slat's plane = its thinnest direction, its real outline = the convex hull of its
# points in that plane, resampled at NA angles from its centre in a frame carried along the chain (no twist); the band is
# lofted through these outlines with a smooth (Catmull-Rom) interpolation between them, the ends closed. A stripe map is
# written: the length positions covered by ribs (the "dark" pieces) so the texture puts dark red exactly there. Built on
# one side and mirrored (exact symmetry). Prints the deviation from the slats' outer points.
# Usage: python regen_loft.py <pieces.npz> <out.obj> <stripes.json> <dark_piece> <other_piece>...   (pieces of one side)
import sys, json, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import ConvexHull, cKDTree
Z = np.load(sys.argv[1]); OUT, SJ = sys.argv[2], sys.argv[3]; NAMES = sys.argv[4:]; NA = 48; SUB = 6
slats = []
for k, nm in enumerate(NAMES):
    v = Z["v|" + nm].astype(float); t = Z["t|" + nm]; e = np.vstack([t[:, [0, 1]], t[:, [1, 2]]])
    n, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(v),) * 2), directed=False)
    for i in range(n):
        p = v[lab == i]
        if len(p) >= 8: slats.append((p, k == 0))
print("PLACI %d (%d nervuri)" % (len(slats), sum(d for _, d in slats)))
C = np.array([p.mean(0) for p, _ in slats]); order = [int(np.argmax(C[:, 1]))]; left = set(range(len(C))) - set(order)
while left:
    j = min(left, key=lambda i: np.linalg.norm(C[i] - C[order[-1]])); order.append(j); left.remove(j)
slats = [slats[i] for i in order]; C = C[order]
# merge slats lying at the same station (a rib and a plate side by side) is not needed: each is a station of its own
tan = np.gradient(C, axis=0); tan /= np.linalg.norm(tan, axis=1)[:, None]
outl = []; U = None
for k, (p, dark) in enumerate(slats):
    q = p - C[k]; ev, evec = np.linalg.eigh(np.cov(q.T)); nrm = evec[:, 0]
    if np.dot(nrm, tan[k]) < 0: nrm = -nrm
    nrm = 0.5 * nrm + 0.5 * tan[k]; nrm /= np.linalg.norm(nrm)            # the slat plane, kept close to the band direction
    if U is None: U = np.cross(nrm, [0, 0, 1.0]); U /= np.linalg.norm(U)
    U = U - nrm * np.dot(U, nrm); U /= np.linalg.norm(U); V = np.cross(nrm, U)
    x, y = q @ U, q @ V; h = ConvexHull(np.stack([x, y], 1)); hx, hy = x[h.vertices], y[h.vertices]
    a = np.arctan2(hy, hx); o = np.argsort(a); a, r = a[o], np.hypot(hx, hy)[o]
    th = np.linspace(-np.pi, np.pi, NA, endpoint=False); R = np.interp(th, a, r, period=2 * np.pi)
    outl.append(C[k] + R[:, None] * (np.cos(th)[:, None] * U + np.sin(th)[:, None] * V))
    slats[k] = (p, dark, k)
O = np.array(outl)                                                         # (stations, NA, 3)
# light smoothing across stations (rib and plate outlines differ a little: no ripples)
Os = O.copy()
for _ in range(2): Os[1:-1] = 0.25 * Os[:-2] + 0.5 * Os[1:-1] + 0.25 * Os[2:]
O = 0.5 * O + 0.5 * Os
def catmull(P0, P1, P2, P3, t): return 0.5 * (2 * P1 + (-P0 + P2) * t + (2 * P0 - 5 * P1 + 4 * P2 - P3) * t * t + (-P0 + 3 * P1 - 3 * P2 + P3) * t ** 3)
rings = []; station_of = []
n = len(O)
for k in range(n - 1):
    for s in range(SUB):
        t = s / SUB; rings.append(catmull(O[max(k - 1, 0)], O[k], O[k + 1], O[min(k + 2, n - 1)], t)); station_of.append(k + t)
rings.append(O[-1]); station_of.append(n - 1); X = np.array(rings); m = len(X)
L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(X.mean(1), axis=0), axis=1))]; uL = L / L[-1]
verts = list(X.reshape(-1, 3)); uvs = [(uL[k], i / NA) for k in range(m) for i in range(NA + 1)]; faces = []
for k in range(m - 1):
    for i in range(NA):
        a_, b_ = k * NA + i, k * NA + (i + 1) % NA; ua, ub = k * (NA + 1) + i, k * (NA + 1) + i + 1
        faces.append(((a_, ua), (b_, ub), (b_ + NA, ub + NA + 1), (a_ + NA, ua + NA + 1)))
for k, sgn in ((0, -1), (m - 1, 1)):
    verts.append(X[k].mean(0)); ci = len(verts) - 1; uvs.append((uL[k], 0.5)); cu = len(uvs) - 1
    for i in range(NA):
        a_, b_ = k * NA + i, k * NA + (i + 1) % NA; ua, ub = k * (NA + 1) + i, k * (NA + 1) + i + 1
        faces.append(((ci, cu), (b_, ub), (a_, ua)) if sgn < 0 else ((ci, cu), (a_, ua), (b_, ub)))
# stripes: the length position of every rib (dark) with its thickness along the band
st = np.array(station_of); stripes = []
for p, dark, k in slats:
    if not dark: continue
    i = int(np.argmin(np.abs(st - k))); th_ = np.ptp((p - C[k]) @ tan[k]); stripes.append([float(uL[i]), float(th_ / L[-1])])
json.dump({"length_m": float(L[-1]), "stripes": stripes}, open(SJ, "w"))
Vv = np.array(verts); M = Vv.copy(); M[:, 0] *= -1; nv, nu = len(Vv), len(uvs)
with open(OUT, "w") as f:
    f.write("".join("v %.3f %.3f %.3f\n" % tuple(q) for q in np.vstack([Vv, M]))); f.write("".join("vt %.5f %.5f\n" % uv for uv in uvs + uvs))
    for fc in faces: f.write("f " + " ".join("%d/%d" % (a + 1, b + 1) for a, b in fc) + "\n")
    for fc in faces: f.write("f " + " ".join("%d/%d" % (a + 1 + nv, b + 1 + nu) for a, b in fc[::-1]) + "\n")
allp = np.vstack([p for p, _, _ in slats]); d = cKDTree(X.reshape(-1, 3)).query(allp)[0]
print("NACELA: %d statii (placi), lungime %.0f m, %d dungi (nervuri), %d fete/parte; distanta puncte placi -> suprafata m: 50%%:%.1f 90%%:%.1f 99%%:%.1f"
      % (n, L[-1], len(stripes), len(faces), np.percentile(d, 50), np.percentile(d, 90), np.percentile(d, 99)))
