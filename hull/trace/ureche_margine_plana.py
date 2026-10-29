# The ear's margin outline brought parallel to the PS's base (asked: g_upv_contur_margine_D parallel with pot_PS's base): the
# old margin lay on a tilted plane (z = c + k*y); it is put on the horizontal plane z = ZM (its mean height by default).
# Each vertebra moves whole by its tip's dz, then is redrawn to the standard: a C of two quarter ellipses in its plane
# y = const, from its top end (by the body) out to the margin (vertical there) and back to its bottom end.
# Usage: python ureche_margine_plana.py <ureche_vertebre npz> <out.npz> ; env ZM=(mean) GROS=(the ends' own heights) ASCUTIT=2 (<2 sharper) CORP=npz:dx (the ribs carried in onto the body) ZJOS=z (bottom line on that plane) LUNG_IN=m (ends carried in, straight, level) PRELUNG=1 (the margin carried on into the body) MARGINE_DREAPTA=1 MD_PARAM=y1a,y1b,y2a,y2b,R (straight sides + arc) MUCHIE=E (flat faces, curved edge E m) INDOIRE=deg INDOIRE_L=m (the margin's ends turned inwards) MUCHIE_PARALEL=1 (edge lines = the margin moved in) MUCHIE_SUS=m CAPAT_SUS_DREPT=1 CAPETE_ARC=1 BRAT=m (ends: side + arc + straight arm into the body) PLAN_INT=a,b (vertical inner plane x=a+by: both end lines on it, the sides carried on to it) VERTEBRE_EXTRA=n PAS_V=m
import sys, os, numpy as np
G = dict(np.load(sys.argv[1])); OUT = sys.argv[2]; M = G["contur_margine_D"].astype(float)
ZM = float(os.environ.get("ZM", "nan")); ZM = M[:, 2].mean() if np.isnan(ZM) else ZM
PI_ = tuple(float(q) for q in os.environ["PLAN_INT"].split(",")) if os.environ.get("PLAN_INT") else None   # a,b: inner plane x = a + b y (vertical)
if os.environ.get("MARGINE_DREAPTA", "0") == "1":                       # the standard: two straight sides fitted on the old margin
    o_ = np.argsort(-M[:, 1]); Mo = M[o_]                                 # (front along the PS, back along the arm) + a tangent arc
    Y1A, Y1B, Y2A, Y2B, RF_ = (float(q) for q in os.environ.get("MD_PARAM", "100,290,-280,-20,60").split(","))
    m1 = (Mo[:, 1] > Y1A) & (Mo[:, 1] < Y1B); b1, a1 = np.polyfit(Mo[m1, 1], Mo[m1, 0], 1)          # x = a + b y
    m2 = (Mo[:, 1] > Y2A) & (Mo[:, 1] < Y2B); b2, a2 = np.polyfit(Mo[m2, 1], Mo[m2, 0], 1)
    yk = (a2 - a1) / (b1 - b2); K = np.array([a1 + b1 * yk, yk])                                     # the corner
    d1 = np.array([b1, 1.0]) / np.hypot(b1, 1) * -1; d2 = np.array([b2, 1.0]) / np.hypot(b2, 1) * -1  # both pointing backwards
    th = np.arccos(np.clip(-d1 @ d2, -1, 1)); Lc = RF_ / np.tan(th / 2); t0 = K - d1 * Lc; t1 = K + d2 * Lc
    bis = d2 - d1; bis /= np.linalg.norm(bis); cc = K + bis * RF_ / np.sin(th / 2)
    a0 = np.arctan2(t0[1] - cc[1], t0[0] - cc[0]); a1_ = np.arctan2(t1[1] - cc[1], t1[0] - cc[0]); da = (a1_ - a0 + np.pi) % (2 * np.pi) - np.pi
    arc_ = cc + RF_ * np.c_[np.cos(a0 + np.linspace(0, 1, 30) * da), np.sin(a0 + np.linspace(0, 1, 30) * da)]
    yt, yb = Mo[:, 1].max(), Mo[:, 1].min()
    if PI_ is not None: yt = (a1 - PI_[0]) / (PI_[1] - b1); yb = (a2 - PI_[0]) / (PI_[1] - b2)   # PLAN_INT: the sides on to the inner plane
    P1 = np.array([a1 + b1 * yt, yt]); P2 = np.array([a2 + b2 * yb, yb])
    Mn = np.vstack([np.linspace(P1, t0, 60)[:-1], arc_, np.linspace(t1, P2, 80)[1:]])
    print("MARGINE LA STANDARD: latura fata x = %.1f %+.4f y, latura spate x = %.1f %+.4f y, colt y %.0f racordat R %.0f; fata de cea veche medie %.1f m, max %.1f m" % (
        a1, b1, a2, b2, yk, RF_, np.mean([np.min(np.linalg.norm(Mn - q[:2], axis=1)) for q in M]), np.max([np.min(np.linalg.norm(Mn - q[:2], axis=1)) for q in M])))
    M = np.c_[Mn, np.full(len(Mn), M[:, 2].mean())]
