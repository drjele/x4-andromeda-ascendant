# The PS's surface brought onto its confirmed vertebrae (asked: alter sep_PS's surface to follow the guides). Every 2 m of y
# between the shoulders the vertebra is rebuilt as in vertebre_ps.py (deck / belly kept up to the attach points, side bulged
# out to the median outline); the side between the attach points, seen from O = (attach x, median z), is a curve r_s(theta)
# on the PS and r_t(theta) on the vertebra (theta from the bottom attach -90 to the top attach +90 deg) - every vertex there
# is moved along its ray from O by r_t / r_s (a star-shaped stretch: it cannot fold a slice; nothing moves at the attach
# points). Tables smoothed along y and interpolated per vertex; both sides (|x|). Same faces, same vertex order.
# VP_ATT2 attach depth at the back (linear from VP_ATT at the front); VA_FADE_FATA / VA_FADE ease-in / ease-out (m);
# VA_SI_INAUNTRU=1 also pulled in where the PS sticks out past the guide; past the U each leg stub handled on its own;
# VA_DOAR_SUS=1 only the upper half; VA_PRINDE=y_a,y_b,k soft clamp onto the guide (in plan) in that strip.
# Usage: python ps_vertebre_aplica.py <pieces.npz> <ghid_median.npz> <out.npz> ; env VP_Y0=262 VP_Y1=-30 VP_ATT=25 VP_K=0.6 VA_NET=2
import sys, os, numpy as np, trimesh
from scipy.ndimage import gaussian_filter1d
D = np.load(sys.argv[1]); M = np.load(sys.argv[2]); OUT = sys.argv[3]; MX = -1700.0; e = lambda k, d: float(os.environ.get(k, d))
Y0, Y1, ATT, KT, NET = e("VP_Y0", "262"), e("VP_Y1", "-30"), e("VP_ATT", "25"), e("VP_K", "0.6"), e("VA_NET", "2")
v0 = D["PS__v"].astype(float) - [MX, 0, 0]; f0 = D["PS__f"]; ps = trimesh.Trimesh(v0, f0, process=False)
Gm = M["contur_umar_median"]; ZM = Gm[0, 2]; R = Gm[Gm[:, 0] >= 0]; R = R[np.argsort(-R[:, 1])]; xg = lambda y: np.interp(-y, -R[:, 1], R[:, 0])
def herm(p0, t0, p1, t1, n=40):
    L = np.linalg.norm(p1 - p0) * KT; s = np.linspace(0, 1, n)[:, None]
    return (2*s**3 - 3*s**2 + 1) * p0 + (s**3 - 2*s**2 + s) * L * t0 + (-2*s**3 + 3*s**2) * p1 + (s**3 - s**2) * L * t1
TH = np.radians(np.linspace(-90, 90, 361)); ys, XA, RS, RT = [], [], [], []
def polar(curve, O):                                   # r(theta) of a curve seen from O, on the TH grid (theta = atan2(dz, dx))
    q = curve - O; th = np.arctan2(q[:, 1], q[:, 0]); r = np.hypot(q[:, 0], q[:, 1]); o = np.argsort(th)
    return np.interp(TH, th[o], r[o])
for y in np.arange(Y0, Y1 - 0.1, -2.0):
    s = ps.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: continue
    Lp = max([q[:, [0, 2]] for q in s.discrete], key=lambda q: q[:, 0].max())
    if Lp[:, 0].min() > 1:                             # past the U: a leg stub - ordered round its own centre, outer side
        Lq = Lp[:-1] if np.allclose(Lp[0], Lp[-1]) else Lp; c = Lq.mean(0); a_ = np.arctan2(Lq[:, 1] - c[1], Lq[:, 0] - c[0])
        H = Lq[np.abs(a_) < np.radians(100)]; H = H[np.argsort(-np.arctan2(H[:, 1] - c[1], H[:, 0] - c[0]))]
    else:
        H = Lp[Lp[:, 0] >= -0.5]
        if len(H) < 6: continue
        ang = np.arctan2(H[:, 1] - ZM, H[:, 0]); H = H[np.argsort(-ang)]
    if len(H) < 6: continue
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(H, axis=0), axis=1))]; u = np.arange(0, d[-1], 0.5); H = np.c_[np.interp(u, d, H[:, 0]), np.interp(u, d, H[:, 1])]
    att = ATT + (e("VP_ATT2", str(ATT)) - ATT) * np.clip((Y0 - y) / (Y0 - Y1), 0, 1)   # attach depth: ATT at the front -> ATT2 at the back
    xm = H[:, 0].max(); up = np.where((H[:, 0] >= xm - att) & (H[:, 1] > ZM))[0]; dn = np.where((H[:, 0] >= xm - att) & (H[:, 1] < ZM))[0]
    if not len(up) or not len(dn): continue
    IN = os.environ.get("VA_SI_INAUNTRU", "0") == "1"  # also pulled in where the PS sticks out past the guide (the fin)
    i, j = up[0], dn[-1]; G = np.array([xg(y) if IN else max(xg(y), xm), ZM])
    t_i = H[min(i + 4, len(H) - 1)] - H[i]; t_i /= np.linalg.norm(t_i); t_j = H[j] - H[max(j - 4, 0)]; t_j /= np.linalg.norm(t_j)
    tgt = np.vstack([herm(H[i], t_i, G, np.array([0.0, -1.0])), herm(G, np.array([0.0, -1.0]), H[j], t_j)[1:]])
    O = np.array([min(H[i, 0], H[j, 0]), ZM]); ys.append(y); XA.append(O[0]); RS.append(polar(H[i:j + 1], O)); RT.append(polar(tgt, O))
