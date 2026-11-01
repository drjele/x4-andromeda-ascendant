# Front-arm guides rebuilt from the spine (asked: the spine made right - the arm's real middle - and used as the guide for all
# the others; the green lines on the outside of the ribs, at their farthest points; the lips centred on the spine; clean lines,
# the current overall shape). Right arm, ship coordinates:
#  1. spine: from a start spine, cut the original across it every PAS_C m, fit an ellipse to each cut, its centre = the real middle;
#     a clean spine (straight runs + tangent arcs seen from above x the same on its profile) fitted through those centres;
#     repeated ITER times;
#  2. ribs: ellipses centred on the spine (radii + angle of the major axis from the cuts, smoothed along the arm);
#  3. contur_exterior / contur_interior = the two ends of each rib's major axis (its farthest points from the spine, on the rib's
#     outside; spine, interior and exterior on one line in every section);
#  4. lips: symmetric about the major axis on the inner side (half the mouth's opening angle from the original lips, one smooth
#     curve going to 0 at the V, so the V lies on the interior); the open ribs end exactly on them;
#  5. contur_gura_PS: one plane, from the lips' PS ends to the exterior's end (nose rounded R_U_NAS); everything ends on its plane.
# Usage: python ghid_brat_fata2.py <arms npz (brat_fata_D__v/__f, ship coords)> <start guides npz (spinare_brat_fata_D)> <out.npz>
import sys, numpy as np, trimesh
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import CubicSpline
from brat_fata_lib import e, ang, chain2, fit2, ellipse_fit, cuts_for, along, at, by_len, circ3, arc2
Z = np.load(sys.argv[1]); G0 = np.load(sys.argv[2]); OUT = sys.argv[3]
t = trimesh.Trimesh(Z["brat_fata_D__v"], Z["brat_fata_D__f"], process=True)
sm_ = lambda w: w ** 2 * (3 - 2 * w)
def arclen(L): return np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
def frames(SP):                                                            # tangent + horizontal-across + up-ish frame along a line
    TS = np.gradient(SP, axis=0); TS /= np.linalg.norm(TS, axis=1)[:, None]
    E1 = np.cross(TS, [0, 0, 1.0]); E1 /= np.linalg.norm(E1, axis=1)[:, None]; return TS, E1, np.cross(E1, TS)
def cut_fit(p_, T_, E1, E2):                                               # the original cut across the line at p_: ellipse in (E1, E2)
    sec = t.section(plane_origin=p_, plane_normal=T_)
    if sec is None: return None
    P = [sec.vertices[k.points] for k in sec.entities]; P = [q for q in P if np.min(np.linalg.norm(q - p_, axis=1)) < 200]
    if not P: return None
    P = np.vstack(P); Q = np.c_[(P - p_) @ E1, (P - p_) @ E2]
    try: c, r, an = ellipse_fit(Q)
    except Exception: return None
    if not np.all(np.isfinite(np.r_[c, r, an])) or r.max() > 400: return None
    return c, r, an, Q
def clean_spine(C, fr_p, fr_z):                                            # straight runs + tangent arcs seen from above x on the profile
    d2 = arclen(C[:, :2]); PL, pp, dvp = fit2(C[:, :2], [f * d2[-1] for f in fr_p], True, ksign=int(e("SENS_SUS", "1")))   # seen from above: one way
    dq = arclen(PL); sl = dq[np.argmin(np.linalg.norm(PL[None] - C[:, None, :2], axis=2), axis=1)]; o_ = np.argsort(sl)
    PR, pz, dvz = fit2(np.c_[sl[o_], C[o_, 2]], [f * (sl.max() - sl.min()) for f in fr_z], True)
    zc = np.interp(dq, PR[:, 0], PR[:, 1]); k_ = (PR[-1, 1] - PR[-2, 1]) / max(PR[-1, 0] - PR[-2, 0], 1e-9)
    zc = np.where(dq > PR[-1, 0], PR[-1, 1] + (dq - PR[-1, 0]) * k_, zc); SP = np.c_[PL, zc]
    d_ = arclen(SP); u_ = np.arange(0, d_[-1], 1.0); return np.c_[[np.interp(u_, d_, SP[:, k]) for k in range(3)]].T, pp, pz
desc = lambda pc: ", ".join("drept %.0f" % L if abs(k) < 1 / 8000 else "arc R %.0f %s %.0f" % (1 / abs(k), "st" if k > 0 else "dr", L) for k, L in pc)
# ---- 1. the spine = the arm's real middle (iterated)
SP = G0["spinare_brat_fata_D"]; d_ = arclen(SP); u_ = np.arange(0, d_[-1], 1.0); SP = np.c_[[np.interp(u_, d_, SP[:, k]) for k in range(3)]].T
FRP = [float(q) for q in e("FR_SUS", "0.036,0.356,0.79").split(",")]; FRZ = [float(q) for q in e("FR_PROFIL", "0.06,0.27,0.80").split(",")]
PASC, ITER, TIPX = float(e("PAS_C", "20")), int(e("ITER", "8")), float(e("FARA_VARF", "120")); DAMP = float(e("PAS_ITER", "0.5"))
for it in range(ITER):
    dS = arclen(SP); TS, E1s, E2s = frames(SP); C = []; off = []
    for s0 in np.arange(10, dS[-1] - TIPX, PASC):                           # (the very tip - the bulb's end, cut obliquely - left out)
        i = int(np.searchsorted(dS, s0)); f_ = cut_fit(SP[i], TS[i], E1s[i], E2s[i])
        if f_ is None: continue
        c, r, an, Q = f_; C.append(SP[i] + E1s[i] * c[0] + E2s[i] * c[1]); off.append(np.linalg.norm(c))
    C = np.array(C); off = np.array(off); C_raw = C.copy()
    jn = np.argmin(np.linalg.norm(SP[None] - C[:, None], axis=2), axis=1); C = SP[jn] + DAMP * (C - SP[jn])   # half way each round (converges)
    tail = SP[dS > dS[-1] - TIPX][::int(PASC)]; C = np.vstack([C, tail, SP[-1:]])   # the tip kept from the spine so far (no shrinking)
    SPn, pp, pz = clean_spine(C, FRP, FRZ); mv = np.min(np.linalg.norm(SPn[:, None] - SP[None], axis=2), axis=1)
    print("SPINARE iteratia %d: centrele reale fata de spinare medie %.1f, max %.1f m; spinare noua %.0f m (de sus %s; profil %s), mutata max %.1f m" % (
        it + 1, off.mean(), off.max(), arclen(SPn)[-1], desc(pp), desc(pz), mv.max()))
    SP = SPn
vt = t.vertices[::7]; s_end = arclen(SP)[np.argmin(np.linalg.norm(SP[None] - vt[:, None], axis=2), axis=1)].max()   # the arm's own tip
SP = SP[arclen(SP) <= s_end + 1]; print("SPINARE taiata la varful bratului: %.0f m" % arclen(SP)[-1])
dS = arclen(SP); TS, E1s, E2s = frames(SP)
SPX = float(e("SPINARE_PALNIE", "0"))                                    # the spine carried straight on into the funnel (asked: more
if SPX > 0:                                                                # ribs at the open end - its underside looked flat); the output
    SP = np.vstack([SP[0] - np.outer(np.arange(SPX, 0, -1.0), TS[0]), SP]); dS = arclen(SP); TS, E1s, E2s = frames(SP)   # cut at the PS plane
# ---- the head (asked: g_bfs_sectiune_brat_fata_S_49 is the arm's head - its end, nothing past it - and the arm turned so the head is
# perpendicular to the X axis, the other end staying where it is to meet the rest): CAP_S = the head's spine parameter; the head plane
# = the plane across the spine there. At the end everything (guides, band, surface) turned about the head's centre: rigidly up to
# s 0, the turn eased (quintic) to nothing at ROTIRE_LUNG m along the spine - by each point's place along the spine, not its distance
CAPS = float(e("CAP_S", "nan")); CAPS = None if np.isnan(CAPS) else CAPS
if CAPS is not None:
    from scipy.spatial import cKDTree
    C_H = SP[0] + TS[0] * CAPS; T_H = TS[0].copy(); TGT = np.array([np.sign(T_H[0]), 0, 0.0]); K_H = np.cross(T_H, TGT)
    TH_ROT = np.arctan2(np.linalg.norm(K_H), T_H @ TGT); K_H /= np.linalg.norm(K_H); LROT = float(e("ROTIRE_LUNG", "500")); KD_SP = cKDTree(SP)
    def W(P):
        P = np.asarray(P, float); sh = P.shape; Q = P.reshape(-1, 3); ii_ = KD_SP.query(Q)[1]; sq_ = dS[ii_] + np.einsum("ij,ij->i", Q - SP[ii_], TS[ii_])   # (continuous)
        sq_ = np.where((Q - C_H) @ T_H < 0, 0.0, sq_); x_ = np.clip(sq_ / LROT, 0, 1); w_ = 1 - x_ ** 3 * (10 - 15 * x_ + 6 * x_ ** 2)
        a_ = TH_ROT * w_; V_ = Q - C_H; c_, s_ = np.cos(a_)[:, None], np.sin(a_)[:, None]
        R_ = V_ * c_ + np.cross(K_H, V_) * s_ + np.outer(V_ @ K_H, K_H) * (1 - c_); return (C_H + R_).reshape(sh)
    print("CAP la s %.1f: planul capului rotit cu %.1f grd -> perpendicular pe X; rotirea scade la 0 pe %.0f m de spinare" % (CAPS, np.degrees(TH_ROT), LROT))
