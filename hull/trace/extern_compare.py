# An external 3D model (triangles, any axes) projected orthographically and laid over every confirmed view silhouette
# on the multi-view drawing: the model's axes found from its extents (length > width > height) and the sign/flip of
# each searched per view; scale and shift fitted on the silhouette (IoU); overlay sheets (grey = both, magenta = only
# the model, yellow = only our contours) and the IoU per view. With "--also" a second view of the same axis pair is
# compared against the same projection, which shows which of the two opposite drawings the model agrees with.
# Usage: python extern_compare.py <model.npz> <layout.json> <vederi.json> <views.json> <out_dir> <tag>
#   views.json: {"top": spec, "bottom": spec, "back": spec, "front": spec, "side": spec}  (calibrate.py specs; side: {"faces": path})
import sys, json, os, numpy as np, cv2
MZ, LJ, VJ, SJ, OD, TAG = sys.argv[1:7]; z = np.load(MZ); LAY = json.load(open(LJ)); VIEWS = json.load(open(VJ)); SP = json.load(open(SJ)); os.makedirs(OD, exist_ok=True)
Wc, Hc = LAY["size"]; AFF = {k: np.array(v, float) for k, v in LAY["aff"].items()}
TR = np.concatenate([z[k][z["t" + k[1:]]] for k in z.files if k.startswith("v|")])
c = TR.reshape(-1, 3); ext = np.ptp(c, 0); order = np.argsort(-ext)                 # length, width, height axes of the model
L, Wd, Hh = order; print(TAG, "extents", ext.round(2), "-> length axis", "xyz"[L], "width", "xyz"[Wd], "height", "xyz"[Hh], "L/W %.2f L/H %.2f W/H %.2f" % (ext[L] / ext[Wd], ext[L] / ext[Hh], ext[Wd] / ext[Hh]))
def sil(spec, key):
    if "faces" in spec:
        F = json.load(open(spec["faces"])); m = np.zeros(spec.get("size", [860, 3260]), np.uint8)
        for t in F:
            for f in F[t]:
                cv2.fillPoly(m, [np.round(np.array(f["outer"])).astype(np.int32)], 1)
                for h in f.get("holes", []): cv2.fillPoly(m, [np.round(np.array(h)).astype(np.int32)], 0)
        m = m > 0
    elif "zone" in spec:
        zz = np.load(spec["zone"]); nm = json.load(open(spec["names"])); g = [int(k) for k, t in nm.items() if t.startswith("G")]; m = (zz > 0) & ~np.isin(zz, g)
    else: zz = np.load(spec["npz"]); m = np.any([zz[t] for t in zz.files], 0)
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return cv2.warpAffine(m, AFF[key], (Wc, Hc), flags=cv2.INTER_NEAREST) > 0
# canvas axes per view: (canvas-x axis, canvas-y axis) as model axes; top/bottom: width across, length down; side: height across, length down; back/front: width across, height down
AX = {"top": (Wd, L), "bottom": (Wd, L), "side": (Hh, L), "back": (Wd, Hh), "front": (Wd, Hh)}
def raster(ax, sx, sy, shape, box):
    u = TR[:, :, ax[0]] * sx; v = TR[:, :, ax[1]] * sy; x0, y0, x1, y1 = box
    k = min((x1 - x0) / np.ptp(u), (y1 - y0) / np.ptp(v)) if False else None
    return u, v
res = {}
PROJ = {}
def proj(ax, R=1600):                                                      # the model's silhouette on one axis pair, rasterised once
    if ax in PROJ: return PROJ[ax]
    u = TR[:, :, ax[0]]; v = TR[:, :, ax[1]]; k = (R - 20) / max(np.ptp(u), np.ptp(v))
    m = np.zeros((int(np.ptp(v) * k) + 20, int(np.ptp(u) * k) + 20), np.uint8)
    cv2.fillPoly(m, list(np.round(np.stack([(u - u.min()) * k + 10, (v - v.min()) * k + 10], 2)).astype(np.int32)), 1)
    ys, xs = np.nonzero(m); PROJ[ax] = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; return PROJ[ax]
def place(img, box, kx, ky):
    x0, y0, x1, y1 = box; w, h = (x1 - x0) * kx, (y1 - y0) * ky; out = np.zeros((Hc, Wc), np.uint8)
    r = cv2.resize(img, (max(int(w), 1), max(int(h), 1)), interpolation=cv2.INTER_NEAREST); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    X0, Y0 = int(round(cx - r.shape[1] / 2)), int(round(cy - r.shape[0] / 2)); X1, Y1 = X0 + r.shape[1], Y0 + r.shape[0]
    a0, b0 = max(X0, 0), max(Y0, 0); a1, b1 = min(X1, Wc), min(Y1, Hc); out[b0:b1, a0:a1] = r[b0 - Y0:b1 - Y0, a0 - X0:a1 - X0]; return out > 0
for key, spec in SP.items():
    S = sil(spec, key); ys, xs = np.nonzero(S); box = (xs.min(), ys.min(), xs.max(), ys.max()); P0 = proj(AX[key]); best = None
    for fx in (False, True):
        for fy in (False, True):
            P = P0[::-1 if fy else 1, ::-1 if fx else 1]
            for kx in np.linspace(0.9, 1.1, 9):
                for ky in np.linspace(0.9, 1.1, 9):
                    M = place(P, box, kx, ky); iou = (M & S).sum() / max((M | S).sum(), 1)
                    if best is None or iou > best[0]: best = (iou, fx, fy, kx, ky, M)
    iou, fx, fy, kx, ky, M = best
    y0, y1, x0, x1 = box[1], box[3], box[0], box[2]
    b0, b1, a0, a1 = max(y0 - 60, 0), min(y1 + 60, Hc), max(x0 - 60, 0), min(x1 + 60, Wc)
    img = np.full((b1 - b0, a1 - a0, 3), 18, np.uint8); s_, m_ = S[b0:b1, a0:a1], M[b0:b1, a0:a1]
    img[s_ & m_] = (90, 90, 90); img[m_ & ~s_] = (255, 90, 255); img[s_ & ~m_] = (0, 210, 255)
    cv2.putText(img, "%s %s: mov = doar modelul, galben = doar contururile noastre; IoU %.3f; scara %.2f/%.2f" % (TAG, key, iou, kx, ky), (10, 36), 0, 1.0, (235, 235, 235), 2, cv2.LINE_AA)
    cv2.imwrite(f"{OD}/{TAG}_{key}.png", cv2.resize(img, None, fx=0.5, fy=0.5)); res[key] = round(float(iou), 3)
    print(TAG, key, "IoU %.3f" % iou, "flip %s/%s scale %.2f/%.2f" % (fx, fy, kx, ky), flush=True)
json.dump(res, open(f"{OD}/{TAG}_iou.json", "w"), indent=1)
