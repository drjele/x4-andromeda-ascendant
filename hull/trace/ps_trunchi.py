# PS as a frustum slab (asked: a flat top, no hole - like the belly V but the big face below and the small one on top, the
# small one the same outline 20 % smaller): the outline seen from above = inside the confirmed outer silhouette, outside the
# inner one (the U between the arms), from the tip back to YR; the bottom face that outline at ZB, the top face the outline
# scaled by TOP (about its centre of area) at ZT, the sides straight between them, every edge rounded (RK m). Built as a
# field: the outline's signed distance (raster 1 m) taken at each height on the outline scaled for that height, closed by the
# two planes (smooth max), surface at 0 (marching cubes). Writes verts / faces (ship coordinates, centred).
# PS_ANCORA_SPATE=1: the top scaled about the back's middle (y YR), the U's walls leaning out PS_U_CRESTE m at the top.
# Usage: python ps_trunchi.py <ghid_drept3.npz> <out.npz> [zb] [zt] [top] [yr]
import sys, numpy as np, cv2
from scipy.ndimage import distance_transform_edt as edt, map_coordinates, gaussian_filter
from skimage.measure import marching_cubes
G = np.load(sys.argv[1]); OUT = sys.argv[2]; ZB = float(sys.argv[3]) if len(sys.argv) > 3 else 256.0; ZT = float(sys.argv[4]) if len(sys.argv) > 4 else 316.0
TOP = float(sys.argv[5]) if len(sys.argv) > 5 else 0.8; YR = float(sys.argv[6]) if len(sys.argv) > 6 else -90.0; RK, C = 5.0, 1.0
X0, Y0 = -220.0, YR - 30; NX, NY = int(440 / C), int((520 - Y0) / C)
def poly(Q): return (((Q - [X0, Y0]) / C)).astype(np.int32)
Bo = G["B"]; Bi = G["B_int"]; m = np.zeros((NY, NX), np.uint8)
ob = Bo[Bo[:, 1] >= YR - 5]; cv2.fillPoly(m, [poly(np.vstack([ob, [[ob[-1, 0], YR], [ob[0, 0], YR]]]))], 1)   # inside the outer line
ib = Bi[Bi[:, 1] >= YR - 40]; gap = np.zeros_like(m); cv2.fillPoly(gap, [poly(np.vstack([ib, [[ib[-1, 0], YR - 40], [ib[0, 0], YR - 40]]]))], 1)
import os
ANC = os.environ.get("PS_ANCORA_SPATE"); GU = float(os.environ.get("PS_U_CRESTE", "10"))
if ANC:                                                                 # scaled about the back's middle (the legs keep their height to the
    mo = m.copy(); mo[:int((YR - Y0) / C)] = 0                          # arms); the U's walls lean out by GU m at the top instead
    so = ((edt(mo == 0) - edt(mo == 1)) * C).astype(np.float32); sh = ((edt(gap == 0) - edt(gap == 1)) * C).astype(np.float32)
m[gap > 0] = 0; m[:int((YR - Y0) / C)] = 0                              # minus the U, cut at YR
sd = ((edt(m == 0) - edt(m == 1)) * C).astype(np.float32) if not ANC else so   # < 0 inside (rows y, columns x)
ii, jj = np.nonzero(m); cy, cx = (ii.mean() * C + Y0) if not ANC else YR, 0.0   # centre of area (on the middle line) / the back
area = m.sum() * C * C
xs = np.arange(X0 + C / 2, X0 + NX * C, C); ys = np.arange(Y0 + C / 2, Y0 + NY * C, C); zs = np.arange(ZB - 12, ZT + 12, C)
Xg, Yg = np.meshgrid(xs, ys, indexing="xy")
F = np.empty((len(zs), NY, NX), np.float32); sm = lambda a, b, k: (a + b + np.sqrt((a - b) ** 2 + k ** 2)) / 2
for k, z in enumerate(zs):
    t = np.clip((z - ZB) / (ZT - ZB), 0, 1); s = 1 - (1 - TOP) * t     # the outline's scale at this height
    px, py = cx + (Xg - cx) / s, cy + (Yg - cy) / s
    d2 = map_coordinates(sd, [(py - Y0) / C - 0.5, (px - X0) / C - 0.5], order=1, mode="nearest") * s
    if ANC: d2 = np.maximum(d2, GU * t - sh)
    F[k] = sm(sm(d2, ZB - z, RK), z - ZT, RK)
F = gaussian_filter(F, 0.6)
v, f, _, _ = marching_cubes(F, 0.0, spacing=(C, C, C)); v = v[:, [2, 1, 0]] + [X0 + C / 2, Y0 + C / 2, ZB - 12]
f = f[:, ::-1]
np.savez(OUT, v=v.astype(np.float32), f=f.astype(np.int32))
print("PS TRUNCHI: jos z %.0f (contur %.0f m2), sus z %.0f (contur x%.2f), spate la y %.0f; %d varfuri, %d fete; x %.0f..%.0f y %.0f..%.0f" % (
    ZB, area, ZT, TOP, YR, len(v), len(f), v[:, 0].min(), v[:, 0].max(), v[:, 1].min(), v[:, 1].max()))
