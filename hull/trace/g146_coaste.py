# nt_146 ribs: one vertical plane per station through the paired points of the two plan rails (body: y = const, arm: across the arm), the reference section read in that plane and
# fitted with one family: inner end + straight run + outer end, elliptic quarters on top and below. Writes the raw parameters per station.
import numpy as np, trimesh, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from scipy.spatial import cKDTree as KD
from scipy.ndimage import gaussian_filter1d as gf
O = "/home/adrian/Documents/Andromeda/2026-11-05-nt146/"; P = "/home/adrian/Documents/Andromeda/2026-10-29-imbinari/piese/"
Z = np.load(P + "nt_ref_toate.npz", allow_pickle=True); v = Z["R005_146_C__v"].astype(float) * [-1, 1, 1]; f = Z["R005_146_C__f"][:, ::-1]; m = trimesh.Trimesh(v, f, process=False)
R = np.load(O + "rails_plan.npz"); E, I = R["E"], R["I"]; arc = lambda A: np.r_[0, np.cumsum(np.linalg.norm(np.diff(A, axis=0), axis=1))]; sE, sI = arc(E), arc(I)
at = lambda A, s, q: np.stack([np.interp(q, s, A[:, 0]), np.interp(q, s, A[:, 1])], 1)
# pairing. Body: same y, inner point on the axis. After the V's corner: across the arm, straight rail normal; between them linear in arc length so no two planes cross.
yb = np.r_[430.0, np.arange(424, -28, -6.0), np.arange(-28, -37.6, -1.5), -37.6]; eb = np.array([sE[np.argmin(np.abs(E[:, 1] - y) + 1e3 * (sE > 700))] for y in yb]); B = [(np.array([0.0, y]), e) for y, e in zip(yb, eb)]
S0 = 230.0; qI = np.arange(S0, sI[-1], 6.0); tI = at(I, sI, qI); near = KD(E).query(tI)[1]; eT = gf(sE[near].astype(float), 3, mode="nearest"); eT = np.maximum.accumulate(eT)
mI = np.r_[np.arange(1.2, 26, 1.5), np.arange(30, 96, 6.0), np.arange(96, 136, 1.5), np.arange(140, S0 - 2, 6.0)]; mE = np.interp(mI, [0, S0], [eb[-1], eT[0]])
pairs = [(p, at(E, sE, np.array([e]))[0]) for p, e in B] + [(at(I, sI, np.array([a]))[0], at(E, sE, np.array([e]))[0]) for a, e in zip(mI, mE)] + [(a, at(E, sE, np.array([e]))[0]) for a, e in zip(tI, eT)]
pairs.append((I[-1], E[-1])); Pi = np.array([p[0] for p in pairs]); Pe = np.array([p[1] for p in pairs])
# rib rotation eased: the map inner point -> outer point smoothed over the apex and the V (a sudden change of rotation rate shows as a crease across the surface)
qI = arc(Pi); qE = np.array([sE[np.argmin(np.linalg.norm(E - p, axis=1))] for p in Pe]); ug = np.arange(0, qI[-1] + 1, 1.0); eg = np.interp(ug, qI, qE); SIG = 32.0; es = gf(eg, SIG, mode="nearest"); wg = np.clip((qI[-1] - 120 - ug) / 60, 0, 1) * np.clip((ug - 140) / 80, 0, 1); eg = eg + wg * (es - eg); eg = np.maximum.accumulate(eg); Pe = at(E, sE, np.interp(qI, ug, eg)); Pe[-1] = E[-1]
n = len(Pi); w = np.linalg.norm(Pe - Pi, axis=1); print("statii", n, "latime min/max %.1f %.1f" % (w.min(), w.max()))
def rib(u, th):
    """(t, z) model, S-shaped family: inner quarter ellipse from the wall end up to the run, straight (possibly sloped) run, outer quarter ellipse down to the rail.
    th: zT, zB, zE, ao, zIt, zIb, ai, zTi, zBi, W -> top and bottom z at t."""
    zT, zB, zE, ao, zIt, zIb, ai, zTi, zBi, W = th
    def side(t, zc, zci, z_i):
        a = np.clip(ao, .5, W); b = np.clip(ai, 0, W - a); e = W - a; z = zci + (zc - zci) * np.clip((t - b) / max(e - b, 1e-6), 0, 1); o = t > e; xo = (t[o] - e) / a; z[o] = zE + (zc - zE) * np.sqrt(np.clip(1 - xo ** 2, 0, 1))
        if b > .01: i_ = t < b; xi = (b - t[i_]) / b; z[i_] = z_i + (zci - z_i) * np.sqrt(np.clip(1 - xi ** 2, 0, 1))
        return z
    return side(u, zT, zTi, zIt), side(u, zB, zBi, zIb)
