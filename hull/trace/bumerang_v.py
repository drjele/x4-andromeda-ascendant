# The 103 band as a boomerang (asked: of the right outline keep only its right part - the very open V - and the other
# guides, also V-shaped, perpendicular to it with their tip on it; a 3D form like a boomerang): the spine = the band's
# outer edge from its front tip to its rear tip (smoothed); every STEP m along it a V in the vertical plane across the
# spine, its tip on the spine at the band's middle height there, its two arms going inwards (one up, one down) at HALF
# degrees each side of the horizontal (the PS nose's angle), as long as the band is wide there (capped). Writes the guides.
# BV_SPINARE=m (spine smoothing, ends kept, mirrored run-on), BV_LUNGIMI=m (arms' lengths and tips' heights smoothed along).
# BV_BARA=R: the spine as a bent bar (two straight runs + one arc of radius R at the V's corner), one section all along.
# BV_DEPARTE=m (bar moved out), BV_COT_DY=m (its corner moved forward), BV_GROS=m (vertical distance between the rails).
# BV_LIPIT=<npz:v,f;npz:v,f>: rails glued to those pieces (spine at BV_Z, rails BV_GROS apart, straight in side view).
# BV_SINE_DREPTE=1: each rail a bent bar too (through its glued front end, its point at the spine's corner, its rear end).
# BV_SINE_DX=m: both rails moved in x (seen from above: negative = left).
# BV_JOS_SUB_SUS=1: the lower rail is the upper one lowered by BV_GROS (same vertical plane).
# BV_JOS_ROT=deg (lower rail turned in plan about its middle), BV_SUS_DX / BV_SUS_DZ (upper rail moved in / up).
# BV_JOS_DX=m (lower rail moved in x); BV_SPINARE_LUNGA=1 (spine ends carried on straight until they touch the pieces).
# BV_LINGURA=w: each V arm a curve (a lying spoon) leaving the rail along the piece's surface (weight w), bending to the tip.
# BV_TRAPEZ=h: each V a small trapezoid - its tip a vertical side h m high centred on the spine.
# Usage: python bumerang_v.py <bumerang_ghidaje.npz> <teren_103.npz> <out.npz> <sheet.png> [step] [half_deg] [max_arm]
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d, map_coordinates
B = np.load(sys.argv[1]); T = np.load(sys.argv[2]); OUT, SHEET = sys.argv[3], sys.argv[4]
STEP = float(sys.argv[5]) if len(sys.argv) > 5 else 20.0; HALF = float(sys.argv[6]) if len(sys.argv) > 6 else 25.9; AMAX = float(sys.argv[7]) if len(sys.argv) > 7 else 45.0
ol = B["contur_dreapta"][:, :2]; it, ib = np.argmax(ol[:, 1]), np.argmin(ol[:, 1])
seg1 = ol[min(it, ib):max(it, ib) + 1]; seg2 = np.vstack([ol[max(it, ib):], ol[:min(it, ib) + 1]])
sp = seg1 if seg1[:, 0].mean() > seg2[:, 0].mean() else seg2              # the outer (right) side: the very open V
if sp[0, 1] < sp[-1, 1]: sp = sp[::-1]                                  # from the front tip to the rear tip
d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(sp, axis=0), axis=1))]; u = np.arange(0, d[-1], 1.0)
import os
SS = float(os.environ.get("BV_SPINARE", "4")); SL = float(os.environ.get("BV_LUNGIMI", "0"))   # smoothing (m) of the spine; of the
sp = np.stack([np.interp(u, d, sp[:, i]) for i in (0, 1)], 1); e0, e1 = sp[0].copy(), sp[-1].copy()   # arms' lengths and the tips'
pad = int(4 * SS); ext = np.vstack([2 * sp[0] - sp[pad:0:-1], sp, 2 * sp[-1] - sp[-2:-pad - 2:-1]])   # height along the spine (0 = off)
sp = np.stack([gaussian_filter1d(ext[:, i], SS) for i in (0, 1)], 1)[pad:pad + len(u)]; sp[0], sp[-1] = e0, e1   # ends kept
RB = float(os.environ.get("BV_BARA", "0"))                              # a bent bar: two straight runs from the tips to the V's corner
if RB:                                                                  # (the outer edge's farthest point), joined by one arc of radius RB
    DEP = float(os.environ.get("BV_DEPARTE", "0")); DY = float(os.environ.get("BV_COT_DY", "0"))   # the bar moved DEP m away from
    Vx = sp[np.argmax(sp[:, 0])] + [DEP + float(os.environ.get("BV_COT_DX", "0")), DY]; P0, P1 = e0 + [DEP, 0], e1 + [DEP, 0]   # corner DY m
                                                                        # forward, BV_COT_DX m sideways (negative = flatter V, closer in)
    u1 = (P0 - Vx) / np.linalg.norm(P0 - Vx); u2 = (P1 - Vx) / np.linalg.norm(P1 - Vx); phi = np.arccos(np.clip(u1 @ u2, -1, 1)) / 2
    tl = RB / np.tan(phi); T1, T2 = Vx + u1 * tl, Vx + u2 * tl; bis = (u1 + u2) / np.linalg.norm(u1 + u2); Cc = Vx + bis * RB / np.sin(phi)
    a1, a2 = np.arctan2(*(T1 - Cc)[::-1]), np.arctan2(*(T2 - Cc)[::-1]); da = np.angle(np.exp(1j * (a2 - a1)))
    arc = Cc + RB * np.stack([np.cos(a1 + np.linspace(0, da, max(int(abs(da) * RB), 8))), np.sin(a1 + np.linspace(0, da, max(int(abs(da) * RB), 8)))], 1)
    def ln(p, q): n_ = max(int(np.linalg.norm(q - p)), 2); return p + np.outer(np.arange(n_) / n_, q - p)
    poly = np.vstack([ln(P0, T1), arc, ln(T2, P1), [P1]]); dd = np.r_[0, np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))]
    u = np.arange(0, dd[-1], 1.0); sp = np.stack([np.interp(u, dd, poly[:, i]) for i in (0, 1)], 1)
    print("BARA: colt (%.0f, %.0f), unghiul V-ului %.0f grade, arc raza %.0f m (tangente la %.0f m de colt), brate drepte %.0f / %.0f m" % (
        *Vx, np.degrees(2 * phi), RB, tl, np.linalg.norm(T1 - P0), np.linalg.norm(P1 - T2)))
