# Sections + long guide lines on one graph (asked: on PS the sections grow steadily from the tip back to the thickness where
# the arms join; the tip contours stay; guides top / bottom / left / right through the sections, aligned, then the copy is
# built from them - like a hull's stations and waterlines). From sectiuni_spline.py's contours: per station its rails
# (top z, bottom z, half width; on the arms per arm: outer x, inner x, top z, bottom z). PS (in front of the U): width and
# height made non-decreasing from the tip backwards (isotonic fit, then a smoothing spline; the tip, y > YTIP, kept), the
# middle height only smoothed; each contour's shape (radius per angle, in its box) smoothed along y; then every contour
# rescaled to its new rails, so sections and rails agree. Arms: rails and shapes only smoothed along y. Writes the aligned
# sections (same flat format), the rails, and the graph (raw dots, aligned lines).
# With a silhouette file (outer B, inner U) the widths are taken from it (asked: every section touches the silhouettes left
# and right): PS half width = outer line; arms outer = outer line, inner = inner line, each eased back into the measured
# value over FADE m past the line's end.
# Usage: python sectiuni_aliniate.py <sectiuni.npz> <out_prefix> [ytip] [sigma_stations] [silueta.npz]
import sys, numpy as np, cv2
from scipy.interpolate import UnivariateSpline
Z = np.load(sys.argv[1]); PRE = sys.argv[2]; YTIP = float(sys.argv[3]) if len(sys.argv) > 3 else 400.0; SG = float(sys.argv[4]) if len(sys.argv) > 4 else 6.0
ys, pts, sy, st = Z["ys"], Z["pts"], Z["sy"], Z["start"]; YU = -33.4; NA = 180; FADE = 100.0
SIL = np.load(sys.argv[5]) if len(sys.argv) > 5 else None
def sil_x(Q, yv):                                                      # the silhouette's right-side x at each y (nan where absent)
    R_ = Q[Q[:, 0] >= 0]; R_ = R_[np.argsort(R_[:, 1])]; return np.where((yv >= R_[:, 1].min()) & (yv <= R_[:, 1].max()), np.interp(yv, R_[:, 1], R_[:, 0]), np.nan)
def onto(v, yv, Q):                                                    # v replaced by the silhouette where it exists; past its end
    R_ = Q[Q[:, 0] >= 0]; R_ = R_[np.argsort(R_[:, 1])]; xs = sil_x(Q, yv)  # the silhouette's straight side continued (no bend)
    ye = R_[0, 1]; k_ = (R_[min(20, len(R_) - 1), 0] - R_[0, 0]) / (R_[min(20, len(R_) - 1), 1] - R_[0, 1])
    return np.where(np.isnan(xs) & (yv < ye), R_[0, 0] + k_ * (yv - ye), np.where(np.isnan(xs), v, xs))
cont = {round(float(y), 1): [pts[st[c]:st[c + 1]] for c in np.nonzero(np.abs(sy - y) < 1e-3)[0]] for y in ys}
def polar(F, c):                                                       # the contour as NA points evenly along it, from its top (the
    lo, hi = F.min(0), F.max(0); half = (hi - lo) / 2; U = (F - c) / half  # middle on PS) going clockwise, in its box - works for
    if 0.5 * np.sum(U[:, 0] * np.roll(U[:, 1], -1) - np.roll(U[:, 0], -1) * U[:, 1]) > 0: U = U[::-1]   # any shape (not star-shaped)
    U = np.roll(U, -int(np.argmax(U[:, 1] - 0.02 * np.abs(U[:, 0]))), axis=0); Uc = np.vstack([U, U[:1]])
    s_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Uc, axis=0), axis=1))]; u = np.linspace(0, s_[-1], NA, endpoint=False)
    return np.stack([np.interp(u, s_, Uc[:, 0]), np.interp(u, s_, Uc[:, 1])], 1).ravel()
def unpolar(r, c, half): return c + r.reshape(-1, 2) * half
def iso_up(v):                                                         # non-decreasing least-squares fit (pool adjacent violators)
    b = [[x, 1.0] for x in v]; out = []
    for x in b:
        out.append(x)
        while len(out) > 1 and out[-2][0] > out[-1][0]:
            x2 = out.pop(); x1 = out.pop(); w = x1[1] + x2[1]; out.append([(x1[0] * x1[1] + x2[0] * x2[1]) / w, w])
    return np.concatenate([[m] * int(w) for m, w in out])
def gs(v, s):
    n = int(3 * s); k = np.exp(-0.5 * (np.arange(-n, n + 1) / s) ** 2); k /= k.sum(); return np.convolve(np.pad(v, n, mode="edge"), k, "valid")
