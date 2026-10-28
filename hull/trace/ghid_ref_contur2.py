# Reference guide lines for 169_C, second pass (asked: centred on the reference, the arms' lines longer, straight, placed so
# they cut the reference arms as little as possible): the reference outline seen from above, measured from its own middle
# (x ~ -4.7, both sides pooled). Each arm line = a SUPPORT line: for every slope, pushed until it only touches the arm's edge
# from outside (outer line: beyond the outer edge; inner line: inside the gap between the arms), allowing 1 % of the edge
# points past it; the slope with the line closest to the edge on average is kept. The nose: the best 2-segment polyline of
# the outline in front; corners rounded by one arc each (radius fitted to the outline); the inner lines meet on the axis
# in one arc (the U). Writes both lines (x, y) in reference coordinates.
# Usage: python ghid_ref_contur2.py <esantion_punte.npz> <out.npz>
import sys, os, numpy as np, cv2
D = np.load(sys.argv[1]); OUT = sys.argv[2]; env = lambda k, d: float(os.environ.get(k, d))
YLOW, YU, YN, XMX, Q_ = env("GHID_Y_JOS", "-850"), env("GHID_Y_U", "-30"), env("GHID_Y_NAS", "250"), env("GHID_XMAX", "400"), env("GHID_TOL", "0.01")
P = D["ps"]; P = P[P[:, 1] > YLOW - 5]
rows = np.round(P[:, 1]).astype(int); cen = np.median([(P[rows == r, 0].min() + P[rows == r, 0].max()) / 2 for r in range(int(YLOW), 470, 10) if (rows == r).sum() > 20 and np.abs(P[rows == r, 0]).max() < XMX])
X = np.abs(P[:, 0] - cen); PX = 1.0; y0 = YLOW - 5; W, H = int(X.max() / PX) + 10, int((P[:, 1].max() - y0) / PX) + 10
m = np.zeros((H, W), np.uint8); m[((P[:, 1] - y0) / PX).astype(int), (X / PX).astype(int)] = 1
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
ext, inn = [], []
for r in range(H):
    xs = np.nonzero(m[r])[0] * PX; y = y0 + r * PX; xs = xs[xs < XMX]
    if len(xs) < 3 or y < YLOW: continue
    ext.append((xs.max(), y))
    if xs.min() > 4 and y < YU: inn.append((xs.min(), y))
ext, inn = np.array(ext), np.array(inn)
def support(Q, outside):                                               # x = a + b y touching the edge from outside / inside
    best = None
    for b in np.linspace(-0.6, 0.6, 1201):
        r_ = Q[:, 0] - b * Q[:, 1]; a = np.quantile(r_, 1 - Q_) if outside else np.quantile(r_, Q_)
        cost = np.mean(np.abs(a + b * Q[:, 1] - Q[:, 0]))
        if best is None or cost < best[0]: best = (cost, a, b)
    return best
side = ext[ext[:, 1] < YN]; ce, ae, be = support(side, True)                # the long straight side (arm -> nose)
nose = ext[ext[:, 1] >= YN]
def polyfit(Q, ns):
    n = len(Q); E = np.full((n, n), np.inf)
    for i in range(n):
        for j in range(i + 1, n):
            d = Q[j] - Q[i]; L = np.linalg.norm(d); w = Q[i + 1:j] - Q[i]; E[i, j] = float(np.sum((w[:, 0] * d[1] - w[:, 1] * d[0]) ** 2) / max(L, 1e-9) ** 2)
    best = np.full((ns + 1, n), np.inf); arg = np.zeros((ns + 1, n), int); best[0, 0] = 0
    for s in range(1, ns + 1):
        for j in range(1, n):
            c = best[s - 1, :j] + E[:j, j]; i = int(np.argmin(c)); best[s, j], arg[s, j] = c[i], i
    idx = [n - 1]
    for s in range(ns, 0, -1): idx.append(arg[s, idx[-1]])
    return idx[::-1]
