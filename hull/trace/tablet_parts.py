# Group the drawing regions into ship parts (from the user's colours and answers) and write one sheet per part:
# for every view the part shows in, the reference with the part tinted and outlined, beside the cut-out itself.
# Usage: python tablet_parts.py <drawings_dir>
import sys, json, numpy as np, cv2
D = sys.argv[1]; R = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"
# region ids as numbered on the regiuni_* sheets
PARTS = {
    "corp": {"desen_1": [11], "desen_3": [10, 8], "desen_2": [13], "desen_4": [14], "desen_5": [10, "blue_hull"]},
    "brate": {"desen_1": [3, 4, 7, 9, 10, 12, 13, 14], "desen_3": [2, 5, 7, 9, 11, 12, 13, 16], "desen_2": [2, 3, 4, 5],
              "desen_4": [2, 4, 5, 6, 9, 15, 16, 18, 11, "mirror:11"], "desen_5": [2, 6, 7, 11, 12, 13]},
    "aripi_superioare": {"desen_2": [6, 7, 10], "desen_5": [4, 8]},
    "aripi_inferioare": {"desen_5": [9]},
    "semiluna": {"desen_2": [12]},
    "hangare": {"desen_2": [14, 15]},
}
# top view 3/14 hold arm + lower wing together (user, 2026-10-24); split against V4 when building the 3D
COL = {"corp": (0, 150, 255), "brate": (60, 220, 60), "aripi_superioare": (255, 90, 200), "hangare": (240, 160, 40), "aripi_inferioare": (255, 200, 0), "semiluna": (0, 230, 255)}
def smooth(m, sigma=10):
    # organic outline: the hand-drawn wobble taken out by a circular gaussian along each contour, holes kept
    cs, hier = cv2.findContours(m.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE); out = np.zeros(m.shape, np.uint8)
    if hier is None: return m
    k = np.exp(-0.5 * (np.arange(-3 * sigma, 3 * sigma + 1) / sigma) ** 2); k /= k.sum()
    for c, h in zip(cs, hier[0]):
        if len(c) < 6 * sigma: continue
        p = c[:, 0].astype(float); q = np.stack([np.convolve(np.r_[p[-3 * sigma:, i], p[:, i], p[:3 * sigma, i]], k, "valid") for i in (0, 1)], 1)
        cv2.fillPoly(out, [np.round(q).astype(np.int32)], 0 if h[3] >= 0 else 1)
    return out > 0
saved = {}
for part, views in PARTS.items():
    rows = []
    for name, ids in views.items():
        j = json.load(open(f"{D}/regions_{name}.json")); reg = np.load(f"{D}/regions_{name}.npz")["reg"]; view = j["view"]
        maps = {r["id"]: r["label_map"] for r in j["regions"]}; m = np.isin(reg, [maps[i] for i in ids if isinstance(i, int)])
        for tok in [i for i in ids if isinstance(i, str)]:
            if tok.startswith("mirror:"):
                # the drawn side mirrored about the ship's centre line in this view
                src = reg == maps[int(tok[7:])]; ship = cv2.resize(cv2.imread(f"{R}/{view}_mask.png", 0), (reg.shape[1], reg.shape[0])) > 127
                xs = np.nonzero(ship.any(0))[0]; cx = (xs.min() + xs.max()) / 2; ys, xx = np.nonzero(src)
                xm = np.clip(np.round(2 * cx - xx).astype(int), 0, reg.shape[1] - 1); add = np.zeros_like(m); add[ys, xm] = True
                m |= cv2.morphologyEx(add.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
            elif tok == "blue_hull":
                # the open blue outline behind the drawn body regions (rear of the body in profile, drawn in pieces)
                # closed by the hull of all its pieces
                pen = np.load(f"{D}/regions_{name}.npz")["pen_blue"]; drawn = np.isin(reg, [maps[i] for i in ids if isinstance(i, int)])
                x1 = np.nonzero(drawn.any(0))[0].max(); ys, xs = np.nonzero(pen); keep = xs > x1 + 40
                if keep.sum() > 200:
                    hull = cv2.convexHull(np.stack([xs[keep], ys[keep]], 1).astype(np.int32)); add = np.zeros(m.shape, np.uint8); cv2.fillPoly(add, [hull], 1); m |= add > 0
        m = smooth(m); saved[f"{part}|{name}"] = m
        ref = cv2.imread(f"{R}/{view}.png"); ref = cv2.resize(ref, (reg.shape[1], reg.shape[0]), interpolation=cv2.INTER_CUBIC)
        c = np.array(COL[part], np.uint8); left = (ref * 0.55).astype(np.uint8); left[m] = (ref[m] * 0.5 + c * 0.5).astype(np.uint8)
        edge = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((7, 7), np.uint8)) > 0; left[edge] = c
        cut = np.zeros_like(ref); cut[m] = ref[m]; cut[edge] = c
        for r in j["regions"]:
            if r["id"] in ids and not r["outside"]:
                x, y = int(r["centre"][0]), int(r["centre"][1]); cv2.putText(left, str(r["id"]), (x - 20, y + 15), 0, 1.6, (255, 255, 255), 4)
        row = np.hstack([left, np.full((ref.shape[0], 16, 3), 90, np.uint8), cut])
        cv2.putText(row, f"{part} / {view} ({name})", (20, 60), 0, 2.0, (255, 255, 255), 4); rows.append(row)
    W = max(r.shape[1] for r in rows); sheet = np.vstack([np.pad(r, ((0, 16), (0, W - r.shape[1]), (0, 0)), constant_values=90) for r in rows])
    cv2.imwrite(f"{D}/parte_{part}.jpg", cv2.resize(sheet, None, fx=0.35, fy=0.35, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(part, [f"{n}:{len(i)}" for n, i in views.items()])
json.dump(PARTS, open(f"{D}/parts_map.json", "w"), indent=1); np.savez_compressed(f"{D}/part_masks.npz", **saved)
