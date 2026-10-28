# The PS body's deck, simplified (asked: a V with a rounded nose seen from above, domed on top, flat underneath, a flat
# floor under the 086 lid so the lid's walls close a room over it): written in the same section format as ps_deck.py, so
# ps_corp_mesh.py builds it with the blend into the rear arms (the U). Outline: the deck envelope's edge fitted by a
# straight line along y + the rounded nose (quarter ellipse, same slope); bottom flat (BURTA); top a dome over |x|
# (centre height from the reference, smoothed along y); under the lid's footprint (the 086 outline, same fit as ps_086.py)
# the top comes down to a flat floor (BURTA + PODEA) with a smooth step; everything twicing-smoothed; edge rounded.
# Usage: python ps_corp_simplu.py <punte_corp.npz> <esantion_punte.npz> <out.npz>
import sys, os, numpy as np
N = np.load(sys.argv[1]); SP = np.load(sys.argv[2]); OUT = sys.argv[3]
env = lambda k, d: float(os.environ.get(k, d))
ZB, PODEA, RAMPA, YB = env("CORP_BURTA", "266"), env("CORP_PODEA", "6"), env("CORP_RAMPA", "10"), env("CORP_YB", "-20")
ys0, s0 = N["ys"], N["s"]; keep = ys0 >= YB - 1e-6; ys = ys0[keep]; K = len(ys); s = s0; M = len(s)
def gs1(z, sg):
    n = int(3 * sg); k = np.exp(-0.5 * (np.arange(-n, n + 1) / sg) ** 2); k /= k.sum()
    return np.convolve(np.r_[2 * z[0] - z[n:0:-1], z, 2 * z[-1] - z[-2:-n - 2:-1]], k, "valid")
tw = lambda z, sg: 2 * gs1(z, sg) - gs1(gs1(z, sg), sg)
# outline (asked: a V with a rounded nose, keeping the reference's general form): straight sides from the reference
# half-width at y = 0 to the nose's widest point (NAS_A at NAS_Y), then the nose a superellipse of exponent NAS_P (rounded
# but pointed like the reference's) down to the tip
E0 = N["edge"][keep]; ytip = float(N["ytip"]); Er = float(np.interp(0.0, ys, E0))
NA, NY, NP = env("CORP_NAS_A", "120"), env("CORP_NAS_Y", "280"), env("CORP_NAS_P", "1.6"); NB_ = ytip - NY
E = np.where(ys <= NY, Er + (NA - Er) * np.clip(ys, 0, None) / NY, NA * np.clip(1 - (np.clip(ys - NY, 0, None) / NB_) ** NP, 0, 1) ** (1 / NP))
E[ys < 0] = Er; E[-1] = 0.0; cE = [(NA - Er) / NY]; a_, b_ = NA, NB_
if os.environ.get("CORP_OGIVA"):                                        # asked: ONE smooth curve - w(y) = A (1 - ((y - y0)/L)^p)^(1/p)
    y0_, L_ = ys[0], ytip - ys[0]; best = None                          # from the deck's back to the tip, A and p fitted on the reference
    for p_ in np.linspace(1.2, 3.5, 47):
        f_ = (1 - np.clip((ys - y0_) / L_, 0, 1) ** p_) ** (1 / p_); A__ = float(f_ @ E0 / (f_ @ f_)); err = np.mean((A__ * f_ - E0) ** 2)
        if best is None or err < best[0]: best = (err, A__, p_)
    _, A__, p_ = best; E = A__ * (1 - np.clip((ys - y0_) / L_, 0, 1) ** p_) ** (1 / p_); cE = [0.0]; a_, b_ = A__, p_
    print("OGIVA: w(y) = %.1f (1 - ((y - %.0f)/%.0f)^%.2f)^(1/%.2f), abatere fata de referinta %.1f m (rms)" % (A__, y0_, L_, p_, p_, np.sqrt(best[0])))
