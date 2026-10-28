# The confirmed outlines of every view as 3D polylines in the model's world frame (x across, y bow+, z up), at the
# proportions the user chose (length L, width L/1.84, height L/3.96): each view's lines mapped by their own extent onto
# the matching face of the box (top on z=+H/2, bottom on z=-H/2, side on x=-W/2, back on y=stern, front on y=bow,
# the front aligned on its top edge because the drawing is cut below). Writes JSON {view: [[x,y,z]...]}.
# Usage: python contours_world.py <spec.json> <length_m> <y_bow> <out.json>
import sys, json, numpy as np
S = json.load(open(sys.argv[1])); L = float(sys.argv[2]); YB = float(sys.argv[3]); OUT = sys.argv[4]
W, H = L / 1.84, L / 3.96; YS = YB - L
def load(p):
    d = json.load(open(p))
    if isinstance(d, list): return [np.array(c, float) for l in d for c in l["curves"]]
    out = []
    for k, v in d.items():
        if isinstance(v, dict): out.append(np.array(v["points"], float))
        else: out += [np.array(c, float) for c in v]
    return out
res = {}
for view, spec in S.items():
    cs = [c for c in load(spec["lines"]) if len(c) > 2]; P = np.vstack(cs); x0, y0 = P.min(0); x1, y1 = P.max(0)
    out = []
    for c in cs:
        if view in ("top", "bottom"):                                      # sheet x: bow (left) -> stern, sheet y: across
            ax = spec["axis"]; k = L / (x1 - x0)
            X = (c[:, 1] - ax) * k * (W / (2 * max(abs(y0 - ax), abs(y1 - ax)) * k)); Y = YB - (c[:, 0] - x0) * k
            Z = np.full(len(c), H / 2 + 20 if view == "top" else -H / 2 - 20)
        elif view == "side":
            k = L / (x1 - x0); Y = YB - (c[:, 0] - x0) * k; Z = H / 2 - (c[:, 1] - y0) * (H / (y1 - y0)); X = np.full(len(c), -W / 2 - 20)
        else:
            ax = spec["axis"]; k = W / (2 * max(abs(x0 - ax), abs(x1 - ax))); X = (c[:, 0] - ax) * k
            Z = H / 2 - (c[:, 1] - y0) * k * (1 if view == "front" else H / ((y1 - y0) * k)); Y = np.full(len(c), YB + 20 if view == "front" else YS - 20)
        out.append(np.stack([X, Y, Z], 1).round(2).tolist())
    res[view] = out; print(view, len(out), "lines")
json.dump(res, open(OUT, "w"))
