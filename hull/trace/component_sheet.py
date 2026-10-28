# One drawing sheet per component, seen straight along each axis: top (+Z), bottom (-Z), front (+Y), back (-Y), left
# side and right side (the confirmed profile and its mirror), all at the multi-view drawing's scale and bow up. Solid
# fill + outline = the component's confirmed zones (symmetric views mirrored from one half); dashed outline = deduced
# from the current mesh (V17) where no confirmed view shows the part: the mesh is projected into that view and fitted on
# the ship's confirmed silhouette there by its bounding box. The whole ship is drawn faint in every panel for context.
# Usage: python component_sheet.py <components.json> <layout.json> <vederi.json> <mesh.npz> <deduce.json> <out_dir>
#   deduce.json: {"AR": {"side": ["A7"], "back": ["A7"], ...}, ...}  mesh part prefixes per missing view, or
#   {"AR": {"side": "plane:BF", ...}}: the part lies in another part's plane (a blade on the arm): its confirmed top
#   footprint lifted to that part's height at the same length (from the confirmed side view), with its strap thickness
import sys, json, os, numpy as np, cv2
CJ, LJ, VJ, MESH, DJ, OD = sys.argv[1:7]; COMP = json.load(open(CJ)); LAY = json.load(open(LJ)); VIEWS = json.load(open(VJ))
DED = json.load(open(DJ)); MZ = np.load(MESH); os.makedirs(OD, exist_ok=True)
Wc, Hc = LAY["size"]; AFF = {k: np.array(v, float) for k, v in LAY["aff"].items()}
SYM = ("top", "bottom", "back", "front")
def sym(key, m):
    if key not in SYM: return m
    ax = VIEWS[key]["axis"]; vert = key in ("back", "front"); n = m.shape[1] if vert else m.shape[0]; i = np.arange(n)
    src = np.clip(np.where(i <= ax, i, np.round(2 * ax - i).astype(int)), 0, n - 1); return m[:, src] if vert else m[src]
def view_mask(spec):
    if "zone" in spec:
        z = np.load(spec["zone"]); nm = json.load(open(spec["names"])); return np.isin(z, [int(k) for k, t in nm.items() if t in spec["take"]])
    if "npz" in spec:
        z = np.load(spec["npz"]); return np.any([z[t] for t in spec["take"]], 0)
    F = json.load(open(spec["faces"])); H, W = spec.get("size", [860, 3260]); m = np.zeros((H, W), np.uint8)
    for t in spec["take"]:
        for f in F[t]:
            cv2.fillPoly(m, [np.round(np.array(f["outer"])).astype(np.int32)], 1)
            for h in f.get("holes", []): cv2.fillPoly(m, [np.round(np.array(h)).astype(np.int32)], 0)
    return m > 0
def warp(key, m): return cv2.warpAffine(m.astype(np.uint8), AFF[key], (Wc, Hc), flags=cv2.INTER_NEAREST) > 0
# the whole ship per view on the canvas: the union of every component's zones there
ship = {k: np.zeros((Hc, Wc), bool) for k in AFF}
comp_canvas = {}
for comp, views in COMP.items():
    comp_canvas[comp] = {}
    for key, spec in views.items():
        w = warp(key, sym(key, view_mask(spec))); comp_canvas[comp][key] = w; ship[key] |= w
# mesh projection per view (world x lateral, y forward, z up) -> canvas, fitted on the ship's box there
names = [k[2:] for k in MZ.files if k.startswith("v|") and not k.startswith("v|SRC")]
allv = np.vstack([MZ["v|" + n] for n in names])
def proj(key, v):
    if key in ("top", "bottom"): return np.stack([v[:, 0], -v[:, 1]], 1)
    if key == "side": return np.stack([v[:, 2], -v[:, 1]], 1)
    return np.stack([v[:, 0], -v[:, 2]], 1)
def fit(key):
    p = proj(key, allv); ys, xs = np.nonzero(ship[key]); lo, hi = p.min(0), p.max(0)
    sx = (xs.max() - xs.min()) / (hi[0] - lo[0]); sy = (ys.max() - ys.min()) / (hi[1] - lo[1])
    return lambda q: np.stack([xs.min() + (q[:, 0] - lo[0]) * sx, ys.min() + (q[:, 1] - lo[1]) * sy], 1)
