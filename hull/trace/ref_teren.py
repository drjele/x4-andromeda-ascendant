# The reference piece read as terrain (asked: copy the original faithfully, holes covered, to the standards discussed): its
# triangles sampled onto a CELL m grid seen from above; where a cell has two layers (> GAP m apart) the highest is the top,
# the lowest the bottom; a single layer goes to the top or the bottom by the local middle of the two-layer cells around it.
# The footprint = every covered cell, closed, inner holes filled (the open U at the back stays open). The holes in each face
# filled from around (linear, then nearest), the small steps and ribs smoothed (gaussian SIG m), the right half (x >= 0)
# mirrored. Guides: cross sections (top and bottom lines) at the given y, long profiles at the given x, the plan outline.
# Sheet: the reference's exact cuts (grey) under the guides (red top / blue bottom). Writes the fields and the guides.
# SUS_INCHIDERE=m: the top's valleys narrower than that filled from above; SIG_JOS=m: the bottom's own smoothing.
# FOAIE_GROS=m: a band read as a sheet (one layer -> bottom m under the top); FARA_OGLINDA=1: no mirroring, closed outline.
# Usage: python ref_teren.py <ref.npz (v,f)> <out.npz> <sheet.png> <xc> <y,y,..> <x,x,..> [cell] [sig] [title] [outline_sig]
import sys, numpy as np, trimesh, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.ndimage import binary_closing, binary_fill_holes, gaussian_filter, distance_transform_edt as edt
from scipy.interpolate import griddata
Z = np.load(sys.argv[1]); OUT, SHEET, XC = sys.argv[2], sys.argv[3], float(sys.argv[4])
YS = [float(t) for t in sys.argv[5].split(",")]; XS = [float(t) for t in sys.argv[6].split(",")]
CELL = float(sys.argv[7]) if len(sys.argv) > 7 else 2.0; SIG = float(sys.argv[8]) if len(sys.argv) > 8 else 6.0; TT = sys.argv[9] if len(sys.argv) > 9 else ""
GAP = 4.0; v = Z["v"].astype(float).copy(); v[:, 0] -= XC; f = Z["f"]
x0, y0 = -np.abs(v[:, 0]).max() - 10, v[:, 1].min() - 10; nx = int(2 * -x0 / CELL) + 1; ny = int((v[:, 1].max() + 10 - y0) / CELL) + 1
pts = []
for t in f:                                                             # dense samples on every triangle (about CELL/2 apart)
    a, b, c = v[t]; n = int(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / (CELL / 2)) + 2
    i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1)); k = (i + j) <= n; u, w = i[k] / n, j[k] / n
    pts.append(a + np.outer(u, b - a) + np.outer(w, c - a))
P = np.vstack(pts); ci = ((P[:, 1] - y0) / CELL).astype(int); cj = ((P[:, 0] - x0) / CELL).astype(int); idx = ci * nx + cj
zmax = np.full(nx * ny, -np.inf); zmin = np.full(nx * ny, np.inf); np.maximum.at(zmax, idx, P[:, 2]); np.minimum.at(zmin, idx, P[:, 2])
zmax, zmin = zmax.reshape(ny, nx), zmin.reshape(ny, nx); cov = np.isfinite(zmax)
two = cov & (zmax - zmin > GAP); one = cov & ~two
mid = np.where(two, (zmax + zmin) / 2, np.nan); yy, xx = np.nonzero(two)
midf = griddata((yy, xx), mid[two], np.indices((ny, nx)).transpose(1, 2, 0).reshape(-1, 2), method="nearest").reshape(ny, nx)
midf = gaussian_filter(midf, 10)
top = np.where(two | (one & (zmax >= midf)), zmax, np.nan); bot = np.where(two | (one & (zmin < midf)), zmin, np.nan)
import os
FG = float(os.environ.get("FOAIE_GROS", "0"))                          # a sheet piece (a band): where it is one layer, its top is that
if FG: top = np.where(cov, zmax, np.nan); bot = np.where(two, zmin, np.where(one, zmax - FG, np.nan))   # layer, its bottom FG m under
FU = float(os.environ.get("FOAIE_UMPLE", "0"))                         # near the two-layer part (the C folded round the side) the bottom
if FG and FU: bot[one & (edt(~two) * CELL < FU)] = np.nan              # is filled from that part's lower lip (a full side, no trench)
foot = binary_fill_holes(binary_closing(cov, np.ones((5, 5))))       # the footprint (inner holes filled, the U open to the back)
def fill(F, SIG=SIG, CLOSE=0.0):                                        # holes filled from around, then smoothed, inside the footprint
    ok = np.isfinite(F) & foot; yy, xx = np.nonzero(ok); g = np.indices((ny, nx)).transpose(1, 2, 0).reshape(-1, 2)
    L = griddata((yy, xx), F[ok], g, method="linear").reshape(ny, nx); N = griddata((yy, xx), F[ok], g, method="nearest").reshape(ny, nx)
    L = np.where(np.isfinite(L), L, N); w = gaussian_filter(foot.astype(float), SIG / CELL)
    if CLOSE:                                                           # valleys narrower than CLOSE m filled from above (a ball rolled
        from scipy.ndimage import grey_closing                          # over the face): the dips left where the original has no face
        r = int(CLOSE / 2 / CELL); yy_, xx_ = np.mgrid[-r:r + 1, -r:r + 1]; L = grey_closing(L, footprint=(yy_ ** 2 + xx_ ** 2) <= r * r)
    return gaussian_filter(np.where(foot, L, 0), SIG / CELL) / np.maximum(w, 1e-6)