out = {"contur_margine_D": np.c_[M[:, :2], np.full(len(M), ZM)]}; mx = []
def offset_in(P, d):                                                    # a plan polyline (front -> back) moved d m inwards (-x side), along its normals
    t_ = np.gradient(P[:, :2], axis=0); t_ /= np.linalg.norm(t_, axis=1)[:, None]; n_ = np.c_[-t_[:, 1], t_[:, 0]]
    n_[n_[:, 0] > 0] *= -1; return np.c_[P[:, :2] + d * n_, P[:, 2:]]
Ms = M[np.argsort(-M[:, 1])]; MO = None
MUS = float(os.environ.get("MUCHIE_SUS", os.environ.get("MUCHIE", "20")))   # MUCHIE_SUS=m: the top edge line its own distance in (bottom = MUCHIE)
if os.environ.get("MUCHIE_PARALEL", "0") == "1": MO = offset_in(Ms, float(os.environ.get("MUCHIE", "20")))[::-1]; MOS = offset_in(Ms, MUS)[::-1]   # sorted by y for interp
TB = None
if os.environ.get("CORP"):                                             # file:dx - the body (gp_PS + gp_brat_spate_D) the ribs reach
    import trimesh; fn_, dx_ = os.environ["CORP"].split(":"); Bd = np.load(fn_); Vs, Fs, o_ = [], [], 0
    for n_ in ("gp_PS", "gp_brat_spate_D"): v_ = Bd[n_ + "__v"] + [float(dx_), 0, 0]; Vs.append(v_); Fs.append(Bd[n_ + "__f"] + o_); o_ += len(v_)
    TB = trimesh.Trimesh(np.vstack(Vs), np.vstack(Fs), process=False)
