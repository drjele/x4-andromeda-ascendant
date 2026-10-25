# Bottom view, edits by number on jos_reguli (2026-10-25): line 1 carried on to the outer outline C1 at its front end;
# line 3 drawn a little toward line 2 at the centreline; line 6 continued up alongside C7's upper edge to line 1; C1
# split into sections at the points where the inner lines meet it, each section smoothed (rules) with its ends held;
# everything mirrored, numbered.
# Usage: python bottom_edits.py <dir>
import sys, json, numpy as np, cv2
from scipy.interpolate import splprep, splev
O = sys.argv[1]; AX = 883.0; J = json.load(open(f"{O}/jos_reguli.json"))
OUT_ = [np.array(c) for c in J["outlines"]]; L = [np.array(c) for c in J["lines"]]
mir = lambda c: np.stack([c[:, 0], 2 * AX - c[:, 1]], 1)
def spline(p, tol, closed=False, pin=True):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]; keep = np.r_[True, np.diff(d) > 1e-6]; p, d = p[keep], d[keep]
    t = np.linspace(0, d[-1], max(int(d[-1] / 7), 8)); q = np.stack([np.interp(t, d, p[:, i]) for i in (0, 1)], 1)
    w = np.ones(len(q)); w[[0, -1]] = 60 if pin and not closed else 1
    tck, _ = splprep([q[:, 0], q[:, 1]], w=w, s=len(q) * tol ** 2, per=1 if closed else 0, k=3)
    return np.stack(splev(np.linspace(0, 1, max(80, int(d[-1] / 2))), tck), 1)
