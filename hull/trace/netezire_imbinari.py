# Smooth surfaces and no visible edge between the rear arms and the PS (asked: "netezește suprafețele; singura muchie vizibilă
# rămasă e între brațe și PS"). 1) Tangent blend at the arm's mouth: at each mouth vertex the arm's direction going back
# (u_a) is turned into the PS's direction carried across the seam (u_p); the arm's vertices s m behind the mouth move by
# (u_p - u_a) * s (1 - s/L)^2 - mouth fixed, same tangent as the PS there, nothing changes past L. 2) Taubin smoothing
# (lambda 0.5 / mu -0.53) only where earlier steps deformed the pieces (displacement vs the reference export > 0.05 m, grown by
# a few rings) plus the new blend band; everything outside stays fixed. D done, S = mirror (same vertex order); the PS whole.
# Usage: python netezire_imbinari.py <pieces_now.npz> <pieces_before_edits.npz> <out.npz> ; env RAC_L=60 TAUBIN=20
import sys, os, numpy as np
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree
N = np.load(sys.argv[1]); B = np.load(sys.argv[2]); OUT = sys.argv[3]; MX = -1700.0
L = float(os.environ.get("RAC_L", "60")); IT = int(os.environ.get("TAUBIN", "20"))
def adj(f, n):
    E = np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]; A = coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
    A.data[:] = 1; return A
def taubin(v, f, move, it):
    A = adj(f, len(v)); deg = np.asarray(A.sum(1)).ravel(); v = v.copy()
    for _ in range(it):
        for lam in (0.5, -0.53):
            d = (A @ v) / deg[:, None] - v; v[move] += lam * d[move]
    return v
def grow(mask, f, n, k):
    A = adj(f, n)
    for _ in range(k): mask = mask | ((A @ mask.astype(float)) > 0)
    return mask
def rough(v, f, zone):                                   # 95th percentile of the angle between neighbouring faces in a zone
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); fn /= np.linalg.norm(fn, axis=1)[:, None] + 1e-12
    E = np.r_[np.c_[f[:, 0], f[:, 1]], np.c_[f[:, 1], f[:, 2]], np.c_[f[:, 2], f[:, 0]]]; fi = np.tile(np.arange(len(f)), 3)
    k = np.sort(E, 1); o = np.lexsort((k[:, 1], k[:, 0])); k, fi = k[o], fi[o]; same = np.all(k[1:] == k[:-1], 1)
    a, b = fi[:-1][same], fi[1:][same]; inz = zone[f[a]].any(1)
    ang = np.degrees(np.arccos(np.clip((fn[a[inz]] * fn[b[inz]]).sum(1), -1, 1))); return np.percentile(ang, 95) if len(ang) else 0
out = {}
# 1) arm mouth blend (D)
av, af = N["brat_spate_D__v"].astype(float), N["brat_spate_D__f"]; pv = N["PS__v"].astype(float)
E = np.sort(np.r_[af[:, [0, 1]], af[:, [1, 2]], af[:, [2, 0]]], 1); E, c = np.unique(E, axis=0, return_counts=True)
rim = np.unique(E[c == 1]); rim = rim[av[rim, 1] > -60]; y0 = av[rim, 1].mean()
ba = (av[:, 1] < y0 - 7) & (av[:, 1] > y0 - 13); bp = (pv[:, 1] > y0 + 7) & (pv[:, 1] < y0 + 13)
ta, tp = cKDTree(av[ba][:, [0, 2]]), cKDTree(pv[bp][:, [0, 2]])
ua = av[ba][ta.query(av[rim][:, [0, 2]])[1]] - av[rim]; ua /= np.linalg.norm(ua, axis=1)[:, None]
up = -(pv[bp][tp.query(av[rim][:, [0, 2]])[1]] - av[rim]); up /= np.linalg.norm(up, axis=1)[:, None]
dl = up - ua; cr = cKDTree(av[rim][:, [0, 2]])
for _ in range(3): dl = np.array([dl[cr.query_ball_point(p, 12)].mean(0) for p in av[rim][:, [0, 2]]])   # smoothed round the mouth
cos0 = np.degrees(np.arccos(np.clip((ua * up).sum(1), -1, 1)))
s = np.abs(av[:, 1] - y0) / np.maximum(np.abs(ua[:, 1]).mean(), 0.3); band = (av[:, 1] < y0 + 0.5) & (s < L)
j = cr.query(av[band][:, [0, 2]])[1]; h = s[band] * (1 - s[band] / L) ** 2
AV = av.copy(); AV[band] += dl[j] * h[:, None]; AV[rim] = av[rim]
print("RACORD gura brat_spate: unghi brat/PS inainte median %.0f max %.0f grd; %d varfuri pe %.0f m" % (np.median(cos0), cos0.max(), band.sum(), L))
# 1b) the PS's last PS_L m before the mouth straightened: its surface ran round into its back cap (a groove at the seam);
#     outer-side vertices near the mouth's ring (seen along y) go onto the straight line from the PS a PS_L m ahead to the ring
PL = float(os.environ.get("PS_L", "0")); pf = N["PS__f"]   # 0 = off (12 m flipped 293 PS faces, worse seam)
pnn = np.zeros_like(pv); fnn = np.cross(pv[pf[:, 1]] - pv[pf[:, 0]], pv[pf[:, 2]] - pv[pf[:, 0]])
for k_ in range(3): np.add.at(pnn, pf[:, k_], fnn)
pnn /= np.linalg.norm(pnn, axis=1)[:, None] + 1e-12
PV = pv.copy(); qb = (pv[:, 1] > y0 + PL - 1.5) & (pv[:, 1] < y0 + PL + 1.5); tq = cKDTree(pv[qb][:, [0, 2]]) if PL > 0 else None
for side in ((1, -1) if PL > 0 else ()):            # both mouths (right arm, its mirror on the left)
    rr = av[rim].copy(); rr[:, 0] = MX + side * (rr[:, 0] - MX); trr = cKDTree(rr[:, [0, 2]])
    near = (pv[:, 1] >= y0 - 0.5) & (pv[:, 1] < y0 + PL) & (pnn[:, 1] > -0.85) & (np.sign(pv[:, 0] - MX) == side)
    dd, jr = trr.query(pv[near][:, [0, 2]]); ok_ = dd < 8
    idx = np.where(near)[0][ok_]; r_ = rr[jr[ok_]]; q_ = pv[qb][tq.query(r_[:, [0, 2]])[1]]
    t_ = np.clip((y0 + PL - pv[idx, 1]) / PL, 0, 1); tgt = q_ + (r_ - q_) * t_[:, None]
    w_ = np.clip(1 - dd[ok_] / 8, 0, 1); w_ = w_ * w_ * (3 - 2 * w_)
    PV[idx] = pv[idx] + (tgt - pv[idx]) * w_[:, None]
