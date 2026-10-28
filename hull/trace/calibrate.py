# Calibration of opposite views: in orthographic views the outer silhouette and the through-holes seen from +Z and -Z
# (and from +Y and -Y) must coincide. Each view's silhouette = its confirmed zones minus the ones named as gaps (G),
# brought onto the multi-view drawing (multiview.py layout), the opposite view moved onto it by its centreline (same
# rows for top/bottom: the shared length; same height origin for front/back), compared: grey = both, yellow = only
# the first view, green = only the second; every difference larger than a few px numbered with its width (px on the
# drawing and % of the half width). A view cut by its frame is compared only above the cut (front).
# Usage: python calibrate.py <layout.json> <vederi.json> <pairs.json> <out_dir>
#   pairs.json: [{"name": "sus_jos", "a": ["top", spec], "b": ["bottom", spec], "rows_max": null}, ...]
#   spec: {"zone": npy, "names": json, "gaps": [names]} | {"npz": path, "take": [names]}
import sys, json, os, numpy as np, cv2
from scipy.ndimage import label, distance_transform_edt
LJ, VJ, PJ, OD = sys.argv[1:5]; LAY = json.load(open(LJ)); VIEWS = json.load(open(VJ)); PAIRS = json.load(open(PJ)); os.makedirs(OD, exist_ok=True)
Wc, Hc = LAY["size"]; AFF = {k: np.array(v, float) for k, v in LAY["aff"].items()}
def sil(spec):
    if "zone" in spec:
        z = np.load(spec["zone"]); nm = json.load(open(spec["names"])); gaps = [int(k) for k, t in nm.items() if t in spec.get("gaps", []) or t.startswith("G")]
        return (z > 0) & ~np.isin(z, gaps)
    z = np.load(spec["npz"]); return np.any([z[t] for t in (spec.get("take") or z.files)], 0)
def centre(key): A = AFF[key]; ax = VIEWS[key]["axis"]; return A[0, 0] * ax + A[0, 2] if key in ("back", "front") else A[0, 1] * ax + A[0, 2]
def to_canvas(key, m): return cv2.warpAffine(m.astype(np.uint8), AFF[key], (Wc, Hc), flags=cv2.INTER_NEAREST) > 0
def mirror(m, cx): i = np.arange(Wc); src = np.clip(np.where(i <= cx, i, np.round(2 * cx - i).astype(int)), 0, Wc - 1); return m[:, src]
report = {}
for P in PAIRS:
    ka, sa = P["a"]; kb, sb = P["b"]
    A = mirror(to_canvas(ka, sil(sa)), centre(ka)); B = mirror(to_canvas(kb, sil(sb)), centre(kb))
    # bring B onto A: same centre column; rows: top/bottom share the length rows, front/back aligned on the top edge
    dx = int(round(centre(ka) - centre(kb)))
    ya = np.nonzero(A.any(1))[0]; yb = np.nonzero(B.any(1))[0]; dy = 0 if ka in ("top", "bottom") else int(ya.min() - yb.min())
    B = np.roll(np.roll(B, dx, 1), dy, 0)
    if P.get("rows_max_of"):                                               # a view cut by its frame: compare only down to its cut
        cut = np.nonzero((A if P["rows_max_of"] == "a" else B).any(1))[0].max() - P.get("margin", 30)
        A[cut:] = False; B[cut:] = False
    rows = np.nonzero((A | B).any(1))[0]; cols = np.nonzero((A | B).any(0))[0]
    y0, y1, x0, x1 = rows.min() - 40, rows.max() + 40, cols.min() - 40, cols.max() + 40
    a, b = A[y0:y1, x0:x1], B[y0:y1, x0:x1]; half = (cols.max() - cols.min()) / 2
    img = np.full(a.shape + (3,), 18, np.uint8); img[a & b] = (90, 90, 90); img[a & ~b] = (0, 210, 255); img[b & ~a] = (80, 220, 80)
    iou = (a & b).sum() / max((a | b).sum(), 1); diffs = []
    for m_, tag in ((a & ~b, "A"), (b & ~a, "B")):
        lab, n = label(m_)
        for i in range(1, n + 1):
            r = lab == i
            if r.sum() < 600: continue
            w = 2 * distance_transform_edt(r).max()
            if w < 8: continue
            ys, xs = np.nonzero(r); cx_ = x0 + xs.mean() - centre(ka)
            if cx_ > 2: continue                                            # symmetric: number the left half only
            diffs.append((ys.mean(), xs.mean(), w, tag, int(r.sum())))
    diffs.sort(); out = []
    for k, (y, x, w, tag, area) in enumerate(diffs, 1):
        cv2.circle(img, (int(x), int(y)), 26, (255, 255, 255), -1); t = str(k); cv2.putText(img, t, (int(x) - 10 * len(t), int(y) + 10), 0, 0.95, (0, 0, 0), 3)
        out.append({"n": k, "only_in": P["a"][0] if tag == "A" else P["b"][0], "width_px": round(float(w), 1), "width_pct_half": round(100 * w / half, 1), "area_px": area})
    nm = {"top": "SUS", "bottom": "JOS", "front": "FATA", "back": "SPATE"}
    cv2.putText(img, "galben = doar %s, verde = doar %s, gri = ambele; IoU %.3f" % (nm[ka], nm[kb], iou), (20, 40), 0, 1.1, (235, 235, 235), 2, cv2.LINE_AA)
    cv2.imwrite(f"{OD}/{P['name']}.png", cv2.resize(img, None, fx=0.6, fy=0.6)); report[P["name"]] = {"iou": round(float(iou), 3), "diffs": out}
    print(P["name"], "IoU %.3f" % iou, "; ".join("%d:%s %.0fpx(%.1f%%)" % (d["n"], nm[d["only_in"]], d["width_px"], d["width_pct_half"]) for d in out))
json.dump(report, open(f"{OD}/calibrare.json", "w"), indent=1)
