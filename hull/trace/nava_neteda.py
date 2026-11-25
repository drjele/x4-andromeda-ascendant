# The missing components as smooth, decoration-free surfaces in the confirmed ship's frame (S half, mirrored): the arm BS + BJ is one
# sweep that starts as the confirmed arm row by row (tube) and turns into a flat bar; CORP and the deck (etaj) are sections of rounded
# half-planes whose sizes run smoothly along y; AI, AS, PI + ARCU are smooth solids that carry the tangent blend to their neighbours, so
# the neighbours stay untouched. Implicit pieces are meshed at CELL m and every vertex put exactly on the surface.
# Usage: python nava_neteda.py <dir with npz>  -> neteda.npz (v__<piece>, f__<piece>)
import sys, numpy as np
from scipy.interpolate import PchipInterpolator, CubicSpline
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes
D = sys.argv[1]; CELL = 4.0; OUT = {}
def curve(d, sig=35):                                                       # smooth function through a table (monotone, then softened)
    x = np.array(sorted(d)); f = PchipInterpolator(x, [d[k] for k in x]); s = np.arange(x[0] - 200, x[-1] + 201, 2.0); v = f(np.clip(s, x[0], x[-1])); v = gaussian_filter1d(v, sig / 2, mode="nearest")
    return lambda t: np.interp(t, s, v)
def smax(p, q, k): h = np.maximum(k - np.abs(p - q), 0) / k; return np.maximum(p, q) + h * h * k / 4
def smin(p, q, k): return -smax(-p, -q, k)
# --- arm: BS (confirmed rows) -> BJ
d = np.load(f"{D}/ASAMBLAT_NOU.npz"); n = list(d["n"]); V = d["v"][np.unique(d["t"][d["o"] == n.index("an_brat_spate_S")])]
G = V[:1288 * 96].reshape(1288, 96, 3) * [-1, 1, 1]; C = G.mean(1); i0 = np.where((C[:, 1] < -1200) & (C[:, 2] < 168))[0][0]; i1 = np.where((np.arange(1288) > i0) & (C[:, 1] > -1080))[0][0]; i2 = np.where((np.arange(1288) > i0) & (C[:, 1] > -640))[0][0]
ctrl = np.array([[577, -450, -221], [591, -300, -241], [599, -150, -258], [602, 0, -270], [598, 150, -279], [590, 300, -283], [579, 450, -281], [566, 600, -276], [550, 750, -270], [527, 900, -264], [502, 1050, -259], [478, 1200, -255], [462, 1310, -257]], float)
P = np.vstack([C[i0:i2:20], ctrl]); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; cs = CubicSpline(s, P); ss = np.arange(0, s[-1], 4.0); path = cs(ss); sm = gaussian_filter1d(path, 30, axis=0, mode="nearest")
w = np.clip((path[:, 1] + 800) / 250, 0, 1) * np.clip((s[-1] - ss) / 250, 0, 1); w = w * w * (3 - 2 * w); path = path * (1 - w)[:, None] + sm * w[:, None]
tan = np.gradient(path, axis=0); tan /= np.linalg.norm(tan, axis=1)[:, None]
out = np.array([1.0, 0, 0]); e1 = out - tan * tan[:, :1]; e1 /= np.linalg.norm(e1, axis=1)[:, None]; e2 = np.cross(tan, e1)
kt = cKDTree(C[i0:]); near = i0 + kt.query(path)[1]
def axes(row):                                                             # wide axis, half sizes of a confirmed row
    X = row - row.mean(0); u, sv, vt = np.linalg.svd(X); return vt[0], np.ptp(X @ vt[0]) / 2, np.ptp(X @ vt[1]) / 2
