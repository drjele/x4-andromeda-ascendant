# The original's faces read exactly, to keep its details crisp (asked: the details' edges brought to the standard - they
# looked like little stairs; the top done the same): on a CELL m grid, each cell centre gets the exact height of every
# original triangle above / below it (barycentric, not the lowest sample in the cell - that put the step edges on the grid);
# two layers -> top = highest, bottom = lowest; one layer -> by the confirmed guides' middle. Where the original has no face
# (its holes, the dips) the confirmed guides (ref_teren.py, filled and closed from above) take over, blended over BL m.
# Then a light smoothing (SIG m) that joins the step edges without flattening them, the right half mirrored. Same layout as
# ref_teren.py (top, bot, foot, outline ...), so the builders read it unchanged.
# Usage: python ref_fete_exacte.py <ref.npz> <confirmed teren.npz> <out.npz> <xc> [cell] [sig] [blend]
import sys, numpy as np
from scipy.ndimage import map_coordinates, gaussian_filter, distance_transform_edt as edt
Z = np.load(sys.argv[1]); G = np.load(sys.argv[2]); OUT, XC = sys.argv[3], float(sys.argv[4])
C = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5; SIG = float(sys.argv[6]) if len(sys.argv) > 6 else 0.75; BL = float(sys.argv[7]) if len(sys.argv) > 7 else 3.0
GAP = 4.0; v = Z["v"].astype(float).copy(); v[:, 0] -= XC; f = Z["f"]
gx0, gy0, GC = float(G["x0"]), float(G["y0"]), float(G["cell"]); gny, gnx = G["top"].shape
x0, y0 = gx0, gy0; nx, ny = int(gnx * GC / C), int(gny * GC / C)
zmax = np.full((ny, nx), -np.inf); zmin = np.full((ny, nx), np.inf)
for t in f:                                                             # exact heights at the cell centres under each triangle
    P = v[t]; lo = np.floor((P[:, :2].min(0) - [x0, y0]) / C - 0.5).astype(int); hi = np.ceil((P[:, :2].max(0) - [x0, y0]) / C - 0.5).astype(int)
    lo = np.maximum(lo, 0); hi = np.minimum(hi, [nx - 1, ny - 1])
    if (hi < lo).any(): continue
    jj, ii = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1)); px = x0 + (jj + 0.5) * C; py = y0 + (ii + 0.5) * C
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = P; d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(d) < 1e-9: continue
    l1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / d; l2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / d; l3 = 1 - l1 - l2
    k = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
    if not k.any(): continue
    z = l1 * az + l2 * bz + l3 * cz; ii, jj, z = ii[k], jj[k], z[k]
    np.maximum.at(zmax, (ii, jj), z); np.minimum.at(zmin, (ii, jj), z)
cov = np.isfinite(zmax); two = cov & (zmax - zmin > GAP); one = cov & ~two
yy, xx = np.mgrid[0:ny, 0:nx]; gi, gj = (yy + 0.5) * C / GC - 0.5, (xx + 0.5) * C / GC - 0.5
up = lambda F: map_coordinates(F.astype(float), [gi, gj], order=1, mode="nearest")
top0, bot0 = up(G["top"]), up(G["bot"]); foot = up(G["foot"].astype(float)) > 0.5; mid = (top0 + bot0) / 2
hasT = two | (one & (zmax >= mid)); hasB = two | (one & (zmin < mid))
hasT &= np.abs(np.where(hasT, zmax, top0) - top0) < 12               # a face far off the confirmed one (inner parts) is not the skin
hasB &= np.abs(np.where(hasB, zmin, bot0) - bot0) < 12
def merge(E, has, F0):                                                  # exact where the original has the face, the guide elsewhere
    w = np.clip(edt(has) * C / BL, 0, 1); return np.where(has, E, F0) * w + F0 * (1 - w)
top = merge(zmax, hasT, top0); bot = merge(zmin, hasB, bot0)
def sm(F):
    wf = gaussian_filter(foot.astype(float), SIG / C); return np.where(foot, gaussian_filter(np.where(foot, F, 0), SIG / C) / np.maximum(wf, 1e-6), F)
top, bot = sm(top), sm(bot)
jc = int(round(-x0 / C))                                                # the right half mirrored
for F in (top, bot):
    F[:, :jc] = F[:, jc + 1:2 * jc + 1][:, ::-1][:, :jc] if F.shape[1] > 2 * jc else F[:, :jc]
bot = np.minimum(bot, top - 1)
np.savez(OUT, top=top.astype(np.float32), bot=bot.astype(np.float32), foot=foot, x0=x0, y0=y0, cell=C, xc=XC, outline=G["outline"])
print("FETE EXACTE: celula %.1f m (%d x %d); fata de sus exacta pe %.0f%% din amprenta, jos pe %.0f%%; netezire %.2f m, trecere spre ghidaj %.0f m" % (
    C, nx, ny, 100 * (hasT & foot).sum() / foot.sum(), 100 * (hasB & foot).sum() / foot.sum(), SIG, BL))
