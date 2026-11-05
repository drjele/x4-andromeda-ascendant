# nt_146 from clean guides, surface lofted THROUGH them so they lie on it by construction. Half on x > 0 (S side of the reference), mirrored. Plan rails = lines + tangent arcs (g146_plan.py),
# height rails = lines + tangent arcs over arc length, ribs = planar: inner quarter ellipse + straight run + outer quarter ellipse. Writes <out>/146.npz + 146_g.npz, report + sheets.
import numpy as np, trimesh, json, os, sys, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, g1_arce as g
from scipy.interpolate import PchipInterpolator as PC
from scipy.ndimage import gaussian_filter1d as gf
from scipy.spatial import cKDTree as KD
O = "/home/adrian/Documents/Andromeda/2026-11-05-nt146/"; P = "/home/adrian/Documents/Andromeda/2026-10-29-imbinari/piese/"; OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
C = np.load(O + "coaste_raw.npz"); Pi, Pe, W, th, nb = C["Pi"], C["Pe"], C["w"], C["th"], int(C["nb"]); arc = lambda A: np.r_[0, np.cumsum(np.linalg.norm(np.diff(A, axis=0), axis=1))]; S = arc((Pi + Pe) / 2) + 16.0; n = len(S); sap = S[nb - 1]
ok = ~np.isnan(th[:, 0]); print("apex la s = %.0f; statii %d" % (sap, n)); SEG = {}
from scipy.interpolate import make_lsq_spline
def rail(name, s, y, tol=1.2, lmin=70.0, nmax=14):
    """Height over arc length: slope piecewise linear (arcs tangent to each other at these slopes), fewest knots within tol; a knot goes where the misfit is largest."""
    o = np.argsort(s); s, y = s[o], y[o]; kn = []
    while True:
        t = np.r_[[s[0]] * 3, kn, [s[-1]] * 3]; sp = make_lsq_spline(s, y, t, k=2); r = np.abs(sp(s) - y); e = gf(r, 3, mode="nearest"); j = int(np.argmax(e))
        if e[j] <= tol or len(kn) >= nmax: break
        c = np.array([s[0], *kn, s[-1]]); q = s[j]
        if np.abs(c - q).min() < lmin:
            g_ = np.diff(c); i = int(np.argmax(g_)); q = c[i] + g_[i] / 2
            if g_[i] < 2 * lmin: break
        kn = sorted(kn + [float(q)])
    SEG[name] = dict(noduri=[round(k) for k in kn], max=round(float(e.max()), 2)); return lambda q: sp(np.clip(q, s[0], s[-1]))