def gs2(M, s): return np.stack([gs(M[:, j], s) for j in range(M.shape[1])], 1)
# ---- PS: one contour per station (in front of the U)
yp = np.array([y for y in ys if y > YU and any(F[:, 0].min() < 0 < F[:, 0].max() for F in cont[round(float(y), 1)])])   # one body across the middle
FP = [max([F for F in cont[round(float(y), 1)] if F[:, 0].min() < 0 < F[:, 0].max()], key=len) for y in yp]
top = np.array([F[:, 1].max() for F in FP]); bot = np.array([F[:, 1].min() for F in FP]); w = np.array([F[:, 0].max() for F in FP])
H = top - bot; zc = (top + bot) / 2
tip = yp > YTIP; wt = np.where(tip, 50.0, 1.0)
def mono(v, rear, sg):                                                 # tip kept, then growing outwards (sg: +1 up / -1 down) to the
    u = sg * v; m = np.minimum(iso_up(u), sg * rear); m[tip] = u[tip]; m = np.maximum.accumulate(m)   # rear value, reached at the
    n = len(m); ramp = np.clip((np.arange(n) - (n - 25)) / 24.0, 0, 1); m = (1 - ramp) * m + ramp * sg * rear   # U, smooth
    f = UnivariateSpline(-yp, m, w=wt, s=n * 0.3, k=3)(-yp); f = np.maximum.accumulate(np.where(tip, u, f)); f[-1] = sg * rear
    return sg * np.maximum.accumulate(f)
ARMS0 = None                                                           # the arms' rails at the U (filled below, used here)
# ---- arms: the right blob per station (behind the U)
ya = np.array([y for y in ys if y <= YU and any(F[:, 0].min() > 0 for F in cont[round(float(y), 1)])])
FA = [max([F for F in cont[round(float(y), 1)] if F[:, 0].min() > 0], key=len) for y in ya]
ao, ai, at, ab = [np.array(v) for v in zip(*[(F[:, 0].max(), F[:, 0].min(), F[:, 1].max(), F[:, 1].min()) for F in FA])]
sm = lambda v: UnivariateSpline(-ya, gs(v, SG), s=len(v) * 0.5, k=3)(-ya)
ao2, ai2, at2, ab2 = sm(ao), sm(ai), sm(at), sm(ab)
if SIL is not None: ao2, ai2 = onto(ao2, ya, SIL["B"]), onto(ai2, ya, SIL["B_int"])
RA = np.array([polar(F, np.array([(F[:, 0].max() + F[:, 0].min()) / 2, (F[:, 1].max() + F[:, 1].min()) / 2])) for F in FA]); RAs = gs2(RA, SG)
AP = [unpolar(RAs[i], np.array([(ao2[i] + ai2[i]) / 2, (at2[i] + ab2[i]) / 2]), np.array([(ao2[i] - ai2[i]) / 2, (at2[i] - ab2[i]) / 2])) for i in range(len(ya))]
# ---- PS rails grow to the arms' values at the U (top up, bottom down, width out), the tip kept
top2, bot2, w2 = mono(top, at2[0], 1), mono(bot, ab2[0], -1), mono(w, ao2[0], 1); H2, zc2 = top2 - bot2, (top2 + bot2) / 2
if SIL is not None:                                                    # PS half width = the outer silhouette (tip kept)
    xs = sil_x(SIL["B"], yp); w2 = np.where(np.isnan(xs), w2, xs)       # the tip too: every section touches it (heights kept)
R = np.array([polar(F, np.array([0.0, (F[:, 1].max() + F[:, 1].min()) / 2])) for F in FP]); Rs = gs2(R, SG); Rs[tip] = R[tip]
RP = [unpolar(Rs[i], np.array([0.0, zc2[i]]), np.array([w2[i], H2[i] / 2])) for i in range(len(yp))]
RP = [np.vstack([P[P[:, 0] >= 0], (P[P[:, 0] >= 0] * [-1, 1])[::-1]]) for P in RP]   # exactly symmetric
import os
if os.environ.get("SEC_ELIPSA"):                                        # asked: every contour an ellipse (a flattened circle) on
    tt_ = np.linspace(0, 2 * np.pi, NA, endpoint=False) + np.pi / 2      # its rails - top / bottom / sides, nothing else
    el = lambda cx, cz, ax, bz: np.stack([cx + ax * np.cos(tt_), cz + bz * np.sin(tt_)], 1)
    RP = [el(0.0, zc2[i], w2[i], H2[i] / 2) for i in range(len(yp))]
    AP = [el((ao2[i] + ai2[i]) / 2, (at2[i] + ab2[i]) / 2, (ao2[i] - ai2[i]) / 2, (at2[i] - ab2[i]) / 2) for i in range(len(ya))]
