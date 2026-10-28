# One or more pieces regenerated as a single clean outer shell: their surfaces sampled densely (the mirror pieces of the
# other side folded on, so the result is exactly symmetric), marked in a voxel grid (VOX m), the marks thickened a little
# so the skin is closed, everything enclosed filled (no inside parts, no holes), a morphological closing of radius
# FILLET m (rounded joints where pieces meet, organic), the surface extracted (marching cubes), Taubin-smoothed (shape and
# size kept), the vertices pulled part of the way onto the original surface (accuracy), then mirrored across x = 0.
# Writes an OBJ and prints the deviation from the original (metres, both ways) and the triangle count.
# Env: SIG (field blur, voxels), PULL (0..1 pull onto the original; 0 = no dents from grooves), OPEN (m, bumps
# smaller than this removed).
# Usage: python regen_shell.py <pieces.npz> <out.obj> <vox_m> <fillet_m> <smooth_passes> <pieces...>   (piece "A/B" = A on its
#        own side + B mirrored onto it)
import sys, os, numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes
a = sys.argv[1:]; Z = np.load(a[0]); OUT = a[1]; VOX, FIL, PASS = float(a[2]), float(a[3]), int(a[4]); SPEC = a[5:]
rng = np.random.default_rng(0)
def sample(v, t, density):
    T = v[t]; ar = np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1); n = int(ar.sum() * density) + 1000
    i = rng.choice(len(t), n, p=ar / ar.sum()); r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1)
    return T[i, 0] * (1 - s)[:, None] + T[i, 1] * (s * (1 - r2))[:, None] + T[i, 2] * (s * r2)[:, None]
dens = 4.0 / VOX ** 2; pts = []
for sp in SPEC:
    for k, name in enumerate(sp.split("/")):
        p = sample(Z["v|" + name].astype(float), Z["t|" + name], dens)
        if k == 1: p[:, 0] *= -1
        pts.append(p)
P = np.vstack(pts); side = np.sign(np.median(P[:, 0])) or 1.0
P[:, 0] = np.abs(P[:, 0]) * side if abs(np.median(P[:, 0])) > 1 else P[:, 0]       # off-centre pieces: all on one side
centre = abs(np.median(P[:, 0])) <= 1                                       # a piece on the centre line: symmetrised by folding
if centre: P = np.vstack([P, P * [-1, 1, 1]])
pad = FIL + 4 * VOX; lo = P.min(0) - pad; hi = P.max(0) + pad; shape = np.ceil((hi - lo) / VOX).astype(int) + 1
idx = np.floor((P - lo) / VOX).astype(int); G = np.zeros(shape, bool); G[tuple(idx.T)] = True
G = ndi.binary_dilation(G, iterations=1)                                   # skin closed
G = ndi.binary_fill_holes(G)                                               # inside filled: only the outer shape remains
r = max(1, int(round(FIL / VOX)))
if r:
    ball = np.linalg.norm(np.mgrid[-r:r + 1, -r:r + 1, -r:r + 1], axis=0) <= r
    G = ndi.binary_closing(G, structure=ball)                              # rounded joints (fillets)
    G = ndi.binary_fill_holes(G)
SIG = float(os.environ.get("SIG", 1.0)); PULL = float(os.environ.get("PULL", 0.7)); OPEN = float(os.environ.get("OPEN", 0)); ro = int(round(OPEN / VOX))
if ro:                                                                    # small bumps (decorations standing out) removed
    ballo = np.linalg.norm(np.mgrid[-ro:ro + 1, -ro:ro + 1, -ro:ro + 1], axis=0) <= ro; G = ndi.binary_opening(G, structure=ballo)
field = ndi.gaussian_filter(G.astype(np.float32), SIG)                     # soft field: smooth iso-surface (SIG voxels)
verts, faces, _, _ = marching_cubes(field, 0.5); verts = verts * VOX + lo
# Taubin smoothing
E = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]); E = np.unique(np.sort(E, 1), axis=0); deg = np.bincount(E.ravel(), minlength=len(verts)).astype(float)
def lap(x):
    s = np.zeros_like(x); np.add.at(s, E[:, 0], x[E[:, 1]]); np.add.at(s, E[:, 1], x[E[:, 0]]); return s / np.maximum(deg, 1)[:, None] - x
for _ in range(PASS):
    for f in (0.5, -0.53): verts += f * lap(verts)
# pulled part of the way onto the original surface (the dilation made it a little fat)
tr = cKDTree(P); d, j = tr.query(verts); w = np.clip(1 - d / (3 * VOX), 0, 1)[:, None] * PULL; verts = verts * (1 - w) + P[j] * w
for _ in range(max(PASS // 4, 2)):
    for f in (0.5, -0.53): verts += f * lap(verts)
if centre:
    verts[:, 0] -= 0.0
    keep = verts[:, 0] >= 0                                                # exact symmetry for a centre piece: right half mirrored
    vv = verts.copy(); vv[~keep, 0] = -vv[~keep, 0]; verts = vv            # (folded points made it symmetric already; tidy the seam)
mv = verts.copy(); mv[:, 0] *= -1; n = len(verts)
allv = np.vstack([verts, mv]) if not centre else verts; allf = np.vstack([faces, faces[:, ::-1] + n]) if not centre else faces
with open(OUT, "w") as f:
    f.write("".join("v %.3f %.3f %.3f\n" % tuple(p) for p in allv)); f.write("".join("f %d %d %d\n" % tuple(x + 1 for x in fc) for fc in allf))
newp = sample(verts, faces, dens / 2); src = P[rng.choice(len(P), min(len(P), 300000), replace=False)]
d1 = cKDTree(newp).query(src)[0]; d2 = cKDTree(src).query(newp)[0]
pc = lambda d: " ".join("%d%%:%.1f" % (p, np.percentile(d, p)) for p in (50, 90, 99))
print("INVELIS %s: voxel %.1f m, racord %.1f m, %d triunghiuri total" % (" ".join(SPEC), VOX, FIL, len(allf)))
print("ABATERE original->nou m", pc(d1), "| nou->original m", pc(d2))
