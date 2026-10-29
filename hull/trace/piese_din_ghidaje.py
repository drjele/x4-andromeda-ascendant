# The PS and its arms built from their confirmed guides (asked: the assembled guides look right - make the pieces). Ship
# coordinates, one surface per piece (caps / holes closed later in Blender, piese_din_ghidaje_blend.py):
#   PS        - side from the C ribs (one every DS m round the outer outline: quarter ellipse out to the bulge, quarter
#               ellipse up and in to the inner line; bulge and its height interpolated between the confirmed ribs; end on the
#               inner line at the same fraction of the way round), bottom flat z 280 (outer outline), top flat (inner line)
#   PS_rama   - between the rim's outer and inner outlines, the guide's section (flat top, quarter-ellipse bottom, inner wall)
#   PS_carena - the ruled solid between the big side (z 280) and the floor (same point order)
#   capac_086 - on the trapezoid base: slanted walls (45 deg) up to a flat top at the spine's height, corners rounded
#   brat_spate_D / _S - the tube swept along the clean spine (parallel-transport frames), the section ellipses interpolated
# env CAMERE=T,WM[,1[,1]]: the hood's chambers as cutters (3rd 1 = open below, no floor; 4th 1 = no front wall); URECHI=<ears guide npz>: the little ears as plates.
# Usage: python piese_din_ghidaje.py <ps ribs npz (ghid_ps_rama_v8)> <rama npz (ghid_rama_baza)> <carena npz (_asamblat)>
#        <capac npz (_asamblat)> <brat npz (ghid_brat_v2)> <out.npz> ; env DS=2 OFF_BR=80,-120,0
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import spate_ps as SPS
from scipy.ndimage import gaussian_filter1d
GP, GR, GC, GK, GB = (np.load(a) for a in sys.argv[1:6]); OUT = sys.argv[6]; DS = float(os.environ.get("DS", "2"))
ob = np.array([float(q) for q in os.environ.get("OFF_BR", "80,-120,0").split(",")]); out = {}
def grid_faces(nu, nv, close_u=True):                   # quads of an nu x nv grid (rows u around, columns v along), as triangles
    F = []
    for i in range(nu if close_u else nu - 1):
        i2 = (i + 1) % nu
        for j in range(nv - 1):
            a, b, c, d = i * nv + j, i2 * nv + j, i2 * nv + j + 1, i * nv + j + 1; F += [[a, b, c], [a, c, d]]
    return np.array(F)
def resample_closed(P, step):
    P = P[:-1] if np.allclose(P[0], P[-1]) else P; c = np.vstack([P, P[:1]]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    u = np.arange(0, d[-1], step); return np.c_[[np.interp(u, d, c[:, k]) for k in range(P.shape[1])]].T
def roll_tip_cw(P):                                    # start at the tip (max y on the axis), clockwise seen from above
    j = int(np.argmax(P[:, 1] - 5 * np.abs(P[:, 0]))); P = np.roll(P, -j, 0)
    a = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]); return P if a < 0 else np.r_[P[:1], P[1:][::-1]]
# ---- PS body
E = roll_tip_cw(resample_closed(GP["contur_rama_exterior_pe_PS"], DS)); ZP = float(GP["contur_rama_exterior_pe_PS"][0, 2])
LIN = roll_tip_cw(resample_closed(GP["contur_sus_nervuri"], 0.5)); ZL = float(LIN[0, 2])
dE = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([E, E[:1]])[:, :2], axis=0), axis=1))]; LE = dE[-1]
dL = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([LIN, LIN[:1]])[:, :2], axis=0), axis=1))]; LL_ = np.vstack([LIN, LIN[:1]])
st = []                                                # the confirmed ribs: arc position of their foot, bulge e and its height
for k in sorted(q for q in GP.files if q.startswith("nervura") and q.endswith("_D")):
    q = GP[k]; p = q[0, :2]; T = q[-1, :2]; nr = (p - T) / np.linalg.norm(p - T); u = (q[:, :2] - p) @ nr; j = int(np.argmax(u))
    s_ = dE[int(np.argmin(np.linalg.norm(E[:, :2] - p, axis=1)))]; st.append((s_, max(u[j], 0.5), q[j, 2]))
