# The missing components as smooth, decoration-free surfaces in the confirmed ship's frame (S half, mirrored): the arm BS + BJ is one
# sweep that starts as the confirmed arm row by row (tube) and turns into a flat bar; CORP and the deck (etaj) are sections of rounded
# half-planes whose sizes run smoothly along y; AI, AS, PI + ARCU are smooth solids that carry the tangent blend to their neighbours, so
# the neighbours stay untouched. Implicit pieces are meshed at CELL m and every vertex put exactly on the surface.
# Second variant (on v289): the hangar ceiling (brow) belongs to AI, deep hangars tapering to the hull, softer joints, BJ blended into BF.
# Third variant (on v290): AS flares into BS from below, lips and roots tangent, the roof follows the deck, normals from the surfaces themselves.
# Fourth variant (on v291): BF and BJ run into one blunt rounded tip with a common blend; the deck never wider than the hull (the rest is AI).
# Fifth: the forms of v293 as closed solids (inner walls on the borders, 1 m under the skin, stitched), parts joined ring to ring.
# Sixth (on V1): the arm tip as neck, bulb and cone (between the confirmed arm and the reference R004 022_S), everything else as V1.
# Usage: python nava_neteda6.py <dir with npz>  -> neteda5.npz (v__<piece>, f__<piece>)
import sys, numpy as np
from scipy.interpolate import PchipInterpolator, CubicSpline
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes
D = sys.argv[1]; CELL = 3.0; OUT = {}
def curve(d, sig=35):                                                       # smooth function through a table (monotone, then softened)
    x = np.array(sorted(d)); f = PchipInterpolator(x, [d[k] for k in x]); s = np.arange(x[0] - 200, x[-1] + 201, 2.0); v = f(np.clip(s, x[0], x[-1])); v = gaussian_filter1d(v, sig / 2, mode="nearest")
    h = CubicSpline(s[::3], v[::3]); return lambda t: h(np.clip(t, s[0], s[-1] - 6))                     # cubic, so the normals have no steps
def smax(p, q, k): h = np.maximum(k - np.abs(p - q), 0) / k; return np.maximum(p, q) + h * h * k / 4
def smin(p, q, k): return -smax(-p, -q, k)
# --- arm: BS (confirmed rows) -> BJ
d = np.load(f"{D}/ASAMBLAT_NOU.npz"); n = list(d["n"]); V = d["v"][np.unique(d["t"][d["o"] == n.index("an_brat_spate_S")])]
G = V[:1288 * 96].reshape(1288, 96, 3) * [-1, 1, 1]; C = G.mean(1); i0 = np.where((C[:, 1] < -1200) & (C[:, 2] < 168))[0][0]; i1 = np.where((np.arange(1288) > i0) & (C[:, 1] > -1080))[0][0]; i2 = np.where((np.arange(1288) > i0) & (C[:, 1] > -640))[0][0]
ctrl = np.array([[577, -450, -221], [591, -300, -241], [599, -150, -258], [602, 0, -270], [598, 150, -279], [590, 300, -283], [579, 450, -281], [566, 600, -276], [550, 750, -270], [527, 900, -264], [502, 1050, -259], [479, 1200, -255], [467, 1270, -257], [455, 1330, -263]], float)
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
Wt = curve({-1100: 2 * A0[k1], -800: 80, -640: 98, -550: 120, -450: 148, -300: 172, -150: 186, 0: 190, 150: 168, 300: 140, 450: 120, 600: 108, 750: 99, 900: 94, 1050: 90, 1200: 84, 1270: 76, 1332: 46}, 60); Tt = curve({-1100: 2 * B0[k1], -640: 60, -450: 78, -300: 92, -150: 100, 0: 106, 150: 100, 300: 92, 450: 82, 600: 75, 750: 70, 900: 67, 1050: 64, 1200: 60, 1270: 54, 1332: 34}, 60)
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
    def __call__(s, p):                                                     # frame and sizes interpolated along the path (no jumps from sample to sample)
        i = s.t.query(p, workers=4)[1]; m = len(s.p); d0 = s.p[np.minimum(i + 1, m - 1)] - s.p[np.maximum(i - 1, 0)]; x = i + ((p - s.p[i]) * d0).sum(1) / (d0 * d0).sum(1) * (np.minimum(i + 1, m - 1) - np.maximum(i - 1, 0))
        x = np.clip(x, 0, m - 1.000001); j = x.astype(int); w = (x - j); lp = lambda X: X[j] + (X[j + 1] - X[j]) * (w if X.ndim == 1 else w[:, None])
        r = p - lp(s.p); A, B, nn = lp(s.A), lp(s.B), lp(s.N); u = np.abs((r * lp(s.U)).sum(1)) / A; v = np.abs((r * lp(s.W)).sum(1)) / B
        u, v = np.maximum(u, 1e-6), np.maximum(v, 1e-6); q = (u ** nn + v ** nn) ** (1 / nn); g = np.hypot((u / q) ** (nn - 1) / A, (v / q) ** (nn - 1) / B); e0 = -((p - s.p[0]) * s.T0).sum(1); e1 = ((p - s.p[-1]) * s.T1).sum(1); return np.maximum((q - 1) / g, np.maximum(e0, e1))
