# Ribs (nervuri) for the PS edge along the rim's outer outline drawn on sep_PS (asked: the outline's tip a bit forward and
# fuller - from ghid_rama_curat.py - and now the ribs). Every PAS m along the outline (right half, mirrored), in the
# vertical plane across it: a C of two quarter ellipses (the guide-line standard) - from the outline point on the flat
# bottom (z ZP) out to the PS side's outermost point (its distance E beyond the outline and height ZE, measured on the PS's
# own section there, at least EMIN m) and back in to the top surface above the outline point (ZT, measured). Where the
# outline runs past the PS (the new tip) the nearest measured values are used.
# Usage: python ghid_ps_nervuri.py <ghid outline npz (contur_rama_exterior)> <sep_PS npz v,f (ship coords)> <out.npz>
# NV_LINIE_NPZ=file:key: the inner line = that guide exactly (e.g. the hood's base outline).
# NV_LINIE_Z=z|mediana: the inner line flat in one horizontal plane; NV_EASE=m the ribs' last m eased onto it.
# NV_PERECHI=fractie: each rib ends on the inner line at the same fraction of the way round (from the tip).
# NV_LINIE_CAPAC=<hood npz>: that line = the hood's outline from above (+NV_CAPAC_OFF m).
# NV_LINIE=1: one continuous inner line on the top (outline NV_W in, the flat zone's edge along the hood), ribs end on it.
# env PAS=40 EMIN=1 NV_MOD=c|sectiune|curat NV_W=40 NV_PLAT=77,47,279 (sectiune: the PS's own section, stopped at the flat zone)
import sys, os, numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
G = np.load(sys.argv[1]); D = np.load(sys.argv[2]); OUT = sys.argv[3]; PAS, EMIN = float(os.environ.get("PAS", "40")), float(os.environ.get("EMIN", "1"))
E = G["contur_rama_exterior"]; ZP = float(E[0, 2]); P2 = E[:, :2]
t = trimesh.Trimesh(D["v"], D["f"], process=False)
cc = np.vstack([P2, P2[:1]]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cc, axis=0), axis=1))]; st = []
for s_ in np.arange(0, d[-1] / 2 + 0.1, PAS):
    i = np.searchsorted(d, s_); p = np.array([np.interp(s_, d, cc[:, 0]), np.interp(s_, d, cc[:, 1])])
    if p[0] < -0.1: continue
    tg = cc[min(i + 1, len(cc) - 1)] - cc[max(i - 1, 0)]; tg /= np.linalg.norm(tg); nout = np.array([-tg[1], tg[0]])   # clockwise: outward = left
    sec = t.section(plane_origin=[p[0], p[1], ZP], plane_normal=[tg[0], tg[1], 0]); m = None
    if sec is None: sec = t.section(plane_origin=[p[0] + 0.01 * tg[0], p[1] + 0.01 * tg[1], ZP], plane_normal=[tg[0], tg[1], 0])   # plane on a vertex
    if sec is not None:
        zc, best = [], None                            # top: the highest crossing of the section with the vertical above p
        for L in sec.discrete:
            u = (L[:, :2] - p) @ nout; w = (L[:, :2] - p) @ tg
            for a_, b_ in zip(range(len(L) - 1), range(1, len(L))):
                if u[a_] * u[b_] <= 0 and u[a_] != u[b_]: zc.append(L[a_, 2] + (L[b_, 2] - L[a_, 2]) * (0 - u[a_]) / (u[b_] - u[a_]))
            ok = np.abs(u) < 60
            if ok.any():
                j = np.argmax(np.where(ok, u, -1e9))
                if best is None or u[j] > best[0]: best = (u[j], L[j, 2])
        if best is not None: m = (best[0], best[1], max(zc) if zc else np.nan)
    st.append((p, nout, m))