FIT = {k: fit(k) for k in AFF}
def mesh_mask(key, prefixes):
    m = np.zeros((Hc, Wc), np.uint8); f = FIT[key]
    for n in names:
        if not n.startswith(tuple(prefixes)): continue
        tri = MZ["v|" + n][MZ["t|" + n].astype(int)]; q = f(proj(key, tri.reshape(-1, 3))).reshape(-1, 3, 2)
        for t in np.round(q).astype(np.int32): cv2.fillConvexPoly(m, t, 1)
    return m > 0
# panels: the component's box over all views, each panel cropped to its view's ship box
# a part in another part's plane: heights per canvas row from the host's side-view band, mapped to front/back heights
def ext_rows(m): ys, xs = np.nonzero(m); return xs.min(), xs.max(), ys.min(), ys.max()
def centre(key, ax): A = AFF[key]; return A[0, 0] * ax + A[0, 1] * ax * 0 + A[0, 2] if key in ("back", "front") else A[0, 1] * ax + A[0, 2]
def plane_mask(comp, host, key):
    top = comp_canvas[comp]["top"]; side = comp_canvas[host]["side"]; Hs = np.arange(Hc)
    c = np.full(Hc, np.nan); t = np.full(Hc, np.nan)
    for y in range(Hc):
        xs = np.nonzero(side[y])[0]
        if len(xs): c[y] = xs.mean(); t[y] = len(xs)
    ok = ~np.isnan(c); c = np.interp(Hs, Hs[ok], c[ok]); t = np.interp(Hs, Hs[ok], t[ok])
    sx0, sx1, _, _ = ext_rows(ship["side"]); out = np.zeros((Hc, Wc), np.uint8); ys, xs = np.nonzero(top)
    if key == "side":
        for y in np.unique(ys): out[y, int(c[y] - t[y] / 2):int(c[y] + t[y] / 2) + 1] = 1
        return out > 0
    if key == "bottom":
        dx = int(round(centre("bottom", VIEWS["bottom"]["axis"]) - centre("top", VIEWS["top"]["axis"]))); out[ys, np.clip(xs + dx, 0, Wc - 1)] = 1; return out > 0
    _, _, by0, by1 = ext_rows(ship["back"]); _, _, fy0, _ = ext_rows(ship[key]); hh = by1 - by0
    dx = centre(key, VIEWS[key]["axis"]) - centre("top", VIEWS["top"]["axis"])
    for x, y in zip(xs, ys):
        lo = (c[y] - t[y] / 2 - sx0) / (sx1 - sx0); hi = (c[y] + t[y] / 2 - sx0) / (sx1 - sx0)
        y0, y1 = int(fy0 + (1 - hi) * hh), int(fy0 + (1 - lo) * hh); out[y0:y1 + 1, int(round(x + dx))] = 1
    return cv2.morphologyEx(out, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0
# a V blade on the host's inner edge seen end-on (front/back): base on the host's inner edge (the side facing the
# centreline), the blade reaching inward along the edge's inward normal as far as its confirmed top width at that
# lateral position, the V's apex line in the middle; widest at the root, gone where the top footprint ends
def vee_mask(comp, host, key):
    top = comp_canvas[comp]["top"]; hm = comp_canvas[host][key]; out = np.zeros((Hc, Wc), np.uint8)
    cx_t = centre("top", VIEWS["top"]["axis"]); cx_v = centre(key, VIEWS[key]["axis"]); apex = []
    for side in (-1, 1):
        cols = [x for x in range(Wc) if hm[:, x].any() and (x - cx_v) * side > 0]
        xs = np.array(cols); ye = np.array([np.nonzero(hm[:, x])[0].max() for x in xs], float)       # inner (lower) edge of the arc
        k = np.exp(-0.5 * (np.arange(-30, 31) / 10) ** 2); k /= k.sum(); ye = np.convolve(np.pad(ye, 30, mode="edge"), k, "valid")
        dy = np.gradient(ye); n = np.stack([-dy, np.ones_like(dy)], 1) * np.array([[1, 1]]); n /= np.linalg.norm(n, axis=1)[:, None]
        if side > 0: n[:, 0] *= 1
        n[:, 0] = np.where((n[:, 0] * side) > 0, -n[:, 0], n[:, 0])                                   # inward: toward the centreline
        base, tip = [], []
        for x, y, nn in zip(xs, ye, n):
            w = top[:, int(round(x - cx_v + cx_t))].sum() if 0 <= int(round(x - cx_v + cx_t)) < Wc else 0
            if w < 2: continue
            base.append((x, y)); tip.append((x + nn[0] * w, y + nn[1] * w))
        if len(base) > 2:
            poly = np.array(base + tip[::-1]); cv2.fillPoly(out, [np.round(poly).astype(np.int32)], 1); apex.append(np.array(tip))
    VEE_APEX[(comp, key)] = apex
    return out > 0
VEE_APEX = {}
# rules the user gave (drawn solid): "copytop" = the same footprint as from above (nothing covers it from below);
# "overlap:HOST" = seen end-on it lies over the host, so it is the host's own area over the lateral span of its top footprint
def attach_mask(comp, host, key):
    # "attach:HOST" (plan views): the part keeps its place against the host's edge as seen from above. Its pixels are read
    # as (share of the way along the shared edge, distance from the edge) and laid along the host's facing edge in this
    # view, at the same distance along that edge's normal.
    from scipy.spatial import cKDTree
    top = comp_canvas[comp]["top"]; ht = comp_canvas[host]["top"]; hb = comp_canvas[host][key]; out = np.zeros((Hc, Wc), np.uint8)
    ct, cb = centre("top", VIEWS["top"]["axis"]), centre(key, VIEWS[key]["axis"])
    def curve(pts):                                                        # ordered by row, smoothed, with arclength share and normals
        pts = pts[np.argsort(pts[:, 1])]; k = np.exp(-0.5 * (np.arange(-15, 16) / 5) ** 2); k /= k.sum()
        pts = np.stack([np.convolve(np.pad(pts[:, j], 15, mode="edge"), k, "valid") for j in (0, 1)], 1)
        sl = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]; tg = np.gradient(pts, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-9
        return pts, sl / max(sl[-1], 1), np.stack([-tg[:, 1], tg[:, 0]], 1)
    for side in (-1, 1):
        half = lambda x, c: (x - c) * side > 0
        ys, xs = np.nonzero(top); k = half(xs, ct); P = np.stack([xs[k], ys[k]], 1).astype(float)
        if not len(P): continue
        edge_t = ht & cv2.dilate(top.astype(np.uint8), np.ones((25, 25), np.uint8)).astype(bool)
        ey, ex = np.nonzero(edge_t); kk = half(ex, ct); E = np.stack([ex[kk], ey[kk]], 1).astype(float)
        rows = {}
        for x, y in zip(*np.nonzero(hb.T)):
            if half(x, cb): rows[y] = max(rows.get(y, -1e9), x) if side < 0 else min(rows.get(y, 1e9), x)
        if len(E) < 5 or len(rows) < 5: continue
        Ct, St, Nt = curve(E); Cb, Sb, Nb = curve(np.array([(x, y) for y, x in rows.items()], float))
        tr = cKDTree(Ct); d, i = tr.query(P); sgn = np.sign(((P - Ct[i]) * Nt[i]).sum(1)); dist = d * sgn
        j = np.clip(np.searchsorted(Sb, St[i]), 0, len(Sb) - 1)
        # the normal on the bottom edge pointing the same way relative to the host (away from it, into the hole)
        nb = Nb[j] * np.where(((Cb[j] - np.array([cb, Cb[j][:, 1].mean() if False else 0])[None, :] * 0) * 0).sum(1) == 0, 1, 1)[:, None]
        away = np.sign(((Nb[j] * (np.array([cb, 0]) - Cb[j]) * np.array([1, 0])).sum(1)) + 1e-9)          # toward the centreline
        Q = Cb[j] + nb * (np.abs(dist) * away)[:, None]
        for q in np.round(Q).astype(int): cv2.circle(out, (int(q[0]), int(q[1])), 3, 1, -1)
    out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    out = (cv2.GaussianBlur(out.astype(np.float32), (0, 0), 12) > 0.5).astype(np.uint8)                   # organic edge, no teeth
    n, lab, st, _ = cv2.connectedComponentsWithStats(out); keep = np.zeros(n, bool); keep[1:] = st[1:, 4] > 0.15 * st[1:, 4].max()
    return keep[lab] & ~hb
def rule_mask(comp, rule, key):
    if rule.startswith("attach:"): return attach_mask(comp, rule[7:], key)
    top = comp_canvas[comp]["top"]; dx = int(round(centre(key, VIEWS[key]["axis"]) - centre("top", VIEWS["top"]["axis"])))
    if rule == "copytop":                                                  # verbatim: the same place in the panel as from above
        ox, oy = BOX[key][0] - BOX["top"][0], BOX[key][1] - BOX["top"][1]
        out = np.zeros((Hc, Wc), bool); ys, xs = np.nonzero(top); out[np.clip(ys + oy, 0, Hc - 1), np.clip(xs + ox, 0, Wc - 1)] = True; return out
    host = comp_canvas[rule.split(":")[1]][key]; cols = np.zeros(Wc, bool); xs = np.nonzero(top.any(0))[0]; cols[np.clip(xs + dx, 0, Wc - 1)] = True
    return host & cols[None, :]
PANELS = [("SUS (+Z)", "top", False), ("FATA (+Y)", "front", False), ("PROFIL STANGA (-X)", "side", False),
          ("JOS (-Z)", "bottom", False), ("SPATE (-Y)", "back", False), ("PROFIL DREAPTA (+X)", "side", True)]
def box(m, pad=40):
    ys, xs = np.nonzero(m); return max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, Wc), min(ys.max() + pad, Hc)
