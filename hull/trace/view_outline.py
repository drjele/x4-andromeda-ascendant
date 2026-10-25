# Outlines of a reference view from its negative (ship vs the flat background), the way the profile and bottom views
# were done: background = dark AND flat, reaching the border, plus enclosed flat-dark holes; the view's symmetry axis
# found on the silhouette and one half (the better lit one, or the one asked) mirrored; the borders traced and made
# smooth and continuous (periodic smoothing spline), numbered; the negative shown in green.
# Usage: python view_outline.py <image> <out_dir> <tag> <axis: v|h> [half: a|b|auto] [hole_min_px]
import sys, json, numpy as np, cv2
from scipy.interpolate import splprep, splev
IMG, OD, TAG, AXD = sys.argv[1:5]; HALF = sys.argv[5] if len(sys.argv) > 5 else "auto"; HMIN = int(sys.argv[6]) if len(sys.argv) > 6 else 1200; K = 4
im = cv2.imread(IMG); big = cv2.resize(im, None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC); H, W = big.shape[:2]
g = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY).astype(np.float32); bgv = float(np.median(np.r_[g[:8].ravel(), g[-8:].ravel()]))
mu = cv2.blur(g, (9, 9)); sd = np.sqrt(np.maximum(cv2.blur(g * g, (9, 9)) - mu * mu, 0))
flat = ((mu <= bgv + 3) & (sd <= 3.0)).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(flat, connectivity=4)
bg = np.zeros((H, W), bool)
for i in range(1, n):
    x, y, w, h, a = st[i]
    if x == 0 or y == 0 or x + w == W or y + h == H or a >= HMIN: bg |= lab == i
ship = ~bg
# symmetry axis
if AXD == "h": ship_t = ship
else: ship_t = ship.T
L_ = ship_t.shape[0]; rows = np.nonzero(ship_t.any(1))[0]; best = None
for a2 in range(2 * rows.min() + 20, 2 * rows.max() - 20, 2):
    idx = a2 - np.arange(L_); ok = (idx >= 0) & (idx < L_); f = np.zeros_like(ship_t); f[ok] = ship_t[idx[ok]]
    sc = (f & ship_t).sum() / max((f | ship_t).sum(), 1)
    if best is None or sc > best[0]: best = (sc, a2)
AX = best[1] / 2
r = np.arange(L_); src = np.clip(np.where(r <= AX, r, np.round(2 * AX - r).astype(int)), 0, L_ - 1); src_b = np.clip(np.where(r >= AX, r, np.round(2 * AX - r).astype(int)), 0, L_ - 1)
gt = g if AXD == "h" else g.T
if HALF == "auto": HALF = "a" if gt[:int(AX)][ship_t[:int(AX)]].mean() >= gt[int(AX):][ship_t[int(AX):]].mean() else "b"
sel = src if HALF == "a" else src_b
ship_m = ship_t[sel]; ship_m = ship_m if AXD == "h" else ship_m.T
bgm = ~ship_m; vis = (big[sel] if AXD == "h" else big[:, sel]).copy()
# outlines: smooth closed curves of the mirrored ship mask
sm = (cv2.GaussianBlur(ship_m.astype(np.float32), (0, 0), 6) > 0.5).astype(np.uint8)
cs, _ = cv2.findContours(sm, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE); curves = []
def periodic(c, tol=3.5):
    c = c.astype(float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
    t = np.linspace(0, d[-1], max(int(d[-1] / 8), 12), endpoint=False); q = np.stack([np.interp(t, d, c[:, i]) for i in (0, 1)], 1); q = np.vstack([q, q[:1]])
    tck, _ = splprep([q[:, 0], q[:, 1]], s=len(q) * tol ** 2, per=1, k=3); return np.stack(splev(np.linspace(0, 1, max(200, int(d[-1] / 2))), tck), 1)
for c in cs:
    if cv2.contourArea(c) < 600: continue
    curves.append(periodic(c[:, 0, :]))
curves.sort(key=lambda c: -cv2.contourArea(np.round(c).astype(np.int32)))
out = vis.copy(); out[bgm] = (0, 170, 0)
if AXD == "h": cv2.line(out, (0, int(AX)), (W, int(AX)), (255, 255, 0), 1)
else: cv2.line(out, (int(AX), 0), (int(AX), H), (255, 255, 0), 1)
for c in curves: cv2.polylines(out, [np.round(c).astype(np.int32)], True, (255, 80, 255), 5, cv2.LINE_AA)
for k, c in enumerate(curves):
    q = c[int(len(c) * 0.15)]; p = (int(q[0]), int(q[1])); cv2.circle(out, p, 30, (255, 255, 255), -1); txt = "C%d" % (k + 1)
    cv2.putText(out, txt, (p[0] - 9 * len(txt), p[1] + 11), 0, 0.95, (200, 0, 200), 3)
np.save(f"{OD}/{TAG}_fundal.npy", bgm); json.dump({"axis": AX, "axis_dir": AXD, "half": HALF, "outlines": [c.tolist() for c in curves]}, open(f"{OD}/{TAG}_contur.json", "w"))
cv2.imwrite(f"{OD}/{TAG}_contur_numerotat.png", cv2.resize(out, None, fx=0.5, fy=0.5)); print("VIEW %s axis %.1f (%s, IoU %.3f), half %s, %d outlines" % (TAG, AX, AXD, best[0], HALF, len(curves)))
