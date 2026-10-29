# Guides for the PS's rim (asked: draw the rim beside, with its outline / guides as before - it has to be a triangle with a
# rounded head). In plan: a triangle with a rounded head - two straight sides (fitted to the body's bottom outline between
# y FY0..FY1, symmetric), a nose arc tangent to both with its tip on the body's tip, a straight back at y YB, back corners
# rounded RC m, shrunk (offset in) until it lies under the body; the inner outline = the outer one RW m in (offset, smoothed). Section guides perpendicular to the outline
# every PAS m (right half, mirrored): top flat on the body (z ZP), bottom a quarter ellipse from the outer edge (z ZP) down
# to the inner edge (z ZP - H; H = the current rim's depth there, median) with a vertical inner wall - each in its own plane.
# FORMA=ogiva: straight sides where they fit under the body, the head = the body outline OG m in (pointed, long).
# Usage: python ghid_rama.py <fund_contururi.npz> <fund_harta.npz> <out.npz> ; env RW=17 YB=-25 RC=10 FY0=-10 FY1=300 PAS=40 RMIN=60
import sys, os, numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
C = np.load(sys.argv[1]); Hm = np.load(sys.argv[2]); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d))
RW, YB, RC, FY0, FY1, PAS = e("RW", "17"), e("YB", "-25"), e("RC", "10"), e("FY0", "-10"), e("FY1", "300"), e("PAS", "40")
RMIN = e("RMIN", "60"); ZP = float(C["z"][0])
K = C["contur_corp"]; Rt = K[(K[:, 0] > 0) & (K[:, 1] > FY0) & (K[:, 1] < FY1)]; b, a = np.polyfit(Rt[:, 1], Rt[:, 0], 1)    # x = a + b y
yt = K[:, 1].max()
# nose circle: centre (0, yc), radius r, tangent to the line x - b y - a = 0, tip at yc + r = yt
n = np.array([1.0, -b]) / np.hypot(1, b); r = (a + b * yt) / (1 + np.hypot(1, b) * 1 / np.hypot(1, b) * 0 + b / np.hypot(1, b) * 0 + 0) if False else None
# distance from (0, yc) to the line: |0 - b yc - a| / sqrt(1 + b^2) = r, with yc = yt - r (b < 0: the sides close towards the nose)
s_ = np.hypot(1, b); r = (a + b * yt) / (s_ + b)          # from (a + b (yt - r)) / s_ = r
yc = yt - r; tp = np.array([0.0, yc]) + r * n             # tangent point on the right side
def outline(off, a=a, b=b, yt=yt):                     # the rounded triangle offset `off` m inwards, clockwise from the tip
    s_ = np.hypot(1, b); n = np.array([1.0, -b]) / s_; r = (a + b * yt) / (s_ + b); yc = yt - r
    aa = a - off * s_; rr = r - off; ybb = YB + off
    tpp = np.array([0.0, yc]) + rr * n; xb = aa + b * ybb
    th0 = np.arctan2(tpp[1] - yc, tpp[0]); th = np.linspace(np.pi / 2, th0, 60)            # tip -> right tangent point
    right = np.c_[rr * np.cos(th), yc + rr * np.sin(th)]
    yy = np.linspace(tpp[1], ybb, 200); side = np.c_[aa + b * yy, yy]
    back = np.c_[np.linspace(xb, 0, 80), np.full(80, ybb)]
    half = np.vstack([right, side[1:], back[1:]])
    return np.vstack([half, (half[::-1] * [-1, 1])[1:-1]])
def smooth_corners(p, rc):
    if rc <= 0: return p
    cc = np.vstack([p, p[:1]]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cc, axis=0), axis=1))]; u = np.arange(0, d[-1], 0.5)
    q = np.c_[np.interp(u, d, cc[:, 0]), np.interp(u, d, cc[:, 1])]; sg = rc / 0.5 / 2
    return np.c_[gaussian_filter1d(q[:, 0], sg, mode="wrap"), gaussian_filter1d(q[:, 1], sg, mode="wrap")]
