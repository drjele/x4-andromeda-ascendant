# One face of the guides split into its components and put back together (asked: break it into components, clean each on
# its own, then assemble them into one - the stray ribs out, the details kept): on a CELL m grid the face's step edges
# (slope steeper than STEEP) cut it into panels; panels smaller than AMIN m2 or thinner than TMIN m (the stray ribs) are
# dropped and their cells given to the neighbours; every panel smoothed on its own (SIGP m, only its cells, carried a bit
# past its edge); the panels' borders smoothed in plan (SIGB m) so they run as clean lines; the face rebuilt from them, the
# steps kept as edges with a narrow bevel (BEV m). The right half mirrored. Writes the terrain with that face replaced and
# a sheet (panels coloured, before / after heights).
# Usage: python fata_componente.py <teren.npz> <top|bot> <out.npz> <sheet.png> [cell] [steep] [amin] [tmin] [sigp] [sigb] [bev]
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.ndimage import map_coordinates, gaussian_filter, label, distance_transform_edt as edt, binary_erosion
T = dict(np.load(sys.argv[1])); KEY, OUT, SHEET = sys.argv[2], sys.argv[3], sys.argv[4]
P = [float(t) for t in sys.argv[5:]] + [None] * 7
C = P[0] or 0.5; STEEP = P[1] or 0.8; AMIN = P[2] or 150.0; TMIN = P[3] or 2.5; SIGP = P[4] or 3.0; SIGB = P[5] or 1.5; BEV = P[6] or 0.5
x0, y0, GC = float(T["x0"]), float(T["y0"]), float(T["cell"]); gny, gnx = T[KEY].shape; nx, ny = int(gnx * GC / C), int(gny * GC / C)
yy, xx = np.mgrid[0:ny, 0:nx]; gi, gj = (yy + 0.5) * C / GC - 0.5, (xx + 0.5) * C / GC - 0.5
H = map_coordinates(T[KEY].astype(float), [gi, gj], order=1, mode="nearest"); foot = map_coordinates(T["foot"].astype(float), [gi, gj], order=1) > 0.5
gy_, gx_ = np.gradient(gaussian_filter(H, 0.5 / C), C); slope = np.hypot(gx_, gy_)
flat = foot & (slope < STEEP); lab, n = label(flat)
area = np.bincount(lab.ravel(), minlength=n + 1) * C * C; thick = np.zeros(n + 1)
d = edt(flat) * C; np.maximum.at(thick, lab.ravel(), d.ravel())
keep = (area >= AMIN) & (thick >= TMIN); keep[0] = False
lab = np.where(keep[lab], lab, 0); ids = np.nonzero(keep)[0]
_, (ii, jj) = edt(lab == 0, return_indices=True); full = np.where(foot, lab[ii, jj], 0)   # every cell to its nearest kept panel
sm = np.full((ny, nx), -np.inf); best = np.zeros((ny, nx), int); Z = np.zeros((ny, nx))
for k in ids:                                                           # each panel: smoothed on its own, its border smoothed
    m = lab == k; w = gaussian_filter(m.astype(float), SIGP / C)
    zk = gaussian_filter(np.where(m, H, 0), SIGP / C) / np.maximum(w, 1e-6)
    near = gaussian_filter((full == k).astype(float), SIGB / C)
    reach = edt(~(full == k)) * C < 4 * SIGB + 2                        # only around the panel
    if not reach.any(): continue
    _, (pi, pj) = edt(~m, return_indices=True); zk = np.where(w > 0.05, zk, H[pi, pj])   # past its edge: its nearest own height
    upd = reach & (near > sm); sm[upd] = near[upd]; best[upd] = k; Z[upd] = zk[upd]
Z = np.where(foot & (best > 0), Z, H)
Z = gaussian_filter(Z, BEV / C)                                         # the steps as edges with a narrow bevel
jc = int(round(-x0 / C)); nm = min(jc, nx - jc - 1); Z[:, jc - nm:jc] = Z[:, jc + 1:jc + 1 + nm][:, ::-1]
T[KEY] = Z.astype(np.float32); T["cell"] = C; T["foot"] = foot
other = "bot" if KEY == "top" else "top"; T[other] = map_coordinates(T[other].astype(float), [gi, gj], order=1, mode="nearest").astype(np.float32)
if KEY == "bot": T["bot"] = np.minimum(T["bot"], T["top"] - 1)
else: T["top"] = np.maximum(T["top"], T["bot"] + 1)
np.savez(OUT, **T)
fig, ax = plt.subplots(1, 3, figsize=(24, 13)); ext = [x0, x0 + nx * C, y0, y0 + ny * C]
rng = np.random.default_rng(1); cols = rng.random((n + 1, 3)); cols[0] = 1
ax[0].imshow(np.where(foot[..., None], cols[best], 1), origin="lower", extent=ext); ax[0].set_title("%d componente (%d nervuri/bucati mici scoase)" % (len(ids), n - len(ids)))
for a, F, t in ((ax[1], H, "inainte"), (ax[2], Z, "dupa (componente reasamblate)")):
    ls = np.gradient(F, axis=1) - np.gradient(F, axis=0); a.imshow(np.where(foot, ls, np.nan), origin="lower", extent=ext, cmap="gray", vmin=-1.5, vmax=1.5); a.set_title(t)
for a in ax: a.set_aspect("equal")
fig.tight_layout(); fig.savefig(SHEET, dpi=70)
print("COMPONENTE %s: %d panouri pastrate, %d bucati scoase (sub %.0f m2 sau mai subtiri de %.1f m); panta treptei > %.1f; netezire panou %.1f m, margini %.1f m, tesitura %.1f m" % (
    KEY, len(ids), n - len(ids), AMIN, TMIN, STEEP, SIGP, SIGB, BEV))
