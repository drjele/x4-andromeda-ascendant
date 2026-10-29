# Guides for the back arms as ovals starting from the PS's back walls (asked: the arms start from gp_PS's two straight back
# walls, exactly in that shape, and become ovals - widened at the PS, ovals along the whole path, on the same centre line
# as the tubes now). Right arm: the spine = the clean spine of ghid_brat (offsets taken off); section 0 = the right back
# wall's outline (gp_PS cut at the plane YW, just inside the back edge's rounding: the wall's own closed loop); then every PAS m a section across
# the spine (parallel-transport frame, width axis horizontal at the PS) blending (quintic, over LT m) from the wall shape
# (and its centre) to an ellipse WxH on the spine; ellipses on to the end. Left = mirror.
# Usage: python ghid_brat_oval.py <ghid_brat npz> <ps npz (gp_PS__v/__f, ship coords)> <out.npz> ; env W=90 H=58 LT=150 PAS=25 OFF=80,-120,0 YW=-52 XN=-1e9
import sys, os, numpy as np, trimesh
G = np.load(sys.argv[1]); PSn = np.load(sys.argv[2]); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d))
W_, H_, LT, PAS, YW, XN = e("W", "90"), e("H", "58"), e("LT", "150"), e("PAS", "25"), e("YW", "-52"), e("XN", "-1e9")
off = np.array([float(q) for q in os.environ.get("OFF", "80,-120,0").split(",")])
C = G["spinare_brat_D"] - off; dC = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
TG = np.gradient(C, axis=0); TG /= np.linalg.norm(TG, axis=1)[:, None]
e1 = np.cross(TG[0], [0, 0, 1.0]); e1 /= np.linalg.norm(e1); F1 = [e1]
for i in range(1, len(C)):
    a = F1[-1] - (F1[-1] @ TG[i]) * TG[i]; F1.append(a / np.linalg.norm(a))
F1 = np.array(F1); F2 = np.cross(TG, F1)
if F1[0, 0] < 0: F1, F2 = -F1, -F2                                       # width axis pointing outwards (+x) at the PS
if F2[0, 2] < 0: F2 = -F2
t = trimesh.Trimesh(PSn["gp_PS__v"], PSn["gp_PS__f"], process=False)
sec = t.section(plane_origin=[0, YW, 0], plane_normal=[0, 1, 0]); L = max((q for q in sec.discrete if q[:, 0].mean() > 0), key=len)   # the right wall's own loop
L = L[L[:, 0] >= XN]; c0 = np.array([(L[:, 0].min() + L[:, 0].max()) / 2, YW, (L[:, 2].min() + L[:, 2].max()) / 2])
NA = 96; th = np.linspace(0, 2 * np.pi, NA, endpoint=False)
ang = np.arctan2(L[:, 2] - c0[2], L[:, 0] - c0[0]); o_ = np.argsort(ang); A_, Pw = ang[o_], L[o_]
def ray_wall(a):                                                           # the wall outline's radius at angle a (closed straight at XN)
    d = np.array([np.cos(a), np.sin(a)]); best = None
    seg = list(zip(Pw[:-1], Pw[1:])) + [(Pw[-1], Pw[0])]
    for p, q in seg:
        P = np.array([p[0] - c0[0], p[2] - c0[2]]); Q = np.array([q[0] - c0[0], q[2] - c0[2]]); M = np.c_[d, P - Q]
        if abs(np.linalg.det(M)) < 1e-9: continue
        s_, u_ = np.linalg.solve(M, P)
        if s_ > 0 and -1e-6 <= u_ <= 1 + 1e-6 and (best is None or s_ < best): best = s_
    return best
Rw = np.array([ray_wall(a) for a in th])
Re = 1 / np.sqrt((np.cos(th) / (W_ / 2)) ** 2 + (np.sin(th) / (H_ / 2)) ** 2)
ease = lambda x: x ** 3 * (x * (6 * x - 15) + 10)
j0 = int(np.argmin(np.abs(C[:, 1] - YW)))                                  # the spine where it leaves the wall plane
cs = np.array([C[j0] @ F1[j0], C[j0] @ F2[j0]]); cw = np.array([c0 @ F1[j0], c0 @ F2[j0]]); dcen = cw - cs   # wall centre vs spine
out = {"spinare_brat_D": C[j0:]}
k = 0; svals = list(np.arange(0, LT, PAS)) + list(np.arange(LT, dC[-1] - dC[j0], 2 * PAS))
for s in svals:
    j = min(int(np.searchsorted(dC, dC[j0] + s)), len(C) - 1); w = ease(min(s / LT, 1.0))
    R = (1 - w) * Rw + w * Re; dc = (1 - w) * dcen
    xy = np.c_[R * np.cos(th), R * np.sin(th)] + dc
    if s == 0: Q = np.c_[c0[0] + Rw * np.cos(th), np.full(NA, YW), c0[2] + Rw * np.sin(th)]   # section 0: the wall itself
    else: Q = C[j] + np.outer(xy[:, 0], F1[j]) + np.outer(xy[:, 1], F2[j])
    out["sectiune_brat_D_%02d" % k] = np.vstack([Q, Q[:1]]); k += 1
for kk in list(out): out[kk.replace("_D", "_S")] = out[kk] * [-1, 1, 1]
print("BRAT OVAL: perete PS x %.0f..%.0f z %.0f..%.0f (centru %.0f, %.0f; %.0f x %.0f m) -> oval %.0f x %.0f in %.0f m, apoi oval pe toata spinarea (%.0f m); %d sectiuni pe brat; centrul peretelui fata de spinare %.1f, %.1f m" % (
    L[:, 0].min(), L[:, 0].max(), L[:, 2].min(), L[:, 2].max(), c0[0], c0[2], L[:, 0].max() - L[:, 0].min(), L[:, 2].max() - L[:, 2].min(), W_, H_, LT, dC[-1] - dC[j0], k, *dcen))
np.savez(OUT, **out)
