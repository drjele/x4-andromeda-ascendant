# The arms' guides from PS down round the loops to their tips, by the line rules (straight runs, one arc where they meet,
# no traced wobble): a centre line seen from above = the arm's straight middle (between the confirmed outer and inner
# lines, continued straight), ONE arc at the loop's bottom (radius fitted to the reference tube's middle there), the far
# branch's straight middle (fitted to the reference tube), ended so its half-round tip reaches the reference's tip. The
# guides = that line +- half the arms' constant width, eased from the confirmed lines (funnel near PS) between Y0 and Y1;
# the tip a half circle. Right side (x > 0), mirrored on write. Writes B / B_int (whole, flat), the centre line, a sheet.
# Usage: python ghid_bucla.py <ghid_drept3.npz> <elipse_ghidaje.npz> <tub_corp.npz> <out.npz> [png] [ref outline g2_t1.npz]
import sys, numpy as np, cv2
G = np.load(sys.argv[1]); RL = np.load(sys.argv[2]); TB = np.load(sys.argv[3]); OUT = sys.argv[4]; PNG = sys.argv[5] if len(sys.argv) > 5 else None
Y0, Y1, TIPY = -150.0, -450.0, -427.0
ex, ix = RL["br_ext"], RL["br_int"]; W = float(np.median((ex[:, 0] - ix[:, 0])[ex[:, 1] < -700]))   # the arms' constant width
m = (ex[:, 1] < Y1 + 50); mid = np.stack([(ex[m, 0] + ix[m, 0]) / 2, ex[m, 1]], 1)
def fitline(P):                                                        # least squares line: point + unit direction
    c = P.mean(0); d = np.linalg.svd(P - c)[2][0]; return c, d
ca, da = fitline(mid); da = da if da[1] < 0 else -da                     # the arm's middle, going down
C = TB["C"][:, :2] * [-1, 1]; kb = int(np.argmin(C[:, 1]))              # the reference tube's middle (right side), its bottom
far = C[kb:][(C[kb:, 1] > -1150) & (C[kb:, 1] < -560)]; cf, df = fitline(far); df = df if df[1] > 0 else -df   # far branch, going up
def meet(c1, d1, c2, d2):
    t = np.linalg.lstsq(np.array([d1, -d2]).T, c2 - c1, rcond=None)[0]; return c1 + d1 * t[0]
V = meet(ca, da, cf, df)                                               # the corner (below the loop)
u1, u2 = -da, df; ang = np.arccos(np.clip(u1 @ u2, -1, 1)); bis = (u1 + u2) / np.linalg.norm(u1 + u2)
near = C[max(kb - 60, 0):kb + 60]; best = None
for R in np.linspace(20, 300, 281):                                    # the arc's radius fitted to the reference tube's bottom
    dt = R / np.tan(ang / 2); cc = V + bis * R / np.sin(ang / 2); e = np.mean((np.linalg.norm(near - cc, axis=1) - R) ** 2)
    if best is None or e < best[0]: best = (e, R)
R = best[1]; dt = R / np.tan(ang / 2); t1, t2 = V + u1 * dt, V + u2 * dt; cc = V + bis * R / np.sin(ang / 2)
a1, a2 = np.arctan2(*(t1 - cc)[::-1]), np.arctan2(*(t2 - cc)[::-1])
if a2 - a1 > np.pi: a2 -= 2 * np.pi
if a1 - a2 > np.pi: a2 += 2 * np.pi
end = cf + df * ((TIPY - W / 2 - cf[1]) / df[1])                        # the far branch ends so its half-round tip reaches TIPY
def seg(p, q, step=2.0): n = max(int(np.linalg.norm(q - p) / step), 1); return p + np.outer(np.arange(n) / n, q - p)
start = ca + da * ((Y0 - ca[1]) / da[1])
cl = np.vstack([seg(start, t1), np.array([cc + R * np.array([np.cos(a), np.sin(a)]) for a in np.linspace(a1, a2, max(int(R * abs(a2 - a1) / 2), 8), endpoint=False)]), seg(t2, end), [end]])
tg = np.gradient(cl, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]; nr = np.stack([tg[:, 1], -tg[:, 0]], 1)   # right of the way down = outside
if (nr[0] @ [1, 0]) < 0: nr = -nr
def sil(Q, y):                                                         # the confirmed line's x at height y (right side)
    Rr = Q[Q[:, 0] >= 0]; Rr = Rr[np.argsort(Rr[:, 1])]; return np.interp(y, Rr[:, 1], Rr[:, 0])
