# The whole PS body (169_C) from one smooth field, no stitch (step 2, second form): PS = an ellipse per y on its rails (the
# nose closed along the outer silhouette), the arms = an ellipse per y between the outer and inner lines, the loops = the
# body's tube centre line (ps_corp_mesh.py CORP_DUMP + plan move) with ONE constant section, the arms' own at their last
# station (so the arms run into the loops without a neck). Each a first-order signed distance (smooth, no voxel steps);
# blended along y (PS -> arms under the U over TU m, arms -> tube over TT m); the U cut on the inner silhouette; built one y
# slice at a time (memory); a light gaussian, surface at 0 (marching cubes), a few Taubin passes. Writes verts / faces.
# With the guides continued to the arms' ends (ghid_extins.py) the loops follow them from above: each ring's middle between
# the two lines (across the line's own direction), its across width = their distance, smoothed, eased in past the arms;
# the line carried on to the guides' tip.
# Usage: python sectiuni_corp_tot.py <elipse_ghidaje.npz> <silueta.npz> <L_corp.npz> <plan_d.npz> <out.npz> [cell] [ghid_extins.npz]
import sys, os, numpy as np
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
R = np.load(sys.argv[1]); SIL = np.load(sys.argv[2]); LZ = np.load(sys.argv[3]); PD = np.load(sys.argv[4]); OUT = sys.argv[5]
CELL = float(sys.argv[6]) if len(sys.argv) > 6 else 2.0
YU, YT, TT = -33.4, -760.0, 70.0; TU = float(os.environ.get("SEC_TRECERE_U", "70"))
def rail(k, j, yq):
    Q = R[k]; o = np.argsort(Q[:, 1]); return np.interp(yq, Q[o, 1], Q[o, j])
Bo = SIL["B"]; Bo = Bo[Bo[:, 0] >= 0]; Bo = Bo[np.argsort(Bo[:, 1])]; ytipS = R["ps_lat"][:, 1].max()
def ps_par(y):
    w = rail("ps_lat", 0, y); top = rail("ps_sus", 2, y); bot = rail("ps_jos", 2, y)
    if y > ytipS:
        ws = np.interp(y, Bo[:, 1], Bo[:, 0]); h0 = top - bot; zc = (top + bot) / 2; s = ws / max(w, 1e-6); return ws, zc + h0 * s / 2, zc - h0 * s / 2
    return w, top, bot
def ar_par0(y): return rail("br_ext", 0, y), rail("br_int", 0, y), rail("br_sus", 2, y), rail("br_jos", 2, y)
UNI = os.environ.get("SEC_UNIFORM")                                      # asked: one diameter along the whole arm (the funnel near PS
UY0, UY1 = -150.0, -450.0                                               # kept): past UY0 the section eases into the loops' one by UY1,
def ar_par(y):                                                          # the middle staying between the guides
    o_, i_, t_, b_ = ar_par0(y)
    if not UNI: return o_, i_, t_, b_
    u = np.clip((UY0 - y) / (UY0 - UY1), 0, 1); u = u * u * (3 - 2 * u); cx, cz = (o_ + i_) / 2, (t_ + b_) / 2
    w = (1 - u) * (o_ - i_) + u * 2 * TA0; h = (1 - u) * (t_ - b_) + u * 2 * TB0; return cx + w / 2, cx - w / 2, cz + h / 2, cz - h / 2
ye = R["br_ext"][:, 1].min(); o_, i_, t_, b_ = ar_par0(ye); TA, TB = (o_ - i_) / 2, (t_ - b_) / 2   # the loops' section
TA0, TB0 = TA, TB
L = LZ["L"].copy(); L[..., :2] += PD["d"]; cen = L.mean(1)
def g1(v, s):
    n = int(3 * s); k = np.exp(-0.5 * (np.arange(-n, n + 1) / s) ** 2); k /= k.sum(); return np.convolve(np.pad(v, n, mode="edge"), k, "valid")
