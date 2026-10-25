# Read the user's tablet drawings: align each onto its ref-01 view (SIFT, similarity), pick the drawn strokes by colour,
# split the view into the regions the outlines close, and find the marks inside them (hatches = holes, letters).
# Writes per view: regions.npz (label map at 4x the ref crop) + a numbered sheet + regions.json.
# Usage: python tablet_regions.py <drawings_dir>   (expects align.json from the alignment step next to the drawings)
import sys, json, numpy as np, cv2
from skimage.morphology import skeletonize
D = sys.argv[1]; R = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"; K = 4
AL = json.load(open(f"{D}/align.json"))
# hue ranges (OpenCV 0..180) of the user's pens; saturation keeps the lightened, greyish reference out
PENS = {"green": [(35, 85)], "orange": [(9, 24)], "red": [(0, 8), (170, 180)], "blue": [(100, 135)], "yellow": [(25, 35)]}
BGR = {"green": (60, 220, 60), "orange": (0, 150, 255), "red": (40, 40, 240), "blue": (240, 80, 40), "yellow": (0, 230, 255)}
def pens(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); h, s, v = cv2.split(hsv); out = {}
    for name, ranges in PENS.items():
        m = np.zeros(h.shape, bool)
        for lo, hi in ranges: m |= (h >= lo) & (h <= hi)
        out[name] = m & (s > 110) & (v > 90)
    b, g, r = cv2.split(img.astype(np.int16)); out["green"] |= (g - np.maximum(r, b) > 25) & (s > 45)   # the pale green pen
    return out
def bridge(outline, R=110):
    # join each open stroke end to the nearest outline ahead of it, so outlines that stop just short still close
    sk = skeletonize(outline > 0); nb = cv2.filter2D(sk.astype(np.uint8), -1, np.ones((3, 3), np.float32)) - sk
    ends = np.argwhere(sk & (nb == 1)); pts = np.argwhere(sk); out = outline.copy()
    for e in ends:
        near = pts[np.hypot(*(pts - e).T) < 14]; back = near.mean(0); d = e - back
        if np.hypot(*d) < 1e-3: continue
        d = d / np.hypot(*d); v = pts - e; dist = np.hypot(*v.T)
        ok = (dist > 20) & (dist < R) & ((v @ d) > 0.55 * dist)
        if ok.any():
            t = pts[ok][np.argmin(dist[ok])]; cv2.line(out, (int(e[1]), int(e[0])), (int(t[1]), int(t[0])), 1, 9)
    return out
