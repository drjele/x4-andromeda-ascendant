# Guides for a clear, straight joint 103 <-> PS (asked: the joint line drawn, glued to the PS, 103's inner edges put on it):
# the PS's vertical side wall (its outline at z WALL, right half) fitted with a bent bar seen from above - two straight runs
# and one arc of radius R at the corner (corner height searched for the best fit); the top joint = that bar moved IN_SUS m
# inwards and laid on the PS's upper surface (highest point of the PS's section there), the bottom joint = the bar moved
# IN_JOS m inwards and laid on the PS's underside (lowest point). Writes the two lines (+ the wall fit) in ship coordinates.
# Usage: python linie_imbinare_ghid.py <pieces.npz> <out.npz> [y0 y1] ; env IMB_WALL=300 IMB_R=150 IMB_IN_SUS=15 IMB_IN_JOS=12
import sys, os, numpy as np, trimesh
D = np.load(sys.argv[1]); OUT = sys.argv[2]; Y0, Y1 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (-60.0, 300.0)
WALL = float(os.environ.get("IMB_WALL", "300")); R = float(os.environ.get("IMB_R", "150"))
IS, IJ = float(os.environ.get("IMB_IN_SUS", "15")), float(os.environ.get("IMB_IN_JOS", "12"))
v = D["PS__v"].copy(); v[:, 0] += 1700; m = trimesh.Trimesh(v, D["PS__f"], process=False)
sec = m.section(plane_origin=[0, 0, WALL], plane_normal=[0, 0, 1]); P = np.vstack(list(sec.discrete)); P = P[P[:, 0] > 0]
ys = np.arange(Y0, Y1 + 1, 2.0); wx = np.array([P[np.abs(P[:, 1] - y) < 1.5, 0].max() for y in ys])
def bar(yc):                                            # two least-squares lines (x = a + b y) meeting near yc, joined by an arc
    A, B = ys < yc, ys >= yc
    if A.sum() < 5 or B.sum() < 5: return None
    la = np.polyfit(ys[A], wx[A], 1); lb = np.polyfit(ys[B], wx[B], 1)
    yi = (lb[1] - la[1]) / (la[0] - lb[0]) if la[0] != lb[0] else yc
    p_ = lambda l, y: np.c_[np.polyval(l, y), y]
    Pa, Pb, Pc = p_(la, np.array([Y0]))[0], p_(lb, np.array([Y1]))[0], p_(la, np.array([yi]))[0]
    u1 = (Pa - Pc) / np.linalg.norm(Pa - Pc); u2 = (Pb - Pc) / np.linalg.norm(Pb - Pc); ph = np.arccos(np.clip(u1 @ u2, -1, 1)) / 2
    if not (Y0 < yi < Y1) or ph > np.radians(89.5): L = np.vstack([Pa, Pb])
    else:
        t = R / np.tan(ph); A1, A2 = Pc + u1 * t, Pc + u2 * t; C = Pc + (u1 + u2) / np.linalg.norm(u1 + u2) * R / np.sin(ph)
        b1, b2 = np.arctan2(*(A1 - C)[::-1]), np.arctan2(*(A2 - C)[::-1]); db = np.angle(np.exp(1j * (b2 - b1)))
        L = np.vstack([Pa, A1, C + R * np.c_[np.cos(b1 + np.linspace(0, db, 40)), np.sin(b1 + np.linspace(0, db, 40))], A2, Pb])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]; L = np.c_[[np.interp(np.arange(0, d[-1], 1.0), d, L[:, i]) for i in (0, 1)]].T
    err = wx - np.interp(ys, L[::-1, 1] if L[0, 1] > L[-1, 1] else L[:, 1], L[::-1, 0] if L[0, 1] > L[-1, 1] else L[:, 0])
    return L, np.abs(err).mean(), np.abs(err).max(), yi
best = min((b for b in (bar(yc) for yc in np.arange(Y0 + 20, Y1 - 20, 5.0)) if b), key=lambda b: b[1])
L, em, ex, yi = best
print("PERETE PS la z %.0f: bara indoita (2 drepte + arc R %.0f la y %.0f): abatere medie %.1f m, max %.1f m" % (WALL, R, yi, em, ex))
t = np.gradient(L, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]; nin = np.c_[t[:, 1], -t[:, 0]]
if (nin[:, 0] > 0).mean() > 0.5: nin = -nin                           # inwards = towards the ship's axis (-x on the right half)
out = {"perete": np.c_[L, np.full(len(L), WALL)]}
for key, off, pick in (("imbinare_sus", IS, np.max), ("imbinare_jos", IJ, np.min)):
    Q = L + off * nin; Z = []
    for x, y in Q:
        s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
        S = np.vstack(list(s.discrete)) if s is not None else np.zeros((0, 3)); S = S[np.abs(S[:, 0] - x) < 1.5]
        Z.append(pick(S[:, 2]) if len(S) else np.nan)
    Z = np.array(Z); ok = np.isfinite(Z); Z = np.interp(np.arange(len(Z)), np.where(ok)[0], Z[ok])
    out[key] = np.c_[Q, Z]
    tz = np.degrees(np.arctan(np.abs(np.diff(Z)))); print("%s: %.0f m spre interior, z %.1f..%.1f, panta max %.1f grd/m" % (key, off, Z.min(), Z.max(), tz.max()))
np.savez(OUT, **out); print("SALVAT", OUT)
