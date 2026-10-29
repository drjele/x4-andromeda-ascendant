# Vertebrae to lengthen the PS out to the confirmed median outline (asked: "vertebre ca să lungim forma lui sep_PS până la
# g_umm_sep_contur_umar_median"). At each station y (every PAS m between Y0 and Y1) the PS's real section (right half, from
# the deck on the axis round the side to the belly on the axis): deck and belly kept up to the attach points (on the
# section, D_ATT m in from its widest x, above / below the median plane), the side replaced by two Hermite curves -
# leaving the section along its own direction (no corner), meeting at the guide point (x of the confirmed outline, z of the
# median plane) with a vertical tangent (widest there). Left half = mirror; each vertebra in its plane y = const.
# VP_EXTRA=y1,y2: extra vertebrae past the U (the section in two leg stubs): only each stub's outer side reshaped.
# Usage: python vertebre_ps.py <pieces.npz> <ghid_median.npz> <out.npz> ; env VP_Y0=260 VP_Y1=-40 VP_PAS=20 VP_ATT=25 VP_K=0.6
import sys, os, numpy as np, trimesh
D = np.load(sys.argv[1]); M = np.load(sys.argv[2]); OUT = sys.argv[3]; MX = -1700.0; e = lambda k, d: float(os.environ.get(k, d))
Y0, Y1, PAS, ATT, KT = e("VP_Y0", "260"), e("VP_Y1", "-40"), e("VP_PAS", "20"), e("VP_ATT", "25"), e("VP_K", "0.6")
ps = trimesh.Trimesh(D["PS__v"] - [MX, 0, 0], D["PS__f"], process=False)
Gm = M["contur_umar_median"]; ZM = Gm[0, 2]; R = Gm[Gm[:, 0] >= 0]; R = R[np.argsort(-R[:, 1])]; xg = lambda y: np.interp(-y, -R[:, 1], R[:, 0])
def herm(p0, t0, p1, t1, n=30):
    L = np.linalg.norm(p1 - p0) * KT; s = np.linspace(0, 1, n)[:, None]
    return (2*s**3 - 3*s**2 + 1) * p0 + (s**3 - 2*s**2 + s) * L * t0 + (-2*s**3 + 3*s**2) * p1 + (s**3 - s**2) * L * t1
out = {}; rep = []
for k, y in enumerate(np.arange(Y0, Y1 - 0.1, -PAS)):
    s = ps.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: continue
    Lp = max([q[:, [0, 2]] for q in s.discrete], key=lambda q: q[:, 0].max())   # the loop reaching furthest right
    H = Lp[Lp[:, 0] >= -0.5]
    if len(H) < 6: continue
    ang = np.arctan2(H[:, 1] - ZM, H[:, 0]); H = H[np.argsort(-ang)]      # deck -> side -> belly
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(H, axis=0), axis=1))]; u = np.arange(0, d[-1], 0.5)
    H = np.c_[np.interp(u, d, H[:, 0]), np.interp(u, d, H[:, 1])]
    xm = H[:, 0].max(); up = np.where((H[:, 0] >= xm - ATT) & (H[:, 1] > ZM))[0]; dn = np.where((H[:, 0] >= xm - ATT) & (H[:, 1] < ZM))[0]
    if not len(up) or not len(dn): continue
    i, j = up[0], dn[-1]; G = np.array([xg(y), ZM])
    t_i = H[min(i + 4, len(H) - 1)] - H[i]; t_i /= np.linalg.norm(t_i); t_j = H[j] - H[max(j - 4, 0)]; t_j /= np.linalg.norm(t_j)
    c1 = herm(H[i], t_i, G, np.array([0.0, -1.0])); c2 = herm(G, np.array([0.0, -1.0]), H[j], t_j)
    half = np.vstack([H[:i], c1, c2[1:], H[j + 1:]])
    full = np.vstack([half, (half * [-1, 1])[::-1][1:]])
    out["vertebra_%02d" % k] = np.c_[full[:, 0], np.full(len(full), y), full[:, 1]]
    rep.append((y, xm, G[0], G[0] - xm, H[i, 0], H[i, 1], H[j, 0], H[j, 1]))
for k2, y in enumerate([float(q) for q in os.environ.get("VP_EXTRA", "").split(",") if q]):   # past the U: each leg stub's
    s = ps.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])                               # outer side only
    if s is None: continue
    L = max([q[:, [0, 2]] for q in s.discrete], key=lambda q: q[:, 0].mean()); L = L[:-1] if np.allclose(L[0], L[-1]) else L
    c = L.mean(0); th = np.degrees(np.arctan2(L[:, 1] - c[1], L[:, 0] - c[0])); xm = L[:, 0].max()
    up = (L[:, 0] >= xm - ATT) & (L[:, 1] > ZM); dn = (L[:, 0] >= xm - ATT) & (L[:, 1] < ZM)
    if not up.any() or not dn.any(): continue
    it, ib = np.where(up)[0][np.argmax(th[up])], np.where(dn)[0][np.argmin(th[dn])]; G = np.array([max(xg(y), xm), ZM])
    o = np.argsort(th); Ls, ts = L[o], th[o]; inner = np.r_[np.where(ts > th[it])[0], np.where(ts < th[ib])[0]]
    P_in = np.vstack([L[it], Ls[inner], L[ib]])                                                   # top attach -> inner side -> bottom attach
    t_t = L[it] - Ls[np.where(ts > th[it])[0][:4]].mean(0); t_t /= np.linalg.norm(t_t)            # leaving outwards
    t_b = Ls[np.where(ts < th[ib])[0][-4:]].mean(0) - L[ib]; t_b /= np.linalg.norm(t_b)
    c1 = herm(L[it], t_t, G, np.array([0.0, -1.0])); c2 = herm(G, np.array([0.0, -1.0]), L[ib], -t_b)
    loop = np.vstack([P_in, c2[::-1][1:], c1[::-1][1:]])
    out["vertebra_%02d_D" % (15 + k2)] = np.c_[loop[:, 0], np.full(len(loop), y), loop[:, 1]]
    out["vertebra_%02d_S" % (15 + k2)] = np.c_[-loop[:, 0], np.full(len(loop), y), loop[:, 1]]
    rep.append((y, xm, G[0], G[0] - xm, L[it, 0], L[it, 1], L[ib, 0], L[ib, 1]))
for r in rep: print("y %4.0f: PS cel mai lat x %.1f -> ghidaj x %.1f (%+.1f m); prindere sus (%.0f, %.0f), jos (%.0f, %.0f)" % r)
np.savez(OUT, **out); print("VERTEBRE:", len(out), "in planele y, z median %.1f" % ZM)