K0 = int(np.nonzero(cen[:, 1] < YT + 100)[0][0]); C = np.stack([g1(cen[:, i], 3.0) for i in range(3)], 1)[K0:]   # tube centre line
ke = int(np.argmin(np.abs(C[:, 1] - ye) + 1e3 * (np.arange(len(C)) > len(C) // 2)))   # the tube's point at the arms' last station
tgt = np.array([-(o_ + i_) / 2, ye, (t_ + b_) / 2]); off = tgt - C[ke]; off[1] = 0.0   # (on the inner branch): moved onto the
wk = np.clip(1 - (np.arange(len(C)) - ke) / 120.0, 0, 1); wk = wk * wk * (3 - 2 * wk); C = C + wk[:, None] * off   # arm's middle, eased out along the loop
print("TUB mutat pe mijlocul bratului: %.1f m in x, %.1f m in z la y %.0f" % (off[0], off[2], ye))
AK = np.full(len(C), TA)                                                # the section's across half width per point of the line
if len(sys.argv) > 7:                                                  # asked: the loops follow the guides continued to the arms' ends
    GX = np.load(sys.argv[7]); go, gi = [Q[Q[:, 0] <= 0] for Q in (GX["B"], GX["B_int"])]   # (the _S side, from above)
if os.environ.get("PICIOR_INDOIT"):                                      # asked: the legs as straight tubes at the right angle and
    TBR = np.load(os.environ["PICIOR_INDOIT"])["C"]; kb_ = int(np.argmin(TBR[:, 1]))   # thickness, then bent into place: line A = the
    mA = (R["br_ext"][:, 1] < -450)                                     # arm's 3D middle (straight fit), line B = the reference loop's
    PA_ = np.stack([-(R["br_ext"][mA, 0] + R["br_int"][mA, 0]) / 2, R["br_ext"][mA, 1], (R["br_sus"][mA, 2] + R["br_jos"][mA, 2]) / 2], 1)
    def fit3(P): c = P.mean(0); d = np.linalg.svd(P - c)[2][0]; return c, d / np.linalg.norm(d)
    cA, dA = fit3(PA_); dA = dA if dA[1] < 0 else -dA                    # far branch (straight fit, going up), the bend between them
    FB = TBR[kb_:][(TBR[kb_:, 1] > -1150) & (TBR[kb_:, 1] < -560)]; cB, dB = fit3(FB); dB = dB if dB[1] > 0 else -dB   # one smooth
    on = lambda c, d, y: c + d * ((y - c[1]) / d[1])                    # the point of a line at height y (in plan, along y)
    ybot = TBR[kb_, 1]; yt = ybot + float(os.environ.get("PICIOR_RIDICARE", "80"))   # the U-turn: both lines taken at the loop's
    p0, p1 = on(cA, dA, yt), on(cB, dB, yt); dd = np.linalg.norm(p1 - p0); Lt = 1.7 * dd   # bottom (+ a radius), joined by one smooth
    t_ = np.linspace(0, 1, max(int(2.5 * dd), 40), endpoint=False)      # U (quintic: tangent to both, no kink)
    h = [1 - 10 * t_ ** 3 + 15 * t_ ** 4 - 6 * t_ ** 5, t_ - 6 * t_ ** 3 + 8 * t_ ** 4 - 3 * t_ ** 5, 10 * t_ ** 3 - 15 * t_ ** 4 + 6 * t_ ** 5, -4 * t_ ** 3 + 7 * t_ ** 4 - 3 * t_ ** 5]
    bend = np.outer(h[0], p0) + np.outer(h[1], dA * Lt) + np.outer(h[2], p1) + np.outer(h[3], dB * Lt)
    def line(p, q, step=2.0): n = max(int(np.linalg.norm(q - p) / step), 1); return p + np.outer(np.arange(n) / n, q - p)
    start = C[ke]; Lc = dd; PAc, PBc = p0, p1
    tipy = -427.0 - TA; endB = cB + dB * ((tipy - cB[1]) / dB[1])
    leg = np.vstack([line(start, p0), bend, line(p1, endB), [endB]])
    C = np.vstack([C[:ke], leg]); AK = np.full(len(C), TA)
    print("PICIOR indoit: brat dir (%.3f, %.3f, %.3f), ramura dir (%.3f, %.3f, %.3f); U intre (%.0f, %.0f, %.0f) si (%.0f, %.0f, %.0f), deschidere %.0f m; fund y %.0f; capat (%.0f, %.0f, %.0f)" % (
        *dA, *dB, *p0, *p1, dd, bend[:, 1].min(), *endB))
elif len(sys.argv) > 7 and "centru_bucla" in GX.files:                    # the drawn centre line (straight + one arc + straight, ghid_bucla.py):
    cl = GX["centru_bucla"] * [-1, 1]                                   # the loop's middle laid on it by length along both (from the arms'
    j0 = int(np.argmin(np.linalg.norm(cl - C[ke, :2], axis=1)))         # last station to the tip), height kept, eased in over 40 rings
    sc_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C[ke:, :2], axis=0), axis=1))]; sl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cl[j0:], axis=0), axis=1))]
    kbo = int(np.argmin(C[ke:, 1])); jbn = int(np.argmin(cl[j0:, 1]))     # the old loop's bottom laid on the new arc's bottom: its dive
    m_ = np.interp(sc_, [0, sc_[kbo], sc_[-1]], [0, sl[jbn], sl[-1]])     # (height) happens with the turn, as on the reference
    tgt = np.stack([np.interp(m_, sl, cl[j0:, i]) for i in range(2)], 1)
    ramp = np.clip(np.arange(len(C) - ke) / 40.0, 0, 1); ramp = ramp * ramp * (3 - 2 * ramp)
    C[ke:, :2] = (1 - ramp)[:, None] * C[ke:, :2] + ramp[:, None] * tgt; AK = np.full(len(C), TA)
    zs_ = C[ke:, 2]; n_ = 75; kz = np.exp(-0.5 * (np.arange(-n_, n_ + 1) / 10.0) ** 2); kz /= kz.sum()   # the height along the loop
    zf = np.convolve(np.pad(zs_, n_, mode="edge"), kz, "valid"); C[ke:, 2] = (1 - ramp) * zs_ + ramp * zf   # smoothed (no 3D bend)
    print("BUCLE pe linia de centru desenata: %d inele, mutare max %.1f m, sectiune constanta %.1f x %.1f m" % (len(C) - ke, np.abs((1 - 0) * (tgt - C[ke:, :2])).max(), 2 * TA, 2 * TB))