CA = TB is not None and os.environ.get("CAPETE_ARC", "0") == "1"
if CA:                                                                   # CAPETE_ARC: each end of the margin = the straight side, an arc
    import igl                                                           # (INDOIRE deg over INDOIRE_L m, inwards) and a straight arm of at
    Vb = np.asarray(TB.vertices, float); Fb = np.asarray(TB.faces, np.int64)   # least BRAT m before it enters the body (+3 m in);
    BEND = np.radians(float(os.environ.get("INDOIRE", "20"))); LB = float(os.environ.get("INDOIRE_L", "30")); ARM = float(os.environ.get("BRAT", "10"))
    def ends_arc(P):                                                     # P ends at the end; the arc starts earlier on the side if needed
        L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P[::-1, :2], axis=0), axis=1))][::-1]       # distance to the end
        for s0 in np.arange(0, 150, 1.0):
            j = int(np.searchsorted(-L, -s0)); C = np.array([np.interp(-s0, -L, P[:, 0]), np.interp(-s0, -L, P[:, 1])])
            d0 = P[-1, :2] - P[-2, :2] if s0 == 0 else C - P[max(j - 1, 0), :2]; d0 /= np.linalg.norm(d0)
            turn = 1 if d0[1] > 0 else -1                                    # rotate towards -x
            tt = np.arange(1, 400, 1.0); ang = turn * BEND * np.minimum(tt / LB, 1.0)
            D = np.c_[d0[0] * np.cos(ang) - d0[1] * np.sin(ang), d0[0] * np.sin(ang) + d0[1] * np.cos(ang)]; Q = C + np.cumsum(D, axis=0)
            w = igl.winding_number(Vb, Fb, np.c_[Q, np.full(len(Q), ZM)]); ins = np.where(w > 0.5)[0]
            if not len(ins): continue
            i_ = ins[0]
            if tt[i_] - LB >= ARM:
                ex = [Q[i_] + D[i_] * 1.5, Q[i_] + D[i_] * 3]
                return np.vstack([P[:j, :2], C, Q[:i_ + 1], ex]), s0, tt[i_] - LB
        raise SystemExit("CAPETE_ARC: no fit")
    Mfb = M[np.argsort(-M[:, 1])]
    B_, sb, ab = ends_arc(Mfb); F_, sf, af = ends_arc(B_[::-1]); Mn = F_[::-1]
    d_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Mn, axis=0), axis=1))]; u_ = np.arange(0, d_[-1], 1.0); Mn = np.c_[np.interp(u_, d_, Mn[:, 0]), np.interp(u_, d_, Mn[:, 1])]
    M = np.c_[Mn, np.full(len(Mn), ZM)]; out["contur_margine_D"] = M.copy()
    if MO is not None: MO = offset_in(M, float(os.environ.get("MUCHIE", "20")))[::-1]
    print("CAPETE ARC: fata - arcul porneste %.0f m inainte de capatul laturii, brat drept %.0f m pana intra in PS; spate - arcul la %.0f m, brat %.0f m pana intra in brat; R arc %.0f m; y %.0f..%.0f" % (
        sf, af, sb, ab, LB / BEND, M[:, 1].min(), M[:, 1].max()))
VXS = os.environ.get("VERTEBRE_EXTRA", "0").split(","); VXF, VXB = int(VXS[0]), int(VXS[-1]); VX = max(VXF, VXB)   # VERTEBRE_EXTRA=n or front,back: more vertebrae at the ends, every PAS_V m
if VX:                                                                   # (copies of the end ones moved in y, then rebuilt like all)
    PV = float(os.environ.get("PAS_V", "20")); vk_ = sorted((q for q in G if q.startswith("vertebra_")), key=lambda q: G[q][0, 1])
    for i in range(1, VXF + 1): G["vertebra_f%d_D" % i] = G[vk_[-1]] + [0, i * PV, 0]
    for i in range(1, VXB + 1): G["vertebra_s%d_D" % i] = G[vk_[0]] - [0, i * PV, 0]
