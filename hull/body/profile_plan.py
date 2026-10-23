# Proposed side profile: the control polyline closed around the whole body (top then bottom), resampled
# by arc length and smoothed as one closed curve, so the bow and stern round off without any break.
import json, numpy as np, cv2
R = np.array(json.load(open("super_rings.json"))); Y = R[:, 0, 1]; T0 = R[:, :, 2].max(1); B0 = R[:, :, 2].min(1)
P = json.load(open("profile_plan.json"))
top = sorted(P["top"], key=lambda p: -p[0]); bot = sorted(P["bottom"], key=lambda p: p[0])
loop = np.array(top + bot[1:-1], float)                     # bow -> stern along the top, back along the bottom
seg = np.linalg.norm(np.diff(np.vstack([loop, loop[:1]]), axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
L = s[-1]; ss = np.arange(0, L, 1.0)
closed = np.vstack([loop, loop[:1]])
pts = np.stack([np.interp(ss, s, closed[:, 0]), np.interp(ss, s, closed[:, 1])], 1)
def smooth(sig):
    r = int(3 * sig); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum()
    return np.stack([np.convolve(np.r_[pts[-r:, c], pts[:, c], pts[:r, c]], k, "valid") for c in (0, 1)], 1)
fine, wide = smooth(P["soft"]), smooth(P.get("end_soft", 55))
# wide rounding near the bow and the stern, fine everywhere else, blended smoothly
d_end = np.minimum(pts[:, 0].max() - pts[:, 0], pts[:, 0] - pts[:, 0].min())
w = np.exp(-(d_end / P.get("end_reach", 140)) ** 2)[:, None]
sm = fine * (1 - w) + wide * w
# split back into top and bottom at the two extremes in y
i_bow, i_st = sm[:, 0].argmax(), sm[:, 0].argmin()
a, b = sorted((i_bow, i_st)); part1, part2 = sm[a:b + 1], np.vstack([sm[b:], sm[:a + 1]])
tp, bt = (part1, part2) if part1[:, 1].mean() > part2[:, 1].mean() else (part2, part1)
yy = np.arange(sm[:, 0].min(), sm[:, 0].max() + 0.01, 2.0)
T = np.interp(yy, *zip(*sorted(zip(tp[:, 0], tp[:, 1])))); B = np.interp(yy, *zip(*sorted(zip(bt[:, 0], bt[:, 1]))))
json.dump({"y": yy.tolist(), "top": T.tolist(), "bottom": B.tolist()}, open("profile_target.json", "w"))
SC = 0.9; W, H = int((Y.max() - Y.min()) * SC) + 260, 560; img = np.full((H, W, 3), 255, np.uint8)
px = lambda y: int(120 + (Y.max() - y) * SC); pz = lambda z: int(300 - z * SC)
smp = np.array([[px(p[0]), pz(p[1])] for p in sm])
cv2.fillPoly(img, [smp], (225, 205, 175)); cv2.polylines(img, [smp], True, (40, 30, 20), 2)
for Z in (T0, B0):
    c = np.array([[px(y), pz(z)] for y, z in zip(Y, Z)])
    for p0, p1 in zip(c[:-1:6], c[3::6]): cv2.line(img, tuple(p0), tuple(p1), (130, 130, 130), 1)
for kk, ys in enumerate(range(1000, -800, -100), 1):
    x = px(ys); cv2.line(img, (x, 70), (x, 90), (0, 0, 220), 2); cv2.line(img, (x, 500), (x, 520), (0, 0, 220), 2)
    cv2.putText(img, f"S{kk}", (x - 18, 62), 0, 0.7, (0, 0, 220), 2); cv2.putText(img, f"y{ys}", (x - 24, 545), 0, 0.45, (0, 0, 220), 1)
cv2.putText(img, "PROFIL propus (plin) peste cel actual (gri punctat)", (20, 30), 0, 0.9, (0, 0, 0), 2)
cv2.imwrite("profile_plan.png", img)
