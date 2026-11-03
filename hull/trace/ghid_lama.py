# Clean guides for the red blade Circle.007 (asked: new animated blades equivalent to Circle.007 / lame_rosu - first only this pair,
# folding by rotation from the root next to PS into the front arm; guides first, then the piece). In the blade's own plane (fitted
# to the reference's S half): the centre line = a circle arc continued by a tangent straight line to the tip (fitted to the
# reference's skeleton); the width = constant W0 along the arc, then falling linearly to 0 at the tip along the straight part;
# so each edge is a concentric arc + a straight line (clean lines). The root end = a straight cut at the reference's angle.
# Writes guides (ship coords, S side; D = mirror): margine_exterioara, margine_interioara, mijloc, contur (closed outline),
# sectiune_NN (straight cross lines every PAS m), balama (the hinge axis: through the root centre along the plane normal);
# the plane frame and the fitted parameters go to <out>_param.npz.
# Usage: python ghid_lama.py <c7_plan.npz> <out.npz> ; env PAS=60 TH=8
import sys, os, numpy as np
from scipy.optimize import minimize
Z = np.load(sys.argv[1]); OUT = sys.argv[2]; PAS, TH = float(os.environ.get("PAS", 60)), float(os.environ.get("TH", 8))
c, e1, e2, n = Z["c"], Z["e1"], Z["e2"], Z["n"]; C = Z["contur"]; K = Z["skel"]; KW = Z["skel_w"]
K = K[K[:, 0] > -185]                                                   # skeleton without the root fork
def curve(p, s):                                                          # arc (centre cx, cy, radius R, from angle a0 to a1, clockwise) + tangent line of length Lt
    cx, cy, R, a0, a1, Lt = p
    out = []
    for t in s:
        La = R * (a0 - a1)
        if t <= La: a = a0 - t / R; out.append((cx + R * np.cos(a), cy + R * np.sin(a)))
        else:
            a = a1; px, py = cx + R * np.cos(a), cy + R * np.sin(a); dx, dy = np.sin(a), -np.cos(a); u = t - La; out.append((px + dx * u, py + dy * u))
    return np.array(out)
def length(p): return p[2] * (p[3] - p[4]) + p[5]
def cost(p):
    if p[2] < 50 or p[3] <= p[4] or p[5] < 10: return 1e12
    Q = curve(p, np.linspace(0, length(p), 600)); d = np.min(np.linalg.norm(K[:, None, :] - Q[None, ::2, :], axis=2), axis=1)
    tip = np.linalg.norm(Q[-1] - C[np.argmax(C[:, 0])]); root = np.min(np.linalg.norm(K - Q[0], axis=1))
    return np.mean(d ** 2) + .05 * tip ** 2 + .05 * root ** 2
best = None
for R0 in (120, 180, 260):
    for cy0 in (-150, -100, -50):
        p0 = np.array([20, cy0, R0, np.pi - .2, .3, 250.0]); r = minimize(cost, p0, method="Nelder-Mead", options={"maxiter": 6000, "xatol": 1e-3, "fatol": 1e-4})
        if best is None or r.fun < best.fun: best = r
p = best.x; L = length(p); La = p[2] * (p[3] - p[4])
s = np.arange(0, L + .01, .5); Mid = curve(p, s)
dk = np.min(np.linalg.norm(K[:, None, :] - Mid[None, ::2, :], axis=2), axis=1)
print("MIJLOC: arc R %.1f (%.0f m) + dreapta tangenta %.0f m; schelet fata de linie medie %.2f, max %.2f m" % (p[2], La, p[5], dk.mean(), dk.max()))
# width from the reference outline, per station
T = np.gradient(Mid, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]; Nn = np.c_[-T[:, 1], T[:, 0]]
def half(i, sg):
    q = Mid[i]; v = sg * Nn[i]; d = C - q; along = d @ T[i]; m = np.abs(along) < 1.0
    if not m.any(): return np.nan
    w = d[m] @ v; w = w[w > 0]; return w.min() if len(w) else np.nan
wo = np.array([half(i, 1) for i in range(len(s))]); wi = np.array([half(i, -1) for i in range(len(s))])
W = wo + wi; ok = ~np.isnan(W) & (s > 30) & (s < La)
W0 = float(np.median(W[ok])); off = float(np.median(((wo - wi) / 2)[ok]))
print("LATIME pe arc: mediana %.1f m (min %.1f max %.1f), decalaj fata de mijloc %.2f m" % (W0, np.nanmin(W[ok]), np.nanmax(W[ok]), off))
w = np.where(s <= La, W0, W0 * np.clip((L - s) / (L - La), 0, 1))
Eo = Mid + Nn * (w / 2)[:, None]; Ei = Mid - Nn * (w / 2)[:, None]
dco = np.array([np.min(np.linalg.norm(C - q, axis=1)) for q in np.r_[Eo[s > 20], Ei[s > 20]]])
print("MARGINI fata de conturul referintei: medie %.2f, max %.2f m (fara radacina)" % (dco.mean(), dco.max()))
# root cut: the reference's root end - straight line through the root corners of the outline
r0 = Mid[0]; cut_dir = Nn[0]
to3 = lambda Q2, h=0.0: c + np.outer(Q2[:, 0], e1) + np.outer(Q2[:, 1], e2) + h * n
G = {"mijloc": to3(Mid), "margine_exterioara": to3(Eo), "margine_interioara": to3(Ei), "contur": to3(np.r_[Ei[:1], Eo, Ei[::-1]]),
     "taietura_radacina": to3(np.r_[Ei[:1], Eo[:1]])}
for k, sk in enumerate(np.arange(PAS, L - 5, PAS)):
    i = int(np.argmin(np.abs(s - sk))); G["sectiune_%02d" % k] = to3(np.r_[Ei[i:i + 1], Eo[i:i + 1]])
G["balama"] = np.r_[to3(Mid[:1], -TH * 2), to3(Mid[:1], TH * 2)]
for k in list(G): G[k + "_D"] = G[k] * [-1, 1, 1]
np.savez(OUT, **{("lama_" + k if not k.endswith("_D") else "lama_" + k[:-2] + "_D"): v for k, v in G.items()})
np.savez(OUT.replace(".npz", "_param.npz"), plan_c=c, plan_e1=e1, plan_e2=e2, plan_n=n, param=p, W0=W0, L=L)   # (only polylines in OUT: ghidaje_npz_draw.py draws every array)
print("GHIDAJE lama: lungime %.0f m, latime %.1f m, grosime (piesa) %.0f m; radacina la %s (nava), balama dupa normala planului %s" % (L, W0, TH, np.round(to3(Mid[:1])[0], 1), np.round(n, 3)))
