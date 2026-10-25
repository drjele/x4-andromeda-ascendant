# Lines made clean for a view: each one resampled by arc length and fitted with a smoothing spline (even, continuous
# arcs, no teeth or kinks), its ends held where they were so junctions stay joined; drawn on the clean reference.
# Usage: python clean_lines.py <view> <lines.json> <tol> <out.png>
import sys, json, numpy as np, cv2
from scipy.interpolate import splprep, splev
VIEW, LJ, TOL, OUT = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]; K = 4
src = json.load(open(LJ)); cols = [(255, 80, 255), (40, 40, 255), (0, 220, 255), (0, 255, 0)]
im = cv2.resize(cv2.imread(f"/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01/{VIEW}.png"), None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC)
out = (im * 0.8).astype(np.uint8); res = {}
if len(sys.argv) > 8:                                                      # the background shown (the negative), the lit half mirrored
    bgm = np.load(sys.argv[8]); A_ = float(sys.argv[7]); r_ = np.arange(im.shape[0]); src_ = np.clip(np.where(r_ <= A_, r_, np.round(2 * A_ - r_).astype(int)), 0, im.shape[0] - 1)
    out = im[src_].copy(); out[bgm] = (0, 170, 0)
def fit(c):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]; keep = np.r_[True, np.diff(d) > 1e-6]; c, d = c[keep], d[keep]
    if d[-1] < 20 or len(c) < 6: return c
    t = np.linspace(0, d[-1], max(int(d[-1] / 5), 8)); q = np.stack([np.interp(t, d, c[:, i]) for i in (0, 1)], 1)
    closed = np.hypot(*(q[0] - q[-1])) < 4
    if closed: q[-1] = q[0]
    w = np.ones(len(q)); w[[0, -1]] = 1 if closed else 60
    tck, _ = splprep([q[:, 0], q[:, 1]], w=w, s=len(q) * TOL ** 2, per=1 if closed else 0, k=3 if len(q) > 4 else 1)
    return np.stack(splev(np.linspace(0, 1, max(80, int(d[-1] / 2))), tck), 1)
JOIN = float(sys.argv[5]) if len(sys.argv) > 5 else 0; JOIN_GROUPS = [int(x) for x in sys.argv[6].split(",") if x] if len(sys.argv) > 6 else []
def merge(lines):
    # lines whose ends meet within JOIN px joined into one (the gaps left at the centreline and between pieces)
    L = [np.array(c, float) for c in lines]
    while True:
        best = None
        for i in range(len(L)):
            for j in range(len(L)):
                if i == j: continue
                for a, b, d in ((-1, 0, np.hypot(*(L[i][-1] - L[j][0]))), (-1, -1, np.hypot(*(L[i][-1] - L[j][-1])))):
                    if d < JOIN and (best is None or d < best[0]): best = (d, i, j, b)
        if best is None: return L
        _, i, j, b = best; nj = L[j] if b == 0 else L[j][::-1]; L[i] = np.vstack([L[i], nj]); L.pop(j)
AXIS = float(sys.argv[7]) if len(sys.argv) > 7 else None
def across(lines):
    # the mirrored halves come in pairs (line, mirror): a line ending near the axis is joined to its own mirror into
    # one continuous curve through the axis
    L = [np.array(c, float) for c in lines]; out_ = []
    for i in range(0, len(L) - 1, 2):
        a, b = L[i], L[i + 1]; ends = [(abs(a[e][1] - AXIS), e) for e in (0, -1)]; d, e = min(ends)
        if d < 40:
            a2 = a if e == -1 else a[::-1]; b2 = b[::-1] if e == -1 else b
            out_.append(np.vstack([a2, b2]))
            o = 0 if e == -1 else -1                                        # the other end may touch the axis too (a closed ring)
            if abs(a2[0][1] - AXIS) < 40: out_[-1] = np.vstack([out_[-1], out_[-1][:1]])
        else: out_ += [a, b]
    return out_
for n, (path, lines) in enumerate(src.items()):
    res[path] = []
    if AXIS is not None: lines = across(lines)
    if JOIN and n in JOIN_GROUPS: lines = merge(lines)
    for c in lines:
        f = fit(np.array(c, float)); res[path].append(f.tolist()); cv2.polylines(out, [np.round(f).astype(np.int32)], False, cols[n % len(cols)], 5, cv2.LINE_AA)
json.dump(res, open(OUT.replace(".png", ".json"), "w")); cv2.imwrite(OUT, cv2.resize(out, None, fx=0.5, fy=0.5)); print("CLEAN", sum(len(v) for v in res.values()), "lines")
