# Guides for the front arm (asked: brat_fata_D/S redone with the guide method - guides next to it, confirmed, then the
# surfaces). Right arm (ship coordinates): its centre line walked along the tube (each step the section across the current
# direction, the next point = that section's box centre - robust for the open C of the mouth); tip -> PS, then the tip itself
# from a walk out of the PS end. The clean spine = a chain of constant-curvature pieces (straight runs / arcs), each in its
# own plane, tangent to the next (a bent bar), fitted by least squares to the walked line.
# Usage: python ghid_brat_fata.py <arms npz (brat_fata_D__v/__f, ship coords)> <out.npz> ; env BUC=s1,s2,... (piece ends, m)
import sys, os, numpy as np, trimesh
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares
Z = np.load(sys.argv[1]); OUT = sys.argv[2]; e = lambda k, d: os.environ.get(k, d)
t = trimesh.Trimesh(Z["brat_fata_D__v"], Z["brat_fata_D__f"], process=True)
def walk(p, tg, ST=6, n=1000):
    cen = [p]
    for _ in range(n):
        q = p + ST * tg; s = t.section(plane_origin=q, plane_normal=tg)
        if s is None: break
        P = [s.vertices[k.points] for k in s.entities]; P = [a for a in P if np.linalg.norm(a.mean(0) - q) < 250]
        if not P: break
        P = np.vstack(P); c = 0.5 * (P.min(0) + P.max(0))
        if np.linalg.norm(c - p) < 1: break
        tn = (c - p) / np.linalg.norm(c - p); tg = 0.6 * tg + 0.4 * tn; tg /= np.linalg.norm(tg); p = c; cen.append(p)
    return np.array(cen)
s0 = t.section(plane_origin=[0, 1300, 0], plane_normal=[0, 1, 0]); w = walk(s0.vertices.mean(0), np.array([0, -1.0, 0]))
i = int(np.argmin(w[:, 1])); back = w[:i + 1][::-1]; tip = w[i:]; tip = tip[tip[:, 1] > back[-1, 1] + 6]   # PS -> y 1300, then on to the tip
c = np.vstack([back, tip]); c = np.c_[[gaussian_filter1d(c[:, k], 3, mode="nearest") for k in range(3)]].T
d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]; u = np.arange(0, d[-1], 2.0)
RL = np.c_[[np.interp(u, d, c[:, k]) for k in range(3)]].T
CUT = float(e("CUT_PS", "48")); RL = RL[u >= CUT]; u = u[u >= CUT] - CUT          # the walk hooks in the wide funnel at the PS end
def chain2(P0, a0, pieces, ds=1.0):                                         # 2D bent bar: (signed curvature, length) pieces, tangent
    P = np.array(P0, float); a = a0; pts = [P.copy()]
    for kap, L in pieces:
        n_ = max(int(np.ceil(L / ds)), 1); h = L / n_
        for _ in range(n_):
            if abs(kap) < 1e-9: P = P + h * np.array([np.cos(a), np.sin(a)])
            else: P = P + (np.array([np.sin(a + kap * h) - np.sin(a), np.cos(a) - np.cos(a + kap * h)])) / kap; a += kap * h
            pts.append(P.copy())
    return np.array(pts)
def fit2(R2, cuts, first_straight=True, last_straight=False, kmax=0.03, a0fix=None):                                   # straight runs + tangent arcs through the 2D line R2
    d2 = np.r_[0, np.cumsum(np.linalg.norm(np.diff(R2, axis=0), axis=1))]; ends = list(cuts) + [d2[-1]]
    a0 = np.arctan2(*(R2[min(8, len(R2) - 1)] - R2[0])[::-1]) if a0fix is None else a0fix; n_ = len(ends); L0 = np.diff(np.r_[0, ends])
    def res(x):
        Q = chain2(R2[0], x[0], list(zip(x[1:n_ + 1], x[n_ + 1:])), 4.0); dq = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
        Q = np.c_[[np.interp(np.linspace(0, dq[-1], 400), dq, Q[:, k]) for k in range(2)]].T; D2 = np.linalg.norm(R2[::3, None] - Q[None], axis=2)
        return np.r_[D2.min(1), D2.min(0), 3 * np.linalg.norm(Q[-1] - R2[-1])]
    kap0 = []                                                              # first guess: each stretch's mean turning
    tg = np.unwrap(np.arctan2(*np.gradient(R2, axis=0).T[::-1]))
    for lo_, hi_ in zip(np.r_[0, ends[:-1]], ends):
        m = (d2 >= lo_) & (d2 <= hi_); kap0.append((tg[m][-1] - tg[m][0]) / max(hi_ - lo_, 1))
    if first_straight: kap0[0] = 0.0
    x0 = np.r_[a0, np.clip(kap0, -kmax, kmax), L0]; lo = np.r_[a0 - 0.5, np.full(n_, -kmax), 0.6 * L0]; hi = np.r_[a0 + 0.5, np.full(n_, kmax), 1.4 * L0]
    if first_straight: lo[1], hi[1] = -1e-7, 1e-7
    if a0fix is not None: lo[0], hi[0] = a0fix - 1e-7, a0fix + 1e-7         # the start direction given (tangent to a line before)
    if last_straight: lo[n_], hi[n_] = -1e-7, 1e-7; x0[n_] = 0.0
    x = least_squares(res, np.clip(x0, lo + 1e-9, hi - 1e-9), bounds=(lo, hi), x_scale=np.r_[1, np.full(n_, 1e-3), L0]).x
    Q = chain2(R2[0], x[0], list(zip(x[1:n_ + 1], x[n_ + 1:])), 0.5); dv = np.min(np.linalg.norm(R2[:, None] - Q[None], axis=2), axis=1)
    return Q, list(zip(x[1:n_ + 1], x[n_ + 1:])), dv
