# The hood's guides to the standard (asked: g_cap_sep_contur_capac_baza a trapezoid, no small inner ribs; the hood's ribs
# and its middle spine start from the base outline; that outline and g_psr_sep_contur_sus_nervuri identical). The base:
# a trapezoid fitted to the hood's silhouette seen from above - back edge y YB, front edge y YF, straight sides fitted on
# y SY0..SY1 - corners rounded RC (lines + tangent arcs), symmetric, in the plane z ZC. Ribs every PAS m (planes y = const):
# from the base outline's left point over the hood's top to its right point (the top taken from the hood's own section,
# the last EA m eased down onto the base points); the spine likewise along x = 0 from the back to the front edge.
# CT_MOD=trapez: clean ribs - slanted walls (UNGHI) up to a flat top, height H_SPATE at the back -> H_FATA at the front,
# corners RF_T; the spine the same along x = 0.
# Usage: python ghid_capac_trapez.py <hood npz v,f (ship coords)> <out.npz> ; env ZC=326 RC=8 PAS=20 EA=6 SM=1.5 DZ=0
import sys, os, numpy as np, trimesh, cv2
from scipy.ndimage import gaussian_filter1d
D = np.load(sys.argv[1]); OUT = sys.argv[2]; e = lambda k, d: float(os.environ.get(k, d))
ZC, RC, PAS, EA, SM, DZ = e("ZC", "326"), e("RC", "8"), e("PAS", "20"), e("EA", "6"), e("SM", "1.5"), e("DZ", "0")
t = trimesh.Trimesh(D["v"], D["f"], process=False); y0, y1 = t.bounds[0, 1], t.bounds[1, 1]
YB, YF = e("YB", str(round(y0, 1))), e("YF", str(round(y1, 1)))
PX = 0.25; X0, Y0 = -100.0, y0 - 10; M = np.zeros((int((y1 - y0 + 20) / PX), int(200 / PX)), np.uint8)
px = lambda q: np.c_[(q[:, 0] - X0) / PX, (q[:, 1] - Y0) / PX].astype(np.int32)
for tri in t.vertices[t.faces][:, :, :2]: cv2.fillConvexPoly(M, px(tri), 1)
M = (M | np.flip(M, 1)).astype(bool); rows = np.arange(M.shape[0]) * PX + Y0
half = np.array([(np.where(M[j])[0].max() * PX + X0) if M[j].any() else np.nan for j in range(M.shape[0])])
SY0, SY1 = e("SY0", str(YB + 20)), e("SY1", str(YF - 30)); ok = (rows > SY0) & (rows < SY1) & np.isfinite(half)
b, a = np.polyfit(rows[ok], half[ok], 1)                                                  # side: x = a + b y
def seg(p, q, step=0.5): n = max(int(np.linalg.norm(q - p) / step), 2); return np.linspace(p, q, n)
def arc(c, r, a0, a1):
    n = max(int(abs(a1 - a0) / np.radians(3)) + 2, 3); tt = np.linspace(a0, a1, n); return np.c_[c[0] + r * np.cos(tt), c[1] + r * np.sin(tt)]
def corner(P, d0, d1, r):                              # fillet at corner P between incoming dir d0 and outgoing dir d1 (unit)
    th = np.arccos(np.clip(-d0 @ d1, -1, 1)); L = r / np.tan(th / 2); t0 = P - d0 * L; t1 = P + d1 * L
    bis = (d1 - d0); bis /= np.linalg.norm(bis); c = P + bis * r / np.sin(th / 2)
    return t0, t1, arc(c, r, np.arctan2(t0[1] - c[1], t0[0] - c[0]), np.arctan2(t1[1] - c[1], t1[0] - c[0]))
# right half, clockwise from the front middle: front edge -> front-right corner -> side -> back-right corner -> back edge
Pf = np.array([a + b * YF, YF]); Pb = np.array([a + b * YB, YB])
dF = np.array([1.0, 0.0]); dS = (Pb - Pf) / np.linalg.norm(Pb - Pf); dB = np.array([-1.0, 0.0])
f0, f1, fa = corner(Pf, dF, dS, RC); b0, b1, ba = corner(Pb, dS, dB, RC)
h = np.vstack([seg(np.array([0.0, YF]), f0), fa[1:], seg(f1, b0)[1:], ba[1:], seg(b1, np.array([0.0, YB]))[1:]])
T = np.vstack([h, (h[::-1] * [-1, 1])[1:-1]]); T = np.vstack([T, T[:1]])
out = {"contur_capac_baza": np.c_[T, np.full(len(T), ZC)]}
def xb(y): return a + b * y                            # the base's half-width at y (the straight sides)
def top_profile(L, coord):                             # the top envelope of a section loop along `coord` (0 = x, 1 = y)
    return L
