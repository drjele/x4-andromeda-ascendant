# Bottom view, final clean-up of the inner lines (2026-10-25): the body's edge made one closed, even curve (the nose arc,
# its upper edge along the background, the drawn edge under the U arch, the stern), the inner curve of the long arms
# made one continuous arc, the stray tip pieces dropped, everything mirrored about the centreline.
# Usage: python beautify_bottom.py <dir>
import sys, json, numpy as np, cv2
from scipy.interpolate import splprep, splev
O = sys.argv[1]; AX = 883.0
C = [np.array(c) for c in json.load(open(f"{O}/salvat_jos_v1/jos_contur_si_impartiri.json"))]; L = {i: C[i] for i in range(0, len(C), 2)}
bg = np.load(f"{O}/jos_fundal_verde.npy"); H, W = bg.shape
def spline(p, closed, tol, n=1500):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]; keep = np.r_[True, np.diff(d) > 1e-6]; p, d = p[keep], d[keep]
    t = np.linspace(0, d[-1], max(int(d[-1] / 8), 10)); q = np.stack([np.interp(t, d, p[:, i]) for i in (0, 1)], 1)
    if closed:
        while len(q) > 4 and np.hypot(*(q[-1] - q[0])) < 6: q = q[:-1]
        q = np.vstack([q, q[:1]])
    tck, _ = splprep([q[:, 0], q[:, 1]], s=len(q) * tol ** 2, per=1 if closed else 0, k=3); return np.stack(splev(np.linspace(0, 1, n), tck), 1)
mir = lambda c: np.stack([c[:, 0], 2 * AX - c[:, 1]], 1)
# the body: upper half from the nose tip to the stern, then its mirror back
def edge_from_bg(x0, x1, y0):                                              # the body's top edge against the background, in a band
    pts = []
    for x in range(int(x0), int(x1), 6):
        col = bg[int(y0):int(AX), x]; ship = np.nonzero(~col)[0]
        if len(ship): pts.append((x, y0 + ship[0]))
    return np.array(pts, float)
nose = L[22][::-1]                                                         # (553,870) -> (687,804)
top = edge_from_bg(700, 1420, 600)
under = L[20]                                                              # (1511,677) -> (2147,620)
stern = L[24][::-1]                                                        # (2361,650) -> (2428,707)
back = []
for y in range(720, int(AX), 6):                                           # the stern face against the background
    row = bg[y, 2300:2600]; s = np.nonzero(~row)[0]
    if len(s): back.append((2300 + s[-1], y))
half = np.vstack([np.array([[nose[0][0] - 8, AX]]), nose, top, under, stern, np.array(back, float)])
loop = np.vstack([half, mir(half)[::-1][1:-1]]); body = spline(loop, True, 9.0)
arm = spline(np.vstack([L[4], L[6]]), False, 6.0)                         # inner curve of the long arms, one arc
keep = [spline(L[12], False, 5.0, 400)]                                    # arm edge toward AI
ush = spline(np.vstack([L[16], mir(L[16])[::-1]][::-1]), False, 6.0); ush2 = spline(np.vstack([L[18], mir(L[18])[::-1]][::-1]), False, 6.0)   # the U arch, through the axis
tail = [spline(np.vstack([L[8], L[14]]), False, 4.0, 300)]
lines = [body, arm, mir(arm), ush, ush2] + keep + [mir(c) for c in keep] + tail + [mir(c) for c in tail]
im = cv2.resize(cv2.imread("/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01/bottom.png"), (W, H), interpolation=cv2.INTER_CUBIC)
r = np.arange(H); src = np.clip(np.where(r <= AX, r, np.round(2 * AX - r).astype(int)), 0, H - 1); out = im[src].copy(); out[bg] = (0, 170, 0)
for c in json.load(open(f"{O}/jos_contur_negativ.json")): cv2.polylines(out, [np.round(np.array(c)).astype(np.int32)], True, (255, 80, 255), 5, cv2.LINE_AA)
cv2.polylines(out, [np.round(body).astype(np.int32)], True, (60, 60, 255), 5, cv2.LINE_AA)
for c in lines[1:]: cv2.polylines(out, [np.round(c).astype(np.int32)], False, (0, 220, 255), 5, cv2.LINE_AA)
json.dump({"body": body.tolist(), "lines": [c.tolist() for c in lines[1:]]}, open(f"{O}/jos_contur_si_impartiri_v3.json", "w"))
cv2.imwrite(f"{O}/jos_contur_si_impartiri_v3.png", cv2.resize(out, None, fx=0.5, fy=0.5)); print("BEAUTIFIED", len(lines))
