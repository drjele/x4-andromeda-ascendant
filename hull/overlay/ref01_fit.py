# Fit our orthographic renders onto the ref-01 views: per view a scale pair and an offset (ours -> ref pixels)
# that maximise the silhouette overlap, started from the bounding boxes; writes ref01/fit.json.
import json, numpy as np, cv2
from scipy.optimize import minimize
R = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"; O = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/view/ref01"
spec = json.load(open(f"{O}/views.json")); fit = {}
def ours(view, tag):
    im = cv2.imread(f"{O}/{view}_{tag}.png", cv2.IMREAD_UNCHANGED); k = spec[view]["rot"]
    return np.rot90(im, k) if k else im
def bbox(m): ys, xs = np.nonzero(m); return xs.min(), xs.max(), ys.min(), ys.max()
def warp(m, p, size):
    sx, sy, tx, ty = p; A = np.float32([[sx, 0, tx], [0, sy, ty]]); return cv2.warpAffine(m, A, size, flags=cv2.INTER_LINEAR)
for view in spec:
    ref = cv2.imread(f"{R}/{view}_mask.png", 0) > 127; m = ours(view, "mask")[:, :, 3] > 127
    rx0, rx1, ry0, ry1 = bbox(ref); ox0, ox1, oy0, oy1 = bbox(m)
    s = min((rx1 - rx0) / (ox1 - ox0), (ry1 - ry0) / (oy1 - oy0)); p0 = [s, s, (rx0 + rx1) / 2 - s * (ox0 + ox1) / 2, (ry0 + ry1) / 2 - s * (oy0 + oy1) / 2]
    mf = m.astype(np.float32); size = (ref.shape[1], ref.shape[0])
    def loss(p):
        w = warp(mf, p, size) > 0.5; return -(w & ref).sum() / max((w | ref).sum(), 1)
    best = min((minimize(loss, [p0[0] * a, p0[1] * b, p0[2], p0[3]], method="Nelder-Mead", options={"xatol": 0.05, "fatol": 1e-4, "maxiter": 600}) for a in (0.9, 1.0, 1.1) for b in (0.9, 1.0, 1.1)), key=lambda r: r.fun)
    fit[view] = {"p": [float(v) for v in best.x], "iou": round(-float(best.fun), 3)}; print(view, fit[view])
json.dump(fit, open(f"{R}/fit.json", "w"), indent=1)