A0, B0, ph = np.zeros(len(path)), np.zeros(len(path)), np.zeros(len(path))
for i, r in enumerate(near): wd, A0[i], B0[i] = axes(G[r]); ph[i] = np.arctan2(wd @ e2[i], wd @ e1[i])
ph = np.unwrap(2 * ph) / 2; k1 = np.where(path[:, 1] > -1080)[0]; k1 = k1[k1 > 20][0]; A0[k1:], B0[k1:], = A0[k1], B0[k1]; ph[k1:] = ph[k1]
tgt = np.array([.80, 0, -.60]); pt = np.arctan2(e2 @ tgt, e1 @ tgt); pt = pt + np.pi * np.round((ph[k1] - pt) / np.pi); pt = np.unwrap(2 * pt) / 2; pt += np.pi * np.round((ph[k1] - pt[k1 + 80]) / np.pi)
step = lambda x, lo, hi: (lambda q: q ** 3 * (q * (6 * q - 15) + 10))(np.clip((x - lo) / (hi - lo), 0, 1))
y = path[:, 1]; b = step(ss, ss[k1], ss[k1] + 640); phi = ph * (1 - b) + pt * b; print("rasucire BJ grade", np.degrees(phi[k1]).round(1), "->", np.degrees(phi[-1]).round(1))
Wt = curve({-1100: 2 * A0[k1], -800: 80, -640: 90, -450: 124, -300: 160, -150: 184, 0: 190, 150: 168, 300: 140, 450: 120, 600: 108, 750: 99, 900: 94, 1050: 90, 1200: 84, 1320: 76}, 60); Tt = curve({-1100: 2 * B0[k1], -640: 58, -450: 74, -300: 90, -150: 100, 0: 106, 150: 100, 300: 92, 450: 82, 600: 75, 750: 70, 900: 67, 1050: 64, 1200: 60, 1320: 56}, 60)
bb = step(ss, ss[k1], ss[k1] + 350); A = A0 * (1 - bb) + Wt(y) / 2 * bb; B = B0 * (1 - bb) + Tt(y) / 2 * bb; N = 2 + 2.2 * step(ss, ss[k1], ss[k1] + 700)
U = e1 * np.cos(phi)[:, None] + e2 * np.sin(phi)[:, None]; W = np.cross(tan, U)
def sweep(path, U, W, A, B, N, th):
    c, sn = np.cos(th), np.sin(th); q = 2 / N[:, None]; X = A[:, None] * np.sign(c) * np.abs(c) ** q; Y = B[:, None] * np.sign(sn) * np.abs(sn) ** q
    return path[:, None] + X[..., None] * U[:, None] + Y[..., None] * W[:, None]
r0 = G[near[k1]] - path[k1]; th = np.arctan2(r0 @ W[k1] / B[k1], r0 @ U[k1] / A[k1]); S = sweep(path, U, W, A, B, N, th)
pre = G[i0:near[k1]]; blend = np.arange(near[k1], 1288); print("BJ rand de legatura: abatere fata de bratul confirmat", np.abs(S[k1] - G[near[k1]]).max().round(3), "m")
off = G[near[k1]] - S[k1]; wo = 1 - step(ss[k1:], ss[k1], ss[k1] + 200); BJ = np.concatenate([pre, S[k1:] + off[None] * wo[:, None, None]]); BS = G[:i0 + 1]
def tube(R, capa, capb):
    m, nn = R.shape[:2]; i, j = np.meshgrid(np.arange(m - 1), np.arange(nn), indexing="ij"); a0 = i * nn + j; a1 = i * nn + (j + 1) % nn; f = np.concatenate([np.stack([a0, a1, a1 + nn], -1).reshape(-1, 3), np.stack([a0, a1 + nn, a0 + nn], -1).reshape(-1, 3)]); v = R.reshape(-1, 3); e = []
    for flag, r, rev in ((capa, 0, 1), (capb, m - 1, 0)):
        if flag: v = np.vstack([v, R[r].mean(0)]); k = np.arange(nn) + r * nn; t = np.stack([np.full(nn, len(v) - 1), k, np.roll(k, -1)], 1); e.append(t[:, ::-1] if rev else t)
    return v, np.concatenate([f] + e)
