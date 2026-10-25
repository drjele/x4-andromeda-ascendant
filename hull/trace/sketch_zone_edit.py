# Edit the closed zones of a view by the user's notes: each zone rasterised from <view>_faces.json, then cut by
# polygons ("cut": removed from the zone), grown by polygons ("add") or by the ship's silhouette in a box ("refmask"),
# or created ("new"); polygons in ref-crop px x4;
# smooth outlines (outer + holes) recomputed and drawn filled for confirmation. Writes <view>_faces_v<n>.json.
# Usage: python sketch_zone_edit.py <dir> <view> <edits.json> <out.png>
import sys, json, numpy as np, cv2
D, VIEW, ED, OUT = sys.argv[1:5]; R = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"; K = 4
E = json.load(open(ED)); F = json.load(open(f"{D}/{E['from']}")); ref = cv2.imread(f"{R}/{VIEW}.png"); H, W = ref.shape[0] * K, ref.shape[1] * K
def mask_of(f):
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.round(np.array(f["outer"])).astype(np.int32)], 1)
    for h in f["holes"]: cv2.fillPoly(m, [np.round(np.array(h)).astype(np.int32)], 0)
    return m
def poly(p, smooth=True):
    p = np.array(p, float)
    if smooth and 3 < len(p) < 40:                                              # a closed Catmull-Rom so hand-placed points read as curves
        q = []; n = len(p)
        for i in range(n):
            p0, p1, p2, p3 = p[i - 1], p[i], p[(i + 1) % n], p[(i + 2) % n]
            for t in np.linspace(0, 1, 16, endpoint=False):
                q.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
        p = np.array(q)
    return np.round(p).astype(np.int32)
M = {}
for k, f in F.items():                                                     # zones renamed into one (e.g. two visible pieces of the body)
    t = E.get("rename", {}).get(k, k); M[t] = np.maximum(M.get(t, np.zeros((H, W), np.uint8)), mask_of(f))
for t in set(E.get("rename", {}).values()):                                # the line that separated the merged zones closed up
    from scipy.ndimage import binary_fill_holes
    M[t] = binary_fill_holes(cv2.morphologyEx(M[t], cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))).astype(np.uint8)