st = np.array(sorted(st)); ss = np.r_[st[:, 0], LE - st[::-1, 0]]; ee = np.r_[st[:, 1], st[::-1, 1]]; zz = np.r_[st[:, 2], st[::-1, 2]]   # + mirror
o_ = np.argsort(ss); ss, ee, zz = ss[o_], ee[o_], zz[o_]
K1, K2 = 16, 40; rows = []
for i in range(len(E)):
    p = E[i, :2]; f = dE[i] / LE; T = np.array([np.interp(f * dL[-1], dL, LL_[:, c]) for c in range(3)])
    e = np.interp(dE[i], ss, ee, period=LE); ze = np.interp(dE[i], ss, zz, period=LE); ze = min(max(ze, ZP + 1), ZL - 1)
    v_ = p - T[:2]; w = np.linalg.norm(v_); nr = v_ / w
    C2 = SPS.rib(e, ze, ZP + float(SPS.dz(p[1])), ZL, w, p[1], K1, K2)        # (the back: bottom dropped, ribs squarer)
    rows.append(np.c_[p[0] + C2[:, 0] * nr[0], p[1] + C2[:, 0] * nr[1], C2[:, 1]])
R = np.array(rows); nu, nv = R.shape[:2]; out["PS__v"] = R.reshape(-1, 3); out["PS__f"] = grid_faces(nu, nv)
# ---- rim
Eo = GR["contur_rama_exterior"]; ZR = float(Eo[0, 2]); HR = ZR - float(GR["contur_rama_interior_jos"][0, 2])
O = resample_closed(Eo[:, :2], 1.0); Ii = resample_closed(GR["contur_rama_interior"][:, :2], 0.5); N, M = len(O), len(Ii)
tg = np.roll(O, -1, 0) - np.roll(O, 1, 0); tg /= np.linalg.norm(tg, axis=1)[:, None]; a_ = 0.5 * np.sum(O[:, 0] * np.roll(O[:, 1], -1) - np.roll(O[:, 0], -1) * O[:, 1])
nin = np.c_[tg[:, 1], -tg[:, 0]] * (1 if a_ < 0 else -1)
RW = float(np.median(np.min(np.linalg.norm(O[:, None, :] - Ii[None, ::8, :], axis=2), axis=1)))
idx = np.argmin(np.linalg.norm((O + RW * nin)[:, None, :] - Ii[None, :, :], axis=2), axis=1)
t_ = np.unwrap(idx * 2 * np.pi / M) * M / (2 * np.pi); t_ = np.maximum.accumulate(t_ - t_[0]) if t_[-1] >= t_[0] else -np.maximum.accumulate(-(t_ - t_[0]))
keep = np.r_[True, np.diff(t_) != 0]; ii = np.arange(N); t_ = np.interp(ii, np.r_[ii[keep], N], np.r_[t_[keep], M * np.sign(t_[-1] if t_[-1] != 0 else 1)])
tf = (t_ + idx[0]) % M; i0 = np.floor(tf).astype(int); fr = (tf - i0)[:, None]; Pin = Ii[i0] * (1 - fr) + Ii[(i0 + 1) % M] * fr
KR = 12; s = np.linspace(0, 1, KR + 1); zb = ZR - HR * np.sqrt(np.clip(1 - (1 - s) ** 2, 0, 1))
loop = []                                              # per outer point: bottom outer->inner, inner wall up, top inner->outer
for i in range(N):
    xy = O[i] + np.outer(s, Pin[i] - O[i]); bot = np.c_[xy, zb]; top = np.c_[xy[::-1], np.full(KR + 1, ZR)][:-1]   # inner top included (vertical inner wall), outer = bot[0]
    loop.append(np.vstack([bot, top]))
RR = np.array(loop); nu, nv = RR.shape[:2]; F = grid_faces(nu, nv)
F = np.vstack([F, [[i * nv + nv - 1, ((i + 1) % nu) * nv + nv - 1, ((i + 1) % nu) * nv + 0] for i in range(nu)], [[i * nv + nv - 1, ((i + 1) % nu) * nv, i * nv] for i in range(nu)]])
out["PS_rama__v"] = RR.reshape(-1, 3); out["PS_rama__f"] = F
# ---- keel
T_ = GC["contur_carena_sus"]; J_ = GC["contur_carena_jos"]; T_ = T_[:-1] if np.allclose(T_[0], T_[-1]) else T_; J_ = J_[:-1] if np.allclose(J_[0], J_[-1]) else J_
nk = len(T_); KV = np.vstack([T_, J_]); KF = [[i, (i + 1) % nk, nk + (i + 1) % nk] for i in range(nk)] + [[i, nk + (i + 1) % nk, nk + i] for i in range(nk)]
out["PS_carena__v"] = KV; out["PS_carena__f"] = np.array(KF)
# ---- hood
B_ = GK["contur_capac_baza"]; ZC = float(B_[0, 2]); SP = GK["spinare_capac_mijloc"]; YB, YF = B_[:, 1].min(), B_[:, 1].max()
def half_w(P, y):
    q = np.vstack([P, P[:1]]); xs = [a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) for a, b in zip(q[:-1], q[1:]) if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]]
    xs = [x for x in xs if x > 0]; return max(xs) if xs else 0.0