fine = lambda X: np.stack([np.interp(np.arange(0, len(X) - 1, .25), np.arange(len(X)), X[:, k]) for k in range(X.shape[1])], 1) if X.ndim > 1 else np.interp(np.arange(0, len(X) - 1, .25), np.arange(len(X)), X)
f_bj = Sweep(*map(fine, (path, U, W, A, B, N)))
jb = np.arange(0, i0, 2); cb = C[jb]; tb = np.gradient(cb, axis=0); tb /= np.linalg.norm(tb, axis=1)[:, None]; ax = [axes(G[j]) for j in jb]; Ub = np.array([q[0] for q in ax]); Ub *= np.sign((Ub * Ub[0]).sum(1))[:, None]; f_bs = Sweep(cb, Ub, np.cross(tb, Ub), np.array([q[1] for q in ax]), np.array([q[2] for q in ax]), np.full(len(jb), 2.0))
# --- CORP
zt = curve({-780: 50, 60: 48, 120: 38, 180: 34, 300: 27, 420: 20, 540: 12, 660: 5, 780: -3, 900: -16, 1020: -33, 1107: -55}, 30); zb = curve({-800: 46, -720: 6, -660: -14, -600: -37, -540: -60, -480: -79, -420: -95, -360: -112, -300: -128, -240: -144, -180: -156, -120: -166, -60: -175, 0: -184, 60: -193, 120: -201, 180: -207, 240: -211, 360: -217, 480: -220, 660: -220, 780: -209, 900: -196, 1020: -172, 1107: -130}, 40)
wh = curve({-790: 128, -720: 148, -660: 172, -600: 203, -540: 235, -480: 252, -420: 240, -300: 226, -180: 226, -60: 244, 0: 256, 60: 254, 120: 243, 180: 223, 240: 205, 300: 192, 360: 186, 480: 172, 600: 157, 720: 139, 840: 119, 960: 98, 1040: 74, 1107: 40}, 35); wl = curve({-790: 84, -720: 104, -660: 118, -600: 122, -540: 126, -480: 130, -300: 142, -180: 150, 0: 152, 180: 147, 360: 133, 600: 115, 780: 103, 900: 92, 1020: 66, 1107: 25}, 35)
def f_corp(p):
    a, y, z = np.abs(p[:, 0]), p[:, 1], p[:, 2]; t, bt, h, l = zt(y), zb(y), wh(y), wl(y); H = np.maximum(t - bt, 20); nx, nz = H, -(h - l); L = np.hypot(nx, nz); side = ((a - l) * nx + (z - bt) * nz) / L
    f = smax(side, bt + .07 * (np.sqrt(a * a + 4900) - 70) - z, 60); f = smax(f, z - t, np.interp(y, [150, 450], [22, 55])); f = smax(f, y - 1152, 130); return smax(f, -786 - y, 60)
# --- etaj
et = curve({-780: 138, -720: 150, -600: 161, -480: 168, -360: 166, -240: 160, -120: 148, 0: 138, 60: 135, 120: 128, 180: 113, 240: 95, 300: 75, 360: 53, 420: 30, 470: 8, 520: -20}, 30); we = curve({-780: 82, -720: 106, -660: 133, -600: 158, -540: 179, -480: 190, -420: 200, -240: 200, -120: 196, 0: 190, 60: 182, 120: 170, 180: 154, 240: 137, 300: 122, 360: 105, 480: 88}, 35)
wr = curve({-780: 97, -720: 122, -660: 146, -600: 174, -540: 197, -480: 209, -420: 214, -300: 214, -180: 222, -60: 226, 0: 234, 60: 236, 120: 224, 180: 206, 240: 190, 300: 178, 360: 160, 420: 143, 520: 120}, 35); wc = curve({60: 14, 100: 22, 180: 45, 240: 63, 300: 70, 420: 80, 520: 90}, 25)
eb = curve({-800: 28, -400: 28, -200: 38, -60: 38, 0: 34, 60: 30, 120: 22, 180: 18, 300: 12, 420: 5, 520: -5}, 30)
ek = curve({-800: 0, -380: 0, -220: .06, 40: .06, 160: .25, 520: .25}, 40)
def f_etaj(p):
    a, y, z = np.abs(p[:, 0]), p[:, 1], p[:, 2]; t, e, r = et(y), we(y), wr(y); zr = np.minimum(62, t - 8); nx, nz = t - zr, r - e; L = np.hypot(nx, nz); slope = ((a - e) * nx + (z - t) * nz) / L
    f = smax(z - t - .02 * (0 - a * 0), slope, 30); f = smax(f, a - r, 40); f = smax(f, eb(y) - z - ek(y) * np.maximum(0, r - np.sqrt(a * a + 900)), 20); f = smax(f, -782 - y - (z - 60) * .10, 50)
    ch = smax(a - wc(y), 92 - y, 34); return smax(f, -ch, 18)
