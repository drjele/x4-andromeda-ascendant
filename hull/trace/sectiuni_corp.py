# Step 2 of the hybrid rebuild (the confirmed ellipse sections -> one closed smooth volume): on a grid (CELL m) the inside
# of three shapes, from the rails of sectiuni_aliniate.py (SEC_ELIPSA): PS = an ellipse per y on the axis (half width,
# top, bottom; the nose closed along the outer silhouette, its height shrinking with the width), the arms = an ellipse per
# y between the outer and inner lines, and the uniform loop tube (the body's rows, ps_corp_mesh.py CORP_DUMP + plan move)
# where the arms run into the loops. Each turned into a signed distance; blended along y (PS -> arms under the U over
# TU m, arms -> tube over TT m), the U between the arms cut exactly on the inner silhouette, a light gaussian on the field,
# surface at 0 (marching cubes), a few Taubin passes. Writes verts / faces (ship coordinates relative to the middle).
# Usage: python sectiuni_corp.py <elipse_ghidaje.npz> <silueta.npz> <L_corp.npz> <plan_d.npz> <out.npz> [cell]
import sys, numpy as np
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
R = np.load(sys.argv[1]); SIL = np.load(sys.argv[2]); LZ = np.load(sys.argv[3]); PD = np.load(sys.argv[4]); OUT = sys.argv[5]
CELL = float(sys.argv[6]) if len(sys.argv) > 6 else 1.5
YU, TU, YT, TT, YEND = -33.4, 70.0, -760.0, 70.0, -1010.0
X0, X1, Y0, Y1, Z0, Z1 = -360.0, 360.0, YEND, 480.0, 200.0, 400.0
xs = np.arange(X0 + CELL / 2, X1, CELL); ys = np.arange(Y0 + CELL / 2, Y1, CELL); zs = np.arange(Z0 + CELL / 2, Z1, CELL)
NX, NY, NZ = len(xs), len(ys), len(zs); print("GRILA %d x %d x %d (%.0f M celule, %.1f m)" % (NX, NY, NZ, NX * NY * NZ / 1e6, CELL))
X, Zg = np.meshgrid(xs, zs, indexing="ij")                             # one y slice at a time (x, z)
def rail(k, j, yq):                                                    # rail k component j at heights yq (held at the ends)
    Q = R[k]; o = np.argsort(Q[:, 1]); return np.interp(yq, Q[o, 1], Q[o, j])
# PS rails, the nose closed along the outer silhouette
Bo = SIL["B"]; Bo = Bo[Bo[:, 0] >= 0]; Bo = Bo[np.argsort(Bo[:, 1])]; ytipS = R["ps_lat"][:, 1].max()
def ps_par(y):
    w = rail("ps_lat", 0, y); top = rail("ps_sus", 2, y); bot = rail("ps_jos", 2, y)
    if y > ytipS:                                                      # past the first station: width from the silhouette, height
        ws = np.interp(y, Bo[:, 1], Bo[:, 0]); h0 = top - bot; zc = (top + bot) / 2; s = ws / max(w, 1e-6); return ws, zc + h0 * s / 2, zc - h0 * s / 2
    return w, top, bot
def ar_par(y): return rail("br_ext", 0, y), rail("br_int", 0, y), rail("br_sus", 2, y), rail("br_jos", 2, y)
# tube rings (loop part): ellipse per ring in its own frame
L = LZ["L"].copy(); L[..., :2] += PD["d"]; cen = L.mean(1); keep = (cen[:, 1] < YT + 80) & (cen[:, 1] > YEND - 40) & (cen[:, 2] > Z0 + 20)
rings = []
idx = np.nonzero(keep)[0]
for k in idx:
    if k == 0 or k == len(L) - 1: continue
    t = cen[k + 1] - cen[k - 1]; ds = np.linalg.norm(t) / 2; t /= np.linalg.norm(t); sd = np.cross(t, [0, 0, 1.0]); sd /= np.linalg.norm(sd); up = np.cross(sd, t)
    q = L[k] - cen[k]; rings.append((cen[k], t, sd, up, np.abs(q @ sd).max(), np.abs(q @ up).max(), ds))