x0, y0, C = float(T["x0"]), float(T["y0"]), float(T["cell"]); g = lambda F, P: map_coordinates(F.astype(float), [(P[:, 1] - y0) / C - 0.5, (P[:, 0] - x0) / C - 0.5], order=1, mode="nearest")
foot = T["foot"].astype(float)
tg = np.gradient(sp, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]; nin = np.stack([-tg[:, 1], tg[:, 0]], 1)
probe = sp + 5 * nin; nin = nin * (1 if (g(foot, probe) > 0.5).mean() >= 0.5 else -1)   # one side into the band for the whole spine
if RB: nin = nin * (1 if nin[:, 0].mean() < 0 else -1)                 # the bar: inwards = towards the ship's middle (the PS)
                                                                        # (per point it flipped near the tips)
inner = sp + 3 * nin; zm = (g(T["top"], inner) + g(T["bot"], inner)) / 2; zm = gaussian_filter1d(zm, max(6, SL), mode="nearest")
W = np.zeros(len(sp))                                                   # the band's width across the spine at every metre
for i in range(len(sp)):
    for s_ in np.arange(1, 120, 1.0):
        if g(foot, (sp[i] + s_ * nin[i])[None])[0] < 0.5: break
        W[i] = s_
W = np.clip(W, 8.0, AMAX)
if SL: W = gaussian_filter1d(W, SL, mode="nearest")
if RB:                                                                  # a bar: one section all along (median width), the tips' height
    W[:] = float(os.environ.get("BV_LATIME", np.median(W)))             # straight from the front to the back
    if os.environ.get("BV_GROS"): W[:] = float(os.environ["BV_GROS"]) / (2 * np.sin(np.radians(HALF)))   # the rails BV_GROS m apart
    zm = np.linspace(np.median(zm[:60]), np.median(zm[-60:]), len(zm))
G = {"spinare": np.c_[sp, zm]}; th = np.radians(HALF); k = 0
for i in np.arange(0, len(sp), int(STEP)):
    L = W[i]; tip = np.r_[sp[i], zm[i]]; dirh = np.r_[nin[i], 0]
    up = tip + L * (np.cos(th) * dirh + np.r_[0, 0, np.sin(th)]); dn = tip + L * (np.cos(th) * dirh - np.r_[0, 0, np.sin(th)])
    G["v_%02d" % k] = np.stack([up, tip, dn]); k += 1