desc = lambda pc: ", ".join("drept %.0f" % L if abs(k) < 1 / 8000 else "arc R %.0f %s %.0f" % (1 / abs(k), "st" if k > 0 else "dr", L) for k, L in pc)
# plan view (x, y), then the profile: z against the length along the plan line
PL, pcs_p, dv_p = fit2(RL[:, :2], [float(q) for q in e("BUC_SUS", "60,600,1330").split(",")])
dpl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(PL, axis=0), axis=1))]
sr = np.array([dpl[np.argmin(np.linalg.norm(PL - p, axis=1))] for p in RL[:, :2]])   # each walked point's place along the plan line
o_ = np.argsort(sr); PR2 = np.c_[sr[o_], RL[o_, 2]]
PRc, pcs_z, dv_z = fit2(PR2, [float(q) for q in e("BUC_PROFIL", "100,450,1350").split(",")])
zc = np.interp(dpl, PRc[:, 0], PRc[:, 1]); kz_ = (PRc[-1, 1] - PRc[-2, 1]) / max(PRc[-1, 0] - PRc[-2, 0], 1e-9)
zc = np.where(dpl > PRc[-1, 0], PRc[-1, 1] + (dpl - PRc[-1, 0]) * kz_, zc); SP = np.c_[PL, zc]   # the profile carried straight past its end
EXT = float(e("EXT_PS", "110")); t0 = SP[5] - SP[0]; t0 /= np.linalg.norm(t0)                  # the first straight run carried back into
SP = np.vstack([SP[0] - np.outer(np.arange(EXT, 0, -1.0), t0), SP])                            # the funnel, up to the PS-side mouth
print("SPINARE prelungita %.0f m spre PS pana la %s" % (EXT, SP[0].round(0)))
print("PLAN (sus): %s; fata de real medie %.1f, max %.1f m" % (desc(pcs_p), dv_p.mean(), dv_p.max()))
print("PROFIL (z pe lungimea din plan): %s; fata de real medie %.1f, max %.1f m" % (desc(pcs_z), dv_z.mean(), dv_z.max()))
dev = np.min(np.linalg.norm(RL[:, None] - SP[None], axis=2), axis=1)
print("SPINARE REALA: %.0f m, din %s pana la varf %s" % (u[-1], RL[0].round(0), RL[-1].round(0)))
print("SPINARE CURATA fata de cea reala: medie %.1f m, 95%% %.1f, max %.1f m (la s %.0f)" % (dev.mean(), np.percentile(dev, 95), dev.max(), u[np.argmax(dev)]))
# sections across the clean spine every PAS m: the real cut, a clean ellipse fitted to it (direct conic fit - works on the open
# C of the mouth too); the open part between the lips noted (the cut's free ends)
dS = np.r_[0, np.cumsum(np.linalg.norm(np.diff(SP, axis=0), axis=1))]; TS = np.gradient(SP, axis=0); TS /= np.linalg.norm(TS, axis=1)[:, None]
def frame(i):
    E1 = np.cross(TS[i], [0, 0, 1.0]); E1 /= np.linalg.norm(E1); return E1, np.cross(E1, TS[i])
def ellipse_fit(Q):                                                        # Fitzgibbon direct ellipse fit -> centre, radii, angle
    x_, y_ = Q[:, 0], Q[:, 1]; D = np.c_[x_ * x_, x_ * y_, y_ * y_, x_, y_, np.ones(len(x_))]; Sm = D.T @ D
    Cm = np.zeros((6, 6)); Cm[0, 2] = Cm[2, 0] = 2; Cm[1, 1] = -1
    w_, v_ = np.linalg.eig(np.linalg.solve(Sm + 1e-9 * np.eye(6), Cm)); a = np.real(v_[:, np.argmax(np.real(w_))])
    A, B, C_, Dd, Ee, F = a; M = np.array([[A, B / 2], [B / 2, C_]]); c = np.linalg.solve(2 * M, [-Dd, -Ee])
    k = c @ M @ c - F; w2, v2 = np.linalg.eigh(M); r = np.sqrt(np.abs(k / w2)); return c, r, np.arctan2(v2[1, 0], v2[0, 0])
PAS = float(e("PAS", "40")); st = []
for s_ in np.arange(PAS / 2, dS[-1] - 10, PAS):
    i = int(np.searchsorted(dS, s_)); p_ = SP[i]; E1, E2 = frame(i); sec = t.section(plane_origin=p_, plane_normal=TS[i])
    if sec is None: continue
    ents = [sec.vertices[k.points] for k in sec.entities]; ents = [q for q in ents if np.min(np.linalg.norm(q - p_, axis=1)) < 200]
    if not ents: continue
    Pt = np.vstack(ents); Q = np.c_[(Pt - p_) @ E1, (Pt - p_) @ E2]; c, r, an = ellipse_fit(Q)
    free = [q[[0, -1]] for q in ents if np.linalg.norm(q[0] - q[-1]) > 1]   # open cut = the mouth: its two ends are the lips
    st.append(dict(s=s_, i=i, c=c, r=r, an=an, open=len(free) > 0, lips=np.vstack(free) if free else None, Q=Q))
    print("SECT %4.0f m: centru %+6.1f %+6.1f, raze %5.1f x %5.1f, unghi %4.0f, %s" % (s_, *c, *r, np.degrees(an) % 180, "DESCHISA (gura)" if free else "inchisa"))
# the mouth's free edge (one loop): upper lip (slit tip -> PS corner), the PS-side U (a near-vertical plane), lower lip back
ed = t.edges_sorted; uq, cn = np.unique(ed, axis=0, return_counts=True); bd = uq[cn == 1]; nb = {}
for a_, b_ in bd: nb.setdefault(a_, []).append(b_); nb.setdefault(b_, []).append(a_)
lp = [bd[0][0]]; prev = None
while True:
    nx = [q for q in nb[lp[-1]] if q != prev]; prev = lp[-1]
    if not nx or nx[0] == lp[0]: break
    lp.append(nx[0])
ML = t.vertices[lp]; XPS = float(e("X_PS", "135")); YPS = float(e("Y_PS", "195"))
isps = (ML[:, 0] < XPS) & (ML[:, 1] < YPS); it = int(np.argmax(ML[:, 1])); ML = np.roll(ML, -it, axis=0); isps = np.roll(isps, -it)   # start at the slit tip
k1 = int(np.argmax(isps)); k2 = len(ML) - int(np.argmax(isps[::-1]))          # the PS block = k1..k2-1
up_raw, ps_raw, lo_raw = ML[:k1 + 1], ML[k1:k2], np.vstack([ML[k2 - 1:], ML[:1]])[::-1]   # both lips run slit tip -> PS
sof = lambda P: dS[np.argmin(np.linalg.norm(SP[None] - P[:, None], axis=2), axis=1)]      # place along the clean spine
s_tip = min(sof(up_raw[:1])[0], sof(lo_raw[:1])[0]); s_ps = max(sof(up_raw[-1:])[0], sof(lo_raw[-1:])[0]) if False else 0.0
def as_fn(P, sg):                                                          # lip as a function of s on the grid sg (monotone part)
    sp_ = sof(P); o_ = np.argsort(sp_); sp_, P = sp_[o_], P[o_]; keep = np.r_[True, np.diff(sp_) > 1e-6]
    return np.c_[[np.interp(sg, sp_[keep], P[keep, k]) for k in range(3)]].T
