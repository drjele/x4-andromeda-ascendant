# Calibration applied: the opposite view takes the reference view's outer silhouette and through-holes, its own zones
# (which part is where) carried along by a smooth deformation. On the multi-view drawing, each boundary point of the
# view's silhouette is matched to the nearest boundary point of the reference silhouette (and the other way round),
# the offsets spread into a smooth field (Gaussian-weighted), applied a few times; the warped zone map is then clipped
# to the reference silhouette and the uncovered rim filled from the nearest zone, so the silhouettes coincide exactly.
# The result goes back to the view's own sheet frame as a zone map + names (one half, mirrored), with a sheet to confirm.
# Usage: python calibrate_apply.py <layout.json> <vederi.json> <spec.json> <out_dir>
#   spec: {"view": "bottom", "ref": "top", "ref_sil": {...calibrate.py spec}, "zones": [{"zone"|"npz"...: , "take"/"names": , "as": name}, ...],
#          "sheet": png, "sheet_size": [H, W], "name": "jos"}
import sys, json, os, numpy as np, cv2
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.spatial import cKDTree
LJ, VJ, SJ, OD = sys.argv[1:5]; LAY = json.load(open(LJ)); VIEWS = json.load(open(VJ)); S = json.load(open(SJ)); os.makedirs(OD, exist_ok=True)
Wc, Hc = LAY["size"]; AFF = {k: np.array(v, float) for k, v in LAY["aff"].items()}
def centre(key): A = AFF[key]; ax = VIEWS[key]["axis"]; return A[0, 0] * ax + A[0, 2] if key in ("back", "front") else A[0, 1] * ax + A[0, 2]
def to_canvas(key, m, interp=cv2.INTER_NEAREST): return cv2.warpAffine(m.astype(np.int32 if m.dtype != bool else np.uint8).astype(np.float32), AFF[key], (Wc, Hc), flags=interp)
def mirror(m, cx): i = np.arange(Wc); src = np.clip(np.where(i <= cx, i, np.round(2 * cx - i).astype(int)), 0, Wc - 1); return m[:, src]
def sil(spec):
    if "zone" in spec:
        z = np.load(spec["zone"]); nm = json.load(open(spec["names"])); gaps = [int(k) for k, t in nm.items() if t.startswith("G")]
        return (z > 0) & ~np.isin(z, gaps)
    z = np.load(spec["npz"]); return np.any([z[t] for t in z.files], 0)
V, R = S["view"], S["ref"]
ref = mirror(to_canvas(R, sil(S["ref_sil"])) > 0.5, centre(R))
# the view's zones as one label map on the canvas (later entries override earlier ones)
names = []; lab = np.zeros(S["sheet_size"], np.int32)
for z in S["zones"]:
    if "npz" in z: m = np.load(z["npz"])[z["take"]]
    else:
        zz = np.load(z["zone"]); nm = json.load(open(z["names"])); m = np.isin(zz, [int(k) for k, t in nm.items() if t in z["take"]])
    if z["as"] not in names: names.append(z["as"])
    lab[m] = names.index(z["as"]) + 1
L = mirror(np.round(to_canvas(V, lab)).astype(np.int32), centre(V))
dx = int(round(centre(R) - centre(V))); L = np.roll(L, dx, 1)
if V not in ("top", "bottom"):                                             # front/back: same top edge
    ya = np.nonzero(ref.any(1))[0].min(); yb = np.nonzero((L > 0).any(1))[0].min(); L = np.roll(L, ya - yb, 0)
def edge(m): return np.argwhere(m & ~cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)).astype(float)
yy, xx = np.mgrid[0:Hc, 0:Wc].astype(np.float32); fy = np.zeros((Hc, Wc), np.float32); fx = np.zeros((Hc, Wc), np.float32)
cur = L.copy(); SIG = S.get("sigma", 40)
for it in range(S.get("iters", 6)):
    src = edge(cur > 0); dst = edge(ref)
    if not len(src) or not len(dst): break
    t1 = cKDTree(dst); d1, i1 = t1.query(src); t2 = cKDTree(src); d2, i2 = t2.query(dst)
    P = np.vstack([src, src[i2]]); D = np.vstack([dst[i1] - src, dst - src[i2]])               # forward offsets at the view's boundary
    acc = np.zeros((2, Hc, Wc), np.float32); w = np.zeros((Hc, Wc), np.float32)
    pi = np.round(P).astype(int); np.add.at(acc[0], (pi[:, 0], pi[:, 1]), D[:, 0]); np.add.at(acc[1], (pi[:, 0], pi[:, 1]), D[:, 1]); np.add.at(w, (pi[:, 0], pi[:, 1]), 1)
    g0, g1, gw = gaussian_filter(acc[0], SIG), gaussian_filter(acc[1], SIG), gaussian_filter(w, SIG)
    dy_, dx_ = g0 / (gw + 1e-6), g1 / (gw + 1e-6)
    # backward map: a pixel q comes from q - offset (offset field sampled at q, small steps keep it smooth)
    cur = cv2.remap(cur.astype(np.float32), xx - dx_ * 0.7, yy - dy_ * 0.7, cv2.INTER_NEAREST).astype(np.int32)
    iou = ((cur > 0) & ref).sum() / max(((cur > 0) | ref).sum(), 1); print("iter %d IoU %.3f" % (it, iou))
# clip to the reference silhouette and fill the uncovered rim from the nearest zone
cur[~ref] = 0; miss = ref & (cur == 0)
if miss.any():
    _, (iy, ix) = distance_transform_edt(cur == 0, return_indices=True); cur[miss] = cur[iy[miss], ix[miss]]
cur = mirror(cur, centre(R))
# back to the view's own sheet frame
A = AFF[V]; back = np.roll(cur, -dx, 1)
if V not in ("top", "bottom"): back = np.roll(back, -(ya - yb), 0)
Hs, Ws = S["sheet_size"]; sheet_lab = cv2.warpAffine(back.astype(np.float32), A, (Ws, Hs), flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP).astype(np.int32)
nm = {str(i + 1): n for i, n in enumerate(names)}; N = S["name"]
np.save(f"{OD}/{N}_zone.npy", sheet_lab); json.dump(nm, open(f"{OD}/{N}_nume.json", "w"), indent=1)
# sheet to confirm: zones over the reference image, the reference's silhouette edge in white
im = cv2.imread(S["sheet"]); out = (im * 0.45).astype(np.uint8); rng = np.random.default_rng(4); pal = {i: rng.integers(70, 255, 3) for i in range(1, len(names) + 1)}
for i, c in pal.items(): m = sheet_lab == i; out[m] = (out[m] * 0.35 + c * 0.65).astype(np.uint8)
e = sheet_lab > 0; e = cv2.morphologyEx(e.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; out[e] = (255, 255, 255)
for a in np.unique(sheet_lab)[1:]:
    b = cv2.morphologyEx((sheet_lab == a).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; out[b] = (230, 230, 230)
side = np.zeros((Hs, 900, 3), np.uint8)
for j, (k, t) in enumerate(nm.items()):
    y = 70 + 72 * j; cv2.rectangle(side, (30, y - 30), (90, y + 15), tuple(int(c) for c in pal[int(k)]), -1); cv2.putText(side, "%s  %s" % (k, t), (110, y + 8), 0, 1.1, (235, 235, 235), 2, cv2.LINE_AA)
cv2.imwrite(f"{OD}/{N}_calibrat.png", cv2.resize(np.hstack([out, side]), None, fx=0.5, fy=0.5)); print("SAVED", N, nm)