k = 0
for y in np.arange(np.ceil((YB + RC + 2) / PAS) * PAS, YF - RC - 1, PAS):
    s = t.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: continue
    Lp = max([q[:, [0, 2]] for q in s.discrete], key=lambda q: np.ptp(q[:, 0])); w = xb(y)
    xs = np.linspace(-w, w, int(2 * w / 0.5) + 1); zt = []
    for x in xs:                                       # highest crossing of the loop at this x
        zz = [];  q = np.vstack([Lp, Lp[:1]])
        for p0, p1 in zip(q[:-1], q[1:]):
            if (p0[0] - x) * (p1[0] - x) <= 0 and p0[0] != p1[0]: zz.append(p0[1] + (p1[1] - p0[1]) * (x - p0[0]) / (p1[0] - p0[0]))
        zt.append(max(zz) if zz else np.nan)
    zt = np.array(zt); okz = np.isfinite(zt); zt = np.interp(xs, xs[okz], zt[okz]); zt = gaussian_filter1d(np.maximum(zt, ZC), SM / 0.5, mode="nearest")
    d_end = np.minimum(xs + w, w - xs); u = np.clip(d_end / EA, 0, 1); u = u * u * (3 - 2 * u); zt = ZC + u * (zt - ZC)
    out["sectiune_capac_%02d" % k] = np.c_[xs, np.full(len(xs), y), zt]; k += 1
s = t.section(plane_origin=[0, 0, 0], plane_normal=[1, 0, 0]); Lp = max([q[:, [1, 2]] for q in s.discrete], key=lambda q: np.ptp(q[:, 0]))
ys = np.linspace(YB, YF, int((YF - YB) / 0.5) + 1); zt = []
for y in ys:
    zz = []; q = np.vstack([Lp, Lp[:1]])
    for p0, p1 in zip(q[:-1], q[1:]):
        if (p0[0] - y) * (p1[0] - y) <= 0 and p0[0] != p1[0]: zz.append(p0[1] + (p1[1] - p0[1]) * (y - p0[0]) / (p1[0] - p0[0]))
    zt.append(max(zz) if zz else np.nan)
zt = np.array(zt); okz = np.isfinite(zt); zt = np.interp(ys, ys[okz], zt[okz]); zt = gaussian_filter1d(np.maximum(zt, ZC), SM / 0.5, mode="nearest")
d_end = np.minimum(ys - YB, YF - ys); u = np.clip(d_end / EA, 0, 1); u = u * u * (3 - 2 * u); zt = ZC + u * (zt - ZC)
out["spinare_capac_mijloc"] = np.c_[np.zeros(len(ys)), ys, zt]
if os.environ.get("CT_MOD") == "trapez":             # clean trapezoid ribs: slanted walls UNGHI deg from the horizontal up to a flat
    HB, HF, UN, RF = e("H_SPATE", "10"), e("H_FATA", "18"), np.radians(e("UNGHI", "55")), e("RF_T", "4")   # top; height HB at the
    hgt = lambda y: HB + (HF - HB) * (y - YB) / (YF - YB)                                                   # back -> HF at the front
    def fillet_open(P, r):                             # an open polyline (2D) with every inner corner rounded r (lines + arcs)
        out_ = [P[0]]
        for i in range(1, len(P) - 1):
            d0 = (P[i] - P[i - 1]) / np.linalg.norm(P[i] - P[i - 1]); d1 = (P[i + 1] - P[i]) / np.linalg.norm(P[i + 1] - P[i])
            t0, t1, ar = corner(P[i], d0, d1, r); out_ += [*seg(out_[-1], t0)[1:], *ar[1:]]
        out_ += list(seg(out_[-1], P[-1])[1:]); return np.array(out_)
    for kk in [k_ for k_ in out if k_.startswith("sectiune_capac")]: del out[kk]
    k = 0
    for y in np.arange(np.ceil((YB + RC + 2) / PAS) * PAS, YF - RC - 1, PAS):
        w = xb(y); h = hgt(y); dx = h / np.tan(UN)
        P = np.array([[-w, ZC], [-w + dx, ZC + h], [w - dx, ZC + h], [w, ZC]]); C = fillet_open(P, RF)
        out["sectiune_capac_%02d" % k] = np.c_[C[:, 0], np.full(len(C), y), C[:, 1]]; k += 1
    hb, hf = hgt(YB), hgt(YF)
    P = np.array([[YB, ZC], [YB + hb / np.tan(UN), ZC + hb], [YF - hf / np.tan(UN), ZC + hf], [YF, ZC]]); C = fillet_open(P, RF)
    out["spinare_capac_mijloc"] = np.c_[np.zeros(len(C)), C[:, 0], C[:, 1]]
    print("   TRAPEZ: inaltime %.0f m in spate -> %.0f m in fata (z %.0f -> %.0f), pereti oblici la %.0f grd, colturi R %.0f; %d nervuri + spinarea" % (
        HB, HF, ZC + HB, ZC + HF, np.degrees(UN), RF, k))
for kk in out: out[kk] = out[kk] + [0, 0, DZ]
d = np.diff(T, axis=0); ang = np.degrees(np.abs(np.angle(np.exp(1j * (np.arctan2(d[1:, 1], d[1:, 0]) - np.arctan2(d[:-1, 1], d[:-1, 0]))))))
print("BAZA CAPAC TRAPEZ (z %.1f): spate y %.1f latime +-%.1f, fata y %.1f latime +-%.1f, laturi drepte x = %.1f %+.3f y, colturi R %.0f; frangere max %.1f grd la 0,5 m" % (
    ZC, YB, xb(YB), YF, xb(YF), a, b, RC, ang.max()))
print("   %d nervuri (y = const, la %.0f m) si spinarea (x 0), toate pornesc si se termina pe baza; fara contururile camerelor" % (k, PAS))
np.savez(OUT, **out)
