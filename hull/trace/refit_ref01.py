# Refit our ortho renders onto the ref-01 views, trying each view as is and mirrored left-right (the earlier fit never
# tried the mirror, and the top/bottom views came out front-to-back). Writes trace/fit_ref01.json: scale/offset + flip.
import json, numpy as np, cv2
from scipy.optimize import minimize
R = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"; O = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/view/ref01"
spec = json.load(open(f"{O}/views.json")); fit = {}
def bbox(m): ys, xs = np.nonzero(m); return xs.min(), xs.max(), ys.min(), ys.max()
for view in spec:
    ref = cv2.imread(f"{R}/{view}_mask.png", 0) > 127; k = spec[view]["rot"]; size = (ref.shape[1], ref.shape[0]); best = None
    for flip in (False, True):
        m = cv2.imread(f"{O}/{view}_mask.png", cv2.IMREAD_UNCHANGED)[:, :, 3] > 127; m = np.rot90(m, k) if k else m
        if flip: m = m[:, ::-1]
        rx0, rx1, ry0, ry1 = bbox(ref); ox0, ox1, oy0, oy1 = bbox(m); mf = m.astype(np.float32)
        s = min((rx1 - rx0) / (ox1 - ox0), (ry1 - ry0) / (oy1 - oy0)); p0 = [s, s, (rx0 + rx1) / 2 - s * (ox0 + ox1) / 2, (ry0 + ry1) / 2 - s * (oy0 + oy1) / 2]
        def loss(p):
            w = cv2.warpAffine(mf, np.float32([[p[0], 0, p[2]], [0, p[1], p[3]]]), size) > 0.5; return -(w & ref).sum() / max((w | ref).sum(), 1)
        r = min((minimize(loss, [p0[0] * a, p0[1] * b, p0[2], p0[3]], method="Nelder-Mead", options={"xatol": 0.05, "fatol": 1e-4, "maxiter": 800}) for a in (0.9, 1.0, 1.1) for b in (0.9, 1.0, 1.1)), key=lambda r: r.fun)
        print(view, "flip" if flip else "as is", round(-r.fun, 3))
        if best is None or r.fun < best[0]: best = (r.fun, flip, r.x)
    fit[view] = {"p": [float(v) for v in best[2]], "flip": best[1], "iou": round(-float(best[0]), 3)}
json.dump(fit, open("/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/trace/fit_ref01.json", "w"), indent=1); print(json.dumps(fit))