for name, a in AL.items():
    view = a["view"]; ref = cv2.imread(f"{R}/{view}.png"); H, W = ref.shape[:2]
    A = np.array(a["A"]) * K; img = cv2.imread(f"{D}/{name}.jpg")
    warped = cv2.warpAffine(img, A, (W * K, H * K), flags=cv2.INTER_LINEAR, borderValue=(128, 128, 128))
    # colours the reference itself has (the red band, cyan lights) are not pen strokes
    native = pens(cv2.resize(ref, (W * K, H * K), interpolation=cv2.INTER_CUBIC))
    P = {k: (cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0) & ~(cv2.dilate(native[k].astype(np.uint8), np.ones((15, 15), np.uint8)) > 0)
         for k, m in pens(warped).items()}
    ink = np.zeros((H * K, W * K), np.uint8)
    for m in P.values(): ink |= m
    ink = cv2.dilate(ink, np.ones((9, 9), np.uint8))
    # strokes not joined to the outline network are marks (hatches, letters); the rest are outlines
    n, lab, st, cen = cv2.connectedComponentsWithStats(ink)
    marks = []; outline = np.zeros_like(ink)
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if area <= 60: continue
        comp = (lab[y:y + h, x:x + w] == i).astype(np.uint8); pad = cv2.copyMakeBorder(comp, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=0)
        ff = pad.copy(); cv2.floodFill(ff, None, (0, 0), 1); enclosed = (ff == 0).sum()
        if enclosed > 3000 or max(w, h) > 0.25 * W * K: outline[lab == i] = 1
        elif area > 60:
            colour = max(P, key=lambda c: (P[c] & (lab == i)).sum()); marks.append({"colour": colour, "at": [float(cen[i][0]), float(cen[i][1])], "bbox": [int(x), int(y), int(w), int(h)]})
    # an open outline in a part colour (not the green arms) is meant closed: join its two ends
    for c in P:
        if c == "green": continue
        n2, lab2 = cv2.connectedComponents(cv2.dilate(P[c].astype(np.uint8), np.ones((9, 9), np.uint8)))
        for j in range(1, n2):
            comp = lab2 == j
            if comp.sum() < 3000 or not (outline.astype(bool) & comp).any(): continue
            sk = skeletonize(comp)
            for _ in range(40):   # prune the short spurs a shaky hand leaves at the ends
                nb = cv2.filter2D(sk.astype(np.uint8), -1, np.ones((3, 3), np.float32)) - sk; sk = sk & ~(nb == 1)
            nb = cv2.filter2D(sk.astype(np.uint8), -1, np.ones((3, 3), np.float32)) - sk; ends = np.argwhere(sk & (nb == 1))
            if len(ends) == 2 and np.hypot(*(ends[0] - ends[1])) < 0.5 * sk.sum():
                cv2.line(outline, (int(ends[0][1]), int(ends[0][0])), (int(ends[1][1]), int(ends[1][0])), 1, 9)
    closed = cv2.morphologyEx(bridge(outline), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
    ship = cv2.resize(cv2.imread(f"{R}/{view}_mask.png", 0), (W * K, H * K)) > 127
    n, reg, st, cen = cv2.connectedComponentsWithStats((closed == 0).astype(np.uint8), connectivity=4)
    rings = {c: cv2.dilate(P[c].astype(np.uint8), np.ones((9, 9), np.uint8)) > 0 for c in P}
    corners = {reg[0, 0], reg[0, -1], reg[-1, 0], reg[-1, -1]} - {0}; regions = []
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if area < 4000: continue
        m = reg == i; edge = cv2.dilate(m.astype(np.uint8), np.ones((25, 25), np.uint8)).astype(bool) & ~m
        border = {c: int((rings[c] & edge).sum()) for c in P}; total = sum(border.values()) or 1
        inside = [mk for mk in marks if reg[int(mk["at"][1]), int(mk["at"][0])] == i]
        touches = i in corners or ship[m].mean() < 0.3   # mostly background in the reference: not the ship
        dt = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5); cy, cx = np.unravel_index(np.argmax(dt), dt.shape)
        regions.append({"id": len(regions) + 1, "label_map": i, "area_px": int(area), "outside": bool(touches),
                        "border": {c: round(v / total, 2) for c, v in border.items() if v / total > 0.08},
                        "marks": [mk["colour"] for mk in inside], "centre": [float(cx), float(cy)]})
    # sheet: the reference, regions tinted and numbered, the outlines in their pen colours
    base = cv2.resize(ref, (W * K, H * K), interpolation=cv2.INTER_CUBIC); sheet = base.copy(); rng = np.random.default_rng(3)
    for r in regions:
        if r["outside"]: continue
        c = rng.integers(60, 255, 3); m = reg == r["label_map"]; sheet[m] = (sheet[m] * 0.45 + c * 0.55).astype(np.uint8)
    for c, m in P.items(): sheet[m] = BGR[c]
    for r in regions:
        if r["outside"]: continue
        x, y = int(r["centre"][0]), int(r["centre"][1]); t = str(r["id"])
        cv2.circle(sheet, (x, y), 34, (0, 0, 0), -1); cv2.circle(sheet, (x, y), 34, (255, 255, 255), 3)
        cv2.putText(sheet, t, (x - 14 * len(t), y + 14), 0, 1.4, (255, 255, 255), 3)
    cv2.imwrite(f"{D}/regiuni_{name}_{view}.jpg", cv2.resize(sheet, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 88])
    np.savez_compressed(f"{D}/regions_{name}.npz", reg=reg.astype(np.int32), **{f"pen_{c}": m for c, m in P.items()})
    json.dump({"view": view, "scale": K, "regions": regions, "marks": marks}, open(f"{D}/regions_{name}.json", "w"), indent=1)
    print(name, view, "regions", sum(not r["outside"] for r in regions), "marks", len(marks))
