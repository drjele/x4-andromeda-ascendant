# The 055 pieces rebuilt as a slightly domed pad growing out of PS (asked: a tiny bit domed, joined cleanly with PS): the
# footprint = the old piece seen from above (its triangles filled, closed, smoothed); the top = PS's surface there (linear over
# PS's upward-facing vertices, 1 m grid) + a dome HD m high, reached DM m in from the edge (quadratic), starting 0.5 m under PS's surface at the edge so
# it comes out of PS at a shallow angle (a clean meeting line, no step); the bottom 4 m under PS. A field, surface at 0
# (marching cubes). Writes the right piece (x < 0 = S as given), verts / faces, ship coordinates centred.
# P055_COLTURI=n: the outline as n straight sides (the footprint's hull simplified), corners rounded P055_RAZA m.
# Usage: python bombat_055.py <old_055.npz (v,f)> <ps.npz> <out.npz> [hd] [dm]
import sys, numpy as np, cv2
from scipy.ndimage import distance_transform_edt as edt, gaussian_filter, binary_closing, map_coordinates
from skimage.measure import marching_cubes
O = np.load(sys.argv[1]); PS = np.load(sys.argv[2]); OUT = sys.argv[3]
HD = float(sys.argv[4]) if len(sys.argv) > 4 else 4.0; DM = float(sys.argv[5]) if len(sys.argv) > 5 else 14.0; C = 0.5
v = O["v"]; f = O["f"]; x0, y0 = v[:, 0].min() - 15, v[:, 1].min() - 15; nx, ny = int((np.ptp(v[:, 0]) + 30) / C), int((np.ptp(v[:, 1]) + 30) / C)
m = np.zeros((ny, nx), np.uint8)
for t in f: cv2.fillPoly(m, [((v[t][:, :2] - [x0, y0]) / C).astype(np.int32)], 1)
m = binary_closing(m, np.ones((9, 9))).astype(np.uint8)
import os
NC = int(os.environ.get("P055_COLTURI", "0")); RC = float(os.environ.get("P055_RAZA", "6"))
if NC:                                                                  # a clean outline: the footprint's hull as NC straight sides,
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); h = cv2.convexHull(max(cs, key=cv2.contourArea))
    ep = 1.0
    while True:
        q = cv2.approxPolyDP(h, ep, True)
        if len(q) <= NC: break
        ep *= 1.15
    m = np.zeros_like(m); cv2.fillPoly(m, [q], 1)                       # its corners rounded (radius RC: in, then out)
    r = int(RC / C); k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    m = cv2.dilate(cv2.erode(m, k), k); print("055 contur: %d laturi drepte, colturi rotunjite %.0f m" % (len(q), RC))
sd = gaussian_filter(((edt(m == 0) - edt(m == 1)) * C).astype(np.float32), 4.0 if not NC else 1.0)   # footprint distance, smoothed (< 0 inside)
xs = x0 + (np.arange(nx) + 0.5) * C; ys = y0 + (np.arange(ny) + 0.5) * C; X, Y = np.meshgrid(xs, ys, indexing="xy")
G = 1.0; pv, pf = PS["v"], PS["f"]                                    # PS's top surface on a 1 m grid: linear over the vertices of its
fn = np.cross(pv[pf[:, 1]] - pv[pf[:, 0]], pv[pf[:, 2]] - pv[pf[:, 0]]); fn /= np.linalg.norm(fn, axis=1)[:, None] + 1e-12
up = np.unique(pf[fn[:, 2] > 0.15].ravel()); up = up[(np.abs(pv[up, 0] - xs.mean()) < 150) & (np.abs(pv[up, 1] - ys.mean()) < 150)]
gx, gy = np.arange(xs[0], xs[-1] + G, G), np.arange(ys[0], ys[-1] + G, G); GX, GY = np.meshgrid(gx, gy, indexing="xy")
from scipy.interpolate import griddata                                  # upward faces (the top and the sloped sides), not the bottom
zg = griddata(pv[up, :2], pv[up, 2], (GX, GY), method="linear")
if np.isnan(zg).any():                                                  # beyond PS's edge: the nearest known height
    from scipy.ndimage import distance_transform_edt as e2; idx = e2(np.isnan(zg), return_distances=False, return_indices=True); zg = zg[tuple(idx)]
zs = map_coordinates(gaussian_filter(zg, 1.0), [(Y - gy[0]) / G, (X - gx[0]) / G], order=1, mode="nearest")
c = np.clip(-sd / DM, 0, 1); prof = 1 - (1 - c) ** 2; top = zs - 0.5 + (HD + 0.5) * prof; bot = zs - 4
zz = np.arange(bot.min() - 2, top.max() + 2, C); F = np.empty((len(zz), ny, nx), np.float32)
sm = lambda a, b, k: (a + b + np.sqrt((a - b) ** 2 + k ** 2)) / 2
for k, z in enumerate(zz): F[k] = sm(sm(sd, z - top, 0.6), bot - z, 0.6)
vv, ff, _, _ = marching_cubes(F, 0.0, spacing=(C, C, C)); vv = vv[:, [2, 1, 0]] + [xs[0], ys[0], zz[0]]; ff = ff[:, ::-1]
np.savez(OUT, v=vv.astype(np.float32), f=ff.astype(np.int32))
print("055 BOMBAT: amprenta x %.0f..%.0f y %.0f..%.0f (%.0f m2), dom %.1f m (la %.0f m de margine), iese din PS sub unghi mic; %d fete" % (
    X[sd < 0].min(), X[sd < 0].max(), Y[sd < 0].min(), Y[sd < 0].max(), (sd < 0).sum() * C * C, HD, DM, len(ff)))
