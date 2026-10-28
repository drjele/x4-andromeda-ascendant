# All confirmed views on one drawing sheet, laid out like an engineering drawing with the bow up: the top view in the
# middle (width across, length down), the bottom view to its right and the side view to its left (sharing the length
# rows), the back view under the top view and the front view above it (sharing the width columns). The top view sets
# the scale; bottom and side are matched to its length (bow tip to stern), back and front to its width. Dashed
# projection lines run from every top-view line's ends along the length (through side/top/bottom) and from its
# outermost width (through front/top/back). Prints how each view's own other dimension compares (side height vs
# back/front height, bottom width vs top width), which is the cross-check between views.
# Usage: python multiview.py <spec.json> <out.png>
#   spec: {"top": {"lines": path, "axis": row}, "bottom": {...}, "side": {"lines": path}, "back": {"lines": path, "axis": col},
#          "front": {...}}, "match": {"own": [line numbers], "top": [line numbers]} scales back/front on one part instead of
#          the full width (a view cut by its frame), "match": "axis_height" on the back view's centreline height; any view may carry "lat_scale" (its width stretched, e.g. a reference drawn too narrow)  -- line files: view_lines.py output, or {name: [curves]} / {name: {"points": ...}} / {key: [curves]}
import sys, json, numpy as np, cv2
S = json.load(open(sys.argv[1])); OUT = sys.argv[2]
def load(path):
    d = json.load(open(path)); out = []
    if isinstance(d, list):
        for l in d: out.append((str(l["n"]), [np.array(c, float) for c in l["curves"]]))
    else:
        for k, v in d.items():
            if isinstance(v, dict): out.append((k, [np.array(v["points"], float)]))
            else:
                for j, c in enumerate(v): out.append(("%s%d" % (k[:2].upper(), j + 1) if len(v) > 1 else k, [np.array(c, float)]))
    return [(n, cs) for n, cs in out if max(np.ptp(c[:, 0]) + np.ptp(c[:, 1]) for c in cs) > 20]
V = {k: load(v["lines"]) for k, v in S.items()}
def ext(lines, j): p = np.vstack([c for _, cs in lines for c in cs]); return p[:, j].min(), p[:, j].max()
HALF, PAD = 700, 90
# top: u = lateral (row - axis), l = length (x)
t_ax = S["top"]["axis"]; t_l0, t_l1 = ext(V["top"], 0); t_half = max(np.abs(c[:, 1] - t_ax).max() for _, cs in V["top"] for c in cs); s = HALF / t_half
LEN = (t_l1 - t_l0) * s
def tf_plan(lines, ax, l0, l1, lat=1.0):                                   # top/bottom -> (x across, y down the length)
    k = LEN / (l1 - l0); return [(n, [np.stack([(c[:, 1] - ax) * k * lat, (c[:, 0] - l0) * k], 1) for c in cs]) for n, cs in lines], k
panels = {}
panels["top"], kt = tf_plan(V["top"], t_ax, t_l0, t_l1, S["top"].get("lat_scale", 1.0)); KV = {"top": (kt, t_ax, t_l0)}; HALF = max(np.abs(c[:, 0]).max() for _, cs in panels["top"] for c in cs)
report = []
if "bottom" in V:
    b0, b1 = ext(V["bottom"], 0); panels["bottom"], kb = tf_plan(V["bottom"], S["bottom"]["axis"], b0, b1, S["bottom"].get("lat_scale", 1.0))
    bh = max(np.abs(c[:, 0]).max() for _, cs in panels["bottom"] for c in cs); KV["bottom"] = (kb, S["bottom"]["axis"], b0)
    report.append("jos: latimea %.2f fata de sus (1.00)" % (bh / HALF))
side_h = None
if "side" in V:
    x0, x1 = ext(V["side"], 0); z0, z1 = ext(V["side"], 1); k = LEN / (x1 - x0)
    panels["side"] = [(n, [np.stack([(z1 - c[:, 1]) * k, (c[:, 0] - x0) * k], 1) for c in cs]) for n, cs in V["side"]]   # x = height (up -> right), y = length
    side_h = (z1 - z0) * k; KV["side"] = (k, x0, z1)
