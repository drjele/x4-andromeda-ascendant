# A view's outlines from the user's drawing, joined and numbered: the fitted hand lines (all of them, the outer outline
# too; the drawing wins over the contrast) are taken on one half; a point running within PULL px of the reference's
# edge is drawn part of the way onto it (the negative refines a line that already follows that edge, never adds a
# notch); line ends meeting at a junction are clustered into one node; pieces are joined through each node, a node of
# two straight on, a crossing by its most opposite pair, so every outline runs whole; ends on the centreline are joined
# with their mirror twin; each line gets one even smoothing spline (ends held on their nodes), the half is mirrored
# and every line numbered (the twin carries the same number) for the user to adjust by number.
# Usage: python view_lines.py <ref.png> <axis> <h|v> <upper|lower|left|right> <out_prefix> [bg.npy] -- <network.json> ... [full:<rings.json>]
#        full: = curves already whole and symmetric (rings from sketch_rings.py), numbered as they are
import sys, json, numpy as np, cv2
from scipy.interpolate import splprep, splev
from scipy.ndimage import distance_transform_edt
i = sys.argv.index("--"); REF, AX, AD, HALF, OP = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
BG = sys.argv[6] if i > 6 else None; NETS = sys.argv[i + 1:]
PULL, NODE, TOL, STRAIGHT, REACH = 20.0, 14.0, 4.0, 145.0, 70.0
ref = cv2.imread(REF); H, W = ref.shape[:2]
def tr(c): return c[:, ::-1] if AD == "v" else c                         # work with the axis as a row (y = AX)
keep_lo = HALF in ("upper", "left")
pieces = []
FULL = [f[5:] for f in NETS if f.startswith("full:")]; NETS = [f for f in NETS if not f.startswith("full:")]
for f in NETS:
    for c in json.load(open(f)):
        c = tr(np.array(c, float))
        if (keep_lo and c[:, 1].max() <= AX + 2) or (not keep_lo and c[:, 1].min() >= AX - 2): pieces.append(c)
if BG:                                                                     # the edge of the background, in the working frame
    bg = np.load(BG); bg = bg.T if AD == "v" else bg
    edge = bg & ~cv2.erode(bg.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    d, (iy, ix) = distance_transform_edt(~edge, return_indices=True)
    for k, c in enumerate(pieces):
        yi = np.clip(np.round(c[:, 1]).astype(int), 0, d.shape[0] - 1); xi = np.clip(np.round(c[:, 0]).astype(int), 0, d.shape[1] - 1)
        w = np.clip(0.5 * (1 - d[yi, xi] / PULL), 0, None)[:, None]
        pieces[k] = c * (1 - w) + np.stack([ix[yi, xi], iy[yi, xi]], 1) * w
# nodes: line ends within NODE px are one junction
ends = [(k, e, pieces[k][e]) for k in range(len(pieces)) for e in (0, -1)]; grp = list(range(len(ends)))
def root(a):
    while grp[a] != a: a = grp[a]
    return a
for a in range(len(ends)):
    for b in range(a + 1, len(ends)):
        if np.hypot(*(ends[a][2] - ends[b][2])) < NODE: grp[root(b)] = root(a)
node = {}; pos = {}
for a, (k, e, p) in enumerate(ends): node[(k, e)] = root(a); pos.setdefault(root(a), []).append(p)
pos = {n: np.mean(v, 0) for n, v in pos.items()}
for (k, e), n in node.items():
    if abs(pos[n][1] - AX) < 4: pos[n][1] = AX                              # an end on the centreline stays exactly on it
    pieces[k][e] = pos[n]
# join pieces through their nodes
lines = [{"pts": c, "a": node[(k, 0)], "b": node[(k, -1)]} for k, c in enumerate(pieces)]
def out_dir(l, at_a):                                                      # direction leaving the node, ~40 px along the line
    c = l["pts"] if at_a else l["pts"][::-1]; s = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]; j = min(np.searchsorted(s, 40), len(c) - 1)
    v = c[j] - c[0]; return v / max(np.linalg.norm(v), 1e-9)
changed = True
while changed:
    changed = False; inc = {}
    for li, l in enumerate(lines):
        if l["a"] == l["b"] and len(l["pts"]) > 2 and np.hypot(*(l["pts"][0] - l["pts"][-1])) < 1: continue   # already a closed loop
        inc.setdefault(l["a"], []).append((li, True)); inc.setdefault(l["b"], []).append((li, False))
    for n, lst in inc.items():
        if len(lst) < 2 or abs(pos[n][1] - AX) < 1: continue
        if len(lst) == 2: pair = lst
        else:
            best = None
            for x in range(len(lst)):
                for y in range(x + 1, len(lst)):
                    if lst[x][0] == lst[y][0]: continue
                    ang = np.degrees(np.arccos(np.clip(np.dot(out_dir(lines[lst[x][0]], lst[x][1]), out_dir(lines[lst[y][0]], lst[y][1])), -1, 1)))
                    if ang > STRAIGHT and (best is None or ang > best[0]): best = (ang, [lst[x], lst[y]])
            if best is None: continue
            pair = best[1]
        (p, pa), (q, qa) = pair
        if p == q:                                                         # both ends of one line: it closes on itself
            lines[p]["a"] = lines[p]["b"] = n; changed = True; break
        A = lines[p]["pts"] if not pa else lines[p]["pts"][::-1]           # A ends at the node
        B = lines[q]["pts"] if qa else lines[q]["pts"][::-1]               # B starts at the node
        na = lines[p]["b"] if pa else lines[p]["a"]; nb = lines[q]["b"] if qa else lines[q]["a"]
        lines[p] = {"pts": np.vstack([A, B[1:]]), "a": na, "b": nb}; del lines[q]; changed = True; break
