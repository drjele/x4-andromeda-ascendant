# Compare the user's traces with the parts: each stroke is matched to the part whose outline (in that view) it follows
# best, then every stroke point gets its distance to that outline, + where the part sticks out past the trace, - where
# the part falls short of it. Writes a sheet per view and a report. Usage: python compare_trace.py <export.npz> <out_dir>
import sys, json, numpy as np, cv2
from scipy.spatial import cKDTree
SRC, OUT = sys.argv[1], sys.argv[2]; Z = np.load(SRC); HALF = 1800; RES = 1.0   # canvas metres from centre, metres per pixel
N = int(2 * HALF / RES)
def px(p): return np.stack([(p[:, 0] + HALF) / RES, (HALF - p[:, 1]) / RES], 1)
strokes = {}; parts = {}
for k in Z.files:
    kind, view, name = k.split("|", 2)
    if kind == "stroke": strokes.setdefault(view, []).append(Z[k])
    elif kind == "verts": parts.setdefault(view, {})[name] = (Z[k], Z[f"tris|{view}|{name}"])
report = {}
for view, sts in strokes.items():
    masks, trees, edges = {}, {}, {}
    for name, (v, t) in parts[view].items():
        m = np.zeros((N, N), np.uint8); q = np.round(px(v)).astype(np.int32)
        cv2.fillPoly(m, list(q[t]), 1); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)); e = cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
        ys, xs = np.nonzero(e)
        if len(xs): masks[name] = m > 0; edges[name] = e; trees[name] = cKDTree(np.stack([xs, ys], 1))
    canvas = np.full((N, N, 3), 28, np.uint8)
    for e in edges.values(): canvas[e] = (90, 90, 90)
    rows = []
    for i, s in enumerate(sts):
        # resample to ~1 point per metre so long and short segments weigh the same
        seg = np.linalg.norm(np.diff(s, axis=0), axis=1); L = np.r_[0, np.cumsum(seg)]
        s = np.stack([np.interp(np.arange(0, L[-1], 1.0), L, s[:, j]) for j in (0, 1)], 1) if L[-1] > 2 else s
        p = px(s); best = min(trees, key=lambda n: trees[n].query(p)[0].mean())
        d, _ = trees[best].query(p); d = d * RES; ij = np.clip(np.round(p).astype(int), 0, N - 1)
        sign = np.where(masks[best][ij[:, 1], ij[:, 0]], 1.0, -1.0); sd = d * sign
        worst = int(np.argmax(d)); canvas[edges[best]] = (235, 235, 235)
        for (x, y), a in zip(ij, d): cv2.circle(canvas, (x, y), 2, (60, 200, 60) if a < 2 else (0, 210, 240) if a < 6 else (40, 40, 240), -1)
        cv2.putText(canvas, f"{i}: {best}  {np.mean(d):.1f} m", tuple(int(c) + 8 for c in ij[0]), 0, 0.9, (255, 255, 255), 2)
        cv2.circle(canvas, tuple(int(c) for c in ij[worst]), 9, (40, 40, 240), 2)
        rows.append({"stroke": i, "part": best, "mean_m": round(float(np.mean(d)), 1), "max_m": round(float(d[worst]), 1),
                     "max_at_m": [round(float(c), 1) for c in s[worst]], "part_bigger_share": round(float(np.mean(sd > 1)), 2),
                     "part_smaller_share": round(float(np.mean(sd < -1)), 2)})
    ys, xs = np.nonzero(canvas.max(2) > 28); pad = 40
    crop = canvas[max(ys.min() - pad, 0):ys.max() + pad, max(xs.min() - pad, 0):xs.max() + pad]
    cv2.imwrite(f"{OUT}/trace_{view}.png", crop); report[view] = rows
json.dump(report, open(f"{OUT}/trace_report.json", "w"), indent=1)
with open(f"{OUT}/trace_report.md", "w") as f:
    f.write("# Trasare vs piese\n\n+ = piesa iese peste conturul tău, - = piesa nu ajunge la contur. Coordonate în metri, în planul vederii.\n")
    for view, rows in report.items():
        f.write(f"\n## {view}\n\n| linie | piesă | medie m | max m | unde (m) | piesa mai mare | piesa mai mică |\n|---|---|---|---|---|---|---|\n")
        for r in rows: f.write(f"| {r['stroke']} | {r['part']} | {r['mean_m']} | {r['max_m']} | {r['max_at_m']} | {r['part_bigger_share']:.0%} | {r['part_smaller_share']:.0%} |\n")
print(json.dumps(report, indent=1))