ys, XA, RS, RT = np.array(ys), np.array(XA), np.array(RS), np.array(RT)
F = gaussian_filter1d(RT / np.maximum(RS, 1e-6), NET, axis=0, mode="nearest"); XA = gaussian_filter1d(XA, NET, mode="nearest")
if os.environ.get("VA_CAPETE_FIXE", "0") == "1": F[0] = F[-1] = 1.0   # (forced 1 at the ends made a dent at y -20..-30)
if os.environ.get("VA_DOAR_AFARA", "0") == "1": F = np.maximum(F, 1.0)   # the side never pulled inwards (belly kept at least)
o = np.argsort(ys); ys, XA, F = ys[o], XA[o], F[o]
FF = float(os.environ.get("VA_FADE_FATA", "0"))       # at the front the stretch eases in over FF m (the rebuilt side never matches
if FF > 0:                                             # the PS exactly, even where the outline does not move)
    w = np.clip((ys.max() - ys) / FF, 0, 1)[:, None]; w = w * w * (3 - 2 * w); F = 1 + w * (F - 1)
FT = float(os.environ.get("VA_FADE", "0"))             # past the last station (back end): the stretch fades to none over FT m
if FT > 0:
    ye = np.arange(ys[0] - 2, ys[0] - FT - 0.1, -2.0)[::-1]; w = ((ye - (ys[0] - FT)) / FT)[:, None]
    ys = np.r_[ye, ys]; XA = np.r_[np.full(len(ye), XA[0]), XA]; F = np.vstack([1 + w * (F[0] - 1), F])
ax_ = np.abs(v0[:, 0]); sel = (v0[:, 1] >= ys.min()) & (v0[:, 1] <= ys.max())
xa = np.interp(v0[:, 1], ys, XA); sel &= ax_ >= xa
th = np.arctan2(v0[:, 2] - ZM, ax_ - xa); sel &= np.abs(th) <= np.pi / 2
if os.environ.get("VA_DOAR_SUS", "0") == "1": sel &= th > 0   # only the upper half (deck side) onto the vertebrae
ky = np.interp(v0[:, 1], ys, np.arange(len(ys))); k0 = np.clip(np.floor(ky).astype(int), 0, len(ys) - 1); k1 = np.minimum(k0 + 1, len(ys) - 1); a = ky - k0
kt = np.interp(th, TH, np.arange(len(TH))); t0 = np.clip(np.floor(kt).astype(int), 0, len(TH) - 1); t1 = np.minimum(t0 + 1, len(TH) - 1); b = kt - t0
fac = (1 - a) * ((1 - b) * F[k0, t0] + b * F[k0, t1]) + a * ((1 - b) * F[k1, t0] + b * F[k1, t1]); fac = np.where(sel, fac, 1.0)
V = v0.copy(); r = np.hypot(ax_ - xa, v0[:, 2] - ZM); rn = r * fac
V[:, 0] = np.sign(v0[:, 0]) * (xa + rn * np.cos(th)); V[:, 2] = ZM + rn * np.sin(th); V[~sel] = v0[~sel]
CL = os.environ.get("VA_PRINDE")                       # y_a,y_b,k: in that strip whatever sticks out past the guide (in plan)
if CL:                                                 # is brought back onto it - a smooth min, k m soft (the old fin)
    ya, yb, kc = [float(q) for q in CL.split(",")]; w = np.clip(np.minimum(V[:, 1] - ya, yb - V[:, 1]) / 6, 0, 1); w = w * w * (3 - 2 * w)
    xx = np.abs(V[:, 0]); g_ = xg(V[:, 1]); h = np.clip(kc - np.abs(xx - g_), 0, None) / kc; sm = np.minimum(xx, g_) - h * h * kc / 4
    m = (w > 0) & (xx > g_ - kc); V[m, 0] = np.sign(V[m, 0]) * (xx[m] + w[m] * (sm[m] - xx[m]))
t = trimesh.Trimesh(V, f0, process=False); a0 = np.degrees(ps.face_adjacency_angles); a1 = np.degrees(t.face_adjacency_angles)
dm = np.linalg.norm(V - v0, axis=1)
print("PS PE VERTEBRE: %d statii (y %.0f..%.0f), %d varfuri mutate (max %.1f m), etans %s; falduri >120 grd %d (inainte %d), >60 grd %d (inainte %d)" % (
    len(ys), ys.max(), ys.min(), (dm > 0.05).sum(), dm.max(), t.is_watertight, (a1 > 120).sum(), (a0 > 120).sum(), (a1 > 60).sum(), (a0 > 60).sum()))
for y in (200, 120, 40, -20):
    s1 = t.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0]); P = np.vstack(list(s1.discrete))
    print("   y %4d: cel mai lat x acum %.1f, ghidajul %.1f" % (y, P[:, 0].max(), xg(y)))
np.savez(OUT, v=(V + [MX, 0, 0]).astype(np.float32))
