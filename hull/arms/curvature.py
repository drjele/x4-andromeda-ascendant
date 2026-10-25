# Curvature and section width/height along the swept paths (arm, pod, U legs and wedge, raw and smoothed): a
# plot per path, so abrupt direction or thickness changes are found on the path and not guessed from renders.
# Usage: python curvature.py <out.png> [a_params.json g_params.json]
import json, sys, numpy as np, cv2
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; sys.path.insert(0, f"{D}/arms"); from a_frame import member, catmull
A = json.load(open(sys.argv[2] if len(sys.argv) > 2 else f"{D}/arms/a_params.json"))["members"]; G = json.load(open(sys.argv[3] if len(sys.argv) > 3 else f"{D}/uarch/g_params.json"))["members"]
paths = {"arm": A["arm"], "pod": A["pod"], "leg_r": G["leg_r"], "wedge": G["wedge"]}
def curv(C):
    d1 = np.gradient(C, axis=0); d2 = np.gradient(d1, axis=0); n = np.linalg.norm(d1, axis=1)
    return np.linalg.norm(np.cross(d1, d2), axis=1) / np.maximum(n ** 3, 1e-9), np.r_[0, np.cumsum(n[1:])]
W, Hh = 1600, 400; img = np.full((Hh * len(paths), W, 3), 255, np.uint8); rows = []
for i, (name, m) in enumerate(paths.items()):
    raw = catmull(m["path"], 10); C, f, Wd, Ht, _ = member(m, 10); y0 = i * Hh
    # width (green) and height (orange) along the path, 1 px per metre, under the curvature trace
    for v, col in ((Wd, (60, 160, 60)), (Ht, (30, 120, 230))):
        pts = np.array([[int(40 + x * (W - 80)), int(y0 + Hh - 30 - v[j])] for j, x in enumerate(f)]); cv2.polylines(img, [pts], False, col, 2)
    cv2.putText(img, "green: width m, orange: height m, 1 px = 1 m", (W - 420, y0 + Hh - 10), 0, 0.45, (90, 90, 90), 1)
    for C_, col in ((raw, (200, 200, 200)), (C, (30, 30, 200))):
        k, s = curv(C_); k = k * 1000; s = s / s[-1]; pts = np.array([[int(40 + x * (W - 80)), int(y0 + 220 - min(v, 20) * 10)] for x, v in zip(s, k)])
        cv2.polylines(img, [pts], False, col, 1 if col[0] == 200 else 2)
    k, s = curv(C); k = k * 1000; spikes = [(round(float(ss), 3), round(float(kk), 2)) for ss, kk in zip(s / s[-1], k) if kk > 6]
    cv2.putText(img, f"{name}: curvature x1000 (grey raw Catmull, blue smoothed {m.get('smooth', 0)} m); max {k.max():.1f}, spikes>6: {len(spikes)}", (40, y0 + 22), 0, 0.6, (0, 0, 0), 1)
    cv2.line(img, (40, y0 + 220), (W - 40, y0 + 220), (120, 120, 120), 1); cv2.line(img, (40, y0 + Hh - 30), (W - 40, y0 + Hh - 30), (120, 120, 120), 1); rows.append((name, round(float(k.max()), 2), spikes[:12]))
cv2.imwrite(sys.argv[1], img); print(json.dumps(rows))