import os
topf = fill(top, SIG, float(os.environ.get("SUS_INCHIDERE", "0"))); botf = fill(bot, float(os.environ.get("SIG_JOS", SIG)))   # the
                                                                        # bottom can keep its detail (less smoothing)
jc = int(-x0 / CELL)                                                    # the right half mirrored (x >= 0 -> x < 0) - not for a piece
FO = bool(os.environ.get("FARA_OGLINDA"))                               # on one side only (its pair on the other side is mirrored later)
for F in ((topf, botf, foot) if not FO else ()):
    F[:, :jc] = F[:, 2 * jc:jc:-1][:, :jc] if F[:, 2 * jc:jc:-1].shape[1] >= jc else F[:, :jc]
botf = np.minimum(botf, topf)
xs = x0 + (np.arange(nx) + 0.5) * CELL; ys = y0 + (np.arange(ny) + 0.5) * CELL
cs, _ = cv2.findContours(foot.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); oc = max(cs, key=cv2.contourArea)[:, 0]
outline = np.stack([x0 + (oc[:, 0] + 0.5) * CELL, y0 + (oc[:, 1] + 0.5) * CELL], 1)
from scipy.ndimage import gaussian_filter1d, map_coordinates
def smooth_outline(ol, sig):                                            # the outline to the standard: the right half only (x >= 0, from
    k0 = np.argmax(ol[:, 1] - 50 * np.abs(ol[:, 0]))                    # the tip round to the middle again), resampled every 1 m,
    ol = np.roll(ol, -k0, 0)                                            # smoothed with its mirror carried past both ends (no kink on
    if ol[min(5, len(ol) - 1), 0] < ol[0, 0]: ol = np.r_[ol[:1], ol[1:][::-1]]   # the axis), the ends put on x = 0; then mirrored
    kend = np.nonzero(ol[1:, 0] < 0)[0]; h = ol[:kend[0] + 1] if len(kend) else ol
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(h, axis=0), axis=1))]; u = np.arange(0, d[-1], 1.0)
    h = np.stack([np.interp(u, d, h[:, 0]), np.interp(u, d, h[:, 1])], 1); n = len(h)
    m = lambda q: q * [-1, 1]; pad = int(4 * sig)
    e = np.vstack([m(h[1:pad + 1][::-1]), h, m(h[-pad - 1:-1][::-1])])
    e = np.stack([gaussian_filter1d(e[:, 0], sig, mode="nearest"), gaussian_filter1d(e[:, 1], sig, mode="nearest")], 1)[pad:pad + n]
    e[0, 0] = e[-1, 0] = 0.0; e[:, 0] = np.maximum(e[:, 0], 0)
    return np.vstack([e, m(e[-2:0:-1])])