BOX = {k: box(ship[k]) for k in AFF}
def dashed(img, m, col):
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    for c in cs:
        c = c[:, 0, :]
        for i in range(0, len(c) - 6, 16): cv2.polylines(img, [c[i:i + 8]], False, col, 3, cv2.LINE_AA)
def solid_mask(comp, key):
    # the component's solid (confirmed or by the user's rule) area in a view, or None
    rule = DED.get(comp, {}).get(key)
    if isinstance(rule, str) and (rule == "copytop" or rule.startswith(("overlap:", "attach:"))): return rule_mask(comp, rule, key)
    m = comp_canvas[comp].get(key); return m if m is not None and m.any() else None
def shift_panel(m, src, dst):                                              # the same place in the panel: boxes share the top-left offset
    ox, oy = BOX[dst][0] - BOX[src][0], BOX[dst][1] - BOX[src][1]; out = np.zeros_like(m); ys, xs = np.nonzero(m)
    ok = (ys + oy >= 0) & (ys + oy < Hc) & (xs + ox >= 0) & (xs + ox < Wc); out[ys[ok] + oy, xs[ok] + ox] = True; return out
# calibration (orthographic): a component's outline seen from +Z equals the one from -Z, and from -Y the one from +Y;
# the reference view's outline is copied into the opposite one; where the reference does not show the part, the
# opposite view keeps its own. CALIB_LOSS records how much of the opposite view's own area the copy does not cover.
CALIB = {"bottom": "top", "front": "back"}; CALIB_LOSS = {}
PAIR = {"top": "bottom", "bottom": "top", "front": "back", "back": "front"}
REFV = {"top": "top", "bottom": "top", "back": "back", "front": "back"}; THICK = 45
def full_mask(comp, key):
    # reference + attached extensions: position and outline from the reference view (top for Z, back for Y); from the
    # opposite view only the pieces that continue the reference shape (touch it) AND reach well past it (more than THICK
    # px: a real hidden part, not a sliver left by the two drawings not lining up); one smooth organic shape
    from scipy.ndimage import label as _lab, distance_transform_edt as _edt
    if comp == "AR" and key in ("back", "front"): return solid_mask(comp, key)
    rv = REFV[key]; ov = PAIR[rv]; ref = solid_mask(comp, rv); opp = solid_mask(comp, ov)
    if ref is None:
        return shift_panel(opp, ov, key) if opp is not None else None
    ref = shift_panel(ref, rv, key) if rv != key else ref.copy(); full = ref.copy()
    if opp is not None:
        o = shift_panel(opp, ov, key) if ov != key else opp.copy(); out = o & ~ref
        d = _edt(~ref); lab, n = _lab(out); near = cv2.dilate(ref.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
        for i in range(1, n + 1):
            r = lab == i
            if (r & near).any() and d[r].max() > THICK: full |= r
    full = cv2.morphologyEx(full.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    return cv2.GaussianBlur(full.astype(np.float32), (0, 0), 6) > 0.5
def _unused_full_mask(comp, key):
    # union calibration: the part's full outline in a view = what this view shows + what the opposite view shows (moved into
    # this panel), smoothed into one organic shape; the same full outline in both opposite views
    own = solid_mask(comp, key); opp = solid_mask(comp, PAIR[key]) if key in PAIR else None
    if comp == "AR" and key in ("back", "front"): return own                # the user's rule: overlaps BF from the front, not seen from behind
    u = np.zeros((Hc, Wc), bool)
    if own is not None: u |= own
    if opp is not None: u |= shift_panel(opp, PAIR[key], key)
    if not u.any(): return None
    u = cv2.morphologyEx(u.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    return cv2.GaussianBlur(u.astype(np.float32), (0, 0), 6) > 0.5
def calib_mask(comp, key):
    if key in PAIR: return full_mask(comp, key), True
    return solid_mask(comp, key), False
# the ship in a calibrated view = the union of its components there (so the background agrees with the copied parts)
ship0 = {k: v.copy() for k, v in ship.items()}
for key in ("bottom", "front"):                                            # the opposite view's ship = the reference's outline and holes
    ship[key] = shift_panel(ship0[REFV[key]], REFV[key], key)
for comp in COMP:
    tiles = []
    for title, key, flip in PANELS:
        x0, y0, x1, y1 = BOX[key]; t = np.full((y1 - y0, x1 - x0, 3), 18, np.uint8)
        sh = ship[key][y0:y1, x0:x1]; e = cv2.morphologyEx(sh.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
        t[sh] = (45, 45, 45); t[e] = (95, 95, 95)
        m = comp_canvas[comp].get(key)
        rule = DED.get(comp, {}).get(key)
        if isinstance(rule, str) and (rule == "copytop" or rule.startswith(("overlap:", "attach:"))): m = rule_mask(comp, rule, key); title += "  [regula: %s]" % ("ca de sus" if rule == "copytop" else ("suprapus pe " + rule[8:] if rule.startswith("overlap:") else "lipit de " + rule[7:]))
        hidden = None
        if key in PAIR:
            own = solid_mask(comp, key); fm = full_mask(comp, key)
            if fm is not None:
                m = fm; title = title.split("  [")[0] + "  [calibrat: reuniune cu %s]" % {"top": "-Z", "bottom": "+Z", "front": "-Y", "back": "+Y"}[key]
                hidden = fm & ~(own if own is not None else np.zeros_like(fm))
                if own is not None and own.any(): CALIB_LOSS[(comp, key)] = round(100 * hidden.sum() / fm.sum(), 1)
        if m is not None and m.any():
            mm = m[y0:y1, x0:x1]; t[mm] = (40, 170, 230)
            if hidden is not None:                                         # hidden from this side: hatched
                hh = hidden[y0:y1, x0:x1] & ((np.add.outer(np.arange(hidden[y0:y1].shape[0]), np.arange(x1 - x0)) // 9) % 3 == 0); t[hh] = (20, 85, 115)
            cs, _ = cv2.findContours(mm.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE); cv2.drawContours(t, cs, -1, (255, 255, 255), 3, cv2.LINE_AA)
        elif key in DED.get(comp, {}):
            dd = DED[comp][key]
            if isinstance(dd, str) and dd.startswith("vee:"):
                mm = vee_mask(comp, dd[4:], key)[y0:y1, x0:x1]; dashed(t, mm, (255, 0, 255)); title += "  [dedus: V pe %s]" % dd[4:]
            elif isinstance(dd, str) and dd.startswith("plane:"):
                mm = plane_mask(comp, dd[6:], key)[y0:y1, x0:x1]; dashed(t, mm, (255, 0, 255)); title += "  [dedus: in planul %s]" % dd[6:]
            else: mm = mesh_mask(key, dd)[y0:y1, x0:x1]; dashed(t, mm, (255, 0, 255)); title += "  [dedus din V17]"
        else: title += "  [nu se vede]"
        if flip: t = t[:, ::-1].copy()
        bar = np.zeros((70, t.shape[1], 3), np.uint8); cv2.putText(bar, title, (10, 50), 0, 1.4, (235, 235, 235), 3, cv2.LINE_AA)
        tiles.append(np.vstack([bar, t]))
    def row(ts):
        h = max(x.shape[0] for x in ts); return np.hstack([np.vstack([x, np.full((h - x.shape[0], x.shape[1], 3), 0, np.uint8)]) for x in ts] if False else
                                                         [np.vstack([x, np.zeros((h - x.shape[0], x.shape[1], 3), np.uint8)]) for x in ts])
    r1, r2 = row(tiles[:3]), row(tiles[3:]); w = max(r1.shape[1], r2.shape[1])
    pad = lambda r: np.hstack([r, np.zeros((r.shape[0], w - r.shape[1], 3), np.uint8)])
    sheet = np.vstack([np.zeros((110, w, 3), np.uint8), pad(r1), pad(r2)])
    cv2.putText(sheet, comp + "   plin = confirmat, punctat mov = dedus din V17", (20, 80), 0, 2.0, (255, 255, 255), 4, cv2.LINE_AA)
    cv2.imwrite(f"{OD}/{comp}_6vederi.png", cv2.resize(sheet, None, fx=0.4, fy=0.4)); print(comp)
json.dump({"%s %s" % k: v for k, v in CALIB_LOSS.items()}, open(f"{OD}/calibrare_pierderi.json", "w"), indent=1)
print("ASCUNS in vederea proprie (% din conturul complet):", CALIB_LOSS)