elif len(sys.argv) > 7:
    def hit(p, n_, Q):                                                 # where the line p + u*n_ crosses the guide (nearest), or None
        a_, b_ = Q[:-1], Q[1:]; e_ = b_ - a_; den = n_[0] * e_[:, 1] - n_[1] * e_[:, 0]; ok = np.abs(den) > 1e-9
        w_ = a_ - p; u = (w_[:, 0] * e_[:, 1] - w_[:, 1] * e_[:, 0]) / np.where(ok, den, 1); v = (w_[:, 0] * n_[1] - w_[:, 1] * n_[0]) / np.where(ok, den, 1)
        m_ = ok & (v >= 0) & (v <= 1) & (np.abs(u) < 130)
        return None if not m_.any() else p + n_ * u[m_][np.argmin(np.abs(u[m_]))]
    Tp = np.gradient(C[:, :2], axis=0); Tp /= np.maximum(np.linalg.norm(Tp, axis=1), 1e-9)[:, None]
    dxy = np.zeros((len(C), 2)); wv = np.zeros(len(C)); Wd = np.full(len(C), 2 * TA)
    for k in range(ke, len(C)):
        n_ = np.array([-Tp[k, 1], Tp[k, 0]]); qo, qi = hit(C[k, :2], n_, go), hit(C[k, :2], n_, gi)
        if qo is None or qi is None: continue
        dxy[k] = (qo + qi) / 2 - C[k, :2]; Wd[k] = np.linalg.norm(qo - qi); wv[k] = 1.0
    gk = lambda v, s_: np.convolve(np.pad(v, int(3 * s_), mode="edge"), (lambda q: q / q.sum())(np.exp(-0.5 * (np.arange(-int(3 * s_), int(3 * s_) + 1) / s_) ** 2)), "valid")
    for k in range(len(C)):                                            # rings without a crossing take their neighbours' values
        if not wv[k] and k >= ke: j_ = np.nonzero(wv)[0]; j_ = j_[np.argmin(np.abs(j_ - k))] if len(j_) else k; dxy[k], Wd[k] = dxy[j_], Wd[j_]
    ramp = np.clip((np.arange(len(C)) - ke) / 40.0, 0, 1); ramp = ramp * ramp * (3 - 2 * ramp)
    dxy = np.stack([gk(dxy[:, 0], 8.0), gk(dxy[:, 1], 8.0)], 1) * ramp[:, None]; Wd = gk(Wd, 8.0)
    T3 = np.gradient(C, axis=0); T3 /= np.linalg.norm(T3, axis=1)[:, None]   # seen from above a diving tube shows its height too:
    ah = np.sqrt(np.maximum((Wd / 2) ** 2 - (TB * np.abs(T3[:, 2])) ** 2, 0))  # only the rest is its width, kept within +-20 %
    ah = gk(np.clip(ah, 0.8 * TA, 1.2 * TA), 8.0)
    if UNI: ah = np.full(len(C), TA)                                     # one diameter: the loops keep the arm's section
    C[:, :2] += dxy; AK = (1 - ramp) * TA + ramp * ah
    tip = np.array([-564.0, -427.0]); tl = C[-1] - C[-2]; tl /= np.linalg.norm(tl); ext = []
    p_ = C[-1].copy()
    while (tip - p_[:2]) @ (tl[:2] / max(np.linalg.norm(tl[:2]), 1e-9)) > AK[-1] and len(ext) < 200: p_ = p_ + tl * 2.0; ext.append(p_.copy())
    if ext: C = np.vstack([C, ext]); AK = np.r_[AK, np.full(len(ext), AK[-1])]
    print("BUCLE pe ghidaje: %d inele mutate (max %.1f m), latime %.0f..%.0f m, prelungit cu %d inele spre capat" % (int(wv.sum()), np.abs(dxy).max(), (2 * AK[ke:]).min(), (2 * AK[ke:]).max(), len(ext)))