f_body = lambda p: smin(f_corp(p), f_etaj(p), 18 + 14 * step(-p[:, 1], -110, 40))
# --- AI
at = curve({160: 174, 200: 158, 250: 135, 310: 97, 370: 48, 430: -5, 490: -66, 540: -128, 580: -174, 640: -228}, 40); ab = curve({160: -74, 250: -74, 310: -74, 370: -86, 430: -122, 490: -180, 540: -222, 580: -246, 640: -280}, 30)
le = curve({160: 10, 200: -78, 225: -122, 255: -141, 310: -130, 370: -99, 430: -70, 470: -36, 500: 4, 530: 48, 560: 88, 640: 170}, 22); te = curve({160: -512, 205: -496, 235: -484, 265: -473, 310: -463, 370: -449, 430: -441, 480: -447, 520: -458, 560: -476, 640: -508}, 26)
slp = lambda f, a: 1 / np.sqrt(1 + ((f(a + 1) - f(a - 1)) / 2) ** 2)
drop = lambda y: soft_(163 - et(y), 4)
soft_ = lambda x, r: r * np.logaddexp(0, x / r)
lt = curve({160: 190, 225: 150, 250: 104, 290: 36, 330: -22, 360: -60, 395: -83, 430: -76, 470: -38, 500: 4, 530: 48, 560: 88, 640: 170}, 26)
ab2 = lambda a, y: ab(a) + soft_((-230 - y) * .3, 12) * step(-a, -480, -320)                                 # the underside rises aft at the root, as in the references
def f_ai0(p):                                                              # the leading edge leans forward from the lower lip (le) to the roof (lt, flush with the brow)
    a, y, z = p[:, 0], p[:, 1], p[:, 2]; b, t = ab2(a, y), at(a) - drop(y); fr = le(a) + (lt(a) - le(a)) * step((z - b) / (t - b), .15, .85)
    f = smax((z - t) * slp(at, a), (y - fr) * slp(lt, a), 36); g = smax((b - z) * slp(ab, a), (te(a) - y) * slp(te, a), 80); return smax(smax(f, g, 24), smax(168 - a, a - 572, 1), 50)
def f_h(p):                                                                # hangar: under the wing skin, above the lower lip, narrowing to the hull aft
    a, y, z = p[:, 0], p[:, 1], p[:, 2]; f = smax((z - (at(a) - drop(y) - 34)) * slp(at, a), (ab2(a, y) + 16 - z) * slp(ab, a), 34); f = smax(f, (a - hout(y)) * .9, 46); f = smax(f, (262 - a - (55 - z) * 2.2) / 2.42, 40); return smax(f, -372 - y, 70)
hout = curve({-480: 235, -380: 250, -300: 300, -230: 355, -160: 408, -100: 438, 0: 450}, 40)
f_aic = lambda p: smax(f_ai0(p), -f_h(p), 24)
def f_ai1(p): return smin(smin(f_aic(p), f_body(p), (84 - (62 - 40 * step(-p[:, 1], 380, 480) - 14 * step(p[:, 1], -165, -95)) * step(p[:, 2], 20, 110)) * (.4 + .6 * step(f_h(p), -4, 14))), f_bj(p), 80)
def f_ai(p): return smax(f_ai1(p), -f_h(p), 8)
# --- AS
tz = lambda d: curve(d, 14)
asa = tz({110: 144, 150: 142, 175: 139, 200: 131, 225: 123, 250: 125, 275: 143, 295: 162, 320: 170}); asy = tz({110: -370, 170: -392, 200: -404, 225: -420, 250: -440, 275: -458, 300: -474, 320: -480}); hx = tz({110: 60, 170: 47, 200: 34, 225: 25, 245: 22, 270: 23, 290: 28, 320: 28}); hy = tz({110: 185, 170: 152, 200: 130, 225: 108, 248: 98, 268: 108, 288: 146, 320: 150}); sh = tz({110: 0, 215: 0, 290: .166, 320: .166})
def f_as0(p):
    a, y, z = p[:, 0], p[:, 1], p[:, 2]; u = np.maximum(np.abs(a - asa(z) - sh(z) * -(y - asy(z))) / hx(z), 1e-6); v = np.maximum(np.abs(y - asy(z)) / hy(z), 1e-6); m = 2.3; q = (u ** m + v ** m) ** (1 / m); g = np.hypot((u / q) ** (m - 1) / hx(z), (v / q) ** (m - 1) / hy(z)); return smax((q - 1) / g, smax(120 - z, z - 289, 2), 14)
