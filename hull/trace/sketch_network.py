# The user's hand-drawn outlines as a clean network: the chosen pen components thinned to centre lines, short spurs
# pruned, the skeleton split at its junctions into branches, each branch fitted with a smoothing spline whose ends stay
# on the junctions (so the lines stay joined), small gaps between branch ends closed. For drawings where the outlines
# cross and branch (the views from above/below), where one walk per stroke cannot follow them.
# Usage: python sketch_network.py <dir> <view> <net.json> <out.png>
import sys, json, numpy as np, cv2
from skimage.morphology import skeletonize
from scipy.interpolate import splprep, splev
D, VIEW, NJ, OUT = sys.argv[1:5]; R = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"; K = 4
N = json.load(open(NJ)); SPUR, TOL, GAP = N.get("spur", 45), N.get("tol", 5.0), N.get("gap", 40)
NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
ref = cv2.imread(f"{R}/{VIEW}.png"); H, W = ref.shape[0] * K, ref.shape[1] * K
mask = np.zeros((H, W), bool)
for pen, ids in N["pens"].items():
    lab = np.load(f"{D}/{pen}_lab.npy")
    for i in ids: mask |= lab == i
mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0     # strokes drawn twice side by side read as one
if N.get("half"):
    # one half of a symmetric view processed on its own (the strokes past the centreline dropped); the result is
    # mirrored at the end, so the user picks the half drawn better
    sil = cv2.resize((cv2.imread(f"{R}/{VIEW}_mask.png", 0) > 127).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    rows = np.nonzero(sil.any(1))[0]; best = None
    for a2 in range(2 * rows.min() + 20, 2 * rows.max() - 20, 2):
        idx = a2 - np.arange(H); ok = (idx >= 0) & (idx < H); f = np.zeros_like(sil); f[ok] = sil[idx[ok]]
        sc = (f & sil).sum() / max((f | sil).sum(), 1)
        if best is None or sc > best[0]: best = (sc, a2)
    AX = best[1] / 2
    if N["half"] == "upper": mask[int(np.ceil(AX)):] = False
    else: mask[:int(np.floor(AX)) + 1] = False
    print("half %s, axis row %.1f" % (N["half"], AX))
if N.get("mirror"):
    # the ship is symmetric about its centreline (a row here): the axis found on the reference silhouette, then each
    # stroke paired with its mirror image through distance fields, the band between a line and its mirrored twin
    # thinned to the line halfway between them, so both halves come out the same
    from scipy.ndimage import distance_transform_edt
    sil = cv2.resize((cv2.imread(f"{R}/{VIEW}_mask.png", 0) > 127).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    rows = np.nonzero(sil.any(1))[0]; best = None
    for ax2 in range(2 * rows.min() + 20, 2 * rows.max() - 20, 2):        # axis at ax2 / 2 (half pixels)
        idx = ax2 - np.arange(H); ok = (idx >= 0) & (idx < H); f = np.zeros_like(sil); f[ok] = sil[idx[ok]]
        sc = (f & sil).sum() / max((f | sil).sum(), 1)
        if best is None or sc > best[0]: best = (sc, ax2)
    ax2 = best[1]; idx = np.clip(ax2 - np.arange(H), 0, H - 1); flip = mask[idx]
    d1 = distance_transform_edt(~mask); d2 = distance_transform_edt(~flip); band = (d1 + d2) < N.get("pair", 45)
    band &= (np.minimum(d1, d2) < N.get("pair", 45) / 2 + 4)
    mask = cv2.morphologyEx(band.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
    print("mirror axis row %.1f (silhouette IoU %.3f)" % (ax2 / 2, best[0]))
S = set(map(tuple, np.argwhere(skeletonize(mask))))
nbr = lambda p: [(p[0] + a, p[1] + b) for a, b in NB if (p[0] + a, p[1] + b) in S]
for _ in range(4):                                                         # spurs off
    cut = False
    for e in [p for p in S if len(nbr(p)) == 1]:
        run, q, prev = [e], e, None
        while True:
            nb = [n for n in nbr(q) if n != prev]
            if len(nb) != 1 or len(run) > SPUR: break
            prev, q = q, nb[0]; run.append(q)
        if len(run) <= SPUR and len(nbr(q)) >= 3: S.difference_update(run[:-1]); cut = True
    if not cut: break
# junction clusters (adjacent junction pixels are one node) and the branches between them
J = {p for p in S if len(nbr(p)) >= 3}; node = {}; centres = []
for p in J:
    if p in node: continue
    stack, comp = [p], []
    while stack:
        q = stack.pop()
        if q in node: continue
        node[q] = len(centres); comp.append(q); stack += [n for n in nbr(q) if n in J and n not in node]
    centres.append(np.mean(comp, 0)[::-1])
seen = set(); branches = []
starts = [(j, n) for j in J for n in nbr(j) if n not in J] + [(e, None) for e in S if len(nbr(e)) == 1]
for a, first in starts:
    path = [a] if first else []; q = first or a; prev = a if first else None
    if first and (a, first) in seen: continue
    while True:
        path.append(q); seen.add((prev, q)) if prev else None
        if q in J and len(path) > 1: break
        nb = [n for n in nbr(q) if n != prev and (len(path) < 2 or n != path[-2])]
        nb = [n for n in nb if n not in path[-3:]]
        if not nb: break
        prev, q = q, nb[0]
    if len(path) < 6: continue
    key = (path[0], path[-1]) if path[0] <= path[-1] else (path[-1], path[0])
    if any(k == key and abs(len(b) - len(path)) < 5 for k, b in [((b[0], b[-1]) if b[0] <= b[-1] else (b[-1], b[0]), b) for b in branches]): continue
    branches.append(path)
loops = S - {p for b in branches for p in b}                              # closed rings with no junction
# junctions closer than "merge" are one crossing (the two drawn halves crossed at slightly different places): their
# nodes merged, the short branches inside the merged crossing dropped, the rest pinned on its centre
MG = N.get("merge", 0); grp = list(range(len(centres)))
def root(i):
    while grp[i] != i: i = grp[i]
    return i
for i in range(len(centres)):
    for j in range(i + 1, len(centres)):
        if np.hypot(*(centres[i] - centres[j])) < MG: grp[root(j)] = root(i)
cl = {}
for i in range(len(centres)): cl.setdefault(root(i), []).append(i)
newc = {r: np.mean([centres[i] for i in m], 0) for r, m in cl.items()}
for q, i in list(node.items()): node[q] = root(i)
centres = [newc.get(i, centres[i]) for i in range(len(centres))]
branches = [b for b in branches if not (b[0] in node and b[-1] in node and node[b[0]] == node[b[-1]] and len(b) < 3 * MG)]
def fit(p, closed):
    p = np.array(p, float)[:, ::-1]; d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    if d[-1] < 10: return p
    t = np.linspace(0, d[-1], max(int(d[-1] / 4), 8)); q = np.stack([np.interp(t, d, p[:, i]) for i in (0, 1)], 1)
    if closed: q = np.vstack([q[:-1], q[:1]]) if np.hypot(*(q[-1] - q[0])) < 3 else np.vstack([q, q[:1]])
    w = np.ones(len(q)); w[[0, -1]] = 1 if closed else 100
    k = 3 if len(q) > 4 else 1
    tck, _ = splprep([q[:, 0], q[:, 1]], w=w, s=len(q) * TOL ** 2, per=1 if closed else 0, k=k)
    return np.stack(splev(np.linspace(0, 1, max(60, int(d[-1] / 2))), tck), 1)
for pt in N.get("drop_near", []):                                          # branches the user marked as not there (by a point on them)
    branches = [b for b in branches if np.hypot(*(np.array(b[len(b) // 2])[::-1] - pt)) > 25]   # by the branch's middle, so its neighbours at the same junction stay
curves = []; pinned = set()
for b in branches:
    c = fit(b, False); pinned.update({(len(curves), e) for e in (0, -1) if b[e] in node})
    for end in (0, -1):                                                    # ends pinned on the junction centre
        if b[end] in node: c[end] = centres[node[b[end]]]
    curves.append(c)
if len(loops) > 30:
    from scipy.ndimage import label as lbl
    arr = np.zeros((H, W), bool); arr[tuple(np.array(list(loops)).T)] = True; ll, nn = lbl(arr, np.ones((3, 3)))
    for k_ in range(1, nn + 1):
        pts = set(map(tuple, np.argwhere(ll == k_)))
        if len(pts) < 30: continue
        start = next(iter(pts)); path, seenp, q = [start], {start}, start
        while True:
            nb = [n for n in [(q[0] + a, q[1] + b) for a, b in NB] if n in pts and n not in seenp]
            if not nb: break
            q = nb[0]; seenp.add(q); path.append(q)
        curves.append(fit(path, True))
joins = N.get("joins", [])
if N.get("half"):
    # one half of a symmetric view processed on its own (the strokes past the centreline dropped); the result is
    # mirrored at the end, so the user picks the half drawn better
    sil = cv2.resize((cv2.imread(f"{R}/{VIEW}_mask.png", 0) > 127).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    rows = np.nonzero(sil.any(1))[0]; best = None
    for a2 in range(2 * rows.min() + 20, 2 * rows.max() - 20, 2):
        idx = a2 - np.arange(H); ok = (idx >= 0) & (idx < H); f = np.zeros_like(sil); f[ok] = sil[idx[ok]]
        sc = (f & sil).sum() / max((f | sil).sum(), 1)
        if best is None or sc > best[0]: best = (sc, a2)
    AX = best[1] / 2
    if N["half"] == "upper": mask[int(np.ceil(AX)):] = False
    else: mask[:int(np.floor(AX)) + 1] = False
    print("half %s, axis row %.1f" % (N["half"], AX))
if N.get("mirror"): joins = joins + [[[a_[0], ax2 - a_[1]], [b_[0], ax2 - b_[1]]] for a_, b_ in joins]   # each hand join mirrored too
for a_, b_ in joins:                                         # hand-given joins: the line end nearest a_ carried to the line nearest b_ (a smooth curve)
    a_, b_ = np.array(a_, float), np.array(b_, float)
    ci, e = min(((ci, e) for ci, c in enumerate(curves) for e in (0, -1)), key=lambda t: np.hypot(*(curves[t[0]][t[1]] - a_)))
    cj = min(range(len(curves)), key=lambda j: np.min(np.hypot(*(curves[j] - b_).T)) if j != ci else 1e9); q = curves[cj][np.argmin(np.hypot(*(curves[cj] - b_).T))]
    p0 = curves[ci][e]; tan = (curves[ci][-1] - curves[ci][-8]) if e == -1 else (curves[ci][0] - curves[ci][7]); tan = tan / max(np.linalg.norm(tan), 1e-9)
    ctl = p0 + tan * np.hypot(*(q - p0)) * 0.5; t_ = np.linspace(0, 1, 30)[1:, None]; seg = (1 - t_) ** 2 * p0 + 2 * (1 - t_) * t_ * ctl + t_ ** 2 * q
    curves[ci] = np.vstack([curves[ci], seg]) if e == -1 else np.vstack([seg[::-1], curves[ci]])
# free ends joined to the nearest line within GAP (this network's own lines, and those of the networks named in "meet")
others = [np.array(c) for f in N.get("meet", []) for c in json.load(open(f"{D}/{f}"))]
ends = [(ci, e) for ci, c in enumerate(curves) for e in (0, -1) if np.hypot(*(c[0] - c[-1])) > 3 and (ci, e) not in pinned]   # ends on a junction are not free
for ci, e in ends:
    p = curves[ci][e]; best = None
    for cj, c in enumerate(curves + others):
        d = np.hypot(*(c - p).T)
        if cj == ci: d[max(0, (len(c) - 25) if e == -1 else 0):(len(c) if e == -1 else 25)] = 1e9
        k_ = int(np.argmin(d))
        lim = N.get("meet_gap", GAP) if cj >= len(curves) else GAP
        if d[k_] < lim and d[k_] > 1.5 and (best is None or d[k_] < best[0]): best = (d[k_], c[k_])
    if best is not None:
        seg = np.linspace(p, best[1], 12)[1:]; curves[ci] = np.vstack([curves[ci], seg]) if e == -1 else np.vstack([seg[::-1], curves[ci]])
if N.get("half"):
    for c in curves:                                                       # ends that stop just short of the centreline put on it
        for e in (0, -1):
            if abs(c[e][1] - AX) < N.get("snap", 25): c[e][1] = AX
    curves = curves + [np.stack([c[:, 0], 2 * AX - c[:, 1]], 1) for c in curves]
out = (cv2.resize(ref, (W, H)) * 0.75).astype(np.uint8)
if N.get("half"): cv2.line(out, (0, int(round(AX))), (W, int(round(AX))), (255, 255, 0), 2)
for c in curves: cv2.polylines(out, [np.round(c).astype(np.int32)], False, tuple(N.get("colour", [0, 255, 0])), 6, cv2.LINE_AA)
json.dump([c.tolist() for c in curves], open(f"{D}/{VIEW}_network.json", "w")); cv2.imwrite(OUT, cv2.resize(out, None, fx=0.5, fy=0.5))
print("NETWORK branches %d, rings %d, junctions %d" % (len(branches), len(curves) - len(branches), len(centres)))
