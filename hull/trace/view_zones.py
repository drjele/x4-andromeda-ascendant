# Numbered faces of a view: the ship = the smoothed outlines of the negative (largest = outer border, the rest holes),
# cut by those outlines and by the user's lines drawn whole; the thin slivers between a hand line and the real edge
# dropped, the faces filled, mirrored halves numbered the same, drawn with numbers for the user to name.
# Usage: python view_zones.py <ref.png> <contour.json> <sliver_px> <out_prefix> <lines.json> ... [cut:x1,y1,x2,y2 ...]
#        cut = a short border the drawing implies but does not reach (e.g. a line tip to the outline), mirrored too
#        names:<file.json> = {number: name} drawn as a legend at the side
import sys, json, numpy as np, cv2
from scipy.ndimage import label
REF, CJ, SL, OP = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
ref = cv2.imread(REF); H, W = ref.shape[:2]; C = json.load(open(CJ)); AX = float(C["axis"]); O = [np.round(np.array(c)).astype(np.int32) for c in C["outlines"]]
ship = np.zeros((H, W), np.uint8); cv2.fillPoly(ship, [O[0]], 1); cv2.fillPoly(ship, O[1:], 0); bg = ship == 0
lines = np.zeros((H, W), np.uint8); cv2.polylines(lines, O, True, 1, 7)
for f in sys.argv[5:]:
    if f.startswith("names:"): continue
    if f.startswith("cut:"): x1, y1, x2, y2 = map(float, f[4:].split(",")); cv2.line(lines, (int(x1), int(y1)), (int(x2), int(y2)), 1, 7); continue
    d = json.load(open(f))
    for c in (d.values() if isinstance(d, dict) else d):
        c = np.array(c["points"] if isinstance(c, dict) else c); cv2.polylines(lines, [np.round(c).astype(np.int32)], False, 1, 7)
lines = cv2.morphologyEx(lines, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8)) > 0     # line ends a few px short of another line close on it
mx = np.clip(np.round(2 * AX - np.arange(W)).astype(int), 0, W - 1)
lines |= lines[:, mx]; bg = bg[:, np.minimum(np.arange(W), mx)]          # symmetric: a border on either side closes both, the ship as its left half
lab, n = label(~bg & ~lines); sizes = np.bincount(lab.ravel()); faces = [i for i in range(1, n + 1) if sizes[i] > 1500 and cv2.distanceTransform((lab == i).astype(np.uint8), cv2.DIST_L2, 5).max() > SL]
# number the left half first (by position), the right twin gets the same number
info = []
for i in faces:
    ys, xs = np.nonzero(lab == i); info.append((i, xs.mean(), ys.mean()))
num = {}; k = 0
for i, x, y in sorted(info, key=lambda t: (round(t[2] / 120), t[1])):
    if i in num: continue
    k += 1; num[i] = k
    tw = min(info, key=lambda t: np.hypot(t[1] - (2 * AX - x), t[2] - y))
    if tw[0] != i and np.hypot(tw[1] - (2 * AX - x), tw[2] - y) < 60: num[tw[0]] = k
rng = np.random.default_rng(3); pal = {v: rng.integers(60, 255, 3) for v in set(num.values())}
out = (ref * 0.55).astype(np.uint8); z = np.zeros((H, W), np.int32)
for i, v in num.items(): out[lab == i] = (out[lab == i] * 0.45 + pal[v] * 0.55).astype(np.uint8); z[lab == i] = v
out[lines] = (255, 255, 255)
for i, x, y in info:
    m = (lab == i).astype(np.uint8); dt = cv2.distanceTransform(m, cv2.DIST_L2, 5); yy, xx = np.unravel_index(np.argmax(dt), dt.shape)
    t = str(num[i]); cv2.circle(out, (int(xx), int(yy)), 30, (255, 255, 255), -1); cv2.putText(out, t, (int(xx) - 11 * len(t), int(yy) + 12), 0, 1.1, (0, 0, 0), 3)
NM = next((json.load(open(f[6:])) for f in sys.argv[5:] if f.startswith("names:")), None)
if NM:
    side = np.zeros((H, 1100, 3), np.uint8)
    for j, (v, t) in enumerate(sorted(NM.items(), key=lambda kv: int(kv[0]))):
        y = 70 + 75 * j; cv2.rectangle(side, (30, y - 30), (90, y + 15), tuple(int(c) for c in pal.get(int(v), (90, 90, 90))), -1)
        cv2.putText(side, "%s  %s" % (v, t), (110, y + 8), 0, 1.15, (235, 235, 235), 3, cv2.LINE_AA)
    out = np.hstack([out, side])
np.save(f"{OP}_zone.npy", z); cv2.imwrite(f"{OP}_zone_numerotate.png", cv2.resize(out, None, fx=0.5, fy=0.5)); print("FACES", len(faces), "NUMBERS", k)
