# The faces between a view's confirmed lines (view_lines.py): the lines drawn as borders, the region reaching the image
# border is the background, every other region is a face; a face and its mirror twin get one number; with a names file
# ({number: name}) the faces are filled per name and listed in a legend, so the user corrects the naming by number.
# Writes <prefix>_zone.npy (face number per pixel) and <prefix>_zone_numerotate.png.
# Usage: python line_zones.py <ref.png> <lines.json> <axis> <h|v> <out_prefix> [names.json|-] [cuts.json]
#        cuts.json = [[x1, y1, x2, y2], ...] proposed cuts on one half (mirrored), drawn dashed magenta T1, T2...
import sys, json, numpy as np, cv2
from scipy.ndimage import label
REF, LJ, AX, AD, OP = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4], sys.argv[5]; NM = json.load(open(sys.argv[6])) if len(sys.argv) > 6 and sys.argv[6] != "-" else {}
ref = cv2.imread(REF); H, W = ref.shape[:2]; lines = np.zeros((H, W), np.uint8)
for l in json.load(open(LJ)):
    for c in l["curves"]: cv2.polylines(lines, [np.round(np.array(c)).astype(np.int32)], False, 1, 7)
# small gaps the hand left at line ends closed (an end within GAP px of another line is carried onto it)
GAP = 40; cs = [np.array(c) for l in json.load(open(LJ)) for c in l["curves"]]
for i, c in enumerate(cs):
    if np.hypot(*(c[0] - c[-1])) < 5: continue
    for e in (0, -1):
        p = c[e]; best = None
        for j, o in enumerate(cs):
            q = o if j != i else (o[len(o) // 4:] if e == 0 else o[:-len(o) // 4])
            d = np.hypot(*(q - p).T); k = int(np.argmin(d))
            if 2 < d[k] < GAP and (best is None or d[k] < best[0]): best = (d[k], q[k])
        if best: cv2.line(lines, tuple(np.round(p).astype(int)), tuple(np.round(best[1]).astype(int)), 1, 7)
# proposed cuts (sheet px, one half; mirrored): short borders between parts that run into each other
CUTS = json.load(open(sys.argv[7])) if len(sys.argv) > 7 else []
cutm = np.zeros_like(lines)
for x1, y1, x2, y2 in CUTS:
    for a_, b_ in ((x1, x2), ((2 * AX - x1), (2 * AX - x2))) if AD == "v" else ((x1, x2),):
        cv2.line(cutm, (int(a_), int(y1)), (int(b_), int(y2)), 1, 7)
    if AD == "h": cv2.line(cutm, (int(x1), int(2 * AX - y1)), (int(x2), int(2 * AX - y2)), 1, 7)
lines |= cutm
lab, n = label(lines == 0); edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
info = []
for i in range(1, n + 1):
    if i in edge: continue
    ys, xs = np.nonzero(lab == i)
    if len(xs) < 1500: continue
    info.append((i, xs.mean(), ys.mean(), len(xs)))
def twin(x, y): return (2 * AX - x, y) if AD == "v" else (x, 2 * AX - y)
num = {}; k = 0
for i, x, y, _ in sorted(info, key=lambda t: (round(t[2] / 150), t[1])):
    if i in num: continue
    k += 1; num[i] = k; tx, ty = twin(x, y)
    j = min(info, key=lambda t: np.hypot(t[1] - tx, t[2] - ty))
    if j[0] != i and np.hypot(j[1] - tx, j[2] - ty) < 60: num[j[0]] = k
names = sorted(set(NM.values())); rng = np.random.default_rng(5); pal = {nm: rng.integers(60, 255, 3) for nm in names}; pal_n = {v: rng.integers(60, 255, 3) for v in set(num.values())}
out = (ref * 0.5).astype(np.uint8); z = np.zeros((H, W), np.int32)
for i, v in num.items():
    m = lab == i; c = pal.get(NM.get(str(v)), pal_n[v]); out[m] = (out[m] * 0.4 + c * 0.6).astype(np.uint8); z[m] = v
out[lines > 0] = (255, 255, 255)
for k_, (x1, y1, x2, y2) in enumerate(CUTS, 1):
    for (a1, b1, a2, b2) in [(x1, y1, x2, y2), ((2 * AX - x1, y1, 2 * AX - x2, y2) if AD == "v" else (x1, 2 * AX - y1, x2, 2 * AX - y2))]:
        P = np.linspace([a1, b1], [a2, b2], 16)
        for t in range(0, 15, 2): cv2.line(out, tuple(np.round(P[t]).astype(int)), tuple(np.round(P[t + 1]).astype(int)), (255, 0, 255), 9)
    cv2.putText(out, "T%d" % k_, (int(x2) + 12, int(y2) + 12), 0, 1.3, (255, 0, 255), 4)
for i, x, y, _ in info:
    m = (lab == i).astype(np.uint8); dt = cv2.distanceTransform(m, cv2.DIST_L2, 5); yy, xx = np.unravel_index(np.argmax(dt), dt.shape); t = str(num[i])
    cv2.circle(out, (int(xx), int(yy)), 28, (255, 255, 255), -1); cv2.putText(out, t, (int(xx) - 11 * len(t), int(yy) + 11), 0, 1.0, (0, 0, 0), 3)
if NM:
    side = np.zeros((H, 1150, 3), np.uint8)
    for j, (v, t) in enumerate(sorted(NM.items(), key=lambda kv: int(kv[0]))):
        y = 70 + 72 * j; cv2.rectangle(side, (30, y - 30), (90, y + 15), tuple(int(c) for c in pal[t]), -1)
        cv2.putText(side, "%s  %s" % (v, t), (110, y + 8), 0, 1.1, (235, 235, 235), 2, cv2.LINE_AA)
    out = np.hstack([out, side])
np.save(f"{OP}_zone.npy", z); cv2.imwrite(f"{OP}_zone_numerotate.png", cv2.resize(out, None, fx=0.5, fy=0.5)); print("FACES", len(info), "NUMBERS", k)