vk = sorted(q for q in G if q.startswith("v_"))                        # the arms' ends as rails (shown, and measured)
G["sina_sus"] = np.stack([G[q][0] for q in vk]); G["sina_jos"] = np.stack([G[q][2] for q in vk])
def turn(P):
    t_ = np.diff(P[:, :2], axis=0); h_ = np.arctan2(t_[:, 1], t_[:, 0]); dl = np.linalg.norm(t_, axis=1)
    return np.degrees(np.abs(np.angle(np.exp(1j * np.diff(h_)))) / np.maximum((dl[1:] + dl[:-1]) / 2, 1e-6)).max()
print("STANDARD: spinare cotitura max %.2f grade/m; sine (capetele bratelor) cotitura max sus %.2f / jos %.2f grade/m; varfuri z %.1f..%.1f" % (
    turn(G["spinare"]), turn(G["sina_sus"]), turn(G["sina_jos"]), zm.min(), zm.max()))
LIP = os.environ.get("BV_LIPIT")                                       # the rails glued to the pieces beside (PS + rear arm): spine at
if LIP:                                                                 # height BV_Z, rails BV_GROS apart straight along (side view);
    import trimesh                                                      # each V's arms reach exactly the pieces' surface at the rails'
    ZS = float(os.environ.get("BV_Z", "295")); GR = float(os.environ.get("BV_GROS", "21"))   # heights (the V opens as needed)
    ms = [trimesh.Trimesh(np.load(p)[k.split(",")[0]], np.load(p)[k.split(",")[1]], process=False) for p, k in (q.split(":") for q in LIP.split(";"))]
    def cut(z):
        segs = [trimesh.intersections.mesh_plane(m_, [0, 0, 1], [0, 0, z]) for m_ in ms]; return np.vstack([q for q in segs if len(q)])[:, :, :2]
    def reach(P0, dv, S_):
        a_, b_ = S_[:, 0], S_[:, 1]; e_ = b_ - a_; w_ = a_ - P0
        den = dv[0] * e_[:, 1] - dv[1] * e_[:, 0]; ok_ = np.abs(den) > 1e-9
        t_ = np.where(ok_, (w_[:, 0] * e_[:, 1] - w_[:, 1] * e_[:, 0]) / np.where(ok_, den, 1), np.inf); u_ = np.where(ok_, (w_[:, 0] * dv[1] - w_[:, 1] * dv[0]) / np.where(ok_, den, 1), -1)
        t_ = np.where((u_ >= 0) & (u_ <= 1) & (t_ > 0), t_, np.inf); return t_.min()
    SU, SJ = cut(ZS + GR / 2), cut(ZS - GR / 2)
    hu = np.array([reach(sp[i], nin[i], SU) for i in range(len(sp))]); hj = np.array([reach(sp[i], nin[i], SJ) for i in range(len(sp))])
    cap = float(os.environ.get("BV_MAX", "60")); hu, hj = [gaussian_filter1d(np.clip(np.where(np.isfinite(h_), h_, cap), 6, cap), 15, mode="nearest") for h_ in (hu, hj)]
    Ru, Rj = sp + hu[:, None] * nin, sp + hj[:, None] * nin
    if os.environ.get("BV_SINE_DREPTE"):                               # the rails straight too (a bent bar each, through their glued
        def bara(P0, Vc, P1, R_):                                       # front end, their point at the spine's corner and their rear
            u1 = (P0 - Vc) / np.linalg.norm(P0 - Vc); u2 = (P1 - Vc) / np.linalg.norm(P1 - Vc); ph = np.arccos(np.clip(u1 @ u2, -1, 1)) / 2   # end;
            tl_ = R_ / np.tan(ph); A1, A2 = Vc + u1 * tl_, Vc + u2 * tl_; Cc_ = Vc + (u1 + u2) / np.linalg.norm(u1 + u2) * R_ / np.sin(ph)   # it may
            b1, b2 = np.arctan2(*(A1 - Cc_)[::-1]), np.arctan2(*(A2 - Cc_)[::-1]); db = np.angle(np.exp(1j * (b2 - b1))); nn = max(int(abs(db) * R_), 8)   # cut a
            arc_ = Cc_ + R_ * np.stack([np.cos(b1 + np.linspace(0, db, nn)), np.sin(b1 + np.linspace(0, db, nn))], 1)   # little into the pieces)
            L_ = lambda p, q: p + np.outer(np.arange(max(int(np.linalg.norm(q - p)), 2)) / max(int(np.linalg.norm(q - p)), 2), q - p)
            Pl = np.vstack([L_(P0, A1), arc_, L_(A2, P1), [P1]]); dd_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pl, axis=0), axis=1))]
            uu = np.linspace(0, dd_[-1], len(sp)); return np.stack([np.interp(uu, dd_, Pl[:, i]) for i in (0, 1)], 1)
        ic = int(np.argmax(sp[:, 0])); Ru = bara(Ru[0], Ru[ic], Ru[-1], RB); Rj = bara(Rj[0], Rj[ic], Rj[-1], RB)
    SDZ = float(os.environ.get("BV_SUS_DZ", "0"))                       # the upper rail raised
    SDX = float(os.environ.get("BV_SINE_DX", "0")); Ru, Rj = Ru + [SDX, 0], Rj + [SDX, 0]   # the rails moved in x (left = -x)
    if os.environ.get("BV_JOS_SUB_SUS"): Rj = Ru.copy()                # the lower rail right under the upper one (parallel, one plane)
    RJ_ = float(os.environ.get("BV_JOS_ROT", "0"))                     # the lower rail turned in plan about its middle (degrees,
    if RJ_:                                                             # negative = clockwise seen from above)
        cm = Rj[len(Rj) // 2].copy(); a_ = np.radians(RJ_); Rm = np.array([[np.cos(a_), -np.sin(a_)], [np.sin(a_), np.cos(a_)]]); Rj = (Rj - cm) @ Rm.T + cm
    Ru = Ru + [float(os.environ.get("BV_SUS_DX", "0")), 0]               # the upper rail moved in x (inwards = -x)
    Rj = Rj + [float(os.environ.get("BV_JOS_DX", "0")), 0]               # the lower rail moved in x (left = -x)
    G = {"spinare": np.c_[sp, np.full(len(sp), ZS)]}; k = 0
    for i in np.arange(0, len(sp), int(STEP)):
        tip = np.r_[sp[i], ZS]; up = np.r_[Ru[i], ZS + GR / 2 + SDZ]; dn = np.r_[Rj[i], ZS - GR / 2]
        TH_ = float(os.environ.get("BV_TRAPEZ", "0"))                  # a small trapezoid: the V's tip cut to a vertical side TH_ m high,
        if TH_:                                                         # its middle on the spine (a flat outer face instead of an edge)
            G["v_%02d" % k] = np.stack([up, tip + [0, 0, TH_ / 2], tip - [0, 0, TH_ / 2], dn]); k += 1; continue
        LW = float(os.environ.get("BV_LINGURA", "0"))                  # a lying spoon: each arm leaves the rail along the piece's
        if LW:                                                          # surface there (its section in the V's plane), then bends to the
            tg_ = np.r_[tg[i], 0.0]                                     # tip a little harder - a cubic close to the straight arm
            S3 = np.vstack([q for q in (trimesh.intersections.mesh_plane(m_, tg_, tip) for m_ in ms) if len(q)])
            def arm(P0, P3):
                mid_ = S3.mean(1); j_ = np.argmin(np.linalg.norm(mid_ - P0, axis=1)); tt = S3[j_, 1] - S3[j_, 0]; tt /= np.linalg.norm(tt)
                ch = P3 - P0; L_ = np.linalg.norm(ch); dch = ch / L_; tt = tt if tt @ dch > 0 else -tt
                t0_ = LW * tt + (1 - LW) * dch; t0_ /= np.linalg.norm(t0_)
                P1 = P0 + t0_ * L_ / 3; P2 = P0 + dch * 2 * L_ / 3 + (P0 + t0_ * 2 * L_ / 3 - (P0 + dch * 2 * L_ / 3)) * 0.35
                u_ = np.linspace(0, 1, 17)[:, None]; return (1 - u_) ** 3 * P0 + 3 * (1 - u_) ** 2 * u_ * P1 + 3 * (1 - u_) * u_ ** 2 * P2 + u_ ** 3 * P3
            G["v_%02d" % k] = np.vstack([arm(up, tip), arm(dn, tip)[::-1][1:]]); k += 1; continue
        G["v_%02d" % k] = np.stack([up, tip, dn]); k += 1
    if os.environ.get("BV_SPINARE_LUNGA"):                             # the spine's ends carried on straight along their direction until
        SM = cut(ZS)                                                    # they touch the pieces beside (front: PS, back: the arm)
        t0 = sp[0] - sp[3]; t0 /= np.linalg.norm(t0); t1 = sp[-1] - sp[-4]; t1 /= np.linalg.norm(t1)
        e0_, e1_ = reach(sp[0], t0, SM), reach(sp[-1], t1, SM); e0_ = e0_ if np.isfinite(e0_) and e0_ < 80 else 0; e1_ = e1_ if np.isfinite(e1_) and e1_ < 80 else 0
        ext0 = sp[0] + np.outer(np.arange(int(e0_), 0, -1), t0); ext1 = sp[-1] + np.outer(np.arange(1, int(e1_) + 1), t1)
        G["spinare"] = np.c_[np.vstack([ext0, sp, ext1]), np.full(len(ext0) + len(sp) + len(ext1), ZS)]
        print("SPINARE lungita: fata +%.0f m (pana la PS), spate +%.0f m (pana la brat)" % (e0_, e1_))
    G["sina_sus"] = np.c_[Ru, np.full(len(sp), ZS + GR / 2 + SDZ)]; G["sina_jos"] = np.c_[Rj, np.full(len(sp), ZS - GR / 2)]
    print("LIPIT: spinare la z %.1f, sine la z %.1f / %.1f (drepte in vedere laterala); bratele V pana la piese: sus %.0f..%.0f m, jos %.0f..%.0f m; deschiderea V %.0f..%.0f grade" % (
        ZS, ZS + GR / 2, ZS - GR / 2, hu.min(), hu.max(), hj.min(), hj.max(), np.degrees(np.arctan2(GR / 2, np.maximum(hu, hj).max())) * 2, np.degrees(np.arctan2(GR / 2, np.minimum(hu, hj).min())) * 2))
    print("STANDARD lipit: sine cotitura max sus %.2f / jos %.2f grade/m" % (turn(G["sina_sus"]), turn(G["sina_jos"])))
np.savez(OUT, **G)
fig, ax = plt.subplots(1, 2, figsize=(22, 14))
ax[0].plot(ol[:, 0], ol[:, 1], "-", color="0.8"); ax[0].plot(sp[:, 0], sp[:, 1], "g-", lw=2.5, label="spinarea (latura dreapta, V foarte deschis)")
for kk in G:
    if kk.startswith("v_"): q = G[kk]; ax[0].plot(q[:, 0], q[:, 1], "r-", lw=1.2)
ax[0].set_aspect("equal"); ax[0].grid(alpha=.3); ax[0].legend(); ax[0].set_title("de sus: spinarea si V-urile (bratele spre interior)")
for kk in list(G)[1::4]:
    if kk.startswith("v_"):
        q = G[kk]; tp = q[len(q) // 2]; ax[1].plot(-np.linalg.norm(q[:, :2] - tp[:2], axis=1), q[:, 2], "-", lw=1.2, label=kk)
ax[1].set_aspect("equal"); ax[1].grid(alpha=.3); ax[1].legend(fontsize=8); ax[1].set_title("sectiuni in V (varful pe spinare, spre interior la stanga)")
fig.tight_layout(); fig.savefig(SHEET, dpi=60)
print("BUMERANG V: spinare %.0f m (din fata y %.0f la spate y %.0f, cotul la x %.0f y %.0f), %d V-uri din %.0f in %.0f m, deschidere +-%.1f grade, brate %.0f..%.0f m" % (
    u[-1], sp[0, 1], sp[-1, 1], sp[np.argmax(sp[:, 0]), 0], sp[np.argmax(sp[:, 0]), 1], k, STEP, STEP, HALF,
    min(np.linalg.norm(G[q][0] - G[q][1]) for q in G if q.startswith("v_")), max(np.linalg.norm(G[q][0] - G[q][1]) for q in G if q.startswith("v_"))))