for k in sorted(q for q in G if q.startswith("vertebra_")):
    A = G[k].astype(float); y = float(np.median(A[:, 1])); it = int(np.argmax(A[:, 0])); dz = ZM - A[it, 2]
    if CA and not (M[:, 1].min() + 2 < y < M[:, 1].max() - 2): print("vertebra %s (y %.0f) dincolo de capatul marginii - scoasa (e in corp)" % (k, y)); continue
    A[:, 2] += dz                                                        # the whole vertebra moved with the margin
    xm = float(np.interp(y, M[np.argsort(M[:, 1]), 1], M[np.argsort(M[:, 1]), 0]))   # its tip on the (moved) margin
    e1, e2 = (A[0], A[-1]) if A[0, 2] > A[-1, 2] else (A[-1], A[0])      # top / bottom ends (by the body)
    GR = float(os.environ.get("GROS", "0"))                             # GROS=m: the ear's thickness at the body (ends at ZM +- GROS/2)
    if GR > 0: e1 = e1.copy(); e2 = e2.copy(); e1[2] = ZM + GR / 2; e2[2] = ZM - GR / 2
    ZJ = os.environ.get("ZJOS")                                        # ZJOS=z: the ribs' bottom line on that plane (the PS base), thickness kept
    if ZJ and GR > 0: e2[2] = float(ZJ); e1[2] = float(ZJ) + GR
    if TB is not None:                                                   # CORP: both ends carried in (level) onto the body's surface
        sec = TB.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
        if sec is not None:
            for e_ in (e1, e2):
                xs = []
                for L in sec.discrete:
                    for a_, b_ in zip(L[:-1], L[1:]):
                        if (a_[2] - e_[2]) * (b_[2] - e_[2]) <= 0 and a_[2] != b_[2]: xs.append(a_[0] + (e_[2] - a_[2]) * (b_[0] - a_[0]) / (b_[2] - a_[2]))
                xs = [x for x in xs if x < xm]
                if xs: e_[0] = max(xs)
    if PI_ is not None: e1 = e1.copy(); e2 = e2.copy(); e1[0] = e2[0] = PI_[0] + PI_[1] * y   # PLAN_INT: both ends on the inner plane
    th = np.linspace(0, np.pi / 2, 40)                                   # the standard: a C of two quarter ellipses in the plane y,
    q = 2.0 / float(os.environ.get("ASCUTIT", "2"))                      # superellipse: 2 = ellipse, <2 = sharper towards the tip
    MU = float(os.environ.get("MUCHIE", "0"))                            # MUCHIE=E: flat top and bottom (one plane each, all along),
    if MU > 0:                                                           # only the last E m curve into the tip - the same edge everywhere
        E1 = min(MU, 0.8 * (xm - e1[0])); E2 = min(MU, 0.8 * (xm - e2[0]))
        if MO is not None:                                               # MUCHIE_PARALEL: the edge starts on the margin moved E m in (normal)
            xo = float(np.interp(y, MO[:, 1], MO[:, 0])); xs_ = float(np.interp(y, MOS[:, 1], MOS[:, 0]))
            if PI_ is not None: xo = max(xo, e1[0] + 0.5); xs_ = max(xs_, e1[0] + 0.5)
            else: e1[0] = min(e1[0], xo - 1); e2[0] = min(e2[0], xo - 1)                              # narrow front: the ends carried in past it
            E1 = xm - xs_; E2 = xm - xo
        up = np.vstack([np.c_[np.linspace(e1[0], xm - E1, 12)[:-1], np.full(11, e1[2])], np.c_[xm - E1 + E1 * np.sin(th) ** q, ZM + (e1[2] - ZM) * np.cos(th) ** q]])
        dn = np.vstack([np.c_[xm - E2 + E2 * np.sin(th[::-1][1:]) ** q, ZM + (e2[2] - ZM) * np.cos(th[::-1][1:]) ** q], np.c_[np.linspace(xm - E2, e2[0], 12)[1:], np.full(11, e2[2])]])
    else:
        up = np.c_[e1[0] + (xm - e1[0]) * np.sin(th) ** q, ZM + (e1[2] - ZM) * np.cos(th) ** q]          # vertical at the tip, level at the ends
        dn = np.c_[e2[0] + (xm - e2[0]) * np.sin(th[::-1][1:]) ** q, ZM + (e2[2] - ZM) * np.cos(th[::-1][1:]) ** q]
    C = np.vstack([up, dn])
    LI = float(os.environ.get("LUNG_IN", "0"))                           # both ends carried on inwards LI m, straight, level (parallel to the base)
    if LI > 0:
        a0 = np.c_[np.linspace(C[0, 0] - LI, C[0, 0], 12)[:-1], np.full(11, C[0, 1])]; a1 = np.c_[np.linspace(C[-1, 0], C[-1, 0] - LI, 12)[1:], np.full(11, C[-1, 1])]
        C = np.vstack([a0, C, a1])
    out[k] = np.c_[C[:, 0], np.full(len(C), y), C[:, 1]]; mx.append(abs(dz))
if os.environ.get("CAPAT_SUS_DREPT", "0") == "1":                       # the top inner ends on one straight line, moved in until no vertebra
    vk = [k for k in out if k.startswith("vertebra_")]                  # gets shorter - each top run carried on, level, to that line
    E_ = np.array([[out[k][0, 1], out[k][0, 0]] for k in vk]); b_, a_ = np.polyfit(E_[:, 0], E_[:, 1], 1); a_ += min(0.0, (E_[:, 1] - (a_ + b_ * E_[:, 0])).min())
    for k in vk:
        V_ = out[k]; xl = a_ + b_ * V_[0, 1]
        out[k] = np.vstack([np.c_[np.linspace(xl, V_[0, 0], 12)[:-1], np.full(11, V_[0, 1]), np.full(11, V_[0, 2])], V_])
    print("CAPAT SUS DREPT: x = %.1f %+.4f y; vertebre lungite cu %.0f..%.0f m" % (a_, b_, (E_[:, 1] - (a_ + b_ * E_[:, 0])).min(), (E_[:, 1] - (a_ + b_ * E_[:, 0])).max()))
