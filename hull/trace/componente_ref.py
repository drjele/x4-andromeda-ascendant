# One face of the original rebuilt from its own components (asked: break it into components, put each in order on its own,
# then assemble them into one - the stray ribs out, the details kept): the original's faces of that side (top / bottom, by
# the confirmed guides' middle) welded and split into panels at its sharp edges (neighbouring faces more than ANG degrees
# apart); near-vertical panels (step walls) and panels thinner than TMIN m or smaller than AMIN m2 (the stray ribs) left out;
# every kept panel rasterised exactly (CELL m), smoothed on its own (SIGP m) with its plan outline smoothed (SIGB m); the face
# = on each cell the lowest (bottom) / highest (top) panel there, cells no panel covers from the confirmed guide; the steps
# kept as edges with a narrow bevel (BEV m); the right half mirrored. Writes the terrain with that face replaced + a sheet.
# CURATA_R=m: ribs / dents narrower than 2 m x that removed; the cleaner half (left or right) is the one mirrored.
# SUS_GHIDAJ_SUB=y0,y1: behind y0 the face is the confirmed smooth guide, blended into the components up to y1.
# Usage: python componente_ref.py <ref.npz> <teren.npz> <top|bot> <out.npz> <sheet.png> <xc> [cell ang tmin amin sigp sigb bev]
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.ndimage import map_coordinates, gaussian_filter, distance_transform_edt as edt
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
Z = np.load(sys.argv[1]); T = dict(np.load(sys.argv[2])); KEY, OUT, SHEET, XC = sys.argv[3], sys.argv[4], sys.argv[5], float(sys.argv[6])
P = [float(t) for t in sys.argv[7:]] + [None] * 7
C = P[0] or 0.5; ANG = P[1] or 25.0; TMIN = P[2] or 2.5; AMIN = P[3] or 100.0; SIGP = P[4] or 2.0; SIGB = P[5] or 1.2; BEV = P[6] or 0.4
v = Z["v"].astype(float).copy(); v[:, 0] -= XC; f = Z["f"]
key = np.round(v / 0.01).astype(np.int64); _, wid, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); f = inv.ravel()[f]; v = v[wid]   # welded
x0, y0, GC = float(T["x0"]), float(T["y0"]), float(T["cell"]); gny, gnx = T[KEY].shape; nx, ny = int(gnx * GC / C), int(gny * GC / C)
yy, xx = np.mgrid[0:ny, 0:nx]; gi, gj = (yy + 0.5) * C / GC - 0.5, (xx + 0.5) * C / GC - 0.5
up = lambda F: map_coordinates(F.astype(float), [gi, gj], order=1, mode="nearest")
top0, bot0 = up(T["top"]), up(T["bot"]); foot = up(T["foot"].astype(float)) > 0.5
_, (oi, oj) = edt(~foot, return_indices=True); top0, bot0 = top0[oi, oj], bot0[oi, oj]   # outside the footprint: the nearest value
mid = (top0 + bot0) / 2                                                 # inside (no stray zeros pulled in by the smoothing)
cc = v[f].mean(1); ci = np.clip(((cc[:, 1] - y0) / C).astype(int), 0, ny - 1); cj = np.clip(((cc[:, 0] - x0) / C).astype(int), 0, nx - 1)
side = cc[:, 2] >= mid[ci, cj] if KEY == "top" else cc[:, 2] < mid[ci, cj]
fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); fa = np.linalg.norm(fn, axis=1) / 2; fn /= np.maximum(2 * fa, 1e-12)[:, None]
E = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1); fid = np.tile(np.arange(len(f)), 3)
o = np.lexsort((E[:, 1], E[:, 0])); E, fid = E[o], fid[o]; same = np.all(E[1:] == E[:-1], axis=1)
a, b = fid[:-1][same], fid[1:][same]; ok = side[a] & side[b] & (np.abs(np.sum(fn[a] * fn[b], 1)) > np.cos(np.radians(ANG)))
nc, comp = connected_components(coo_matrix((np.ones(ok.sum()), (a[ok], b[ok])), shape=(len(f), len(f))), directed=False)
comp = np.where(side, comp, -1)
def raster(fs):                                                         # exact heights of these faces at the cell centres
    zr = np.full((ny, nx), np.nan)
    for t in f[fs]:
        Pt = v[t]; lo = np.maximum(np.floor((Pt[:, :2].min(0) - [x0, y0]) / C - 0.5).astype(int), 0); hi = np.minimum(np.ceil((Pt[:, :2].max(0) - [x0, y0]) / C - 0.5).astype(int), [nx - 1, ny - 1])
        if (hi < lo).any(): continue
        jj, ii = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1)); px = x0 + (jj + 0.5) * C; py = y0 + (ii + 0.5) * C
        (ax_, ay_, az), (bx, by, bz), (cx, cy, cz) = Pt; d = (by - cy) * (ax_ - cx) + (cx - bx) * (ay_ - cy)
        if abs(d) < 1e-9: continue
        l1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / d; l2 = ((cy - ay_) * (px - cx) + (ax_ - cx) * (py - cy)) / d; l3 = 1 - l1 - l2
        k = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6); z = (l1 * az + l2 * bz + l3 * cz)[k]; ii, jj = ii[k], jj[k]
        cur = zr[ii, jj]; zr[ii, jj] = np.where(np.isnan(cur), z, np.minimum(cur, z) if KEY == "bot" else np.maximum(cur, z))
    return zr