# a free end (not on a junction) that stops short of another line is carried on to it, straight, so outlines close
deg = {}
for l in lines: deg[l["a"]] = deg.get(l["a"], 0) + 1; deg[l["b"]] = deg.get(l["b"], 0) + 1
for li, l in enumerate(lines):
    for at_a in (True, False):
        nd = l["a"] if at_a else l["b"]
        if deg.get(nd, 0) > 1 or abs(pos[nd][1] - AX) < 1: continue
        p = l["pts"][0] if at_a else l["pts"][-1]; best = None
        for lj, o in enumerate(lines):
            q = o["pts"] if lj != li else (o["pts"][len(o["pts"]) // 4:] if at_a else o["pts"][:-len(o["pts"]) // 4])
            d_ = np.hypot(*(q - p).T); k_ = int(np.argmin(d_))
            if d_[k_] < REACH and (best is None or d_[k_] < best[0]): best = (d_[k_], q[k_])
        if best is not None and best[0] > 1:
            seg = np.linspace(p, best[1], 10)[1:]; l["pts"] = np.vstack([seg[::-1], l["pts"]]) if at_a else np.vstack([l["pts"], seg])
def smooth(c, closed):
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]; keep = np.r_[True, np.diff(s) > 1e-6]; c, s = c[keep], s[keep]
    if s[-1] < 12: return c
    t = np.linspace(0, s[-1], max(int(s[-1] / 4), 8)); q = np.stack([np.interp(t, s, c[:, j]) for j in (0, 1)], 1)
    if closed: q = q[:-1] if np.hypot(*(q[-1] - q[0])) < 2 else q; q = np.vstack([q, q[:1]])
    w = np.ones(len(q)); w[[0, -1]] = 1 if closed else 100
    tck, _ = splprep([q[:, 0], q[:, 1]], w=w, s=len(q) * TOL ** 2, per=1 if closed else 0, k=3 if len(q) > 4 else 1)
    r = np.stack(splev(np.linspace(0, 1, max(80, int(s[-1] / 2))), tck), 1)
    if not closed: r[0], r[-1] = c[0], c[-1]
    return r
res = []
for l in lines:
    c = l["pts"]; on0, on1 = abs(c[0][1] - AX) < 1, abs(c[-1][1] - AX) < 1; m = lambda p: np.stack([p[:, 0], 2 * AX - p[:, 1]], 1)
    if on0 and on1: full = smooth(np.vstack([c, m(c)[::-1][1:]]), True); res.append([full])           # both ends on the axis: one closed curve
    elif on0 or on1:
        cc = c if on1 else c[::-1]; full = smooth(np.vstack([cc, m(cc)[::-1][1:]]), False); res.append([full])   # crosses the axis: one curve
    else:
        closed = l["a"] == l["b"] and np.hypot(*(c[0] - c[-1])) < 1; sm = smooth(c, closed); res.append([sm, m(sm)])
for f in FULL: res += [[tr(np.array(c, float))] for c in json.load(open(f))]
# number from the front/top-left, the half's lines first
order = sorted(range(len(res)), key=lambda j: (np.round(res[j][0][:, 1].mean() / 150), res[j][0][:, 0].mean()))
out = (ref * 0.7).astype(np.uint8)
if BG: b = np.load(BG); out[b] = (0, 150, 0)
data = []
for num, j in enumerate(order, 1):
    for c in res[j]:
        cw = tr(c); cv2.polylines(out, [np.round(cw).astype(np.int32)], False, (0, 220, 255), 5, cv2.LINE_AA)
    c0 = tr(res[j][0]); p = c0[len(c0) // 2]; t = str(num)
    cv2.circle(out, (int(p[0]), int(p[1])), 26, (255, 255, 255), -1); cv2.putText(out, t, (int(p[0]) - 10 * len(t), int(p[1]) + 10), 0, 0.95, (0, 0, 0), 3)
    data.append({"n": num, "curves": [tr(c).tolist() for c in res[j]]})
json.dump(data, open(f"{OP}_linii.json", "w")); cv2.imwrite(f"{OP}_linii_numerotate.png", cv2.resize(out, None, fx=0.5, fy=0.5)); print("LINES", len(data))