rings = []                                                             # section frames carried along the line without turning
T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]     # (parallel transport, double reflection): the flat
sd = np.cross(T[0], [0, 0, 1.0]); sd /= np.linalg.norm(sd)              # ellipse does not twist where the loop dives
for k in range(len(C)):
    if k:
        v1 = C[k] - C[k - 1]; c1 = v1 @ v1; rL = sd - (2 / c1) * (v1 @ sd) * v1; tL = T[k - 1] - (2 / c1) * (v1 @ T[k - 1]) * v1
        v2 = T[k] - tL; c2 = v2 @ v2; sd = rL - (2 / c2) * (v2 @ rL) * v2 if c2 > 1e-12 else rL; sd /= np.linalg.norm(sd)
    if 0 < k < len(C) - 1:
        ds = np.linalg.norm(C[k + 1] - C[k - 1]) / 2; up = np.cross(sd, T[k]); rings.append((C[k], T[k], sd.copy(), up / np.linalg.norm(up), ds, AK[k]))
cy = np.array([r[0][1] for r in rings]); KB = int(np.argmin(cy))          # the loop's bottom: rings past it = the branch going back up
X0, X1 = -(np.abs(C[:, 0]).max() + AK.max() + 20), np.abs(C[:, 0]).max() + AK.max() + 20; Y0, Y1 = C[:, 1].min() - TA - 20, 480.0
Z0, Z1 = min(C[:, 2].min() - TA - 20, 200.0), 400.0
DPS = os.environ.get("SEC_DOAR_PS")                                     # PS alone (the arms are their own tubes, brate_tub.py): the
if DPS: YEND = float(DPS); X0, X1, Y0, Z0, Z1 = -260.0, 260.0, YEND - 60.0, 150.0, 460.0   # sections down to YEND, the back end rounded
PRZ = np.load(os.environ["PS_PRIZE"]) if DPS and os.environ.get("PS_PRIZE") else None   # PS's sockets: the arms' first rings (to the
if PRZ is not None:                                                     # joint cut + a little) joined smoothly to PS
    kz_ = int(PRZ["ks"]) + 6; PP, PF1, PF2, PA, PB, PT = [PRZ[k][:kz_] for k in ("centru", "F1", "F2", "Ak", "Bk", "T")]
    Y0 = min(Y0, PP[:, 1].min() - 60); X0, X1 = -max(260.0, np.abs(PP[:, 0]).max() + 80), max(260.0, np.abs(PP[:, 0]).max() + 80)
