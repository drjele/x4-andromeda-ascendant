# Experiment: the mesh moved toward the user's confirmed zones (profile + bottom view). For each part group the model's
# silhouette in a view is compared with the zone's silhouette on a world grid (through the ref-01 fit); boundary
# points of the model are matched to the nearest zone boundary, the offsets spread into a smooth field, and the group's
# vertices moved by part of it in that view's two axes; views alternate over several iterations.
# Usage: python fit_zones.py <mesh.npz> <out_dir> [iterations]
import sys, json, numpy as np, cv2
from scipy.ndimage import distance_transform_edt
MESH, OD = sys.argv[1:3]; IT = int(sys.argv[3]) if len(sys.argv) > 3 else 6
T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; Z = "/home/adrian/Documents/Andromeda/2026-10-25-tableta-v14"
FIT = json.load(open(f"{T}/trace/fit_ref01.json")); ORTHO = json.load(open(f"{T}/view/ref01/views.json")); AXV = json.load(open(f"{T}/trace/cam_axes.json")); K = 4
VOX = 4.0; g = [np.arange(-1100, 1100.1, VOX), np.arange(-1700, 1700.1, VOX), np.arange(-600, 600.1, VOX)]
def to_ref(view, p):
    n, s, k = ORTHO[view]["res"], ORTHO[view]["scale"], ORTHO[view]["rot"]; sx, sy, tx, ty = FIT[view]["p"]
    u = p @ np.array(AXV[view]["right"]); w = p @ np.array(AXV[view]["up"]); col = u / s * n + n / 2; row = n / 2 - w / s * n
    i, j = {0: (row, col), 1: (n - col, row), -1: (col, n - row)}[k]
    if FIT[view].get("flip"): j = n - j
    return sx * j + tx, sy * i + ty
VIEWS = {"side": (1, 2), "bottom": (0, 1)}
def sample(view, mask):
    a, b = VIEWS[view]; A, B = np.meshgrid(g[a], g[b], indexing="ij"); p = np.zeros(A.shape + (3,)); p[..., a] = A; p[..., b] = B
    x, y = to_ref(view, p.reshape(-1, 3)); x = np.round(x * K).astype(int); y = np.round(y * K).astype(int)
    ok = (x >= 0) & (y >= 0) & (x < mask.shape[1]) & (y < mask.shape[0]); out = np.zeros(x.shape, bool); out[ok] = mask[y[ok], x[ok]]; return out.reshape(A.shape)
# the zones
side = json.load(open(f"{Z}/final_profil/side_faces_final.json")); SH = (215 * K, 815 * K)
def side_mask(names):
    m = np.zeros(SH, np.uint8)
    for nm in names:
        for pc in side[nm]:
            cv2.fillPoly(m, [np.round(np.array(pc["outer"])).astype(np.int32)], 1)
            for h in pc["holes"]: cv2.fillPoly(m, [np.round(np.array(h)).astype(np.int32)], 0)
    return m > 0
bot = np.load(f"{Z}/final_jos/jos_zone.npz"); bmask = lambda names: np.logical_or.reduce([bot[n] for n in names])
GROUPS = {   # group: (model part prefixes, side zones, bottom zones)
    "brate": (("A",), ["BRAT"], ["BRAT", "BS"]),
    "punte": (("V",), ["PUNTE"], []),
    "aripi_sus": (("U",), ["AS"], []),
    "aripi_jos": (("L", "H"), ["AI"], ["AI"]),
    "corp": (("C",), ["CORP", "CORP spate", "CORP bot", "CORP etaj"], ["CORP fata", "CORP spate"]),
    "arc_u": (("G",), [], ["ARC U"])}
SIL = {"brate": ("A1", "A2"), "corp": ("C0", "C22")}                      # the parts whose silhouette stands for the group
M = np.load(MESH); V = {k[2:]: M[k].astype(np.float64) for k in M.files if k.startswith("v|") and not k.startswith("v|SRC")}; TR = {k[2:]: M[k] for k in M.files if k.startswith("t|")}
def keys(group, sil=False):
    pre = GROUPS[group][0]; ks = [k for k in V if k.split("|")[0].startswith(pre)]
    if sil and group in SIL: ks = [k for k in ks if k.split("|")[0] in SIL[group]]
    return ks
