# One zone that holds several parts (the arms in the side and bottom views) split by short proposed cuts: the zone's
# mask (from yesterday's faces or zone map) cut along the segments (mirrored over the centreline when the view is
# symmetric), the pieces numbered, filled and named from a names file, the cuts dashed magenta T1, T2... Writes the
# piece map (<prefix>_zone.npy) and <prefix>_zone_numerotate.png for the user to confirm by number.
# Usage: python mask_split.py <ref.png> <faces.json|zones.npz> <zone name> <cuts.json> <axis|-> <h|v|-> <out_prefix> [names.json]
import sys, json, numpy as np, cv2
from scipy.ndimage import label
REF, SRC, ZN, CJ, AX, AD, OP = sys.argv[1:8]; NM = json.load(open(sys.argv[8])) if len(sys.argv) > 8 else {}
ref = cv2.imread(REF); H, W = ref.shape[:2]
if SRC.endswith(".npz"): m = np.load(SRC)[ZN].astype(np.uint8)
else:
    m = np.zeros((H, W), np.uint8)
    for f in json.load(open(SRC))[ZN]:
        cv2.fillPoly(m, [np.round(np.array(f["outer"])).astype(np.int32)], 1)
        for h in f.get("holes", []): cv2.fillPoly(m, [np.round(np.array(h)).astype(np.int32)], 0)
CUTS = json.load(open(CJ)); segs = []
for x1, y1, x2, y2 in CUTS:
    segs.append((x1, y1, x2, y2))
    if AX != "-":
        a = float(AX); segs.append((x1, 2 * a - y1, x2, 2 * a - y2) if AD == "h" else (2 * a - x1, y1, 2 * a - x2, y2))
cut = np.zeros_like(m)
for x1, y1, x2, y2 in segs: cv2.line(cut, (int(x1), int(y1)), (int(x2), int(y2)), 1, 7)
lab, n = label((m > 0) & (cut == 0)); info = []
for i in range(1, n + 1):
    ys, xs = np.nonzero(lab == i)
    if len(xs) > 800: info.append((i, xs.mean(), ys.mean()))
num = {}; k = 0
for i, x, y in sorted(info, key=lambda t: (round(t[2] / 150), t[1])):
    if i in num: continue
    k += 1; num[i] = k
    if AX != "-":
        a = float(AX); tx, ty = (x, 2 * a - y) if AD == "h" else (2 * a - x, y)
        j = min(info, key=lambda t: np.hypot(t[1] - tx, t[2] - ty))
        if j[0] != i and np.hypot(j[1] - tx, j[2] - ty) < 80: num[j[0]] = k
rng = np.random.default_rng(7); pal = {v: rng.integers(70, 255, 3) for v in set(num.values())}
out = (ref * 0.5).astype(np.uint8); z = np.zeros((H, W), np.int32)
for i, v in num.items(): mm = lab == i; out[mm] = (out[mm] * 0.35 + pal[v] * 0.65).astype(np.uint8); z[mm] = v
for t_, (x1, y1, x2, y2) in enumerate(segs):
    P = np.linspace([x1, y1], [x2, y2], 16)
    for t in range(0, 15, 2): cv2.line(out, tuple(np.round(P[t]).astype(int)), tuple(np.round(P[t + 1]).astype(int)), (255, 0, 255), 9)
for c, (x1, y1, x2, y2) in enumerate(CUTS, 1): cv2.putText(out, "T%d" % c, (int(x2) + 12, int(y2) + 12), 0, 1.3, (255, 0, 255), 4)
for i, x, y in info:
    mm = (lab == i).astype(np.uint8); dt = cv2.distanceTransform(mm, cv2.DIST_L2, 5); yy, xx = np.unravel_index(np.argmax(dt), dt.shape); t = str(num[i])
    cv2.circle(out, (int(xx), int(yy)), 28, (255, 255, 255), -1); cv2.putText(out, t, (int(xx) - 11 * len(t), int(yy) + 11), 0, 1.0, (0, 0, 0), 3)
if NM:
    side = np.zeros((H, 1000, 3), np.uint8)
    for j, (v, t) in enumerate(sorted(NM.items(), key=lambda kv: int(kv[0]))):
        y = 70 + 72 * j; cv2.rectangle(side, (30, y - 30), (90, y + 15), tuple(int(c) for c in pal.get(int(v), (90, 90, 90))), -1)
        cv2.putText(side, "%s  %s" % (v, t), (110, y + 8), 0, 1.1, (235, 235, 235), 2, cv2.LINE_AA)
    out = np.hstack([out, side])
np.save(f"{OP}_zone.npy", z); cv2.imwrite(f"{OP}_zone_numerotate.png", cv2.resize(out, None, fx=0.5, fy=0.5)); print("PIECES", k)