nj = ok & ((S < 570) | (S > 600)); zT = rail("sus", S[nj], th[nj, 0]); zB = rail("jos", S[nj], th[nj, 1]); M = (zT(S) + zB(S)) / 2; mk = ok & ((S < 585) | (S > 630)); zE = rail("mijloc", S[mk], np.where(S[mk] > 630, M[mk], th[mk, 2]), tol=2.0, lmin=120.0)
ao0 = rail("ao", S[ok & (S < 575)], np.minimum(th[ok & (S < 575), 3], W[ok & (S < 575)]), tol=4.0, lmin=50.0)
K = lambda xs, ys: PC(xs, ys)
XK = np.array([380, 400, 470, 490, 530, 558, 625, 660]); dlt = lambda f, ys: PC(XK, np.r_[0, 0, np.array(ys) - f(XK[2:7]), np.array(ys)[-1] - float(f(625.0))])     # offset from the height rail, zero slope where it starts: no kink on the rail
dT = dlt(zT, [-258.8, -260.5, -263.2, -263.7, -262.0]); dB = dlt(zB, [-329.7, -325.0, -317.0, -307.0, -298.0])
tzTi = lambda s: zT(s) + np.where(s < 380, 0.0, dT(np.clip(s, 380, 660))); tzBi = lambda s: zB(s) + np.where(s < 380, 0.0, dB(np.clip(s, 380, 660)))
Ta, Ba = float(tzTi(np.array(sap))), float(tzBi(np.array(sap))); hw = lambda s: np.where(s < sap, 0.0, K([sap, 530, 558, 625, 1500], [(Ta - Ba) / 2, 23, 17, 8, 8])(np.minimum(s, 1500))); cw = K([sap, 530, 558, 625, 1500], [(Ta + Ba) / 2, -290, -285, -278, -278])
zW = lambda s: np.where(s <= sap, (Ta + Ba) / 2, cw(np.minimum(s, 1500)))
LA, LB = 535.0, 612.0; lam = lambda s: (lambda x: x * x * (3 - 2 * x))(float(np.clip((s - LA) / (LB - LA), 0, 1)))    # the V's profile melts into the arm's ellipse: two fixed shapes blended, no knot moving along the rib
Nt = 26; Nw = 3
def rib(k):
    """Ring of the station: t, z; top from the wall to the outer rail, bottom back, then the wall."""
    s, w = S[k], W[k]; zt, zb, ze = float(zT(s)), float(zB(s)), float(zE(s)); tt = np.arange(0, w + .25, .25); L = lam(s); u = np.linspace(0, 1, Nt + 1); tq = w * (1 - np.cos(np.pi * u)) / 2
    ell = lambda zc: ze + (zc - ze) * np.sqrt(np.clip(1 - ((tt - w / 2) / (w / 2)) ** 2, 0, 1))
    if L >= 1: ttop, tbot = ell(zt), ell(zb); wt, wb = ze, ze
    else:
        a = min(float(ao0(min(s, 574.0))), w); b = 0.0 if s < sap else min(5.0, (s - sap) * 1.5); b = min(b, w - a); e = w - a; c, h = float(zW(s)), float(hw(s)); zit, zib = c + h, c - h; zi, zbi = float(tzTi(np.array(s))), float(tzBi(np.array(s)))
        def side(zc, zci, z_i):
            z = zci + (zc - zci) * np.clip((tt - b) / max(e - b, 1e-6), 0, 1); o = tt > e; z[o] = ze + (zc - ze) * np.sqrt(np.clip(1 - ((tt[o] - e) / max(a, 1e-6)) ** 2, 0, 1))
            if b > .01: i = tt < b; z[i] = z_i + (zci - z_i) * np.sqrt(np.clip(1 - ((b - tt[i]) / b) ** 2, 0, 1))
            m = np.exp(-((tt - e) / 7.0) ** 2) * min(1.0, abs(zc - zci) / 6.0); m[(tt < 1.5) | (tt > w - 1.5)] = 0; return z + np.clip(m, 0, 1) * (gf(z, 3.0 / .25, mode="nearest") - z)
        p1, p2 = side(zt, zi, zit), side(zb, zbi, zib); ttop, tbot = (1 - L) * p1 + L * ell(zt), (1 - L) * p2 + L * ell(zb)
    a1 = np.interp(tq, tt, ttop); a2 = np.interp(tq, tt, tbot); a1[-1] = a2[-1] = ze; top = np.c_[tq, a1]; bot = np.c_[tq, a2][::-1][1:]; wall = np.c_[np.zeros(Nw - 1), np.linspace(a2[0], a1[0], Nw + 1)[1:-1]]; return np.vstack([top, bot, wall]), a1[0], a2[0]
k0 = int(np.argmin(np.abs(Pi[:nb, 1] - 395.0))); Pi, Pe, W, S = Pi[k0:], Pe[k0:], W[k0:], S[k0:]; nb -= k0; n = len(S)
RG = [rib(k)[0] for k in range(n)]; nr = len(RG[0])
# nose: the last ribs closed as a half ellipse in (y, z), so the two sides meet on the axis in one round tip
d = (Pe - Pi); d = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9); V = np.array([np.c_[Pi[k, 0] + d[k, 0] * R[:, 0], Pi[k, 1] + d[k, 1] * R[:, 0], R[:, 1]] for k, R in enumerate(RG)])
E_ = np.load(O + "rails_plan.npz")["E"]; sE = arc(E_); r0 = RG[0].copy(); r1 = RG[1]; zc = float(zE(S[0])); Y0 = Pi[0, 1]; NS = []; oe = np.argsort(E_[:400, 1])
u0 = .8; A0 = (452.5 - Y0) / (1 - u0); yc = 452.5 - A0; g0 = np.sqrt(1 - u0 ** 2); print("nas: elipsa semi-axa %.0f, centrul y %.0f" % (A0, yc))   # one long ellipse from y 395 to the tip
PHI = np.linspace(np.arcsin(u0) + .03, np.pi / 2 - .06, 26)[::-1]; ST = yc + A0 * np.sin(PHI)
for y in ST:
    f = np.sqrt(np.clip(1 - ((y - yc) / A0) ** 2, 0, 1)) / g0; xe = float(np.interp(y, E_[oe, 1], E_[oe, 0])); ringx = r0[:, 0] / max(W[0], 1e-6) * xe; NS.append(np.c_[ringx, np.full(nr, y), zc + (r0[:, 1] - zc) * f])
