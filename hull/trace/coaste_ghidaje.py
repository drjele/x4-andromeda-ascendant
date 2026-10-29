# Guides for the PS grown into its ears as ONE shape (asked: the left ribs carried right across - each rib one curve of the
# same ellipse over the whole width, in one plane; the outer edge (spine) in one plane; guides perpendicular to the PS's
# surface first, to see how it has to change). Per station y (every PAS m, where the PS is): the ear's half-width a = the
# confirmed spine (103's outer edge); the rib = a top half-ellipse through the PS's deck on the axis and a bottom one through
# its belly on the axis, both a wide, centred at zc - they meet at the edges with a vertical tangent; zc on one plane
# z = c + k*y (the spine planar, the same both sides). Past the PS's end (along the arms) the sections take the arms too. Perpendicular guides: points along the PS's section (every STEP m of
# its outline), along the outline's normal in that plane, to the rib - how far the PS moves out (+) or in (-) there.
# CO_BRAT_Y=y1,y2: between them the rib slides from the PS's one ellipse (centred on the axis) to one per arm (centred on
# the arm, its height) - smoothstep; behind y2 each arm's own curve. CO_INTERIOR=m the rib's inner half hugs the arm (m off
# its inner face); CO_FARA=15_D,... ribs left out; CO_JOS_SCALA=f the PS ribs' belly half f times as deep
# (flatter, higher; fading out towards the arms). Usage: python coaste_ghidaje.py <103_D.npz> <pieces.npz> <out.npz> ; env CO_PAS=40 CO_STEP=10
import sys, os, numpy as np, trimesh
R = np.load(sys.argv[1])["v"].astype(float).reshape(-1, 4, 3); D = np.load(sys.argv[2]); OUT = sys.argv[3]
PAS, STEP = float(os.environ.get("CO_PAS", "40")), float(os.environ.get("CO_STEP", "10"))
PIESE = os.environ.get("CO_PIESE", "PS,brat_spate_D,brat_spate_S").split(",")   # sectioned together: past the PS's end the
ps = trimesh.util.concatenate([trimesh.Trimesh(D[n + "__v"] + [1700, 0, 0], D[n + "__f"], process=False) for n in PIESE])   # arms
edge = (R[:, 1] + R[:, 2]) / 2; o = np.argsort(edge[:, 1])
y_hi = min(edge[:, 1].max(), ps.vertices[:, 1].max()) - 15; y_lo = edge[:, 1].min() + 2   # the ears' whole length (along the arms too)
ys = np.r_[np.arange(y_hi, y_lo + PAS / 4, -PAS), y_lo]                    # + one rib right at the ears' end
def sec(y):
    s = ps.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0]); return [e[:, [0, 2]] for e in s.discrete] if s is not None else []
rows = []
for y in ys:
    P = np.vstack(sec(y)); ax_ = P if os.environ.get("CO_INFASURATOR", "1") == "1" else P[np.abs(P[:, 0]) < 2]   # highest /
    # lowest point of the whole section (on the axis alone the U between the arms made the rib cut 25 m into the PS)
    if not len(ax_): continue
    rows.append((y, np.interp(y, edge[o, 1], edge[o, 0]), ax_[:, 1].max(), ax_[:, 1].min()))
rows = np.array(rows); y_, a_, zt, zb = rows.T
BY = [float(x_) for x_ in os.environ.get("CO_BRAT_Y", "15,-65").split(",")]   # along the arms: each arm's own rib (its centre
br = trimesh.Trimesh(D["brat_spate_D__v"] + [1700, 0, 0], D["brat_spate_D__f"], process=False)   # and height), reached from the
def arm(y):                                            # PS's one-ellipse rib by a smooth slide between BY[0] and BY[1]
    s = br.section(plane_origin=[0, min(y, -47.0), 0], plane_normal=[0, 1, 0])
    if s is None: return None
    P = max([e[:, [0, 2]] for e in s.discrete], key=len); return P[:, 0].mean(), P[:, 1].max(), P[:, 1].min(), P[:, 0].min()
