# Clean line = straight lines + tangent arcs only. A planar curve as a chain of (length, curvature) segments: heading is continuous and piecewise linear in arc length,
# so the chain is tangent-continuous by construction. Knots from Douglas-Peucker on heading(s), refined by least squares, curvature under KLIN snapped to a true straight line;
# the coarsest chain within TOL m wins. Import: fit(P, tol, rmin, x0=None, th0=None) -> dict(seg=[(L, k)], x0, th0, dev, devmax); draw(res, step)
import numpy as np
from scipy.optimize import least_squares
from scipy.ndimage import gaussian_filter1d as gf
from scipy.spatial import cKDTree as KD
KLIN = 1 / 4000.0
def resample(P, h):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; k = np.r_[True, np.diff(s) > 1e-9]; P, s = P[k], s[k]
    u = np.linspace(0, s[-1], max(int(s[-1] / h) + 1, 4)); return np.stack([np.interp(u, s, P[:, a]) for a in range(P.shape[1])], 1), u
def chain(x0, th0, L, K, u):
    """Points at arc lengths u along the chain, exact on each arc."""
    e = np.r_[0, np.cumsum(L)]; th = th0 + np.r_[0, np.cumsum(L * K)]; p = np.zeros((len(L) + 1, 2)); p[0] = x0
    def adv(p0, t0, k, d):
        small = np.abs(k) < 1e-9; t1 = t0 + k * d; kk = np.where(small, 1.0, k)
        dx = np.where(small, d * np.cos(t0), (np.sin(t1) - np.sin(t0)) / kk); dy = np.where(small, d * np.sin(t0), (np.cos(t0) - np.cos(t1)) / kk); return p0 + np.stack([dx, dy], -1)
    for i in range(len(L)): p[i + 1] = adv(p[i], th[i], K[i], L[i])
    j = np.clip(np.searchsorted(e, u, side="right") - 1, 0, len(L) - 1); return adv(p[j], th[j], K[j], u - e[j])
def rdp(s, y, eps):
    keep = [0, len(s) - 1]; st = [(0, len(s) - 1)]
    while st:
        a, b = st.pop()
        if b <= a + 1: continue
        t = (s[a + 1:b] - s[a]) / (s[b] - s[a]); d = np.abs(y[a + 1:b] - (y[a] + t * (y[b] - y[a]))); i = int(np.argmax(d))
        if d[i] > eps: m = a + 1 + i; keep.append(m); st += [(a, m), (m, b)]
    return np.array(sorted(keep))
def fit(P, tol=1.5, rmin=10.0, x0=None, th0=None, h=2.0, lmin=12.0, nmax=16):
    """Fewest segments within tol: start from one arc, add a knot where the chain is furthest from the line, refit everything."""
    Q, u = resample(np.asarray(P, float), h); Fine = resample(np.asarray(P, float), 0.25)[0]; tree = KD(Fine); kmax = 1.0 / rmin; n = len(Q); wt = np.ones(n); wt[[0, -1]] = 6.0
    d = np.gradient(gf(Q, 3.0, axis=0, mode="nearest"), axis=0); th = np.unwrap(np.arctan2(d[:, 1], d[:, 0])); fx, ft = x0 is not None, th0 is not None; head = (0 if fx else 2) + (0 if ft else 1)
    X0 = np.asarray(x0, float) if fx else Q[0]; T0 = th0 if ft else th[0]; knots = [0.0, u[-1]]; best = None
    def run(knots):
        kn = np.array(knots); m = len(kn) - 1; L0 = np.diff(kn); ii = np.searchsorted(u, kn).clip(0, n - 1); K0 = np.clip(np.diff(th[ii]) / L0, -kmax * .99, kmax * .99)
        def un(z):
            i = 0; a = X0 if fx else z[:2]; i = 0 if fx else 2; t = T0 if ft else z[i]; i += 0 if ft else 1; return a, t, z[i:i + m], z[i + m:]
        z0 = np.r_[[] if fx else X0, [] if ft else [T0], L0, K0]; lo = np.r_[[-np.inf] * head, [lmin * .6] * m, [-kmax] * m]; hi = np.r_[[np.inf] * head, [np.inf] * m, [kmax] * m]; z0 = np.clip(z0, lo + 1e-9, hi - 1e-9)
        xs = np.r_[[50.0] * (0 if fx else 2), [] if ft else [.1], [30.0] * m, [.002] * m]
        def res(z, f=1.0):
            a, t, L, K = un(z); return ((chain(a, t, L, K * f, u / u[-1] * L.sum()) - Q) * wt[:, None]).ravel()
        r = least_squares(res, z0, bounds=(lo, hi), max_nfev=40, x_scale=xs); a, t, L, K = un(r.x); f = (np.abs(K) >= KLIN).astype(float)
        if not f.all(): r = least_squares(lambda z: res(z, f), r.x, bounds=(lo, hi), max_nfev=25, x_scale=xs); a, t, L, K = un(r.x); K = K * f
        S = chain(a, t, L, K, np.arange(0, L.sum() + .25, .5)); d1 = tree.query(S)[0]; d2 = KD(S).query(Fine)[0]; d1[-40:] = 0; d2[-80:] = 0
        return dict(seg=list(zip(L.tolist(), K.tolist())), x0=np.asarray(a, float), th0=float(t), dev=float(d1.mean()), devmax=float(max(d1.max(), d2.max())), tot=float(L.sum())), S, d1, d2
    while True:
        R, S, d1, d2 = run(knots); w_ = S[int(np.argmax(d1))] if d1.max() > d2.max() else Fine[int(np.argmax(d2))]; print("   %d segmente: max %.2f m la (%.0f, %.0f)" % (len(knots) - 1, R["devmax"], w_[0], w_[1]))
        if best is None or R["devmax"] < best["devmax"]: best = R
        if R["devmax"] <= tol or len(knots) - 1 >= nmax: return best
        j = int(np.argmax(d2)); q = Fine[j]; a = u[int(np.argmin(np.linalg.norm(Q - q, axis=1)))]   # the worst place on the line itself, as arc length on the line
        L = np.array([s[0] for s in R["seg"]]); knots = [0.0] + (np.cumsum(L)[:-1] / L.sum() * u[-1]).tolist() + [u[-1]]; cand = np.array(knots)
        if np.abs(cand - a).min() < lmin: mids = (cand[:-1] + cand[1:]) / 2; mids = mids[np.diff(cand) >= 2 * lmin]; a = mids[np.argmin(np.abs(mids - a))] if len(mids) else None
        if a is None: return best
        knots = sorted(knots + [float(a)])
def draw(R, step=0.5):
    L = np.array([s[0] for s in R["seg"]]); K = np.array([s[1] for s in R["seg"]]); u = np.r_[np.arange(0, L.sum(), step), L.sum()]; return chain(R["x0"], R["th0"], L, K, u), u