if TB is not None and os.environ.get("PRELUNG", "0") == "1" and not CA:           # the margin carried on, straight, at both ends until inside the body
    import igl
    Mm = out["contur_margine_D"]; Mm = Mm[np.argsort(-Mm[:, 1])]; Vb = np.asarray(TB.vertices, float); Fb = np.asarray(TB.faces, np.int64)
    BEND = np.radians(float(os.environ.get("INDOIRE", "0"))); LB = float(os.environ.get("INDOIRE_L", "30"))
    def grow(P0, P1):                                                    # from P1 along P1 - P0 until inside, then 3 m more; with INDOIRE the
        d0 = (P1 - P0) / np.linalg.norm(P1 - P0); pts = []; q_ = P1.copy()   # direction turns smoothly inwards (towards -x) over LB m (an arc)
        for t_ in np.arange(1, 200, 1.0):
            a_ = BEND * min(t_ / LB, 1.0); turn = np.sign(np.cross([d0[0], d0[1], 0], [-1, 0, 0])[2]) or 1
            ca, sa = np.cos(turn * a_), np.sin(turn * a_); d_ = np.array([d0[0] * ca - d0[1] * sa, d0[0] * sa + d0[1] * ca, 0.0])
            q_ = q_ + d_; pts.append(q_.copy())
            if igl.winding_number(Vb, Fb, q_[None].astype(np.float64))[0] > 0.5:
                pts += [q_ + d_ * 1.5, q_ + d_ * 3]; break
        return np.array(pts)
    fa = grow(Mm[3], Mm[0]); ba = grow(Mm[-4], Mm[-1])
    out["contur_margine_D"] = np.vstack([fa[::-1], Mm, ba]); print("MARGINE prelungita: fata %.0f m, spate %.0f m (pana intra in PS / brat)" % (len(fa), len(ba)))
if MO is not None:
    Mf_ = out["contur_margine_D"]; O_ = offset_in(Mf_, float(os.environ.get("MUCHIE", "20"))); OS_ = offset_in(Mf_, MUS)
    vz = [out[k] for k in out if k.startswith("vertebra_")]; zt_ = max(v[:, 2].max() for v in vz); zb_ = min(v[:, 2].min() for v in vz)
    if PI_ is not None:
        O_ = O_[O_[:, 0] > PI_[0] + PI_[1] * O_[:, 1] + 0.5]             # the edge lines stop at the inner plane
        OS_ = OS_[OS_[:, 0] > PI_[0] + PI_[1] * OS_[:, 1] + 0.5]
        yy_ = np.linspace(Mf_[:, 1].max(), Mf_[:, 1].min(), 200); xl_ = PI_[0] + PI_[1] * yy_
        out["linie_capat_sus_D"] = np.c_[xl_, yy_, np.full(200, zt_)]; out["linie_capat_jos_D"] = np.c_[xl_, yy_, np.full(200, zb_)]
    out["linie_muchie_sus_D"] = np.c_[OS_[:, :2], np.full(len(OS_), zt_)]; out["linie_muchie_jos_D"] = np.c_[O_[:, :2], np.full(len(O_), zb_)]
    print("LINII MUCHIE: conturul mutat %.0f m spre interior (normal), pe toata lungimea, z %.1f / %.1f" % (float(os.environ.get("MUCHIE", "20")), zt_, zb_))
print("MARGINE URECHE: din planul inclinat (z %.1f..%.1f) in planul orizontal z %.1f, paralel cu baza PS; %d vertebre mutate intregi (max %.1f m) si refacute ca C curat (2 sferturi de elipsa, plan y)" % (
    M[:, 2].min(), M[:, 2].max(), ZM, len(mx), max(mx)))
np.savez(OUT, **out)
