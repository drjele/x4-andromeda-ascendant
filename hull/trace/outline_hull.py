# The ship from the user's outlines only: each view's silhouette (top, bottom, side) pulled straight through the ship
# and intersected (a visual hull), mirrored to perfect symmetry, as one mesh for the whole ship and one for the body.
# Front/back stay out: ref 01 draws them in perspective, they would carve wrongly.
# Usage: python outline_hull.py <drawings_dir> <out.npz>
import sys, json, numpy as np, cv2
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
D, OUT = sys.argv[1], sys.argv[2]; T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
# the refit that also tried the mirror (the bottom view needs it)
FIT = json.load(open(f"{T}/trace/fit_ref01.json")); ORTHO = json.load(open(f"{T}/view/ref01/views.json")); AX = json.load(open(f"{T}/trace/cam_axes.json"))
AL = json.load(open(f"{D}/align.json")); MASKS = np.load(f"{D}/part_masks.npz"); K = 4; VOX = 5.0
BOX = np.array([[-1100, 1100], [-1500, 1500], [-500, 500]], float)
g = [np.arange(lo, hi + VOX / 2, VOX) for lo, hi in BOX]
def to_ref(view, p):
    # world points -> pixel (x, y) in the 4x ref crop, through the ortho render and the fit
    n, s, k = ORTHO[view]["res"], ORTHO[view]["scale"], ORTHO[view]["rot"]; sx, sy, tx, ty = FIT[view]["p"]
    u = p @ np.array(AX[view]["right"]); w = p @ np.array(AX[view]["up"]); col = u / s * n + n / 2; row = n / 2 - w / s * n
    i, j = {0: (row, col), 1: (n - col, row), -1: (col, n - row)}[k]
    if FIT[view].get("flip"): j = n - j
    return (sx * j + tx) * K, (sy * i + ty) * K
def sample(view, mask, a, b, plane):
    # the view's 2D mask resampled on a world grid spanned by axes a, b (the third coordinate 0)
    A, B = np.meshgrid(g[a], g[b], indexing="ij"); p = np.zeros(A.shape + (3,)); p[..., a] = A; p[..., b] = B
    x, y = to_ref(view, p.reshape(-1, 3)); x = np.round(x).astype(int); y = np.round(y).astype(int)
    ok = (x >= 0) & (y >= 0) & (x < mask.shape[1]) & (y < mask.shape[0]); out = np.zeros(x.shape, bool); out[ok] = mask[y[ok], x[ok]]
    return out.reshape(A.shape)
def silhouette(name):
    # the drawn regions plus the rest of the ship in the reference, minus the hatched holes
    view = AL[name]["view"]; j = json.load(open(f"{D}/regions_{name}.json")); reg = np.load(f"{D}/regions_{name}.npz")["reg"]
    ref = cv2.resize(cv2.imread(f"{T}/overlay/ref01/{view}_mask.png", 0), (reg.shape[1], reg.shape[0])) > 127
    drawn = np.isin(reg, [r["label_map"] for r in j["regions"] if not r["outside"]])
    holes = np.isin(reg, [r["label_map"] for r in j["regions"] if "red" in r["marks"] and r["outside"]])
    m = (ref | drawn) & ~cv2.dilate(holes.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    return cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((9, 9), np.uint8)) > 0
def part(name, part_name): return MASKS[f"{part_name}|{name}"] if f"{part_name}|{name}" in MASKS.files else None
def solid(top_xy, side_yz):
    f = (top_xy[:, :, None] & side_yz[None, :, :]).astype(np.float32); f = 0.5 * (f + f[::-1])   # mirror about x = 0
    f = gaussian_filter(f, 1.6); v, fc, _, _ = marching_cubes(f, 0.5, spacing=(VOX, VOX, VOX)); return (v + BOX[:, 0]).astype(np.float32), fc.astype(np.int32)
NAMES = {AL[n]["view"]: n for n in AL}
sil_top = sample("top", silhouette(NAMES["top"]), 0, 1, "xy"); sil_bottom = sample("bottom", silhouette(NAMES["bottom"]), 0, 1, "xy"); top = sil_top & sil_bottom
side = sample("side", silhouette(NAMES["side"]), 1, 2, "yz")
ship_v, ship_f = solid(top, side)
body_top = sample("top", part(NAMES["top"], "corp"), 0, 1, "xy"); body_bottom = sample("bottom", part(NAMES["bottom"], "corp"), 0, 1, "xy"); body_xy = body_top | body_bottom
body_side = sample("side", part(NAMES["side"], "corp"), 1, 2, "yz"); body_v, body_f = solid(body_xy, body_side)
def others(view, a, b):
    # every drawn part except the body, in this view: where the body edge meets one, it is a junction or hidden
    out = None
    for k in MASKS.files:
        pn, nm = k.split("|")
        if nm == NAMES[view] and pn != "corp":
            m = sample(view, MASKS[k], a, b, ""); out = m if out is None else out | m
    return out
np.savez_compressed(OUT, others_top=others("top", 0, 1), others_bottom=others("bottom", 0, 1), others_side=others("side", 1, 2), ship_v=ship_v, ship_f=ship_f, body_v=body_v, body_f=body_f, top=top, side=side, body_xy=body_xy, body_side=body_side, sil_top=sil_top, sil_bottom=sil_bottom, arms_top=sample("top", part(NAMES["top"], "brate"), 0, 1, "xy"), arms_bottom=sample("bottom", part(NAMES["bottom"], "brate"), 0, 1, "xy"), arms_side=sample("side", part(NAMES["side"], "brate"), 1, 2, "yz"), body_top=body_top, body_bottom=body_bottom)
print("HULL ship", len(ship_v), "body", len(body_v), "extent", ship_v.min(0).round(), ship_v.max(0).round())
