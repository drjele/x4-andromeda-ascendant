# The PS deck with its rear junction: nose + plate 086 + side strips 103 + nose strips 055 + blades 118/117, from the
# nose tip back to YEND, where the deck opens in a U into the two rear (V) arms. Each section (plane y = const) is an
# envelope over |x| (both halves pooled: symmetric by construction) between an inner edge XIN (0 on the deck, the U
# opening behind it) and the outer edge EDGE: top = highest shell point, bottom = lowest. Openings (teardrops, slots in
# the belly, holes) are closed by a one-sided morphological closing (top: dents filled, plates kept; bottom: slots
# filled), mirrored at x = 0, nothing past the edges so the thin fins stay; then smoothed with twicing; the outer edge
# rounded (top and bottom meet in a half-ellipse); the inner side of the arms a half-ellipse wall bulging into the gap,
# growing from nothing at the U's apex. Rounder nose: the outline's last metres a quarter-ellipse with the same slope.
# Grid: y every DY m, s from the inner wall to the edge in NS steps.
# Usage: python ps_deck.py <esantion_punte.npz> <out.npz> [yend]
import sys, os, numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv
D = np.load(sys.argv[1]); OUT = sys.argv[2]; YEND = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
KEYS = [k for k in D.files if k not in os.environ.get("PUNTE_FARA", "").split(",")]   # pieces left out (built separately)
P = np.vstack([D[k] for k in KEYS]); P = P[P[:, 1] > YEND - 20]; print("piese in corp:", " ".join(KEYS))
DY, NS, DX_ = 2.0, 120, 1.0
env = lambda k, d: float(os.environ.get(k, d))
P[:, 0] = np.abs(P[:, 0]); ytip = P[:, 1].max()
ys = np.arange(YEND, ytip, DY); K = len(ys); nb = int(np.ceil(P[:, 0].max() / DX_)) + 1
TOP = np.full((K, nb), np.nan); BOT = TOP.copy(); EDGE = np.full(K, np.nan); XIN = np.full(K, np.nan)
yi = np.round((P[:, 1] - YEND) / DY).astype(int); xi = np.round(P[:, 0] / DX_).astype(int); ok = (yi >= 0) & (yi < K)
for k in range(K):
    m = ok & (yi == k)
    if m.sum() < 5: continue
    q, b = P[m], xi[m]; EDGE[k] = np.percentile(q[:, 0], 99.5)
    h = np.bincount(b, minlength=nb); occ = np.nonzero(h > 3)[0]; XIN[k] = occ[0] * DX_ if len(occ) else 0.0
    order = np.argsort(b); bs, zs = b[order], q[order, 2]; cut = np.r_[0, np.nonzero(np.diff(bs))[0] + 1, len(bs)]
    for a0, a1 in zip(cut[:-1], cut[1:]): TOP[k, bs[a0]] = zs[a0:a1].max(); BOT[k, bs[a0]] = zs[a0:a1].min()
for A_ in (EDGE, XIN):
    g = ~np.isnan(A_); A_[:] = np.interp(np.arange(K), np.nonzero(g)[0], A_[g])
def gs1(z, sg):                                                         # gaussian along a 1-D array, odd reflection ends
    n = int(3 * sg); k = np.exp(-0.5 * (np.arange(-n, n + 1) / sg) ** 2); k /= k.sum()
    if n == 0: return z
    return np.convolve(np.r_[2 * z[0] - z[n:0:-1], z, 2 * z[-1] - z[-2:-n - 2:-1]], k, "valid")
