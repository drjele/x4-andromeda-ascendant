# The user's lines laid onto the background cut-out: every point of a drawn line that runs within `snap` px of the
# background's edge is moved onto that edge (the outline is the reference's own), points further in stay where the
# user drew them (borders between overlapping parts); lightly smoothed, built on the upper half and mirrored.
# Usage: python snap_lines.py <view> <background.npy> <axis> <snap> <out.png> <lines.json:colour> ...
import sys, json, numpy as np, cv2
from scipy.ndimage import distance_transform_edt
VIEW, BGF, AX, SNAP, OUT = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]; K = 4
bg = np.load(BGF); H, W = bg.shape
edge = bg & ~cv2.erode(bg.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
d, (iy, ix) = distance_transform_edt(~edge, return_indices=True)
im = cv2.resize(cv2.imread(f"/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01/{VIEW}.png"), (W, H), interpolation=cv2.INTER_CUBIC)
r = np.arange(H); src = np.clip(np.where(r <= AX, r, np.round(2 * AX - r).astype(int)), 0, H - 1)
out = im[src].copy(); out[bg] = (0, 230, 0); res = {}
for spec in sys.argv[6:]:
    path, col = spec.split(":"); col = tuple(int(c) for c in col.split(",")); lines = []
    for c in json.load(open(path)):
        c = np.array(c, float); c = c[c[:, 1] <= AX + 1]
        if len(c) < 5: continue
        yi = np.clip(np.round(c[:, 1]).astype(int), 0, H - 1); xi = np.clip(np.round(c[:, 0]).astype(int), 0, W - 1)
        near = d[yi, xi] < SNAP; c[near, 0] = ix[yi[near], xi[near]]; c[near, 1] = iy[yi[near], xi[near]]
        s = 3; k = np.exp(-0.5 * (np.arange(-3 * s, 3 * s + 1) / s) ** 2); k /= k.sum()
        if len(c) > 6 * s: c = np.stack([np.convolve(np.pad(c[:, j], 3 * s, mode="edge"), k, "valid") for j in (0, 1)], 1)
        lines += [c, np.stack([c[:, 0], 2 * AX - c[:, 1]], 1)]
    for c in lines: cv2.polylines(out, [np.round(c).astype(np.int32)], False, col, 5, cv2.LINE_AA)
    res[path] = [c.tolist() for c in lines]
json.dump(res, open(OUT.replace(".png", ".json"), "w")); cv2.imwrite(OUT, cv2.resize(out, None, fx=0.5, fy=0.5)); print("SNAPPED", {k.split("/")[-1]: len(v) for k, v in res.items()})