f_as = lambda p: smin(smin(f_as0(p), f_body(p), 60), f_bs(p), 34)
# --- PI + ARCU: a plate of constant rounding over a plan outline, along a mid height; PI outline from grannyte
zm = curve({200: -322, 120: -326, 60: -323, 0: -319, -60: -310, -120: -298, -180: -287, -240: -280, -300: -272, -360: -259, -420: -239, -480: -214, -540: -186, -600: -152, -660: -119, -720: -96, -780: -84, -840: -80, -880: -76, -925: -65, -975: -48, -1010: -36}, 45); TH = curve({200: 60, 60: 70, 0: 70, -60: 68, -120: 63, -240: 56, -400: 52, -850: 52, -905: 44, -950: 24, -1000: 24}, 24)
cen = np.array([[0, -60], [52, -90], [97, -130], [116, -180], [128, -240], [141, -300], [155, -360], [170, -420], [189, -480], [212, -540], [243, -600], [282, -660], [323, -720], [370, -780], [414, -826], [452, -872], [478, -914], [492, -944]], float); cq = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cen, axis=0), axis=1))]; ca = CubicSpline(cq, cen)(np.arange(0, cq[-1], 2)); ca = gaussian_filter1d(ca, 12, axis=0, mode="nearest"); hwid = np.interp(ca[:, 1], [-950, -900, -840, -600, -300, -180, -110], [12, 28, 35, 34, 34, 42, 56]); hwid = gaussian_filter1d(hwid, 14, mode="nearest"); ta = cKDTree(ca); tca = np.gradient(ca, axis=0); tca /= np.linalg.norm(tca, axis=1)[:, None]; hsl = np.gradient(hwid) / 2
pw = curve({-200: 160, -120: 151, -60: 136, 0: 119, 60: 99, 120: 73, 150: 55, 170: 38, 182: 22, 188: 4}, 8); pin = curve({-60: -40, -90: 10, -120: 40, -180: 72, -240: 94}, 25)
def d2(a, y):                                                              # plan distance, negative inside: arm bands joined to the PI ogive
    def arm(q):
        P2 = np.stack([q, y], 1); dd, i = ta.query(P2, workers=4); t2 = tca[i]; w2 = P2 - ca[i]; al = np.clip((w2 * t2).sum(1), -1.2, 1.2); al = np.where((i == 0) | (i == len(ca) - 1), np.minimum(np.maximum(al, np.where(i == 0, 0, -1.2)), np.where(i == 0, 1.2, 0)), al); return np.linalg.norm(w2 - t2 * al[:, None], axis=1) - (hwid[i] + al * hsl[i])
    u, w = np.maximum(a / 152, 1e-6), np.maximum(np.abs(y + 62) / 250, 1e-6); m = 1.9; q = (u ** m + w ** m) ** (1 / m); og = (q - 1) / np.hypot((u / q) ** (m - 1) / 152, (w / q) ** (m - 1) / 250)
    og = smax(og, -50 - .62 * np.sqrt(a * a + 4000) - y, 50); return smin(smin(arm(a), arm(-a), 60), og, 70)
def f_pi0(p):
    a, y, z = np.abs(p[:, 0]), p[:, 1], p[:, 2]; R = 25.0; s1 = (zm(y + 2) - zm(y - 2)) / 4; qx = d2(a, y) + R; qz = np.abs(z - zm(y)) / np.sqrt(1 + s1 * s1) - TH(y) / 2 + R; return np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qx, qz), 0) - R
f_pi = lambda p: smin(f_pi0(p), f_bj(p), 62)
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
    V, F, Q, n = [], [], [], 0
    for x in m: v, t = x[:2]; V.append(v); F.append(t + n); Q.append(x[2] if len(x) > 2 else areal(v, t)); n += len(v)
    return np.vstack(V), np.vstack(F), np.vstack(Q)