CAP = np.load(os.environ["PS_CAPAC"]) if DPS and os.environ.get("PS_CAPAC") else None   # flat where the 086 hood sits
xs = np.arange(X0 + CELL / 2, X1, CELL); ys = np.arange(Y0 + CELL / 2, Y1, CELL); zs = np.arange(Z0 + CELL / 2, Z1, CELL)
NX, NY, NZ = len(xs), len(ys), len(zs); print("GRILA %d x %d x %d (%.0f M celule, %.1f m); bucle: sectiune %.1f x %.1f m, %d inele" % (NX, NY, NZ, NX * NY * NZ / 1e6, CELL, 2 * TA, 2 * TB, len(rings)))
X, Zg = np.meshgrid(xs, zs, indexing="ij")
if CAP is not None:                                                     # the hood's footprint (its outline from above) as a plan
    import cv2                                                          # distance (< 0 inside); the top there cut flat at PS_CAPAC_Z,
    from scipy.ndimage import distance_transform_edt as edt_            # rising at 45 deg outside (rounded), into the dome
    hull = cv2.convexHull(((CAP[:, :2] - [X0, Y0]) / CELL).astype(np.int32)); msk = np.zeros((len(ys), len(xs)), np.uint8); cv2.fillPoly(msk, [hull], 1)
    capd = ((edt_(msk == 0) - edt_(msk == 1)) * CELL).T.astype(np.float32); CZ = float(os.environ.get("PS_CAPAC_Z", "316"))
def edist(u, w, a_, b_):
    a_, b_ = np.maximum(a_, 1e-3), np.maximum(b_, 1e-3); g = (u / a_) ** 2 + (w / b_) ** 2 - 1
    gr = 2 * np.sqrt((u / a_ ** 2) ** 2 + (w / b_ ** 2) ** 2); return np.maximum(g / np.maximum(gr, 1e-6), -np.minimum(a_, b_))
PSG, PSN = float(os.environ.get("PS_GROS", "1")), float(os.environ.get("PS_N", "2"))
def sedist(u, w, a_, b_, n):                                            # signed distance to a superellipse, first order
    a_, b_ = max(a_, 1e-3), max(b_, 1e-3); p, q = np.abs(u / a_) + 1e-9, np.abs(w / b_) + 1e-9; G = (p ** n + q ** n) ** (1 / n)
    gu, gw = p ** (n - 1) / a_ * G ** (1 - n), q ** (n - 1) / b_ * G ** (1 - n); return np.maximum((G - 1) / np.maximum(np.sqrt(gu ** 2 + gw ** 2), 1e-9), -min(a_, b_))