spy = SP[:, 1]; spz = SP[:, 2]; o2 = np.argsort(spy); MH = 60; RF = float(os.environ.get("RF_CAPAC", "7")); rows = []
for y in np.linspace(YB + 0.05, YF - 0.05, int((YF - YB) / 1.0)):
    w = half_w(B_[:, :2], y); h = max(np.interp(y, spy[o2], spz[o2]) - ZC, 0.0); dx = min(h, w * 0.9)
    P = [[-w, ZC], [-w + dx, ZC + h], [w - dx, ZC + h], [w, ZC]]
    prof = np.array(P, float); dd = np.r_[0, np.cumsum(np.linalg.norm(np.diff(prof, axis=0), axis=1))]
    if dd[-1] < 1e-6: dd = np.linspace(0, 1, 4)
    u = np.linspace(0, dd[-1], MH); top = np.c_[np.interp(u, dd, prof[:, 0]), np.interp(u, dd, prof[:, 1])]
    if h > 0.5:                                        # rounded corners: a light smoothing of the profile (corners ~RF)
        sg = RF / max(dd[-1] / MH, 1e-3) / 2; tp = np.c_[gaussian_filter1d(top[:, 0], sg, mode="nearest"), gaussian_filter1d(top[:, 1], sg, mode="nearest")]
        tp[0], tp[-1] = top[0], top[-1]; top = tp
    bot = np.c_[np.linspace(w, -w, 20)[1:-1], np.full(18, ZC)]
    L2 = np.vstack([top, bot]); rows.append(np.c_[L2[:, 0], np.full(len(L2), y), L2[:, 1]])
H_ = np.array(rows); nr_, nc_ = H_.shape[:2]; HF = []
for r in range(nr_ - 1):
    for j in range(nc_):
        a, b, c, d = r * nc_ + j, r * nc_ + (j + 1) % nc_, (r + 1) * nc_ + (j + 1) % nc_, (r + 1) * nc_ + j; HF += [[a, b, c], [a, c, d]]
out["capac_086__v"] = H_.reshape(-1, 3); out["capac_086__f"] = np.array(HF)
CAM = os.environ.get("CAMERE")                        # the hood's chambers (cutters, the hood made hollow in Blender): T m walls,
if CAM:                                                # WM m middle wall, one long chamber a side, run out through the front (mouth)
    cp_ = [float(q) for q in CAM.split(",")]; T, WM = cp_[0], cp_[1]; JOS = len(cp_) > 2 and cp_[2] > 0   # 3rd = 1: open below too (no floor)
    GURA = len(cp_) > 3 and cp_[3] > 0                                         # 4th = 1: no front wall (open in front, full height)
    R2 = B_[(B_[:, 0] > 0) & (B_[:, 1] > YB + 15) & (B_[:, 1] < YF - 15)]; bb, aa = np.polyfit(R2[:, 1], R2[:, 0], 1); S2 = np.sqrt(2)
    def inner(y):
        h = max(np.interp(y, spy[o2], spz[o2]) - ZC, 0.0); w = aa + bb * y; zf, zt = ZC + T, ZC + h - T
        if zt <= zf + 0.5: return None
        xf = w - (zf - ZC) - T * S2; xt = w - (zt - ZC) - T * S2; return (WM / 2, xf, xt, zf, zt) if xt > WM / 2 + 1 else None
    rows = []; last = None
    for y in np.arange(YB + T * S2 + T, YF + 6, 1.0):
        hf_ = max(np.interp(YF - 30, spy[o2], spz[o2]) - ZC, 0.0); yg = YF - hf_ - 1   # where the front wall starts
        q = inner(min(y, yg)) if (GURA and y >= yg) else (inner(y) if y <= YF else None)
        if q is None and last is not None and y > (YB + YF) / 2: q = last          # past the front: the last section, through the mouth
        if q is None: continue
        last = q; x0, xf, xt, zf, zt = q
        if JOS: xf = xf + (zf - (ZC - 3)); zf = ZC - 3                          # the floor taken out: the cutter runs below the base (45 deg kept)
        rows.append(np.array([[x0, y, zf], [xf, y, zf], [xt, y, zt], [x0, y, zt]]))
    Rc = np.array(rows); nr_ = len(Rc); CF = []
    for r in range(nr_ - 1):
        for j in range(4):
            a_, b_, c_, d_ = r * 4 + j, r * 4 + (j + 1) % 4, (r + 1) * 4 + (j + 1) % 4, (r + 1) * 4 + j; CF += [[a_, b_, c_], [a_, c_, d_]]
    out["camera_D__v"] = Rc.reshape(-1, 3); out["camera_D__f"] = np.array(CF); out["camera_S__v"] = Rc.reshape(-1, 3) * [-1, 1, 1]; out["camera_S__f"] = np.array(CF)[:, ::-1]
