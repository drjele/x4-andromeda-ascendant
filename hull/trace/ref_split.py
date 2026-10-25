# Outlines of a view taken from the reference itself: the ship is everything that is not the black background, its
# borders (outer and holes) traced and smoothed; the user's drawn lines are kept only where they run inside the
# ship, away from the black, as the borders between parts that overlap there. One half (above the centreline) is
# built and mirrored.
# Usage: python ref_split.py <dir> <view> <drawn_network.json> <gray> <out.png>
import sys, json, numpy as np, cv2
from scipy.ndimage import distance_transform_edt
D, VIEW, NET, T, OUT = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]; R = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"; K = 4
ref = cv2.resize(cv2.imread(f"{R}/{VIEW}.png"), None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC); H, W = ref.shape[:2]
g = cv2.GaussianBlur(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), (5, 5), 0)
# the background is one flat grey: black = dark AND flat (local std small), so dark shading on the hull stays ship
g0 = cv2.cvtColor(cv2.imread(f"{R}/{VIEW}.png"), cv2.COLOR_BGR2GRAY).astype(np.float32)
mu = cv2.blur(g0, (5, 5)); sd = np.sqrt(np.maximum(cv2.blur(g0 * g0, (5, 5)) - mu * mu, 0))
bg = ((mu <= T) & (sd <= 3.0)).astype(np.uint8); nb, lb, sb, _ = cv2.connectedComponentsWithStats(bg, connectivity=4)
h0, w0 = g0.shape; keep = np.zeros(nb, bool)
for i in range(1, nb):
    x, y, w, h, a_ = sb[i]; keep[i] = (x == 0 or y == 0 or x + w == w0 or y + h == h0) or a_ > 300
bg = keep[lb].astype(np.uint8); ship = cv2.resize(1 - bg, (W, H), interpolation=cv2.INTER_LINEAR)
if len(sys.argv) > 7:                                                      # flat dark patches inside the drawn body outline are hull, not holes
    red = np.vstack([np.array(c) for c in json.load(open(sys.argv[7]))]); body = np.zeros((H, W), np.uint8)
    cv2.fillPoly(body, [cv2.convexHull(np.round(red).astype(np.int32))], 1)
    nh, lh, sh, _ = cv2.connectedComponentsWithStats((1 - ship).astype(np.uint8), connectivity=4)
    for i in range(1, nh):
        x, y, w, h, a_ = sh[i]
        if not (x == 0 or y == 0 or x + w == W or y + h == H) and body[lh == i].mean() > 0.6: ship[lh == i] = 1
ship = (cv2.GaussianBlur(ship.astype(np.float32), (0, 0), 7) > 0.5).astype(np.uint8)   # organic, even borders
sil = ship > 0; best = None; rows = np.nonzero(sil.any(1))[0]
for a2 in range(2 * rows.min() + 20, 2 * rows.max() - 20, 2):
    idx = a2 - np.arange(H); ok = (idx >= 0) & (idx < H); f = np.zeros_like(sil); f[ok] = sil[idx[ok]]
    sc = (f & sil).sum() / max((f | sil).sum(), 1)
    if best is None or sc > best[0]: best = (sc, a2)
AX = float(sys.argv[6]) if len(sys.argv) > 6 else best[1] / 2; half = ship.copy(); half[int(np.ceil(AX)):] = 0
cs, hi = cv2.findContours(half, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
s = 4; kk = np.exp(-0.5 * (np.arange(-3 * s, 3 * s + 1) / s) ** 2); kk /= kk.sum()
sm = lambda c: np.stack([np.convolve(np.r_[c[-3 * s:, i], c[:, i], c[:3 * s, i]], kk, "valid") for i in (0, 1)], 1)
outl = [sm(c[:, 0, :].astype(float)) for c in cs if cv2.contourArea(c) > 300]
def off_axis(c):                                                          # the cut along the axis is not a border: split the outline there
    keep = np.abs(c[:, 1] - AX) > 3; runs = np.split(np.arange(len(c)), np.where(np.diff(keep.astype(int)) != 0)[0] + 1)
    return [c[r] for r in runs if keep[r[0]] and len(r) > 5]
outl = [p for c in outl for p in off_axis(c)]
# the user's lines inside the ship, away from its borders: the overlaps between parts
dist = distance_transform_edt(ship); inner = []
for c in json.load(open(NET)):
    c = np.array(c); c = c[c[:, 1] < AX]
    if len(c) < 5: continue
    xi = np.clip(np.round(c[:, 0]).astype(int), 0, W - 1); yi = np.clip(np.round(c[:, 1]).astype(int), 0, H - 1); inside = dist[yi, xi] > 22
    for run in np.split(np.arange(len(c)), np.where(np.diff(inside.astype(int)) != 0)[0] + 1):
        if inside[run[0]] and np.hypot(*np.diff(c[run], axis=0).T).sum() > 80: inner.append(c[run])
mir = lambda c: np.stack([c[:, 0], 2 * AX - c[:, 1]], 1)
out = (ref * 0.75).astype(np.uint8); cv2.line(out, (0, int(AX)), (W, int(AX)), (255, 255, 0), 1)
for c in outl: cv2.polylines(out, [np.round(c).astype(np.int32), np.round(mir(c)).astype(np.int32)], False, (0, 255, 0), 5, cv2.LINE_AA)
for c in inner: cv2.polylines(out, [np.round(c).astype(np.int32), np.round(mir(c)).astype(np.int32)], False, (0, 200, 255), 5, cv2.LINE_AA)
json.dump({"axis": AX, "outlines": [c.tolist() for c in outl], "inner": [c.tolist() for c in inner]}, open(f"{D}/{VIEW}_ref_split.json", "w"))
cv2.imwrite(OUT, cv2.resize(out, None, fx=0.5, fy=0.5)); print("REF SPLIT axis %.1f, %d outlines from the reference, %d inner lines from the drawing" % (AX, len(outl), len(inner)))