MOD = os.environ.get("NV_MOD", "c")                    # "sectiune": the rib = sep_PS's own section (smoothed), from the outline
W_IN, FZ = float(os.environ.get("NV_W", "40")), [float(q) for q in os.environ.get("NV_PLAT", "77,47,279").split(",")]
from scipy.ndimage import gaussian_filter1d             # point on the bottom round the side and over the top, inwards W_IN m or
def rib_sectiune(p, tg, nout):                         # to the hood's flat zone (|x| <= FZ0, y FZ1..FZ2), whichever comes first
    sec = None
    for dj in (0.0, 0.01, -0.01):
        sec = t.section(plane_origin=[p[0] + dj * tg[0], p[1] + dj * tg[1], ZP], plane_normal=[tg[0], tg[1], 0])
        if sec is not None: break
    if sec is None: return None
    L = max(sec.discrete, key=lambda q: len(q)); L = L[:-1] if np.allclose(L[0], L[-1]) else L
    u = (L[:, :2] - p) @ nout; i0 = int(np.argmin(np.abs(u) + np.abs(L[:, 2] - ZP)))
    n = len(L); dirn = 1 if u[(i0 + 1) % n] > u[(i0 - 1) % n] else -1; pts = [np.array([p[0], p[1], ZP])]; wend = W_IN
    if FZ[1] <= p[1] <= FZ[2]: wend = min(W_IN, abs(p[0]) - FZ[0])
    hit = hit_force[0] if hit_force[0] is not None else lin_hit(p, nout)
    if hit is not None: hit = (float(np.linalg.norm(hit[1][:2] - p)), hit[1]); wend = hit[0]
    k = i0; zmax_seen = ZP
    for _ in range(n):
        q = L[k]; uu = (q[:2] - p) @ nout; zmax_seen = max(zmax_seen, q[2])
        if q[2] > ZP + 2 and uu < -wend and q[2] >= zmax_seen - 30: break
        if q[2] >= ZP - 0.5: pts.append(q)
        k = (k + dirn) % n
    P = np.array(pts); dd = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; uu_ = np.arange(0, dd[-1], 0.5)
    R = np.c_[[np.interp(uu_, dd, P[:, c]) for c in range(3)]].T
    if len(R) > 8:
        a, b = R[0].copy(), R[-1].copy(); R = np.c_[[gaussian_filter1d(R[:, c], 3, mode="nearest") for c in range(3)]].T; R[0], R[-1] = a, b
    o = (R[:, :2] - p) @ tg; R[:, :2] -= np.outer(o, tg)                     # exactly in the plane
    if hit is not None:                                # ends exactly on the inner line (the last 6 m eased onto it)
        EA = float(os.environ.get("NV_EASE", "6")); w_ = np.clip(1 - (np.linalg.norm(R[:, :2] - R[-1, :2], axis=1)) / EA, 0, 1); w_ = w_ * w_ * (3 - 2 * w_)
        R += w_[:, None] * (hit[1] - R[-1])
    return R