AR = np.array([arm(y) for y in y_]); w_ = np.clip((BY[0] - y_) / (BY[0] - BY[1]), 0, 1); w_ = w_ * w_ * (3 - 2 * w_)
cx_ = w_ * AR[:, 0]; zt = (1 - w_) * np.where(y_ > -45, zt, zt[np.argmin(np.abs(y_ + 25))]) + w_ * AR[:, 1]
zb = (1 - w_) * np.where(y_ > -45, zb, zb[np.argmin(np.abs(y_ + 25))]) + w_ * AR[:, 2]
k, c = np.polyfit(y_, (zt + zb) / 2, 1); zc = c + k * y_                     # the spine's plane z = c + k y (both sides)
print("COASTE: %d statii y %.0f..%.0f; spinarea in planul z = %.1f %+.4f*y (inclinare %.1f grd pe lungime)" % (len(y_), y_.max(), y_.min(), c, k, np.degrees(np.arctan(k))))
out = {}; th = np.linspace(0, np.pi, 181); worst = []
for i, (y, aw, t, b) in enumerate(zip(y_, a_, zt, zb)):
    bt, bb = t - zc[i], zc[i] - b; cx = cx_[i]; a = aw - cx            # the right rib: centre cx, reaching the edge aw
    bb *= 1 - (1 - float(os.environ.get("CO_JOS_SCALA", "1"))) * (1 - w_[i])   # PS ribs: the belly half flatter (higher)
    MI = float(os.environ.get("CO_INTERIOR", "3"))                     # inner side hugging the arm (MI m off its inner face)
    ai = (1 - w_[i]) * a + w_[i] * max(cx - AR[i, 3] + MI, 5.0)        # its own inner width, through the same smooth transition
    ax_c = np.where(np.cos(th) >= 0, a, ai)                            # outer half: a; inner half: ai (still one plane, G1)
    top = np.c_[cx + ax_c * np.cos(th), np.full(len(th), y), zc[i] + bt * np.sin(th)]
    bot = np.c_[cx + ax_c[::-1] * np.cos(th[::-1]), np.full(len(th), y), zc[i] - bb * np.sin(th[::-1])]
    R_ = np.vstack([top, bot[1:]])
    if cx < 0.5: out["coasta_%02d" % i] = R_                          # on the PS: one rib over the whole width
    else:                                                               # along the arms: one per arm
        SK = {x_ for x_ in os.environ.get("CO_FARA", "").split(",") if x_}   # ribs left out (asked: coasta_15_D was extra)
        if "%02d_D" % i not in SK: out["coasta_%02d_D" % i] = R_
        if "%02d_S" % i not in SK: out["coasta_%02d_S" % i] = R_ * [-1, 1, 1]
    ell = lambda xx, zz: ((xx - cx) / (a if xx >= cx else ai)) ** 2 + ((zz - zc[i]) / (bt if zz >= zc[i] else bb)) ** 2
    for e in sec(y):                                                # perpendiculars along the right half of the PS's outline
        if e[:, 0].max() < 5: continue
        xmin_ = 5 if e[:, 0].min() < 0 else e[:, 0].mean()  # PS (crosses the axis): its right half; an arm: only its outer half
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(e, axis=0), axis=1))]; n_ = len([q for q in out if q.startswith("perp_%02d_" % i)])
        for s_ in np.arange(0, d[-1], STEP):
            p = np.array([np.interp(s_, d, e[:, 0]), np.interp(s_, d, e[:, 1])])
            if p[0] < xmin_: continue
            j = np.searchsorted(d, s_); tg = e[min(j + 1, len(e) - 1)] - e[max(j - 1, 0)]; tg /= np.linalg.norm(tg) + 1e-12
            nv = np.array([tg[1], -tg[0]]); nv = nv if (nv @ (p - [0, zc[i]])) > 0 else -nv   # outwards
            lo, hi = -60.0, 120.0                            # where the normal line meets the rib (bisection on the ellipse)
            f_ = lambda u: ell(*(p + u * nv)) - 1
            if f_(lo) * f_(hi) > 0: continue
            for _ in range(50):
                mid = (lo + hi) / 2
                if f_(lo) * f_(mid) <= 0: hi = mid
                else: lo = mid
            u = (lo + hi) / 2; worst.append((u, y, p[0], p[1]))
            if abs(u) > 1: out["perp_%02d_%02d" % (i, n_)] = np.array([[p[0], y, p[1]], [p[0] + u * nv[0], y, p[1] + u * nv[1]]]); n_ += 1
    print("   y %5.0f: centru x %.0f (trecere %.0f%%), margine x %.0f, sus z %.0f, jos z %.0f, spinarea z %.0f" % (y, cx, 100 * w_[i], aw, t, b, zc[i]))
w = np.array(worst); print("PERPENDICULARE: PS iese in afara pana la %.1f m (max), intra spre interior pana la %.1f m" % (w[:, 0].max(), -w[:, 0].min()))
out["contur_margine_D"] = np.c_[a_, y_, zc]; out["contur_margine_S"] = np.c_[-a_, y_, zc]
PO = os.environ.get("CO_PARAM_OUT")                    # the ribs' parameters per station (to build the ears from the same ribs)
if PO:
    MI = float(os.environ.get("CO_INTERIOR", "3")); SC = float(os.environ.get("CO_JOS_SCALA", "1"))
    a2 = a_ - cx_; ai2 = (1 - w_) * a2 + w_ * np.maximum(cx_ - AR[:, 3] + MI, 5.0)
    bt2 = zt - zc; bb2 = (zc - zb) * (1 - (1 - SC) * (1 - w_))
    np.savez(PO, y=y_, cx=cx_, a=a2, ai=ai2, bt=bt2, bb=bb2, zc=zc, w=w_); print("PARAMETRI COASTE ->", PO)
np.savez(OUT, **out)