class Sweep:                                                               # first-order distance to a swept superellipse
    def __init__(s, path, U, W, A, B, N): s.p, s.U, s.W, s.A, s.B, s.N, s.t = path, U, W, A, B, N, cKDTree(path); s.T0 = (path[4] - path[0]) / np.linalg.norm(path[4] - path[0]); s.T1 = (path[-1] - path[-5]) / np.linalg.norm(path[-1] - path[-5])
    def __call__(s, p):
        dd, i = s.t.query(p, workers=4); r = p - s.p[i]; u = np.abs((r * s.U[i]).sum(1)) / s.A[i]; v = np.abs((r * s.W[i]).sum(1)) / s.B[i]; nn = s.N[i]
        u, v = np.maximum(u, 1e-6), np.maximum(v, 1e-6); q = (u ** nn + v ** nn) ** (1 / nn); g = np.hypot((u / q) ** (nn - 1) / s.A[i], (v / q) ** (nn - 1) / s.B[i]); e0 = -((p - s.p[0]) * s.T0).sum(1); e1 = ((p - s.p[-1]) * s.T1).sum(1); return np.maximum((q - 1) / g, np.maximum(e0, e1))
fine = lambda X: np.stack([np.interp(np.arange(0, len(X) - 1, .25), np.arange(len(X)), X[:, k]) for k in range(X.shape[1])], 1) if X.ndim > 1 else np.interp(np.arange(0, len(X) - 1, .25), np.arange(len(X)), X)
f_bj = Sweep(*map(fine, (path, U, W, A, B, N)))
jb = np.arange(0, i0, 2); cb = C[jb]; tb = np.gradient(cb, axis=0); tb /= np.linalg.norm(tb, axis=1)[:, None]; ax = [axes(G[j]) for j in jb]; Ub = np.array([q[0] for q in ax]); Ub *= np.sign((Ub * Ub[0]).sum(1))[:, None]; f_bs = Sweep(cb, Ub, np.cross(tb, Ub), np.array([q[1] for q in ax]), np.array([q[2] for q in ax]), np.full(len(jb), 2.0))
# --- CORP
zt = curve({-780: 50, 60: 48, 120: 38, 180: 34, 300: 27, 420: 20, 540: 12, 660: 5, 780: -3, 900: -16, 1020: -33, 1107: -55}, 30); zb = curve({-800: 46, -720: 6, -660: -14, -600: -37, -540: -60, -480: -79, -420: -95, -360: -112, -300: -128, -240: -144, -180: -156, -120: -166, -60: -175, 0: -184, 60: -193, 120: -201, 180: -207, 240: -211, 360: -217, 480: -220, 660: -220, 780: -209, 900: -196, 1020: -172, 1107: -130}, 40)
wh = curve({-790: 128, -720: 148, -660: 172, -600: 203, -540: 235, -480: 255, -420: 252, -300: 250, -180: 262, -60: 282, 0: 278, 60: 262, 120: 243, 180: 223, 240: 205, 300: 192, 360: 186, 480: 172, 600: 157, 720: 139, 840: 119, 960: 98, 1040: 74, 1107: 40}, 35); wl = curve({-790: 84, -720: 104, -660: 118, -600: 122, -540: 126, -480: 130, -300: 142, -180: 150, 0: 152, 180: 147, 360: 133, 600: 115, 780: 103, 900: 92, 1020: 66, 1107: 25}, 35)
def f_corp(p):
    a, y, z = np.abs(p[:, 0]), p[:, 1], p[:, 2]; t, bt, h, l = zt(y), zb(y), wh(y), wl(y); H = np.maximum(t - bt, 20); nx, nz = H, -(h - l); L = np.hypot(nx, nz); side = ((a - l) * nx + (z - bt) * nz) / L
    f = smax(side, bt + .07 * (np.sqrt(a * a + 4900) - 70) - z, 60); f = smax(f, z - t, np.interp(y, [150, 450], [22, 55])); f = smax(f, y - 1139, 130); return smax(f, -786 - y, 60)
