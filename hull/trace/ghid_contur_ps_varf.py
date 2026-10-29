# The PS's outline from the nose as ONE even curve (asked: seen from above it leaves the tip with a constant curve and then
# makes a sudden shoulder - it should carry on constant; side guides from the tip to section 05, on one continuous line):
# an ellipse arc x^2/A^2 + (y - yc)^2/B^2 = 1 through the tip (x 0 at the nose, so yc = y_tip - B) and the PS's outline at
# the two named sections (fitted, least squares on both), drawn left and right: in the top-view plane (z ZT, like
# contur_PS_sus) and on the PS's side at the height where the section is widest; the current outline's deviation printed.
# Usage: python ghid_contur_ps_varf.py <guides_ps.npz> <pieces.npz> <out.npz> <y_a> <y_b>
import sys, numpy as np, trimesh
from scipy.optimize import least_squares
G = np.load(sys.argv[1]); D = np.load(sys.argv[2]); OUT = sys.argv[3]; YA, YB = float(sys.argv[4]), float(sys.argv[5]); MX = -1700.0
C = G["contur_PS_sus"]; ZT = C[0, 2]; R = C[C[:, 0] >= 0]; R = R[np.argsort(-R[:, 1])]
xo = lambda y: np.interp(-y, -R[:, 1], R[:, 0]); ytip = R[:, 1].max()
pts = np.array([[xo(YA), YA], [xo(YB), YB]])
def res(q):
    A, B = q; yc = ytip - B; return pts[:, 0] ** 2 / A ** 2 + (pts[:, 1] - yc) ** 2 / B ** 2 - 1
A, B = least_squares(res, [130.0, 400.0], bounds=([50, 50], [400, 2000])).x; yc = ytip - B
ys = np.linspace(ytip, YB, 400); x = A * np.sqrt(np.clip(1 - (ys - yc) ** 2 / B ** 2, 0, None))
dev = x - xo(ys); i = np.argmax(np.abs(dev))
print("ELIPSA: A %.1f m (jumatate de latime maxima), B %.1f m, centru y %.1f; trece prin varf (y %.0f) si x %.1f la y %.0f, x %.1f la y %.0f" % (
    A, B, yc, ytip, A * np.sqrt(max(0, 1 - (YA - yc) ** 2 / B ** 2)), YA, A * np.sqrt(max(0, 1 - (YB - yc) ** 2 / B ** 2)), YB))
print("CONTURUL ACTUAL fata de elipsa: abatere max %.1f m la y %.0f (umarul), medie %.1f m" % (dev[i], ys[i], np.abs(dev).mean()))
ps = trimesh.Trimesh(D["PS__v"] - [MX, 0, 0], D["PS__f"], process=False); zw = []
for y in ys:                                          # height of the widest point of the section (side guide)
    s = ps.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: zw.append(np.nan); continue
    P = np.vstack(list(s.discrete)); zw.append(P[np.argmax(P[:, 0]), 2])
zw = np.array(zw); ok = np.isfinite(zw); zw = np.interp(np.arange(len(zw)), np.where(ok)[0], zw[ok])
from scipy.ndimage import gaussian_filter1d
zw = gaussian_filter1d(zw, 8, mode="nearest")
out = {"contur_varf_sus_D": np.c_[x, ys, np.full(len(ys), ZT)], "contur_varf_sus_S": np.c_[-x, ys, np.full(len(ys), ZT)],
       "contur_varf_lateral_D": np.c_[x, ys, zw], "contur_varf_lateral_S": np.c_[-x, ys, zw]}
np.savez(OUT, **out)