RES = []; PTS = []
for k in range(n):
    a, b = Pi[k], Pe[k]; d = (b - a) / max(np.linalg.norm(b - a), 1e-6); nr = np.array([-d[1], d[0], 0.0]); o = np.array([a[0], a[1], 0.0]); segs = trimesh.intersections.mesh_plane(m, nr, o); W = float(w[k])
    if len(segs) == 0: RES.append(np.full(9, np.nan)); PTS.append(np.zeros((0, 2))); continue
    q = np.vstack([s0 + (s1 - s0) * np.linspace(0, 1, max(2, int(np.linalg.norm(s1 - s0) / .5) + 1))[:, None] for s0, s1 in segs]); t = (q[:, :2] - a) @ d; q2 = np.c_[t, q[:, 2]]; q2 = q2[(t > -2) & (t < W + 2)]; PTS.append(q2)
    if len(q2) < 8: RES.append(np.full(9, np.nan)); continue
    zm = np.median(q2[:, 1]); top = q2[q2[:, 1] >= zm]; bot = q2[q2[:, 1] < zm]; onax = k < len(B); inner_flat = onax
    x0 = [top[:, 1].max(), bot[:, 1].min(), zm, min(.35 * W, 40), top[:, 1].max() if onax else zm, bot[:, 1].min() if onax else zm, 0.0 if onax else min(.4 * W, 20), top[:, 1].max(), bot[:, 1].min()]
    def res(x):
        T_, B_ = rib(top[:, 0].clip(0, W), [*x, W])[0], rib(bot[:, 0].clip(0, W), [*x, W])[1]; return np.r_[T_ - top[:, 1], B_ - bot[:, 1]]
    lo = [zm, zm - 200, zm - 40, .5, zm - 60, zm - 60, 0.0, zm - 100, zm - 200]; hi = [zm + 200, zm, zm + 40, W, zm + 60, zm + 60, 0.001 if onax else W, zm + 200, zm + 100]; x0 = np.clip(x0, np.array(lo) + 1e-6, np.array(hi) - 1e-6)
    r = least_squares(res, x0, bounds=(lo, hi), loss="soft_l1", f_scale=1.0, max_nfev=60); RES.append(r.x)
RES = np.array(RES); np.savez(O + "coaste_raw.npz", Pi=Pi, Pe=Pe, w=w, th=RES, nb=len(B)); s_c = arc((Pi + Pe) / 2); names = ["zT", "zB", "zE", "ao", "zIt", "zIb", "ai", "zTi", "zBi"]; S_C = s_c; zone = np.nonzero((s_c > 470) & (s_c < 660))[0]; print("  s    zT    zB    zE    ao   zIt   zIb   ai  zTi  zBi   w")
for k in zone[:: 2]: print("%4.0f " % s_c[k] + " ".join("%6.1f" % q for q in RES[k]) + " %5.1f" % w[k])
fig, ax = plt.subplots(3, 1, figsize=(15, 11))
for j in (0, 1, 2, 4, 5): ax[0].plot(s_c, RES[:, j], label=names[j], lw=.9)
ax[1].plot(s_c, RES[:, 3], label="ao"); ax[1].plot(s_c, RES[:, 6], label="ai"); ax[1].plot(s_c, w, label="w"); ax[2].plot((Pi[:: 4] * 1)[:, 0], Pi[:: 4, 1], "k."); ax[2].set_aspect("equal")
for k in range(0, n, 6): ax[2].plot([Pi[k, 0], Pe[k, 0]], [Pi[k, 1], Pe[k, 1]], "r", lw=.5)
for a in ax[:2]: a.legend(); a.grid(alpha=.3)
fig.tight_layout(); fig.savefig(O + "a5_param.png", dpi=80)
idx = np.r_[np.linspace(2, nb_ := np.searchsorted(s_c, 470), 8).astype(int), np.searchsorted(s_c, np.linspace(475, 640, 17)), np.linspace(np.searchsorted(s_c, 700), n - 2, 5).astype(int)]; fig, ax = plt.subplots(6, 5, figsize=(20, 14))
for a, k in zip(ax.ravel(), idx):
    if len(PTS[k]) == 0 or np.isnan(RES[k]).any(): continue
    a.plot(PTS[k][:, 0], PTS[k][:, 1], ".", color=".6", ms=1.5); u = np.linspace(0, w[k], 300); T_, B_ = rib(u, [*RES[k], w[k]]); a.plot(u, T_, "r", lw=.8); a.plot(u, B_, "b", lw=.8); a.set_aspect("equal"); a.set_title("s=%.0f (%.0f,%.0f)" % (s_c[k], Pi[k, 0], Pi[k, 1]), fontsize=8)
fig.tight_layout(); fig.savefig(O + "a6_coaste.png", dpi=70)
