# Bottom view zones from the confirmed lines (jos_reguli_v2): small gaps at line ends closed, the U arch's strands
# closed off from the arm's rear loop (a short segment between the two windows of each loop), the faces filled and
# named by seed points, drawn with a legend.
# Usage: python bottom_zones.py <dir>
import sys, json, numpy as np, cv2
O = sys.argv[1]; AX = 883.0; J = json.load(open(f"{O}/jos_reguli_v2.json"))
els = [np.array(c) for c in J["c1_sections"]]; OUTL = [np.array(c) for c in J["outlines"]]; L = [np.array(c) for c in J["lines"]]
for k, c in enumerate(L):                                                   # line ends within 30 px of another element joined to it
    for e in (0, -1):
        p = c[e]; best = min(((np.min(np.hypot(*(o - p).T)), o[np.argmin(np.hypot(*(o - p).T))]) for o in els + OUTL + [x for j, x in enumerate(L) if j != k]), key=lambda t: t[0])
        if 1 < best[0] < 30: seg = np.linspace(p, best[1], 8); L[k] = np.vstack([L[k], seg[1:]]) if e == -1 else np.vstack([seg[::-1][:-1], L[k]])
cut = []                                                                   # (the strut is now closed by line 8 in the outlines)
C6 = OUTL[4]
bg = np.load(f"{O}/salvat_jos_v1/jos_fundal_verde.npy"); H, W = bg.shape; cv_ = np.zeros((H, W), np.uint8)
for c in els + L + cut: cv2.polylines(cv_, [np.round(c).astype(np.int32)], False, 255, 7)
for c in OUTL: cv2.polylines(cv_, [np.round(c).astype(np.int32)], True, 255, 7)
n, lab = cv2.connectedComponents((cv_ == 0).astype(np.uint8), connectivity=4)
ZONES = [("BRAT", "bratele de jos (inelul exterior + buclele din spate)", (90, 200, 90), [(952, 214), (2800, 300)]),
         ("BS", "bratul superior, vazut de dedesubt", (230, 160, 60), [(1320, 370)]),
         ("AI", "aripa inferioara", (60, 170, 240), [(1880, 440), (2165, 545)]),
         ("ARC U", "arcul U (G1), banda in S", (200, 90, 220), [(1730, 820), (2585, 400)]),
         ("CORP fata", "corpul, in fata arcului U", (70, 70, 230), [(1200, 866)]),
         ("CORP spate", "corpul, in interiorul arcului U", (40, 40, 160), [(2180, 866)])]
im = cv2.resize(cv2.imread("/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01/bottom.png"), (W, H), interpolation=cv2.INTER_CUBIC)
r = np.arange(H); src = np.clip(np.where(r <= AX, r, np.round(2 * AX - r).astype(int)), 0, H - 1); base = (im[src] * 0.55).astype(np.uint8); out = base.copy(); res = {}
for name, _, col, seeds in ZONES:
    ids = set()
    for x, y in seeds: ids |= {lab[y, x], lab[int(round(2 * AX - y)), x]}
    m = np.isin(lab, list(ids - {0})); res[name] = m
    ov = out.copy(); ov[m] = col; out = cv2.addWeighted(out, 0.45, ov, 0.55, 0)
