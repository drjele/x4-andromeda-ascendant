# The background of a symmetric view, for checking: built on the half above the centreline (the better lit one) and
# mirrored. Background = flat dark grey reaching the image border, plus only the enclosed holes the user named (seed
# points), plus narrow dark gaps given by seed (dark though not flat: the background seen through a slit). "inside": a mask
# of the user's outer outline; no background inside it (minus a margin), except the named holes.
# Usage: python ref_background.py <view> <bg.json> <out.png>
import sys, json, numpy as np, cv2
VIEW, BJ, OUT = sys.argv[1:4]; B = json.load(open(BJ)); K = 4
im = cv2.imread(f"/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01/{VIEW}.png"); g0 = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
big = cv2.resize(im, None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC); H, W = big.shape[:2]; g = cv2.resize(g0, (W, H), interpolation=cv2.INTER_CUBIC)
mu = cv2.blur(g, (9, 9)); sd = np.sqrt(np.maximum(cv2.blur(g * g, (9, 9)) - mu * mu, 0))
flat = ((mu <= B["gray"]) & (sd <= B.get("flat", 3.0))).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(flat, connectivity=4)
bg = np.zeros((H, W), bool)
for i in range(1, n):
    x, y, w, h, a = st[i]
    if x == 0 or y == 0 or x + w == W or y + h == H: bg |= lab == i
if B.get("inside"):                                                       # dark ship parts the flat test mistakes for background: nothing inside
    ins = cv2.erode(np.load(B["inside"]).astype(np.uint8), np.ones((2 * B.get("inside_margin", 15) + 1,) * 2, np.uint8)) > 0   # the user's outer line (eroded) is background
    bg &= ~ins
for sx, sy in B["holes"]: bg |= lab == lab[sy, sx]
for sl in B.get("slits", []):                                              # a narrow dark gap: dark pixels connected to the seed, inside its box
    x0, y0, x1, y1 = sl["box"]; d = np.zeros((H, W), np.uint8); d[y0:y1, x0:x1] = cv2.GaussianBlur(g, (5, 5), 0)[y0:y1, x0:x1] < sl["gray"]
    nn, ll = cv2.connectedComponents(d, connectivity=8); bg |= ll == ll[sl["seed"][1], sl["seed"][0]] if ll[sl["seed"][1], sl["seed"][0]] else False
AX = B["axis"]
full = np.zeros_like(bg); r = np.arange(H); src = np.where(r <= AX, r, np.round(2 * AX - r).astype(int)); full = bg[np.clip(src, 0, H - 1)]
out = big[np.clip(src, 0, H - 1)].copy(); out[full] = (0, 230, 0)   # the lit half and its mirror image; cv2.line(out, (0, int(AX)), (W, int(AX)), (255, 255, 0), 2)
np.save(OUT.replace(".png", ".npy"), full); cv2.imwrite(OUT, cv2.resize(out, None, fx=0.5, fy=0.5)); print("BACKGROUND", int(full.sum()), "px")