Mb = np.zeros((2400, 1600), np.uint8); px = lambda q: np.c_[(q[:, 0] + 200) / 0.25, (q[:, 1] + 80) / 0.25].astype(np.int32)
cv2.fillPoly(Mb, [px(K)], 1); Mb = cv2.erode(Mb, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(bool)   # body, 1 m in
def inside(q): j = px(q); return Mb[np.clip(j[:, 1], 0, 2399), np.clip(j[:, 0], 0, 1599)].all()
FORMA = os.environ.get("FORMA", "triunghi")
best = None                                            # the triangle touching the body from inside: for each side slope b the
Kr = K[(K[:, 0] > 0) & (K[:, 1] > YB) & (K[:, 1] < FY1 + 30)]   # (the nose is the arc's job) widest a that stays in, then the highest tip that stays in; the one
for bb in (np.arange(-0.35, 0.0, 0.005) if FORMA != "ogiva" else []):                # closest to the body's outline (mean distance) wins
    aa = (Kr[:, 0] - bb * Kr[:, 1]).min() - 1
    for tt in np.arange(yt - 1, yt - 80, -1.0):
        if (aa + bb * tt) / (np.hypot(1, bb) + bb) < RMIN: continue   # the head stays round
        q = smooth_corners(outline(0, aa, bb, tt), RC)
        if inside(q):
            dm = np.mean([np.min(np.linalg.norm(q - k_, axis=1)) for k_ in K[::4]])
            if best is None or dm < best[0]: best = (dm, aa, bb, tt)
            break
O = 0.0
if best: _, a, b, yt = best
s_ = np.hypot(1, b); n = np.array([1.0, -b]) / s_; r = (a + b * yt) / (s_ + b); yc = yt - r
if FORMA == "ogiva":                                   # straight sides where they fit under the body, the head = the body's own
    a0, b0 = np.polyfit(Rt[:, 1], Rt[:, 0], 1)[::-1]   # outline OG m in (pointed, long, as the original); joined smoothly
    OG = e("OG", "2"); Mo = np.zeros_like(Mb, np.uint8); cv2.fillPoly(Mo, [px(K)], 1)
    Mo = cv2.erode(Mo, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2 * OG / 0.25) + 1,) * 2)).astype(bool)
    jj, ii = np.mgrid[0:Mb.shape[0], 0:Mb.shape[1]]; X_ = ii * 0.25 - 200; Y_ = jj * 0.25 - 80
    T = (np.abs(X_) <= a0 + b0 * Y_ - OG) & (Y_ >= YB) & Mo
    def cont(m):
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
        c = np.c_[c[:, 0] * 0.25 - 200, c[:, 1] * 0.25 - 80]; c = smooth_corners(c, RC); c = np.roll(c, -np.argmax(c[:, 1]), 0)
        ar = 0.5 * np.sum(c[:, 0] * np.roll(c[:, 1], -1) - np.roll(c[:, 0], -1) * c[:, 1]); return c if ar < 0 else np.r_[c[:1], c[1:][::-1]]   # clockwise
    ext = cont(T); rw = int(RW / 0.25); inn = cont(cv2.erode(T.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rw + 1, 2 * rw + 1))))
    a, b, yt = a0, b0, ext[:, 1].max(); r = float("nan")
else:
    ext = smooth_corners(outline(O, a, b, yt), RC); inn = smooth_corners(outline(O + RW, a, b, yt), RC)
xs, ys, Zp = Hm["xs"], Hm["ys"], Hm["Zp"]
def zbot(p): ix = np.clip(np.searchsorted(xs, p[:, 0]), 0, len(xs) - 1); iy = np.clip(np.searchsorted(ys, p[:, 1]), 0, len(ys) - 1); return Zp[iy, ix]
zi = zbot(inn); H = float(np.nanmedian(ZP - zi[(inn[:, 1] > 0) & (inn[:, 1] < 400)])); H = max(H, 2.0)
out = {"contur_rama_exterior": np.c_[ext, np.full(len(ext), ZP)], "contur_rama_interior": np.c_[inn, np.full(len(inn), ZP)],
       "contur_rama_interior_jos": np.c_[inn, np.full(len(inn), ZP - H)]}
# sections: along the right half of the outer outline, every PAS m, normal inwards
R_ = ext[ext[:, 0] >= 0]; R_ = R_[np.argsort(-np.arctan2(R_[:, 1] - 200, R_[:, 0]))] if False else R_
cc = np.vstack([ext, ext[:1]]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cc, axis=0), axis=1))]; L = d[-1]; k = 0
for t in np.arange(0, L / 2 + 0.1, PAS):
    i = np.searchsorted(d, t); p = np.array([np.interp(t, d, cc[:, 0]), np.interp(t, d, cc[:, 1])])
    if p[0] < -0.1: continue
    tg = cc[min(i + 1, len(cc) - 1)] - cc[max(i - 1, 0)]; tg /= np.linalg.norm(tg); nin = np.array([tg[1], -tg[0]])   # clockwise (tip -> right -> back): inward = right
    s = np.linspace(0, 1, 25); bot = np.c_[p + np.outer(s * RW, nin), ZP - H * np.sqrt(np.clip(1 - (1 - s) ** 2, 0, 1))]
    top = np.c_[p + np.outer(s[::-1] * RW, nin), np.full(25, ZP)]
    sec = np.vstack([bot, top])                        # outer edge -> bottom -> inner bottom -> inner top -> along the top back
    out["sectiune_rama_%02d_D" % k] = sec
    if p[0] > 0.1: out["sectiune_rama_%02d_S" % k] = sec * [-1, 1, 1]
    k += 1
print("RAMA TRIUNGHI: laturi x = %.1f %+.3f y (potrivite pe conturul corpului y %.0f..%.0f), varf rotund R %.0f m (centru y %.0f, varf y %.0f), spate drept y %.0f, colturi R %.0f" % (a, b, FY0, FY1, r, yc, yt, YB, RC))
print("   inscris sub corp: laturi x = %.1f %+.3f y, varf y %.0f, R %.0f" % (a, b, yt, r))
print("   exterior x %.0f..%.0f y %.0f..%.0f; interior (%.0f m) x %.0f..%.0f y %.0f..%.0f; inaltimea ramei la interior H %.1f m (z %.1f..%.0f); %d sectiuni la %.0f m (dreapta + oglinda)" % (
    ext[:, 0].min(), ext[:, 0].max(), ext[:, 1].min(), ext[:, 1].max(), RW, inn[:, 0].min(), inn[:, 0].max(), inn[:, 1].min(), inn[:, 1].max(), H, ZP - H, ZP, k, PAS))
dv = []
for q in K:                                            # how far the triangle is from the body's outline
    dv.append(np.min(np.linalg.norm(ext - q, axis=1)))
print("   abaterea fata de conturul corpului: medie %.1f m, max %.1f m" % (np.mean(dv), np.max(dv)))
np.savez(OUT, **out)