def areal(v, t):                                                            # vertex normals of a swept grid
    c = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]); q = np.zeros_like(v)
    for i in range(3): np.add.at(q, t[:, i], c)
    return q / np.maximum(np.linalg.norm(q, axis=1), 1e-9)[:, None]
def grad(f, m, sym=False):                                                  # the surface's own normals, faces turned outwards
    v, t = m[:2]; q = np.stack([f(v + dv) - f(v - dv) for dv in np.eye(3) * .4], 1)
    if sym: q[v[:, 0] < 1e-3, 0] = 0
    q /= np.maximum(np.linalg.norm(q, axis=1), 1e-9)[:, None]; c = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]); bad = (c * q[t].sum(1)).sum(1) < 0; t = t.copy(); t[bad] = t[bad][:, ::-1]; return v, t, q
def swp(R, capa, capb):                                                     # a swept part with outward normals
    v, t = tube(R, capa, capb); c = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]); m = t.max() // 96; ctr = R.mean(1)[np.minimum(t[:, 0] // R.shape[1], len(R) - 1)]; t = t if ((v[t].mean(1) - ctr) * c).sum() > 0 else t[:, ::-1]; return v, t, areal(v, t)
def plane(pp, tt): return lambda p: (p - pp) @ tt
soft = lambda x, r: r * np.logaddexp(0, x / r)                              # confirmed borders (zone_curate.py)
u_ = lambda p: .77 * p[:, 0] - .64 * p[:, 2]
b_bj = lambda p: np.minimum(u_(p) - (500 + 15 * np.clip((p[:, 1] + 225) / 225, -1, 1) - np.maximum(p[:, 1] - 130, 0) - soft(-470 - p[:, 1], 8) * 1.5), p[:, 0] - 300)
b_ai = lambda p: p[:, 0] - (185 - 3 * (p[:, 2] + 70) / 220) - np.minimum(soft((p[:, 1] + 160) * 2.6, 22) + soft((-512 - p[:, 1]) * 1.4, 18), 235)
b_et = lambda p: p[:, 2] - (50 - .065 * soft(p[:, 1] - 70, 25))
R3 = len(pre); ra, rb = np.argmin(np.abs(path[:, 1] + 655)), np.argmin(np.abs(path[:, 1] - 420)); pa, pb = k1 + 3, np.argmin(np.abs(path[:, 1] + 690))
ba, bbk = np.argmin(np.abs(C[:i0, 1] + 210)), np.argmin(np.abs(C[:i0, 1] + 760)); tC = np.gradient(C, axis=0); tC /= np.linalg.norm(tC, axis=1)[:, None]
row = lambda i: R3 + (i - k1)                                               # path index -> BJ row
def f_all(p): return smin(smin(f_ai1(p), f_as0(p), 62), f_bs(p), 50)
print("corp + etaj + AI + AS + racordari"); v, t = fast(f_all, np.array([0, -832, -384.]), np.array([732, 1184, 352.]), CELL, True)
v, t = v, t; pB = lambda p: np.minimum(plane(C[ba], tC[ba])(p), plane(C[bbk], -tC[bbk])(p)); pJ = lambda p: np.minimum(plane(path[ra], tan[ra])(p), plane(path[rb], -tan[rb])(p))
isBS = lambda p: np.minimum(f_as0(p), f_body(p)) - f_bs(p)
def part(m, g): return clip(*m, g), clip(*m, lambda p: -g(p))
H, rest = part((v, t), lambda p: np.minimum(np.minimum(np.minimum(-f_h(p) - f_ai0(p), f_body(p) - f_aic(p)), p[:, 1] + 480), (at(p[:, 0]) - drop(p[:, 1]) - 52 - p[:, 2]))); bsm, rest = part(rest, isBS); bsm = clip(*bsm, lambda p: pB(p) - 1.5); bjm, rest = part(rest, b_bj); bjm = clip(*bjm, lambda p: pJ(p) - 1.5)
asm, rest = part(rest, lambda p: np.minimum(np.minimum(np.minimum(f_body(p), f_ai0(p)) - f_as0(p), p[:, 2] - 125), 199 - p[:, 0])); b_st = lambda p: p[:, 0] - (185 - 3 * (p[:, 2] + 70) / 220) - soft((p[:, 1] - 10) * .16, 12)   # deck | hangar roof: one plane, bent outwards ahead
def b_aib(p): w, q = step(p[:, 1], -300, -150), step(p[:, 2], 0, 40); return (1 - w) * b_ai(p) + w * (q * b_st(p) + (1 - q) * (f_body(p) - f_aic(p)))   # aft the confirmed plane, ahead and low the middle of the fillet
aim, rest = part(rest, b_aib); etm, com = part(rest, lambda p: (lambda w: (f_corp(p) - f_etaj(p)) * w + (p[:, 2] - 34) * (1 - w))(step(p[:, 1], -330, -200)))
OUT.update({k: grad(f_all, q, True) for k, q in (("H", H), ("AS", asm), ("AI", aim), ("CORP etaj", etm), ("CORP", com))}); bsm, bjm = grad(f_all, bsm), grad(f_all, bjm)
print("PI + ARCU"); v, t = fast(f_pi, np.array([0, -1104, -380.]), np.array([640, 220, 60.]), CELL, True); bj2, pim = part((v, t), lambda p: f_pi0(p) - f_bj(p)); pQ = lambda p: np.minimum(plane(path[pa], tan[pa])(p), plane(path[pb], -tan[pb])(p)); bj2 = clip(*bj2, lambda p: pQ(p) - 1.5); OUT["PI (ARCU)"] = grad(f_pi, pim, True); bj2 = grad(f_pi, bj2)
PARTS = {"BS": [swp(BS[:ba + 1], True, False), bsm, swp(BS[bbk:], False, False)]}
qv = d["v"][np.unique(d["t"][d["o"] == n.index("an_brat_fata_S")])] * [-1, 1, 1]; ys = np.arange(880, 1246, 15.0); pc = np.array([(qv[np.abs(qv[:, 1] - t_) < 5].max(0) + qv[np.abs(qv[:, 1] - t_) < 5].min(0)) / 2 for t_ in ys]); fit = [np.polyfit(ys, pc[:, k], 3) for k in range(3)]
for _ in range(3):                                                          # centres and half axes of the arm in planes across it, smooth cubics along y
    pc = np.stack([np.polyval(f_, ys) for f_ in fit], 1); tq = np.gradient(pc, axis=0); tq /= np.linalg.norm(tq, axis=1)[:, None]; ce, ha, hb, ua = [], [], [], []
    for c_, t_ in zip(pc, tq):
        k = (np.abs((qv - c_) @ t_) < 5) & (np.linalg.norm(qv - c_, axis=1) < 95); X = qv[k] - c_; X -= np.outer(X @ t_, t_); w_ = np.array([.82, .08, -.56]); w_ -= t_ * (w_ @ t_); w_ /= np.linalg.norm(w_); n_ = np.cross(t_, w_); xx, yy = X @ w_, X @ n_; ce.append(c_ + w_ * (xx.max() + xx.min()) / 2 + n_ * (yy.max() + yy.min()) / 2); ha.append(np.ptp(xx) / 2); hb.append(np.ptp(yy) / 2)
    fit = [np.polyfit(ys, np.array(ce)[:, k], 3) for k in range(3)]
