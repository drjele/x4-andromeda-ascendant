# A plate component's outline seen from above, from ONE reference piece (asked for 055: our piece must look like R122
# 055_S from above - the _D piece is offset ~11 m, so pooling the two blurred it): its sampled points rasterized at PX,
# closed (gaps between samples), the outer contour lightly smoothed (corners kept), resampled. Writes (x, y) loop.
# Usage: python ps_contur_sus.py <esantion.npz> <key> <out.npz>
import sys, os, numpy as np, cv2
D = np.load(sys.argv[1]); Q = D[sys.argv[2]]; OUT = sys.argv[3]; PX = float(os.environ.get("CONTUR_PX", "0.5")); SG = float(os.environ.get("CONTUR_NET", "1.0"))
x0, y0 = Q[:, 0].min() - 10, Q[:, 1].min() - 10; W, H = int((np.ptp(Q[:, 0]) + 20) / PX), int((np.ptp(Q[:, 1]) + 20) / PX)
m = np.zeros((H, W), np.uint8); ij = np.round((Q[:, :2] - [x0, y0]) / PX).astype(int); m[ij[:, 1], ij[:, 0]] = 1
r = int(2.0 / PX); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)[:, 0].astype(float) * PX + [x0, y0]
n = int(3 * SG / PX); k = np.exp(-0.5 * (np.arange(-n, n + 1) * PX / SG) ** 2); k /= k.sum()
c = np.stack([np.convolve(np.r_[c[-n:, i], c[:, i], c[:n, i]], k, "valid") for i in range(2)], 1)
if np.sum(c[:, 0] * np.roll(c[:, 1], -1) - np.roll(c[:, 0], -1) * c[:, 1]) < 0: c = c[::-1]
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([c, c[:1]]), axis=0), axis=1))]; u = np.linspace(0, s[-1], 360, endpoint=False)
L = np.stack([np.interp(u, s, np.r_[c[:, i], c[0, i]]) for i in range(2)], 1)
np.savez(OUT, loop=L); print("CONTUR %s: x %.0f..%.0f y %.0f..%.0f, perimetru %.0f m, arie %.0f m2" % (sys.argv[2], L[:, 0].min(), L[:, 0].max(), L[:, 1].min(), L[:, 1].max(), s[-1], cv2.contourArea(L.astype(np.float32))))
