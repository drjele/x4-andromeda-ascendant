# Guides for the back arms that join the PS (asked: guides for the arms joined to the PS too). From the right arm (ship
# coordinates): its centre line (walked along the tube - each step the section across the current direction, its centre
# the next point; follows the hairpin - smoothed SMC m, resampled), then every PAS m a section
# perpendicular to the centre line, replaced by a clean ellipse (centre, axes and radii from the section's own spread) in
# that plane; the spine = the centre line. The left arm = the mirror. Offsets (OFF_D / OFF_S = "dx,dy,dz") baked in for
# drawing on the exploded arms. SP_CURAT=1: the spine = straight + tangent arc + straight in one plane (clean lines),
# the ellipses centred on it. R_CONST=1: the rings constant (circles of the tube's radius), no flare. Usage: python ghid_brat.py <arm npz v,f (ship coords, right)> <out.npz> ; env PAS=50 SMC=30
import sys, os, numpy as np, trimesh
from scipy.ndimage import gaussian_filter1d
D = np.load(sys.argv[1]); OUT = sys.argv[2]; PAS, SMC = float(os.environ.get("PAS", "50")), float(os.environ.get("SMC", "30"))
off = lambda k: np.array([float(q) for q in os.environ.get(k, "0,0,0").split(",")])
t = trimesh.Trimesh(D["v"], D["f"], process=False); ylo, yhi = t.bounds[0, 1], t.bounds[1, 1]
cen = []                                               # walked along the tube from the PS end: each step the section across the
s0_ = t.section(plane_origin=[0, yhi - 3, 0], plane_normal=[0, 1, 0]); L0 = max(s0_.discrete, key=len)   # current direction,
p = L0.mean(0); tg = np.array([0.0, -1.0, 0.0]); cen.append(p); ST = float(os.environ.get("PAS_MERS", "8"))  # its centre next
for _ in range(2000):
    q = p + ST * tg; s = t.section(plane_origin=q, plane_normal=tg)
    if s is None: break
    Ls = [L for L in s.discrete if np.linalg.norm(L.mean(0) - q) < 60]
    if not Ls: break
    L = min(Ls, key=lambda L: np.linalg.norm(L.mean(0) - q)); n_ = L.mean(0)
    if np.linalg.norm(n_ - p) < 1: break
    tg_new = (n_ - p) / np.linalg.norm(n_ - p); tg = 0.6 * tg + 0.4 * tg_new; tg /= np.linalg.norm(tg); p = n_; cen.append(p)
cen = np.array(cen); cen = np.c_[[gaussian_filter1d(cen[:, k], SMC / ST, mode="nearest") for k in range(3)]].T
d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cen, axis=0), axis=1))]; u = np.arange(0, d[-1], 1.0)
C = np.c_[[np.interp(u, d, cen[:, k]) for k in range(3)]].T
if os.environ.get("SP_CURAT") == "1":                 # clean spine: a straight run from the PS end, a tangent arc, a straight run -
    Cm = C.copy(); P0 = Cm[0]; n_ = len(Cm)           # all in one plane (through the PS end, spanned by the two runs' directions)
    up = Cm[(np.arange(n_) > 150) & (Cm[:, 2] > Cm[:, 2].max() - 25)]; dA = up[-1] - up[0]; dA -= 0 * dA
    w_, v_ = np.linalg.eigh(np.cov((up - up.mean(0)).T)); dA = v_[:, -1] * np.sign(v_[:, -1] @ (up[-1] - up[0]))
    lo_i = np.arange(n_) > np.argmin(Cm[:, 1]) + 150; lo = Cm[lo_i]; w_, v_ = np.linalg.eigh(np.cov((lo - lo.mean(0)).T)); dB = v_[:, -1] * np.sign(v_[:, -1] @ (lo[-1] - lo[0]))
    ref = np.cross(dA, [0, 0, 1.0]); ref /= np.linalg.norm(ref); ref2 = np.cross(dA, ref)
    best = None
    for phi in np.radians(np.arange(0, 180, 3)):      # the plane turned round the upper run; the lower run fitted in it
        nP = np.cos(phi) * ref + np.sin(phi) * ref2; e1 = dA; e2 = np.cross(nP, e1)
        to2 = lambda X: np.c_[(X - P0) @ e1, (X - P0) @ e2]; to3 = lambda Q: P0 + np.outer(Q[:, 0], e1) + np.outer(Q[:, 1], e2)
        L2 = to2(lo); b2 = L2.mean(0); w2, v2 = np.linalg.eigh(np.cov((L2 - b2).T)); db2 = v2[:, -1] * np.sign(v2[:, -1] @ (L2[-1] - L2[0]))
        M2 = np.c_[np.array([1.0, 0.0]), -db2]
        if abs(np.linalg.det(M2)) < 1e-6: continue
        ta, tb = np.linalg.solve(M2, b2); K = np.array([ta, 0.0]); endB = b2 + db2 * ((L2[-1] - b2) @ db2)
        d0 = np.array([1.0, 0.0]); d1 = db2; th = np.arccos(np.clip(-d0 @ d1, -1, 1))
        for RBc in np.arange(40, 400, 10):
            Lc = RBc / np.tan(th / 2); t0 = K - d0 * Lc; t1 = K + d1 * Lc
            if t0[0] < 50 or (endB - t1) @ d1 < 50: continue
            bis = d1 - d0; bis /= np.linalg.norm(bis); cc = K + bis * RBc / np.sin(th / 2)
            a0 = np.arctan2(t0[1] - cc[1], t0[0] - cc[0]); a1 = np.arctan2(t1[1] - cc[1], t1[0] - cc[0]); da = a1 - a0
            if abs(da) > np.pi: da -= np.sign(da) * 2 * np.pi
            arc2 = cc + RBc * np.c_[np.cos(a0 + np.linspace(0, 1, 120) * da), np.sin(a0 + np.linspace(0, 1, 120) * da)]
            Q = np.vstack([np.linspace([0, 0], t0, 300)[:-1], arc2, np.linspace(t1, endB, 300)[1:]]); X3 = to3(Q)
            dev = np.mean([np.min(np.linalg.norm(X3 - c_, axis=1)) for c_ in Cm[::20]])
            if best is None or dev < best[0]: best = (dev, RBc, X3, nP, np.linalg.norm(t0), np.linalg.norm(endB - t1))
    devm, RB, X3 = best[:3]; dmax = max(np.min(np.linalg.norm(X3 - c_, axis=1)) for c_ in Cm[::5])
    dd = np.r_[0, np.cumsum(np.linalg.norm(np.diff(X3, axis=0), axis=1))]; uu = np.arange(0, dd[-1], 1.0); C = np.c_[[np.interp(uu, dd, X3[:, k]) for k in range(3)]].T; u = uu
    print("SPINARE CURATA: drept %.0f m din PS, arc R %.0f m, drept %.0f m, intr-un plan (normala %.2f, %.2f, %.2f); fata de bratul real medie %.1f m, max %.1f m" % (
        best[4], RB, best[5], *best[3], devm, dmax))
