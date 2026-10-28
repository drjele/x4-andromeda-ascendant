# The inner top silhouette (the U between the arms) redrawn (asked: its sides went over the reference arms seen from above -
# smaller angle between them; the top a bit rounder): each side a straight SUPPORT line of the reference arms' inner edge
# (seen from above, over y in [Y1, Y0]): the slope whose line stays in the gap and touches the edge from the gap side (TOLQ
# of the edge points allowed past it); the top one circle arc tangent to both sides, its top kept at the U's height (YU).
# The line runs to the old line's end height. The outer silhouette kept. Writes B (outer, unchanged) and B_int (new).
# Usage: python ghid_interior_nou.py <esantion_punte.npz> <ghid_drept2.npz> <out.npz> [png]
import sys, os, numpy as np, cv2
D = np.load(sys.argv[1]); G = np.load(sys.argv[2]); OUT = sys.argv[3]; PNG = sys.argv[4] if len(sys.argv) > 4 else None
env = lambda k, d: float(os.environ.get(k, d)); Y0, Y1, TOLQ, CEN = env("GI_Y0", "-120"), env("GI_Y1", "-817"), env("GI_TOL", "0.01"), -4.68
old = G["B_int"]; YU = float(old[:, 1].max()); YE = float(old[:, 1].min())
P = D["ps"][:, :2].copy(); P[:, 0] -= CEN; P = P[(P[:, 1] < -20) & (P[:, 1] > YE - 20) & (np.abs(P[:, 0]) < 329)]
PX = 1.0; XM = 330.0; y0 = YE - 20; H = int((-20 - y0) / PX) + 2; W = int(2 * XM / PX)
m = np.zeros((H, W), np.uint8); m[((P[:, 1] - y0) / PX).astype(int), ((P[:, 0] + XM) / PX).astype(int)] = 1
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))); m = np.maximum(m, m[:, ::-1])
inn = []
for r in range(H):
    y = y0 + r * PX
    if not (Y1 <= y <= Y0): continue
    xs = np.nonzero(m[r, W // 2:])[0] * PX
    xs = xs[xs < 300]
    if len(xs) and xs.min() > 2: inn.append((xs.min(), y))
inn = np.array(inn); best = None
for b in np.linspace(-0.6, 0.0, 601):                                 # x = a + b*y, staying in the gap (x <= edge)
    a = np.quantile(inn[:, 0] - b * inn[:, 1], TOLQ); cost = np.mean(inn[:, 0] - (a + b * inn[:, 1]))
    if best is None or cost < best[0]: best = (cost, a, b)
cost, a, b = best
d = np.array([b, 1.0]) / np.hypot(b, 1.0); d = -d if d[1] > 0 else d   # the side's direction, downwards
nrm = np.array([1.0, -b]) / np.hypot(1.0, b)                            # normal of x - b*y = a (unit), pointing to +x
# circle on the axis, top at YU, tangent to the line: |(0, yc)·nrm - a/|..|| = R with yc = YU - R
k = 1.0 / np.hypot(1.0, b)                                              # line: k*x - k*b*y - k*a = 0
f = lambda R: abs(k * 0 - k * b * (YU - R) - k * a) - R
lo, hi = 1.0, 500.0
for _ in range(80):
    mid = (lo + hi) / 2
    if np.sign(f(mid)) == np.sign(f(lo)): lo = mid
    else: hi = mid
R = (lo + hi) / 2; yc = YU - R; c = np.array([0.0, yc])
t = c + nrm * R * (1 if (a + b * yc) > 0 else -1) if False else None
foot = c - (k * c[0] - k * b * c[1] - k * a) * np.array([k, -k * b])    # tangent point = foot of the perpendicular from the centre
end = np.array([a + b * YE, YE])
q0, q1 = np.pi / 2, np.arctan2(foot[1] - yc, foot[0])
arc = np.array([c + R * np.array([np.cos(q), np.sin(q)]) for q in np.linspace(q0, q1, 60)])
line = foot + np.outer(np.linspace(0, 1, int(np.linalg.norm(end - foot)) + 1)[1:], end - foot)
Rt = np.vstack([arc, line]); Bi = np.vstack([(Rt * [-1, 1])[::-1][:-1], Rt])
np.savez(OUT, B=G["B"], B_int=Bi, centru=CEN)
old_r = old[old[:, 0] >= 0]
oi = lambda y: np.interp(-y, -old_r[np.argsort(-old_r[:, 1])][:, 1], old_r[np.argsort(-old_r[:, 1])][:, 0])
print("SILUETA INTERIOARA noua: laturi x = %.1f %+.3f*y (vechi la y -500: %.0f, nou %.0f; la y %.0f: vechi %.0f, nou %.0f); arc R %.0f cu varful la y %.0f, tangent la (%.0f, %.0f); muchia bratelor: in medie la %.1f m de linie, %.0f %% puncte dincolo" % (
    a, b, oi(-500.0), a + b * -500, YE, oi(YE), end[0], R, YU, *foot, cost, 100 * np.mean(inn[:, 0] < a + b * inn[:, 1] - 0.5)))
if PNG:
    Q = D["ps"].copy(); Q[:, 0] -= CEN; Q = Q[(Q[:, 1] > -900) & (Q[:, 1] < 200) & (np.abs(Q[:, 0]) < 330)]
    sc = 0.9; im = np.full((int(1100 * sc) + 20, int(660 * sc) + 20, 3), 255, np.uint8)
    fxy = lambda X: np.stack([(X[:, 0] + 330) * sc + 10, (200 - X[:, 1]) * sc + 10], 1).astype(np.int32)
    for p in fxy(Q[::4, :2]): im[p[1], p[0]] = (185, 185, 185)
    cv2.polylines(im, [fxy(old)], False, (160, 160, 160), 2); cv2.polylines(im, [fxy(Bi)], False, (220, 80, 0), 2); cv2.polylines(im, [fxy(G["B"])], False, (0, 0, 220), 2)
    cv2.imwrite(PNG, im)