uu = np.clip((Y0 - cl[:, 1]) / (Y0 - Y1), 0, 1); uu = np.where(np.arange(len(cl)) > np.argmin(cl[:, 1]), 1.0, uu * uu * (3 - 2 * uu))
oe = cl + nr * W / 2; ie = cl - nr * W / 2
so = np.stack([sil(G["B"], cl[:, 1]), cl[:, 1]], 1); si = np.stack([sil(G["B_int"], cl[:, 1]), cl[:, 1]], 1)   # whole points eased
oe = (1 - uu)[:, None] * so + uu[:, None] * oe; ie = (1 - uu)[:, None] * si + uu[:, None] * ie                       # (x and y)
cap = np.array([end + W / 2 * (np.cos(a) * nr[-1] + np.sin(a) * tg[-1]) for a in np.linspace(0, np.pi, 41)])   # tip half circle (forward)
Bo = G["B"][G["B"][:, 0] >= 0]; Bo = Bo[np.argsort(-Bo[:, 1])]; Bo = Bo[Bo[:, 1] > Y0]
Bi = G["B_int"][G["B_int"][:, 0] >= 0]; Bi = Bi[np.argsort(-Bi[:, 1])]; Bi = Bi[Bi[:, 1] > Y0]
outer = np.vstack([Bo, oe, cap[1:21]]); inner = np.vstack([Bi, ie, cap[20:-1][::-1]])
def turn(Q):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]; u = np.arange(0, s[-1], 2.0); P = np.stack([np.interp(u, s, Q[:, i]) for i in range(2)], 1)
    d = np.diff(P, axis=0); d /= np.maximum(np.linalg.norm(d, axis=1), 1e-9)[:, None]; return np.degrees(np.arccos(np.clip(np.sum(d[1:] * d[:-1], 1), -1, 1))).max()
mir = lambda H: np.vstack([(H * [-1, 1])[::-1], H[1:]])
np.savez(OUT, B=mir(outer), B_int=mir(inner), centru_bucla=cl, latime=W, raza=R)
print("BUCLA: latime %.1f m; brat x = %.1f %+.3f*(y...) dir (%.3f, %.3f); ramura (%.3f, %.3f); arc R %.0f la fund (%.0f, %.0f); capat (%.0f, %.0f) + semicerc; intoarcere max ghidaj exterior %.1f, interior %.1f grade la 2 m" % (
    W, ca[0], 0, *da, *df, R, *cc, *end, turn(outer), turn(inner)))
if PNG:
    sc = 0.5; im = np.full((int(1900 * sc) + 20, int(1300 * sc) + 20, 3), 255, np.uint8)
    f = lambda Q: np.stack([(Q[:, 0] + 650) * sc + 10, (500 - Q[:, 1]) * sc + 10], 1).astype(np.int32)
    if len(sys.argv) > 6: cv2.polylines(im, [f(np.load(sys.argv[6])["contur"])], True, (190, 190, 190), 1)
    for Q, c in ((mir(outer), (0, 0, 220)), (mir(inner), (220, 80, 0)), (cl, (0, 150, 0)), (cl * [-1, 1], (0, 150, 0))): cv2.polylines(im, [f(Q)], False, c, 2)
    cv2.imwrite(PNG, im)
