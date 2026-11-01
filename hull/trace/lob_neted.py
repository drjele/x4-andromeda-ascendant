# The lobe as one clean surface (asked: the new arms' lobes - clean surfaces, small waves still show; it should be one lobe / teardrop,
# sphere-like, smooth): from rib SECT (eased in over RAMPA m) to the tip, per section across the spine an ellipse fitted to the piece
# (centre, two radii, angle); the four parameters smoothed strongly along the spine (smoothing spline, SMOOTH); over the last LUNG m
# the radii follow an ogive (1-u)^PUTERE to the point, the tip carried EXTRA m further along the spine's end. Every vertex in the zone
# moved onto its section's ellipse at the same ellipse angle (its offset along the spine kept). Both arms (left mirrored).
# Usage: python lob_neted.py <piece npz> <guides npz> <out npz> ; env SECT=42 RAMPA=60 LUNG=80 EXTRA=8 PUTERE=0.6 PAS=4 SMOOTH=3
import sys, os, numpy as np
from scipy.spatial import cKDTree
from scipy.interpolate import UnivariateSpline
from brat_fata_lib import ellipse_fit
Z = np.load(sys.argv[1]); G = np.load(sys.argv[2]); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d)); sm = lambda w: w * w * (3 - 2 * w)
V = Z["brat_fata_D__v"].copy(); F = Z["brat_fata_D__f"]; SP = G["spinare_brat_fata_D"]
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]; dS = arclen(SP); TS = np.gradient(SP, axis=0); TS /= np.linalg.norm(TS, axis=1)[:, None]
tE = TS[-1]
def frame(sq):
    sq = np.atleast_1d(sq); i = np.clip(np.searchsorted(dS, sq), 1, len(SP) - 1); f = np.clip((sq - dS[i - 1]) / (dS[i] - dS[i - 1]), 0, 1)
    p = SP[i - 1] + (SP[i] - SP[i - 1]) * f[:, None]; p = np.where((sq > dS[-1])[:, None], SP[-1] + np.outer(sq - dS[-1], tE), p)
    t = TS[i - 1] + (TS[i] - TS[i - 1]) * f[:, None]; t /= np.linalg.norm(t, axis=1)[:, None]
    e1 = np.cross(t, [0, 0, 1.0]); e1 /= np.linalg.norm(e1, axis=1)[:, None]; e2 = np.cross(e1, t); return p, t, e1, e2
kd = cKDTree(SP); j = kd.query(V)[1]; s = dS[j] + np.einsum("ij,ij->i", V - SP[j], TS[j])
sA = dS[kd.query(G["sectiune_brat_fata_D_%02d" % int(e("SECT", "42"))].mean(0))[1]]; send = s.max()
LU, EX, PW, RP = e("LUNG", "80"), e("EXTRA", "8"), e("PUTERE", "0.6"), e("RAMPA", "60"); s0c = send - LU
zone = s > sA - RP; P, T, E1, E2 = frame(s[zone]); q = V[zone] - P; along = np.einsum("ij,ij->i", q, T); x, y = np.einsum("ij,ij->i", q, E1), np.einsum("ij,ij->i", q, E2)
st = np.arange(sA - RP, s0c + 1e-6, e("PAS", "4")); par = []
for s_ in st:
    m = np.abs(s[zone] - s_) < 3
    if m.sum() < 20: par.append(None); continue
    c, r, an = ellipse_fit(np.c_[x[m], y[m]])
    if r[0] < r[1]: an += np.pi / 2
    an = (an + np.pi / 2) % np.pi - np.pi / 2; par.append([c[0], c[1], r.max(), r.min(), an])
ok = np.array([p_ is not None for p_ in par]); st_ = st[ok]; PR = np.array([p_ for p_ in par if p_ is not None]); PR[:, 4] = np.unwrap(2 * PR[:, 4]) / 2
spl = [UnivariateSpline(st_, PR[:, k], s=len(st_) * e("SMOOTH", "3") * (np.std(PR[:, k]) * 0.05) ** 2, k=3) for k in range(5)]
def params(sq):
    sc = np.minimum(sq, s0c); out_ = np.array([sp(sc) for sp in spl]).T          # (from the ogive's start: its radii scaled down)
    u = np.clip((sq - s0c) / LU, 0, 1); fac = (1 - u) ** PW; out_[:, 2] *= fac; out_[:, 3] *= fac; out_[:, 0] *= fac; out_[:, 1] *= fac; return out_
sz = s[zone]; snew = np.where(sz > s0c, s0c + (sz - s0c) * (LU + EX) / LU, sz); P2, T2, E12, E22 = frame(snew)
pr = params(sz); cx, cy, a, b, an = pr.T
xr, yr = x - cx, y - cy; c_, s_ = np.cos(-an), np.sin(-an); xl, yl = xr * c_ - yr * s_, xr * s_ + yr * c_
th = np.arctan2(yl / np.maximum(b, 1e-3), xl / np.maximum(a, 1e-3)); xn, yn = a * np.cos(th), b * np.sin(th)
c2, s2 = np.cos(an), np.sin(an); xw, yw = xn * c2 - yn * s2 + cx, xn * s2 + yn * c2 + cy
w = sm(np.clip((sz - (sA - RP)) / RP, 0, 1))
NV = P2 + T2 * along[:, None] + E12 * xw[:, None] + E22 * yw[:, None]
V[zone] = V[zone] * (1 - w[:, None]) + NV * w[:, None]
np.savez(OUT, brat_fata_D__v=V, brat_fata_D__f=F, brat_fata_S__v=V * [-1, 1, 1], brat_fata_S__f=F[:, ::-1])
print("LOB neted: de la s %.0f (rampa %.0f m) la varf (s %.0f -> %.0f), ogiva pe ultimii %.0f m; %d sectiuni potrivite; %d varfuri mutate, max %.2f m" % (
    sA, RP, send, send + EX, LU, len(st_), zone.sum(), np.linalg.norm(V - Z["brat_fata_D__v"], axis=1).max()))
