# Overlay a version on the user's drawings (world frame through the corrected ref-01 fit) and on grannyte's
# original mesh: the whole ship and each part group, from above, below and the side. Grey = both, red = only the
# model, cyan = only the reference; the IoU is printed on each panel and written to overlay.json.
# Usage: python overlay_check.py <drawings_dir> <mesh.npz> <out_dir> <tag>
import sys, json, numpy as np, cv2
D, MESH, ODIR, TAG = sys.argv[1:5]; sys.argv = ["x", D, "/dev/null"]
exec(open("/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/trace/outline_hull.py").read().split("NAMES = {")[0])
NAMES = {AL[n]["view"]: n for n in AL}; Z = np.load(MESH)
GROUPS = {"nava": None, "corp": "C", "brate": "A", "aripi_superioare": "U", "aripi_inferioare": "LHW", "semiluna": "C16"}
DRAWN = {"corp": "corp", "brate": "brate", "aripi_superioare": "aripi_superioare", "aripi_inferioare": "aripi_inferioare", "semiluna": "semiluna"}
VIEWS = {"top": (0, 1), "bottom": (0, 1), "side": (1, 2)}
def raster(keys, a, b):
    m = np.zeros((len(g[b]), len(g[a])), np.uint8)
    for k in keys:
        v = Z[f"v|{k}"]; t = Z[f"t|{k}"]; q = np.stack([(v[:, a] - g[a][0]) / VOX, (v[:, b] - g[b][0]) / VOX], 1)
        # one triangle at a time: fillPoly on many polygons fills by parity, so overlapping triangles would cancel
        for tri in np.round(q[t]).astype(np.int32): cv2.fillConvexPoly(m, tri, 1)
    return m.T.astype(bool)   # [a, b] like the sampled drawings
def keys_of(group):
    pre = GROUPS[group]; ks = [k[2:] for k in Z.files if k.startswith("v|") and not k.startswith("v|SRC")]
    if pre is None: return ks
    if pre == "C16": return [k for k in ks if k.split("|")[0] == "C16"]
    if pre == "C": return [k for k in ks if k.startswith("C")]
    return [k for k in ks if k[0] in pre]
def panel(model, ref, title):
    im = np.full(model.shape + (3,), 25, np.uint8); im[model & ref] = (150, 150, 150); im[model & ~ref] = (40, 40, 230); im[~model & ref] = (230, 210, 40)
    im = np.ascontiguousarray(im.transpose(1, 0, 2)[::-1]); iou = (model & ref).sum() / max((model | ref).sum(), 1)
    cv2.putText(im, f"{title}  IoU {iou:.2f}", (10, 30), 0, 0.8, (255, 255, 255), 2); return im, round(float(iou), 3)
def crop(ims):
    m = np.zeros(ims[0].shape[:2], bool)
    for im in ims: m |= im.max(2) > 30
    ys, xs = np.nonzero(m); return [im[max(ys.min() - 10, 0):ys.max() + 10, max(xs.min() - 10, 0):xs.max() + 10] for im in ims]
report = {}
for group in GROUPS:
    rows = []; report[group] = {}
    for view, (a, b) in VIEWS.items():
        model = raster(keys_of(group), a, b); cells = []
        if group == "nava": ref = sample(view, silhouette(NAMES[view]), a, b, "")
        else: pm = part(NAMES[view], DRAWN[group]); ref = sample(view, pm, a, b, "") if pm is not None else None
        if ref is not None: im, iou = panel(model, ref, f"{group}/{view} vs desen"); cells.append(im); report[group][f"{view}_desen"] = iou
        if group == "nava":
            im, iou = panel(model, raster(["SRC|source"], a, b), f"nava/{view} vs original"); cells.append(im); report[group][f"{view}_original"] = iou
        if cells: rows.append(np.hstack(crop(cells)) if len(cells) > 1 else crop(cells)[0])
    if rows:
        W = max(r.shape[1] for r in rows); sheet = np.vstack([np.pad(r, ((0, 8), (0, W - r.shape[1]), (0, 0))) for r in rows])
        cv2.imwrite(f"{ODIR}/overlay_{TAG}_{group}.png", sheet)
json.dump(report, open(f"{ODIR}/overlay_{TAG}.json", "w"), indent=1); print(TAG, json.dumps(report))