# the U arch's small "ears" beside the windows (between line 7 and the window, above the strands) belong to AI
# (the outer strand, line 2, is carried on to the window, so the ears come out as faces of their own, given to AI)
# the U arch first, exactly as its outlines give it: the closed band line 2 - line 8 (lower) - line 3 - line 8 (upper)
l2u, l3u = L[2] if L[2][0][1] < L[2][-1][1] else L[2][::-1], L[3] if L[3][0][1] < L[3][-1][1] else L[3][::-1]
band = np.vstack([l2u, l3u[::-1]]); arc = np.zeros((H, W), np.uint8); cv2.fillPoly(arc, [np.round(band).astype(np.int32)], 1); arc = arc > 0
for k in res: res[k] &= ~arc
res["ARC U"] = arc
taken = np.zeros((H, W), bool)
for m in res.values(): taken |= m
for i in range(1, n):                                                       # leftover pieces of ship: to the zone they border the most (the ears go to AI)
    m = lab == i
    if taken[m].any() or m.sum() < 200 or bg[m].mean() > 0.5: continue
    ring = cv2.dilate(m.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
    best = max(res, key=lambda k: (res[k] & ring).sum())
    if (res["AI"] & ring).any(): best = "AI"                               # a piece beside the U arch that also touches AI is AI (the arch's strands are smooth)
    if (res[best] & ring).sum(): res[best] |= m
# zones made smooth (each mask blurred, every pixel to the strongest zone, so no stubs poke out), and only the borders
# between different zones drawn (lines inside one zone, like 7 within AI, are not zone borders)
names = [z[0] for z in ZONES]; shipf = np.zeros((H, W), np.uint8)             # the ship from the smooth outlines (not the raw pixel mask)
cv2.fillPoly(shipf, [np.round(np.vstack(els)).astype(np.int32)], 1)
for c in OUTL: cv2.fillPoly(shipf, [np.round(c).astype(np.int32)], 0)
ship = shipf > 0
# no blur (it thinned the narrow U arch): the line pixels between faces go to the nearest zone, so each zone reaches
# the middle of its border lines and keeps the exact width the outlines give it
from scipy.ndimage import distance_transform_edt
zl0 = np.full((H, W), -1, np.int16)
for i, k in enumerate(names): zl0[res[k]] = i
_, (iy, ix) = distance_transform_edt(zl0 < 0, return_indices=True); zl0 = zl0[iy, ix]
for i, k in enumerate(names): res[k] = (zl0 == i) & ship & (~arc if k != "ARC U" else True)
res["ARC U"] = arc                                                          # the arch untouched by the fill
zl = np.full((H, W), -1, np.int16)
for i, k in enumerate(names): zl[res[k]] = i
edge = np.zeros((H, W), bool)
for dy, dx in ((0, 1), (1, 0)):
    a_, b_ = zl[:H - dy, :W - dx], zl[dy:, dx:]; e_ = a_ != b_; edge[:H - dy, :W - dx] |= e_
edge = cv2.dilate(edge.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
out = base.copy()
for name, _, col, _ in ZONES:
    ov = out.copy(); ov[res[name]] = col; out = cv2.addWeighted(out, 0.45, ov, 0.55, 0)
out[edge] = (255, 255, 255)
for name, _, col, seeds in ZONES:
    ys, xs = np.nonzero(res[name][:int(AX)])
    if len(xs): o = np.argmin(np.hypot(xs - np.median(xs), ys - np.median(ys))); cv2.putText(out, name, (int(xs[o]) - 60, int(ys[o])), 0, 1.5, (255, 255, 255), 4)
pad = np.full((H, 1500, 3), 25, np.uint8); cv2.putText(pad, "Zone - vedere de jos", (30, 90), 0, 1.8, (0, 255, 255), 4)
for k, (name, desc, col, _) in enumerate(ZONES):
    y = 200 + k * 130; cv2.rectangle(pad, (30, y - 50), (100, y + 10), col, -1); cv2.putText(pad, name, (125, y - 10), 0, 1.5, (255, 255, 255), 4); cv2.putText(pad, desc, (125, y + 40), 0, 1.05, (200, 200, 200), 2)
y = 200 + len(ZONES) * 130; cv2.rectangle(pad, (30, y - 50), (100, y + 10), (40, 40, 40), -1); cv2.rectangle(pad, (30, y - 50), (100, y + 10), (255, 255, 255), 2)
cv2.putText(pad, "gol (G)", (125, y - 10), 0, 1.5, (255, 255, 255), 4); cv2.putText(pad, "ferestrele buclelor si fanta dintre brate", (125, y + 40), 0, 1.05, (200, 200, 200), 2)
np.savez_compressed(f"{O}/jos_zone.npz", **{k: v for k, v in res.items()})
cv2.imwrite(f"{O}/jos_zone.png", cv2.resize(np.hstack([out, pad]), None, fx=0.5, fy=0.5)); print("ZONES", {k: int(v.sum()) for k, v in res.items()})