URE = os.environ.get("URECHI")                         # the little ears: plates from their guide outlines (z top..top-TH)
if URE:
    U = np.load(URE); zt_, zb_ = U["z_urechiuse"][0, :2]
    for kk in [q for q in U.files if q.startswith("contur_urechiusa")]:
        P = U[kk][:-1, :2]; n = len(P); V = np.vstack([np.c_[P, np.full(n, zt_)], np.c_[P, np.full(n, zb_)]])
        F = [[i, (i + 1) % n, n + (i + 1) % n] for i in range(n)] + [[i, n + (i + 1) % n, n + i] for i in range(n)]
        nm = kk.replace("contur_", ""); out[nm + "__v"] = V; out[nm + "__f"] = np.array(F) if kk.endswith("_D") else np.array(F)[:, ::-1]
# ---- arms: sweep along the spine with parallel-transport frames
C = GB["spinare_brat_D"] - ob; dC = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
TG = np.gradient(C, axis=0); TG /= np.linalg.norm(TG, axis=1)[:, None]
e1 = np.cross(TG[0], [0, 0, 1.0]); e1 /= np.linalg.norm(e1); F1 = [e1]
for i in range(1, len(C)):
    a = F1[-1] - (F1[-1] @ TG[i]) * TG[i]; F1.append(a / np.linalg.norm(a))
F1 = np.array(F1); F2 = np.cross(TG, F1)
secs = []
for k in sorted(q for q in GB.files if q.startswith("sectiune_brat_D")):
    q = GB[k] - ob; c = q.mean(0); j = int(np.argmin(np.linalg.norm(C - c, axis=1)))
    Q = np.c_[(q - C[j]) @ F1[j], (q - C[j]) @ F2[j]]; cv = np.cov((Q - Q.mean(0)).T); w, v = np.linalg.eigh(cv)
    r = np.sqrt(2 * w); ang = np.arctan2(v[1, 1], v[0, 1]); secs.append((dC[j], r[1], r[0], ang))
secs = np.array(sorted(secs)); secs[:, 3] = np.unwrap(2 * secs[:, 3]) / 2
NS_ = 48; th = np.linspace(0, 2 * np.pi, NS_, endpoint=False); rows = []
for s0 in np.arange(0, dC[-1], DS):
    j = int(np.searchsorted(dC, s0)); j = min(j, len(C) - 1)
    ra, rb, an = (np.interp(s0, secs[:, 0], secs[:, k]) for k in (1, 2, 3))
    xy = np.c_[ra * np.cos(th), rb * np.sin(th)] @ np.array([[np.cos(an), np.sin(an)], [-np.sin(an), np.cos(an)]])
    rows.append(C[j] + np.outer(xy[:, 0], F1[j]) + np.outer(xy[:, 1], F2[j]))
A_ = np.array(rows); nr_ = len(A_); AF = []
for r in range(nr_ - 1):
    for j in range(NS_):
        a, b, c, d = r * NS_ + j, r * NS_ + (j + 1) % NS_, (r + 1) * NS_ + (j + 1) % NS_, (r + 1) * NS_ + j; AF += [[a, b, c], [a, c, d]]
AV = A_.reshape(-1, 3); AF = np.array(AF)
out["brat_spate_D__v"] = AV; out["brat_spate_D__f"] = AF; out["brat_spate_S__v"] = AV * [-1, 1, 1]; out["brat_spate_S__f"] = AF[:, ::-1]
for n_ in ("PS", "PS_rama", "PS_carena", "capac_086", "brat_spate_D"):
    v = out[n_ + "__v"]; print("PIESA %-13s %7d varfuri %7d fete  x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f" % (n_, len(v), len(out[n_ + "__f"]), *np.r_[v.min(0), v.max(0)][[0, 3, 1, 4, 2, 5]]))
np.savez(OUT, **out)