OS = float(sys.argv[10]) if len(sys.argv) > 10 else 5.0
def smooth_closed(ol, sig):                                             # a one-sided piece: the whole closed outline, resampled every
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([ol, ol[:1]]), axis=0), axis=1))]   # 1 m, smoothed all round (wrapping)
    u = np.arange(0, d[-1], 1.0); q = np.vstack([ol, ol[:1]])
    h = np.stack([np.interp(u, d, q[:, 0]), np.interp(u, d, q[:, 1])], 1)
    return np.stack([gaussian_filter1d(h[:, 0], sig, mode="wrap"), gaussian_filter1d(h[:, 1], sig, mode="wrap")], 1)
outline_raw = outline; outline = smooth_outline(outline_raw, OS) if not FO else smooth_closed(outline_raw, OS)
oz = map_coordinates(np.where(foot, topf, np.nanmean(topf[foot])), [(outline[:, 1] - y0) / CELL - 0.5, (outline[:, 0] - x0) / CELL - 0.5], order=1, mode="nearest")
oz = gaussian_filter1d(np.r_[oz[-30:], oz, oz[:30]], OS)[30:-30]; outline = np.c_[outline, oz]   # its height on the top, smoothed alike
import os
if os.environ.get("CONTUR_Z"): outline[:, 2] = float(os.environ["CONTUR_Z"])   # a flat outline guide (one plane, as agreed for outlines)
G = {}; tm = trimesh.Trimesh(v, f, process=False)
fig, ax = plt.subplots(len(YS) + 2, 1, figsize=(14, 3.0 * (len(YS) + 2)))
for a, y in zip(ax, YS):
    r = int((y - y0) / CELL); m = foot[r]
    for q in trimesh.intersections.mesh_plane(tm, [0, 1, 0], [0, y, 0]): a.plot(q[:, 0], q[:, 2], "-", color="0.6", lw=1)
    a.plot(xs[m], topf[r, m], "r-", lw=1.4); a.plot(xs[m], botf[r, m], "b-", lw=1.4)
    G["sec_%d" % y] = np.stack([xs[m], np.full(m.sum(), y), topf[r, m], botf[r, m]], 1)
    a.set_title("y = %.0f: referinta (gri), ghidaj sus (rosu) / jos (albastru)" % y, fontsize=9); a.set_aspect("equal"); a.grid(alpha=.3)
a = ax[-2]
for x, c in zip(XS, ["k", "b", "g", "m", "c"]):
    k = int((x - x0) / CELL); m = foot[:, k]
    for q in trimesh.intersections.mesh_plane(tm, [1, 0, 0], [x, 0, 0]): a.plot(q[:, 1], q[:, 2], "-", color="0.7", lw=.8)
    a.plot(ys[m], topf[m, k], "-", color=c, lw=1.3, label="x = %.0f" % x); a.plot(ys[m], botf[m, k], "--", color=c, lw=1.3)
    G["prof_%d" % x] = np.stack([np.full(m.sum(), x), ys[m], topf[m, k], botf[m, k]], 1)
a.legend(fontsize=8); a.set_title("profile lungi: sus (plin) / jos (punctat), referinta gri", fontsize=9); a.set_aspect("equal"); a.grid(alpha=.3)
a = ax[-1]; a.imshow(np.where(foot, topf - botf, np.nan), origin="lower", extent=[xs[0], xs[-1], ys[0], ys[-1]], cmap="viridis"); a.plot(outline_raw[:, 0], outline_raw[:, 1], "-", color="0.5", lw=.6); a.plot(outline[:, 0], outline[:, 1], "r-", lw=1)
a.set_title("grosime (sus - jos), contur in plan (rosu)", fontsize=9); a.set_aspect("equal")
fig.suptitle(TT); fig.tight_layout(); fig.savefig(SHEET, dpi=100)
np.savez(OUT, top=topf, bot=botf, foot=foot, x0=x0, y0=y0, cell=CELL, xc=XC, outline=outline, outline_raw=outline_raw, **G)
print("TEREN %s: celule %d x %d, acoperite %d (doua straturi %d, un strat %d), amprenta %d; grosime %.0f..%.0f m; contur %d puncte" % (
    TT, nx, ny, cov.sum(), two.sum(), one.sum(), foot.sum(), np.nanmin(np.where(foot, topf - botf, np.nan)), np.nanmax(np.where(foot, topf - botf, np.nan)), len(outline)))