best = np.full((ny, nx), np.nan); lab = np.zeros((ny, nx), int); kept = 0; dropped = 0
for k in np.unique(comp[comp >= 0]):
    fs = np.nonzero(comp == k)[0]; A = fa[fs].sum(); nz = np.abs(np.sum(fn[fs, 2] * fa[fs]) / max(A, 1e-9))
    if nz < 0.35 or A < AMIN: dropped += 1; continue                    # step walls / small bits
    zr = raster(fs); m = np.isfinite(zr)
    if not m.any() or (edt(m) * C >= TMIN / 2).sum() < 0.5 * m.sum(): dropped += 1; continue   # ribs: mostly thinner than TMIN
    w = gaussian_filter(m.astype(float), SIGP / C); zs = gaussian_filter(np.where(m, zr, 0), SIGP / C) / np.maximum(w, 1e-6)
    import cv2                                                          # its outline polished: straight runs (approxPolyDP 1.5 m),
    cs, hi_ = cv2.findContours(m.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)   # corners rounded (SIGB), then let a
    pm = np.zeros((ny, nx), np.uint8)                                   # little past its edge (1.5 m) so neighbours meet where
    order = sorted(range(len(cs)), key=lambda i: hi_[0][i][3] != -1)   # their surfaces cross (a clean line), not in a filled gap;
    for i in order:                                                     # outer outlines fill, the holes' outlines (the V slot) empty
        if cv2.contourArea(cs[i]) * C * C < 20: continue
        cv2.fillPoly(pm, [cv2.approxPolyDP(cs[i], 1.5 / C, True)], 0 if hi_[0][i][3] != -1 else 1)
    ms = gaussian_filter(pm.astype(float), SIGB / C) > 0.5
    ms = edt(~ms) * C <= 1.5
    _, (pi, pj) = edt(~m, return_indices=True); zs = np.where(w > 0.05, zs, zr[pi, pj])
    if KEY == "bot": better = ms & (np.isnan(best) | (zs < best))
    else: better = ms & (np.isnan(best) | (zs > best))
    best[better] = zs[better]; lab[better] = k + 1; kept += 1
G0 = bot0 if KEY == "bot" else top0; cov = np.isfinite(best) & foot
if KEY == "bot":                                                        # gaps between panels (the V slot) filled smoothly from the
    from scipy.interpolate import griddata                              # panels around them, not from the guide (no edge left)
    ci_, cj_ = np.nonzero(cov); s_ = slice(None, None, 3)
    F0 = griddata((ci_[s_], cj_[s_]), best[ci_[s_], cj_[s_]], (yy, xx), method="linear"); F0 = np.where(np.isfinite(F0), F0, G0)
    F0 = np.where(cov, best, gaussian_filter(F0[oi, oj], 4.0 / C))
