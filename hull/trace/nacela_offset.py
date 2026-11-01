# The nacelle's V point from the width function (asked: seen from above, the distance lips -> nacelle V point = the same function as
# the arm's width exterior -> interior, with an offset; the V point exactly in the plane of the green lines). Per section across the
# spine (stations of latime_liniara.py, the new lines): the V point on the line exterior -> interior carried on past the interior (the
# lips' middle along the mouth), its distance from the lips' middle seen from above = W(s) - W(s_V) (0 at the lips' V, growing as
# the width does); the V kept where all three meet. Ribs redrawn: equal width along the V point's line, light / dark alternating,
# the dark ones bulged RELIEF m outwards (along the band line).
# Usage: python nacela_offset.py <guides npz (already on the new lines)> <trei_linii npz> <out npz> ; env LATIME=5.25 RELIEF=1.0
import sys, os, numpy as np
from scipy.spatial import cKDTree
G = dict(np.load(sys.argv[1])); K = np.load(sys.argv[2]); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d))
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
S1, E1, I1, st, W = K["_kor_spinare_noua"], K["_kor_exterior_nou"], K["_kor_interior_nou"], K["_latime_s"], K["_latime_w"]
T = np.gradient(S1, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
from scipy.ndimage import gaussian_filter1d                             # (the band's direction per station smoothed: its small jitter
UB = I1 - E1; UB /= np.linalg.norm(UB, axis=1)[:, None]                    # grows to metres out at the V point)
UB = np.c_[[gaussian_filter1d(UB[:, k], e("NETEZ_DIR", "6"), mode="nearest") for k in range(3)]].T
UB -= T * np.einsum("ij,ij->i", UB, T)[:, None]; UB /= np.linalg.norm(UB, axis=1)[:, None]
BZ = G["buze_gura_brat_fata_D"]; iv = int(np.argmax([np.linalg.norm(BZ[i] - BZ[0]) + np.linalg.norm(BZ[i] - BZ[-1]) for i in range(len(BZ))]))
VX = BZ[iv]; L1, L2 = BZ[:iv + 1], BZ[iv:][::-1]
def cross(L, p, n):
    sd = (L - p) @ n; k = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    if not len(k):                                                         # (the head: the lips end in its plane)
        j = int(np.argmin(np.abs(sd))); return L[j] if abs(sd[j]) < 1.0 and np.linalg.norm(L[j] - p) < 400 else None
    X = L[k] + (L[k + 1] - L[k]) * (sd[k] / (sd[k] - sd[k + 1]))[:, None]; return X[np.argmin(np.linalg.norm(X - p, axis=1))]
jV = int(np.argmin(np.abs(np.einsum("ij,ij->i", VX - S1, T)) + 1e-3 * np.linalg.norm(S1 - VX, axis=1))); WV = W[jV]
A_, B_, TP = [], [], []
for j in range(jV):
    a, b = cross(L1, S1[j], T[j]), cross(L2, S1[j], T[j])
    if a is None or b is None: continue
    u = I1[j] - E1[j]; u /= np.linalg.norm(u); M = (a + b) / 2; M = E1[j] + u * ((M - E1[j]) @ u)   # (the lips' middle on the band line)
    D = W[j] - WV; t = D / max(np.linalg.norm(u[:2]), 1e-6); A_.append(a); B_.append(b); TP.append(M + u * t)
if e("ROTIRE", "1") > 0:                                                   # (asked again: the lips' own shape turned about the V, seen from
    # above - the lips' middle line rotated about the V's vertical by the angle that puts the head end W(0) - W(V) away; each section's
    # V point = where that rotated line crosses, seen from above, the section's line exterior -> interior; its height from that line)
    Mx = np.array([E1[j] + (I1[j] - E1[j]) / np.linalg.norm(I1[j] - E1[j]) * (((cross(L1, S1[j], T[j]) + cross(L2, S1[j], T[j])) / 2 - E1[j])
                   @ ((I1[j] - E1[j]) / np.linalg.norm(I1[j] - E1[j]))) for j in range(jV) if cross(L1, S1[j], T[j]) is not None and cross(L2, S1[j], T[j]) is not None])
    Jx = [j for j in range(jV) if cross(L1, S1[j], T[j]) is not None and cross(L2, S1[j], T[j]) is not None]
    if Jx[0] != 0: print("  (statia capului fara taieturi de buze: incepe la statia %d)" % Jx[0])
    M2 = np.vstack([Mx[:, :2], VX[:2]]); r0 = M2[0] - VX[:2]; D0 = W[0] - WV
    o2 = (I1[Jx[0]] - E1[Jx[0]])[:2]; o2 /= np.linalg.norm(o2)                # (outwards, seen from above, at the head)
    def rot(a): c_, s_ = np.cos(a), np.sin(a); R = np.array([[c_, -s_], [s_, c_]]); return VX[:2] + (M2 - VX[:2]) @ R.T
    sg = 1.0 if (rot(0.01)[0] - M2[0]) @ o2 > 0 else -1.0
    a_ = sg * np.arcsin(min(D0 / np.linalg.norm(r0), 0.9)); RM = rot(a_)
    for _ in range(20):                                                    # (the head end exactly D0 away, measured across, from above)
        d_ = (RM[0] - M2[0]) @ o2; a_ *= D0 / max(d_, 1e-6); RM = rot(a_)
    TP2 = []
    for jj, j in enumerate(Jx):
        u = I1[j] - E1[j]; u /= np.linalg.norm(u); p2, d2 = I1[j][:2], u[:2]
        best = None
        for k in range(len(RM) - 1):                                       # crossing of the 2D line p2 + l d2 with the rotated polyline
            q, r = RM[k], RM[k + 1] - RM[k]; Mm = np.array([[d2[0], -r[0]], [d2[1], -r[1]]])
            if abs(np.linalg.det(Mm)) < 1e-9: continue
            l, m = np.linalg.solve(Mm, q - p2)
            if 0 <= m <= 1 and (best is None or abs(l) < abs(best)): best = l
        TP2.append(I1[j] + u * (best / max(np.linalg.norm(d2), 1e-9) * np.linalg.norm(d2) / np.linalg.norm(d2) if best is not None else 0) if best is None else I1[j] + u * best)
    TP = np.array(TP2); A_ = np.array([cross(L1, S1[j], T[j]) for j in Jx]); B_ = np.array([cross(L2, S1[j], T[j]) for j in Jx])
    if "_ref_nacela_varf" in K.files and e("LINIAR_CAPAT2", "1") > 0:     # (asked: seen from above the distance V point -> capat2 grows
        RF = K["_ref_nacela_varf"]; sV_ = st[jV]; TQ, num, den = [], 0.0, 0.0    # linearly; its slope from the reference's V points)
        def at_dist(j, M, u, b, D):                                        # the point M + u t (t > 0) at distance D from b, from above
            p2, u2, b2 = M[:2], u[:2], b[:2]; A2 = u2 @ u2; B2 = 2 * u2 @ (p2 - b2); C2 = (p2 - b2) @ (p2 - b2) - D * D
            dsc = max(B2 * B2 - 4 * A2 * C2, 0.0); return M + u * max((-B2 + np.sqrt(dsc)) / (2 * A2), 0.0)
        Ms, Us = [], []
        for jj, j in enumerate(Jx):
            u = UB[j]; M = I1[j] + u * (((A_[jj] + B_[jj]) / 2 - I1[j]) @ u); Ms.append(M); Us.append(u)
            if np.isfinite(RF[j]).all():
                tr = M + u * max((RF[j] - M) @ u, 0.0); dref = np.linalg.norm((tr - B_[jj])[:2])
                x = sV_ - st[j]; num += dref * x; den += x * x
        kL = num / max(den, 1e-9)
        TP = np.array([at_dist(j, Ms[jj], Us[jj], B_[jj], kL * (sV_ - st[j])) for jj, j in enumerate(Jx)])
        for _ in range(int(e("ITER_LINIAR", "0"))):                        # (linear along the V point's own line, from the V: refitted
            xT = np.r_[arclen(np.vstack([TP, VX]))[::-1][1:]]               # with the way along that line)
            num, den = 0.0, 0.0
            for jj, j in enumerate(Jx):
                if np.isfinite(RF[j]).all():
                    tr = Ms[jj] + Us[jj] * max((RF[j] - Ms[jj]) @ Us[jj], 0.0); num += np.linalg.norm((tr - B_[jj])[:2]) * xT[jj]; den += xT[jj] ** 2
            kL = num / max(den, 1e-9); TP = np.array([at_dist(j, Ms[jj], Us[jj], B_[jj], kL * xT[jj]) for jj, j in enumerate(Jx)])
        print("NACELA liniara fata de capat2: distanta de sus = %.4f x (drumul pana la V), %.0f m la cap" % (kL, np.linalg.norm((TP[0] - B_[0])[:2])))
    MUN = e("MU_NACELA", "1e-3")                                           # (clean line: the station-by-station crossings smoothed on
    if MUN > 0:                                                            # third differences, each point put back on its station's line)
        m_ = len(TP); D = np.diff(np.eye(m_), 3, axis=0); Am = D.T @ D + MUN * np.eye(m_); fx = np.zeros(m_, bool); fx[0] = True; fx[-1] = True; fr = ~fx
        TS_ = TP.copy()
        for k in range(3): TS_[fr, k] = np.linalg.solve(Am[np.ix_(fr, fr)], MUN * TP[fr, k] - Am[np.ix_(fr, fx)] @ TP[fx, k])
        for jj, j in enumerate(Jx):
            u = UB[j]; TP[jj] = I1[j] + u * ((TS_[jj] - I1[j]) @ u)
    MZN = e("MU_Z_NACELA", "0")                                            # (asked: clean along Z - the height profile smoothed on its
    if MZN > 0:                                                            # own, each point moved along its band line to that height)
        m_ = len(TP); D = np.diff(np.eye(m_), 3, axis=0); Am = D.T @ D + MZN * np.eye(m_); fx = np.zeros(m_, bool); fx[0] = True; fx[-1] = True; fr = ~fx
        zt = TP[:, 2].copy(); zt[fr] = np.linalg.solve(Am[np.ix_(fr, fr)], MZN * TP[fr, 2] - Am[np.ix_(fr, fx)] @ TP[fx, 2]); mvz = []
        for jj, j in enumerate(Jx):
            u = UB[j]
            if abs(u[2]) > 0.05: t_ = (zt[jj] - TP[jj, 2]) / u[2]; mvz.append(abs(t_)); TP[jj] = TP[jj] + u * t_
        print("NACELA profil Z netezit: varful mutat pe linia benzii max %.2f m" % (max(mvz) if mvz else 0))
    print("NACELA rotita: mijlocul buzelor rotit de sus in jurul V cu %.2f grd (capatul de la cap la %.1f m)" % (np.degrees(abs(a_)), D0))
A_, B_, TP = np.vstack([A_, VX]), np.vstack([B_, VX]), np.vstack([TP, VX])
hk = "sectiune_brat_fata_D_%02d" % int(e("CAP_SECT", "49"))
if hk in G:                                                                # (the three start exactly in the head rib's plane: cut there,
    Hc = G[hk].mean(0); Hn = np.linalg.svd(G[hk] - Hc)[2][2]; Hn *= np.sign((VX - Hc) @ Hn)   # or carried straight on to it)
    def to_head(L):
        sd = (L - Hc) @ Hn
        if sd[0] > 0:
            d = L[0] - L[1]; t = sd[0] / max(-(d @ Hn), 1e-9); return np.vstack([L[0] + d * t, L])
        j = int(np.argmax(sd > 0)); q = L[j - 1] + (L[j] - L[j - 1]) * (-sd[j - 1]) / (sd[j] - sd[j - 1]); return np.vstack([q, L[j:]])
    A_, B_, TP = to_head(A_), to_head(B_), to_head(TP)
    n_ = max(len(A_), len(B_), len(TP))                                    # (same count again: each by its own way head -> V)
    rs = lambda L: np.c_[[np.interp(np.linspace(0, 1, n_), arclen(L) / arclen(L)[-1], L[:, k]) for k in range(3)]].T
    A_, B_, TP = rs(A_), rs(B_), rs(TP)
for k in [k for k in G if "nacela" in k]: G.pop(k)
G["contur_nacela_capat1_D"], G["contur_nacela_varf_D"], G["contur_nacela_capat2_D"] = A_, TP, B_
LAT, REL = e("LATIME", "5.25"), e("RELIEF", "1.0"); dT = arclen(TP); nr = int(dT[-1] // LAT); edg = np.linspace(0, dT[-1], nr + 1)
kd = cKDTree(S1)
at_ = lambda L, x: np.array([np.interp(x, dT, L[:, k]) for k in range(3)])
for i in range(nr):                                                        # (asked: the first rib in the head's plane, then every rib
    x = edg[i]; a_, p_, b_ = at_(A_, x), at_(TP, x), at_(B_, x)             # width along the V point's line towards the V)
    seg = np.vstack([np.linspace(a_, p_, 30)[:-1], np.linspace(p_, b_, 30)])
    if i % 2 == 0 and REL > 0:
        jj = kd.query(p_)[1]; o = I1[jj] - E1[jj]; o /= np.linalg.norm(o); seg = seg + np.outer(np.sin(np.linspace(0, np.pi, len(seg))), o) * REL
    G["nacela_nervura_%s_%03d_D" % ("inchisa" if i % 2 == 0 else "deschisa", i)] = seg
for k in list(G):
    if "nacela" in k and k.endswith("_D"): G[k.replace("_D", "_S")] = G[k] * [-1, 1, 1]
pl = []                                                                    # check: the V point vs the plane of the green lines
for p in TP[:-1]:
    j = int(np.argmin(np.abs(np.einsum("ij,ij->i", p - S1, T)) + 1e-3 * np.linalg.norm(S1 - p, axis=1))); nn = np.cross(T[j], I1[j] - E1[j]); nn /= np.linalg.norm(nn)
    pl.append(abs((p - E1[j]) @ nn))
print("NACELA: varful la W(s) - W(V) de buze (de sus), max %.0f m la cap; fata de planul liniilor verzi medie %.3f, max %.3f m; %d nervuri de %.2f m" % (
    (W[0] - WV), np.mean(pl), np.max(pl), nr, dT[-1] / nr))
np.savez(OUT, **G)
