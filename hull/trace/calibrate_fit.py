# Global calibration of opposite views before any local change: the second view's silhouette scaled (separately across
# and along/up) and shifted along the non-symmetric axis around its centreline, to best match the first view's
# silhouette (IoU on a reduced grid, coarse then fine). Prints the best scale/shift and the IoU before/after, writes the
# overlay after the fit with the remaining differences numbered (same colours as calibrate.py).
# Usage: python calibrate_fit.py <layout.json> <vederi.json> <pairs.json> <out_dir>
import sys, json, os, numpy as np, cv2
from scipy.ndimage import label, distance_transform_edt
LJ, VJ, PJ, OD = sys.argv[1:5]; LAY = json.load(open(LJ)); VIEWS = json.load(open(VJ)); PAIRS = json.load(open(PJ))
Wc, Hc = LAY["size"]; AFF = {k: np.array(v, float) for k, v in LAY["aff"].items()}
def centre(key): A = AFF[key]; ax = VIEWS[key]["axis"]; return A[0, 0] * ax + A[0, 2] if key in ("back", "front") else A[0, 1] * ax + A[0, 2]
def sil(spec):
    if "zone" in spec:
        z = np.load(spec["zone"]); nm = json.load(open(spec["names"])); gaps = [int(k) for k, t in nm.items() if t.startswith("G")]
        m = (z > 0) & ~np.isin(z, gaps)
    else: z = np.load(spec["npz"]); m = np.any([z[t] for t in z.files], 0)
    return cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0             # the zone border lines closed
def canvas(key, m):
    w = cv2.warpAffine(m.astype(np.uint8), AFF[key], (Wc, Hc), flags=cv2.INTER_NEAREST) > 0
    cx = centre(key); i = np.arange(Wc); src = np.clip(np.where(i <= cx, i, np.round(2 * cx - i).astype(int)), 0, Wc - 1); w = w[:, src]
    return np.roll(w, int(round(Wc / 2 - cx)), 1)                           # centreline at the middle column
res = {}
for P in PAIRS:
    ka, sa = P["a"]; kb, sb = P["b"]; A = canvas(ka, sil(sa)); B = canvas(kb, sil(sb))
    if P.get("rows_max_of"):
        cut = np.nonzero(A.any(1))[0].max() - P.get("margin", 30)
    else: cut = Hc
    q = 4; a = cv2.resize(A.astype(np.uint8), (Wc // q, Hc // q), interpolation=cv2.INTER_AREA) > 0
    b0 = cv2.resize(B.astype(np.uint8), (Wc // q, Hc // q), interpolation=cv2.INTER_AREA) > 0; cq = cut // q
    ya = np.nonzero(a.any(1))[0]; yb = np.nonzero(b0.any(1))[0]; cy_b = (yb.min() + yb.max()) / 2
    def warp(m, sx, sy, ty, shape, cyb, cx):
        M = np.float32([[sx, 0, cx - sx * cx], [0, sy, cyb - sy * cyb + ty]]); return cv2.warpAffine(m.astype(np.uint8), M, shape[::-1], flags=cv2.INTER_NEAREST) > 0
    def score(m):
        aa, mm = a[:cq], m[:cq]; return (aa & mm).sum() / max((aa | mm).sum(), 1)
    cx = a.shape[1] / 2; best = (score(b0), 1.0, 1.0, 0.0); before = best[0]
    for rng_s, rng_t, steps in ((0.15, 60, 7), (0.04, 12, 5), (0.01, 3, 5)):
        _, bsx, bsy, bty = best
        for sx in bsx + np.linspace(-rng_s, rng_s, steps):
            for sy in bsy + np.linspace(-rng_s, rng_s, steps):
                for ty in bty + np.linspace(-rng_t, rng_t, steps):
                    v = score(warp(b0, sx, sy, ty, a.shape, cy_b, cx))
                    if v > best[0]: best = (v, sx, sy, ty)
    v, sx, sy, ty = best
    Bf = warp(B, sx, sy, ty * q, A.shape, cy_b * q, Wc / 2); A2, B2 = A.copy(), Bf.copy(); A2[cut:] = False; B2[cut:] = False
    rows = np.nonzero((A2 | B2).any(1))[0]; cols = np.nonzero((A2 | B2).any(0))[0]
    y0, y1, x0, x1 = rows.min() - 40, rows.max() + 40, cols.min() - 40, cols.max() + 40; aa, bb = A2[y0:y1, x0:x1], B2[y0:y1, x0:x1]
    img = np.full(aa.shape + (3,), 18, np.uint8); img[aa & bb] = (90, 90, 90); img[aa & ~bb] = (0, 210, 255); img[bb & ~aa] = (80, 220, 80)
    half = (cols.max() - cols.min()) / 2; diffs = []
    for m_, who in ((aa & ~bb, ka), (bb & ~aa, kb)):
        lab, n = label(m_)
        for i in range(1, n + 1):
            r = lab == i; w = 2 * distance_transform_edt(r).max(); ys, xs = np.nonzero(r)
            if r.sum() < 600 or w < 8 or x0 + xs.mean() > Wc / 2 + 2: continue
            diffs.append((ys.mean(), xs.mean(), w, who))
    diffs.sort(); nm = {"top": "SUS", "bottom": "JOS", "front": "FATA", "back": "SPATE"}; out = []
    for k, (y, x, w, who) in enumerate(diffs, 1):
        cv2.circle(img, (int(x), int(y)), 26, (255, 255, 255), -1); t = str(k); cv2.putText(img, t, (int(x) - 10 * len(t), int(y) + 10), 0, 0.95, (0, 0, 0), 3)
        out.append({"n": k, "only_in": nm[who], "width_pct_half": round(100 * w / half, 1)})
    cv2.putText(img, "dupa potrivire: galben = doar %s, verde = doar %s; IoU %.3f (inainte %.3f)" % (nm[ka], nm[kb], v, before), (20, 40), 0, 1.0, (235, 235, 235), 2, cv2.LINE_AA)
    cv2.imwrite(f"{OD}/{P['name']}_potrivit.png", cv2.resize(img, None, fx=0.6, fy=0.6))
    res[P["name"]] = {"scale_across": round(float(sx), 3), "scale_along": round(float(sy), 3), "shift_along_px": round(float(ty * q), 1), "iou_before": round(float(before), 3), "iou_after": round(float(v), 3), "diffs": out}
    print(P["name"], json.dumps({k: v_ for k, v_ in res[P["name"]].items() if k != "diffs"}), "; ".join("%d:%s %.1f%%" % (d["n"], d["only_in"], d["width_pct_half"]) for d in out))
json.dump(res, open(f"{OD}/potrivire_globala.json", "w"), indent=1)
