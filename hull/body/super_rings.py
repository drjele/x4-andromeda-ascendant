# Body rings from body_super.json: profiles sampled every 2 m, smoothed along the ship so the
# curvature is continuous, the bow flattened slightly at the very tip. Also writes body_grid.json.
import json, numpy as np
from scipy.interpolate import PchipInterpolator
P = json.load(open("body_super.json")); y = np.array(P["y"], float)
f = {k: PchipInterpolator(y, np.array(P[k], float)) for k in ("a", "b", "zc", "n")}
ftop = PchipInterpolator(np.array(P["top_y"], float), np.array(P["top_z"], float))
STEP, SIGMA = 2.0, P.get("smooth_m", 14.0)
Y = np.arange(y[0], y[-1] + 1e-6, STEP); Y[-1] = y[-1]
A, B, ZC, N = (f[k](Y) for k in ("a", "b", "zc", "n")); TOP = ftop(Y)
def smooth(v):
    r = int(3 * SIGMA / STEP); k = np.exp(-0.5 * (np.arange(-r, r + 1) * STEP / SIGMA) ** 2); k /= k.sum()
    return np.convolve(np.pad(v, r, mode="edge"), k, "valid")
BOT = ZC - B
A, BOT, TOP, N = smooth(A), smooth(BOT), smooth(TOP), smooth(N)
# flatten the tip a little: the last stretch is squeezed vertically toward its centre line
sq0, sq = P.get("tip_squash", [80.0, 0.3])
w = np.clip((Y - (y[-1] - sq0)) / sq0, 0, 1); w = w * w
mid = (TOP + BOT) / 2; TOP = mid + (TOP - mid) * (1 - sq * w); BOT = mid + (BOT - mid) * (1 - sq * w)
# close each end with a cap that starts with the hull's own slope and ends round:
# r(x) = sqrt(r0^2 + 2 r0 s0 x - c x^2), r'(0) = s0, r(L) = 0 with a vertical tangent
def cap_end(end, Lmax):
    sgn = -1 if end == -1 else 1
    best = Lmax
    for L in np.arange(Lmax, 6, -2.0):
        j0 = int(np.argmin(np.abs(np.abs(Y - Y[end]) - L)))
        ok = True
        for v in (A, TOP - mid, mid - BOT):
            r0 = v[j0]; s0 = (v[j0 - sgn] - v[j0 + sgn]) / (2 * STEP) * 1.0 if 0 < j0 < len(Y) - 1 else 0.0
            # slope measured toward the end
            s0 = (v[j0 + (1 if end == -1 else -1)] - v[j0]) / STEP
            if r0 + 2 * s0 * L <= 0.05 * r0: ok = False
        if ok: best = L; break
    L = best; j0 = int(np.argmin(np.abs(np.abs(Y - Y[end]) - L))); m0 = mid[j0]
    xs = np.abs(Y - Y[j0]); m = (np.abs(Y - Y[end]) < np.abs(Y[j0] - Y[end]))
    out = []
    for v in (A, TOP - mid, mid - BOT):
        r0 = v[j0]; s0 = (v[j0 + (1 if end == -1 else -1)] - v[j0]) / STEP
        c = (r0 * r0 + 2 * r0 * s0 * L) / (L * L)
        out.append(np.sqrt(np.clip(r0 * r0 + 2 * r0 * s0 * xs[m] - c * xs[m] ** 2, 0, None)))
    A[m] = out[0]; mid[m] = m0; TOP[m] = m0 + out[1]; BOT[m] = m0 - out[2]
    return L
print("tip cap", cap_end(-1, P.get("tip_cap", 60.0)), "stern cap", cap_end(0, 12.0))
ZC = (TOP + BOT) / 2; HB = (TOP - BOT) / 2
ANG = 128; th = 2 * np.pi * np.arange(ANG) / ANG; c, s = np.cos(th), np.sin(th)
top_n = P.get("top_n", 2.0)
rings = []
for i, yy in enumerate(Y):
    nn = np.where(s > 0, top_n, N[i])
    x = A[i] * np.sign(c) * np.abs(c) ** (2 / nn); z = ZC[i] + HB[i] * np.sign(s) * np.abs(s) ** (2 / nn)
    rings.append([[float(u), float(yy), float(v)] for u, v in zip(x, z)])
json.dump(rings, open("super_rings.json", "w"))
json.dump({"y": Y.tolist(), "a": A.tolist(), "b": HB.tolist(), "zc": ZC.tolist(), "n": N.tolist(), "bt": HB.tolist()}, open("body_grid.json", "w"))
print(len(rings), "rings")