def raster(ks, view):
    a, b = VIEWS[view]; m = np.zeros((len(g[b]), len(g[a])), np.uint8)
    for k in ks:
        q = np.stack([(V[k][:, a] - g[a][0]) / VOX, (V[k][:, b] - g[b][0]) / VOX], 1)
        for tri in np.round(q[TR[k]]).astype(np.int32): cv2.fillConvexPoly(m, tri, 1)
    return m.T > 0
TGT = {}
for gr, (_, sz, bz) in GROUPS.items():
    if sz: TGT[(gr, "side")] = sample("side", side_mask(sz))
    if bz: TGT[(gr, "bottom")] = sample("bottom", bmask(bz))
def iou(a, b): return (a & b).sum() / max((a | b).sum(), 1)
def step(gr, view, frac=0.6, reach=70.0, sigma=6.0):
    tgt = TGT[(gr, view)]; mod = raster(keys(gr, True), view); a, b = VIEWS[view]
    em = mod & ~cv2.erode(mod.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool); et = tgt & ~cv2.erode(tgt.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    d, (iy, ix) = distance_transform_edt(~et, return_indices=True); pts = np.argwhere(em)
    dd = d[pts[:, 0], pts[:, 1]] * VOX; ok = dd < reach; pts = pts[ok]
    DX = np.zeros(mod.shape); DY = np.zeros(mod.shape); WT = np.zeros(mod.shape)
    # the grids are [a, b]: rows along axis a, columns along axis b
    DX[pts[:, 0], pts[:, 1]] = (iy[pts[:, 0], pts[:, 1]] - pts[:, 0]) * VOX; DY[pts[:, 0], pts[:, 1]] = (ix[pts[:, 0], pts[:, 1]] - pts[:, 1]) * VOX; WT[pts[:, 0], pts[:, 1]] = 1
    bx, by, bw = (cv2.GaussianBlur(x, (0, 0), sigma) for x in (DX, DY, WT)); fx = np.where(bw > 1e-6, bx / np.maximum(bw, 1e-6), 0); fy = np.where(bw > 1e-6, by / np.maximum(bw, 1e-6), 0)
    fade = np.clip(cv2.GaussianBlur(WT, (0, 0), sigma * 3) * 40, 0, 1); fx *= fade; fy *= fade
    for k in keys(gr):
        ia = np.clip(np.round((V[k][:, a] - g[a][0]) / VOX).astype(int), 0, len(g[a]) - 1); ib = np.clip(np.round((V[k][:, b] - g[b][0]) / VOX).astype(int), 0, len(g[b]) - 1)
        V[k][:, a] += frac * fx[ia, ib]; V[k][:, b] += frac * fy[ia, ib]
log = {}
for (gr, view), t in TGT.items(): log[f"{gr}/{view}"] = [round(iou(raster(keys(gr, True), view), t), 3)]
for it in range(IT):
    for view in ("side", "bottom"):
        for gr in GROUPS:
            if (gr, view) in TGT: step(gr, view)
    for (gr, view), t in TGT.items(): log[f"{gr}/{view}"].append(round(iou(raster(keys(gr, True), view), t), 3))
    print("iter", it + 1, {k: v[-1] for k, v in log.items()})
out = {f"v|{k}": v.astype(np.float32) for k, v in V.items()}; out.update({f"t|{k}": v for k, v in TR.items()}); np.savez_compressed(f"{OD}/mesh_fit.npz", **out)
json.dump(log, open(f"{OD}/fit_log.json", "w"), indent=1)
# sheets: per view, zones (grey) vs model before (red outline) and after (green outline)
M0 = np.load(MESH); V0 = {k[2:]: M0[k].astype(np.float64) for k in M0.files if k.startswith("v|") and not k.startswith("v|SRC")}
for view in VIEWS:
    tg = np.logical_or.reduce([t for (gr, v), t in TGT.items() if v == view]); Vf = dict(V)
    V.clear(); V.update(V0); before = raster([k for gr in GROUPS for k in keys(gr)], view); V.clear(); V.update(Vf); after = raster([k for gr in GROUPS for k in keys(gr)], view)
    im = np.full(tg.shape + (3,), 25, np.uint8); im[tg] = (110, 110, 110)
    for m, col in ((before, (40, 40, 230)), (after, (60, 230, 60))):
        e = m & ~cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool); im[cv2.dilate(e.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0] = col
    im = np.ascontiguousarray(im.transpose(1, 0, 2)[::-1])                 # a to the right, b up
    cv2.imwrite(f"{OD}/fit_{view}.png", cv2.resize(im, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_NEAREST))
print("DONE")