if PL > 0: print("PS indreptat pe ultimii %.0f m inainte de gura: %d varfuri, deplasare max %.2f m" % (PL, (np.linalg.norm(PV - pv, axis=1) > 0.01).sum(), np.linalg.norm(PV - pv, axis=1).max()))
pv = PV
# 2) smoothing where deformed (+ the blend band), boundaries fixed
for nm, v, f in (("PS", pv, N["PS__f"]), ("brat_spate_D", AV, af), ("brat_fata_D", N["brat_fata_D__v"].astype(float), N["brat_fata_D__f"])):
    moved = np.linalg.norm(v - B[nm + "__v"].astype(float), axis=1) > 0.05
    zone = grow(moved, f, len(v), 3)
    E2 = np.sort(np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]], 1); E2, c2 = np.unique(E2, axis=0, return_counts=True)
    free = np.zeros(len(v), bool); free[np.unique(E2[c2 == 1])] = True
    move = zone & ~free & grow(zone, f, len(v), 0) & ~(grow(~zone, f, len(v), 1) & zone & False)
    inner = zone & ~grow(~zone, f, len(v), 1)              # keep a fixed ring at the zone's border
    r0 = rough(v, f, zone); V = taubin(v, f, inner & ~free, IT); r1 = rough(V, f, zone)
    print("NETEZIT %-13s zona %6d varfuri: asperitate 95%% %.1f -> %.1f grd, deplasare max %.2f m" % (nm, zone.sum(), r0, r1, np.linalg.norm(V - v, axis=1).max()))
    out[nm] = V
for d_, s_ in (("brat_spate_D", "brat_spate_S"), ("brat_fata_D", "brat_fata_S")):
    S = out[d_].copy(); S[:, 0] = 2 * MX - S[:, 0]; out[s_] = S
# check the crease after
av2 = out["brat_spate_D"]; pv2 = out["PS"]; ta2, tp2 = cKDTree(av2[ba][:, [0, 2]]), cKDTree(pv2[bp][:, [0, 2]])
ua2 = av2[ba][ta2.query(av2[rim][:, [0, 2]])[1]] - av2[rim]; ua2 /= np.linalg.norm(ua2, axis=1)[:, None]
up2 = -(pv2[bp][tp2.query(av2[rim][:, [0, 2]])[1]] - av2[rim]); up2 /= np.linalg.norm(up2, axis=1)[:, None]
a2 = np.degrees(np.arccos(np.clip((ua2 * up2).sum(1), -1, 1))); print("DUPA: unghi brat/PS la gura median %.1f max %.1f grd; gura pe PS: abatere max %.2f m" % (
    np.median(a2), a2.max(), cKDTree(pv2).query(av2[rim])[0].max()))
np.savez(OUT, **out)
