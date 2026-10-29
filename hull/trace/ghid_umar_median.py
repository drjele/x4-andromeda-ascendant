# The confirmed shoulder-free outline as ONE symmetric guide in the PS's median plane, with perpendicular guides (asked: the
# D and S lines one guide, symmetric, in the PS's middle plane; perpendiculars for the surface; how it compares with the
# reference's). The right line (confirmed, contur_umar_PS_D) is joined to its mirror through the tip; z = the PS's middle
# height. Perpendiculars: the PS's real outline at that height (horizontal section), every STEP m, along its normal in the
# plane out to the guide (both sides) - how far the side has to move there. Comparison with contur_umar_R002_D, per y.
# Usage: python ghid_umar_median.py <ghid_umar.npz> <pieces.npz> <out.npz> ; env GM_STEP=10
import sys, os, numpy as np, trimesh
U = np.load(sys.argv[1]); D = np.load(sys.argv[2]); OUT = sys.argv[3]; MX = -1700.0; STEP = float(os.environ.get("GM_STEP", "10"))
ps = trimesh.Trimesh(D["PS__v"] - [MX, 0, 0], D["PS__f"], process=False); ZM = (ps.vertices[:, 2].min() + ps.vertices[:, 2].max()) / 2
Pd = U["contur_umar_PS_D"][:, :2]; Pd = Pd[np.argsort(-Pd[:, 1])]                     # tip first
if Pd[0, 0] > 0.5: Pd = np.vstack([[0.0, Pd[0, 1] + 0.0], Pd])
YEND = os.environ.get("GM_YEND")                       # the straight sides carried on to the PS's end (same slope)
if YEND:
    YEND = float(YEND) if YEND != "ps" else ps.vertices[:, 1].min() + 1; a_, b_ = Pd[-12], Pd[-1]; k_ = (b_[0] - a_[0]) / (b_[1] - a_[1])
    ye = np.arange(Pd[-1, 1] - 1, YEND - 0.1, -1.0); Pd = np.vstack([Pd, np.c_[Pd[-1, 0] + k_ * (ye - Pd[-1, 1]), ye]])
    print("LATURI PRELUNGITE pana la y %.0f (x %.1f)" % (Pd[-1, 1], Pd[-1, 0]))
G = np.vstack([(Pd * [-1, 1])[::-1], Pd[1:]])                                          # left end -> tip -> right end
out = {"contur_umar_median": np.c_[G, np.full(len(G), ZM)]}
xg = lambda y: np.interp(-y, -Pd[:, 1], Pd[:, 0])
s = ps.section(plane_origin=[0, 0, ZM], plane_normal=[0, 0, 1]); n_ = 0; mv = []
for e in s.discrete:
    e = e[:, :2]; d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(e, axis=0), axis=1))]
    for t in np.arange(0, d[-1], STEP):
        p = np.array([np.interp(t, d, e[:, 0]), np.interp(t, d, e[:, 1])]); j = np.searchsorted(d, t)
        if p[1] > Pd[:, 1].max() - 2 or p[1] < Pd[:, 1].min() + 2 or abs(p[0]) < 20: continue
        tg = e[min(j + 1, len(e) - 1)] - e[max(j - 1, 0)]; tg /= np.linalg.norm(tg) + 1e-12; nv = np.array([tg[1], -tg[0]])
        if nv[0] * np.sign(p[0]) < 0: nv = -nv                                         # outwards
        side = np.sign(p[0]); f = lambda u: abs(p[0] + u * nv[0]) - xg(p[1] + u * nv[1])
        lo, hi = -40.0, 80.0
        if f(lo) * f(hi) > 0: continue
        for _ in range(50):
            m = (lo + hi) / 2
            if f(lo) * f(m) <= 0: hi = m
            else: lo = m
        u = (lo + hi) / 2; mv.append((u, p[1]))
        if abs(u) > 0.5: out["perp_umar_%03d" % n_] = np.array([[p[0], p[1], ZM], [p[0] + u * nv[0], p[1] + u * nv[1], ZM]]); n_ += 1
mv = np.array(mv)
print("GHIDAJ MEDIAN: o linie simetrica, %d puncte, in planul z %.1f (mijlocul PS: %.0f..%.0f); %d perpendiculare la %.0f m; latura iese pana la %.1f m (y %.0f), intra pana la %.1f m" % (
    len(G), ZM, ps.vertices[:, 2].min(), ps.vertices[:, 2].max(), n_, STEP, mv[:, 0].max(), mv[np.argmax(mv[:, 0]), 1], max(-mv[:, 0].min(), 0)))
if "contur_umar_R002_D" in U.files:
    Rr = U["contur_umar_R002_D"][:, :2]; Rr = Rr[np.argsort(-Rr[:, 1])]; ys = np.arange(min(Pd[:, 1].max(), Rr[:, 1].max()) - 1, max(Pd[:, 1].min(), Rr[:, 1].min()) + 1, -1.0)
    dx = xg(ys) - np.interp(-ys, -Rr[:, 1], Rr[:, 0]); i = np.argmax(np.abs(dx))
    print("FATA DE REFERINTA (ghidajul R002 169_C): abatere x medie %.1f m, max %.1f m la y %.0f (+ = al nostru mai lat); pe zone:" % (np.abs(dx).mean(), dx[i], ys[i]))
    for a, b in ((470, 300), (300, 240), (240, 100), (100, 0), (0, -45)):
        m = (ys <= a) & (ys > b)
        if m.any(): print("   y %4d..%4d: medie %+.1f m, max |%.1f| m" % (a, b, dx[m].mean(), np.abs(dx[m]).max()))
np.savez(OUT, **out)
