# The shoulder where brat_spate, PS and 103 meet pulled up under 103 (asked: "umărul tras nițel în sus să fie acoperit de
# 103"): the PS's and the rear arm's vertices that lie under 103 seen from above but below 103's bottom face are measured
# per y; the lift needed (+ MARJA m), smoothed along y, is one field A(y) * w(x from the axis) * w(z, bottom part only),
# applied the same to PS and both rear arms (mirrored about the axis), so the arm's mouth stays glued to the PS.
# Usage: python umar_ridicat.py <pieces.npz> <103_D.npz (ship coords)> <out.npz> ; env UMAR_MARJA=1 UMAR_Z0=282 UMAR_Z1=298
import sys, os, numpy as np
from scipy.ndimage import gaussian_filter1d
D = np.load(sys.argv[1]); R = np.load(sys.argv[2])["v"].astype(float).reshape(-1, 4, 3); OUT = sys.argv[3]; MX = -1700.0
MARJA = float(os.environ.get("UMAR_MARJA", "1")); Z0, Z1 = float(os.environ.get("UMAR_Z0", "282")), float(os.environ.get("UMAR_Z1", "298"))
ys = R[:, 3, 1]; o = np.argsort(ys)
def bottom(x, y):                                       # 103's bottom face: inner bottom edge -> bottom of the small outer side
    xr, zr = np.interp(y, ys[o], R[o, 3, 0]), np.interp(y, ys[o], R[o, 3, 2]); xs, zs = np.interp(y, ys[o], R[o, 2, 0]), np.interp(y, ys[o], R[o, 2, 2])
    t = np.clip((x - xr) / (xs - xr), 0, 1); return zr + t * (zs - zr), (x >= xr) & (x <= xs)
YW = [float(x_) for x_ in os.environ.get("UMAR_Y", "-125,-30,20").split(",")]   # the shoulder's y window + fade (m)
yb = np.arange(YW[0] - YW[2], YW[1] + YW[2] + 1, 2.0); need = np.zeros(len(yb))
for n in ("PS", "brat_spate_D"):
    w = D[n + "__v"].astype(float).copy(); w[:, 0] -= MX; zb, under = bottom(w[:, 0], w[:, 1]); low = under & (w[:, 2] < zb + MARJA)
    low &= (w[:, 1] >= YW[0]) & (w[:, 1] <= YW[1])
    k = np.clip(np.round((w[low, 1] - yb[0]) / 2).astype(int), 0, len(yb) - 1)
    np.maximum.at(need, k, zb[low] + MARJA - w[low, 2])
ins = (yb >= YW[0]) & (yb <= YW[1]); need[ins] = np.maximum(need[ins], gaussian_filter1d(need, 3)[ins])
A = gaussian_filter1d(np.where(ins, need, 0), 2)
fade = np.clip(np.minimum(yb - (YW[0] - YW[2]), (YW[1] + YW[2]) - yb) / YW[2], 0, 1); A = np.maximum(A, np.interp(yb, yb[ins], need[ins]) * fade * fade * (3 - 2 * fade))
A = gaussian_filter1d(A, 3); print("UMAR: ridicare necesara max %.1f m (y %.0f), zona y %.0f..%.0f" % (
    need.max(), yb[np.argmax(need)], yb[need > 0].min(), yb[need > 0].max()))
xin = np.interp(yb, ys[o], R[o, 3, 0])                  # 103's inner bottom edge per y: the lift fades in over 20 m before it
def field(p):
    x, y, z = np.abs(p[:, 0] - MX), p[:, 1], p[:, 2]
    a = np.interp(y, yb, A, left=0, right=0); x0 = np.interp(y, yb, xin) - 20
    wx = np.clip((x - x0) / 20, 0, 1); wx = wx * wx * (3 - 2 * wx); wz = np.clip((Z1 - z) / (Z1 - Z0), 0, 1); wz = wz * wz * (3 - 2 * wz)
    return a * wx * wz
out = {}
for n in ("PS", "brat_spate_D", "brat_spate_S"):
    v = D[n + "__v"].astype(float); f = D[n + "__f"]; d = field(v); V = v.copy(); V[:, 2] += d; out[n] = V
    n0 = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); n1 = np.cross(V[f[:, 1]] - V[f[:, 0]], V[f[:, 2]] - V[f[:, 0]])
    print("%s: %d varfuri ridicate (max %.1f m), fete intoarse %d" % (n, (d > 0.05).sum(), d.max(), ((n0 * n1).sum(1) < 0).sum()))
for n in ("PS", "brat_spate_D"):                        # check: what is still below 103's bottom
    w = out[n].copy(); w[:, 0] -= MX; zb, under = bottom(w[:, 0], w[:, 1]); low = under & (w[:, 2] < zb - 0.05) & (w[:, 1] >= YW[0]) & (w[:, 1] <= YW[1])
    print("VERIFICARE %s: sub fata de jos a lui 103 raman %d varfuri (max %.2f m)" % (n, low.sum(), (zb - w[:, 2])[low].max() if low.any() else 0))
np.savez(OUT, **out)
