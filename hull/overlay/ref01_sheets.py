# Per-component overlay sheets on the ref-01 views: the reference with our whole silhouette as a thin white
# edge and the component filled/edged in colour, beside our shaded render warped into the same frame.
# Usage: python ref01_sheets.py <out_dir> [group ...]   (groups: body vplate links arms upper uarch)
import json, sys, numpy as np, cv2
R = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"; O = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/view/ref01"
OUT = sys.argv[1]; groups = sys.argv[2:] or ["body", "vplate", "links", "arms", "upper", "uarch"]
spec = json.load(open(f"{O}/views.json")); fit = json.load(open(f"{R}/fit.json")); K = 2
COL = {"body": (60, 140, 255), "vplate": (40, 220, 255), "links": (80, 230, 120), "arms": (255, 150, 60), "upper": (255, 90, 200), "uarch": (255, 60, 90)}
def ours(view, tag):
    im = cv2.imread(f"{O}/{view}_{tag}.png", cv2.IMREAD_UNCHANGED); k = spec[view]["rot"]; return np.rot90(im, k) if k else im
def warp(im, view, size):
    sx, sy, tx, ty = fit[view]["p"]; A = np.float32([[sx * K, 0, tx * K], [0, sy * K, ty * K]]); return cv2.warpAffine(im, A, size, flags=cv2.INTER_LINEAR)
def edge(mask): return cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
for g in groups:
    rows = []
    for view in ("side", "top", "bottom", "front", "back"):
        ref = cv2.imread(f"{R}/{view}.png"); ref = cv2.resize(ref, None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC); size = (ref.shape[1], ref.shape[0])
        allm = warp(ours(view, "mask")[:, :, 3], view, size) > 127; gm = warp(ours(view, g)[:, :, 3], view, size) > 127
        left = ref.copy(); c = np.array(COL[g], np.uint8)
        left[gm] = (left[gm] * 0.55 + c * 0.45).astype(np.uint8); left[edge(allm)] = (235, 235, 235); left[edge(gm)] = c
        sh = ours(view, "shaded"); a = warp(sh[:, :, 3], view, size) / 255.0; rgb = warp(sh[:, :, :3], view, size)
        right = (np.full_like(ref, 40) * (1 - a[..., None]) + rgb * a[..., None]).astype(np.uint8); right[gm] = (right[gm] * 0.5 + c * 0.5).astype(np.uint8)
        cv2.putText(left, f"{g} / {view}  (IoU all {fit[view]['iou']})", (10, 24), 0, 0.7, (255, 255, 255), 2)
        rows.append(np.hstack([left, right]))
    W = max(r.shape[1] for r in rows); sheet = np.vstack([np.pad(r, ((0, 6), (0, W - r.shape[1]), (0, 0)), constant_values=120) for r in rows])
    cv2.imwrite(f"{OUT}/ref01_{g}.png", sheet); print("sheet", g, sheet.shape)
