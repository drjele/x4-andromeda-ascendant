# The ship's outline against ref 01 in world numbers: the ref silhouettes (overlay/ref01/<view>_mask.png) sampled on a
# world grid through the corrected fit, and the version's mesh rasterised on the same grid; prints the arms' extents
# from above (rear loop end, front tip length and spread) and the side profile's top/bottom per y.
# Usage: python ref_extents.py <mesh.npz> [group-prefix]
import sys, json, numpy as np, cv2
T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; Z = np.load(sys.argv[1]); PRE = sys.argv[2] if len(sys.argv) > 2 else ""
FIT = json.load(open(f"{T}/trace/fit_ref01.json")); ORTHO = json.load(open(f"{T}/view/ref01/views.json")); AX = json.load(open(f"{T}/trace/cam_axes.json"))
VOX = 4.0; g = [np.arange(-1100, 1100.1, VOX), np.arange(-1900, 1700.1, VOX), np.arange(-500, 500.1, VOX)]
def to_ref(view, p):
    n, s, k = ORTHO[view]["res"], ORTHO[view]["scale"], ORTHO[view]["rot"]; sx, sy, tx, ty = FIT[view]["p"]
    u = p @ np.array(AX[view]["right"]); w = p @ np.array(AX[view]["up"]); col = u / s * n + n / 2; row = n / 2 - w / s * n
    i, j = {0: (row, col), 1: (n - col, row), -1: (col, n - row)}[k]
    if FIT[view].get("flip"): j = n - j
    return sx * j + tx, sy * i + ty
def ref(view, a, b):
    m = cv2.imread(f"{T}/overlay/ref01/{view}_mask.png", 0) > 127
    A, B = np.meshgrid(g[a], g[b], indexing="ij"); p = np.zeros(A.shape + (3,)); p[..., a] = A; p[..., b] = B
    x, y = to_ref(view, p.reshape(-1, 3)); x = np.round(x).astype(int); y = np.round(y).astype(int)
    ok = (x >= 0) & (y >= 0) & (x < m.shape[1]) & (y < m.shape[0]); out = np.zeros(x.shape, bool); out[ok] = m[y[ok], x[ok]]; return out.reshape(A.shape)
def model(a, b, pre=""):
    m = np.zeros((len(g[b]), len(g[a])), np.uint8)
    for k in [k[2:] for k in Z.files if k.startswith("v|") and not k.startswith("v|SRC") and k[2:].startswith(pre)]:
        v = Z[f"v|{k}"]; t = Z[f"t|{k}"]; q = np.stack([(v[:, a] - g[a][0]) / VOX, (v[:, b] - g[b][0]) / VOX], 1)
        for tri in np.round(q[t]).astype(np.int32): cv2.fillConvexPoly(m, tri, 1)
    return m.T.astype(bool)
R, M = ref("top", 0, 1), model(0, 1); x, y = g[0], g[1]
def ext(m, name):
    rows = m[x > 300]; ys = y[rows.any(0)]; front = m[:, y > 900]; xs_f = x[front.any(1)]
    print("TOP %-6s rear end y %6.0f   front tip y %6.0f   x span at y>900: %4.0f..%4.0f   x at y=1200: %s" % (name, ys.min(), ys.max(), xs_f.min() if len(xs_f) else 0, xs_f.max() if len(xs_f) else 0,
          x[m[:, np.argmin(abs(y - 1200))]].round().tolist()[::8]))
ext(R, "ref"); ext(M, "model")
Rs, Ms = ref("side", 1, 2), model(1, 2); zz = g[2]
print("SIDE y      ref top/bottom   model top/bottom")
for yy in range(-1300, 1401, 100):
    j = np.argmin(abs(y - yy)); r, mm = zz[Rs[j]], zz[Ms[j]]
    print("SIDE %5d   %5s %5s      %5s %5s" % (yy, *(("%.0f" % r.max(), "%.0f" % r.min()) if len(r) else ("-", "-")), *(("%.0f" % mm.max(), "%.0f" % mm.min()) if len(mm) else ("-", "-"))))
