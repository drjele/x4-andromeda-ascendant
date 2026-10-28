# The red nacelle as one smooth V lying on its side (the user's rule, as for the attack blades): the base on the arm's inner
# edge, as thick there as the arm, the V narrowing to its point toward the inside; the V follows the row of real slats
# (ribs + plates): per slat its centre, the direction from the arm to the slat (depth) and the slat's real extent in depth
# and across; every quantity then fitted along the row with a smoothing spline (few control points), so the surfaces are
# perfectly smooth; the V's corners slightly rounded. Stripes (rib positions) written for the texture. Built on one side
# and mirrored (exact symmetry).
# Usage: python regen_vee.py <pieces.npz> <out.obj> <stripes.json> <arm_piece> <dark_piece> <other_piece>... [--knots K]
import sys, json, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from scipy.interpolate import make_lsq_spline
a = sys.argv[1:]; K = 7
if "--knots" in a: i = a.index("--knots"); K = int(a[i + 1]); a = a[:i] + a[i + 2:]
Z = np.load(a[0]); OUT, SJ, ARM = a[1], a[2], a[3]; NAMES = a[4:]; NS, NR = 220, 12
arm = Z["v|" + ARM].astype(float); tarm = cKDTree(arm)
slats = []
for k, nm in enumerate(NAMES):
    v = Z["v|" + nm].astype(float); t = Z["t|" + nm]; e = np.vstack([t[:, [0, 1]], t[:, [1, 2]]])
    n, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(v),) * 2), directed=False)
    slats += [(v[lab == i], k == 0) for i in range(n) if (lab == i).sum() >= 8]
C = np.array([p.mean(0) for p, _ in slats]); order = [int(np.argmax(C[:, 1]))]; left = set(range(len(C))) - set(order)
while left:
    j = min(left, key=lambda i: np.linalg.norm(C[i] - C[order[-1]])); order.append(j); left.remove(j)
slats = [slats[i] for i in order]; C = C[order]
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]; u = s / s[-1]
tan = np.gradient(C, axis=0); tan /= np.linalg.norm(tan, axis=1)[:, None]
rows = []
for k, (p, dark) in enumerate(slats):
    q = arm[tarm.query(C[k])[1]]                                            # nearest arm point: the V's base side
    dvec = C[k] - q; dvec -= tan[k] * np.dot(dvec, tan[k]); dvec /= np.linalg.norm(dvec)   # depth: from the arm inward, across the band
    wvec = np.cross(tan[k], dvec)                                            # across: the V's opening
    pd, pw = (p - C[k]) @ dvec, (p - C[k]) @ wvec
    base = C[k] + dvec * pd.min(); apex = C[k] + dvec * pd.max()
    half = np.percentile(np.abs(pw - np.median(pw)), 95); cw = np.median(pw)
    rows.append(np.r_[base + wvec * cw, apex + wvec * cw, wvec, [half]])
R = np.array(rows)
def fit(col):
    tt = np.r_[[0] * 4, np.linspace(0, 1, K + 2)[1:-1], [1] * 4]; return make_lsq_spline(u, col, tt, k=3)(np.linspace(0, 1, NS))
F = np.stack([fit(R[:, j]) for j in range(R.shape[1])], 1)
B, A_, W = F[:, 0:3], F[:, 3:6], F[:, 6:9]; W /= np.linalg.norm(W, axis=1)[:, None]; H = np.maximum(F[:, 9], 1.0)
# the V section: base edge (two corners at the arm, opening = arm thickness there) and the point inward, corners rounded
prof = []
for t in np.linspace(0, 1, NR, endpoint=False): prof.append((0.0, -1 + 2 * t))          # base edge, along the opening
for t in np.linspace(0, 1, NR, endpoint=False): prof.append((t, 1 - t))                  # upper flank to the point
for t in np.linspace(0, 1, NR, endpoint=False): prof.append((1 - t, -t))                 # lower flank back to the base
prof = np.array(prof); NA = len(prof)
pr = prof.copy()
for _ in range(3): pr = 0.25 * np.roll(pr, 1, 0) + 0.5 * pr + 0.25 * np.roll(pr, -1, 0)   # rounded corners
X = B[:, None, :] + pr[None, :, 0:1] * (A_ - B)[:, None, :] + pr[None, :, 1:2] * H[:, None, None] * W[:, None, :]
# ends: the V tapers to nothing over the last few percent (smooth tips)
tap = np.minimum(1, np.minimum(np.arange(NS), NS - 1 - np.arange(NS)) / (0.03 * NS)) ** 0.5
mid = X.mean(1, keepdims=True); X = mid + (X - mid) * tap[:, None, None]
L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(X.mean(1), axis=0), axis=1))]; uL = L / L[-1]
verts = X.reshape(-1, 3); uvs = [(uL[k], i / NA) for k in range(NS) for i in range(NA + 1)]; faces = []
for k in range(NS - 1):
    for i in range(NA):
        a_, b_ = k * NA + i, k * NA + (i + 1) % NA; ua, ub = k * (NA + 1) + i, k * (NA + 1) + i + 1
        faces.append(((a_, ua), (b_, ub), (b_ + NA, ub + NA + 1), (a_ + NA, ua + NA + 1)))
stripes = []
for (p, dark), uk in zip(slats, u):
    if dark: stripes.append([float(uk), float(np.ptp(p @ tan[0]) / L[-1]) if False else float(np.ptp((p - p.mean(0)) @ (np.gradient(C, axis=0)[0] / np.linalg.norm(np.gradient(C, axis=0)[0]))) / L[-1])])
json.dump({"length_m": float(L[-1]), "stripes": stripes}, open(SJ, "w"))
M = verts.copy(); M[:, 0] *= -1; nv, nu = len(verts), len(uvs)
with open(OUT, "w") as f:
    f.write("".join("v %.3f %.3f %.3f\n" % tuple(q) for q in np.vstack([verts, M]))); f.write("".join("vt %.5f %.5f\n" % x for x in uvs + uvs))
    for fc in faces: f.write("f " + " ".join("%d/%d" % (p_ + 1, q_ + 1) for p_, q_ in fc) + "\n")
    for fc in faces: f.write("f " + " ".join("%d/%d" % (p_ + 1 + nv, q_ + 1 + nu) for p_, q_ in fc[::-1]) + "\n")
allp = np.vstack([p for p, _ in slats]); d = cKDTree(verts).query(allp)[0]
print("V CULCAT: %d placi, lungime %.0f m, adancime V mediana %.0f m, deschidere la baza %.0f m, %d puncte de control; placi->suprafata m 50%%:%.1f 90%%:%.1f 99%%:%.1f"
      % (len(slats), L[-1], np.median(np.linalg.norm(A_ - B, axis=1)), 2 * np.median(H), K, np.percentile(d, 50), np.percentile(d, 90), np.percentile(d, 99)))