# --- etaj
et = curve({-780: 138, -720: 150, -600: 161, -480: 168, -360: 166, -240: 160, -120: 148, 0: 138, 60: 135, 120: 128, 180: 113, 240: 95, 300: 75, 360: 53, 420: 30, 470: 8, 520: -20}, 30); we = curve({-780: 92, -720: 122, -660: 155, -600: 185, -540: 208, -480: 220, -420: 220, -240: 220, -120: 213, 0: 204, 60: 194, 120: 180, 180: 161, 240: 141, 300: 122, 360: 105, 480: 88}, 35)
wr = curve({-780: 135, -720: 158, -660: 182, -600: 214, -540: 245, -480: 268, -420: 252, -300: 244, -230: 262, -180: 300, -130: 342, -70: 356, -20: 334, 60: 288, 120: 258, 180: 228, 240: 204, 300: 183, 360: 163, 420: 145, 520: 120}, 35); wc = curve({60: 14, 100: 22, 180: 45, 240: 63, 300: 70, 420: 80, 520: 90}, 25)
eb = curve({-800: 28, 0: 28, 60: 28, 120: 22, 180: 18, 300: 12, 420: 5, 520: -5}, 30)
ek = curve({-800: 0, -380: 0, -220: .25, 520: .25}, 40)
def f_etaj(p):
    a, y, z = np.abs(p[:, 0]), p[:, 1], p[:, 2]; t, e, r = et(y), we(y), wr(y); zr = np.minimum(62, t - 8); nx, nz = t - zr, r - e; L = np.hypot(nx, nz); slope = ((a - e) * nx + (z - t) * nz) / L
    f = smax(z - t - .02 * (0 - a * 0), slope, 30); f = smax(f, a - r, 24); f = smax(f, eb(y) - z - ek(y) * np.maximum(0, r - np.sqrt(a * a + 900)), 20); f = smax(f, -782 - y - (z - 60) * .10, 50)
    ch = smax(a - wc(y), 92 - y, 34); return smax(f, -ch, 18)
f_body = lambda p: smin(f_corp(p), f_etaj(p), 22)
# --- AI
at = curve({160: 172, 200: 159, 250: 134, 310: 92, 370: 45, 430: -6, 490: -66, 540: -128, 580: -174, 640: -228}, 40); ab = curve({160: -64, 250: -64, 310: -64, 370: -78, 430: -122, 490: -180, 540: -222, 580: -246, 640: -280}, 30)
le = curve({160: -165, 220: -156, 250: -150, 310: -128, 370: -99, 430: -70, 470: -36, 500: 4, 530: 48, 560: 88, 640: 170}, 22); te = curve({160: -492, 250: -478, 310: -463, 370: -449, 430: -441, 480: -447, 520: -458, 560: -474, 640: -510}, 22)
slp = lambda f, a: 1 / np.sqrt(1 + ((f(a + 1) - f(a - 1)) / 2) ** 2)
def f_ai0(p):
    a, y, z = p[:, 0], p[:, 1], p[:, 2]; f = smax((z - at(a)) * slp(at, a), (y - le(a)) * slp(le, a), 85); g = smax((ab(a) - z) * slp(ab, a), (te(a) - y) * slp(te, a), 85); return smax(smax(f, g, 30), smax(175 - a, a - 572, 1), 50)
def f_h(p):                                                                # hangar recess
    a, y, z = p[:, 0], p[:, 1], p[:, 2]; f = smax((z - (78 - .85 * (a - 225))) / 1.31, -46 - .5 * np.maximum(a - 330, 0) - z, 40); return smax(f, -215 - y, 45)
def f_ai1(p): return smin(smin(smax(f_ai0(p), -f_h(p), 8), f_body(p), 60 - 40 * step(p[:, 2], 20, 110)), f_bj(p), 45)
def f_ai(p): return smax(f_ai1(p), -f_h(p), 8)
# --- AS
tz = lambda d: curve(d, 14)
asa = tz({110: 144, 150: 142, 175: 139, 200: 131, 225: 123, 250: 125, 275: 143, 300: 166, 320: 172}); asy = tz({110: -370, 170: -392, 200: -404, 225: -420, 250: -440, 275: -458, 300: -474, 320: -480}); hx = tz({110: 60, 170: 47, 200: 34, 225: 25, 250: 22, 275: 21, 320: 22}); hy = tz({110: 185, 170: 152, 200: 130, 225: 108, 250: 95, 275: 92, 320: 98}); sh = tz({110: 0, 215: 0, 290: .166, 320: .166})
def f_as0(p):
    a, y, z = p[:, 0], p[:, 1], p[:, 2]; u = np.maximum(np.abs(a - asa(z) - sh(z) * -(y - asy(z))) / hx(z), 1e-6); v = np.maximum(np.abs(y - asy(z)) / hy(z), 1e-6); m = 2.3; q = (u ** m + v ** m) ** (1 / m); g = np.hypot((u / q) ** (m - 1) / hx(z), (v / q) ** (m - 1) / hy(z)); return smax((q - 1) / g, smax(120 - z, z - 303, 2), 4)