s_lo = max(sof(up_raw[-1:])[0], sof(lo_raw[-1:])[0]); sg = np.arange(s_lo, s_tip, 1.0)
UP, LO = as_fn(up_raw, sg), as_fn(lo_raw, sg); SM = float(e("SM_BUZE", "8"))
UP = np.c_[[gaussian_filter1d(UP[:, k], SM, mode="nearest") for k in range(3)]].T; LO = np.c_[[gaussian_filter1d(LO[:, k], SM, mode="nearest") for k in range(3)]].T
MID = (UP + LO) / 2; G = UP - LO; LJ = float(e("U_FANTA", "60"))           # the slit's end: a round U (half-gap ~ sqrt of the distance)
j0 = int(np.searchsorted(sg, s_tip - LJ)); g0 = G[j0]; ss = np.clip((s_tip - sg) / LJ, 0, 1)
G = np.where((sg > s_tip - LJ)[:, None], g0[None] * np.sqrt(ss)[:, None], G)
MID = np.c_[[gaussian_filter1d(MID[:, k], 2 * SM, mode="nearest") for k in range(3)]].T
UPc, LOc = MID + G / 2, MID - G / 2                                       # both meet at the slit's end
def cuts_for(Ltot, step, ends=0.0, end_step=None):                         # piece ends every step m, denser near both ends (the bulbs)
    c = list(np.arange(step, Ltot - step / 2, step)); end_step = end_step or float(e("CAPETE_PAS", "200"))
    if ends: c += list(np.arange(end_step, ends, end_step)) + list(np.arange(Ltot - ends, Ltot - end_step / 2, end_step))
    c = np.unique(np.round(c)); return [q for q in c if 10 < q < Ltot - 10]
def along(PLc, X2):                                                        # place of 2D points along a 2D line (arc length)
    dq = np.r_[0, np.cumsum(np.linalg.norm(np.diff(PLc, axis=0), axis=1))]; return dq[np.argmin(np.linalg.norm(PLc[None] - X2[:, None], axis=2), axis=1)], dq
def at(PLc, dq, sv):                                                       # point at arc length sv (carried straight past the ends)
    t0, t1 = (PLc[1] - PLc[0]) / max(dq[1], 1e-9), (PLc[-1] - PLc[-2]) / max(dq[-1] - dq[-2], 1e-9)
    X = np.c_[[np.interp(sv, dq, PLc[:, k]) for k in range(PLc.shape[1])]].T
    X[sv < 0] = PLc[0] + np.outer(sv[sv < 0], t0); X[sv > dq[-1]] = PLc[-1] + np.outer(sv[sv > dq[-1]] - dq[-1], t1); return X
def curat_pp(L3, step_p, step_z, ends=0.0, a0p=None, a0z=None):                                # a 3D line made clean: straight runs + tangent arcs seen from
    d3 = np.sum(np.linalg.norm(np.diff(L3[:, :2], axis=0), axis=1))        # above, and again on its profile (z along the plan line)
    PLc, pc1, dv1 = fit2(L3[:, :2], cuts_for(d3, step_p, ends), False, a0fix=a0p); sl, dq = along(PLc, L3[:, :2]); o_ = np.argsort(sl)
    PRc, pc2, dv2 = fit2(np.c_[sl[o_], L3[o_, 2]], cuts_for(sl.max() - sl.min(), step_z, ends), False, a0fix=a0z)
    zq = np.interp(dq, PRc[:, 0], PRc[:, 1]); k1_ = (PRc[-1, 1] - PRc[-2, 1]) / max(PRc[-1, 0] - PRc[-2, 0], 1e-9); k0_ = (PRc[1, 1] - PRc[0, 1]) / max(PRc[1, 0] - PRc[0, 0], 1e-9)
    zq = np.where(dq > PRc[-1, 0], PRc[-1, 1] + (dq - PRc[-1, 0]) * k1_, np.where(dq < PRc[0, 0], PRc[0, 1] + (dq - PRc[0, 0]) * k0_, zq))   # carried straight past the profile's ends
    X = np.c_[PLc, zq]; dv = np.min(np.linalg.norm(L3[:, None] - X[None], axis=2), axis=1); return X, dv, pc1, pc2
def u_curat(A, B, step, RU, stepB=None, kmax=0.03):                        # two edges A, B (2D, open end -> towards their meeting) made clean
    FA, pa, da_ = fit2(A, cuts_for(np.sum(np.linalg.norm(np.diff(A, axis=0), axis=1)), step), False, True, kmax)   # (last piece straight),
    FB, pb, db_ = fit2(B, cuts_for(np.sum(np.linalg.norm(np.diff(B, axis=0), axis=1)), stepB or step), False, True, kmax)   # joined by one arc of
    dA = FA[-1] - FA[-3]; dA /= np.linalg.norm(dA); dB = FB[-1] - FB[-3]; dB /= np.linalg.norm(dB)          # radius RU tangent to both
    t_, u_ = np.linalg.solve(np.c_[dA, -dB], FB[-1] - FA[-1]); X = FA[-1] + t_ * dA                           # (a rounded V: the U)
    th_ = np.arccos(np.clip(dA @ dB, -1, 1)); RU = min(RU, DMAXU * np.tan(th_ / 2)); dd = RU / np.tan(th_ / 2)   # th_ = the V's opening angle
    # (a narrow V: the arc shrinks so its tangent points stay within DMAXU m of the meeting point)
    TA, TB = X - dA * dd, X - dB * dd; bis = -(dA + dB); bis /= np.linalg.norm(bis); cc = X + bis * RU / np.sin(th_ / 2)
    def trim(F, d_, T_):
        k_ = (F - T_) @ d_ < 0; F = F[k_]; return np.vstack([F, T_]) if np.linalg.norm(F[-1] - T_) > 1e-6 else F
    FA, FB = trim(FA, dA, TA), trim(FB, dB, TB)
    if RU <= 0: return np.vstack([FA, FB[::-1][1:]]), pa, pb, np.r_[da_, db_], np.degrees(th_)   # RU 0: a sharp V at the meeting point
    a0, a1 = np.arctan2(*(TA - cc)[::-1]), np.arctan2(*(TB - cc)[::-1]); da = (a1 - a0 + np.pi) % (2 * np.pi) - np.pi
    arc = cc + RU * np.c_[np.cos(a0 + np.linspace(0, 1, 60) * da), np.sin(a0 + np.linspace(0, 1, 60) * da)]
    return np.vstack([FA, arc[1:-1], FB[::-1]]), pa, pb, np.r_[da_, db_], np.degrees(th_)
