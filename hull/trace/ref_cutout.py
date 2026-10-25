# A gap cut out of the reference itself: the black background showing through, in a box, as the connected dark region
# that holds a seed point; smoothed into one even closed outline. Writes it (ref-crop px x4) to a json.
# Usage: python ref_cutout.py <view> <x0> <y0> <x1> <y1> <seed_x> <seed_y> <gray> <out.json>
import sys, json, numpy as np, cv2
VIEW = sys.argv[1]; x0, y0, x1, y1, sx, sy, T = map(int, sys.argv[2:9]); OUT = sys.argv[9]
g = cv2.resize(cv2.cvtColor(cv2.imread(f"/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01/{VIEW}.png"), cv2.COLOR_BGR2GRAY), None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
g = cv2.GaussianBlur(g, (5, 5), 0); m = np.zeros(g.shape, np.uint8); m[y0:y1, x0:x1] = (g[y0:y1, x0:x1] < T)
m = cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab = cv2.connectedComponents(m, connectivity=8); k = lab[sy, sx]
if k == 0: d = np.where(lab > 0, np.hypot(*np.mgrid[0:g.shape[0], 0:g.shape[1]][::-1] - np.array([sx, sy])[:, None, None]), 1e9); k = lab.flat[np.argmin(d)]
reg = (lab == k).astype(np.uint8); cs, _ = cv2.findContours(reg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
s = 6; kk = np.exp(-0.5 * (np.arange(-3 * s, 3 * s + 1) / s) ** 2); kk /= kk.sum()
c = np.stack([np.convolve(np.r_[c[-3 * s:, i], c[:, i], c[:3 * s, i]], kk, "valid") for i in (0, 1)], 1)
json.dump(c.tolist(), open(OUT, "w")); print("CUTOUT area %d px, box %s" % (reg.sum(), cv2.boundingRect(reg)))