Bi = SIL["B_int"]; Bi = Bi[Bi[:, 0] >= 0]; Bi = Bi[np.argsort(Bi[:, 1])]
sm = lambda v: v * v * (3 - 2 * v); BIG = np.float32(1e3)
F = np.empty((NX, NY, NZ), np.float32)
for j, y in enumerate(ys):
    if DPS:                                                             # (thickness x PS_GROS about its middle, section exponent PS_N:
        w, top, bot = ps_par(max(y, YU + 2.0)); hb = (top - bot) / 2 * PSG    # < 2 = thicker middle, thinner edges - an arrowhead)
        if os.environ.get("PS_FUND_PLAT"):                              # flat bottom on the base, only the top domed: a half
            ht = (top - bot) * PSG; gt = sedist(X, Zg - bot, w, ht, PSN); gb = bot - Zg   # (super)ellipse over the base plane,
            fp = (gt + gb + np.sqrt((gt - gb) ** 2 + 6.0 ** 2)) / 2      # the bottom edge slightly rounded
        else: fp = edist(X, Zg - (top + bot) / 2, w, hb) if PSN == 2.0 else sedist(X, Zg - (top + bot) / 2, w, hb, PSN)
        a_ = YEND - y; k_ = 25.0
        f = (fp + a_ + np.sqrt((fp - a_) ** 2 + k_ ** 2)) / 2                # rounded cut at the back (smooth max)
        if CAP is not None:
            zc_ = CZ + np.maximum(capd[:, j], 0)[:, None]; g_ = Zg - zc_; f = (f + g_ + np.sqrt((f - g_) ** 2 + 8.0 ** 2)) / 2
        if PRZ is not None:                                             # the sockets: the arms' rings (both sides), smooth union
            fa_ = np.full(X.shape, BIG, np.float32)
            for r in np.nonzero(np.abs(PP[:, 1] - y) < 80)[0]:
                for sg in (1, -1):
                    cc = PP[r] * [sg, 1, 1]; Q = np.stack([X - cc[0], np.full(X.shape, y - cc[1]), Zg - cc[2]], -1)
                    t_, f1, f2 = PT[r] * [sg, 1, 1], PF1[r] * [sg, 1, 1], PF2[r] * [sg, 1, 1]
                    d = edist(Q @ f1, Q @ f2, PA[r], PB[r]).astype(np.float32); d[np.abs(Q @ t_) > 2.0 + CELL] = BIG; fa_ = np.minimum(fa_, d)
            f = (f + fa_ - np.sqrt((f - fa_) ** 2 + 20.0 ** 2)) / 2      # smooth union (radius 20 m)
        if Bi[:, 1].min() <= y <= YU:                                     # the U cut with rounded edges (smooth max)
            g_ = np.interp(y, Bi[:, 1], Bi[:, 0]) - np.abs(X); f = (f + g_ + np.sqrt((f - g_) ** 2 + 20.0 ** 2)) / 2
        F[:, j] = f; continue
    t1 = sm(np.clip((YU - y) / TU, 0, 1)); t2 = sm(np.clip((YT - y) / TT, 0, 1))
    fp = fa = ft = BIG
    if t1 < 1 and y <= Y1:
        w, top, bot = ps_par(max(y, YU + 2.0)); fp = edist(X, Zg - (top + bot) / 2, w, (top - bot) / 2)
    if t1 > 0 and t2 < 1:
        o_, i_, t_, b_ = ar_par(min(y, YU - 2.0)); fa = edist(np.abs(X) - (o_ + i_) / 2, Zg - (t_ + b_) / 2, (o_ - i_) / 2, (t_ - b_) / 2)
    ft = np.full(X.shape, BIG, np.float32); fb = np.full(X.shape, BIG, np.float32)
    for r in np.nonzero(np.abs(cy - y) < 60)[0]:
        if t2 <= 0 and r <= KB: continue
        c, t, sd, up, ds, ak = rings[r]
        for sg in (1, -1):
            cc = c * [sg, 1, 1]; il, ih = np.searchsorted(xs, cc[0] - max(ak, TA) - 25), np.searchsorted(xs, cc[0] + max(ak, TA) + 25)
            kl, kh = np.searchsorted(zs, cc[2] - max(ak, TA) - 25), np.searchsorted(zs, cc[2] + max(ak, TA) + 25)
            Q = np.stack([X[il:ih, kl:kh] - cc[0], np.full((ih - il, kh - kl), y - cc[1]), Zg[il:ih, kl:kh] - cc[2]], -1)
            tt_, sdd, upp = t * [sg, 1, 1], sd * [sg, 1, 1], up * [sg, 1, 1]
            d = edist(Q @ sdd, Q @ upp, ak, TB).astype(np.float32); d[np.abs(Q @ tt_) > ds + CELL] = BIG
            tgt_ = ft if r <= KB else fb; tgt_[il:ih, kl:kh] = np.minimum(tgt_[il:ih, kl:kh], d)
    f = (1 - t1) * fp + t1 * np.minimum((1 - t2) * fa + t2 * ft, fb)        # the far branch joined whole
    if Bi[:, 1].min() <= y <= YU: f = np.maximum(f, np.interp(y, Bi[:, 1], Bi[:, 0]) - np.abs(X))   # the U cut
    F[:, j] = f
F = gaussian_filter(F, 0.7)
v, fcs, _, _ = marching_cubes(F, 0.0, spacing=(CELL, CELL, CELL)); del F; v += [X0 + CELL / 2, Y0 + CELL / 2, Z0 + CELL / 2]
e = np.unique(np.sort(np.vstack([fcs[:, [0, 1]], fcs[:, [1, 2]], fcs[:, [2, 0]]]), 1), axis=0); deg = np.bincount(e.ravel(), minlength=len(v)).astype(float)[:, None]
def avg(V):
    S = np.zeros_like(V); np.add.at(S, e[:, 0], V[e[:, 1]]); np.add.at(S, e[:, 1], V[e[:, 0]]); return S / np.maximum(deg, 1)
for _ in range(10): v = v + 0.5 * (avg(v) - v); v = v + -0.53 * (avg(v) - v)
np.savez(OUT, v=v.astype(np.float32), f=fcs.astype(np.int32))
print("SUPRAFATA: %d varfuri, %d fete; y %.0f..%.0f, x %.0f..%.0f, z %.0f..%.0f" % (len(v), len(fcs), v[:, 1].min(), v[:, 1].max(), v[:, 0].min(), v[:, 0].max(), v[:, 2].min(), v[:, 2].max()))
