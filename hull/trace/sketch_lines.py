# The user's hand-drawn outlines as smooth curves: each pen stroke component thinned to a centre line, short side
# branches pruned, walked whole (closed strokes all the way round, open ones end to end), pieces of one line joined
# across small gaps, then fitted with a smoothing spline with few knots so the curve is an even arc (hand lines are
# meant as continuous, elliptical pieces). Drawn over the dimmed reference with the raw strokes faint underneath.
# Usage: python sketch_lines.py <dir> <view> <labels.json> <out.png>
import sys, json, numpy as np, cv2
from skimage.morphology import skeletonize
from scipy.interpolate import splprep, splev
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import shortest_path
D, VIEW, LAB, OUT = sys.argv[1:5]; R = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"; K = 4
L = json.load(open(LAB)); SPUR, GAP = L.get("spur", 40), L.get("gap", 70)
NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
def neighbours(S, p): return [(p[0] + a, p[1] + b) for a, b in NB if (p[0] + a, p[1] + b) in S]
def prune(S):
    # drop side branches shorter than SPUR (walk in from each end point; stop at a junction)
    for _ in range(3):
        ends = [p for p in S if len(neighbours(S, p)) == 1]; cut = False
        for e in ends:
            run, q, prev = [e], e, None
            while True:
                nb = [n for n in neighbours(S, q) if n != prev]
                if len(nb) != 1 or len(run) > SPUR: break
                prev, q = q, nb[0]; run.append(q)
            if len(run) <= SPUR and len(neighbours(S, q)) >= 3: S.difference_update(run[:-1]); cut = True
        if not cut: break
    return S
def walk(S, near=None):
    # order the centre line: round the loop when it has no end points, else the longest route between two end points
    ends = [p for p in S if len(neighbours(S, p)) == 1]
    if not ends:
        start = next(iter(S)); path, seen, q = [start], {start}, start
        while True:
            nb = [n for n in neighbours(S, q) if n not in seen]
            if not nb: break
            if len(path) > 2: d = np.subtract(q, path[-3]); nb.sort(key=lambda n: -np.dot(np.subtract(n, q), d))
            q = nb[0]; seen.add(q); path.append(q)
        return np.array(path, float)[:, ::-1], True
    pts = list(S); idx = {p: i for i, p in enumerate(pts)}; r, c, w = [], [], []
    for p in pts:
        for n in neighbours(S, p): r.append(idx[p]); c.append(idx[n]); w.append(np.hypot(*np.subtract(n, p)))
    G = coo_matrix((w, (r, c)), shape=(len(pts), len(pts))).tocsr(); E = [idx[e] for e in ends]
    d = shortest_path(G, indices=E); d[np.isinf(d)] = -1
    if near is not None and len(E) > 1:                                  # the route must end at the end point nearest `near`
        j = int(np.argmin([np.hypot(pts[e][1] - near[0], pts[e][0] - near[1]) for e in E])); i = int(np.argmax(d[:, E][:, j])); a, b = E[i], E[j]
    elif len(E) > 1: i, j = np.unravel_index(np.argmax(d[:, E]), (len(E), len(E))); a, b = E[i], E[j]
    else: a, b = E[0], int(np.argmax(d[0]))                              # one end point: to the farthest point
    _, pred = shortest_path(G, indices=a, return_predecessors=True); path = [b]
    while path[-1] != a and pred[path[-1]] >= 0: path.append(pred[path[-1]])
    return np.array([pts[k] for k in path], float)[:, ::-1], False