for z in E.get("new", {}): M[z] = np.zeros((H, W), np.uint8)
GRAY = cv2.resize(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), (W, H), interpolation=cv2.INTER_CUBIC)
SHIP = cv2.resize((cv2.imread(f"{R}/{VIEW}_mask.png", 0) > 127).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
for z, ops in E["ops"].items():
    for kind, pts in ops:
        tmp = np.zeros((H, W), np.uint8)
        if kind == "refmask":                                              # the ship's own silhouette (light on the black background) in a box, outside the zones named
            x0, y0, x1, y1 = pts["box"]; src = (GRAY > pts["gray"]).astype(np.uint8) if "gray" in pts else SHIP; tmp[y0:y1, x0:x1] = src[y0:y1, x0:x1]
            for o in pts.get("outside", []): tmp[M[o] > 0] = 0
            k_ = pts.get("open", 5); tmp = cv2.morphologyEx(tmp, cv2.MORPH_OPEN, np.ones((k_, k_), np.uint8)); n, lab, st, _ = cv2.connectedComponentsWithStats(tmp)
            if n > 1: tmp = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
            if "stick_to" in pts:                                              # each column carried down/up to the zone below if the gap is small
                o = M[pts["stick_to"]]
                for x in np.nonzero(tmp.any(0))[0]:
                    ys = np.nonzero(tmp[:, x])[0]; yo = np.nonzero(o[ys.max():, x])[0]
                    if len(yo) and yo[0] <= pts.get("gap", 40): tmp[ys.max():ys.max() + yo[0] + 1, x] = 1
        elif kind == "shrink":                                             # the zone thinned by px along its border with the other zones, inside a box
            from scipy.ndimage import distance_transform_edt
            x0, y0, x1, y1 = pts["box"]; others = np.zeros((H, W), bool)
            for o in M:
                if o != z: others |= M[o] > 0
            near = (distance_transform_edt(~others) <= pts["px"]) & (M[z] > 0); near[:y0] = near[y1:] = False; near[:, :x0] = near[:, x1:] = False
            dist = {o: distance_transform_edt(M[o] == 0) for o in M if o != z}
            ys, xs = np.nonzero(near)
            for yy, xx in zip(ys, xs): M[min(dist, key=lambda o: dist[o][yy, xx])][yy, xx] = 1
            M[z][near] = 0; continue
        elif kind == "straight_bottom":                                    # the zone's lower edge made the straight line p0-p1: above it, the gap and the zones in `take` join it; below it, its pixels go to the nearest neighbour
            from scipy.ndimage import distance_transform_edt
            (x0, y0), (x1, y1) = pts["p0"], pts["p1"]; Yg, Xg = np.mgrid[0:H, 0:W]; line_y = y0 + (Xg - x0) * (y1 - y0) / (x1 - x0)
            span = (Xg >= x0) & (Xg <= x1); above = span & (Yg <= line_y); below = span & (Yg > line_y)
            top = np.full(W, H); cols = np.nonzero(M[z].any(0))[0]; top[cols] = M[z][:, cols].argmax(0)
            under_top = Yg >= top[None, :]; taken = np.zeros((H, W), bool)
            for o in M: taken |= M[o] > 0
            grab = above & under_top & (~taken | np.logical_or.reduce([M[o] > 0 for o in pts["take"]]))
            for o in pts["take"]: M[o][grab] = 0
            M[z][grab] = 1; drop = below & (M[z] > 0); M[z][drop] = 0
            dist = {o: distance_transform_edt(M[o] == 0) for o in M if o != z}
            ys, xs = np.nonzero(drop)
            for yy, xx in zip(ys, xs): M[min(dist, key=lambda o: dist[o][yy, xx])][yy, xx] = 1
            continue
        elif kind == "grow_into":                                          # grown until it touches the target zone (the line gap between them filled)
            g_ = cv2.dilate(M[z], np.ones((2 * pts["px"] + 1,) * 2, np.uint8)); near = cv2.dilate(M[pts["target"]], np.ones((2 * pts["px"] + 1,) * 2, np.uint8))
            free = np.ones((H, W), bool)
            for o in M:
                if o != z: free &= M[o] == 0
            M[z][(g_ > 0) & (near > 0) & free] = 1; continue
        elif kind == "add_from":                                           # only the area that currently belongs to the zones named
            cv2.fillPoly(tmp, [poly(pts["poly"])], 1); src = np.zeros((H, W), np.uint8)
            for o in pts["from"]: src |= M[o]
            tmp &= src; M[z][tmp > 0] = 1
            for o in pts["from"]: M[o][tmp > 0] = 0
            continue
        else: cv2.fillPoly(tmp, [poly(pts)], 1)
        if kind == "cut": M[z][tmp > 0] = 0
        else:
            M[z][tmp > 0] = 1
            for o in M:                                                    # a zone grown over another takes that area from it
                if o != z and o not in E.get("keep_under", []): M[o][tmp > 0] = 0
pal = {"BRAT": (0, 220, 0), "AI": (255, 170, 0), "CORP": (0, 0, 255), "AS": (40, 40, 170), "gol sub brat": (255, 0, 255), "PUNTE": (0, 255, 255)}
out = cv2.resize(ref, (W, H)) // 3; res = {}
kk = np.exp(-0.5 * (np.arange(-15, 16) / 5.0) ** 2); kk /= kk.sum()
sm = lambda c: np.stack([np.convolve(np.r_[c[-15:, i], c[:, i], c[:15, i]], kk, "valid") for i in (0, 1)], 1)
for z, m in M.items():
    kz = np.ones((E.get("tidy", 11),) * 2, np.uint8); m = cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_CLOSE, kz), cv2.MORPH_OPEN, kz)   # small burrs off the borders
    cs, hi = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if not cs: continue
    hi = hi[0]; parts = [i for i in range(len(cs)) if hi[i][3] < 0 and cv2.contourArea(cs[i]) > 2000]
    res[z] = [{"outer": sm(cs[i][:, 0, :].astype(float)).tolist(), "holes": [sm(cs[j][:, 0, :].astype(float)).tolist() for j in range(len(cs)) if hi[j][3] == i and cv2.contourArea(cs[j]) > 2000]} for i in parts]
    col = pal.get(z, (200, 200, 200)); ov = out.copy(); ov[m > 0] = col; out = cv2.addWeighted(out, 0.55, ov, 0.45, 0)
    for piece in res[z]:
        for q in [piece["outer"]] + piece["holes"]: cv2.polylines(out, [np.round(np.array(q)).astype(np.int32)], True, col, 5, cv2.LINE_AA)
    ys, xs = np.nonzero(m); cv2.putText(out, z, (int(np.median(xs)) - 60, int(np.median(ys))), 0, 1.8, (255, 255, 255), 5, cv2.LINE_AA)
json.dump(res, open(f"{D}/{E['to']}", "w")); cv2.imwrite(OUT, cv2.resize(out, None, fx=0.5, fy=0.5)); print("ZONES", {z: len(v) for z, v in res.items()})
