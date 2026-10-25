# Fit the arm path and its strap sizes onto the user's arm outlines: each control point of the (right) arm is moved
# onto the centre line of the outline, from above for x/y and from the side for y/z, only where that centre line runs
# the same way as the arm (so crossings and the lower wing merged into the arm outline do not pull it), and the strap
# width/height are read from the outline's local width where the outline is a plain strap. Changes are relaxed along
# the loop so the path stays laminar. Writes a candidate a_params and a check sheet.
# Usage: python arm_fit.py <drawings_dir> <a_params.json> <out_params.json> <sheet.png>
import sys, json, numpy as np, cv2
from scipy.ndimage import distance_transform_edt
from skimage.morphology import skeletonize
sys.path.insert(0, "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/arms"); from a_frame import member
D, SRC, OUT, SHEET = sys.argv[1:5]; H = np.load(f"{D}/hull.npz"); P = json.load(open(SRC)); VOX = 5.0
gx = np.arange(-1100, 1100 + VOX / 2, VOX); gy = np.arange(-1500, 1500 + VOX / 2, VOX); gz = np.arange(-500, 500 + VOX / 2, VOX)
REACH, ALIGN, MAXMOVE = 55.0, 0.8, 60.0
def centre_lines(mask, ca, cb):
    sk = skeletonize(mask); dt = distance_transform_edt(mask) * VOX; pts = np.argwhere(sk)
    # local direction of the centre line from its neighbours (principal axis within 4 cells)
    dirs = np.zeros((len(pts), 2))
    for n, p in enumerate(pts):
        q = pts[np.abs(pts - p).max(1) <= 4] - p
        if len(q) > 2: dirs[n] = np.linalg.svd(q - q.mean(0))[2][0]
    return np.stack([ca[pts[:, 0]], cb[pts[:, 1]]], 1), dirs, 2 * dt[pts[:, 0], pts[:, 1]]
def snap(p2, t2, lines):
    xy, dirs, width = lines; d = np.linalg.norm(xy - p2, axis=1); tn = np.linalg.norm(t2)
    if tn < 0.5: return None                            # the arm runs across this view: it says nothing here
    ok = (d < REACH) & (np.abs(dirs @ (t2 / tn)) > ALIGN)
    if not ok.any(): return None
    k = np.argmin(np.where(ok, d, np.inf)); return xy[k], width[k]
arm = P["members"]["arm"]; ctrl = np.array(arm["path"], float); n = len(ctrl)
C, f, W, Hh, R = member(arm, 10); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
right = lambda m: m & (gx[:, None] > 0) if m.shape[0] == len(gx) else m
top = centre_lines(right(H["arms_top"]), gx, gy); side = centre_lines(H["arms_side"], gy, gz)
moves = np.full((n, 3), np.nan); meas_w = np.full(n, np.nan); meas_h = np.full(n, np.nan)
for i, p in enumerate(ctrl):
    j = np.argmin(np.linalg.norm(C - p, axis=1)); t = C[min(j + 2, len(C) - 1)] - C[max(j - 2, 0)]; t /= np.linalg.norm(t)
    a = snap(p[[0, 1]], t[[0, 1]], top); b = snap(p[[1, 2]], t[[1, 2]], side)
    w_now = np.interp(f[j], [r[0] for r in arm["sections"]], [r[1] for r in arm["sections"]])
    h_now = np.interp(f[j], [r[0] for r in arm["sections"]], [r[2] for r in arm["sections"]])
    if a is not None:
        moves[i, 0], moves[i, 1] = a[0] - p[[0, 1]]
        if a[1] < 1.6 * w_now: meas_w[i] = a[1]     # wider than a strap: the lower wing is merged in, not the arm
    if b is not None:
        moves[i, 2] = b[0][1] - p[2]; moves[i, 1] = np.nanmean([moves[i, 1], b[0][0] - p[1]])
        if b[1] < 1.6 * h_now: meas_h[i] = b[1]
def relax(v, sigma=1.5):
    # missing moves become 0, then a circular Gaussian over the closed loop of control points
    v = np.where(np.isnan(v), 0, v); r = int(3 * sigma) + 1; k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    return np.convolve(np.r_[v[-r:], v, v[:r]], k, "valid")
mv = np.stack([relax(moves[:, c]) for c in range(3)], 1); norm = np.linalg.norm(mv, axis=1, keepdims=True)
mv = mv * np.minimum(1, MAXMOVE / np.maximum(norm, 1e-6)); new = ctrl + mv; new[-1] = new[0]   # the loop stays closed
# strap sizes: the measured width/height scale each section by the ratio at the nearest control points
cf = np.array([f[np.argmin(np.linalg.norm(C - p, axis=1))] for p in ctrl])
def ratio(meas, col):
    now = np.array([np.interp(x, [r[0] for r in arm["sections"]], [r[col] for r in arm["sections"]]) for x in cf]); q = meas / now
    q = np.where(np.isnan(q), 1, np.clip(q, 0.7, 1.4)); return relax(q - 1) + 1
qw, qh = ratio(meas_w, 1), ratio(meas_h, 2)
sections = [[r[0], round(r[1] * float(np.interp(r[0], cf[np.argsort(cf)], qw[np.argsort(cf)])), 1), round(r[2] * float(np.interp(r[0], cf[np.argsort(cf)], qh[np.argsort(cf)])), 1)] + list(r[3:]) for r in arm["sections"]]
P2 = json.loads(json.dumps(P)); P2["members"]["arm"]["path"] = np.round(new).astype(int).tolist(); P2["members"]["arm"]["sections"] = sections
json.dump(P2, open(OUT, "w"))
print("ARM FIT moved %d/%d control points from above, %d from the side; max move %.0f m, mean %.0f m" % ((~np.isnan(moves[:, 0])).sum(), n, (~np.isnan(moves[:, 2])).sum(), np.linalg.norm(mv, axis=1).max(), np.linalg.norm(mv, axis=1).mean()))
print("width x%.2f..%.2f (%d measured), height x%.2f..%.2f (%d measured)" % (qw.min(), qw.max(), (~np.isnan(meas_w)).sum(), qh.min(), qh.max(), (~np.isnan(meas_h)).sum()))
# check sheet: the arm outline from above and from the side, the old path (blue) and the new one (red)
C2, *_ = member(P2["members"]["arm"], 10); rows = []
for mask, ca, cb, ax in ((right(H["arms_top"]), gx, gy, (0, 1)), (H["arms_side"], gy, gz, (1, 2))):
    im = np.where(mask.T[::-1, :, None], 90, 25).astype(np.uint8).repeat(3, 2); im = cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    def px(p): return np.stack([(p[:, 0] - ca[0]) / VOX * 2, (cb[-1] - p[:, 1]) / VOX * 2], 1).astype(np.int32)
    cv2.polylines(im, [px(C[:, ax])], False, (255, 140, 40), 3); cv2.polylines(im, [px(C2[:, ax])], False, (40, 40, 255), 3)
    for p, q in zip(px(ctrl[:, ax]), px(new[:, ax])): cv2.line(im, tuple(p), tuple(q), (0, 230, 255), 2)
    ys, xs = np.nonzero(im.max(2) > 25); rows.append(im[max(ys.min() - 20, 0):ys.max() + 20, max(xs.min() - 20, 0):xs.max() + 20])
W2 = max(r.shape[1] for r in rows); cv2.imwrite(SHEET, np.vstack([np.pad(r, ((0, 10), (0, W2 - r.shape[1]), (0, 0))) for r in rows]))