fa, fb = np.polyfit(ys, ha, 2), np.polyfit(ys, hb, 2); print("BF semiaxe la y 1000 / 1200:", np.polyval(fa, 1000).round(1), np.polyval(fb, 1000).round(1), "/", np.polyval(fa, 1200).round(1), np.polyval(fb, 1200).round(1))
yb = np.arange(900, 1226, 15.0); Pf = np.vstack([np.stack([np.polyval(f_, yb) for f_ in fit], 1), [[474, 1276, -243], [464, 1300, -255], [454, 1340, -267], [443, 1384, -282], [428, 1440, -298]]]); sf = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pf, axis=0), axis=1))]; st = np.arange(0, sf[-1], 2.0); pf = gaussian_filter1d(CubicSpline(sf, Pf)(st), 9, axis=0, mode="nearest"); tf = np.gradient(pf, axis=0); tf /= np.linalg.norm(tf, axis=1)[:, None]; Uf = np.array([.82, .08, -.56]) - tf * (tf @ np.array([.82, .08, -.56]))[:, None]; Uf /= np.linalg.norm(Uf, axis=1)[:, None]
ky = [900, 1000, 1100, 1200, 1238, 1262, 1284, 1306, 1328, 1350, 1372, 1394, 1410, 1440]; ka = [np.polyval(fa, q) for q in (900, 1000, 1100, 1200)]; kb = [np.polyval(fb, q) for q in (900, 1000, 1100, 1200)]
g1 = PchipInterpolator(ky, ka + [42, 43.5, 49, 52.5, 49, 42, 33.5, 24, 17, 10]); g2 = PchipInterpolator(ky, kb + [26, 32, 43, 49.5, 47, 40.5, 32.5, 23.5, 17, 10])
Lc = 16.0; Af, Bf = gaussian_filter1d(g1(np.clip(pf[:, 1], 900, 1440)), 6, mode="nearest"), gaussian_filter1d(g2(np.clip(pf[:, 1], 900, 1440)), 6, mode="nearest"); s0 = (np.argmin(np.abs(pf[:, 1] - 1419)) * 2.0 - Lc); Wf = np.cross(tf, Uf); tp = cKDTree(pf); ix = np.arange(len(pf)); CP_, CU_, CW_, CA_, CB_ = [CubicSpline(ix, q) for q in (pf, Uf, Wf, Af, Bf)]
def f_sw(p):                                                                # the arm's ellipse closed by an ogive along its own path, one formula (no ring), cubic along the path
    i = tp.query(p, workers=4)[1]; x = np.clip(i + ((p - pf[i]) * tf[i]).sum(1) / 2.0, 0, len(pf) - 1.0)
    for _ in range(2): c_ = CP_(x); t_ = CP_(x, 1); x = np.clip(x + ((p - c_) * t_).sum(1) / (t_ * t_).sum(1), 0, len(pf) - 1.0)
    r_ = p - CP_(x); A_, B_ = CA_(x), CB_(x); u, v, h = np.abs((r_ * CU_(x)).sum(1)) / A_, np.abs((r_ * CW_(x)).sum(1)) / B_, np.maximum((x * 2.0 - s0) / Lc, 0); q = np.maximum(np.sqrt(u * u + v * v + h * h), 1e-6); g = np.sqrt((u / A_) ** 2 + (v / B_) ** 2 + (h / Lc) ** 2) / q + 1e-9; return (q - 1) / g
