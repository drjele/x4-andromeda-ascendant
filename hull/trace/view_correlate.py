# Two confirmed views correlated on the dimension they share, the way an engineering drawing is laid out: each view's
# numbered lines (view_lines.py) brought to one scale on the shared axis (matched on the ship's full extent there),
# the views stacked, and projection lines dropped from every line's outermost point in the first view through the
# second, so the user sees which line of one view meets which line of the other. Prints each line's extent on the
# shared axis as a share of the half width.
# Usage: python view_correlate.py <out.png> <name>:<lines.json>:<axis>:<h|v>:<down|up|...> <name>:<lines.json>:<axis>:<h|v>:<...>
#   h = the centreline is a row (shared axis = rows of that image), v = a column; the 5th field orients the other axis
#   in the sheet ("flip" turns it over).
import sys, json, numpy as np, cv2
OUT = sys.argv[1]; views = []
for spec in sys.argv[2:4]:
    name, path, ax, ad, ori = spec.split(":"); ax = float(ax); D = json.load(open(path)); k = 1 if ad == "h" else 0
    lines = [(l["n"], [np.stack([np.array(c)[:, k] - ax, np.array(c)[:, 1 - k]], 1) for c in l["curves"]]) for l in D]
    lines = [(n, cs) for n, cs in lines if max(np.ptp(c[:, 0]) + np.ptp(c[:, 1]) for c in cs) > 20]   # degenerate stubs out
    M = max(np.abs(c[:, 0]).max() for _, cs in lines for c in cs)
    if ori == "flip": lines = [(n, [np.stack([c[:, 0], -c[:, 1]], 1) for c in cs]) for n, cs in lines]
    views.append((name, lines, M))
HALF = 760; PAD = 60; panels = []
for name, lines, M in views:                                               # lateral -> [-HALF, HALF] px, the other axis at the same scale
    s = HALF / M; pts = np.vstack([c for _, cs in lines for c in cs]); o0, o1 = pts[:, 1].min(), pts[:, 1].max()
    panels.append((name, [(n, [np.stack([c[:, 0] * s, (c[:, 1] - o0) * s], 1) for c in cs]) for n, cs in lines], (o1 - o0) * s, M))
Wc = 2 * HALF + 2 * PAD + 420; Hc = int(sum(p[2] for p in panels) + PAD * (len(panels) + 2)); img = np.full((Hc, Wc, 3), 18, np.uint8)
cx = PAD + HALF; y0 = PAD; cols = [(0, 220, 255), (255, 200, 0)]; tops = []
for pi, (name, lines, h, M) in enumerate(panels):
    cv2.putText(img, name, (12, int(y0) + 30), 0, 1.0, cols[pi], 2, cv2.LINE_AA); cv2.line(img, (cx, int(y0)), (cx, int(y0 + h)), (90, 90, 90), 1)
    for n, cs in lines:
        for c in cs: cv2.polylines(img, [np.round(c + [cx, y0]).astype(np.int32)], False, cols[pi], 2, cv2.LINE_AA)
        c0 = cs[0]; p = c0[len(c0) // 2] + [cx, y0]; t = ("S" if pi == 0 else "P") + str(n)
        cv2.putText(img, t, (int(p[0]) + 6, int(p[1]) - 6), 0, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    tops.append((y0, h)); y0 += h + PAD
# projection lines from each line of the first view at its outermost lateral point
name, lines, h, M = panels[0]; rows = []
for n, cs in lines:
    u = max(np.abs(c[:, 0]).max() for c in cs)
    for sg in (-1, 1):
        x = int(cx + sg * u)
        for yy in range(int(tops[0][0]), Hc - PAD, 14): cv2.line(img, (x, yy), (x, min(yy + 7, Hc - PAD)), (120, 120, 120), 1)
    rows.append((n, u / HALF))
for pi, (name, lines, h, M) in enumerate(panels):
    print(name, " ".join("%s%d %.2f" % ("S" if pi == 0 else "P", n, max(np.abs(c[:, 0]).max() for c in cs) / HALF) for n, cs in lines))
cv2.imwrite(OUT, img); print(OUT)