print("TUB: %d inele intre y %.0f si %.0f" % (len(rings), cen[idx, 1].min(), cen[idx, 1].max()))
def edist(u, w, a_, b_):                                               # signed distance to an ellipse, first order (smooth field,
    a_, b_ = np.maximum(a_, 1e-3), np.maximum(b_, 1e-3); g = (u / a_) ** 2 + (w / b_) ** 2 - 1   # no voxel steps)
    gr = 2 * np.sqrt((u / a_ ** 2) ** 2 + (w / b_ ** 2) ** 2); return np.maximum(g / np.maximum(gr, 1e-6), -np.minimum(a_, b_))
BIG = np.float32(1e3); f_ps = np.full((NX, NY, NZ), BIG, np.float32); f_ar = f_ps.copy(); f_tb = f_ps.copy()
for j, y in enumerate(ys):
    if y > YU - TU - 10:                                               # PS (held at the U's values below it)
        w, top, bot = ps_par(max(y, YU + 2.0)); f_ps[:, j] = edist(X, Zg - (top + bot) / 2, w, (top - bot) / 2)
    if y < YU + 10:
        o_, i_, t_, b_ = ar_par(min(y, YU - 2.0)); f_ar[:, j] = edist(np.abs(X) - (o_ + i_) / 2, Zg - (t_ + b_) / 2, (o_ - i_) / 2, (t_ - b_) / 2)
for c, t, sd, up, a_, b_, ds in rings:                                 # the tube: each ring's ellipse over a short slab (both sides)
    for sg in (1, -1):
        cc = c * [sg, 1, 1]; tt_, sdd, upp = t * [sg, 1, 1], sd * [sg, 1, 1], up * [sg, 1, 1]
        jl, jh = np.searchsorted(ys, cc[1] - 60), np.searchsorted(ys, cc[1] + 60); il, ih = np.searchsorted(xs, cc[0] - 70), np.searchsorted(xs, cc[0] + 70)
        if jh <= jl or ih <= il: continue
        Xs, Ys, Zs = np.meshgrid(xs[il:ih], ys[jl:jh], zs, indexing="ij"); Q = np.stack([Xs - cc[0], Ys - cc[1], Zs - cc[2]], -1)
        d = edist(Q @ sdd, Q @ upp, a_, b_).astype(np.float32); d[np.abs(Q @ tt_) > ds + CELL] = BIG
        f_tb[il:ih, jl:jh] = np.minimum(f_tb[il:ih, jl:jh], d)
sm = lambda v: v * v * (3 - 2 * v)
t1 = sm(np.clip((YU - ys) / TU, 0, 1))[None, :, None]; t2 = sm(np.clip((YT - ys) / TT, 0, 1))[None, :, None]
F = (1 - t1) * f_ps + t1 * ((1 - t2) * f_ar + t2 * f_tb); del f_ps, f_ar, f_tb
Bi = SIL["B_int"]; Bi = Bi[Bi[:, 0] >= 0]; Bi = Bi[np.argsort(Bi[:, 1])]   # the U cut on the inner silhouette (plan distance)
xin = np.where((ys >= Bi[:, 1].min()) & (ys <= YU), np.interp(ys, Bi[:, 1], Bi[:, 0]), -1e3)
dgap = (xin[None, :] - np.abs(xs)[:, None]).astype(np.float32)          # > 0 inside the gap
F = np.maximum(F, dgap[:, :, None])
F = gaussian_filter(F, 0.7)
v, fcs, _, _ = marching_cubes(F, 0.0, spacing=(CELL, CELL, CELL)); v += [X0 + CELL / 2, Y0 + CELL / 2, Z0 + CELL / 2]
nb = [[] for _ in range(len(v))]
e = np.vstack([fcs[:, [0, 1]], fcs[:, [1, 2]], fcs[:, [2, 0]]]); e = np.unique(np.sort(e, 1), axis=0)
deg = np.bincount(e.ravel(), minlength=len(v)).astype(float)[:, None]
def avg(V):
    S = np.zeros_like(V); np.add.at(S, e[:, 0], V[e[:, 1]]); np.add.at(S, e[:, 1], V[e[:, 0]]); return S / np.maximum(deg, 1)
for _ in range(10): v = v + 0.5 * (avg(v) - v); v = v + -0.53 * (avg(v) - v)
np.savez(OUT, v=v.astype(np.float32), f=fcs.astype(np.int32))
print("SUPRAFATA: %d varfuri, %d fete; y %.0f..%.0f, x %.0f..%.0f, z %.0f..%.0f" % (len(v), len(fcs), v[:, 1].min(), v[:, 1].max(), v[:, 0].min(), v[:, 0].max(), v[:, 2].min(), v[:, 2].max()))
