# One view's lines in one sheet: each line set (json list of polylines, or of {points} dicts) drawn in its colour over the
# dimmed clean reference, the centreline marked, a legend at the side.
# Usage: python compose_lines.py <ref.png> <axis_x> <out.png> <set.json>:<B,G,R>:<legend> ...
import sys, json, numpy as np, cv2
REF, AX, OUT = sys.argv[1], float(sys.argv[2]), sys.argv[3]; ref = cv2.imread(REF); H, W = ref.shape[:2]
out = np.zeros((H, W + 900, 3), np.uint8); out[:, :W] = (ref * 0.6).astype(np.uint8); cv2.line(out, (int(AX), 0), (int(AX), H), (255, 255, 0), 2)
for k, spec in enumerate(sys.argv[4:]):
    f, col, txt = spec.split(":", 2); col = tuple(int(v) for v in col.split(",")); data = json.load(open(f))
    for c in (data.values() if isinstance(data, dict) else data):
        c = np.array(c["points"] if isinstance(c, dict) else c); cv2.polylines(out, [np.round(c).astype(np.int32)], False, col, 6, cv2.LINE_AA)
    y = 80 + 70 * k; cv2.line(out, (W + 40, y), (W + 120, y), col, 8); cv2.putText(out, txt, (W + 140, y + 12), 0, 1.2, (230, 230, 230), 3, cv2.LINE_AA)
cv2.imwrite(OUT, cv2.resize(out, None, fx=0.5, fy=0.5)); print(OUT)
