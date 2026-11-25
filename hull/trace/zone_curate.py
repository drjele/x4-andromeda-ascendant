# The confirmed zones as clean components of the correlated, decoration-free model (moreno Cube + its arms and legs, PI from grannyte):
# every border is one smooth surface and each triangle is cut exactly on it (no jagged borders), S half mirrored. Borders:
#  BJ | AI    across the wing plate (perpendicular to it), straight from u 515 (y >= 0) to 485 (y = -450)
#  AI | CORP  plane through the section corners (a 190, z -70) .. (a 225, z 150), bent outwards by a tangent round at both ends
#  etaj       above z 50, ahead of y 70 above the fore deck (slope 0.065)
#  H          the recess between hull and wing: box cut by planes, below the wing's top skin, above the lower lip
#  PS | BS    y = -55 (as the confirmed pieces); BS | BJ the plane of the loop's aft end (T3)
# Usage: python zone_curate.py <dir with npz>  -> zone_curate.npz (T, zone)
import sys, numpy as np
D = sys.argv[1]
def load(f, hull=None):
    d = np.load(f"{D}/{f}.npz"); t = d["t"]; n = list(d["n"])
    if hull is not None: t = t[np.isin(d["o"], [n.index(h) for h in hull])]
    return d["v"][t]
def subdiv(T, e):
    while True:
        l = np.linalg.norm(T - np.roll(T, -1, 1), axis=2); k = l.max(1) > e
        if not k.any(): return T
        B, i = T[k], l[k].argmax(1); r = np.arange(len(B)); a, b, c = B[r, i], B[r, (i + 1) % 3], B[r, (i + 2) % 3]; m = (a + b) / 2
        T = np.concatenate([T[~k], np.stack([a, m, c], 1), np.stack([m, b, c], 1)])
def clip(T, f):                                                             # (part with f < 0, part with f >= 0), cut where f = 0
    if not len(T): return T, T
    s = f(T.reshape(-1, 3)).reshape(-1, 3); s = np.where(np.abs(s) < 1e-6, 1e-6, s); n, p = [T[(s < 0).all(1)]], [T[(s >= 0).all(1)]]
    k = ((s < 0).any(1)) & ((s >= 0).any(1)); B, q = T[k], s[k]
    for i in range(3):
        for sg, one, two in ((1, p, n), (-1, n, p)):                        # vertex i alone on its side
            g = (q[:, i] * sg > 0) & (q[:, (i + 1) % 3] * sg < 0) & (q[:, (i + 2) % 3] * sg < 0)
            if not g.any(): continue
            a, b, c = B[g, i], B[g, (i + 1) % 3], B[g, (i + 2) % 3]; w = q[g]; sa, sb, sc = w[:, i], w[:, (i + 1) % 3], w[:, (i + 2) % 3]
            ab = a + (b - a) * (sa / (sa - sb))[:, None]; ac = a + (c - a) * (sa / (sa - sc))[:, None]
            one.append(np.stack([a, ab, ac], 1)); two += [np.stack([ab, b, c], 1), np.stack([ab, c, ac], 1)]
    return np.concatenate(n), np.concatenate(p)
def keep(T, *fs):                                                           # intersection of f >= 0; returns (inside, the rest)
    rest = []
    for f in fs: o, T = clip(T, f); rest.append(o)
    return T, np.concatenate(rest)
def halfS(T): return clip(T, lambda p: -p[:, 0])[1]
soft = lambda x, r: r * np.logaddexp(0, x / r)                              # straight -> tangent round -> straight
a = lambda p: -p[:, 0]; y = lambda p: p[:, 1]; z = lambda p: p[:, 2]
u = lambda p: .77 * a(p) - .64 * z(p)
f_bj = lambda p: np.minimum(u(p) - (500 + 15 * np.clip((y(p) + 225) / 225, -1, 1) - np.maximum(y(p) - 130, 0)), a(p) - 300)                    # never the hull (|x| < 300)
g = lambda p: np.minimum(soft((y(p) + 160) * 2.6, 22) + soft((-430 - y(p)) * 1.0, 22), 235)
f_ai = lambda p: a(p) - (190 + 35 * (z(p) + 70) / 220) - g(p)
f_et = lambda p: z(p) - (50 - .065 * soft(y(p) - 70, 25))
Z = {}
C = subdiv(halfS(load("moreno_v17_al", ["Cube"])), 12)
C, Z["BJ"] = clip(C, f_bj)
H, C = keep(C, lambda p: a(p) - 222, lambda p: 428 - a(p), lambda p: y(p) + 190, lambda p: -88 - y(p), lambda p: z(p) + 82, lambda p: 112 - .8 * (a(p) - 225) - z(p)); Z["H"] = H
C, Z["AI"] = clip(C, f_ai)
Z["CORP"], Z["CORP etaj"] = clip(C, f_et)
L = halfS(load("moreno_v17_al", ["NurbsPath.002_Mesh.002"])); r, Z["PS"] = clip(L, lambda p: y(p) + 55)
aft = r.reshape(-1, 3); zt = aft[aft[:, 1] < aft[:, 1].min() + 6, 2].mean(); print("T3: z", round(float(zt), 1), "la y", aft[:, 1].min().round())
bj2, Z["BS"] = clip(r, lambda p: z(p) - zt); Z["BJ"] = np.concatenate([Z["BJ"], bj2])
Z["BF"] = halfS(load("moreno_v17_al", ["NurbsPath.007_Mesh.004"])); Z["AS"] = halfS(load("moreno_v17_al", ["Circle"]))
# PI + ARCU from grannyte: connected faces from the PI nose under a line between arms and belly, plus the two arm ends
G = load("NAVA_REPO_XMF_al"); V, I = np.unique(G.reshape(-1, 3).round(2), axis=0, return_inverse=True); F = I.reshape(-1, 3); c = V[F].mean(1)
lim = np.interp(c[:, 1], [-900, -620, -500, -275, -150, 200], [-20, -95, -130, -190, -232, -232]); ok = (c[:, 2] < lim) & (np.abs(c[:, 0]) < np.interp(c[:, 1], [-900, -600, -500, -150], [470, 370, 300, 260]))
par = np.arange(len(V))
def find(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
for f in F[ok]:
    for j in f[1:]: par[find(j)] = find(f[0])
seed = np.where(ok)[0][np.argmin(np.linalg.norm(c[ok] - [0, 150, -320], axis=1))]; root = find(F[seed, 0]); sel = ok & np.array([find(i) == root for i in F[:, 0]])
allp = np.arange(len(V)); par = allp.copy()
for f in F:
    for j in f[1:]: par[find(j)] = find(f[0])
rt = np.array([find(i) for i in F[:, 0]])
for q in np.unique(rt):
    P = V[F[rt == q]].reshape(-1, 3); lo, hi = P.min(0), P.max(0)
    if lo[1] > -920 and hi[1] < -560 and hi[2] < 0 and np.abs(P[:, 0]).min() > 200 and len(P) > 3000: sel |= rt == q
Z["PI (ARCU)"] = halfS(V[F[sel]])
T = []; N = []
for k, q in Z.items():
    A = np.linalg.norm(np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]), axis=1); q = q[A > 1e-4]; q = np.concatenate([q, q[:, ::-1] * [-1, 1, 1]]); T.append(q); N += [k] * len(q)
    print(k, len(q), q.min((0, 1)).round(), q.max((0, 1)).round())
np.savez(f"{D}/zone_curate.npz", T=np.concatenate(T), zone=np.array(N))
