# "Regulile de contur" applied to the saved bottom-view outlines (salvat_jos_v1): the negative's outline kept; the
# inner lines without the tip stubs and the stray bit, each one smooth and continuous, lines reaching the centreline
# joined to their mirror, pieces of one border joined, free ends carried onto the nearest outline/line; ship pixels
# the smooth outline leaves outside (in the middle of the ship) marked separately as decorations.
# Usage: python apply_rules_bottom.py <dir>
import sys, json, numpy as np, cv2
from scipy.interpolate import splprep, splev
O = sys.argv[1]; S = f"{O}/salvat_jos_v1"; AX = 883.0
C = [np.array(c) for c in json.load(open(f"{S}/jos_contur_si_impartiri.json"))]; L = {i: C[i] for i in range(0, len(C), 2)}
OUTL = [np.array(c) for c in json.load(open(f"{S}/jos_contur_negativ.json"))]; bg = np.load(f"{S}/jos_fundal_verde.npy"); H, W = bg.shape
def smooth_closed(c, tol):
    # the negative's outline made even too: a periodic smoothing spline (the pixel steps and small bumps off)
    c = np.array(c, float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
    t = np.linspace(0, d[-1], max(int(d[-1] / 8), 12), endpoint=False); q = np.stack([np.interp(t, d, c[:, i]) for i in (0, 1)], 1); q = np.vstack([q, q[:1]])
    tck, _ = splprep([q[:, 0], q[:, 1]], s=len(q) * tol ** 2, per=1, k=3); return np.stack(splev(np.linspace(0, 1, max(200, int(d[-1] / 2))), tck), 1)
OUTL = [smooth_closed(c, 3.5) for c in OUTL]
mir = lambda c: np.stack([c[:, 0], 2 * AX - c[:, 1]], 1)
def spline(p, tol=6.0, n=None, closed=False):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]; keep = np.r_[True, np.diff(d) > 1e-6]; p, d = p[keep], d[keep]
    t = np.linspace(0, d[-1], max(int(d[-1] / 7), 8)); q = np.stack([np.interp(t, d, p[:, i]) for i in (0, 1)], 1)
    w = np.ones(len(q)); w[[0, -1]] = 1 if closed else 40
    if closed: q = np.vstack([q[:-1], q[:1]])
    tck, _ = splprep([q[:, 0], q[:, 1]], w=w, s=len(q) * tol ** 2, per=1 if closed else 0, k=3)
    return np.stack(splev(np.linspace(0, 1, n or max(80, int(d[-1] / 2))), tck), 1)
def to_target(c, targets, reach=120):
    # each free end carried along its direction until it meets an outline or another line (reach px at most)
    for e in (0, -1):
        p = c[e]; dv = c[e] - c[e + 8 if e == 0 else e - 8]; dv /= max(np.linalg.norm(dv), 1e-9); seg = []
        for t in range(2, reach, 2):
            q = p + dv * t; seg.append(q)
            if any(np.min(np.hypot(*(o - q).T)) < 3 for o in targets): break
        else: continue
        seg = np.array(seg); c = np.vstack([seg[::-1], c]) if e == 0 else np.vstack([c, seg])
    return c
lines = []
arm = spline(np.vstack([L[4], L[6]]), 7.0)                                 # the long arm's inner curve, one arc (the two drawn pieces)
lines += [arm, mir(arm)]
for k in (16, 18):                                                         # the U arch's two strands, through the axis
    a = L[k]; lines.append(spline(np.vstack([mir(a)[::-1], a]) if abs(a[0][1] - AX) < 30 else a, 7.0))
nose = spline(np.vstack([L[22], mir(L[22])[::-1]]) if abs(L[22][-1][1] - AX) > 30 else L[22], 5.0)
body_under = spline(L[20], 6.0); stern = spline(L[24], 4.0)
rest = [spline(L[12], 5.0), spline(np.vstack([L[8], L[14]]), 4.0)]
for c in [body_under, stern] + rest: lines += [c, mir(c)]   # the nose lines dropped (not a border)
targets = OUTL + lines
lines = [to_target(c, [t for t in targets if t is not c]) for c in lines]
# decorations: ship left outside the smooth outline
ship = (~bg).astype(np.uint8); inside = np.zeros((H, W), np.uint8)
for c in OUTL: cv2.fillPoly(inside, [np.round(c).astype(np.int32)], 1)
hole = np.zeros((H, W), np.uint8)
outer = max(OUTL, key=lambda c: cv2.contourArea(np.round(c).astype(np.int32)))
cv2.fillPoly(hole, [np.round(outer).astype(np.int32)], 1)
for c in OUTL:
    if c is not outer: cv2.fillPoly(hole, [np.round(c).astype(np.int32)], 0)
extra = (ship & (1 - hole)).astype(np.uint8); extra = cv2.morphologyEx(extra, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(extra); deco = []
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a > 150 and 400 < x < W - 300: deco.append(i)
im = cv2.resize(cv2.imread("/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01/bottom.png"), (W, H), interpolation=cv2.INTER_CUBIC)
r = np.arange(H); src = np.clip(np.where(r <= AX, r, np.round(2 * AX - r).astype(int)), 0, H - 1); out = im[src].copy(); out[bg] = (0, 170, 0)
for i in deco: out[lab == i] = (255, 255, 0)
for c in OUTL: cv2.polylines(out, [np.round(c).astype(np.int32)], True, (255, 80, 255), 5, cv2.LINE_AA)
for c in lines: cv2.polylines(out, [np.round(c).astype(np.int32)], False, (0, 220, 255), 5, cv2.LINE_AA)
def tag(c, txt, col):
    q = c[len(c) // 2]; p = (int(q[0]) + 12, int(q[1]) + 12); cv2.circle(out, p, 26, (255, 255, 255), -1); cv2.putText(out, txt, (p[0] - (18 if len(txt) > 1 else 9), p[1] + 11), 0, 1.0, col, 3)
for k, c in enumerate(OUTL): tag(c[int(len(c) * 0.3):], "C%d" % (k + 1), (200, 0, 200))
seen = []
for k, c in enumerate(lines):
    m = c[len(c) // 2]
    if m[1] > AX + 5 and any(np.hypot(m[0] - s_[0], 2 * AX - m[1] - s_[1]) < 40 for s_ in seen): continue   # one number per mirrored pair
    seen.append(m); tag(c, str(len(seen)), (0, 120, 200))
json.dump({"outlines": [c.tolist() for c in OUTL], "lines": [c.tolist() for c in lines]}, open(f"{O}/jos_reguli.json", "w"))
cv2.imwrite(f"{O}/jos_reguli.png", cv2.resize(out, None, fx=0.5, fy=0.5)); print("RULES lines %d, decorations %d" % (len(lines), len(deco)))
