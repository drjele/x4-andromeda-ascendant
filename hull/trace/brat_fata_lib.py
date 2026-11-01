# Helpers shared by the front-arm guide scripts (clean lines: 2D bent bars, ellipse fit, circles, arcs), taken from ghid_brat_fata.py.
import os, numpy as np
from scipy.optimize import least_squares
e = lambda k, d: os.environ.get(k, d)
ang = lambda P_, c_: np.arctan2(P_[1] - c_[1], P_[0] - c_[0])

def chain2(P0, a0, pieces, ds=1.0):                                         # 2D bent bar: (signed curvature, length) pieces, tangent
    P = np.array(P0, float); a = a0; pts = [P.copy()]
    for kap, L in pieces:
        n_ = max(int(np.ceil(L / ds)), 1); h = L / n_
        for _ in range(n_):
            if abs(kap) < 1e-9: P = P + h * np.array([np.cos(a), np.sin(a)])
            else: P = P + (np.array([np.sin(a + kap * h) - np.sin(a), np.cos(a) - np.cos(a + kap * h)])) / kap; a += kap * h
            pts.append(P.copy())
    return np.array(pts)
def fit2(R2, cuts, first_straight=True, last_straight=False, kmax=0.03, a0fix=None, ksign=0):                                   # straight runs + tangent arcs through the 2D line R2
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
    if ksign > 0: lo[1:n_ + 1] = np.maximum(lo[1:n_ + 1], -1e-7); x0[1:n_ + 1] = np.maximum(x0[1:n_ + 1], 0)   # the bend one way only
    if ksign < 0: hi[1:n_ + 1] = np.minimum(hi[1:n_ + 1], 1e-7); x0[1:n_ + 1] = np.minimum(x0[1:n_ + 1], 0)
    if first_straight: lo[1], hi[1] = -1e-7, 1e-7
    if a0fix is not None: lo[0], hi[0] = a0fix - 1e-7, a0fix + 1e-7         # the start direction given (tangent to a line before)
    if last_straight: lo[n_], hi[n_] = -1e-7, 1e-7; x0[n_] = 0.0
    x = least_squares(res, np.clip(x0, lo + 1e-9, hi - 1e-9), bounds=(lo, hi), x_scale=np.r_[1, np.full(n_, 1e-3), L0]).x
    Q = chain2(R2[0], x[0], list(zip(x[1:n_ + 1], x[n_ + 1:])), 0.5); dv = np.min(np.linalg.norm(R2[:, None] - Q[None], axis=2), axis=1)
    return Q, list(zip(x[1:n_ + 1], x[n_ + 1:])), dv
def ellipse_fit(Q):                                                        # Fitzgibbon direct ellipse fit -> centre, radii, angle
    x_, y_ = Q[:, 0], Q[:, 1]; D = np.c_[x_ * x_, x_ * y_, y_ * y_, x_, y_, np.ones(len(x_))]; Sm = D.T @ D
    Cm = np.zeros((6, 6)); Cm[0, 2] = Cm[2, 0] = 2; Cm[1, 1] = -1
    w_, v_ = np.linalg.eig(np.linalg.solve(Sm + 1e-9 * np.eye(6), Cm)); a = np.real(v_[:, np.argmax(np.real(w_))])
    A, B, C_, Dd, Ee, F = a; M = np.array([[A, B / 2], [B / 2, C_]]); c = np.linalg.solve(2 * M, [-Dd, -Ee])
    k = c @ M @ c - F; w2, v2 = np.linalg.eigh(M); r = np.sqrt(np.abs(k / w2)); return c, r, np.arctan2(v2[1, 0], v2[0, 0])
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
def by_len(P_, n=600):
    d_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P_, axis=0), axis=1))]; return np.c_[[np.interp(np.linspace(0, d_[-1], n), d_, P_[:, k]) for k in range(P_.shape[1])]].T
def circ3(p1, p2, p3):                                                      # the circle through three points
    A = 2 * np.array([p2 - p1, p3 - p1]); c_ = np.linalg.solve(A, [p2 @ p2 - p1 @ p1, p3 @ p3 - p1 @ p1]); return c_, np.linalg.norm(p1 - c_)
def arc2(c_, r_, p0, p1, n=80, longway=False):
    a0, a1 = ang(p0, c_), ang(p1, c_); da = (a1 - a0 + np.pi) % (2 * np.pi) - np.pi
    if longway: da -= np.sign(da) * 2 * np.pi
    return c_ + r_ * np.c_[np.cos(a0 + np.linspace(0, 1, n) * da), np.sin(a0 + np.linspace(0, 1, n) * da)]