nz = nose[::2]; ix = polyfit(nz, 2)
def lfit(S): c = S.mean(0); return c, np.linalg.svd(S - c)[2][0]
LN = [lfit(nz[a:b + 1]) for a, b in zip(ix[:-1], ix[1:])]
def meet(l1, l2):
    (c1, u1), (c2, u2) = l1, l2; t = np.linalg.lstsq(np.array([u1, -u2]).T, c2 - c1, rcond=None)[0]; return c1 + u1 * t[0]
LS = (np.array([ae + be * 0.0, 0.0]), np.array([be, 1.0]) / np.hypot(be, 1.0))
A0 = np.array([ae + be * YLOW, YLOW]); C1 = meet(LS, LN[0]); C2 = meet(LN[0], LN[1]); mir = (LN[1][0] * [-1, 1], LN[1][1] * [-1, 1]); C3 = meet(LN[1], mir); C3[0] = 0.0
def arc(P0, C, P1, Qref, rmax):
    u1, u2 = (P0 - C) / np.linalg.norm(P0 - C), (P1 - C) / np.linalg.norm(P1 - C); ang = np.arccos(np.clip(u1 @ u2, -1, 1)); best = None
    for r in np.linspace(2, rmax, 100):
        dt = r / np.tan(ang / 2)
        if dt > 0.9 * min(np.linalg.norm(P0 - C), np.linalg.norm(P1 - C)): break
        t1, t2 = C + u1 * dt, C + u2 * dt; cc = C + (u1 + u2) / np.linalg.norm(u1 + u2) * r / np.sin(ang / 2)
        dq = np.linalg.norm(Qref - C, axis=1); nr = Qref[dq < max(dt * 1.3, dq.min() + 10)]   # the corner may sit off the outline
        if len(nr) < 3: continue
        e = np.mean((np.linalg.norm(nr - cc, axis=1) - r) ** 2)
        if best is None or e < best[0]: best = (e, r, t1, t2, cc)
    _, r, t1, t2, cc = best; a1, a2 = np.arctan2(*(t1 - cc)[::-1]), np.arctan2(*(t2 - cc)[::-1])
    if a2 - a1 > np.pi: a2 -= 2 * np.pi
    if a1 - a2 > np.pi: a2 += 2 * np.pi
    return r, np.array([cc + r * np.array([np.cos(a), np.sin(a)]) for a in np.linspace(a1, a2, 24)])
print("DBG A0 %s C1 %s C2 %s C3 %s latura x=%.1f%+.3fy" % (A0.round(1), C1.round(1), C2.round(1), C3.round(1), ae, be))
r1, a1 = arc(A0, C1, C2, ext, 150); r2, a2 = arc(C1, C2, C3, ext, 150); r3, a3 = arc(C2, C3, C2 * [-1, 1], ext, 80)
right = np.vstack([[A0], a1, a2, a3[: len(a3) // 2 + 1]]); right[-1, 0] = 0.0
outer = np.vstack([right * [-1, 1], right[::-1][1:]])
ci, ai, bi = support(inn, False)
LI = (np.array([ai, 0.0]), np.array([bi, 1.0]) / np.hypot(bi, 1.0)); U = meet(LI, (LI[0] * [-1, 1], LI[1] * [-1, 1])); U[0] = 0.0
E0 = np.array([ai + bi * YLOW, YLOW]); ru, au = arc(E0, U, E0 * [-1, 1], inn, 120)
inner = np.vstack([[E0 * [-1, 1]], au[::-1] if au[0, 0] > 0 else au, [E0]])
outer[:, 0] += cen; inner[:, 0] += cen
np.savez(OUT, outer=outer, inner=inner, centru=cen)
print("CENTRU referinta x %.1f" % cen)
print("EXTERIOR: latura dreapta x = %.1f %+.3f*y (abatere medie fata de margine %.1f m), colturi la y %.0f / %.0f / varf %.0f, arce R %.0f / %.0f / %.0f" % (ae, be, ce, C1[1], C2[1], C3[1], r1, r2, r3))
print("INTERIOR: drepte x = +-(%.1f %+.3f*y) (abatere medie %.1f m), U la y %.0f cu arc R %.0f, capete la y %.0f (x +-%.0f)" % (ai, bi, ci, U[1], ru, YLOW, E0[0]))
