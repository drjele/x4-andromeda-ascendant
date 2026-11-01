# The three band lines refitted to the reference (asked: lucru_brat_fata's bends are smoother and its arm a little more bulged
# outwards; the lines' ends stay where they are). The reference arm turned with the arm (REF_OUT of ghid_brat_fata2.py). Along the
# spine every PAS m, in the plane across it: the band direction d (spine -> our exterior); the targets = the reference's farthest
# points along d near the band's plane (exterior: +d, interior: -d, only after the lips' V - along the mouth the interior is the lips'
# middle and stays) and its real rib centre (spine). Each line then = a least-squares fit on third differences (smooth curvature)
# pulled to its targets with weight MU, its head end (2 stations: position + the head's direction) and the 3 stations before the lobe
# (Y_LOB; position, direction, curvature) fixed; the lobe kept as it is. Right arm computed, the left one mirrored.
# Usage: python trei_din_referinta.py <guides npz> <ref_rot npz> <out npz> ; env MU=1e-6 PAS=4 Y_LOB=1180 BANDA_TOL=4
import sys, os, numpy as np
G = np.load(sys.argv[1]); RF = np.load(sys.argv[2]); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d))
MU, PAS, YL, TOL = e("MU", "1e-6"), e("PAS", "4"), e("Y_LOB", "1180"), e("BANDA_TOL", "4")
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
SP, EX, IN, BZ = (G["%s_brat_fata_D" % k] for k in ("spinare", "contur_exterior", "contur_interior", "buze_gura"))
RV, RC = RF["v"], RF["c"]
iv = int(np.argmax([np.linalg.norm(BZ[i] - BZ[0]) + np.linalg.norm(BZ[i] - BZ[-1]) for i in range(len(BZ))])); VX = BZ[iv]
def cross(L, p, n):
    sd = (L - p) @ n; k = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    if not len(k): return None
    X = L[k] + (L[k + 1] - L[k]) * (sd[k] / (sd[k] - sd[k + 1]))[:, None]; return X[np.argmin(np.linalg.norm(X - p, axis=1))]
dS = arclen(SP); jl = int(np.argmax(SP[:, 1] >= YL)); s_l = dS[jl]
st = np.r_[np.arange(0, s_l, PAS), s_l]; P_, Tn_, Ex_, In_, tE, tI, tC = [], [], [], [], [], [], []
sV = dS[np.argmin(np.linalg.norm(SP - VX, axis=1))]
for s0 in st:
    p = np.array([np.interp(s0, dS, SP[:, k]) for k in range(3)]); i = min(max(int(np.searchsorted(dS, s0)), 1), len(SP) - 2)
    n = SP[i + 1] - SP[i - 1]; n /= np.linalg.norm(n)
    if s0 == 0: p = SP[0]; n = SP[1] - SP[0]; n /= np.linalg.norm(n)
    a, b = cross(EX, p, n), cross(IN, p, n)
    if s0 == 0: a, b = EX[0], IN[0]
    d = (a - p) / np.linalg.norm(a - p); nb = np.cross(n, d); nb /= np.linalg.norm(nb)
    q = RV - p; m = (np.abs(q @ n) < PAS / 2) & (np.abs(q @ nb) < TOL); x = q[m] @ d if m.any() else np.array([])
    tE.append(p + d * x.max() if len(x) and x.max() > 0 else None)
    tI.append(p + d * x.min() if len(x) and x.min() < 0 and s0 > sV + 20 else None)
    mc = np.abs((RC - p) @ n) < 10; tC.append(p + (RC[mc].mean(0) - p) - n * ((RC[mc].mean(0) - p) @ n) if mc.any() else None)
    P_.append(p); Ex_.append(a); In_.append(b)