bt = d["t"][d["o"] == n.index("an_brat_fata_S")]; q = d["v"][bt] * [-1, 1, 1]; q = q[(q[:, :, 1].min(1) > 940)]; cb_ = q.mean(1); nb = np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]); ok = (np.linalg.norm(nb, axis=1) > 1e-6) & (f_sw(cb_) > -4); cb_, nb = cb_[ok], nb[ok] / np.linalg.norm(nb[ok], axis=1)[:, None]; core = pf[cKDTree(pf).query(cb_)[1]]; nb *= np.sign(((cb_ - core) * nb).sum(1))[:, None]; tb_ = cKDTree(cb_)
def f_mesh(p): dd, i = tb_.query(p, k=10, workers=4); w = 1 / (dd + 1.0) ** 2; w /= w.sum(1)[:, None]; return (((p[:, None] - cb_[i]) * nb[i]).sum(2) * w).sum(1)
iy = np.argmin(np.abs(pf[:, 1] - 1216)); CUT = (pf[iy], tf[iy])
def f_bf(p): w = step((p - CUT[0]) @ CUT[1], 0, 52); return f_mesh(p) * (1 - w) + f_sw(p) * w
ie = np.argmin(np.abs(path[:, 1] - 1296)); f_bje = lambda p: smax(f_bj(p), plane(path[ie], tan[ie])(p), 130)                 # BJ closes round inside the tip
f_tip = lambda p: smin(f_bje(p), f_bf(p), 36 - 4 * step(p[:, 1], 1120, 1260))
rc = np.argmin(np.abs(path[:, 1] - 1020)); v, t = fast(f_tip, np.array([372, 984, -372.]), np.array([612, 1440, -96.]), 2.0, False)
v, t = clip(v, t, lambda p: plane(path[rc], tan[rc])(p) - 1.5); bfm, bj3 = part((v, t), lambda p: f_bje(p) - f_bf(p)); beyond = plane(*CUT); skin = clip(*bfm, lambda p: plane(path[rc], tan[rc])(p) - 60)
OUT["BF varf"] = grad(f_tip, skin[:2]); bj3 = grad(f_tip, bj3); print("BF: abatere suprafata noua fata de brat la taietura", np.percentile(np.abs(f_sw(cb_[np.abs(cb_[:, 1] - 1205) < 8])), [50, 95, 100]).round(2))
PARTS["BJ"] = [swp(BJ[:row(pa) + 1], False, False), bj2, swp(BJ[row(pb):row(ra) + 1], False, False), bjm, swp(BJ[row(rb):row(rc) + 1], False, False), bj3]
print("BS: abatere suprafata racordata fata de randurile confirmate (y -230..-300, -700..-750)", [np.abs(f_bs(G[i])).max().round(3) for i in (ba + 5, ba + 40, bbk - 40, bbk - 5)])
# inner walls: the border surface of each piece, 1 m under the skin
L_h = lambda p: np.minimum(np.minimum(np.minimum(-f_h(p) - f_ai0(p), f_body(p) - f_aic(p)), p[:, 1] + 480), at(p[:, 0]) - drop(p[:, 1]) - 52 - p[:, 2])
L_as = lambda p: np.minimum(np.minimum(np.minimum(f_body(p), f_ai0(p)) - f_as0(p), p[:, 2] - 125), 199 - p[:, 0])
L_et = lambda p: (lambda w: (f_corp(p) - f_etaj(p)) * w + (p[:, 2] - 34) * (1 - w))(step(p[:, 1], -330, -200))
LAB = {"H": lambda p: L_h(p), "BS": lambda p: np.minimum(-L_h(p), isBS(p)), "BJ": lambda p: np.minimum(np.minimum(-L_h(p), -isBS(p)), b_bj(p))}
rest_ = lambda p: np.minimum(np.minimum(-L_h(p), -isBS(p)), -b_bj(p))
LAB["AS"] = lambda p: np.minimum(rest_(p), L_as(p)); LAB["AI"] = lambda p: np.minimum(np.minimum(rest_(p), -L_as(p)), b_aib(p))
LAB["CORP etaj"] = lambda p: np.minimum(np.minimum(np.minimum(rest_(p), -L_as(p)), -b_aib(p)), L_et(p)); LAB["CORP"] = lambda p: np.minimum(np.minimum(np.minimum(rest_(p), -L_as(p)), -b_aib(p)), -L_et(p))
def wall(L, f, m, sym, cell=3.0, dep=1.0):
    lo, hi = m[0].min(0) - 9, m[0].max(0) + 9; lo[0] = 0 if sym else lo[0]; ax = [np.arange(l, h + cell, cell) for l, h in zip(lo, hi)]; X = np.stack(np.meshgrid(*ax, indexing="ij"), -1); g = np.concatenate([L(q) for q in np.array_split(X.reshape(-1, 3), 24)]).reshape(X.shape[:3])
    if g.min() >= 0 or g.max() <= 0: return np.zeros((0, 3)), np.zeros((0, 3), int)
    v, t, _, _ = marching_cubes(g, 0.0, spacing=(cell,) * 3); v += lo; zero = (v[:, 0] < 1e-6) if sym else np.zeros(len(v), bool); e = .5
    for _ in range(5):
        gr = np.stack([(L(v + dv) - L(v - dv)) / (2 * e) for dv in np.eye(3) * e], 1); gr[zero, 0] = 0; q = (gr * gr).sum(1); st = (L(v) / np.maximum(q, .05))[:, None] * gr; ln = np.linalg.norm(st, axis=1); v = v - st * np.minimum(1, .7 * cell / np.maximum(ln, 1e-9))[:, None]; v[zero, 0] = 0
    return clip(v, t, lambda p: -f(p) - dep)