upper = lambda c: c[len(c) // 2][1] < AX
C1 = OUT_[0]; C7 = OUT_[6]
# 1: the left end carried along its direction until it meets C1
l1 = L[0] if L[0][0][0] < L[0][-1][0] else L[0][::-1]
dv = l1[0] - l1[10]; dv /= np.linalg.norm(dv); seg = []
for t in range(2, 700, 2):
    q = l1[0] + dv * t; seg.append(q)
    if np.min(np.hypot(*(C1 - q).T)) < 3: break
# meet C1.1 a third of the way back from the arm's tip (not at the tip): the line's front part bent down onto C1.1,
# leaving it tangent to its own course at x0
x0, xm = 640.0, 450.0
c11 = C1[(C1[:, 1] < AX) & (C1[:, 0] < 1500)]; tgt = c11[np.argmin(np.hypot(c11[:, 0] - xm, c11[:, 1] - 302))]
body = l1[l1[:, 0] >= x0]; p0 = body[0]; tv = body[0] - body[6]; tv /= np.linalg.norm(tv)
ctl = p0 + tv * np.hypot(*(tgt - p0)) * 0.5; t_ = np.linspace(0, 1, 40)[:, None]; bend = (1 - t_) ** 2 * p0 + 2 * (1 - t_) * t_ * ctl + t_ ** 2 * tgt
l1 = spline(np.vstack([bend[::-1], body[1:]]), 5.0)
# 3: the middle drawn toward line 2 (a Gaussian bump across the centreline)
l3 = L[3].copy(); l3[:, 0] -= 18 * np.exp(-0.5 * ((l3[:, 1] - AX) / 110) ** 2)
# 6: from its upper end alongside C7's upper edge, to line 1
l6 = L[8] if L[8][0][1] < L[8][-1][1] else L[8][::-1]                    # upper end first
i0 = np.argmin(C7[:, 0] - C7[:, 1] * 0); tip_lo = np.argmax(C7[:, 0] + C7[:, 1]); tip_hi = np.argmin(C7[:, 0] + C7[:, 1])   # the crescent's two tips
n = len(C7); a = list(range(tip_lo, tip_lo + ((tip_hi - tip_lo) % n) + 1)); b = list(range(tip_hi, tip_hi + ((tip_lo - tip_hi) % n) + 1))
ea, eb = C7[[i % n for i in a]], C7[[i % n for i in b]]
up_edge = ea if np.mean(ea[:, 1] - ea[:, 0] * 0.6) < np.mean(eb[:, 1] - eb[:, 0] * 0.6) else eb
if np.hypot(*(up_edge[0] - l6[0])) > np.hypot(*(up_edge[-1] - l6[0])): up_edge = up_edge[::-1]
tg = np.gradient(up_edge, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]; nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
ctr = C7.mean(0); nr *= np.sign(((up_edge - ctr) * nr).sum(1))[:, None]   # pointing away from the crescent
along = up_edge + nr * 7
end = l1[np.argmin(np.hypot(*(l1 - along[-1]).T))]
l6 = spline(np.vstack([l6[::-1], along, end[None]]), 4.0)
lines = [l1, mir(l1), L[2], l3, L[4], L[5], L[6], L[7], l6, mir(l6), L[10], L[11]]
# the corner between C1.1 and C1.2 (where the arm's inner edge meets the body's top) made sharp on the real edge,
# line 4 started exactly there, and line 7 carried down to meet line 4 (and the mirrors)
shipm = (~np.load(f"{O}/salvat_jos_v1/jos_fundal_verde.npy")).astype(np.uint8)
rawo = max(cv2.findContours(shipm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0, :].astype(float)
l4 = lines[4] if lines[4][0][0] < lines[4][-1][0] else lines[4][::-1]
near = rawo[np.hypot(*(rawo - l4[0]).T) < 70]; P = near[np.argmax(near[:, 0])] + np.array([38.0, -6.0])   # a little right, by the red strip
w = np.clip(1 - np.r_[0, np.cumsum(np.hypot(*np.diff(l4, axis=0).T))] / 250, 0, 1) ** 2; l4 = l4 + np.outer(w, P - l4[0])
l7 = lines[10] if lines[10][0][1] < lines[10][-1][1] else lines[10][::-1]   # upper end first
k = int(np.argmin(np.hypot(*(l4 - l7[-1]).T))); l7 = np.vstack([l7, np.linspace(l7[-1], l4[k], 12)[1:]]); l7 = spline(l7, 3.0)
l6b = lines[8] if np.hypot(*(lines[8][0] - P)) < np.hypot(*(lines[8][-1] - P)) else lines[8][::-1]   # line 6's lower end brought to the corner too
w6 = np.clip(1 - np.r_[0, np.cumsum(np.hypot(*np.diff(l6b, axis=0).T))] / 200, 0, 1) ** 2; l6b = l6b + np.outer(w6, P - l6b[0])
lines[4], lines[5], lines[10], lines[11], lines[8], lines[9] = l4, mir(l4), l7, mir(l7), l6b, mir(l6b)
C1 = C1.copy()
for Q in (P, np.array([P[0], 2 * AX - P[1]])):                            # C1 pulled onto the raw edge near the corner, the corner exactly on it
    d = np.hypot(*(C1 - Q).T); i = int(np.argmin(d)); arc = np.abs(np.r_[0, np.cumsum(np.hypot(*np.diff(C1, axis=0).T))] - np.r_[0, np.cumsum(np.hypot(*np.diff(C1, axis=0).T))][i])
    ww = np.clip(1 - arc / 140, 0, 1); ww = ww * ww * (3 - 2 * ww); nearp = rawo[[int(np.argmin(np.hypot(*(rawo - c).T))) for c in C1[ww > 0]]]
    C1[ww > 0] = C1[ww > 0] * (1 - ww[ww > 0, None]) + nearp * ww[ww > 0, None]; C1[i] = Q
# the U arch even in thickness: its inner strand (3) redrawn at a constant distance from the outer one (2), the
# thickness the arch has where it joins the arm's rear loop (the strut between the two windows)
C6w, C5w = OUT_[5], OUT_[4]
dd = np.hypot(*(C6w[:, None] - C5w[None]).transpose(2, 0, 1)); WU = float(dd.min())
l2 = lines[2]; tg = np.gradient(l2, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]; nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
mid3 = lines[3][len(lines[3]) // 2]; mid2 = l2[len(l2) // 2]
if np.dot(nr[len(l2) // 2], mid3 - mid2) < 0: nr = -nr                    # toward the inner strand
l3n = spline(l2 + nr * WU, 4.0)
for e in (0, -1):                                                           # its ends carried on to the windows
    p = l3n[e]; dv = l3n[e] - l3n[e + 10 if e == 0 else e - 10]; dv /= np.linalg.norm(dv); seg = []
    for t in range(2, 600, 2):
        q = p + dv * t; seg.append(q)
        if any(np.min(np.hypot(*(o - q).T)) < 3 for o in OUT_[1:]): break
    else: seg = []
    if seg: l3n = np.vstack([np.array(seg)[::-1], l3n]) if e == 0 else np.vstack([l3n, np.array(seg)])
UNIFORM = False                                                             # off: back to the confirmed outlines (2026-10-25)
if UNIFORM: lines[3] = l3n; print("U arch thickness", round(WU, 1))
# the U arch's strands (2, 3) carried on along the facing sides of the two windows (C6 / C5) up to the outer arm's
# inner edge, where a short line (8) closes the strut between the windows; mirrored for C3 / C4
def along_window(line, win, tip):
    up = line if line[0][1] > line[-1][1] else line[::-1]                   # (upper half) the end nearer the window last
    if up[-1][1] > AX: up = up[::-1]
    i0 = int(np.argmin(np.hypot(*(win - up[-1]).T))); i1 = int(np.argmin(np.hypot(*(win - tip).T))); n_ = len(win)
    fw = [(i0 + k) % n_ for k in range((i1 - i0) % n_ + 1)]; bw = [(i0 - k) % n_ for k in range((i0 - i1) % n_ + 1)]
    path = win[fw] if len(fw) < len(bw) else win[bw]
    return path
C6u, C5u = OUT_[5], OUT_[4]
tip6 = C6u[np.argmax(C6u[:, 0] - C6u[:, 1])]; tip5 = C5u[np.argmin(C5u[:, 1] + 0.3 * C5u[:, 0])]   # C6's top-right corner, C5's top-left corner
def edge_dir(win, tip, toward):                                             # the direction of a window's top edge at its corner, pointing away along it
    i = int(np.argmin(np.hypot(*(win - tip).T))); n_ = len(win); a_, b_ = win[(i - 25) % n_], win[(i + 25) % n_]
    q = a_ if np.dot(a_ - tip, toward) < np.dot(b_ - tip, toward) else b_; v = tip - q; return v / np.linalg.norm(v)
d6 = edge_dir(C6u, tip6, tip5 - tip6); d5 = edge_dir(C5u, tip5, tip6 - tip5); L8 = np.hypot(*(tip5 - tip6)) * 0.4
t_ = np.linspace(0, 1, 40)[:, None]; P1, P2 = tip6 + d6 * L8, tip5 + d5 * L8
l8 = (1 - t_) ** 3 * tip6 + 3 * (1 - t_) ** 2 * t_ * P1 + 3 * (1 - t_) * t_ ** 2 * P2 + t_ ** 3 * tip5   # line 8 carries C6's top edge on into C5's
def side(win, a_, b_):                                                     # the shorter run of a window's edge from point a_ to point b_
    n_ = len(win); i0 = int(np.argmin(np.hypot(*(win - a_).T))); i1 = int(np.argmin(np.hypot(*(win - b_).T)))
    fw = [(i0 + k) % n_ for k in range((i1 - i0) % n_ + 1)]; bw = [(i0 - k) % n_ for k in range((i0 - i1) % n_ + 1)]
    return win[fw] if len(fw) < len(bw) else win[bw]
starts = {2: (C6u, C6u[np.argmax(C6u[:, 1])], tip6), 3: (C5u, C5u[np.argmin(C5u[:, 0])], tip5)}   # C6 from its lowest point, C5 from its front tip
for li, (win, s0, tip) in starts.items():                                  # each strand: straight to the window, then along its facing side to line 8
    c = lines[li]; top_e = 0 if c[0][1] < c[-1][1] else -1; p = c[top_e]
    run = side(win, s0, tip); ext = spline(np.vstack([np.linspace(p, run[0], 15)[1:-1], run]), 2.5)
    c2 = np.vstack([c, ext]) if top_e == -1 else np.vstack([ext[::-1], c])
    lines[li] = np.vstack([mir(ext)[::-1], c2]) if top_e == -1 else np.vstack([c2, mir(ext)])
for li, tip in ((2, tip6), (3, tip5)):                                      # each strand refitted whole: one completely smooth curve, its ends on line 8's corners
    c = lines[li]; c = c if c[0][1] < c[-1][1] else c[::-1]
    c = spline(c, 6.0); c[0] = tip; c[-1] = [tip[0], 2 * AX - tip[1]]
    c = spline(c, 1.0); lines[li] = c
lines += [l8, mir(l8)]
# C1 in sections: cut where line ends touch it
cuts = sorted({int(np.argmin(np.hypot(*(C1 - p).T))) for c in lines for p in (c[0], c[-1]) if np.min(np.hypot(*(C1 - p).T)) < 6})
secs = []
for k in range(len(cuts)):
    i, j = cuts[k], cuts[(k + 1) % len(cuts)]; idx = np.arange(i, j + 1) if j > i else np.r_[np.arange(i, len(C1)), np.arange(0, j + 1)]
    if len(idx) > 10: secs.append(spline(C1[idx], 4.5))
others = [spline(c, 3.0, closed=True, pin=False) for c in OUT_[1:]]
# C6's upper right corner pulled onto the ship's real edge (the raw background contour) and kept sharp, for C6 and its mirror C3
bgm = np.load(f"{O}/salvat_jos_v1/jos_fundal_verde.npy").astype(np.uint8); nl, lab = cv2.connectedComponents(bgm, connectivity=4)
def sharpen(c, corner_key, R=170):
    ctr = c.mean(0).astype(int); m = (lab == lab[ctr[1], ctr[0]]).astype(np.uint8); raw = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0][0][:, 0, :].astype(float)
    k = np.argmax(corner_key(c)); d = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]; dd = np.abs(d - d[k]); dd = np.minimum(dd, d[-1] - dd)
    w = np.clip(1 - dd / R, 0, 1); w = w * w * (3 - 2 * w); near = raw[[int(np.argmin(np.hypot(*(raw - p).T))) for p in c]]
    c = c * (1 - w[:, None]) + near * w[:, None]
    return spline(np.vstack([c, c[:1]]), 2.0, closed=True, pin=False)      # one continuous line, the V just rounded
others[4] = sharpen(others[4], lambda c: c[:, 0] - c[:, 1])                # C6 (upper half)
others[1] = mir(others[4])                                                 # C3 = its mirror
bg = np.load(f"{O}/salvat_jos_v1/jos_fundal_verde.npy"); H, W = bg.shape
im = cv2.resize(cv2.imread("/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01/bottom.png"), (W, H), interpolation=cv2.INTER_CUBIC)
r = np.arange(H); src = np.clip(np.where(r <= AX, r, np.round(2 * AX - r).astype(int)), 0, H - 1); out = im[src].copy(); out[bg] = (0, 170, 0)
for c in secs + others: cv2.polylines(out, [np.round(c).astype(np.int32)], c is not None and any(c is o for o in others), (255, 80, 255), 5, cv2.LINE_AA)
for c in lines: cv2.polylines(out, [np.round(c).astype(np.int32)], False, (0, 220, 255), 5, cv2.LINE_AA)
def tag(c, txt, col):
    q = c[len(c) // 2]; p = (int(q[0]) + 12, int(q[1]) + 12); cv2.circle(out, p, 30, (255, 255, 255), -1); cv2.putText(out, txt, (p[0] - 9 * len(txt), p[1] + 11), 0, 0.95, col, 3)
for k, c in enumerate(secs): tag(c, "C1.%d" % (k + 1), (200, 0, 200))
for k, c in enumerate(others): tag(c, "C%d" % (k + 2), (200, 0, 200))
names = {0: "1", 2: "2", 3: "3", 4: "4", 6: "5", 8: "6", 10: "7", 12: "8"}
for k, txt in names.items(): tag(lines[k], txt, (0, 120, 200))
json.dump({"c1_sections": [c.tolist() for c in secs], "outlines": [c.tolist() for c in others], "lines": [c.tolist() for c in lines]}, open(f"{O}/jos_reguli_v2.json", "w"))
cv2.imwrite(f"{O}/jos_reguli_v2.png", cv2.resize(out, None, fx=0.5, fy=0.5)); print("EDITS C1 sections %d" % len(secs))