from scipy.optimize import least_squares
from scipy.interpolate import CubicSpline
NK, KSM, MZ = int(e("NODURI", "9")), e("NETEZ_K", "30"), e("MU_Z", "1e-5")
def fit(cur, tgt, fix0=2, fix1=3, sign=None):
    # top view: the curvature = a cubic spline on NK knots along the line, one sign (sign of the line's mean bend), integrated from the
    # head end (position + direction fixed); the end at the lobe tied (position, direction, curvature); profile: the D3 smoother
    cur = np.array(cur); n = len(cur); T = np.array([t_ if t_ is not None else c_ for t_, c_ in zip(tgt, cur)])
    w = np.array([1.0 if t_ is not None else 0.05 for t_ in tgt]); c2 = cur[:, :2]
    sc = arclen(np.c_[c2, np.zeros(n)]); f = sc / sc[-1]
    th = np.unwrap(np.arctan2(*np.gradient(c2, axis=0).T[::-1])); kc = np.gradient(th) / np.gradient(sc)
    sgn = sign if sign is not None else np.sign(np.mean(kc[n // 10: -n // 10]))
    t0, t1 = th[0], th[-1]; k1 = np.mean(kc[-4:]); kn = np.linspace(0, 1, NK)
    def curve(z):
        L = z[0]; kv = sgn * np.abs(z[1:]); ks = CubicSpline(kn, kv)(f) / L * sc[-1] * 0 + CubicSpline(kn, kv)(f)
        ss = f * L; thv = t0 + np.r_[0, np.cumsum((ks[1:] + ks[:-1]) / 2 * np.diff(ss))]
        xy = c2[0] + np.c_[np.r_[0, np.cumsum((np.cos(thv[1:]) + np.cos(thv[:-1])) / 2 * np.diff(ss))], np.r_[0, np.cumsum((np.sin(thv[1:]) + np.sin(thv[:-1])) / 2 * np.diff(ss))]]
        return xy, thv, ks
    def res(z):
        xy, thv, ks = curve(z); r = [(xy - T[:, :2]).ravel() * np.repeat(np.sqrt(w), 2)]
        r.append(5000 * (xy[-1] - c2[-1])); r.append([800 * (thv[-1] - t1), 2e4 * (ks[-1] - k1)])
        r.append(KSM * 1e3 * np.diff(sgn * np.abs(z[1:]), 2)); return np.concatenate([np.ravel(q) for q in r])
    z0 = np.r_[sc[-1], np.abs(np.interp(kn, f, np.convolve(kc, np.ones(9) / 9, mode="same"))) + 1e-5]
    z = least_squares(res, z0, x_scale="jac", max_nfev=4000).x; xy, thv, ks = curve(z)
    D = np.diff(np.eye(n), 3, axis=0); A = D.T @ D + MU * np.diag(w); fx = np.zeros(n, bool); fx[:fix0] = True; fx[n - fix1:] = True; fr = ~fx
    dn = np.linspace(0, sc[-1], 20 * n); cz = np.c_[np.interp(dn, sc, c2[:, 0]), np.interp(dn, sc, c2[:, 1])]; zd = np.interp(dn, sc, cur[:, 2])
    from scipy.spatial import cKDTree
    z0_ = zd[cKDTree(cz).query(xy)[1]]                                      # (each new point's height = the line's own at its place, from above)
    A = D.T @ D + MZ * np.eye(n); zz = z0_.copy(); zz[fr] = np.linalg.solve(A[np.ix_(fr, fr)], MZ * z0_[fr] - A[np.ix_(fr, fx)] @ cur[fx, 2]); zz[fx] = cur[fx, 2]   # (profile: the line's own, smoothed)
    print("  capatul spre lob: abatere %.2f m, directie %.2f grd" % (np.linalg.norm(xy[-1] - c2[-1]), np.degrees(abs(thv[-1] - t1))))
    X = np.c_[xy, zz]; X[-1] = cur[-1]; return X
def tail(L, p_last):                                                       # the line from the lobe on, as it was
    j = int(np.argmin(np.linalg.norm(L - p_last, axis=1))); return L[j + 1:]
out = {}
NS = fit(P_, tC); out["spinare_brat_fata_D"] = np.vstack([NS, tail(SP, P_[-1])])
NE = fit(Ex_, tE); out["contur_exterior_brat_fata_D"] = np.vstack([NE, tail(EX, Ex_[-1])])
kV = int(np.argmin(np.abs(st - sV)))                                       # interior: along the mouth as it is, after the V refitted
jvi = int(np.argmin(np.linalg.norm(IN - VX, axis=1)))
NI = fit(In_[kV:], tI[kV:], 2, 3); NI[0] = VX
out["contur_interior_brat_fata_D"] = np.vstack([IN[:jvi + 1], NI[1:], tail(IN, In_[-1])])
def bend(L):
    d = arclen(L); u = np.arange(0, d[-1], 2.0); Q = np.c_[[np.interp(u, d, L[:, k]) for k in range(3)]].T; t = np.gradient(Q[:, :2], axis=0)
    k = np.degrees(np.gradient(np.unwrap(np.arctan2(t[:, 1], t[:, 0])))) / 2; k = k[Q[:, 1] < YL]; sg = np.sign(k[np.abs(k) > 0.005])
    return int(np.sum(sg[1:] != sg[:-1]))
for k_, old, tg in (("spinare_brat_fata_D", SP, tC), ("contur_exterior_brat_fata_D", EX, tE), ("contur_interior_brat_fata_D", IN, tI)):
    N = out[k_]; mv = np.min(np.linalg.norm(N[:, None] - old[None], axis=2), axis=1).max()
    T = np.array([t_ for t_ in tg if t_ is not None]); dr = np.min(np.linalg.norm(T[:, None] - N[None], axis=2), axis=1)
    print("%-28s mutata max %.1f m; fata de referinta medie %.1f, max %.1f m (inainte %.1f / %.1f); schimbari de sens (de sus, pana la lob) %d -> %d" % (
        k_, mv, dr.mean(), dr.max(), np.min(np.linalg.norm(T[:, None] - old[None], axis=2), axis=1).mean(),
        np.min(np.linalg.norm(T[:, None] - old[None], axis=2), axis=1).max(), bend(old), bend(N)))
# the three in one band: per spine station, the exterior and interior crossings vs the line through them and the spine
dev = []
for p, n in ((out["spinare_brat_fata_D"][i], None) for i in range(0, len(NS), 5)):
    i = int(np.argmin(np.linalg.norm(out["spinare_brat_fata_D"] - p, axis=1))); L = out["spinare_brat_fata_D"]; i = min(max(i, 1), len(L) - 2)
    n = L[i + 1] - L[i - 1]; n /= np.linalg.norm(n); a, b = cross(out["contur_exterior_brat_fata_D"], p, n), cross(out["contur_interior_brat_fata_D"], p, n)
    if a is not None and b is not None: dev.append(np.linalg.norm(np.cross(b - a, p - a)) / np.linalg.norm(b - a))
print("BANDA: spinarea fata de dreapta interior-exterior medie %.2f, max %.2f m" % (np.mean(dev), np.max(dev)))
for k_ in list(out): out[k_.replace("_D", "_S")] = out[k_] * [-1, 1, 1]
nanify = lambda L: np.array([q if q is not None else [np.nan] * 3 for q in L], float)
I_old = nanify(In_); I_new = I_old.copy(); I_new[kV:] = NI                  # (station by station: the old lines -> the new, for the rest)
out["_kor_spinare_veche"], out["_kor_exterior_vechi"], out["_kor_interior_vechi"] = np.array(P_), np.array(Ex_), I_old
out["_kor_spinare_noua"], out["_kor_exterior_nou"], out["_kor_interior_nou"] = NS, NE, I_new
np.savez(OUT, **out)