V = np.vstack([np.array(NS)[None][0], V]); ns = len(V); oax = len(ST) + nb   # stations on the axis
Q = []
for k in range(ns - 1):
    for j in range(nr):
        if k < oax - 1 and j >= 2 * Nt: continue                               # on the axis the wall does not exist, the mirror closes it
        Q.append((k * nr + j, k * nr + (j + 1) % nr if not (k < oax - 1 and j == 2 * Nt - 1) else k * nr + 2 * Nt, (k + 1) * nr + ((j + 1) % nr if not (k < oax - 1 and j == 2 * Nt - 1) else 2 * Nt), (k + 1) * nr + j))
Q = np.array(Q); T = np.vstack([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
# nose and tip caps
cf = []; a0 = 0
for j in range(nr - 1): pass
Vf = V.reshape(-1, 3); tip = np.array([(Vf[(ns - 1) * nr + j]) for j in range(nr)]).mean(0); it_ = len(Vf); Vf = np.vstack([Vf, tip]); tc = np.array([[(ns - 1) * nr + j, (ns - 1) * nr + (j + 1) % nr, it_] for j in range(nr)])[:, [0, 2, 1]]
nz = np.array([0.0, 452.5, zc]); iz = len(Vf); Vf = np.vstack([Vf, nz]); nc = np.array([[j, j + 1, iz] for j in range(2 * Nt)])[:, [0, 2, 1]]; nc[-1, 2] = 0 if False else nc[-1, 2]; Vf[0:2 * Nt + 1, 0] *= 1.0
# weld (collapsed walls, the tube's closed inner end), then mirror across x = 0
F = np.vstack([T, tc, nc]); Vf[np.abs(Vf[:, 0]) < 1e-4, 0] = 0.0; Vf = Vf.copy(); Vm = Vf * [-1, 1, 1]; Fm = F[:, ::-1] + len(Vf); VA = np.vstack([Vf, Vm]); FA = np.vstack([F, Fm])
m = trimesh.Trimesh(VA, FA, process=False); m.merge_vertices(digits_vertex=3); m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices(); trimesh.repair.fix_normals(m)
if m.volume < 0: m.invert()
print("mesh", len(m.vertices), "v", len(m.faces), "f, etans", m.is_watertight, "volum %.0f" % m.volume)
ed = m.edges_sorted; u_, cn = np.unique(ed, axis=0, return_counts=True); be = u_[cn == 1]; print("muchii libere", (cn == 1).sum(), "ne-manifold", (cn > 2).sum(), m.vertices[be.ravel()][:6].round(1).tolist()); ang = np.degrees(m.face_adjacency_angles); print("cute: >60 %d, >30 %d, >15 %d" % ((ang > 60).sum(), (ang > 30).sum(), (ang > 15).sum()))
# guides: ribs (planar), rails
G = {}; Vh = V; KR = np.searchsorted(S, np.r_[np.arange(S[0], sap - 10, 65), sap + 6, sap + 30, sap + 55, sap + 80, sap + 110, np.arange(sap + 170, S[-1] - 15, 75), S[-1]]) + len(ST); KR = np.unique(np.minimum(KR, ns - 1))
for k in KR:
    q = Vh[k]; G["coasta_%d" % int(S[max(k - len(ST), 0)])] = (np.vstack([q, q[:1]]) if k >= oax else q[:2 * Nt])
idx = lambda j: Vh[:, j]; G["contur_ext"] = idx(Nt); iW = np.arange(oax - 1, ns); G["contur_int_sus"] = Vh[iW, 0]; G["contur_int_jos"] = Vh[iW, 2 * Nt]; G["axa_sus"] = Vh[:oax, 0]; G["axa_jos"] = Vh[:oax, 2 * Nt]
kc = np.arange(np.searchsorted(S, sap + 110) + len(ST), ns); G["creasta_sus"] = Vh[kc, Nt // 2]; G["creasta_jos"] = Vh[kc, Nt + Nt // 2]
kink = {}; pq = trimesh.proximity.ProximityQuery(m); dp = []
for nm_, L in G.items():
    if nm_.startswith("coasta"): dp.append(pq.on_surface(L)[1]); continue
    s_ = arc(L); ok_ = np.r_[True, np.diff(s_) > 1e-6]; L = L[ok_]; s_ = s_[ok_]; G[nm_] = L; u = np.arange(0, s_[-1], .5); q = np.stack([np.interp(u, s_, L[:, a]) for a in range(3)], 1); e = np.diff(q, axis=0); e /= np.linalg.norm(e, axis=1, keepdims=True); t = np.degrees(np.arccos(np.clip((e[1:] * e[:-1]).sum(1), -1, 1))); kink[nm_] = (round(float(np.percentile(t, 99)), 2), round(float(t.max()), 2), round(float(s_[-1])), [(q[j + 1].round(0).tolist(), round(float(t[j]), 1)) for j in np.nonzero(t > 3)[0][:: max(1, (t > 3).sum() // 6)]], int((t > 3).sum())); dp.append(pq.on_surface(L[:: 3])[1])
dp = np.concatenate(dp); print("ghidaj-piesa: medie %.3f max %.3f m" % (dp.mean(), dp.max()))
print("franger (p99, max, lungime):"); [print("  ", k, v) for k, v in kink.items()]; print(json.dumps(SEG))
Z = np.load(P + "nt_ref_toate.npz", allow_pickle=True); rv = Z["R005_146_C__v"].astype(float); rf = Z["R005_146_C__f"]; ref = trimesh.Trimesh(rv * [-1, 1, 1], rf[:, ::-1], process=False); half = trimesh.Trimesh(rv * [-1, 1, 1], rf, process=False); a_, _ = trimesh.sample.sample_surface(ref, 40000); b_, _ = trimesh.sample.sample_surface(m, 40000); da = KD(b_).query(a_)[0]; db = KD(a_).query(b_)[0]; print("referinta->piesa medie %.2f p95 %.2f max %.1f; piesa->referinta medie %.2f p95 %.2f max %.1f" % (da.mean(), np.percentile(da, 95), da.max(), db.mean(), np.percentile(db, 95), db.max()))
old = np.load("/home/adrian/Documents/Andromeda/2026-10-29-imbinari/piese/nt/p/146.npz"); om = trimesh.Trimesh(old["v"], old["f"], process=False); ob, _ = trimesh.sample.sample_surface(om, 40000); oa = KD(ob).query(a_)[0]; oc = KD(a_).query(ob)[0]; print("vechea piesa: referinta->piesa medie %.2f p95 %.2f; piesa->referinta medie %.2f p95 %.2f" % (oa.mean(), np.percentile(oa, 95), oc.mean(), np.percentile(oc, 95)))
np.savez(os.path.join(OUT, "146.npz"), v=m.vertices.astype(np.float32), f=m.faces.astype(np.int32), uv=(m.vertices[:, :2] / 4720.0 + .5).astype(np.float32), mat="Material_8", central=True)
GA = {}
for k, L in G.items(): GA[k + "_D"] = L.astype(np.float32); GA[k + "_S"] = (L * [-1, 1, 1]).astype(np.float32)
np.savez(os.path.join(OUT, "146_g.npz"), **GA); np.savez(os.path.join(OUT, "146_ref_S.npz"), v=rv, f=rf)