LIN = None                                             # NV_LINIE=1: the ribs' inner line - one continuous line on the top: the
if os.environ.get("NV_LINIE", "0") == "1":             # outline W_IN m in, and along the hood the flat zone's edge (inner region =
    import cv2                                         # outline eroded W_IN  U  flat zone), smoothed, laid on the top surface
    PXl = 0.25; X0l, Y0l = -200.0, -80.0; Wl, Hl = int(400 / PXl), int(600 / PXl)
    pxl = lambda q: np.c_[(q[:, 0] - X0l) / PXl, (q[:, 1] - Y0l) / PXl].astype(np.int32)
    Mo = np.zeros((Hl, Wl), np.uint8); cv2.fillPoly(Mo, [pxl(P2)], 1); r_ = int(W_IN / PXl)
    Mi = cv2.erode(Mo, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r_ + 1, 2 * r_ + 1)))
    jj, ii = np.mgrid[0:Hl, 0:Wl]; Xg = ii * PXl + X0l; Yg = jj * PXl + Y0l
    zf = (Yg >= FZ[1]) & (Yg <= FZ[2])                 # along the hood: exactly the flat zone's edge
    Mi = ((Mi.astype(bool) & ~(zf & (np.abs(Xg) > FZ[0]))) | (zf & (np.abs(Xg) <= FZ[0]))) & Mo.astype(bool)
    CAP = os.environ.get("NV_LINIE_CAPAC")             # npz v,f: the line = the hood's own outline seen from above, NV_CAPAC_OFF m out
    if CAP:
        Hc = np.load(CAP); Mi = np.zeros((Hl, Wl), np.uint8)
        for tri in Hc["v"][Hc["f"]][:, :, :2]: cv2.fillConvexPoly(Mi, pxl(tri), 1)
        ro = int(float(os.environ.get("NV_CAPAC_OFF", "2")) / PXl); Mi = cv2.dilate(Mi, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ro + 1, 2 * ro + 1))).astype(bool)
    Mi = Mi | np.flip(Mi, 1)
    cs, _ = cv2.findContours(Mi.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
    c = np.c_[c[:, 0] * PXl + X0l, c[:, 1] * PXl + Y0l]; cc2 = np.vstack([c, c[:1]]); d2 = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cc2, axis=0), axis=1))]
    u2 = np.arange(0, d2[-1], 0.5); c = np.c_[np.interp(u2, d2, cc2[:, 0]), np.interp(u2, d2, cc2[:, 1])]
    SM = float(os.environ.get("NV_NETED", "6")); c = np.c_[gaussian_filter1d(c[:, 0], SM / 0.5, mode="wrap"), gaussian_filter1d(c[:, 1], SM / 0.5, mode="wrap")]
    c = (c + np.c_[-c[::-1, 0], c[::-1, 1]][np.argsort(np.arange(len(c)))]) / 2 if False else c
    Pt, _ = trimesh.sample.sample_surface(t, 2500000, seed=3); Pt = Pt[Pt[:, 2] > ZP + 5]
    ix = ((Pt[:, 0] - X0l) / 1.0).astype(int); iy = ((Pt[:, 1] - Y0l) / 1.0).astype(int); Zt = np.full((600, 400), -np.inf); np.maximum.at(Zt, (iy, ix), Pt[:, 2])
    zl = Zt[((c[:, 1] - Y0l) / 1.0).astype(int), ((c[:, 0] - X0l) / 1.0).astype(int)]
    ok = np.isfinite(zl); zl = np.interp(np.arange(len(c)), np.where(ok)[0], zl[ok]); zl = gaussian_filter1d(zl, 4 / 0.5, mode="wrap")
    LIN = np.c_[c, zl]
    LN = os.environ.get("NV_LINIE_NPZ")                # file:key - the line taken as is from another guide (kept identical to it)
    if LN: fn_, kk_ = LN.split(":"); LIN = np.load(fn_)[kk_].astype(float); LIN = LIN[:-1] if np.allclose(LIN[0], LIN[-1]) else LIN; c = LIN[:, :2]; zl = LIN[:, 2]
    LZ = os.environ.get("NV_LINIE_Z")                  # the line in ONE horizontal plane (parallel to the outline's): a height or "mediana"
    if LZ: LIN[:, 2] = np.median(zl) if LZ == "mediana" else float(LZ)
    dl = np.diff(np.vstack([c, c[:1]]), axis=0); ang = np.degrees(np.abs(np.angle(np.exp(1j * (np.arctan2(dl[1:, 1], dl[1:, 0]) - np.arctan2(dl[:-1, 1], dl[:-1, 0]))))))
    print("LINIA DE SUS A NERVURILOR: %d puncte, x %.0f..%.0f, y %.0f..%.0f, z %.0f..%.0f (pe punte); cea mai mare frangere intre pasi de 0,5 m %.1f grd" % (
        len(LIN), c[:, 0].min(), c[:, 0].max(), c[:, 1].min(), c[:, 1].max(), zl.min(), zl.max(), ang.max()))
def lin_hit(p, nout):                                  # where the rib's line (p - u nout, u > 0) meets the inner line, in plan
    if LIN is None: return None
    q = LIN[:, :2] - p; along = q @ (-nout); off = q @ np.array([nout[1], -nout[0]]); cand = np.where((along > 0) & (along < float(os.environ.get("NV_MAXL", str(1.5 * W_IN)))) & (np.abs(off) < 1.0))[0]
    if not len(cand):                                  # (a corner: the rib's line misses it nearby) -> the line's nearest point
        j = int(np.argmin(np.linalg.norm(LIN[:, :2] - (p - W_IN * nout), axis=1))); return float((LIN[j, :2] - p) @ (-nout)), LIN[j]
    j = cand[np.argmin(along[cand])]; return along[j], LIN[j]
hit_force = [None]
st_s = [s0 for s0 in np.arange(0, d[-1] / 2 + 0.1, PAS) if np.interp(s0, d, cc[:, 0]) >= -0.1]
if LIN is not None:
    j0 = int(np.argmax(LIN[:, 1] - 5 * np.abs(LIN[:, 0]))); LIN = np.roll(LIN, -j0, 0)
    ar_ = 0.5 * np.sum(LIN[:, 0] * np.roll(LIN[:, 1], -1) - np.roll(LIN[:, 0], -1) * LIN[:, 1])
    if ar_ > 0: LIN = np.r_[LIN[:1], LIN[1:][::-1]]                                   # clockwise, like the outline
    dL = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([LIN, LIN[:1]])[:, :2], axis=0), axis=1))]
    def LIN_at(f):
        u = f * dL[-1]; LL = np.vstack([LIN, LIN[:1]]); return np.array([np.interp(u, dL, LL[:, c]) for c in range(3)])