for key in ("back", "front"):
    if key not in V: continue
    ax = S[key]["axis"]; half = max(np.abs(c[:, 0] - ax).max() for _, cs in V[key] for c in cs); k = HALF / half; z0, z1 = ext(V[key], 1)
    if S[key].get("match") == "axis_height" and "back" in panels:           # a view cut by its frame: its centreline height (top of PS to the
        def cl(pts): m = np.abs(pts[:, 0]) < 25; return np.ptp(pts[m, 1])     # bottom of the lower deck) equals the back view's
        own = cl(np.vstack([np.stack([c[:, 0] - ax, c[:, 1]], 1) for _, cs in V[key] for c in cs]))
        k = cl(np.vstack([c for _, cs in panels["back"] for c in cs])) / own
    elif "match" in S[key]:                                                  # a view cut by its frame: scaled on a part both views show whole
        own = max(np.abs(c[:, 0] - ax).max() for n, cs in V[key] if n in S[key]["match"]["own"] for c in cs)
        ref = max(np.abs(c[:, 0]).max() for n, cs in panels["top"] if n in S[key]["match"]["top"] for c in cs); k = ref / own
    panels[key] = [(n, [np.stack([(c[:, 0] - ax) * k, (c[:, 1] - z0) * k], 1) for c in cs]) for n, cs in V[key]]
    h = (z1 - z0) * k; KV[key] = (k, ax, z0)
    if side_h: report.append("%s: inaltimea %.2f fata de profil (1.00)" % ({"back": "spate", "front": "fata"}[key], h / side_h))
def size(p): q = np.vstack([c for _, cs in p for c in cs]); return q.min(0), q.max(0)
sw = size(panels["side"])[1][0] if "side" in panels else 0
bh_ = size(panels["back"])[1][1] if "back" in panels else 0; fh = size(panels["front"])[1][1] if "front" in panels else 0
cx_top = PAD + sw + PAD + HALF; y_top = PAD + fh + PAD
W = int(cx_top + HALF + PAD + (2 * HALF + PAD if "bottom" in panels else 0)); H = int(y_top + LEN + PAD + bh_ + PAD)
img = np.full((H, W, 3), 18, np.uint8)
place = {"top": (cx_top, y_top), "bottom": (cx_top + 2 * HALF + PAD, y_top), "side": (PAD, y_top),
         "back": (cx_top, y_top + LEN + PAD), "front": (cx_top, PAD)}
col = {"top": (0, 220, 255), "bottom": (120, 255, 120), "side": (255, 140, 255), "back": (255, 200, 0), "front": (90, 160, 255)}
tag = {"top": "S", "bottom": "J", "side": "", "back": "P", "front": "F"}
name = {"top": "SUS", "bottom": "JOS", "side": "PROFIL", "back": "SPATE", "front": "FATA"}
# projection lines first (under the drawing)
for n, cs in panels["top"]:
    for c in cs:
        for y in (c[:, 1].min(), c[:, 1].max()):
            yy = int(y_top + y)
            for x in range(PAD // 2, W - PAD // 2, 16): cv2.line(img, (x, yy), (x + 8, yy), (70, 70, 70), 1)
    u = max(np.abs(c[:, 0]).max() for c in cs)
    for sg in (-1, 1):
        xx = int(cx_top + sg * u)
        for y in range(PAD // 2, H - PAD // 2, 16): cv2.line(img, (xx, y), (xx, y + 8), (70, 70, 70), 1)
for key, lines in panels.items():
    ox, oy = place[key]
    cv2.putText(img, name[key], (int(ox - (HALF if key in ("top", "bottom", "back", "front") else 0)), int(oy) - 20), 0, 1.1, col[key], 2, cv2.LINE_AA)
    for n, cs in lines:
        for c in cs: cv2.polylines(img, [np.round(c + [ox, oy]).astype(np.int32)], False, col[key], 2, cv2.LINE_AA)
        c0 = cs[0]; p = c0[len(c0) // 2] + [ox, oy]
        cv2.putText(img, tag[key] + n, (int(p[0]) + 5, int(p[1]) - 5), 0, 0.55, (235, 235, 235), 1, cv2.LINE_AA)
for j, r in enumerate(report): cv2.putText(img, r, (PAD, H - 30 - 34 * j), 0, 0.9, (235, 235, 235), 2, cv2.LINE_AA)
# the sheet-px -> canvas affine of every view, for drawing other things (zones, parts) on the same layout
AFF = {}
for key, (k, a, b) in KV.items():
    ox, oy = place[key]; lat = S[key].get("lat_scale", 1.0)
    if key in ("top", "bottom"): AFF[key] = [[0, k * lat, ox - a * k * lat], [k, 0, oy - b * k]]
    elif key == "side": AFF[key] = [[0, -k, ox + b * k], [k, 0, oy - a * k]]
    else: AFF[key] = [[k, 0, ox - a * k], [0, k, oy - b * k]]
json.dump({"size": [W, H], "aff": AFF}, open(OUT.replace(".png", "_layout.json"), "w"), indent=1)
cv2.imwrite(OUT, img); print("\n".join(report)); print(OUT)
