# Closed rings drawn one inside the other around the centreline (a window and its frame): the stroke thinned, one half
# kept and mirrored, the points split into rings by their distance from the centre, each ring a smooth closed curve
# (median radius per angle, periodic spline), centred on the axis.
# Usage: python sketch_rings.py <lab.npy> <id> <axis_x> <half: left|right> <rings> <out.json>
import sys, json, numpy as np
from skimage.morphology import skeletonize
from scipy.interpolate import splprep, splev
LAB, ID, AX, HALF, NR, OUT = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4], int(sys.argv[5]), sys.argv[6]
ys, xs = np.nonzero(skeletonize(np.load(LAB) == ID)); keep = xs <= AX if HALF == "left" else xs >= AX
p = np.stack([xs[keep], ys[keep]], 1).astype(float); p = np.vstack([p, np.stack([2 * AX - p[:, 0], p[:, 1]], 1)])
cy = (p[:, 1].min() + p[:, 1].max()) / 2; sx, sy = np.ptp(p[:, 0]) / 2, np.ptp(p[:, 1]) / 2
ang = np.arctan2((p[:, 1] - cy) / sy, (p[:, 0] - AX) / sx); rad = np.hypot((p[:, 1] - cy) / sy, (p[:, 0] - AX) / sx)
bins = np.linspace(-np.pi, np.pi, 49); rings = [[] for _ in range(NR)]
for a, b in zip(bins[:-1], bins[1:]):
    r = np.sort(rad[(ang >= a) & (ang < b)])
    if len(r) < 2: continue
    cuts = np.argsort(np.diff(r))[-(NR - 1):] if NR > 1 else []; groups = np.split(r, np.sort(np.array(cuts, int)) + 1)
    if len(groups) != NR: continue
    for k, g in enumerate(groups): rings[k].append(((a + b) / 2, np.median(g)))
res = []
for ring in rings:
    t, r = np.array(ring).T; x = AX + r * np.cos(t) * sx; y = cy + r * np.sin(t) * sy
    q = np.stack([x, y], 1); q = np.vstack([q, q[:1]]); tck, _ = splprep([q[:, 0], q[:, 1]], s=len(q) * 4.0 ** 2, per=1, k=3)
    c = np.stack(splev(np.linspace(0, 1, 400), tck), 1); res.append(c.tolist())
json.dump(res, open(OUT, "w")); print("RINGS", [len(r) for r in rings])