# lips: seen from above ONE line (both lips on it, from the PS corner to the slit's end), on the profile lower lip and upper lip
# clean, meeting at the slit's end in a sharp V (their last straight runs' crossing)
DMAXU = float(e("U_TANGENTA_MAX", "60")); SB = float(e("PAS_BUZE", "150")); RUF = float(e("R_V_FANTA", "0")); RUN = float(e("R_U_NAS", "15"))
up_s, lo_s = up_raw, lo_raw                                                # raw: the clean fit does the smoothing, the corners stay put
def by_len(P_, n=600):
    d_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P_, axis=0), axis=1))]; return np.c_[[np.interp(np.linspace(0, d_[-1], n), d_, P_[:, k]) for k in range(P_.shape[1])]].T
U_, L_ = by_len(up_s[::-1]), by_len(lo_s[::-1])                            # PS corner -> slit's end, same number of points
PLB, pcb, dvb = fit2(((U_ + L_) / 2)[:, :2], cuts_for(np.sum(np.linalg.norm(np.diff(((U_ + L_) / 2)[:, :2], axis=0), axis=1)), SB), False)
sl_u, dqb = along(PLB, U_[:, :2]); sl_l, _ = along(PLB, L_[:, :2])
PRB, pzl, pzu, dvz, thf = u_curat(np.c_[sl_l, L_[:, 2]], np.c_[sl_u, U_[:, 2]], SB, RUF)
buze = np.c_[at(PLB, dqb, PRB[:, 0]), PRB[:, 1]]; ib = int(np.argmax(PRB[:, 0])); sbz = sof(buze)
def by_s(P_, sp_):
    o_ = np.argsort(sp_); return np.c_[[np.interp(sg, sp_[o_], P_[o_, k]) for k in range(3)]].T
LOc, UPc = by_s(buze[:ib + 1], sbz[:ib + 1]), by_s(buze[ib:][::-1], sbz[ib:][::-1])
print("BUZE: de sus o singura linie (%s; fata de real medie %.1f, max %.1f m); profil jos (%s) / sus (%s), unite la capatul fantei in V (racord R %.0f; deschidere %.0f grd); abatere medie %.1f, max %.1f m" % (
    desc(pcb), dvb.mean(), dvb.max(), desc(pzl), desc(pzu), RUF, thf, dvz.mean(), dvz.max()))
# the PS-side U: in its own plane; upper edge and lower edge clean, joined at the nose (y ~ -84) by one arc; ends on the lips
c_ps = ps_raw.mean(0); _, _, Vp = np.linalg.svd(ps_raw - c_ps); npl = Vp[2]; b1, b2 = Vp[0], Vp[1]
to2 = lambda X: np.c_[(X - c_ps) @ b1, (X - c_ps) @ b2]
dbz = np.r_[0, np.cumsum(np.linalg.norm(np.diff(buze, axis=0), axis=1))]   # the lips' PS ends eased into that plane over 30 m, so the
sm_ = lambda w: w ** 2 * (3 - 2 * w); wa_, wb_ = np.clip(1 - dbz / 30.0, 0, 1), np.clip(1 - (dbz[-1] - dbz) / 30.0, 0, 1)   # U lies in it
buze = buze - np.outer(sm_(wa_) * ((buze[0] - c_ps) @ npl) + sm_(wb_) * ((buze[-1] - c_ps) @ npl), npl)
psr = by_len(ps_raw, 600); pss = np.c_[[gaussian_filter1d(psr[:, k], SM, mode="nearest") for k in range(3)]].T
w_ = np.linspace(0, 1, len(pss))[:, None]; pss += (1 - w_) * (psr[0] - pss[0]) + w_ * (psr[-1] - pss[-1])   # smoothed, ends kept
Q2 = to2(pss); inose_ = int(np.argmin(pss[:, 1]))
Q2[0], Q2[-1] = to2(buze[-1:])[0], to2(buze[:1])[0]; inose = inose_                       # the nose = the U's farthest point back
A_, B_ = Q2[:inose + 1], Q2[inose:][::-1]; NAS = float(e("NAS_LIBER", "25"))  # upper edge (corner -> nose), lower edge (corner -> nose)
okA = np.linalg.norm(A_ - Q2[inose], axis=1) > NAS; okB = np.linalg.norm(B_ - Q2[inose], axis=1) > NAS   # the nose itself left to the arc
def line_dev(E, ok):                                                       # best straight run from the edge's corner: direction, deviation
    d_ = np.linalg.svd(E[ok] - E[0])[2][0]; d_ *= np.sign(d_ @ (Q2[inose] - E[0])); r_ = E[ok] - E[0]; return d_, np.abs(r_ @ np.array([-d_[1], d_[0]])).max()
(dA_, eA), (dB_, eB) = line_dev(A_, okA), line_dev(B_, okB); SWAP = eB < eA      # the straighter edge = the straight run, the other = the arc
S_, K_, okK, dA = (B_, A_, okA, dB_) if SWAP else (A_, B_, okB, dA_)
def circ3(p1, p2, p3):                                                      # the circle through three points
    A = 2 * np.array([p2 - p1, p3 - p1]); c_ = np.linalg.solve(A, [p2 @ p2 - p1 @ p1, p3 @ p3 - p1 @ p1]); return c_, np.linalg.norm(p1 - c_)