ms = [k for k, q in enumerate(st) if q[2] is not None and not np.isnan(q[2][2])]
import spate_ps as SPS
out = {"contur_rama_exterior_pe_PS": np.c_[E[:, :2], E[:, 2] + SPS.dz(E[:, 1])]}; k_ = 0; rep = []
if LIN is not None: out["contur_sus_nervuri"] = LIN
EZ = []                                                # NV_MOD=curat: the measured bulge (e, ze) smoothed along the stations
for k, (p, nout, m) in enumerate(st):
    mm = m if (m is not None and not np.isnan(m[2])) else st[min(ms, key=lambda q: abs(q - k))][2]; EZ.append((max(mm[0], EMIN), mm[1]))
EZ = np.array(EZ); EZs = np.c_[gaussian_filter1d(np.r_[EZ[::-1], EZ, EZ[::-1]][:, 0], 1.0)[len(EZ):2 * len(EZ)], gaussian_filter1d(np.r_[EZ[::-1], EZ, EZ[::-1]][:, 1], 1.0)[len(EZ):2 * len(EZ)]]
for k, (p, nout, m) in enumerate(st):
    if m is None or np.isnan(m[2]): m = st[min(ms, key=lambda q: abs(q - k))][2]; src = "vecin"
    else: src = "masurat"
    e_ = max(m[0], EMIN); ze, zt = m[1], m[2]; ze = min(max(ze, ZP + 1), zt - 1)
    th = np.linspace(0, np.pi / 2, 20)
    low = np.c_[e_ * np.sin(th), ze - (ze - ZP) * np.cos(th)]; up = np.c_[e_ * np.cos(th[1:]), ze + (zt - ze) * np.sin(th[1:])]
    C = np.vstack([low, up]); X = np.c_[p[0] + C[:, 0] * nout[0], p[1] + C[:, 0] * nout[1], C[:, 1]]
    if MOD == "curat" and LIN is not None:            # a clean C: quarter ellipse out to the bulge (vertical there), quarter ellipse
        T_ = LIN_at(st_s[k] / d[-1]) if os.environ.get("NV_PERECHI") == "fractie" else lin_hit(p, nout)[1]   # up and in to the
        v_ = p - T_[:2]; w_ = np.linalg.norm(v_); nr = v_ / w_; e2, z2 = EZs[k]; zl_ = T_[2]; z2 = min(max(z2, ZP + 1), zl_ - 1)   # line
        import spate_ps as SPS; zb_ = ZP + float(SPS.dz(p[1]))                    # (the back: bottom dropped, ribs squarer)
        C2 = SPS.rib(e2, z2, zb_, zl_, w_, p[1], 24, 60); X = np.c_[p[0] + C2[:, 0] * nr[0], p[1] + C2[:, 0] * nr[1], C2[:, 1]]; src += ", curat (2 sferturi de elipsa)"
    if MOD == "sectiune":
        hT = lin_hit(p, nout); nr = nout
        if LIN is not None and os.environ.get("NV_PERECHI") == "fractie":   # paired in order: the same fraction of the way round
            f_ = st_s[k] / d[-1]; hT = (0.0, LIN_at(f_)); hit_force[0] = hT
        if hT is not None: v_ = p - hT[1][:2]; nr = v_ / np.linalg.norm(v_)          # the rib's plane: through p and its end on the line
        Rr = rib_sectiune(p, np.array([nr[1], -nr[0]]), nr)
        if Rr is not None: X = Rr; src += ", sectiune PS"
    out["nervura_%02d_D" % k_] = X
    if p[0] > 0.1: out["nervura_%02d_S" % k_] = X * [-1, 1, 1]
    rep.append("%02d (x %.0f, y %.0f): iese %.1f m la z %.0f, sus z %.0f; capat z %.0f la %.0f m inauntru [%s]" % (k_, p[0], p[1], e_, ze, zt, X[-1, 2], -((X[-1, :2] - p) @ nout), src)); k_ += 1
print("NERVURI PS: %d pe dreapta (+ oglinda), la %.0f m, fiecare un C din 2 sferturi de elipsa in planul vertical de-a curmezisul conturului" % (k_, PAS))
for r in rep: print("   " + r)
np.savez(OUT, **out)
