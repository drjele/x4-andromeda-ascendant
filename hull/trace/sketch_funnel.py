# A gap redrawn as an even funnel: the curves that bounded it (picked by their midpoints) replaced by one closed
# outline built on their centre line, widest at the chosen end with a round cap, tapering smoothly to a point at the
# other end; mirrored about the view's centreline (row `axis`) for the other half.
# Usage: python sketch_funnel.py <network.json> <funnel.json>
import sys, json, numpy as np
NET, FJ = sys.argv[1:3]; C = [np.array(c) for c in json.load(open(NET))]; F = json.load(open(FJ)); AX = F["axis"]
mirror = lambda c: np.stack([c[:, 0], 2 * AX - c[:, 1]], 1)
def pick(mid):
    return min(range(len(C)), key=lambda i: np.hypot(*(C[i][len(C[i]) // 2] - mid)))
def chain(mids, start):
    # the picked curves joined end to end into one polyline starting at `start`
    parts = [C[pick(m)] for m in mids]; out = np.array([start], float)
    for p in parts:
        if np.hypot(*(p[-1] - out[-1])) < np.hypot(*(p[0] - out[-1])): p = p[::-1]
        out = np.vstack([out, p])
    return out
def resample(p, n):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]; t = np.linspace(0, d[-1], n); return np.stack([np.interp(t, d, p[:, i]) for i in (0, 1)], 1)
top = resample(chain(F["top"], F["wide_end"]), 400); bot = resample(chain(F["bottom"], F["wide_end"]), 400)
mid = np.array([(b + top[np.argmin(np.hypot(*(top - b).T))]) / 2 for b in bot]); k = np.exp(-0.5 * (np.arange(-40, 41) / 14) ** 2); k /= k.sum()
mid = np.stack([np.convolve(np.pad(mid[:, i], 40, mode="edge"), k, "valid") for i in (0, 1)], 1)
mid = mid[int(len(mid) * F.get("start", 0.0)):]; mid = resample(mid, 300)
t = np.linspace(0, 1, len(mid)); w = F["width"] / 2 * (1 - t) ** F.get("taper", 0.9)          # half width, 0 at the narrow tip
tg = np.gradient(mid, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]; nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
side_a = mid + nr * w[:, None]; side_b = mid - nr * w[:, None]
th = np.linspace(0, np.pi, 40)[:, None]; cap = mid[0] + w[0] * (np.cos(th) * nr[0] - np.sin(th) * tg[0])   # round cap from side a to side b, bulging backward
outline = np.vstack([side_a[::-1], cap[1:-1], side_b])
drop = {pick(m) for m in F["top"] + F["bottom"]} | {pick(np.array([m[0], 2 * AX - m[1]])) for m in F["top"] + F["bottom"]}
keep = [c for i, c in enumerate(C) if i not in drop] + [outline, mirror(outline)]
json.dump([c.tolist() for c in keep], open(NET, "w")); print("FUNNEL replaced %d curves, length %.0f px, width %.0f" % (len(drop), np.hypot(*np.diff(mid, axis=0).T).sum(), F["width"]))