f_as = lambda p: smin(smin(f_as0(p), f_body(p), 60), f_bs(p), 34)
# --- PI + ARCU: a plate of constant rounding over a plan outline, along a mid height; PI outline from grannyte
zm = curve({200: -322, 120: -326, 60: -323, 0: -319, -60: -310, -120: -298, -180: -287, -240: -280, -300: -272, -360: -259, -420: -239, -480: -214, -540: -186, -600: -152, -660: -119, -720: -96, -780: -84, -840: -78, -900: -70, -950: -62, -1000: -56}, 45); TH = curve({200: 60, 60: 70, 0: 70, -60: 68, -120: 63, -240: 56, -400: 52, -1000: 52}, 45)
cen = np.array([[0, -60], [52, -90], [97, -130], [116, -180], [128, -240], [141, -300], [155, -360], [170, -420], [189, -480], [212, -540], [243, -600], [282, -660], [323, -720], [370, -780], [420, -840], [468, -895], [498, -925]], float); cq = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cen, axis=0), axis=1))]; ca = CubicSpline(cq, cen)(np.arange(0, cq[-1], 2)); ca = gaussian_filter1d(ca, 12, axis=0, mode="nearest"); hwid = np.interp(ca[:, 1], [-600, -300, -180, -110], [33, 34, 42, 56]); ta = cKDTree(ca)
pw = curve({-200: 160, -120: 151, -60: 136, 0: 119, 60: 99, 120: 73, 150: 55, 170: 38, 182: 22, 188: 4}, 8); pin = curve({-60: -40, -90: 10, -120: 40, -180: 72, -240: 94}, 25)
def d2(a, y):                                                              # plan distance, negative inside: arm bands joined to the PI ogive
    dd, i = ta.query(np.stack([a, y], 1), workers=4); arm = dd - hwid[i]
    # ogive: ellipse-nosed half plane pair
    Ly = 250.0; yn = 188.0; tt = np.clip((yn - y) / Ly, 1e-4, None); half = 152 * np.sqrt(np.clip(1 - np.clip(1 - tt, 0, 1) ** 2, 1e-6, 1)) ** 1.15
    og = (a - half) * np.where(y > yn, 1, .86); og = smax(og, y - yn, 30); og = smax(og, -50 - .62 * np.sqrt(a * a + 4000) - y, 50); return smin(arm, og, 70)
def f_pi0(p):
    a, y, z = np.abs(p[:, 0]), p[:, 1], p[:, 2]; R = 25.0; s1 = (zm(y + 2) - zm(y - 2)) / 4; qx = d2(a, y) + R; qz = np.abs(z - zm(y)) / np.sqrt(1 + s1 * s1) - TH(y) / 2 + R; return np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - R
f_pi = lambda p: smin(f_pi0(p), f_bj(p), 30)
# --- meshing
def mesh(f, lo, hi, cell=CELL, sym=False):
    ax = [np.arange(l, h + cell, cell) for l, h in zip(lo, hi)]; X = np.stack(np.meshgrid(*ax, indexing="ij"), -1); shp = X.shape[:3]; X = X.reshape(-1, 3); F = np.concatenate([f(X[k:k + 400000]) for k in range(0, len(X), 400000)]).reshape(shp)
    v, t, _, _ = marching_cubes(F, 0.0, spacing=(cell,) * 3); v = v + lo; zero = (v[:, 0] < 1e-6) if sym else np.zeros(len(v), bool); e = .5
    for _ in range(6):
        g = np.stack([(f(v + dv) - f(v - dv)) / (2 * e) for dv in np.eye(3) * e], 1); g[zero, 0] = 0; m = (g * g).sum(1); st = (f(v) / np.maximum(m, .05))[:, None] * g; ln = np.linalg.norm(st, axis=1); v = v - st * np.minimum(1, cell / np.maximum(ln, 1e-9))[:, None]; v[zero, 0] = 0
    print("   rest pe suprafata max", np.abs(f(v)).max().round(3), "p99", np.percentile(np.abs(f(v)), 99).round(4)); return v, t