Kk = K_[okK]; nA = np.array([-dA[1], dA[0]]); nA *= np.sign(nA @ (K_[len(K_) // 2] - S_[0]))   # the line's normal towards the curved edge
far = Kk[np.argmax((Kk - S_[0]) @ nA)]                                     # the curved edge's deepest point (from the line)
C0, R0 = circ3(K_[0], far, Kk[-1])                                         # one arc through its corner, its deepest point, its nose end
tN = (Q2[inose] - S_[0]) @ dA; ts = np.linspace(0, 1.3 * tN, 6000)         # nose: arc of radius RUN tangent to the line, inside the circle
gv = np.array([np.linalg.norm(S_[0] + dA * t_ + nA * RUN - C0) - (R0 - RUN) for t_ in ts]); rt = np.where(np.sign(gv[:-1]) != np.sign(gv[1:]))[0]
tt = ts[rt[np.argmin(np.abs(ts[rt] - tN))]] if len(rt) else ts[np.argmin(np.abs(gv))]
cn = S_[0] + dA * tt + nA * RUN; TL = S_[0] + dA * tt; TC = C0 + (cn - C0) / np.linalg.norm(cn - C0) * R0
ang = lambda P_, c_: np.arctan2(P_[1] - c_[1], P_[0] - c_[0])
def arc2(c_, r_, p0, p1, n=80, longway=False):
    a0, a1 = ang(p0, c_), ang(p1, c_); da = (a1 - a0 + np.pi) % (2 * np.pi) - np.pi
    if longway: da -= np.sign(da) * 2 * np.pi
    return c_ + r_ * np.c_[np.cos(a0 + np.linspace(0, 1, n) * da), np.sin(a0 + np.linspace(0, 1, n) * da)]
arcN = arc2(cn, RUN, TL, TC); arcL = arc2(cn, RUN, TL, TC, longway=True)  # the nose arc on the outer side (towards the real nose)
if (arcL[40] - cn) @ dA > (arcN[40] - cn) @ dA: arcN = arcL
PSc = np.vstack([np.linspace(S_[0], TL, 200)[:-1], arcN[:-1], arc2(C0, R0, TC, K_[0], 200)])
if SWAP: PSc = PSc[::-1]                                                   # always from the A end (upper lip's corner) to the B end
thn = 0.0; dvps = np.min(np.linalg.norm(Q2[:, None] - PSc[None], axis=2), axis=1)
pp1 = [(0.0, np.linalg.norm(TL - S_[0]))]; pp2 = [(1 / R0, R0 * abs((ang(K_[0], C0) - ang(TC, C0) + np.pi) % (2 * np.pi) - np.pi))]
PSU = c_ps + np.outer(PSc[:, 0], b1) + np.outer(PSc[:, 1], b2); gap_ps = (np.linalg.norm(PSU[0] - buze[-1]), np.linalg.norm(PSU[-1] - buze[0]))
print("GURA PS: in planul ei, marginea dreapta (%s) si cea in arc (%s), unite la nas de un arc R %.0f (%.0f); fata de real medie %.1f, max %.1f m; capetele fata de buze %.1f / %.1f m" % (
    desc(pp1), desc(pp2), RUN, thn, dvps.mean(), dvps.max(), *gap_ps))
devps = np.abs((ps_raw - c_ps) @ npl)
print("GURA: buze (jos -> U la capatul fantei, s %.0f -> sus) %.0f m, netezite %.0f m; U-ul fantei pe ultimii %.0f m; marginea spre PS in planul ei (abatere %.1f m max)" % (
    s_tip, np.sum(np.linalg.norm(np.diff(buze, axis=0), axis=1)), SM, LJ, devps.max()))
out = {"spinare_brat_fata_D": SP, "_spinare_reala_D": RL, "buze_gura_brat_fata_D": buze, "contur_gura_PS_brat_fata_D": PSU}
# the clean sections: ellipse parameters (major/minor, angle of the major, centre) smoothed along s; in the mouth the arc
# between the lips left open (on the side away from the real cut's gap)
P_ = []
for q in st:
    r_ = np.sort(q["r"])[::-1]; an = q["an"] + (np.pi / 2 if q["r"][0] < q["r"][1] else 0); P_.append([q["s"], *q["c"], *r_, an])
P_ = np.array(P_); P_[:, 5] = np.unwrap(2 * P_[:, 5]) / 2; SE = float(e("SM_SECT", "1.5"))
TIP = float(e("S_BULB", "1500")); mb = P_[:, 0] <= TIP                       # the tip's bulb: each section's own fit (no smoothing across it)
for k in range(1, 6): P_[mb, k] = gaussian_filter1d(P_[mb, k], SE, mode="nearest")
th = np.linspace(0, 2 * np.pi, 361)[:-1]
SGN = np.sign((SP[len(SP) // 2] - c_ps) @ npl); side = lambda X: ((X - c_ps) @ npl) * SGN   # > 0 on the arm's side of the PS-side U's plane
def lip_cross(p0, n0):                                                          # the lips crossing the station's plane: (upper, lower) or None
    sd = (buze - p0) @ n0; cx = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    XP = [buze[j] + (buze[j + 1] - buze[j]) * sd[j] / (sd[j] - sd[j + 1]) for j in cx]; XP = [w for w in XP if np.linalg.norm(w - p0) < 250]
    if len(XP) < 2: return None
    XP = sorted(XP, key=lambda w: np.linalg.norm(w - p0))[:2]; return sorted(XP, key=lambda w: -w[2])
def to_plane(L, arc=False):                                                # a line's PS end brought exactly onto the PS-side U's plane:
    sd = side(L)                                                           # cut where it crosses it, or carried on to it (straight, or arc=True:
    if arc and sd[0] > 0:                                                  # with the same bend - curvature seen from above and slope - as the
        dl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]; j = int(np.searchsorted(dl, 40.0))   # line's first 40 m)
        t0 = L[0, :2] - L[1, :2]; t0 /= np.linalg.norm(t0); t1 = L[j - 1, :2] - L[j, :2]; t1 /= np.linalg.norm(t1)
        kap = np.arctan2(t1[0] * t0[1] - t1[1] * t0[0], t1 @ t0) / max(np.sum(np.linalg.norm(np.diff(L[:j, :2], axis=0), axis=1)), 1e-6)
        dz = (L[0, 2] - L[j, 2]) / max(np.sum(np.linalg.norm(np.diff(L[:j, :2], axis=0), axis=1)), 1e-6); P = L[0].copy(); a_ = np.arctan2(t0[1], t0[0]); ext_ = []
        for _ in range(3000):
            a_ += kap; P = P + np.r_[np.cos(a_), np.sin(a_), dz]; ext_.append(P.copy())
            if side(P[None])[0] <= 0: break
        ext_ = np.array(ext_); q0, q1 = (ext_[-2] if len(ext_) > 1 else L[0]), ext_[-1]; s0_, s1_ = side(np.array([q0, q1]))
        ext_[-1] = q0 + (q1 - q0) * s0_ / (s0_ - s1_); return np.vstack([ext_[::-1], L])
    if sd[0] < 0:
        j = int(np.argmax(sd >= 0)); P0_ = L[j - 1] + (L[j] - L[j - 1]) * sd[j - 1] / (sd[j - 1] - sd[j])
        if np.linalg.norm(L[j] - P0_) < 0.5: j += 1                          # no near-duplicate point next to the cut
        return np.vstack([P0_, L[j:]])
    t_ = L[0] - L[1]; t_ /= np.linalg.norm(t_); d_ = sd[0] / -((t_ @ npl) * SGN)
    return np.vstack([L[0] + np.outer(np.arange(np.ceil(d_), 0, -1.0) / np.ceil(d_) * d_, t_)[:-1] if d_ > 1 else np.empty((0, 3)), L]) if d_ > 0 else L
NE = "contur_exterior_brat_fata_D"; NI = "contur_interior_brat_fata_D"
# FIRST the interior, the spine and the exterior, in the same plane (asked: these three set first, the rest adjusted to them):
# every 2 m along the spine (and exactly at every station), in the section's plane, the horizontal line through the spine point
# (E1) - the exterior / interior where it meets the section's ellipse outwards / inwards (so both lie ON every section; along the
# mouth on the full ellipse, in the opening); the ellipse parameters through a cubic spline between the stations, the spine's
# point and frame interpolated exactly (no jitter); all three end on the PS-side U's plane
from scipy.interpolate import CubicSpline
oP = np.argsort(P_[:, 0]); CSP = [CubicSpline(P_[oP, 0], P_[oP, k]) for k in range(1, 6)]; thd = np.linspace(0, 2 * np.pi, 3601)
def cut_x(s_):                                                             # the ellipse's two crossings of its horizontal axis (E2 = 0)
    c0, c1, ra, rb, an = (f(s_) for f in CSP); Rm = np.array([[np.cos(an), -np.sin(an)], [np.sin(an), np.cos(an)]])
    E = np.array([c0, c1]) + np.c_[ra * np.cos(thd), rb * np.sin(thd)] @ Rm.T; y = E[:, 1]; k = np.where(np.sign(y[:-1]) != np.sign(y[1:]))[0]
    xs = E[k, 0] + (E[k + 1, 0] - E[k, 0]) * y[k] / (y[k] - y[k + 1]); return xs.max(), xs.min()
def frame_at(s_):                                                          # the spine point and frame at exactly s_ (interpolated, no jitter)
    p_ = np.array([np.interp(s_, dS, SP[:, k]) for k in range(3)]); t_ = np.array([np.interp(s_, dS, TS[:, k]) for k in range(3)]); t_ /= np.linalg.norm(t_)
    E1 = np.cross(t_, [0, 0, 1.0]); E1 /= np.linalg.norm(E1); return p_, E1, np.cross(E1, t_)
sd_ = np.unique(np.r_[np.arange(P_[0, 0], P_[-1, 0], 2.0), P_[:, 0]]); X0_ = np.array([cut_x(s_) for s_ in sd_])   # (xe, xi) along the arm
SL = float(e("NETEZ_LATURI", "30"))                                         # the green lines smoothed a little: their distances across (xe,
XS_ = np.array([[np.sum(np.exp(-0.5 * ((sd_ - s0) / SL) ** 2) * X0_[:, k]) / np.sum(np.exp(-0.5 * ((sd_ - s0) / SL) ** 2)) for k in (0, 1)] for s0 in sd_]) if SL > 0 else X0_
def keep_bend(XS_, col=1, nm="INTERIOR"):                                                         # the interior keeps its bend's direction (asked): near each end,
    def curv(xi_):                                                         # where, seen from above, its curvature turns the other way, its
        P = np.array([frame_at(s_)[0] + frame_at(s_)[1] * x_ for s_, x_ in zip(sd_, xi_)]); t_ = np.gradient(P[:, :2], axis=0)   # distance
        a_ = np.unwrap(np.arctan2(t_[:, 1], t_[:, 0])); return gaussian_filter1d(np.gradient(a_) / np.linalg.norm(t_, axis=1), 3), P   # across
    xi_ = XS_[:, col].copy(); k_, P_i = curv(xi_); inside = side(P_i) > 0     # (xi) goes on with the same slope - straight on the spine's
    W_PS, W_V = float(e("CURBA_FEREASTRA_PS", "250")), float(e("CURBA_FEREASTRA_VARF", "450")); MG = float(e("CURBA_MARJA", "16"))   # straight
    s_in0 = sd_[np.argmax(inside)]; mid = (sd_ > s_in0 + W_PS) & (sd_ < sd_[-1] - W_V); sg_ = np.sign(np.median(k_[mid]))   # first run
    bad_ps = np.where(inside & (sd_ < s_in0 + W_PS) & (np.sign(k_) != sg_))[0]; bad_v = np.where((sd_ > sd_[-1] - W_V) & (np.sign(k_) != sg_))[0]
    s_ps, s_v = sd_[0], sd_[-1]
    if len(bad_ps):
        s_ps = sd_[bad_ps.max()] + MG; j = int(np.searchsorted(sd_, s_ps)); sl_ = (xi_[j + 3] - xi_[j]) / (sd_[j + 3] - sd_[j]); xi_[:j] = xi_[j] + (sd_[:j] - sd_[j]) * sl_
    if len(bad_v):
        s_v = sd_[bad_v.min()] - MG; j = int(np.searchsorted(sd_, s_v)); sl_ = (xi_[j] - xi_[j - 3]) / (sd_[j] - sd_[j - 3]); xi_[j:] = xi_[j] + (sd_[j:] - sd_[j]) * sl_
    k2, P2 = curv(xi_); ins2 = side(P2) > 0
    print("%s pastreaza sensul curbei: drept la PS pana la s %.0f, drept spre varf de la s %.0f; schimbari de sens ramase %d; mutat max %.1f m" % (
        nm, s_ps, s_v, int(np.sum(np.diff(np.sign(k2[ins2])) != 0)), np.abs(xi_ - XS_[:, col]).max()))
    XS_ = XS_.copy(); XS_[:, col] = xi_; return XS_
XS_ = keep_bend(XS_)
SLE = float(e("NETEZ_EXTERIOR", "60"))                                     # the exterior smoothed more (its bend one way, steady)
if SLE > SL: XS_[:, 0] = [np.sum(np.exp(-0.5 * ((sd_ - s0) / SLE) ** 2) * X0_[:, 0]) / np.sum(np.exp(-0.5 * ((sd_ - s0) / SLE) ** 2)) for s0 in sd_]
XS_ = keep_bend(XS_, 0, "EXTERIOR")
ext, inn = [], []                                                           # xi) smoothed along s - so they stay in the spine's plane
for s_, (xe, xi) in zip(sd_, XS_):
    p_, E1, E2 = frame_at(s_); ext.append(p_ + E1 * xe); inn.append(p_ + E1 * xi)
out[NE], out[NI] = np.array(ext), np.array(inn)
print("VERZI netezite %.0f m: exteriorul mutat max %.1f m, interiorul max %.1f m (in acelasi plan cu spinarea)" % (SL, np.abs(XS_[:, 0] - X0_[:, 0]).max(), np.abs(XS_[:, 1] - X0_[:, 1]).max()))
def to_green(s_, E):                                                       # a section's ellipse stretched across (E1) so it passes through
    xe0, xi0 = np.interp(s_, sd_, X0_[:, 0]), np.interp(s_, sd_, X0_[:, 1])   # the smoothed green points (the red adjusted to the green)
    xe1, xi1 = np.interp(s_, sd_, XS_[:, 0]), np.interp(s_, sd_, XS_[:, 1])
    E = E.copy(); E[:, 0] = xi1 + (E[:, 0] - xi0) * (xe1 - xi1) / (xe0 - xi0); return E
for nm_ in ("spinare_brat_fata_D", NI, NE):
    L0_ = out[nm_]; out[nm_] = to_plane(L0_, arc=(nm_ == NE))
    print("CAPAT PS %s: pe planul gurii (abatere %.2f m), %+.0f m fata de inainte" % (nm_.split("_")[0] + "_" + nm_.split("_")[1], abs(side(out[nm_][:1])[0]),
          np.sum(np.linalg.norm(np.diff(out[nm_], axis=0), axis=1)) - np.sum(np.linalg.norm(np.diff(L0_, axis=0), axis=1))))
# THEN the lips adjusted to the interior: seen from above they lie on the interior's line (PS -> their V), their V on the
# interior itself (at the V's old place along the spine); their heights kept, eased over the last LIPS_V m so both meet there;
# their PS ends (the corners) where the interior meets the PS-side U's plane, kept at their own heights, in that plane
IN_ = out[NI]; s_in = sof(IN_); apex0 = buze[ib].copy(); s_V = sof(apex0[None])[0]
jV = int(np.argmin(np.abs(s_in - s_V))); IV = IN_[:jV + 1]; QV = IN_[jV]   # the interior from the PS plane to the V; the new V
d2v = np.r_[0, np.cumsum(np.linalg.norm(np.diff(IV[:, :2], axis=0), axis=1))]; LB = float(e("LIPS_V", "150"))
def lip_new(part):                                                         # one lip (PS corner -> V) moved: plan onto the interior, by
    dp = np.r_[0, np.cumsum(np.linalg.norm(np.diff(part[:, :2], axis=0), axis=1))]; f_ = dp / dp[-1]   # the same fraction of its length
    xy = np.c_[[np.interp(f_ * d2v[-1], d2v, IV[:, k]) for k in range(2)]].T
    w_ = sm_(np.clip((dp - (dp[-1] - LB)) / LB, 0, 1)); z_ = part[:, 2] + w_ * (QV[2] - part[-1, 2])
    return np.c_[xy, z_]
lo_n, up_n = lip_new(buze[:ib + 1]), lip_new(buze[ib:][::-1]); buze_old = buze.copy()
buze = np.vstack([lo_n, up_n[::-1][1:]]); buze[ib] = QV
def one_arc(part, zref):                                                   # each lip's profile (height along its plan length) = ONE arc from
    sp = np.r_[0, np.cumsum(np.linalg.norm(np.diff(part[:, :2], axis=0), axis=1))]   # its corner to the V (bend one way, constant),
    A2_, B2_ = np.array([sp[0], zref[0]]), np.array([sp[-1], part[-1, 2]]); c_ = np.linalg.norm(B2_ - A2_); m_ = (A2_ + B2_) / 2   # closest to
    nr = np.array([-(B2_ - A2_)[1], (B2_ - A2_)[0]]) / c_; best = None     # its original heights
    for h in np.r_[np.linspace(-150, -0.5, 600), np.linspace(0.5, 150, 600)]:
        R_ = (c_ * c_ / 4 + h * h) / (2 * h); C_ = m_ + nr * (h - R_); zz = C_[1] + np.sign(h) * np.sign(nr[1]) * np.sqrt(np.maximum(R_ * R_ - (sp - C_[0]) ** 2, 0))
        dv = np.abs(zz - zref).max()
        if best is None or dv < best[0]: best = (dv, zz, abs(R_))
    return np.c_[part[:, :2], best[1]], best
lo_a, ba = one_arc(buze[:ib + 1], buze[:ib + 1, 2]); up_a, bb = one_arc(buze[ib:][::-1], buze[ib:][::-1, 2])   # (to their heights brought to the V)
buze = np.vstack([lo_a, up_a[::-1][1:]]); buze[ib] = QV
for jj in (0, -1): buze[jj] = buze[jj] - ((buze[jj] - c_ps) @ npl) * npl   # the corners exactly on the PS-side U's plane
print("BUZE un singur arc pe profil: jos R %.0f (abatere max %.1f m), sus R %.0f (abatere max %.1f m)" % (ba[2], ba[0], bb[2], bb[0]))
A_[0], B_[0] = to2(buze[-1:])[0], to2(buze[:1])[0]                         # the PS-side U starts from the new corners
dmv = np.min(np.linalg.norm(buze[:, None] - buze_old[None], axis=2), axis=1)
out["buze_gura_brat_fata_D"] = buze
print("BUZE DUPA INTERIOR: de sus pe linia interiorului (PS -> V), V-ul pe interior (mutat %.1f m: %s -> %s), inaltimile pastrate (trecere pe ultimii %.0f m); mutare medie %.1f, max %.1f m" % (
    np.linalg.norm(QV - apex0), apex0.round(0), QV.round(0), LB, dmv.mean(), dmv.max()))
for k, (q, pr) in enumerate(zip(st, P_)):
    i = q["i"]; E1, E2 = frame(i); c, ra, rb, an = pr[1:3], pr[3], pr[4], pr[5]
    if side(SP[i]) < 0: continue                                           # beyond the PS-side U: no section there
    Rm = np.array([[np.cos(an), -np.sin(an)], [np.sin(an), np.cos(an)]]); E = c + (np.c_[ra * np.cos(th), rb * np.sin(th)] @ Rm.T)
    p_s, E1, E2 = frame_at(q["s"]); E = to_green(q["s"], E); X = p_s + np.outer(E[:, 0], E1) + np.outer(E[:, 1], E2)   # (exact frame)
    A2 = None
    LX = lip_cross(p_s, np.cross(E2, E1)) if q["s"] <= s_tip + PAS else None; SNAP = LX is not None
    if SNAP: A2 = np.array([[(w - p_s) @ E1, (w - p_s) @ E2] for w in LX])   # open between the lips, its ends exactly on them
    elif q["s"] < sg[0]:                                                   # in the funnel: open where the plane crosses the PS-side U
        sd = (PSU - p_s) @ np.cross(E2, E1); cx = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
        if len(cx) >= 2:
            XP = [PSU[j] + (PSU[j + 1] - PSU[j]) * sd[j] / (sd[j] - sd[j + 1]) for j in cx]
            XP = sorted(XP, key=lambda w: -np.linalg.norm(w - p_s))[:2]; A2 = np.array([[(w - p_s) @ E1, (w - p_s) @ E2] for w in XP])
        if (A2 is None or np.linalg.norm(A2[0] - A2[1]) < 5) and q["open"]:   # plane almost parallel to the U: the real cut's free ends
            fe = q["lips"]; fe = fe[np.argsort(-np.linalg.norm(fe - fe.mean(0), axis=1))][:2]; A2 = np.array([[(w - p_s) @ E1, (w - p_s) @ E2] for w in fe])
    if A2 is not None:
        aE = np.arctan2(*((E - c) @ Rm)[:, ::-1].T * np.array([[1 / rb], [1 / ra]]))
        aL = np.arctan2(*(((A2 - c) @ Rm) * [1 / ra, 1 / rb])[:, ::-1].T)
        gap = np.arctan2(*((q["Q"] - c) @ Rm * [1 / ra, 1 / rb])[:, ::-1].T)   # where the real cut has material
        a1, a2 = sorted(aL); inside = (aE > a1) & (aE < a2); mat = ((gap > a1) & (gap < a2)).mean()
        keep = inside if mat > 0.5 else ~inside; ix = np.where(keep)[0]
        if len(ix) and not keep.all():
            brk = np.where(np.diff(ix) > 1)[0]; ix = np.roll(ix, -(brk[0] + 1)) if len(brk) else ix
            X = X[ix]
            if SNAP:                                                       # the arc's ends moved onto the lips; each end's move fades to 0
                Y = np.c_[(X - p_s) @ E1, (X - p_s) @ E2]; j0_ = int(np.argmin(np.linalg.norm(A2 - Y[0], axis=1)))   # at the exterior point,
                je = int(np.argmin(np.abs(Y[:, 1]) - 1e3 * (Y[:, 0] > 0)))  # which stays on contur_exterior (the back of the section)
                n_ = len(Y); wa_ = np.zeros(n_); wb_ = np.zeros(n_)
                if je > 0: wa_[:je + 1] = sm_(1 - np.arange(je + 1) / je)
                if je < n_ - 1: wb_[je:] = sm_(np.arange(n_ - je) / (n_ - 1 - je))
                Y = Y + np.outer(wa_, A2[j0_] - Y[0]) + np.outer(wb_, A2[1 - j0_] - Y[-1])
                X = p_s + np.outer(Y[:, 0], E1) + np.outer(Y[:, 1], E2)
        out["sectiune_brat_fata_D_%02d" % k] = X
    else: out["sectiune_brat_fata_D_%02d" % k] = np.vstack([X, X[:1]])
# the PS-side U longer, its nose reaching the exterior line's end (on its plane): the straight edge from its corner through that
# point, the arc through its corner, its deepest point and that point, the nose rounded R RUN there; all in the one plane
E2 = to2(out[NE][:1])[0]
def psu_to(T2):                                                            # the U with its straight edge and arc meeting at T2, rounded R RUN
    dE = T2 - S_[0]; dE /= np.linalg.norm(dE); nE_ = np.array([-dE[1], dE[0]]); nE_ *= np.sign(nE_ @ (K_[len(K_) // 2] - S_[0]))
    far2 = Kk[np.argmax((Kk - S_[0]) @ nE_)]; C1, R1 = circ3(K_[0], far2, T2); tE = np.linalg.norm(T2 - S_[0]); ts = np.linspace(0.3 * tE, tE, 6000)
    gv = np.array([np.linalg.norm(S_[0] + dE * t_ + nE_ * RUN - C1) - (R1 - RUN) for t_ in ts]); rt = np.where(np.sign(gv[:-1]) != np.sign(gv[1:]))[0]
    tt = ts[rt[np.argmin(np.abs(ts[rt] - tE))]] if len(rt) else ts[np.argmin(np.abs(gv))]
    cn = S_[0] + dE * tt + nE_ * RUN; TL = S_[0] + dE * tt; TC = C1 + (cn - C1) / np.linalg.norm(cn - C1) * R1
    arcN = arc2(cn, RUN, TL, TC); arcL = arc2(cn, RUN, TL, TC, longway=True)
    if (arcL[40] - cn) @ dE > (arcN[40] - cn) @ dE: arcN = arcL
    PSc = np.vstack([np.linspace(S_[0], TL, 200)[:-1], arcN[:-1], arc2(C1, R1, TC, K_[0], 200)]); return PSc, R1, TL, dE
T2 = E2.copy()
for _ in range(6):                                                         # the meeting point moved on until the rounded nose's tip IS the
    PSc, R1, TL, dE = psu_to(T2); tip_ = PSc[np.argmax(PSc @ dE)]; T2 = T2 + (E2 - tip_)   # exterior line's end
PSc, R1, TL, dE = psu_to(T2)
if SWAP: PSc = PSc[::-1]
out["contur_gura_PS_brat_fata_D"] = PSU = c_ps + np.outer(PSc[:, 0], b1) + np.outer(PSc[:, 1], b2)
print("GURA PS PRELUNGITA pana la exterior: dreapta %.0f m, arc R %.0f, nas R %.0f; nasul la %.1f m de capatul exteriorului; in plan (abatere %.3f m); capetele pe buze %.2f / %.2f m" % (
    np.linalg.norm(TL - S_[0]), R1, RUN, np.min(np.linalg.norm(PSU - out[NE][0], axis=1)), np.abs((PSU - c_ps) @ npl).max(),
    np.linalg.norm(PSU[0] - buze[-1]), np.linalg.norm(PSU[-1] - buze[0])))
print("SECTIUNI: %d elipse curate la %.0f m (netezite pe %.1f statii), deschise intre buze pe s %.0f..%.0f" % (len(st), PAS, SE, sg[0], s_tip))
for kk in list(out):
    if not kk.startswith("_"): out[kk.replace("_D", "_S")] = out[kk] * [-1, 1, 1]
np.save(OUT.replace(".npz", "_statii.npy"), st, allow_pickle=True)
np.savez(OUT, **out)