# ---- the mouth's free edge (one loop): upper lip, the PS-side U, lower lip (as before)
ed = t.edges_sorted; uq, cn = np.unique(ed, axis=0, return_counts=True); bd = uq[cn == 1]; nb = {}
for a_, b_ in bd: nb.setdefault(a_, []).append(b_); nb.setdefault(b_, []).append(a_)
lp = [bd[0][0]]; prev = None
while True:
    nx = [q for q in nb[lp[-1]] if q != prev]; prev = lp[-1]
    if not nx or nx[0] == lp[0]: break
    lp.append(nx[0])
ML = t.vertices[lp]; isps = (ML[:, 0] < float(e("X_PS", "135"))) & (ML[:, 1] < float(e("Y_PS", "195")))
it_ = int(np.argmax(ML[:, 1])); ML = np.roll(ML, -it_, axis=0); isps = np.roll(isps, -it_)
k1 = int(np.argmax(isps)); k2 = len(ML) - int(np.argmax(isps[::-1]))
up_raw, ps_raw, lo_raw = ML[:k1 + 1], ML[k1:k2], np.vstack([ML[k2 - 1:], ML[:1]])[::-1]
c_ps = ps_raw.mean(0); _, _, Vp = np.linalg.svd(ps_raw - c_ps); npl = Vp[2]; b1, b2 = Vp[0], Vp[1]
to2 = lambda X: np.c_[(X - c_ps) @ b1, (X - c_ps) @ b2]
if CAPS is not None: c_ps, npl, b1, b2 = C_H, T_H, E1s[0], E2s[0]      # (every cut at the PS end now at the head plane)
SGN = np.sign((SP[len(SP) // 2] - c_ps) @ npl); side = lambda X: ((X - c_ps) @ npl) * SGN
sof = lambda P: dS[np.argmin(np.linalg.norm(SP[None] - P[:, None], axis=2), axis=1)]
def to_plane(L, arc=False, skip=0.0):                                      # a line's PS end exactly on the PS-side U's plane: cut there,
    if skip > 0 and side(L[:1])[0] > 0: L = L[arclen(L) >= skip]           # (its first skip m left out: the interpolation's end effect)
    sd = side(L)                                                           # or carried on to it (straight, or with its first 40 m's bend)
    if sd[0] < 0:
        j = int(np.argmax(sd >= 0)); P0_ = L[j - 1] + (L[j] - L[j - 1]) * sd[j - 1] / (sd[j - 1] - sd[j])
        if np.linalg.norm(L[j] - P0_) < 0.5: j += 1
        return np.vstack([P0_, L[j:]])
    dl = arclen(L); j = int(np.searchsorted(dl, 40.0)); t0 = L[0, :2] - L[1, :2]; t0 /= np.linalg.norm(t0)
    t1 = L[j - 1, :2] - L[j, :2]; t1 /= np.linalg.norm(t1); lp_ = max(np.sum(np.linalg.norm(np.diff(L[:j, :2], axis=0), axis=1)), 1e-6)
    kap = np.arctan2(t1[0] * t0[1] - t1[1] * t0[0], t1 @ t0) / lp_ if arc else 0.0; dz = (L[0, 2] - L[j, 2]) / lp_
    kap = min(kap, 0.0) if arc else 0.0                                    # (walking back towards the PS: the bend kept one way, or straight)
    P = L[0].copy(); a_ = np.arctan2(t0[1], t0[0]); ext_ = []
    for _ in range(3000):
        a_ += kap; P = P + np.r_[np.cos(a_), np.sin(a_), dz]; ext_.append(P.copy())
        if side(P[None])[0] <= 0: break
    ext_ = np.array(ext_); q0 = ext_[-2] if len(ext_) > 1 else L[0]; q1 = ext_[-1]; s0_, s1_ = side(np.array([q0, q1]))
    ext_[-1] = q0 + (q1 - q0) * s0_ / (s0_ - s1_); return np.vstack([ext_[::-1], L])
# ---- 2. ribs: ellipses centred on the spine; radii + major-axis angle from the cuts, smoothed
PAS = float(e("PAS", "40")); ST = []
for s0 in np.arange(PAS / 2, dS[-1] - 5, PAS / 4):                         # (dense cuts for the parameters, ribs drawn every PAS)
    i = int(np.searchsorted(dS, s0)); f_ = cut_fit(SP[i], TS[i], E1s[i], E2s[i])
    if f_ is None: continue
    c, r, an, Q = f_; an = an + (np.pi / 2 if r[0] < r[1] else 0); ra, rb = r.max(), r.min()
    ST.append([s0, ra, rb, an, c[0], c[1]])
ST = np.array(ST); ST[:, 3] = np.unwrap(2 * ST[:, 3]) / 2
mx = np.cos(ST[:, 3]); ST[mx < 0, 3] += np.pi                              # the major axis' first end on the outer side (+E1)
ST[:, 3] = np.unwrap(ST[:, 3]); SE = float(e("NETEZ_NERVURI", "3"))       # (in station steps of PAS/4)
ST_RAW = ST.copy(); ST = ST[:, :4]                                         # (the cuts as they are, for the tip's bulb)
yb_ = float(e("Y_BULB", "1240")); SB0 = dS[int(np.argmax(SP[:, 1] >= yb_))] if (SP[:, 1] >= yb_).any() else dS[-1]   # where the bulb starts
CSC = [CubicSpline(ST_RAW[:, 0], np.zeros(len(ST_RAW))) for _ in (0, 1)]  # rib centres off the spine (0 except in the bulb)
TIPB = float(e("S_BULB", "1500"))
jb_ = int(np.searchsorted(ST[:, 0], TIPB)); ST[jb_:, 3] = ST[jb_, 3]          # in the tip's bulb the ribs keep their angle (no hook)
for k in (1, 2, 3): ST[:, k] = gaussian_filter1d(ST[:, k], SE, mode="nearest")   # smoothed along the arm
CS = [CubicSpline(ST[:, 0], ST[:, k]) for k in (1, 2, 3)]
def frame_at(s_):
    p_ = np.array([np.interp(s_, dS, SP[:, k]) for k in range(3)]); t_ = np.array([np.interp(s_, dS, TS[:, k]) for k in range(3)]); t_ /= np.linalg.norm(t_)
    E1 = np.cross(t_, [0, 0, 1.0]); E1 /= np.linalg.norm(E1); return p_, E1, np.cross(E1, t_), t_
def ell(s_, tt):                                                            # rib points at parameter tt (0 = the outer major-axis end)
    p_, E1, E2, _ = frame_at(s_); ra, rb, an = (f(s_) for f in CS); x = ra * np.cos(tt); y = rb * np.sin(tt); c0_, c1_ = CSC[0](s_), CSC[1](s_)
    X = np.c_[c0_ + x * np.cos(an) - y * np.sin(an), c1_ + x * np.sin(an) + y * np.cos(an)]; return p_ + np.outer(X[:, 0], E1) + np.outer(X[:, 1], E2)
# ---- 3. the green lines: the major axis' two ends; that axis (its across / up parts, ra cos an, ra sin an) smoothed more and more
# along the arm until neither line changes the direction of its bend seen from above (iterated)
def even(L, st=1.0):                                                       # a line resampled at even steps (st m)
    d_ = arclen(L); u_ = np.r_[np.arange(0, d_[-1], st), d_[-1]]; return np.c_[[np.interp(u_, d_, L[:, k]) for k in range(L.shape[1])]].T
def sens(L):                                                               # direction changes of the bend seen from above (|k| > 1/10 km)
    L = even(L, 2.0); tt_ = np.gradient(L[:, :2], axis=0); a_ = np.unwrap(np.arctan2(tt_[:, 1], tt_[:, 0])); k_ = gaussian_filter1d(np.gradient(a_) / np.linalg.norm(tt_, axis=1), 3)[5:-5]
    sg = np.sign(k_[np.abs(k_) > 1e-4]); return int(np.sum(np.diff(sg) != 0))
sd_ = np.arange(ST[0, 0], ST[-1, 0], 2.0); AX0 = np.c_[ST[:, 1] * np.cos(ST[:, 3]), ST[:, 1] * np.sin(ST[:, 3])]; RB0 = ST[:, 2].copy()
for sg_ in [float(q) for q in e("NETEZ_AXA", "0,3,6,10,15,20,30").split(",")]:
    AX = np.c_[[gaussian_filter1d(AX0[:, k], sg_, mode="nearest") if sg_ > 0 else AX0[:, k] for k in (0, 1)]].T
    ST[:, 1] = np.linalg.norm(AX, axis=1); ST[:, 3] = np.unwrap(np.arctan2(AX[:, 1], AX[:, 0])); ST[:, 2] = np.minimum(gaussian_filter1d(RB0, max(sg_, 1), mode="nearest"), ST[:, 1])
    CS = [CubicSpline(ST[:, 0], ST[:, k]) for k in (1, 2, 3)]
    EXT = np.array([ell(s_, np.array([0.0]))[0] for s_ in sd_]); INT = np.array([ell(s_, np.array([np.pi]))[0] for s_ in sd_])
    EXT_p, INT_p = to_plane(EXT, arc=True, skip=20), to_plane(INT, arc=True, skip=20); ne_, ni_ = sens(EXT_p), sens(INT_p)
    print("VERZI axa netezita pe %.0f m: schimbari de sens exterior %d, interior %d; raza mare fata de taieturi medie %.1f, max %.1f m" % (
        sg_ * PAS / 4, ne_, ni_, np.abs(ST[:, 1] - np.linalg.norm(AX0, axis=1)).mean(), np.abs(ST[:, 1] - np.linalg.norm(AX0, axis=1)).max()))
    if ne_ == 0 and ni_ == 0: break
def kcurv(L):
    tt_ = np.gradient(L[:, :2], axis=0); a_ = np.unwrap(np.arctan2(tt_[:, 1], tt_[:, 0])); return gaussian_filter1d(np.gradient(a_) / np.linalg.norm(tt_, axis=1), 3)
if ne_ or ni_:                                                             # what remains, near the PS end (straight spine, ribs narrowing fast):
    WPS = float(e("VERZI_FEREASTRA_PS", "350")); s_fix = ST[0, 0]          # the axis goes on linearly there -> the green lines straight like
    for L_ in (EXT, INT):                                                  # the spine, then bending the one way
        k_ = kcurv(L_); bad = np.where((sd_ < sd_[0] + WPS) & (k_ < -1e-4))[0]
        if len(bad): s_fix = max(s_fix, sd_[bad.max()] + 20)
    AXs, RBs = AX.copy(), ST[:, 2].copy()
    while True:                                                            # (iterated: the linear part grown 40 m at a time until clean)
        AX = AXs.copy(); j = int(np.searchsorted(ST[:, 0], s_fix)); sl_ = (AX[j + 2] - AX[j]) / (ST[j + 2, 0] - ST[j, 0]); AX[:j] = AX[j] + np.outer(ST[:j, 0] - ST[j, 0], sl_)
        ST[:, 1] = np.linalg.norm(AX, axis=1); ST[:, 3] = np.unwrap(np.arctan2(AX[:, 1], AX[:, 0])); ST[:, 2] = np.minimum(RBs, ST[:, 1])
        CS = [CubicSpline(ST[:, 0], ST[:, k]) for k in (1, 2, 3)]
        EXT = np.array([ell(s_, np.array([0.0]))[0] for s_ in sd_]); INT = np.array([ell(s_, np.array([np.pi]))[0] for s_ in sd_])
        EXT_p, INT_p = to_plane(EXT, arc=True, skip=20), to_plane(INT, arc=True, skip=20); ne_, ni_ = sens(EXT_p), sens(INT_p)
        print("VERZI la capatul PS axa liniara pana la s %.0f: schimbari de sens exterior %d, interior %d" % (s_fix, ne_, ni_))
        if (ne_ == 0 and ni_ == 0) or s_fix > sd_[0] + WPS: break
        s_fix += 40
# the tip's bulb like the original (asked): from SB0 on (eased in over 60 m) the ribs are the original's cuts - their own radii, angle and
# centre (the bulb hangs off the spine), only lightly smoothed; the green lines follow, closing on the arm's real tip
wB = sm_(np.clip((ST[:, 0] - SB0) / 60.0, 0, 1)); g1 = lambda y: gaussian_filter1d(y, float(e("NETEZ_BULB", "1.5")), mode="nearest")
AXr = np.c_[g1(ST_RAW[:, 1] * np.cos(ST_RAW[:, 3])), g1(ST_RAW[:, 1] * np.sin(ST_RAW[:, 3]))]; AXc = np.c_[ST[:, 1] * np.cos(ST[:, 3]), ST[:, 1] * np.sin(ST[:, 3])]
AXb = AXc * (1 - wB[:, None]) + AXr * wB[:, None]; RBb = ST[:, 2] * (1 - wB) + g1(ST_RAW[:, 2]) * wB
ST[:, 1] = np.linalg.norm(AXb, axis=1); ST[:, 3] = np.unwrap(np.arctan2(AXb[:, 1], AXb[:, 0])); ST[:, 2] = np.minimum(RBb, ST[:, 1])
CS = [CubicSpline(ST[:, 0], ST[:, k]) for k in (1, 2, 3)]; CSC = [CubicSpline(ST[:, 0], g1(ST_RAW[:, 4 + k]) * wB) for k in (0, 1)]
TIPV = t.vertices[np.argmax((t.vertices - SP[-1]) @ TS[-1])]               # the arm's real tip
# ---- the MAIN GUIDES ON ONE BAND (asked: contur_interior, spinare, contur_exterior on the same band, clean lines; then the band; then
# the vertebrae): in every section the band = the line through the spine point at angle a(s) (the ribs' major axis); the exterior at
# xe(s) along it, the interior at xi(s) the other way (where that line meets the rib). a, xe, xi smoothed along the arm until the two
# lines bend one way (the bulb exempt); towards the PS carried on straight (linear) and cut at the PS-side U's plane; at the tip xe, xi
# shrink on a circle's profile to the spine's end (a round snout, both lines closing there)
def frame_at(s_, lob=True):                                                # (carried straight on past both ends of the spine; in the end's
    if s_ < 0: p_ = SP[0] + TS[0] * s_; t_ = TS[0].copy()                  # lobe the spine goes down to the ribs' real middle - asked: the
    elif s_ > dS[-1]: p_ = SP[-1] + TS[-1] * (s_ - dS[-1]); t_ = TS[-1].copy()   # spine IS the middle; so the band / vertebrae keep the lobe)
    else:
        p_ = np.array([np.interp(s_, dS, SP[:, k]) for k in range(3)]); t_ = np.array([np.interp(s_, dS, TS[:, k]) for k in range(3)]); t_ /= np.linalg.norm(t_)
    E1 = np.cross(t_, [0, 0, 1.0]); E1 /= np.linalg.norm(E1); E2 = np.cross(E1, t_)
    if lob: p_ = p_ + E1 * CSC[0](min(s_, dS[-1])) + E2 * CSC[1](min(s_, dS[-1]))
    return p_, E1, E2, t_
B0 = []
for s_ in sd_:
    ra, rb, an = (f(s_) for f in CS); c0_, c1_ = 0.0, 0.0; cpar = c0_ * np.cos(an) + c1_ * np.sin(an); cper = -c0_ * np.sin(an) + c1_ * np.cos(an)   # (centre = spine)
    q_ = np.sqrt(max(1 - (cper / rb) ** 2, 0)); B0.append([an, cpar + ra * q_, -(cpar - ra * q_), rb])
B0 = np.array(B0); B0[:, 0] = np.unwrap(B0[:, 0])
def band_lines(B, s_grid):
    P, Ex, In = [], [], []
    for s_, (a_, xe_, xi_) in zip(s_grid, B[:, :3]):
        p_, E1, E2, _ = frame_at(s_); d_ = E1 * np.cos(a_) + E2 * np.sin(a_); P.append(p_); Ex.append(p_ + d_ * xe_); In.append(p_ - d_ * xi_)
    return np.array(P), np.array(Ex), np.array(In)
def sens_upto(L, ymax):                                                    # bend changes seen from above, before the bulb
    return sens(L[L[:, 1] < ymax]) if (L[:, 1] < ymax).sum() > 20 else 0
s_end = dS[-1]; LIN = float(e("BANDA_LINIAR_PS", "120"))
for sg_ in [float(q) for q in e("NETEZ_BANDA", "15,25,40,60,90").split(",")]:   # (in 2 m samples)
    B = np.c_[[gaussian_filter1d(B0[:, k], sg_, mode="nearest") for k in range(4)]].T
    Bh = np.c_[[gaussian_filter1d(B0[:, k], max(sg_, 60), mode="nearest") for k in range(4)]].T   # near the PS (wide band, where the
    wP = sm_(np.clip(1 - (sd_ - sd_[0]) / float(e("BANDA_PS_NETEZ", "300")), 0, 1)); B = B * (1 - wP[:, None]) + Bh * wP[:, None]   # spine turns) smoother
    Bl = np.c_[[gaussian_filter1d(B0[:, k], float(e("NETEZ_LOB", "4")), mode="nearest") for k in range(4)]].T   # the end's lobe kept
    wL = sm_(np.clip((sd_ - SB0) / 60.0, 0, 1)); B = B * (1 - wL[:, None]) + Bl * wL[:, None]                     # (asked), lightly smoothed
    rr_ = (B[:, 1] + B[:, 2]) / 2; jc = int(np.argmin(np.abs(sd_ + rr_ - s_end))); s_c = sd_[jc]; r_ = rr_[jc]   # the cap: s_c + r = the end
    s_lo = float(e("BANDA_START", "-320")); j0 = int(np.searchsorted(sd_, sd_[0] + LIN))
    slope = (B[j0] - B[0]) / (sd_[j0] - sd_[0]); slope[0] = 0.0; slope[3] = 0.0   # (the band's angle kept: straight lines on the straight spine)
    sg_grid = np.r_[np.arange(s_lo, sd_[0], 2.0), sd_[sd_ <= s_c], np.linspace(s_c, s_end, 40)[1:]]
    BG = []
    jL = int(np.searchsorted(sd_, sd_[0] + LIN)); slope = (B[jL + 1] - B[jL - 1]) / (sd_[jL + 1] - sd_[jL - 1])   # tangent to the band there
    for s_ in sg_grid:                                                     # (the first LIN m and beyond: linear, the band's angle kept,
        if s_ < sd_[jL]: BG.append(B[jL] + slope * (s_ - sd_[jL]))       # joined tangent - no S)
        elif s_ <= s_c: BG.append([np.interp(s_, sd_, B[:, k]) for k in range(4)])
        else:
            f_ = np.sqrt(max(1 - ((s_ - s_c) / (s_end - s_c)) ** 2, 0)); BG.append([B[jc, 0], B[jc, 1] * f_, B[jc, 2] * f_, B[jc, 3] * f_])
    BG = np.array(BG); Pl, EXl, INl = band_lines(BG, sg_grid)
    EXT_p, INT_p = to_plane(EXl), to_plane(INl); ne_, ni_ = sens_upto(EXT_p, yb_), sens_upto(INT_p, yb_)
    print("BANDA netezita %.0f m: schimbari de sens exterior %d, interior %d (inainte de bulb); varf rotund raza %.0f m de la s %.0f" % (sg_ * 2, ne_, ni_, r_, s_c))
    if ne_ == 0 and ni_ == 0: break
BAND_S, BAND = sg_grid, BG; APEX = frame_at(s_end)[0]; TIPV = APEX
def bandp(s_): return [np.interp(s_, BAND_S, BAND[:, k]) for k in range(4)]
def ell(s_, tt):                                                           # a vertebra: an ellipse whose major axis lies on the band, from
    p_, E1, E2, _ = frame_at(s_); a_, xe_, xi_, rb_ = bandp(s_); ra_ = (xe_ + xi_) / 2; m_ = (xe_ - xi_) / 2   # the interior to the exterior
    rb_ = min(rb_, ra_); x = ra_ * np.cos(tt); y = rb_ * np.sin(tt)
    X = np.c_[m_ * np.cos(a_) + x * np.cos(a_) - y * np.sin(a_), m_ * np.sin(a_) + x * np.sin(a_) + y * np.cos(a_)]
    return p_ + np.outer(X[:, 0], E1) + np.outer(X[:, 1], E2)
def cap_rows(nu):                                                          # the round snout's rows (for the surface)
    tt = np.linspace(np.pi, 3 * np.pi, nu) % (2 * np.pi); return [ell(s_, tt) for s_ in np.linspace(s_c, s_end, 14)[:-1]]
CAP_RIBS = [np.vstack([ell(s_, th_v), ell(s_, th_v)[:1]]) for s_ in s_c + (s_end - s_c) * np.array([0.35, 0.65, 0.88]) for th_v in [np.linspace(0, 2 * np.pi, 361)[:-1]]]
out = {}
SPo = np.array([frame_at(s_)[0] for s_ in np.r_[np.arange(0, dS[-1], 1.0), dS[-1]]])   # the spine out: through the lobe's middle
out["spinare_brat_fata_D"] = to_plane(SPo); out["contur_exterior_brat_fata_D"] = EXT_p; out["contur_interior_brat_fata_D"] = INT_p
# ---- 4. lips: symmetric about the major axis on the inner side
def lip_angle(s_):                                                          # half the mouth's opening (from the original lips) at s_
    p_, E1, E2, t_ = frame_at(s_); r_ = []
    for raw in (up_raw, lo_raw):
        sd = (raw - p_) @ t_; cx = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
        X = [raw[j] + (raw[j + 1] - raw[j]) * sd[j] / (sd[j] - sd[j + 1]) for j in cx]; X = [w for w in X if np.linalg.norm(w - p_) < 250]
        if not X: return None
        w = min(X, key=lambda w: np.linalg.norm(w - p_)); an, xe_, xi_, rb = bandp(s_); ra = (xe_ + xi_) / 2; m_ = (xe_ - xi_) / 2; rb = min(rb, ra)
        q = np.array([(w - p_) @ E1, (w - p_) @ E2]) - m_ * np.array([np.cos(an), np.sin(an)]); q = np.array([q[0] * np.cos(an) + q[1] * np.sin(an), -q[0] * np.sin(an) + q[1] * np.cos(an)])
        tt = np.arctan2(q[1] / rb, q[0] / ra); r_.append(abs((tt - np.pi + np.pi) % (2 * np.pi) - np.pi))
    return np.mean(r_)
s_V = min(sof(up_raw[:1])[0], sof(lo_raw[:1])[0]); PH = []
for s_ in np.arange(ST[0, 0], s_V - 5, 10.0):
    a_ = lip_angle(s_)
    if a_ is not None: PH.append((s_, a_))
PH = np.array(PH); dv_ = s_V - PH[:, 0]
cf = np.linalg.lstsq(np.c_[dv_, dv_ ** 2, dv_ ** 3], PH[:, 1], rcond=None)[0]   # one smooth curve, 0 at the V
phi = lambda s_: np.clip(np.polyval(np.r_[cf[::-1], 0], np.clip(s_V - s_, 0, None)), 0, np.pi * 0.95)
sl_ = np.arange(ST[0, 0], s_V, 2.0)
L1 = np.array([ell(s_, np.array([np.pi + phi(s_)]))[0] for s_ in sl_]); L2 = np.array([ell(s_, np.array([np.pi - phi(s_)]))[0] for s_ in sl_])
VX = ell(s_V, np.array([np.pi]))[0]; L1 = np.vstack([L1, VX]); L2 = np.vstack([L2, VX])
if L1[:, 2].mean() > L2[:, 2].mean(): L1, L2 = L2, L1                      # L1 = the lower lip
L1, L2 = to_plane(L1), to_plane(L2)
def lip_clean(L):                                                          # one lip (PS -> V): its bend seen from above kept one way - near
    def kk(L_):                                                            # the PS straight on to the plane, near the V straight into it
        Le = even(L_, 2.0); tt_ = np.gradient(Le[:, :2], axis=0); a_ = np.unwrap(np.arctan2(tt_[:, 1], tt_[:, 0]))
        return Le, gaussian_filter1d(np.gradient(a_) / np.linalg.norm(tt_, axis=1), 3), arclen(Le)
    for _ in range(4):
        Le, k_, u_ = kk(L); sg_ = np.sign(np.median(k_[(u_ > 150) & (u_ < u_[-1] - 150)]))
        b0 = np.where((u_ > 6) & (u_ < 300) & (np.sign(k_) != sg_) & (np.abs(k_) > 1e-4))[0]
        b1 = np.where((u_ > u_[-1] - 250) & (u_ < u_[-1] - 4) & (np.sign(k_) != sg_) & (np.abs(k_) > 1e-4))[0]
        if not len(b0) and not len(b1): break
        if len(b0): L = to_plane(Le[min(b0.max() + 6, len(Le) - 3):]); continue
        j = max(b1.min() - 6, 2); seg = np.linspace(Le[j], Le[-1], max(int(np.linalg.norm(Le[-1] - Le[j])), 2)); L = np.vstack([Le[:j], seg])
    return even(L)
L1, L2 = lip_clean(L1), lip_clean(L2)
buze = np.vstack([L1, L2[::-1][1:]]); out["buze_gura_brat_fata_D"] = buze; ib = len(L1) - 1
# contur_interior in two segments split at the lips' V (asked): along the mouth (PS -> V) in the lips' plane - in every section the
# middle between the two lips (on the major axis, the lips being symmetric about it), ending in the V; after the V the axis' end
def lcross(L, p_, n_):
    sd = (L - p_) @ n_; k = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    if not len(k): return None
    X = L[k] + (L[k + 1] - L[k]) * (sd[k] / (sd[k] - sd[k + 1]))[:, None]; return X[np.argmin(np.linalg.norm(X - p_, axis=1))]
MID = []
for s_ in np.arange(0, s_V, 2.0):
    p_, _, _, t_ = frame_at(s_); a_, b_ = lcross(L1, p_, t_), lcross(L2, p_, t_)
    if a_ is not None and b_ is not None: MID.append((a_ + b_) / 2)
MID = np.vstack([to_plane(np.array(MID)), VX]) if MID else VX[None]
s_int = sof(out["contur_interior_brat_fata_D"]); AFT = out["contur_interior_brat_fata_D"][s_int > s_V]
out["contur_interior_brat_fata_D"] = np.vstack([MID, AFT]); INT_V = len(MID) - 1
print("INTERIOR din 2 segmente la V: PS -> V mijlocul buzelor (%.0f m, in planul lor), V -> varf capatul axei mari (%.0f m)" % (arclen(MID)[-1], arclen(AFT)[-1]))
dph = np.abs(PH[:, 1] - phi(PH[:, 0]))
# ---- the red nacelle's guides (asked: from the lips; its V point in the band's plane - with the interior, the spine and the exterior;
# ribs alternating light / dark red, the dark ones bulged slightly outwards): the two ends on the lips, the V point on the band's line
# out of the mouth (beyond the interior), as deep - relative to the mouth's opening - as the old nacelle (old rails mirrored), 0 at the V
NRJ = e("NACELA_RAILS", "")
if NRJ:
    import json
    RJ = json.load(open(NRJ)); bez_ = lambda c, t_: (lambda c, t_: (1 - t_) ** 3 * c[0] + 3 * (1 - t_) ** 2 * t_ * c[1] + 3 * (1 - t_) * t_ ** 2 * c[2] + t_ ** 3 * c[3])(np.array(c), np.linspace(0, 1, 300)[:, None])
    old = [bez_(r["control"], None) * [-1, 1, 1] for r in RJ["rails"]]; oM = (old[0] + old[2]) / 2
    oapex = np.array(RJ["apex"]) * [-1, 1, 1]; dd_ = np.linalg.norm(oM - oapex, axis=1); ofr = 1 - dd_ / dd_.max()
    rel = np.linalg.norm(old[1] - oM, axis=1) / np.maximum(np.linalg.norm(old[0] - old[2], axis=1), 1e-6); o_ = np.argsort(ofr)
    NA_, NB_, NT_, NS_ = [], [], [], []
    for s_ in np.arange(-400 if CAPS is None else CAPS, s_V, 2.0):
        p_, E1, E2, t_ = frame_at(s_); a_, b_ = lcross(L1, p_, t_), lcross(L2, p_, t_)
        if a_ is None or b_ is None or side(np.array([a_, b_])).min() < -0.5: continue
        an_ = bandp(s_)[0]; d_ = E1 * np.cos(an_) + E2 * np.sin(an_); xm = (((a_ + b_) / 2) - p_) @ d_
        NA_.append(a_); NB_.append(b_); NT_.append((p_, d_, xm, np.linalg.norm(a_ - b_))); NS_.append(s_)
    mids = np.array([q[0] + q[1] * q[2] for q in NT_]); frn = arclen(mids) / arclen(mids)[-1]
    DEPn = gaussian_filter1d(np.interp(frn, ofr[o_], rel[o_]) * np.array([q[3] for q in NT_]), 6, mode="nearest")
    if e("NACELA_UNGHI", ""):                                             # (asked: the lips' shape, as if drawn on them from the V and turned
        dV_ = np.r_[arclen(np.vstack([mids, VX]))[::-1][1:]]               # a few degrees: off the lips' middle by (way to the V) x tan)
        DEPn = dV_ * np.tan(np.radians(float(e("NACELA_UNGHI", "7"))))
    NTIP = np.array([q[0] + q[1] * (q[2] + np.sign(q[2]) * dp_) for q, dp_ in zip(NT_, DEPn * sm_(np.clip((1 - frn) / 0.05, 0, 1)))])   # on the band's line
    NA_, NB_ = np.vstack([np.array(NA_), VX]), np.vstack([np.array(NB_), VX]); NTIP = np.vstack([NTIP, VX])
    out["contur_nacela_capat1_D"], out["contur_nacela_varf_D"], out["contur_nacela_capat2_D"] = NA_, NTIP, NB_
    LATN, RELN = float(e("NACELA_LATIME", "5.24")), float(e("NACELA_RELIEF", "1.0")); dT = arclen(NTIP); nrn = int(dT[-1] // LATN); edg = np.linspace(0, dT[-1], nrn + 1)
    NAC_DOUT = []
    for k_ in range(len(NTIP)):
        q = NT_[min(k_, len(NT_) - 1)]; NAC_DOUT.append(q[1] * np.sign(q[2]))
    NAC_DOUT = np.array(NAC_DOUT)
    for i_ in range(nrn):
        jm = int(np.argmin(np.abs(dT - (edg[i_] + edg[i_ + 1]) / 2))); seg = np.vstack([np.linspace(NA_[jm], NTIP[jm], 30)[:-1], np.linspace(NTIP[jm], NB_[jm], 30)])
        if i_ % 2 == 0 and RELN > 0: seg = seg + np.outer(np.sin(np.linspace(0, np.pi, len(seg))), NAC_DOUT[jm]) * RELN
        out["nacela_nervura_%s_%03d_D" % ("inchisa" if i_ % 2 == 0 else "deschisa", i_)] = seg
    print("NACELA ghidaje: varful V-ului pe linia benzii (iesit din gura pana la %.0f m), capetele pe buze, toate in V; %d nervuri de %.2f m alternand, inchise bombate %.1f m" % (
        DEPn.max(), nrn, dT[-1] / nrn, RELN))
print("BUZE simetrice fata de axa mare: deschiderea (jumatate) %.0f grd la PS -> 0 la V (s %.0f); fata de buzele originale (unghi) medie %.1f, max %.1f grd" % (
    np.degrees(phi(sl_[0])), s_V, np.degrees(dph.mean()), np.degrees(dph.max())))
# ---- ribs drawn every PAS m, open between the lips along the mouth, none beyond the PS-side U
th = np.linspace(0, 2 * np.pi, 361)[:-1]; k_ = 0
s40 = np.arange(PAS / 2, sd_[-1], PAS); s40 = s40[s40 < SB0 - PAS / 4]                 # every PAS m, in the bulb every PAS/2 (one even row)
for s_ in np.r_[s40, np.arange(SB0, sd_[-1], PAS / 2)]:
    pass
    if s_ < s_V:
        ph = phi(s_); tt = np.linspace(np.pi + ph, 3 * np.pi - ph, 361) % (2 * np.pi); X = ell(s_, tt)   # from one lip to the other
        p_, _, _, t_ = frame_at(s_); sd = (buze - p_) @ t_; cx = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]   # its ends exactly on
        XP = [buze[j] + (buze[j + 1] - buze[j]) * sd[j] / (sd[j] - sd[j + 1]) for j in cx]; XP = [w for w in XP if np.linalg.norm(w - p_) < 250]   # the
        if len(XP) >= 2:                                                   # (cleaned) lips, the move fading out to the exterior point
            XP = sorted(XP, key=lambda w: np.linalg.norm(w - p_))[:2]; a0_ = min(XP, key=lambda w: np.linalg.norm(w - X[0])); a1_ = XP[1] if a0_ is XP[0] else XP[0]
            n_ = len(X); m_ = n_ // 2; w0 = np.zeros(n_); w1 = np.zeros(n_); w0[:m_ + 1] = sm_(1 - np.arange(m_ + 1) / m_); w1[m_:] = sm_(np.arange(n_ - m_) / (n_ - 1 - m_))
            X = X + np.outer(w0, a0_ - X[0]) + np.outer(w1, a1_ - X[-1])
    else:
        if s_ >= s_c: continue                                             # (the round cap has its own ribs below)
        X = ell(s_, th); X = np.vstack([X, X[:1]])
    sdX = side(X)
    if (sdX < 0).any():                                                    # in the funnel: the rib cut by the PS-side U's plane
        if (sdX > 0).sum() < 10: continue
        ok_ = sdX > 0; X = np.roll(X, -int(np.argmax(ok_ & ~np.roll(ok_, 1))), axis=0); X = X[side(X) > 0]
    out["sectiune_brat_fata_D_%02d" % k_] = X; k_ += 1
for X in CAP_RIBS: out["sectiune_brat_fata_D_%02d" % k_] = X; k_ += 1
def straight_ps(L, win=400.0):                                             # what is left near the PS end bending the other way: from just past
    for _ in range(5):                                                     # its last such point the line goes straight (its own tangent) to
        Le = even(L, 2.0); tt_ = np.gradient(Le[:, :2], axis=0); a_ = np.unwrap(np.arctan2(tt_[:, 1], tt_[:, 0]))   # the PS plane (iterated)
        k_ = gaussian_filter1d(np.gradient(a_) / np.linalg.norm(tt_, axis=1), 3); u_ = arclen(Le)
        bad = np.where((u_ > 10) & (u_ < win) & (k_ < -1e-4))[0]
        if not len(bad): break
        j = min(bad.max() + 8, len(Le) - 3); L = to_plane(Le[j:]); print("  dreapta la capatul PS pana la %.0f m" % u_[j])
    return even(L)
# ---- 5. contur_gura_PS: one plane, from the lips' PS ends to the exterior's end, nose R_U_NAS
RUN = float(e("R_U_NAS", "8")); Q2 = to2(by_len(ps_raw, 600)); inose = int(np.argmin(by_len(ps_raw, 600)[:, 1]))
Q2[0], Q2[-1] = to2(buze[-1:])[0], to2(buze[:1])[0]
A_, B_ = Q2[:inose + 1], Q2[inose:][::-1]; okA = np.linalg.norm(A_ - Q2[inose], axis=1) > 25; okB = np.linalg.norm(B_ - Q2[inose], axis=1) > 25
def line_dev(E_, ok):
    d_ = np.linalg.svd(E_[ok] - E_[0])[2][0]; d_ *= np.sign(d_ @ (Q2[inose] - E_[0])); r_ = E_[ok] - E_[0]; return d_, np.abs(r_ @ np.array([-d_[1], d_[0]])).max()
(dA_, eA), (dB_, eB) = line_dev(A_, okA), line_dev(B_, okB); SWAP = eB < eA
S_, K_, okK = (B_, A_, okA) if SWAP else (A_, B_, okB); Kk = K_[okK & (np.linalg.norm(K_ - K_[0], axis=1) > 30)]   # (not the corner itself)
E2_ = to2(out["contur_exterior_brat_fata_D"][:1])[0]
def psu_to(T2):
    dE = T2 - S_[0]; dE /= np.linalg.norm(dE); nE_ = np.array([-dE[1], dE[0]]); nE_ *= np.sign(nE_ @ (K_[len(K_) // 2] - S_[0]))
    mk_ = (K_[0] + T2) / 2; nk_ = np.array([-(T2 - K_[0])[1], (T2 - K_[0])[0]]) / np.linalg.norm(T2 - K_[0])   # the lower edge: an arc
    nk_ *= np.sign(nk_ @ (mk_ - (S_[0] + T2) / 2)) if abs(nk_ @ (mk_ - (S_[0] + T2) / 2)) > 1e-6 else 1.0          # sagging away from the
    far2 = mk_ + nk_ * float(e("U_SAGEATA", "0.07")) * np.linalg.norm(T2 - K_[0])                                    # straight edge
    C1, R1 = circ3(K_[0], far2, T2); tE = np.linalg.norm(T2 - S_[0]); ts = np.linspace(0.3 * tE, tE, 6000)
    gv = np.array([np.linalg.norm(S_[0] + dE * t_ + nE_ * RUN - C1) - (R1 - RUN) for t_ in ts]); rt = np.where(np.sign(gv[:-1]) != np.sign(gv[1:]))[0]
    cand = []                                                             # (only a tangency whose arc point lies ahead, towards the nose)
    for tt_ in (ts[rt] if len(rt) else [ts[np.argmin(np.abs(gv))]]):
        cn_ = S_[0] + dE * tt_ + nE_ * RUN; TC_ = C1 + (cn_ - C1) / np.linalg.norm(cn_ - C1) * R1
        if (TC_ - (S_[0] + dE * tt_)) @ dE > -1.0: cand.append(tt_)
    if not cand:                                                          # no good tangency (the edges meet almost tangent): the nose is
        return np.vstack([np.linspace(S_[0], T2, 200)[:-1], arc2(C1, R1, T2, K_[0], 200)]), R1, T2, dE   # their meeting point itself
    tt = min(cand, key=lambda q: abs(q - tE))
    cn = S_[0] + dE * tt + nE_ * RUN; TL = S_[0] + dE * tt; TC = C1 + (cn - C1) / np.linalg.norm(cn - C1) * R1
    arcN = arc2(cn, RUN, TL, TC); arcL = arc2(cn, RUN, TL, TC, longway=True)
    if (arcL[40] - cn) @ dE > (arcN[40] - cn) @ dE: arcN = arcL
    return np.vstack([np.linspace(S_[0], TL, 200)[:-1], arcN[:-1], arc2(C1, R1, TC, K_[0], 200)]), R1, TL, dE
T2 = E2_.copy()
for _ in range(6):
    PSc, R1, TL, dE = psu_to(T2); T2 = T2 + (E2_ - PSc[np.argmax(PSc @ dE)])
PSc, R1, TL, dE = psu_to(T2)
if SWAP: PSc = PSc[::-1]
out["contur_gura_PS_brat_fata_D"] = PSU = c_ps + np.outer(PSc[:, 0], b1) + np.outer(PSc[:, 1], b2)
print("GURA PS: plana (abatere %.3f m), dreapta %.0f m + arc R %.0f + nas R %.0f; nasul pe capatul exteriorului (%.1f m); capetele pe buze %.2f / %.2f m" % (
    np.abs((PSU - c_ps) @ npl).max(), np.linalg.norm(TL - S_[0]), R1, RUN, np.min(np.linalg.norm(PSU - out["contur_exterior_brat_fata_D"][0], axis=1)),
    np.linalg.norm(PSU[0] - buze[-1]), np.linalg.norm(PSU[-1] - buze[0])))
# ---- the open end: from contur_gura_PS to the first whole rib a ROUND transition (asked: more ribs at the end, its underside looked
# flat) - every point moved about the arm's axis (distance along it, radius and angle round it interpolated), not on straight chords;
# three of those rows added to the guides as ribs
NU, DSP = int(e("NU", "121")), float(e("DS", "2"))
def row(s_, NU=NU):
    ph = phi(s_) if s_ < s_V else 0.0; tt = np.linspace(np.pi + ph, 3 * np.pi - ph, NU) % (2 * np.pi); X = ell(s_, tt)
    if s_ >= s_V: return X
    p_, _, _, t_ = frame_at(s_); sd = (buze - p_) @ t_; cx = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    XP = [buze[j] + (buze[j + 1] - buze[j]) * sd[j] / (sd[j] - sd[j + 1]) for j in cx]; XP = [w for w in XP if np.linalg.norm(w - p_) < 250]
    if len(XP) >= 2:
        XP = sorted(XP, key=lambda w: np.linalg.norm(w - p_))[:2]; a0_ = min(XP, key=lambda w: np.linalg.norm(w - X[0])); a1_ = XP[1] if a0_ is XP[0] else XP[0]
        m_ = NU // 2; w0 = np.zeros(NU); w1 = np.zeros(NU); w0[:m_ + 1] = sm_(1 - np.arange(m_ + 1) / m_); w1[m_:] = sm_(np.arange(NU - m_) / (NU - 1 - m_))
        X = X + np.outer(w0, a0_ - X[0]) + np.outer(w1, a1_ - X[-1])
    return X
s_first = next(s_ for s_ in np.arange(sd_[0], s_c, DSP) if (side(row(s_)) >= 2).all())
def resample(L, n): d_ = arclen(L); return np.c_[[np.interp(np.linspace(0, d_[-1], n), d_, L[:, k]) for k in range(3)]].T
def FUN_rows(nu, lams=None):
    X1 = row(s_first, nu); U = PSU.copy(); jn = int(np.argmin(np.linalg.norm(U - out["contur_exterior_brat_fata_D"][0], axis=1)))
    if np.linalg.norm(U[0] - X1[0]) > np.linalg.norm(U[-1] - X1[0]): U = U[::-1]; jn = len(U) - 1 - jn
    m_ = nu // 2; R0 = np.vstack([resample(U[:jn + 1], m_ + 1), resample(U[jn:], nu - m_)[1:]])
    p1, E1a, E2a, T1 = frame_at(s_first)
    def cyl(P): v = P - p1; a_ = v @ T1; w = v - np.outer(a_, T1); return a_, np.linalg.norm(w, axis=1), np.arctan2(w @ E2a, w @ E1a)
    a0, r0, t0 = cyl(R0); a1, r1, t1 = cyl(X1); t0 = t1 + (t0 - t1 + np.pi) % (2 * np.pi) - np.pi
    nl = max(int(np.max(np.abs(a0 - a1)) / DSP), 4); lams = np.arange(nl) / nl if lams is None else lams; rr = []
    nA = SGN * npl; cU = R0.mean(0)                                          # the original's own cuts: planes turning from the first rib's
    for l_ in lams:                                                         # plane (l 1) to the PS-side U's (l 0), through points on the way
        w_ = sm_(l_); a_ = a0 * (1 - l_) + a1 * l_; r_ = r0 * (1 - w_) + r1 * w_; th_ = t0 * (1 - w_) + t1 * w_
        Xi = p1 + np.outer(a_, T1) + np.outer(r_ * np.cos(th_), E1a) + np.outer(r_ * np.sin(th_), E2a)   # (the round blend, as a fallback)
        if 0 < l_ < 1:
            nP = (1 - l_) * nA + l_ * T1; nP /= np.linalg.norm(nP); oP = Xi.mean(0); sec = t.section(plane_origin=oP, plane_normal=nP)
            if sec is not None:
                ents = [sec.vertices[k_.points] for k_ in sec.entities]; ents = [q for q in ents if np.min(np.linalg.norm(q - oP, axis=1)) < 300 and len(q) > 10]
                if ents:
                    Cc = max(ents, key=lambda q: arclen(q)[-1])                  # the main open C, from the end nearer row index 0
                    if np.linalg.norm(Cc[0] - Xi[0]) + np.linalg.norm(Cc[-1] - Xi[-1]) > np.linalg.norm(Cc[-1] - Xi[0]) + np.linalg.norm(Cc[0] - Xi[-1]): Cc = Cc[::-1]
                    Cc = np.c_[[gaussian_filter1d(Cc[:, k], 4, mode="nearest") for k in range(3)]].T
                    Xr = resample(Cc, nu); jx = int(np.argmax((Xr - p1) @ E1a)); jxi = int(np.argmax((Xi - p1) @ E1a))
                    if abs(jx - jxi) > nu // 4: Xr = resample(Cc, nu)          # (orientation kept as is)
                    m2 = nu // 2; W0 = np.zeros(nu); W1 = np.zeros(nu); W0[:m2 + 1] = sm_(1 - np.arange(m2 + 1) / m2); W1[m2:] = sm_(np.arange(nu - m2) / (nu - 1 - m2))
                    Xr = Xr + np.outer(W0, Xi[0] - Xr[0]) + np.outer(W1, Xi[-1] - Xr[-1])   # its ends on our lips (= the blend's ends)
                    g_ = sm_(min(1.0, 4 * min(l_, 1 - l_)))                     # near both ends eased into the U / the first rib
                    Xi = Xi * (1 - g_) + Xr * g_
        rr.append(Xi)
    return rr
kk0 = max(int(q.split("_")[-1]) for q in out if q.startswith("sectiune_brat_fata_D")) + 1
# two vertebrae in the triangular zone between contur_gura_PS and the band's start (asked: smaller): the band's own vertebrae (open
# between the lips) further towards the PS, cut by the PS-side U's plane - only their part inside the zone is kept
s_full = s_first; s_tri = s_full
for s_ in np.arange(s_full, s_full - 600, -2.0):                           # where the vertebra lies wholly beyond the PS plane
    if (side(row(s_, 361)) > 0).sum() < 6: break
    s_tri = s_
nv_ = 0
if CAPS is not None:                                                       # the head: the band's vertebra in the head plane; no triangle,
    out.pop("contur_gura_PS_brat_fata_D", None); PSU = row(CAPS, 361); s_tri = CAPS   # no contur_gura_PS (the head is the arm's end)
    out["sectiune_brat_fata_D_%02d" % kk0] = PSU; kk0 += 1
for f_ in ([] if CAPS is not None else [float(q) for q in e("VERTEBRE_PALNIE", "0.333,0.667").split(",")]):
    X = row(s_full + (s_tri - s_full) * f_, 361); sv = side(X); ok_ = sv > 0
    if ok_.sum() < 6: continue
    runs = np.split(np.arange(len(X)), np.where(np.diff(ok_.astype(int)) != 0)[0] + 1); run = max([r_ for r_ in runs if ok_[r_[0]]], key=len)
    i0, i1 = run[0], run[-1]; ends = []
    for ia, ib in ((i0 - 1, i0), (i1 + 1, i1)):                          # where it leaves the zone: onto contur_gura_PS itself
        if 0 <= ia < len(X): c_ = X[ia] + (X[ib] - X[ia]) * sv[ia] / (sv[ia] - sv[ib]); ends.append(PSU[np.argmin(np.linalg.norm(PSU - c_, axis=1))])
        else: ends.append(X[ib])
    Y = X[i0:i1 + 1].copy(); n_ = len(Y); m2 = n_ // 2; W0 = np.zeros(n_); W1 = np.zeros(n_)
    W0[:m2 + 1] = sm_(1 - np.arange(m2 + 1) / max(m2, 1)); W1[m2:] = sm_(np.arange(n_ - m2) / max(n_ - 1 - m2, 1))
    Y = Y + np.outer(W0, ends[0] - Y[0]) + np.outer(W1, ends[1] - Y[-1])
    out["sectiune_brat_fata_D_%02d" % (kk0 + nv_)] = Y; nv_ += 1
print("VERTEBRE in zona triunghiulara: %d, intre s %.0f (prima vertebra intreaga) si s %.0f (planul gurii)" % (nv_, s_full, s_tri))
kk0 += nv_
if CAPS is None: print("CAPATUL DESCHIS: trecere contur_gura_PS -> prima nervura intreaga (s %.0f), %d randuri (pentru suprafata)" % (s_first, len(FUN_rows(NU))))
# ---- the band itself (asked: carried on to the ends of the exterior, the spine and the interior): across, from the interior (along the
# mouth the lips' middle) to the exterior on the band's line; at the PS end every row cut by the PS-side U's plane (a triangular end up
# to the nose), at the tip closing on the snout
if e("BANDA_OUT", ""):
    NB = 17; BR = []
    for s_ in BAND_S:
        p_, E1, E2, t_ = frame_at(s_); a_, xe_, xi_, _ = bandp(s_); d_ = E1 * np.cos(a_) + E2 * np.sin(a_); x_in = -xi_
        if s_ < s_V:
            la, lb = lcross(L1, p_, t_), lcross(L2, p_, t_)
            if la is not None and lb is not None: x_in = (((la + lb) / 2) - p_) @ d_
        uu = np.linspace(x_in, xe_, 200); Rw = p_ + np.outer(uu, d_); sv = side(Rw)
        if (sv <= 0).all(): continue
        if (sv <= 0).any():
            k = np.where(sv > 0)[0]; Rw = Rw[k.min():k.max() + 1]; sv2 = sv[k.min():k.max() + 1]
            for ia, ib, at_ in ((k.min() - 1, k.min(), 0), (k.max() + 1, k.max(), -1)):
                if 0 <= ia < len(uu): c_ = (p_ + uu[ia] * d_) + ((p_ + uu[ib] * d_) - (p_ + uu[ia] * d_)) * sv[ia] / (sv[ia] - sv[ib]); Rw[at_] = c_
        BR.append(resample(Rw, NB) if arclen(Rw)[-1] > 1e-6 else np.repeat(Rw[:1], NB, 0))
    BR = np.array(BR)
    if CAPS is not None: BR = W(BR)
    nrb = len(BR); Vb = BR.reshape(-1, 3); Fb = []
    for r in range(nrb - 1):
        for jj in range(NB - 1):
            q = [r * NB + jj, r * NB + jj + 1, (r + 1) * NB + jj + 1, (r + 1) * NB + jj]; Fb += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
    tb = trimesh.Trimesh(Vb, np.array(Fb), process=True); tb.merge_vertices(); tb.update_faces(tb.nondegenerate_faces()); tb.remove_unreferenced_vertices()
    np.savez(e("BANDA_OUT", ""), v=tb.vertices * [-1, 1, 1], f=tb.faces[:, ::-1]); np.savez(e("BANDA_OUT", "").replace(".npz", "_D.npz"), v=tb.vertices, f=tb.faces)
    print("BANDA pana la capete: %d randuri, %d fete (S in fisier, D in _D)" % (nrb, len(tb.faces)))
EXT0 = out["contur_exterior_brat_fata_D"][0].copy()
if CAPS is not None:
    for kk in list(out): out[kk] = W(out[kk])
    SP_W = W(SP); sof = lambda P: dS[np.argmin(np.linalg.norm(SP_W[None] - P[:, None], axis=2), axis=1)]
# ---- checks: breaks per line, the green lines on the ribs, the original's surface vs the new ribs
def brk(L):
    t_ = np.diff(L, axis=0); sl = np.linalg.norm(t_, axis=1); ok = sl > 1e-6; t_ = t_[ok]; sl = sl[ok]; t_ /= sl[:, None]
    return np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", t_[:-1], t_[1:]), -1, 1))) / ((sl[:-1] + sl[1:]) / 2)
for k in ("spinare_brat_fata_D", "contur_exterior_brat_fata_D", "contur_gura_PS_brat_fata_D"):
    if k in out: out[k] = even(out[k])
jvi = int(np.argmin(np.linalg.norm(out["contur_interior_brat_fata_D"] - VX, axis=1)))   # the interior: each segment resampled, the V kept
out["contur_interior_brat_fata_D"] = np.vstack([even(out["contur_interior_brat_fata_D"][:jvi + 1]), even(out["contur_interior_brat_fata_D"][jvi:])[1:]])
ibz = int(np.argmin(np.linalg.norm(out["buze_gura_brat_fata_D"] - VX, axis=1)))   # the lips: each side resampled, the V kept sharp
out["buze_gura_brat_fata_D"] = np.vstack([even(out["buze_gura_brat_fata_D"][:ibz + 1]), even(out["buze_gura_brat_fata_D"][ibz:])[1:]])
for k in ("spinare_brat_fata_D", "contur_exterior_brat_fata_D", "contur_interior_brat_fata_D", "buze_gura_brat_fata_D", "contur_gura_PS_brat_fata_D"):
    if k not in out: continue
    L_ = out[k]; jv_ = int(np.argmin(np.linalg.norm(L_ - VX, axis=1))) if (k.startswith("buze") or "interior" in k) else None
    sn = sens(L_) if jv_ is None else "%d / %d (fiecare segment, la V)" % (sens(L_[:jv_ + 1]), sens(L_[jv_:]))
    if jv_ is not None: L_ = np.vstack([L_[:jv_ + 1], L_[jv_ + 1:]])
    a_ = brk(L_); print("FRANGERE %-30s max %.2f p99 %.2f grd/m, lungime %.0f m, schimbari de sens (de sus) %s" % (k, a_.max(), np.percentile(a_, 99), arclen(L_)[-1], sn))
dsurf = np.abs(trimesh.proximity.signed_distance(t, np.vstack([out[k][::4] for k in out if k.startswith("sectiune")]))) if False else None
# ---- the arm's surface from the same guides (PIESA=<out.npz>): rows across every DS m - along the mouth from one lip around the
# outside to the other (ends snapped on the lips, the mouth stays open), after the V the closed ribs (seam on the interior), the
# tip closed on the real tip; at the PS end the first row is contur_gura_PS itself (its nose = the exterior), lofted into the tube
if e("PIESA", ""):
    rows = [row(s_, NU) for s_ in np.arange(s_tri, s_c, DSP)]; cap = cap_rows(NU)   # (from the triangle's start: the band's vertebrae)
    G0 = np.array(rows); cols = []                                           # each line along the arm cut at the PS plane, resampled
    for j in range(NU):
        c_ = G0[:, j]; sv = side(c_); k = int(np.argmax(sv > 0))
        if k > 0: c_ = np.vstack([c_[k - 1] + (c_[k] - c_[k - 1]) * sv[k - 1] / (sv[k - 1] - sv[k]), c_[k:]])
        cols.append(c_)
    MR = int(np.median([len(c_) for c_ in cols]))
    G1 = np.stack([np.c_[[np.interp(np.linspace(0, arclen(c_)[-1], MR), arclen(c_), c_[:, q]) for q in range(3)]].T for c_ in cols], axis=1)
    U_ = PSU.copy(); jn = int(np.argmin(np.linalg.norm(U_ - EXT0, axis=1)))
    if np.linalg.norm(U_[0] - G1[0, 0]) > np.linalg.norm(U_[-1] - G1[0, 0]): U_ = U_[::-1]; jn = len(U_) - 1 - jn
    m_ = NU // 2; R0 = np.vstack([resample(U_[:jn + 1], m_ + 1), resample(U_[jn:], NU - m_)[1:]])
    NL = int(e("RACORD_PS_RANDURI", "12")); D0 = R0 - G1[0]; NL_ = NL                 # its edge = contur_gura_PS, the step eased
    for k in range(min(NL, MR)): G1[k] += D0 * (1 - sm_(k / NL))
    rows = list(G1)
    G = np.array(rows + cap + [np.repeat(APEX[None], NU, 0)])
    if CAPS is not None: G = W(G)
    nr = len(G); V = G.reshape(-1, 3); F = []
    for r in range(nr - 1):
        for j in range(NU - 1):
            q = [r * NU + j, r * NU + j + 1, (r + 1) * NU + j + 1, (r + 1) * NU + j]; F += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
    F = np.array(F); tm = trimesh.Trimesh(V, F, process=True); tm.merge_vertices(); tm.update_faces(tm.nondegenerate_faces()); tm.remove_unreferenced_vertices()
    trimesh.repair.fix_normals(tm); cnt = np.unique(tm.edges_sorted, axis=0, return_counts=True)[1]
    from scipy.spatial import cKDTree
    kd = cKDTree(tm.vertices); IA = out["contur_interior_brat_fata_D"]; IA = IA[sof(IA) > s_V + 5]   # (interior: its segment after the V)
    gd = {"contur_exterior_brat_fata_D": kd.query(out["contur_exterior_brat_fata_D"])[0].max(), "contur_interior_brat_fata_D": kd.query(IA)[0].max()}
    np.savez(e("PIESA", ""), brat_fata_D__v=tm.vertices, brat_fata_D__f=tm.faces, brat_fata_S__v=tm.vertices * [-1, 1, 1], brat_fata_S__f=tm.faces[:, ::-1])
    for sd_n, sg in (("D", 1), ("S", -1)): np.savez(e("PIESA", "").replace(".npz", "_%s.npz" % sd_n), v=tm.vertices * [sg, 1, 1], f=tm.faces if sg > 0 else tm.faces[:, ::-1])
    print("PIESA brat_fata: %d randuri x %d (racord PS %d randuri, tubul de la s %.0f), %d fete; muchii libere %d (gura + capatul PS), ne-manifold %d; ghidaje pe piesa ~ exterior %.1f, interior %.1f m" % (
        nr, NU, NL, s_first, len(tm.faces), int(np.sum(cnt == 1)), int(np.sum(cnt > 2)), gd["contur_exterior_brat_fata_D"], gd["contur_interior_brat_fata_D"]))
for kk in list(out): out[kk.replace("_D", "_S")] = out[kk] * [-1, 1, 1]
out["_spinare_reala_D"] = C_raw
if e("REF_OUT", ""):                                                       # the reference arm (and its real rib centres) turned with the arm
    NV_ = np.load(sys.argv[1])["nacela_rosie_D__v"] if "nacela_rosie_D__v" in np.load(sys.argv[1]).files else np.zeros((0, 3))   # (+ the red nacelle)
    np.savez(e("REF_OUT", ""), v=W(t.vertices) if CAPS is not None else t.vertices, c=W(C_raw) if CAPS is not None else C_raw, spine=SP_W if CAPS is not None else SP,
             nacela=W(NV_) if CAPS is not None and len(NV_) else NV_)
np.savez(OUT, **out); print("SAVED", OUT, len(out), "linii")