ALL = {k: ([OUT[k]], []) for k in ("H", "AS", "AI", "CORP etaj", "CORP", "PI (ARCU)", "BF varf")}; ALL["BS"] = (PARTS["BS"], []); ALL["BJ"] = (PARTS["BJ"], [])
for k in ("H", "AS", "AI", "CORP etaj", "CORP"): ALL[k][1].append(wall(LAB[k], f_all, OUT[k], True))
ALL["BS"][1].append(wall(LAB["BS"], f_all, bsm, False)); ALL["BJ"][1].append(wall(LAB["BJ"], f_all, bjm, False))
L_pi = lambda p: f_bj(p) - f_pi0(p); ALL["PI (ARCU)"][1].append(wall(L_pi, f_pi, OUT["PI (ARCU)"], True)); ALL["BJ"][1].append(wall(lambda p: -L_pi(p), f_pi, bj2, False))
L_tp = lambda p: f_bje(p) - f_bf(p); ALL["BF varf"][1].append(wall(lambda p: np.minimum(L_tp(p), plane(path[rc], tan[rc])(p) - 60), f_tip, OUT["BF varf"], False, 2.0)); ALL["BJ"][1].append(wall(lambda p: -L_tp(p), f_tip, bj3, False, 2.0))
S2 = {"cut_p": CUT[0], "cut_t": CUT[1], "names": np.array(list(ALL))}
for k, (sk, wl) in ALL.items():
    S2[f"{k}|ns"], S2[f"{k}|nw"] = len(sk), len(wl)
    for i, m in enumerate(sk): S2[f"{k}|s{i}v"], S2[f"{k}|s{i}t"], S2[f"{k}|s{i}n"] = m[0], m[1], m[2]
    for i, m in enumerate(wl): S2[f"{k}|w{i}v"], S2[f"{k}|w{i}t"] = m[0], m[1]
    print(k, "parti", [len(m[0]) for m in sk], "pereti", [len(m[0]) for m in wl])
np.savez(f"{D}/neteda5.npz", **S2)
