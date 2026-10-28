# The 086 hood raised with a cavity under it (asked: the hood a little higher, with a dividing wall down the middle of the
# cavity that forms): the hood's confirmed top raised LIFT m; its sides and back come down into the piece under it (seated
# EMB m), WALL m thick; the roof ROOF m thick; under it the cavity, floor = the piece's top face, open at the front; a wall
# MID m thick down its middle (x = 0) from the front to the back wall. Built as a field on a CELL m grid, surface at 0.
# CAPAC_PANTA_LAT / CAPAC_PANTA_SPATE = m in per m up: walls at atan(k) from vertical (1.43 = 55 deg, 2.14 = 65 deg);
# CAPAC_LATIME = x scale of the hood (narrower).
# Usage: python capac_cavitate.py <teren_086_ps.npz> <teren_ps.npz> <out.npz> [lift] [wall] [roof] [mid] [emb]
import sys, numpy as np, cv2
from scipy.ndimage import distance_transform_edt as edt, map_coordinates, gaussian_filter
from skimage.measure import marching_cubes
H = np.load(sys.argv[1]); P = np.load(sys.argv[2]); OUT = sys.argv[3]
A = [float(t) for t in sys.argv[4:]] + [None] * 5
LIFT = A[0] or 12.0; WALL = A[1] or 4.0; ROOF = A[2] or 4.0; MID = A[3] or 4.0; EMB = A[4] or 3.0; C = 0.5
import os
SX = float(os.environ.get("CAPAC_LATIME", "1"))                        # the hood narrowed (its outline and its top scaled in x)
ol = H["outline"][:, :2] * [SX, 1]; X0, Y0 = ol[:, 0].min() - 10, ol[:, 1].min() - 10; NX, NY = int((np.ptp(ol[:, 0]) + 20) / C), int((np.ptp(ol[:, 1]) + 20) / C)
S = 4; m = np.zeros((NY * S, NX * S), np.uint8); cv2.fillPoly(m, [np.round((ol - [X0, Y0]) / C * S).astype(np.int32)], 1)
d2 = ((edt(m == 0) - edt(m == 1)) * C / S)[S // 2::S, S // 2::S][:NY, :NX]   # < 0 inside the hood's outline
xs = X0 + (np.arange(NX) + 0.5) * C; ys = Y0 + (np.arange(NY) + 0.5) * C; X, Y = np.meshgrid(xs, ys, indexing="xy")
g = lambda T, F, sx=1.0: map_coordinates(T[F].astype(float), [(Y - float(T["y0"])) / float(T["cell"]) - 0.5, (X / sx - float(T["x0"])) / float(T["cell"]) - 0.5], order=1, mode="nearest")
pt = g(P, "top"); zt = g(H, "top", SX) + LIFT; zb = pt - EMB
zt = pt + float(__import__("os").environ.get("CAPAC_SCARA_H", "1")) * (zt - pt)   # the hood's height over the piece scaled
import os
KS = float(os.environ.get("CAPAC_PANTA_LAT", "0")); KB = float(os.environ.get("CAPAC_PANTA_SPATE", "0"))   # walls leaning in: m in per
yb = ol[:, 1].min(); wb = np.clip((yb + 60 - Y) / 60, 0, 1); wb = wb * wb * (3 - 2 * wb); KK = KS * (1 - wb) + KB * wb   # m up (back: KB)
pt0 = map_coordinates(P["top"].astype(float), [(Y - float(P["y0"])) / float(P["cell"]) - 0.5, (X - float(P["x0"])) / float(P["cell"]) - 0.5], order=1, mode="nearest")
yf = ol[:, 1].max(); dc = d2 + WALL                                      # the cavity: inside the walls, open at the front (the last
FR = float(__import__("os").environ.get("CAPAC_FATA", "40"))          # rows carry the full-width section from FR m behind the front
row = int(np.clip((yf - FR - Y0) / C, 0, NY - 1)); dc[row:] = dc[row]  # forward, out through the front - between the front horns too)
gy_, gx_ = np.gradient(zt, C); st = np.sqrt(1 + gx_ ** 2 + gy_ ** 2)
zs = np.arange(np.floor(zb.min()) - 3, np.ceil(zt.max()) + 3, C); F = np.empty((len(zs), NY, NX), np.float32)
sm = lambda a, b, k: (a + b + np.sqrt((a - b) ** 2 + k ** 2)) / 2
for k, z in enumerate(zs):
    lean = KK * np.maximum(z - pt0, 0)                                  # the outline drawn in KK m per m up (walls at atan(KK) from vertical)
    solid = sm(d2 + lean, sm((z - zt) / st, zb - z, 1.5), 2.0)
    cav = np.maximum.reduce([dc + lean, pt + 0.0 - z, z - (zt - ROOF), MID / 2 - np.abs(X)])   # < 0 inside the cavity
    F[k] = np.maximum(solid, -cav)
F = gaussian_filter(F, 0.6)
v, f, _, _ = marching_cubes(F, 0.0, spacing=(C, C, C)); v = v[:, [2, 1, 0]] + [xs[0], ys[0], zs[0]]; f = f[:, ::-1]
np.savez(OUT, v=v.astype(np.float32), f=f.astype(np.int32))
inside = (d2 < -WALL) & (np.abs(X) > MID / 2); h = (zt - ROOF - pt)[inside]
print("CAPAC cu cavitate: ridicat %.0f m; pereti %.0f m, acoperis %.0f m, perete de mijloc %.0f m; inaltimea cavitatii %.0f..%.0f m (mediana %.0f); deschis in fata (y %.0f); %d fete" % (
    LIFT, WALL, ROOF, MID, h.min(), h.max(), np.median(h), yf, len(f)))
