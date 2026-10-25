# The user's lines kept only where they lie on the ship, away from the background (the borders between overlapping
# parts), over the negative with the ship's outline; the upper half, mirrored.
# Usage: python inner_lines.py <view> <background.npy> <outline.json> <axis> <margin> <out.png> <lines.json> ...
import sys, json, numpy as np, cv2
from scipy.ndimage import distance_transform_edt
VIEW, BGF, OJ, AX, MG, OUT = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
bg = np.load(BGF); H, W = bg.shape; dist = distance_transform_edt(~bg)
im = cv2.resize(cv2.imread(f"/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01/{VIEW}.png"), (W, H), interpolation=cv2.INTER_CUBIC)
r = np.arange(H); src = np.clip(np.where(r <= AX, r, np.round(2 * AX - r).astype(int)), 0, H - 1); out = im[src].copy(); out[bg] = (0, 170, 0)
for c in json.load(open(OJ)): cv2.polylines(out, [np.round(np.array(c)).astype(np.int32)], True, (255, 80, 255), 5, cv2.LINE_AA)
inner = []
for path in sys.argv[7:]:
    for c in json.load(open(path)):
        c = np.array(c, float); c = c[c[:, 1] <= AX + 1]
        if len(c) < 5: continue
        yi = np.clip(np.round(c[:, 1]).astype(int), 0, H - 1); xi = np.clip(np.round(c[:, 0]).astype(int), 0, W - 1); ok = dist[yi, xi] > MG
        for run in np.split(np.arange(len(c)), np.where(np.diff(ok.astype(int)) != 0)[0] + 1):
            if ok[run[0]] and np.hypot(*np.diff(c[run], axis=0).T).sum() > 60: inner += [c[run], np.stack([c[run][:, 0], 2 * AX - c[run][:, 1]], 1)]
for c in inner: cv2.polylines(out, [np.round(c).astype(np.int32)], False, (0, 220, 255), 5, cv2.LINE_AA)
json.dump([c.tolist() for c in inner], open(OUT.replace(".png", ".json"), "w")); cv2.imwrite(OUT, cv2.resize(out, None, fx=0.5, fy=0.5)); print("INNER", len(inner))
