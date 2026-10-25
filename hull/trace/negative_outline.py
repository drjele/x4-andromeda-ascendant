# Outlines strictly on the border between the ship and the background (the negative): the background mask's contours
# (outer and holes), smoothed into even closed curves, drawn over the negative.
# Usage: python negative_outline.py <view> <background.npy> <axis> <smooth> <out.png>
import sys, json, numpy as np, cv2
VIEW, BGF, AX, SM, OUT = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
bg = np.load(BGF); H, W = bg.shape
ship = (~bg).astype(np.uint8); ship = (cv2.GaussianBlur(ship.astype(np.float32), (0, 0), SM) > 0.5).astype(np.uint8)   # the pixel staircase smoothed off
cs, hi = cv2.findContours(ship, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE); curves = []
for c in cs:
    if cv2.contourArea(c) < 400: continue
    c = c[:, 0, :].astype(float); s = 7; k = np.exp(-0.5 * (np.arange(-3 * s, 3 * s + 1) / s) ** 2); k /= k.sum()
    curves.append(np.stack([np.convolve(np.r_[c[-3 * s:, i], c[:, i], c[:3 * s, i]], k, "valid") for i in (0, 1)], 1))
im = cv2.resize(cv2.imread(f"/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01/{VIEW}.png"), (W, H), interpolation=cv2.INTER_CUBIC)
r = np.arange(H); src = np.clip(np.where(r <= AX, r, np.round(2 * AX - r).astype(int)), 0, H - 1); out = im[src].copy(); out[bg] = (0, 170, 0)
for c in curves: cv2.polylines(out, [np.round(c).astype(np.int32)], True, (255, 80, 255), 5, cv2.LINE_AA)
json.dump([c.tolist() for c in curves], open(OUT.replace(".png", ".json"), "w")); cv2.imwrite(OUT, cv2.resize(out, None, fx=0.5, fy=0.5)); print("OUTLINES", len(curves))
