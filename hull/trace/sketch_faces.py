# The confirmed drawn lines joined into closed outlines: every open end is carried on along its own direction until it
# touches another line (closing the small gaps the hand left), the lines are drawn thin on a canvas, the regions
# between them are the closed faces, and each face takes the part name written inside it (seed points from the
# labels file). Writes the face outlines (smoothed, in ref-crop pixels x4) and a sheet with each face filled.
# Usage: python sketch_faces.py <dir> <view> <labels.json> <out.png>
import sys, json, numpy as np, cv2
D, VIEW, LAB, OUT = sys.argv[1:5]; R = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"; K = 4
L = json.load(open(LAB)); C = json.load(open(f"{D}/{VIEW}_curves.json")); ref = cv2.imread(f"{R}/{VIEW}.png")
H, W = ref.shape[0] * K, ref.shape[1] * K; reach = L.get("extend", 160)
canvas = np.zeros((H, W), np.uint8)
for c in C.values(): cv2.polylines(canvas, [np.round(np.array(c["points"])).astype(np.int32)], c["closed"], 255, L.get("line_px", 7))
def carry(p, d, own):
    # step from p along d until another line is hit (not this line's own pixels near its end)
    d = d / max(np.linalg.norm(d), 1e-9)
    for t in range(4, reach):
        q = np.round(p + d * t).astype(int)
        if not (0 <= q[0] < W and 0 <= q[1] < H): return None
        if canvas[q[1], q[0]] and own[q[1], q[0]] == 0: return q
    return None
added = []
for name, c in C.items():
    if c["closed"]: continue
    pts = np.array(c["points"]); own = np.zeros_like(canvas); cv2.polylines(own, [np.round(pts[:60]).astype(np.int32)], False, 255, 9); cv2.polylines(own, [np.round(pts[-60:]).astype(np.int32)], False, 255, 9)
    for p, d in ((pts[0], pts[0] - pts[12]), (pts[-1], pts[-1] - pts[-13])):
        q = carry(p, d, own)
        if q is not None: cv2.line(canvas, tuple(np.round(p).astype(int)), tuple(q), 255, 3); added.append((name, int(np.hypot(*(q - p)))))
print("ends carried:", added)
faces = (canvas == 0).astype(np.uint8); n, lab = cv2.connectedComponents(faces, connectivity=4)
out = cv2.resize(ref, (W, H)) // 3; pal = [(0, 220, 0), (255, 170, 0), (0, 0, 255), (255, 0, 255), (0, 255, 255), (60, 60, 255), (200, 90, 255), (255, 255, 0), (40, 140, 255), (255, 80, 80)]
outlines = {}; seen = {}
for k, (part, (sx, sy)) in enumerate(L["faces"].items()):
    f = lab[sy, sx]
    if f == 0: print("seed on a line:", part); continue
    if f in seen: print("same face as", seen[f], ":", part); continue      # several labels in one region (e.g. the body seen in pieces)
    seen[f] = part
    m = (lab == f).astype(np.uint8); m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=L.get("line_px", 7) // 2 + 1)     # take back the line width
    # outer outline and holes (the arm is a ring around the windows and the parts inside it)
    cs, hi = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE); hi = hi[0]
    kk = np.exp(-0.5 * (np.arange(-15, 16) / 5.0) ** 2); kk /= kk.sum()
    sm = lambda c: np.stack([np.convolve(np.r_[c[-15:, i], c[:, i], c[:15, i]], kk, "valid") for i in (0, 1)], 1)
    outer = max(range(len(cs)), key=lambda i: cv2.contourArea(cs[i]) if hi[i][3] < 0 else -1)
    holes = [sm(cs[i][:, 0, :].astype(float)) for i in range(len(cs)) if hi[i][3] == outer and cv2.contourArea(cs[i]) > 2000]
    c = sm(cs[outer][:, 0, :].astype(float)); outlines[part] = {"outer": c.tolist(), "holes": [h.tolist() for h in holes]}; col = pal[k % len(pal)]
    ov = out.copy(); ov[m > 0] = col; out = cv2.addWeighted(out, 0.55, ov, 0.45, 0)
    for q in [c] + holes: cv2.polylines(out, [np.round(q).astype(np.int32)], True, col, 5, cv2.LINE_AA)
    cv2.putText(out, part, (sx - 60, sy), 0, 1.8, (255, 255, 255), 5, cv2.LINE_AA)
    print("face", part, "area", int(m.sum()))
json.dump(outlines, open(f"{D}/{VIEW}_faces.json", "w")); cv2.imwrite(OUT, cv2.resize(out, None, fx=0.5, fy=0.5)); print("FACES", len(outlines))
