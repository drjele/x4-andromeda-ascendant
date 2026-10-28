# Guide outlines of every sampled piece: its silhouette seen from above (x, y), from the side (y, z) and from the front
# (x, z), each the outer contour of the rasterized projection (closed over small gaps), lightly smoothed, resampled, and
# placed just outside the piece (above its top, beside its left side, before its front) so the three outlines frame it.
# Usage: python ghid_contur.py <samples.npz> <out.npz>
import sys, numpy as np, cv2
D = np.load(sys.argv[1]); OUT = sys.argv[2]; res = {}
def outline(P2):
    ext = max(np.ptp(P2[:, 0]), np.ptp(P2[:, 1]), 1.0); px = max(ext / 700, 0.25); o0 = P2.min(0) - 5 * px
    W, H = int(np.ptp(P2[:, 0]) / px) + 11, int(np.ptp(P2[:, 1]) / px) + 11; m = np.zeros((H, W), np.uint8)
    ij = np.round((P2 - o0) / px).astype(int); m[ij[:, 1], ij[:, 0]] = 1
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); out = []
    for c in cs:
        if cv2.contourArea(c) < 0.02 * m.sum(): continue
        c = c[:, 0].astype(float) * px + o0; k = np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2); k /= k.sum()
        c = np.stack([np.convolve(np.r_[c[-4:, i], c[:, i], c[:4, i]], k, "valid") for i in range(2)], 1)
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([c, c[:1]]), axis=0), axis=1))]; u = np.linspace(0, s[-1], max(int(s[-1] / (2 * px)), 40), endpoint=False)
        out.append(np.stack([np.interp(u, s, np.r_[c[:, i], c[0, i]]) for i in range(2)], 1))
    return out
for name in D.files:
    P = D[name]; lo, hi = P.min(0), P.max(0); g = 0.03 * max(np.ptp(P, 0)) + 1
    for i, L in enumerate(outline(P[:, [0, 1]])): res["%s|sus|%d" % (name, i)] = np.c_[L, np.full(len(L), hi[2] + g)]
    for i, L in enumerate(outline(P[:, [1, 2]])): res["%s|lateral|%d" % (name, i)] = np.c_[np.full(len(L), lo[0] - g), L]
    for i, L in enumerate(outline(P[:, [0, 2]])): res["%s|fata|%d" % (name, i)] = np.c_[L[:, 0], np.full(len(L), hi[1] + g), L[:, 1]]
np.savez(OUT, **res); print("CONTURURI", len(res), "pentru", len(D.files), "piese")
