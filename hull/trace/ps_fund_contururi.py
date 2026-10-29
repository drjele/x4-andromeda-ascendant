# Outlines for the PS bottom split into pieces (asked: sep_PS simple, completely flat bottom; a separate rim on the edge
# under it, the level difference = the rim's height; the keel's big side the same shape as its small side; the keel's 2
# little ears separate pieces reaching the rim's outline). All in plan (x, y), ship coordinates, symmetric:
#   contur_corp  - the PS's outline in the flat-bottom plane z = ZP (the body's bottom),
#   rama_interior - that outline RW m in (the rim = the ring between the two),
#   carena_jos / carena_sus - the keel floor's outline (flat, z = ZF; from the current floor, z <= ZF + 1) and the same shape
#     scaled to the current big side's box (x +-KX, y KY0..KY1), at z = ZP,
#   ureche_D / ureche_S - plates from the keel's top outline (2 m in) out to the rim's inner outline (1 m in), y EY0..EY1.
# Usage: python ps_fund_contururi.py <ps full.npz v (x -1700)> <faces.npz:key> <keel heightmap npz (fund_harta)> <out.npz>
# env ZP=280 RW=20 ZF=247 KX=115 KY0=-23 KY1=350 EY0=255 EY1=285
import sys, os, numpy as np, trimesh, cv2
from scipy.ndimage import gaussian_filter1d
e = lambda k, d: float(os.environ.get(k, d))
ZP, RW, ZF, KX, KY0, KY1, EY0, EY1 = e("ZP", "280"), e("RW", "20"), e("ZF", "247"), e("KX", "115"), e("KY0", "-23"), e("KY1", "350"), e("EY0", "255"), e("EY1", "285")
V = np.load(sys.argv[1])["v"].astype(float) + [1700.0, 0, 0]; fn, k = sys.argv[2].split(":"); f = np.load(fn)[k]; H = np.load(sys.argv[3]); OUT = sys.argv[4]
t = trimesh.Trimesh(V, f, process=False); PX = 0.25; X0, Y0 = -200.0, -80.0; W_, H_ = int(400 / PX), int(580 / PX)
def to_px(p): return np.c_[(p[:, 0] - X0) / PX, (p[:, 1] - Y0) / PX].astype(np.int32)
def from_px(c): return np.c_[c[:, 0] * PX + X0, c[:, 1] * PX + Y0]
def sym(m): return m | m[:, ::-1] if False else (m | np.flip(m, 1)) if abs(X0 + W_ * PX / 2) < 1e-6 else m
def contour(m, sm=4.0, n=400):
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
    c = from_px(c); c = np.c_[gaussian_filter1d(c[:, 0], sm / PX, mode="wrap"), gaussian_filter1d(c[:, 1], sm / PX, mode="wrap")]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([c, c[:1]]), axis=0), axis=1))]; u = np.linspace(0, d[-1], n, endpoint=False)
    cc = np.vstack([c, c[:1]]); p = np.c_[np.interp(u, d, cc[:, 0]), np.interp(u, d, cc[:, 1])]
    i = np.argmax(p[:, 1] - 1e3 * np.abs(p[:, 0]) * 0); p = np.roll(p, -np.argmax(p[:, 1]), 0)          # start at the tip
    a = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    return p if a > 0 else np.r_[p[:1], p[1:][::-1]]                                                   # counter-clockwise
def mask_poly(p):
    m = np.zeros((H_, W_), np.uint8); cv2.fillPoly(m, [to_px(p)], 1); return m.astype(bool)
s = t.section(plane_origin=[0, 0, ZP], plane_normal=[0, 0, 1]); L = max(s.discrete, key=lambda q: np.ptp(q[:, 0]) * np.ptp(q[:, 1]))[:, :2]
M = mask_poly(L); M = M | np.flip(M, 1); corp = contour(M, 2.0)
r = int(round(RW / PX)); ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
Mi = cv2.erode(M.astype(np.uint8), ker).astype(bool); rama_i = contour(Mi, 4.0)
xs, ys, Zk = H["xs"], H["ys"], H["Zk"]; Fm = np.nan_to_num(Zk, nan=999) <= ZF + 1        # the keel floor (flat part)
gx, gy = np.meshgrid(xs, ys); P = np.c_[gx[Fm], gy[Fm]]; Mf = np.zeros((H_, W_), np.uint8)
step = int(np.ceil((xs[1] - xs[0]) / PX));
for q in to_px(P): cv2.rectangle(Mf, tuple(q - step // 2), tuple(q + step // 2), 1, -1)
Mf = Mf.astype(bool); Mf = Mf | np.flip(Mf, 1)
k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)); Mf = cv2.morphologyEx(cv2.morphologyEx(Mf.astype(np.uint8), cv2.MORPH_CLOSE, k3), cv2.MORPH_OPEN, k3)
n_, lab, st, _ = cv2.connectedComponentsWithStats(Mf); Mf = lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
jos = contour(Mf, 3.0, 240)
sx = KX / np.abs(jos[:, 0]).max(); y0, y1 = jos[:, 1].min(), jos[:, 1].max(); sus = np.c_[jos[:, 0] * sx, KY0 + (jos[:, 1] - y0) * (KY1 - KY0) / (y1 - y0)]
Ms = mask_poly(sus); out_of = (Ms & ~Mi).sum() * PX * PX
def xr(p, y):                                          # the outline's outer x at height y (right side)
    q = np.vstack([p, p[:1]]); xx = []
    for a, b in zip(q[:-1], q[1:]):
        if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]: xx.append(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
    xx = [x for x in xx if x > 0]; return max(xx) if xx else np.nan
ey = np.linspace(EY0, EY1, 31); xin = np.array([xr(sus, y) for y in ey]) - 2; xout = np.array([xr(rama_i, y) for y in ey]) + 1
ur = np.r_[np.c_[xin, ey], np.c_[xout, ey][::-1]]
out = dict(contur_corp=corp, rama_interior=rama_i, carena_jos=jos, carena_sus=sus, ureche_D=ur, ureche_S=ur * [-1, 1],
           z=np.array([ZP, ZF]))
print("CONTUR CORP la z %.0f: x %.0f..%.0f, y %.0f..%.0f" % (ZP, corp[:, 0].min(), corp[:, 0].max(), corp[:, 1].min(), corp[:, 1].max()))
print("RAMA: latime %.0f m, interior x %.0f..%.0f, y %.0f..%.0f" % (RW, rama_i[:, 0].min(), rama_i[:, 0].max(), rama_i[:, 1].min(), rama_i[:, 1].max()))
print("CARENA JOS (podea z %.0f): x %.0f..%.0f, y %.0f..%.0f; SUS (z %.0f): x %.0f..%.0f, y %.0f..%.0f (scara x %.2f, y %.2f); iese din interiorul ramei %.0f m2" % (
    ZF, jos[:, 0].min(), jos[:, 0].max(), y0, y1, ZP, sus[:, 0].min(), sus[:, 0].max(), sus[:, 1].min(), sus[:, 1].max(), sx, (KY1 - KY0) / (y1 - y0), out_of))
print("URECHI y %.0f..%.0f: de la carena x %.1f..%.1f la rama x %.1f..%.1f (lungime %.1f..%.1f m)" % (EY0, EY1, xin.min(), xin.max(), xout.min(), xout.max(), (xout - xin).min(), (xout - xin).max()))
np.savez(OUT, **out)