def fit(p, closed, knots_per_px):
    step = max(1, len(p) // 400); p = p[::step]
    if closed: p = np.vstack([p, p[:1]])
    n = max(6, int(len(p) * step * knots_per_px)); s = len(p) * (L.get("tol", 6.0)) ** 2
    tck, _ = splprep([p[:, 0], p[:, 1]], s=s, per=1 if closed else 0, k=3, nest=n + 8)
    return np.stack(splev(np.linspace(0, 1, 1500), tck), 1)
ref = cv2.imread(f"{R}/{VIEW}.png"); out = cv2.resize(ref, None, fx=K, fy=K) // 3; curves = {}; rest = {}; style = {}
if not L.get("clean_bg"):                                                 # the raw strokes faint underneath (off on a clean reference)
    for pen in {i["pen"] for i in L["lines"]}:
        raw = np.load(f"{D}/{pen}_mask.npy"); out[raw] = (out[raw] * 0.4 + np.array((90, 90, 90))).astype(np.uint8)
else: out = (cv2.resize(ref, None, fx=K, fy=K) * 0.75).astype(np.uint8)
for item in L["lines"]:
    lab = np.load(f"{D}/{item['pen']}_lab.npy"); pieces = []
    for cid in (item["id"] if isinstance(item["id"], list) else [item["id"]]):
        S = set(map(tuple, np.argwhere(skeletonize(lab == cid)))); S = prune(S); w = walk(S, item.get("end_near")); pieces.append(w)
        if item.get("rest_as"):                                            # the branch left over after the main route, as a line of its own
            on = {(int(round(y)), int(round(x))) for x, y in w[0]}; near = {(a + dy, b + dx) for a, b in on for dy in range(-4, 5) for dx in range(-4, 5)}
            R_ = S - near
            if len(R_) > 50:
                from scipy.ndimage import label as _lbl
                arr = np.zeros(lab.shape, bool); arr[tuple(np.array(list(R_)).T)] = True; ll, nn = _lbl(arr, np.ones((3, 3)))
                big = 1 + int(np.argmax(np.bincount(ll.ravel())[1:])); rest[item["rest_as"]] = walk(set(map(tuple, np.argwhere(ll == big))))
    # join the pieces of one line end to end (nearest ends first)
    path, closed = pieces[0]
    for p, _ in pieces[1:]:
        ends = [(np.hypot(*(path[-1] - p[0])), path, p), (np.hypot(*(path[-1] - p[-1])), path, p[::-1]), (np.hypot(*(path[0] - p[-1])), p, path), (np.hypot(*(path[0] - p[0])), p[::-1], path)]
        d, a, b = min(ends, key=lambda t: t[0]); path = np.vstack([a, b]); closed = False
    closed = closed or item.get("closed", False)
    pins = []
    for other in item.get("meet", []):                                    # an end carried on to touch another drawn line
        other, side = (other, None) if isinstance(other, str) else other   # side picks the end: left/right/top/bottom
        if isinstance(other, list): o = np.array([other], float)           # a fixed point ([x, y], ref-crop px x4) instead of a line
        else: o = np.array(curves[other]["points"])
        if side: key = {"left": lambda p: p[0], "right": lambda p: -p[0], "top": lambda p: p[1], "bottom": lambda p: -p[1]}[side]; e = 0 if key(path[0]) < key(path[-1]) else -1
        else: e = min(((np.min(np.hypot(*(o - path[0]).T)), 0), (np.min(np.hypot(*(o - path[-1]).T)), -1)))[1]
        q = o[np.argmin(np.hypot(*(o - path[e]).T))]; seg = np.linspace(path[e], q, 20)[1:]
        path = np.vstack([seg[::-1], path]) if e == 0 else np.vstack([path, seg]); pins.append(q)
    c = fit(path, closed, L.get("knots_per_px", 1 / 90))
    for q in pins:                                                         # the smoothing pulls ends off their target: put them back on it
        if np.hypot(*(c[0] - q)) < np.hypot(*(c[-1] - q)): c = np.vstack([q, c])
        else: c = np.vstack([c, q])
    curves[item["name"]] = {"points": c.tolist(), "closed": closed}; col = tuple(item["colour"])
    style[item["name"]] = (col, item["label"])
for name, (path, _) in rest.items():
    it = next(i for i in L["lines"] if i.get("rest_as") == name); col = tuple(it.get("rest_colour", it["colour"]))
    c = fit(path, False, L.get("knots_per_px", 1 / 90)); curves[name] = {"points": c.tolist(), "closed": False}
    style[name] = (col, it.get("rest_label", name))
for spec in L.get("extend_lines", []):
    name, side, target = spec[:3]; fixed = spec[3] if len(spec) > 3 else None; spec_trim = spec[4] if len(spec) > 4 and spec[4] is not None else 0.04; follow = len(spec) > 5 and spec[5]   # follow = keep turning with the end's curvature; optional fixed direction [dx, dy], share of the end dropped                       # an end carried on along its own direction until it reaches another line
    c = np.array(curves[name]["points"]); o = np.array(curves[target]["points"])
    key = {"left": lambda p: p[0], "right": lambda p: -p[0], "top": lambda p: p[1], "bottom": lambda p: -p[1]}[side]
    e = 0 if key(c[0]) < key(c[-1]) else -1; cc = c if e == -1 else c[::-1]; n = len(cc); cc = cc[:int(n * (1 - spec_trim))]; p0 = cc[-1]; c = cc if e == -1 else cc[::-1]   # the hook at the very end dropped
    # the line's general slope near that end (a hook in the last few percent of the stroke does not count)
    a, b = cc[int(len(cc) * 0.75)], cc[-1]; nearest = fixed == "nearest"; fixed = None if nearest else fixed
    d = np.array(fixed, float) if fixed else (b - a); d = d / np.linalg.norm(d); seg = []; hit = False
    if nearest:                                                            # the shortest way to the other line, leaving tangent to this one (a quadratic curve)
        q = o[np.argmin(np.hypot(*(o - p0).T))]; ctl = p0 + d * np.hypot(*(q - p0)) * 0.5; t_ = np.linspace(0, 1, 40)[1:, None]
        seg = list((1 - t_) ** 2 * p0 + 2 * (1 - t_) * t_ * ctl + t_ ** 2 * q); hit = True
    kappa = 0.0
    if follow:                                                             # the turning rate over the last stretch, carried on
        m = cc[int(len(cc) * 0.7):]; tg = np.diff(m, axis=0); ang = np.unwrap(np.arctan2(tg[:, 1], tg[:, 0])); L_ = np.sum(np.linalg.norm(tg, axis=1))
        kappa = (ang[-1] - ang[0]) / max(L_, 1e-6); d = tg[-5:].sum(0); d = d / np.linalg.norm(d)
    q = p0.copy()
    for t in range(2, 1200 if not hit else 2, 2):
        q = q + d * 2; seg.append(q.copy())
        if kappa: a_ = kappa * 2; d = np.array([d[0] * np.cos(a_) - d[1] * np.sin(a_), d[0] * np.sin(a_) + d[1] * np.cos(a_)])
        if np.min(np.hypot(*(o - q).T)) < 3: hit = True; break
    if not hit: q = o[np.argmin(np.hypot(*(o - p0).T))]; seg = list(np.linspace(p0, q, 40)[1:])   # no crossing: straight to the nearest point
    seg = np.array(seg); curves[name]["points"] = (np.vstack([seg[::-1], c]) if e == 0 else np.vstack([c, seg])).tolist()
def refit(c, closed, tol):
    # one even curve through the whole line, joins included: resampled by arc length, a smoothing spline with the ends held
    c = np.array(c, float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]; keep = np.r_[True, np.diff(d) > 1e-6]; c, d = c[keep], d[keep]
    t = np.linspace(0, d[-1], max(int(d[-1] / 4), 20)); q = np.stack([np.interp(t, d, c[:, i]) for i in (0, 1)], 1)
    if closed:
        while len(q) > 3 and np.hypot(*(q[-1] - q[0])) < 2: q = q[:-1]
        q = np.vstack([q, q[:1]])
    w = np.ones(len(q)); w[[0, -1]] = 50 if not closed else 1
    tck, _ = splprep([q[:, 0], q[:, 1]], w=w, s=len(q) * tol ** 2, per=1 if closed else 0, k=3)
    return np.stack(splev(np.linspace(0, 1, 2000), tck), 1)
if L.get("clean"):
    tols = {i["name"]: i.get("clean_tol") for i in L["lines"]}
    for name, c in curves.items(): c["points"] = refit(c["points"], c["closed"], tols.get(name) or L.get("clean_tol", 5.0)).tolist()
for name, side, dx, dy, rad in L.get("tips", []):                         # a tip pulled toward the reference and sharpened: the move fades with arc distance from the tip
    c = np.array(curves[name]["points"]); i = np.argmin(c[:, 0]) if side == "left" else np.argmax(c[:, 0])
    seg = np.hypot(*np.diff(c, axis=0).T); d = np.abs(np.r_[0, np.cumsum(seg)] - np.r_[0, np.cumsum(seg)][i])
    if curves[name]["closed"]: d = np.minimum(d, seg.sum() - d)
    w = np.clip(1 - d / rad, 0, 1) ** 3; c = c + np.outer(w, [dx, dy]); curves[name]["points"] = c.tolist()
for name, side, rad, sig in L.get("round_tips", []):                       # a tip rounded a little: smoothing along the line near it only
    c = np.array(curves[name]["points"]); n = len(c); i = np.argmin(c[:, 0]) if side == "left" else np.argmax(c[:, 0])
    idx = np.arange(n); k = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2); k /= k.sum()
    pad = np.vstack([c[-3 * sig:], c, c[:3 * sig]]) if curves[name]["closed"] else np.vstack([np.repeat(c[:1], 3 * sig, 0), c, np.repeat(c[-1:], 3 * sig, 0)])
    sm = np.stack([np.convolve(pad[:, j], k, "valid") for j in (0, 1)], 1)
    dd = np.abs(idx - i); dd = np.minimum(dd, n - dd) if curves[name]["closed"] else dd; w = np.clip(1 - dd / rad, 0, 1)[:, None] ** 2
    curves[name]["points"] = (c * (1 - w) + sm * w).tolist()
for name, c in curves.items():
    col, label = style[name]; c_ = np.array(c["points"])
    cv2.polylines(out, [np.round(c_).astype(np.int32)], c["closed"], col, 6, cv2.LINE_AA); q = c_[len(c_) // 2]
    cv2.putText(out, label, (int(q[0]) + 10, int(q[1]) - 10), 0, 1.5, col, 4, cv2.LINE_AA)
json.dump(curves, open(f"{D}/{VIEW}_curves.json", "w")); cv2.imwrite(OUT, cv2.resize(out, None, fx=0.5, fy=0.5)); print("LINES", len(curves))
