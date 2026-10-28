# Flat guide line for the body 169_C (asked: in one plane, as close as possible to the reference outline, only smooth and
# made symmetric): the reference seen from above (raster 1 m, small gaps closed), averaged with its mirror about its own
# middle (symmetric), the outer contour (nose, sides, arms, loops, the gap between the arms), resampled every 1 m, then
# smoothed along itself (periodic gaussian with twicing: keeps the size, removes the small steps) and made exactly
# symmetric (averaged with its mirrored, reversed copy). Several smoothing strengths; for each: distance to the raw
# outline (mean / 95 % / max), smallest radius of curvature, largest turn per 2 m. Coordinates centred (middle at x = 0).
# Usage: python ghid_plan.py <esantion_punte.npz> <out_prefix> [sigma ...]   -> <out_prefix>_s<sigma>.npz + .png
import sys, numpy as np, cv2
D = np.load(sys.argv[1]); PRE = sys.argv[2]; SIG = [float(v) for v in sys.argv[3:]] or [3.0, 6.0, 12.0]
P = D["ps"][:, :2]
rows = np.round(D["ps"][:, 1] / 10).astype(int); cs = []
for r in np.unique(rows):
    q = P[rows == r]; q = q[np.abs(q[:, 0]) < 200]
    if len(q) > 20 and q[:, 1].mean() > -400: cs.append((q[:, 0].min() + q[:, 0].max()) / 2)
cen = float(np.median(cs)); P = P - [cen, 0]
PX = 1.0; XM, Y0, Y1 = np.abs(P[:, 0]).max() + 20, P[:, 1].min() - 20, P[:, 1].max() + 20
W, H = int(2 * XM / PX), int((Y1 - Y0) / PX)
m = np.zeros((H, W), np.float32); m[((P[:, 1] - Y0) / PX).astype(int), ((P[:, 0] + XM) / PX).astype(int)] = 1
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
m = (cv2.GaussianBlur((m + m[:, ::-1]) / 2, (0, 0), 1.5) > 0.5).astype(np.uint8)   # averaged with the mirror
m0 = m.copy()
import os                                                              # steps between the deck's pieces and the gap notch in
CL, OP = float(os.environ.get("GHID_INCHIDERE", "0")), float(os.environ.get("GHID_DESCHIDERE", "0"))   # the loops: closed
if CL > 0: m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(CL / PX) | 1,) * 2))   # (filled),
if OP > 0: m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(OP / PX) | 1,) * 2))    # opened (cut)
cnt = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0].astype(float)
raw = np.stack([cnt[:, 0] * PX - XM, cnt[:, 1] * PX + Y0], 1)
def resample(Q, step):
    Qc = np.vstack([Q, Q[:1]]); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Qc, axis=0), axis=1))]; n = int(s[-1] / step)
    u = np.linspace(0, s[-1], n, endpoint=False); return np.stack([np.interp(u, s, Qc[:, i]) for i in range(2)], 1)
c0 = max(cv2.findContours(m0, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0].astype(float)
ref = np.stack([c0[:, 0] * PX - XM, c0[:, 1] * PX + Y0], 1)            # the reference outline before closing / opening
raw = resample(raw, 1.0); raw = np.roll(raw, -int(np.argmax(raw[:, 1] - 1e3 * np.abs(raw[:, 0]))), axis=0)   # start at the nose tip
def gp(Q, s):                                                          # periodic gaussian
    n = int(4 * s); k = np.exp(-0.5 * (np.arange(-n, n + 1) / s) ** 2); k /= k.sum()
    Z = np.vstack([Q[-n:], Q, Q[:n]]); return np.stack([np.convolve(Z[:, i], k, "valid") for i in range(2)], 1)
def sym(Q):                                                            # average with the mirrored, reversed copy (same start)
    M_ = np.vstack([Q[:1], Q[1:][::-1]]) * [-1, 1]; S = (Q + M_) / 2; S[0, 0] = 0.0; return S
def stats(Q):
    from scipy.spatial import cKDTree
    d = cKDTree(resample(Q, 0.25)).query(ref)[0]
    Qr = resample(Q, 2.0); t = np.diff(np.vstack([Qr, Qr[:1]]), axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
    turn = np.degrees(np.arccos(np.clip(np.sum(t * np.roll(t, 1, 0), 1), -1, 1)))
    rad = 2.0 / np.maximum(np.radians(turn), 1e-9)
    return d.mean(), np.percentile(d, 95), d.max(), rad.min(), turn.max()
out = []
for sg in SIG:
    S = sym(2 * gp(raw, sg) - gp(gp(raw, sg), sg)); S = resample(S, 1.0); S = sym(np.roll(S, -int(np.argmax(S[:, 1] - 1e3 * np.abs(S[:, 0]))), axis=0))
    st = stats(S); np.savez("%s_s%g.npz" % (PRE, sg), contur=S, centru=cen, brut=raw)
    print("VARIANTA sigma %4.1f m: abatere fata de referinta medie %.2f / 95%% %.2f / max %.2f m; raza minima %.1f m; cea mai mare intoarcere %.1f grade la 2 m" % ((sg,) + st))
    sc = 0.5; im = np.full((int((Y1 - Y0) * sc) + 20, int(2 * XM * sc) + 20, 3), 255, np.uint8)
    f = lambda Q: np.stack([(Q[:, 0] + XM) * sc + 10, (Y1 - Q[:, 1]) * sc + 10], 1).astype(np.int32)
    im[(Y1 - P[::7, 1]).astype(int) * 0 + ((Y1 - P[::7, 1]) * sc + 10).astype(int), ((P[::7, 0] + XM) * sc + 10).astype(int)] = (190, 190, 190)
    cv2.polylines(im, [f(ref)], True, (0, 0, 220), 1); cv2.polylines(im, [f(S)], True, (0, 0, 0), 1)
    cv2.imwrite("%s_s%g.png" % (PRE, sg), im)
print("CENTRU referinta x %.2f" % cen)