def clip(v, t, g):                                                         # keeps g > 0, triangles cut exactly where g = 0
    T = v[t]; s = g(v)[t]; keepT = [T[(s > 0).all(1)]]; k = (s > 0).any(1) & ~(s > 0).all(1); B, q = T[k], s[k]
    for i in range(3):
        a, b, c = B[:, i], B[:, (i + 1) % 3], B[:, (i + 2) % 3]; sa, sb, sc = q[:, i], q[:, (i + 1) % 3], q[:, (i + 2) % 3]; L = lambda p, r, x, w: p + (r - p) * (x / np.where(x == w, 1, x - w))[:, None]
        one = (sa > 0) & (sb <= 0) & (sc <= 0); keepT.append(np.stack([a, L(a, b, sa, sb), L(a, c, sa, sc)], 1)[one]); two = (sa <= 0) & (sb > 0) & (sc > 0); ab, acx = L(a, b, sa, sb), L(a, c, sa, sc); keepT += [np.stack([ab, b, c], 1)[two], np.stack([ab, c, acx], 1)[two]]
    T = np.concatenate(keepT); vv, inv = np.unique(T.reshape(-1, 3).round(4), axis=0, return_inverse=True); f = inv.reshape(-1, 3); return vv, f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
def fast(f, lo, hi, cell, sym):                                             # coarse pass first, the fine grid only near the surface
    c = cell * 4; ax = [np.arange(l, h + c, c) for l, h in zip(lo, hi)]; X = np.stack(np.meshgrid(*ax, indexing="ij"), -1); F = np.concatenate([f(q) for q in np.array_split(X.reshape(-1, 3), 8)]).reshape(X.shape[:3])
    from scipy.ndimage import map_coordinates
    af = [np.arange(l, x[-1] + cell / 2, cell) for l, x in zip(lo, ax)]; shp = [len(q) for q in af]; I = np.stack(np.meshgrid(*[np.arange(m) / 4 for m in shp], indexing="ij"), 0).reshape(3, -1); g = map_coordinates(F, I, order=1, mode="nearest"); k = np.abs(g) < c * 2.2
    Y = np.stack([af[j][(I[j][k] * 4 + .5).astype(int)] for j in range(3)], 1); g[k] = np.concatenate([f(q) for q in np.array_split(Y, 12)]); g = g.reshape(shp)
    v, t, _, _ = marching_cubes(g, 0.0, spacing=(cell,) * 3); v = v + lo; zero = (v[:, 0] < 1e-6) if sym else np.zeros(len(v), bool); e = .5
    for _ in range(6):
        gr = np.stack([(f(v + dv) - f(v - dv)) / (2 * e) for dv in np.eye(3) * e], 1); gr[zero, 0] = 0; m = (gr * gr).sum(1); st = (f(v) / np.maximum(m, .05))[:, None] * gr; ln = np.linalg.norm(st, axis=1); v = v - st * np.minimum(1, cell / np.maximum(ln, 1e-9))[:, None]; v[zero, 0] = 0
    r = np.abs(f(v)); print("   pe suprafata max", r.max().round(3), "p99,9", np.percentile(r, 99.9).round(4), "varfuri", len(v)); return v, t
def join(*m):
    V, F, n = [], [], 0
    for v, t in m: V.append(v); F.append(t + n); n += len(v)
    return np.vstack(V), np.vstack(F)
