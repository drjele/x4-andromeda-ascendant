# The belly V rebuilt for the new PS (asked: bigger, its top face the same as PS's flat bottom face): the top outline = PS's
# flat bottom seen from above (its points within 1.5 m of the bottom, raster 1 m, gaps closed, outer contour, smoothing
# spline, right half mirrored), at the bottom's height; the lower face = that outline scaled SC towards an anchor on the
# middle line AN of the length from the back (smaller, towards the back, as the confirmed belly); DEPTH deep; the side a
# slightly full curve between them (rings), both faces closed. Writes verts / faces (ship coordinates, centred).
# Usage: python burta_noua.py <ps_fin.npz> <out.npz> [depth] [scale] [anchor]
import sys, numpy as np, cv2
from scipy.interpolate import splprep, splev
Z = np.load(sys.argv[1]); OUT = sys.argv[2]; DEPTH = float(sys.argv[3]) if len(sys.argv) > 3 else 31.0
SC = float(sys.argv[4]) if len(sys.argv) > 4 else 0.55; AN = float(sys.argv[5]) if len(sys.argv) > 5 else 0.15
v = Z["v"]; zb = float(np.percentile(v[:, 2], 0.5)); B = v[v[:, 2] < zb + 1.5][:, :2]
x0, y0 = -300.0, B[:, 1].min() - 20; m = np.zeros((int(B[:, 1].max() - y0 + 20), 600), np.uint8); m[(B[:, 1] - y0).astype(int), (B[:, 0] - x0).astype(int)] = 1
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))); m = np.maximum(m, m[:, ::-1])
c = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0].astype(float); c = np.stack([c[:, 0] + x0, c[:, 1] + y0], 1)
tck, _ = splprep(c.T, s=len(c) * 1.0, per=1); top = np.array(splev(np.linspace(0, 1, 400, endpoint=False), tck)).T
top = np.roll(top, -int(np.argmax(top[:, 1] - 1e3 * np.abs(top[:, 0]))), axis=0)          # start at the front tip
R = top[1:201] if top[1, 0] > 0 else top[::-1][:200]; R = R[R[:, 0] > 0]; top = np.vstack([[[0, top[0, 1]]], R, (R * [-1, 1])[::-1]])   # symmetric
anc = np.array([0.0, top[:, 1].min() + AN * (top[:, 1].max() - top[:, 1].min())])
NR = 9; rings = []
for i in range(NR):
    t = i / (NR - 1); s = 1 - (1 - SC) * (t ** 0.8); rings.append(np.c_[anc + (top - anc) * s, np.full(len(top), zb - DEPTH * t)])
V = np.vstack(rings + [[[0, (top[:, 1].max() + top[:, 1].min()) / 2, zb]], [[*anc, zb - DEPTH]]]); n = len(top); K = len(rings)
F = [(k * n + i, (k + 1) * n + i, (k + 1) * n + (i + 1) % n, k * n + (i + 1) % n) for k in range(K - 1) for i in range(n)]
F += [(K * n, (i + 1) % n, i) for i in range(n)] + [(K * n + 1, (K - 1) * n + i, (K - 1) * n + (i + 1) % n) for i in range(n)]
np.savez(OUT, v=V.astype(np.float32), fq=np.array([f for f in F if len(f) == 4]), ft=np.array([f for f in F if len(f) == 3]))
area = 0.5 * abs(np.sum(top[:, 0] * np.roll(top[:, 1], -1) - np.roll(top[:, 0], -1) * top[:, 1]))
print("BURTA noua: sus = fundul PS la z %.0f (x %.0f..%.0f, y %.0f..%.0f, %.0f m2), jos x%.2f spre y %.0f la z %.0f" % (zb, top[:, 0].min(), top[:, 0].max(), top[:, 1].min(), top[:, 1].max(), area, SC, anc[1], zb - DEPTH))