tw = lambda z, sg: 2 * gs1(z, sg) - gs1(gs1(z, sg), sg)
EDGE = tw(EDGE, 4.0); EDGE[-1] = 0.0
YR = env("PUNTE_VARF_R", "120"); j = int(np.argmax(ys >= ytip - YR)); Ej = EDGE[j]; m_ = (EDGE[j + 1] - EDGE[j - 1]) / (2 * DY); Lj = ytip - ys[j]
u_ = float(np.clip(-m_ * Lj / max(Ej + m_ * Lj, 1e-6), 0.0, 0.9)) if Ej + m_ * Lj > 0 else 0.9; b_ = Lj / (1 - u_); a_ = Ej / np.sqrt(1 - u_ ** 2); yc = ytip - b_
EDGE[j:] = a_ * np.sqrt(np.clip(1 - ((ys[j:] - yc) / b_) ** 2, 0, 1)); EDGE[-1] = 0.0; print("varf rotunjit: elipsa %.0f x %.0f m de la y %.0f" % (a_, b_, ys[j]))
# the U: the inner edge is 0 on the deck; from the apex (the last row from the nose back with material at x ~ 0) it opens,
# monotone, smoothed; its apex rounded by the twicing
XIN[XIN < 4] = 0.0; ka = K - 1
while ka > 0 and XIN[ka - 1] == 0: ka -= 1
XIN[ka:] = 0.0; XIN[:ka] = np.maximum.accumulate(XIN[:ka][::-1])[::-1]
XIN[:ka] = np.maximum(tw(XIN, 3.0)[:ka], 0.0); XIN[ka:] = 0.0; YAPEX = ys[ka]
s = np.linspace(0, 1, NS + 1)
def resample(A, x0):                                                    # rows to s between x0 and the edge, gaps interpolated
    out = np.full((K, NS + 1), np.nan)
    for k in range(K):
        xs = x0[k] + s * (EDGE[k] - x0[k]); g = ~np.isnan(A[k]) & (np.arange(nb) * DX_ <= EDGE[k] + 1) & (np.arange(nb) * DX_ >= XIN[k] - 1)
        if g.sum() >= 2: out[k] = np.interp(xs, np.nonzero(g)[0] * DX_, A[k][g])
    for j_ in range(NS + 1):
        g = ~np.isnan(out[:, j_])
        if g.sum() >= 2: out[:, j_] = np.interp(np.arange(K), np.nonzero(g)[0], out[g, j_])
    return out
def smooth2(A, sy, ss): return np.apply_along_axis(lambda z: gs1(z, ss), 1, np.apply_along_axis(lambda z: gs1(z, sy), 0, A))
def run(Z, w, op, axis, fillv):                                         # centred flat max/min filter
    h = w // 2; pad = [(0, 0), (0, 0)]; pad[axis] = (h, h)
    return op(swv(np.pad(Z, pad, constant_values=fillv) if fillv is not None else np.pad(Z, pad, mode="edge"), w, axis=axis), axis=-1)
def closing(A, wx, wy):                                                 # fills dents narrower than the window; mirrored at the
    h = wx // 2; n = A.shape[1]                                         # inner side, nothing (-inf) past the outer edge
    Z = np.concatenate([A[:, h:0:-1], A, np.full((A.shape[0], 2 * h), -np.inf)], 1)
    D_ = run(run(Z, wx, np.max, 1, -np.inf), wy, np.max, 0, None)
    return run(run(D_, wy, np.min, 0, None), wx, np.min, 1, np.inf)[:, h:h + n]
def envelopes(x0):
    WS = lambda m_: max(3, int(m_ / (EDGE.max() / NS)) | 1)
    T_ = closing(resample(TOP, x0), WS(env("PUNTE_GAURI_SUS", "60")), 9)
    B_ = -closing(-resample(BOT, x0), WS(env("PUNTE_GAURI_JOS", "140")), 15)
    SY, SS = env("PUNTE_NET_Y", "30"), env("PUNTE_NET_S", "10")
    G2 = lambda A: smooth2(A, SY, SS); T_ = 2 * G2(T_) - G2(G2(T_)); B_ = 2 * G2(B_) - G2(G2(B_))
    return T_, np.minimum(B_, T_ - 0.5)
# first pass: the half-thickness at the inner side gives the depth of the inner wall's bulge; the second pass starts the
# grid that much further out, so the bulge's tip sits on the inner edge of the reference
T1, B1 = envelopes(XIN); H0 = (T1[:, 0] - B1[:, 0]) / 2
WALL = np.clip(XIN / env("PUNTE_U_RAMPA", "20"), 0, 1)                 # 0 on the deck, 1 once the U is open
DEPTH = WALL * np.minimum(H0, 0.4 * (EDGE - XIN)); X0 = XIN + DEPTH
T_, B_ = envelopes(X0)
MID = (T_ + B_) / 2; H = (T_ - B_) / 2
for k in range(K):                                                      # rounded outer edge: half-ellipse over the last re m
    re = max(H[k, -8:].mean(), 1.0); se = 1 - min(re / max(EDGE[k] - X0[k], 1e-6), 0.5)
    H[k] *= np.where(s > se, np.sqrt(np.clip(1 - ((s - se) / (1 - se)) ** 2, 0, 1)), 1.0)
H[-1] = 0.0; MID[-1] = MID[-1].mean()                                   # the nose closes in one point
np.savez(OUT, ys=ys, s=s, edge=EDGE, x0=X0, depth=DEPTH, xin=XIN, top=MID + H, bot=MID - H, ytip=ytip, yapex=YAPEX)
print("PUNTE: y %.0f..%.0f (%d sectiuni), U deschis de la y %.0f (margine interioara la capat %.0f m), latime max %.0f m, grosime max %.1f m" % (ys[0], ys[-1], K, YAPEX, XIN[0], EDGE.max(), 2 * H.max()))