def plane(pp, tt): return lambda p: (p - pp) @ tt
soft = lambda x, r: r * np.logaddexp(0, x / r)                              # confirmed borders (zone_curate.py)
u_ = lambda p: .77 * p[:, 0] - .64 * p[:, 2]
b_bj = lambda p: np.minimum(u_(p) - (500 + 15 * np.clip((p[:, 1] + 225) / 225, -1, 1) - np.maximum(p[:, 1] - 130, 0) - soft(-470 - p[:, 1], 8) * 1.5), p[:, 0] - 300)
b_ai = lambda p: p[:, 0] - (190 + 35 * (p[:, 2] + 70) / 220) - np.minimum(soft((p[:, 1] + 160) * 2.6, 22) + soft((-430 - p[:, 1]), 22), 235)
b_et = lambda p: p[:, 2] - (50 - .065 * soft(p[:, 1] - 70, 25))
R3 = len(pre); ra, rb = np.argmin(np.abs(path[:, 1] + 700)), np.argmin(np.abs(path[:, 1] - 420)); pa, pb = np.argmin(np.abs(path[:, 1] + 1060)), np.argmin(np.abs(path[:, 1] + 800))
ba, bbk = np.argmin(np.abs(C[:i0, 1] + 210)), np.argmin(np.abs(C[:i0, 1] + 760)); tC = np.gradient(C, axis=0); tC /= np.linalg.norm(tC, axis=1)[:, None]
row = lambda i: R3 + (i - k1)                                               # path index -> BJ row
def f_all(p): return smin(smin(f_ai1(p), f_as0(p), 48), f_bs(p), 26)
print("corp + etaj + AI + AS + racordari"); v, t = fast(f_all, np.array([0, -832, -384.]), np.array([732, 1184, 352.]), CELL, True)
v, t = v, t; pB = lambda p: np.minimum(plane(C[ba], tC[ba])(p), plane(C[bbk], -tC[bbk])(p)); pJ = lambda p: np.minimum(plane(path[ra], tan[ra])(p), plane(path[rb], -tan[rb])(p))
isBS = lambda p: np.minimum(f_as0(p), f_body(p)) - f_bs(p)
def part(m, g): return clip(*m, g), clip(*m, lambda p: -g(p))
H, rest = part((v, t), lambda p: np.minimum(np.minimum(-f_h(p) - f_ai0(p), f_body(p) - 2), p[:, 1] + 260)); bsm, rest = part(rest, isBS); bsm = clip(*bsm, pB); bjm, rest = part(rest, b_bj); bjm = clip(*bjm, pJ)
asm, rest = part(rest, lambda p: np.minimum(np.minimum(f_body(p), f_ai0(p)) - f_as0(p), p[:, 2] - 125)); aim, rest = part(rest, b_ai); etm, com = part(rest, lambda p: (lambda w: (f_corp(p) - f_etaj(p)) * w + (p[:, 2] - 34) * (1 - w))(step(p[:, 1], -330, -200)))
OUT.update({"H": H, "AS": asm, "AI": aim, "CORP etaj": etm, "CORP": com})
print("PI + ARCU"); v, t = fast(f_pi, np.array([0, -1104, -380.]), np.array([640, 220, 60.]), CELL, True); bj2, pim = part((v, t), lambda p: f_pi0(p) - f_bj(p)); bj2 = clip(*bj2, lambda p: np.minimum(plane(path[pa], tan[pa])(p), plane(path[pb], -tan[pb])(p))); OUT["PI (ARCU)"] = pim
OUT["BS"] = join(tube(BS[:ba + 1], True, False), bsm, tube(BS[bbk:], False, False)); OUT["BJ"] = join(tube(BJ[:row(pa) + 1], False, False), bj2, tube(BJ[row(pb):row(ra) + 1], False, False), bjm, tube(BJ[row(rb):], False, True))
print("BS: abatere suprafata racordata fata de randurile confirmate (y -230..-300, -700..-750)", [np.abs(f_bs(G[i])).max().round(3) for i in (ba + 5, ba + 40, bbk - 40, bbk - 5)])
S2 = {}
for k, (v, f) in OUT.items():
    c = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1); f = f[c > 1e-6]; v = v * [-1, 1, 1]; S2["v__" + k], S2["f__" + k] = v.astype(np.float32), f; print(k, len(v), len(f), v.min(0).round(), v.max(0).round())
np.savez(f"{D}/neteda.npz", **S2)