out = {"spinare_brat_D": C}; k_ = 0; rep = []
for s0 in np.arange(PAS / 2, u[-1] - 5, PAS):
    i = int(s0); p = C[i]; tg = C[min(i + 3, len(C) - 1)] - C[max(i - 3, 0)]; tg /= np.linalg.norm(tg)
    s = t.section(plane_origin=p, plane_normal=tg)
    if s is None: continue
    L = min(s.discrete, key=lambda q: np.linalg.norm(q.mean(0) - p))
    e1 = np.cross(tg, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(tg, e1)
    Q = np.c_[(L - p) @ e1, (L - p) @ e2]; c = Q.mean(0); w, v = np.linalg.eigh(np.cov((Q - c).T)); r = np.sqrt(2 * w)
    if os.environ.get("SP_CURAT") == "1": c = np.zeros(2)                 # clean: the ellipse centred on the spine
    th = np.linspace(0, 2 * np.pi, 121); E = c + np.c_[r[0] * np.cos(th), r[1] * np.sin(th)] @ v.T
    out["sectiune_brat_D_%02d" % k_] = p + np.outer(E[:, 0], e1) + np.outer(E[:, 1], e2)
    rep.append("%02d la %4.0f m: centru (%.0f, %.0f, %.0f), raze %.1f x %.1f m" % (k_, s0, *(p + c[0] * e1 + c[1] * e2), r.max(), r.min())); k_ += 1
if os.environ.get("R_CONST") == "1":                  # rings constant all along (no flare towards the PS): circles of the tube's
    rr = [float(q.split("raze ")[1].split(" x")[0]) * 0.5 + float(q.split(" x ")[1].split(" m")[0]) * 0.5 for q in rep]   # radius
    s_at = [float(q.split(" la ")[1].split(" m")[0]) for q in rep]; RC_ = float(np.median([r_ for r_, s1 in zip(rr, s_at) if s1 > 300]))
    for kk in [q for q in out if q.startswith("sectiune_brat_D")]:
        q = out[kk]; p = q.mean(0); i = int(np.argmin(np.linalg.norm(C - p, axis=1))); p = C[i]
        tg = C[min(i + 3, len(C) - 1)] - C[max(i - 3, 0)]; tg /= np.linalg.norm(tg); e1 = np.cross(tg, [0, 0, 1.0])
        if np.linalg.norm(e1) < 1e-6: e1 = np.cross(tg, [1.0, 0, 0])
        e1 /= np.linalg.norm(e1); e2 = np.cross(tg, e1); th = np.linspace(0, 2 * np.pi, 121)
        out[kk] = p + np.outer(RC_ * np.cos(th), e1) + np.outer(RC_ * np.sin(th), e2)
    print("INELE CONSTANTE: cercuri de raza %.1f m pe toata lungimea (fara largire spre PS)" % RC_)
for kk in list(out): out[kk.replace("_D", "_S")] = out[kk] * [-1, 1, 1]
for kk in out: out[kk] = out[kk] + (off("OFF_D") if "_D" in kk else off("OFF_S"))
print("BRAT GHIDAJE: spinarea %.0f m (y %.0f..%.0f, z %.0f..%.0f), %d sectiuni elipse la %.0f m, perpendiculare pe spinare; stangul = oglinda" % (
    u[-1], C[:, 1].max(), C[:, 1].min(), C[:, 2].min(), C[:, 2].max(), k_, PAS))
for r_ in rep[:3] + ["..."] + rep[-3:]: print("   " + r_)
np.savez(OUT, **out)