# dome height: the reference's top at x = 0 (deck envelope) above the flat bottom, smoothed along y
Hc = tw(N["top"][keep][:, 0] - ZB, 8.0) + env("CORP_BOMBAT_PLUS", "0"); Hc = np.maximum(Hc, 8.0)   # + extra thickness on top
X = s[None, :] * E[:, None]
TOP = ZB + Hc[:, None] * np.sqrt(np.clip(1 - s[None, :] ** 2, 0, 1)) ** 0.6   # dome (fuller than an ellipse)
# the lid's footprint (same fit as ps_086.py): half-width W(y) straight, front YF - cF x^2, back at YBk
q = SP["p086"]; YBk, YF = q[:, 1].min(), q[:, 1].max(); yy = np.arange(YBk, YF, 4.0)
hw = np.array([(abs(q[np.abs(q[:, 1] - y) < 2][:, 0].min()) + q[np.abs(q[:, 1] - y) < 2][:, 0].max()) / 2 for y in yy])
A_ = np.polyfit(yy[yy < YF - 40], hw[yy < YF - 40], 1); W = lambda y: np.polyval(A_, y); WF = W(YF); xc_ = (q[:, 0].min() + q[:, 0].max()) / 2
fx = np.arange(-WF + 4, WF - 4, 4.0); fy = np.array([q[np.abs(q[:, 0] - xc_ - x) < 2][:, 1].max() for x in fx])
cF = float(np.linalg.lstsq((fx ** 2)[:, None], YF - fy, rcond=None)[0][0])
Y = np.repeat(ys[:, None], M, 1)
dist_in = np.minimum.reduce([W(Y) - X, (YF - cF * X ** 2) - Y, Y - YBk])   # >0 inside the footprint (distance-like)
mask = np.clip(0.5 + dist_in / RAMPA, 0, 1); mask = mask * mask * (3 - 2 * mask)
mask = np.minimum(mask, 1.0)   # smoothstep over RAMPA m
if os.environ.get("CORP_PLATOU"):                                       # no pocket: under the lid a flat plateau (smooth min of the
    zp = float(np.percentile(TOP[mask > 0.99], 10)) if os.environ.get("CORP_PLATOU") == "1" else float(os.environ["CORP_PLATOU"])   # dome and a level),
    kk = 6.0; sm = -kk * np.log(np.exp(-TOP / kk) + np.exp(-zp / kk))   # blended in over the footprint's edge
    TOP = TOP * (1 - mask) + sm * mask; PODEA = zp - ZB; print("PLATOU sub capac la z %.1f" % zp)
else: TOP = TOP * (1 - mask) + (ZB + PODEA) * mask
BOT = np.full_like(TOP, ZB)
def smooth2(A, sy, ss): return np.apply_along_axis(lambda z: gs1(z, ss), 1, np.apply_along_axis(lambda z: gs1(z, sy), 0, A))
G = lambda A: smooth2(A, env("CORP_NET_Y", "3"), env("CORP_NET_S", "2")); TOP = 2 * G(TOP) - G(G(TOP))
if os.environ.get("CORP_PLAT"):                                         # asked: flat top and bottom, curving only toward the edge:
    HP, NP_ = env("CORP_PLAT", "50"), env("CORP_PLAT_N", "4")           # each section a superellipse |x/E|^n + |(z-mid)/(H/2)|^n = 1
    HPy = HP * np.clip((ytip - ys) / env("CORP_PLAT_VARF", "120"), 0.35, 1.0) ** 0.5   # thinning only near the nose, smoothly
    MID = np.repeat((ZB + HPy / 2)[:, None], M, 1); H = (HPy / 2)[:, None] * (1 - s[None, :] ** NP_) ** (1 / NP_)
    TOP, BOT = MID + H, MID - H; print("PLAT: grosime %.0f m (la varf %.0f), sectiune super-elipsa n %.1f" % (HP, HPy[-1], NP_))
TOP = np.maximum(TOP, BOT + 2.0); MID, H = (TOP + BOT) / 2, (TOP - BOT) / 2
for k in range(K if not os.environ.get("CORP_PLAT") else 0):            # rounded edge (the flat section has its own)
    re = max(H[k, -8:].mean(), 1.0); se = 1 - min(re / max(E[k], 1e-6), 0.5)
    H[k] *= np.where(s > se, np.sqrt(np.clip(1 - ((s - se) / (1 - se)) ** 2, 0, 1)), 1.0)
H[-1] = 0.0; MID[-1] = MID[-1].mean()
TOPF, BOTF = MID + H, MID - H; X0 = np.zeros(K); DEP = np.zeros(K)
RU = env("CORP_U_R", "0")                                               # the U where the rear arms meet: a half-circle notch of
if RU > 0:                                                              # radius RU cut into the deck's last RU m (apex at YB + RU)
    for k in range(K):
        dy = ys[k] - YB
        if dy >= RU: continue
        xin = RU - np.sqrt(max(RU ** 2 - (RU - max(dy, 0.0)) ** 2, 0.0))
        h0 = (np.interp(xin, s * E[k], TOPF[k]) - np.interp(xin, s * E[k], BOTF[k])) / 2; dep = min(h0, 0.4 * (E[k] - xin), xin)
        x0 = xin + dep; xs = x0 + s * (E[k] - x0)                       # the row re-sampled from the notch wall to the edge
        TOPF[k], BOTF[k] = np.interp(xs, s * E[k], TOPF[k]), np.interp(xs, s * E[k], BOTF[k]); X0[k], DEP[k] = x0, dep
    print("U: scobitura semicerc raza %.0f m, varful U la y %.0f" % (RU, YB + RU))
np.savez(OUT, ys=ys, s=s, edge=E, x0=X0, depth=DEP, xin=X0 - DEP, top=TOPF, bot=BOTF, ytip=ytip, yapex=YB)
print("CORP SIMPLU: y %.0f..%.0f, V %.2f m/m + varf elipsa %.0f x %.0f, burta z %.0f, bombat pana la %.0f m, podea sub capac z %.0f (y %.0f..%.0f, |x| < %.0f..%.0f)" % (ys[0], ys[-1], cE[0], a_, b_, ZB, Hc.max(), ZB + PODEA, YBk, YF, W(YBk), WF))
