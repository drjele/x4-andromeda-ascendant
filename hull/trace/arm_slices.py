# Arm analysis: a smooth centre curve through the arm (principal curve: vertices binned along y, centroids, re-projected,
# smoothed, a few rounds) and the arm's sections in planes perpendicular to it (triangle/plane intersection segments),
# drawn per station with the boundary edges (holes) marked, to decide the arm's cross-section construction.
# Usage: python arm_slices.py <verts.npy> <faces.json> <out_dir> [stations]
import sys, json, numpy as np, cv2
P = np.load(sys.argv[1]); F = json.load(open(sys.argv[2])); OUT = sys.argv[3]; NST = int(sys.argv[4]) if len(sys.argv) > 4 else 12
T = np.array([f[:3] for f in F] + [[f[0], f[i], f[i + 1]] for f in F if len(f) > 3 for i in range(2, len(f) - 1)])
from collections import Counter
ec = Counter(tuple(sorted(e)) for f in F for e in zip(f, f[1:] + f[:1])); bnd = [e for e, c in ec.items() if c == 1]
# principal curve
ax = np.argmax(np.ptp(P, 0)); s = (P[:, ax] - P[:, ax].min()) / np.ptp(P[:, ax]); K = 60
for it in range(8):
    C = np.array([P[(s >= a) & (s < a + 1 / K)].mean(0) if ((s >= a) & (s < a + 1 / K)).sum() > 5 else np.full(3, np.nan) for a in np.linspace(0, 1 - 1 / K, K)])
    C = C[~np.isnan(C).any(1)]
    for _ in range(3): C[1:-1] = 0.25 * C[:-2] + 0.5 * C[1:-1] + 0.25 * C[2:]
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]; Cd = np.array([np.interp(np.linspace(0, seg[-1], 2000), seg, C[:, i]) for i in range(3)]).T
    j = np.array([np.argmin(np.linalg.norm(Cd - p, axis=1)) for p in P[::1]]); s = j / 1999.0
np.save(OUT + "/centru.npy", Cd)
tg = np.gradient(Cd, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
L = np.sum(np.linalg.norm(np.diff(Cd, axis=0), axis=1)); print("CENTRU lungime %.0f m" % L)
tiles = []
for st in np.linspace(0.03, 0.97, NST):
    i = int(st * 1999); o = Cd[i]; n = tg[i]; u = np.cross(n, [0, 0, 1.0]); u /= np.linalg.norm(u); v = np.cross(n, u)
    d = (P - o) @ n; segs = []
    for t in T:
        dd = d[t]
        if dd.min() > 0 or dd.max() < 0: continue
        pts = []
        for a_, b_ in ((0, 1), (1, 2), (2, 0)):
            if (dd[a_] > 0) != (dd[b_] > 0): w = dd[a_] / (dd[a_] - dd[b_]); pts.append(P[t[a_]] * (1 - w) + P[t[b_]] * w)
        if len(pts) == 2: segs.append(pts)
    segs = np.array(segs); Q = (segs - o) @ np.stack([u, v], 1) if len(segs) else np.zeros((0, 2, 2))
    near = Q[np.linalg.norm(Q.mean(1), axis=1) < 150] if len(Q) else Q
    im = np.full((400, 400, 3), 255, np.uint8); sc = 1.2
    for a_, b_ in near: cv2.line(im, tuple((a_ * [sc, -sc] + 200).astype(int)), tuple((b_ * [sc, -sc] + 200).astype(int)), (0, 0, 0), 1)
    for e in bnd:                                                            # holes: boundary edges crossing the plane
        if (d[e[0]] > 0) != (d[e[1]] > 0):
            w = d[e[0]] / (d[e[0]] - d[e[1]]); q = ((P[e[0]] * (1 - w) + P[e[1]] * w) - o) @ np.stack([u, v], 1)
            if np.linalg.norm(q) < 150: cv2.circle(im, tuple((q * [sc, -sc] + 200).astype(int)), 3, (0, 0, 255), -1)
    cv2.putText(im, "%.0f m" % (st * L), (5, 390), 0, 0.5, (0, 0, 0), 1); tiles.append(im)
rows = [np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]
cv2.imwrite(OUT + "/sectiuni_brat.png", np.vstack(rows)); print("muchii libere", len(bnd))