else: F0 = G0                                                           # top: its holes keep the confirmed (closed) guide
de = edt(foot) * C; edge = np.clip((de - 3.0) / 4.0, 0, 1); edge = edge * edge * (3 - 2 * edge)   # gradual towards the outline
wv = np.clip(edt(cov) * C / 3.0, 0, 1) * edge
Zf = np.where(cov, best, F0) * wv + F0 * (1 - wv)                       # uncovered cells: the confirmed guide, blended over 3 m
import os
from scipy.ndimage import grey_opening, grey_closing
CR = float(os.environ.get("CURATA_R", "0"))                            # ribs / dents narrower than 2 CR m taken out (open + close)
if CR:
    r = int(round(CR / C)); dy, dx = np.mgrid[-r:r + 1, -r:r + 1]; D = dy ** 2 + dx ** 2 <= r * r
    Zc = grey_opening(grey_closing(Zf[oi, oj], footprint=D), footprint=D); Zf = np.where(edt(foot) * C > 3, Zc, Zf)
YS = os.environ.get("SUS_GHIDAJ_SUB")                                  # behind y0..y1 the face follows the confirmed smooth guide
if YS:                                                                  # (where the original has only fragments: no stray ribs)
    ya, yb = [float(t) for t in YS.split(",")]; yc_ = y0 + (yy + 0.5) * C; t_ = np.clip((yc_ - ya) / (yb - ya), 0, 1); t_ = t_ * t_ * (3 - 2 * t_)
    Zf = Zf * t_ + G0 * (1 - t_)
Zf = gaussian_filter(Zf[oi, oj], BEV / C)
jc = int(round(-x0 / C)); nm = min(jc, nx - jc - 1)                    # symmetry: the cleaner half (fewer narrow ribs / dents) mirrored
r2 = int(round(2.0 / C)); dy, dx = np.mgrid[-r2:r2 + 1, -r2:r2 + 1]; D2 = dy ** 2 + dx ** 2 <= r2 * r2
bad = np.abs(grey_opening(grey_closing(Zf, footprint=D2), footprint=D2) - Zf) * (foot & (edt(foot) * C > 3))
bl, br = bad[:, jc - nm:jc].sum(), bad[:, jc + 1:jc + 1 + nm].sum()
if bl < br: Zf[:, jc + 1:jc + 1 + nm] = Zf[:, jc - nm:jc][:, ::-1]; HALF = "stanga"
else: Zf[:, jc - nm:jc] = Zf[:, jc + 1:jc + 1 + nm][:, ::-1]; HALF = "dreapta"
other = "bot" if KEY == "top" else "top"; T[KEY] = Zf.astype(np.float32); T[other] = up(T[other]).astype(np.float32); T["cell"] = C; T["foot"] = foot
if KEY == "bot": T["bot"] = np.minimum(T["bot"], T["top"] - 1)
else: T["top"] = np.maximum(T["top"], T["bot"] + 1)
np.savez(OUT, **T)
fig, ax = plt.subplots(1, 2, figsize=(17, 13)); ext = [x0, x0 + nx * C, y0, y0 + ny * C]
cols = np.random.default_rng(3).random((lab.max() + 1, 3)) * 0.8 + 0.2; cols[0] = 1
ax[0].imshow(np.where(foot[..., None], cols[lab], 1), origin="lower", extent=ext); ax[0].set_title("%s: %d componente pastrate, %d scoase (pereti de treapta, nervuri, bucati mici)" % (KEY, kept, dropped), fontsize=10)
ls = np.gradient(Zf, axis=1) - np.gradient(Zf, axis=0); ax[1].imshow(np.where(foot, ls, np.nan), origin="lower", extent=ext, cmap="gray", vmin=-1.2, vmax=1.2); ax[1].set_title("reasamblat (umbrire)")
for a_ in ax: a_.set_aspect("equal")
fig.tight_layout(); fig.savefig(SHEET, dpi=70)
print("COMPONENTE %s: %d pastrate, %d scoase; acoperit de componente %.0f%% din amprenta; contur panouri %.1f m, curatare %.1f m; jumatatea %s oglindita (defecte stanga %.0f / dreapta %.0f)" % (
    KEY, kept, dropped, 100 * cov.sum() / foot.sum(), SIGB, CR, HALF, bl, br))