if SIL is not None:                                                    # check: every section touches the silhouettes where they are
    eo = [abs(P[:, 0].max() - x) for P, x in zip(RP, sil_x(SIL["B"], yp)) if not np.isnan(x)] + [abs(P[:, 0].max() - x) for P, x in zip(AP, sil_x(SIL["B"], ya)) if not np.isnan(x)]
    ei = [abs(P[:, 0].min() - x) for P, x in zip(AP, sil_x(SIL["B_int"], ya)) if not np.isnan(x)]
    print("ATINGERE silueta: exterior %d statii, abatere max %.2f m; interior %d statii, abatere max %.2f m" % (len(eo), max(eo), len(ei), max(ei)))
# ---- save (flat) + rails
allc = [(y, P) for y, P in zip(yp, RP)] + [(y, P) for y, P in zip(ya, AP)] + [(y, P * [-1, 1]) for y, P in zip(ya, AP)]
pp, syy, ss = [], [], []
for y, P in allc: ss.append(sum(len(q) for q in pp)); syy.append(y); pp.append(P)
np.savez(PRE + ".npz", ys=ys, pts=np.vstack(pp), sy=np.array(syy), start=np.array(ss + [sum(len(q) for q in pp)]))
zw = np.array([P[np.argmax(P[:, 0]), 1] for P in RP]); zo = np.array([P[np.argmax(P[:, 0]), 1] for P in AP]); zi = np.array([P[np.argmin(P[:, 0]), 1] for P in AP])
zw, zo, zi = gs(zw, 15.0), gs(zo, 15.0), gs(zi, 15.0)                  # the side lines' height (the widest point jumps on flat sides)
np.savez(PRE + "_ghidaje.npz", ps_y=yp, ps_sus=np.stack([np.zeros_like(yp), yp, zc2 + H2 / 2], 1), ps_jos=np.stack([np.zeros_like(yp), yp, zc2 - H2 / 2], 1),
         ps_lat=np.stack([w2, yp, zw], 1), br_ext=np.stack([ao2, ya, zo], 1), br_int=np.stack([ai2, ya, zi], 1),
         br_sus=np.stack([(ao2 + ai2) / 2, ya, at2], 1), br_jos=np.stack([(ao2 + ai2) / 2, ya, ab2], 1))
d = lambda a, b: np.abs(a - b)
print("PS (%d statii, varf y > %.0f pastrat): latime %.0f..%.0f m, grosime %.0f..%.0f m, ambele crescatoare spre spate; corectie max latime %.1f, grosime %.1f, mijloc %.1f m" % (
    len(yp), YTIP, w2.min(), w2.max(), H2.min(), H2.max(), d(w2, w).max(), d(H2, H).max(), d(zc2, zc).max()))
print("BRATE (%d statii): exterior %.0f..%.0f, interior %.0f..%.0f, grosime %.0f..%.0f m; corectie max %.1f / %.1f / %.1f / %.1f m" % (
    len(ya), ao2.min(), ao2.max(), ai2.min(), ai2.max(), (at2 - ab2).min(), (at2 - ab2).max(), d(ao2, ao).max(), d(ai2, ai).max(), d(at2, at).max(), d(ab2, ab).max()))
# ---- the graph: every rail against y, raw dots and aligned lines
Wd, Hd = 1500, 700; im = np.full((Hd, Wd, 3), 255, np.uint8); Y0, Y1 = -510, 480
fx = lambda y: (40 + (Y1 - y) / (Y1 - Y0) * (Wd - 80)).astype(int)
def plot(y, v, vmin, vmax, oy, hh, col, raw=None):
    fy = lambda q: (oy + hh - (q - vmin) / (vmax - vmin) * hh).astype(int)
    if raw is not None:
        for a_, b_ in zip(fx(y), fy(raw)): cv2.circle(im, (int(a_), int(b_)), 1, (190, 190, 190), -1)
    cv2.polylines(im, [np.stack([fx(y), fy(v)], 1).astype(np.int32)], False, col, 2)
plot(yp, w2, 0, 260, 20, 280, (0, 0, 220), w); plot(ya, ao2, 0, 260, 20, 280, (0, 0, 220), ao); plot(ya, ai2, 0, 260, 20, 280, (220, 80, 0), ai)
cv2.putText(im, "latime: PS jumatate (rosu), brat exterior (rosu) / interior (albastru)", (45, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
plot(yp, zc2 + H2 / 2, 240, 380, 360, 300, (0, 140, 0), top); plot(yp, zc2 - H2 / 2, 240, 380, 360, 300, (140, 0, 140), bot)
plot(ya, at2, 240, 380, 360, 300, (0, 140, 0), at); plot(ya, ab2, 240, 380, 360, 300, (140, 0, 140), ab)
cv2.putText(im, "inaltime z: sus (verde), jos (mov); varf <- y -> spate", (45, 355), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
for yy in (YTIP, YU): x_ = int(fx(np.array([yy]))[0]); cv2.line(im, (x_, 0), (x_, Hd), (200, 200, 200), 1)
cv2.imwrite(PRE + "_grafic.png", im); print("SALVAT", PRE)
