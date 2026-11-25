# The external models brought onto the reference ship: affine ICP limited to what two copies of a symmetric ship can differ by
# (scale per axis, pitch about x, shift in y and z; nothing across), trimmed, on the hull object only. The target is the reference's
# S half mirrored (the symmetry base); a source is first made level by its own mirror (roll/yaw/shift that maps it to itself).
# Usage: python corelare_aliniaza.py <dir with npz>
import sys, json, numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import least_squares
D = sys.argv[1]; rng = np.random.default_rng(0)
def load(f): d = np.load(f"{D}/{f}.npz"); return d["v"], d["t"], d["o"], list(d["n"])
def sample(v, t, n):
    T = v[t]; c = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = np.linalg.norm(c, axis=1); i = rng.choice(len(t), n, p=a / a.sum())
    r, s = np.sqrt(rng.random(n)), rng.random(n); return T[i, 0] * (1 - r)[:, None] + T[i, 1] * (r * (1 - s))[:, None] + T[i, 2] * (r * s)[:, None]
def rotm(r): cx, sx = np.cos(r[0]), np.sin(r[0]); cy, sy = np.cos(r[1]), np.sin(r[1]); cz, sz = np.cos(r[2]), np.sin(r[2]); return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
def level(P):                                                               # roll, yaw, x shift making P its own mirror
    best = np.zeros(3)
    for _ in range(12):
        Q = P @ rotm([0, best[0], best[1]]).T; Q[:, 0] += best[2]; M = Q * [-1, 1, 1]; tr = cKDTree(Q); d, j = tr.query(M); k = d < np.percentile(d, 80)
        A = np.stack([Q[:, 2], -Q[:, 1], np.ones(len(Q))], 1); r = (M[k] - Q[j][k])[:, 0] / -1
        x = np.linalg.lstsq(np.vstack([A[k] + A[j][k]]), -((Q[:, 0][k]) + Q[j][:, 0][k]), rcond=None)[0]; best += 0.7 * x
    return best, float(np.median(cKDTree(Q).query(Q * [-1, 1, 1])[0]))
v, t, o, n = load("REFERINTA"); h = t[o == n.index("R001 084_D")]; P = sample(v, h, 400000); S = P[P[:, 0] < 0]; REF = np.vstack([S, S * [-1, 1, 1]]); TR = cKDTree(REF)
res = {}
for f, hull in (("moreno_v17", "Cube"), ("NAVA_REPO_XMF", None)):
    v, t, o, n = load(f); hh = t if hull is None else t[o == n.index(hull)]; P = sample(v, hh, 60000)
    lv, sym = level(P.copy()); L = rotm([0, lv[0], lv[1]]); v1 = v @ L.T + [lv[2], 0, 0]; P = P @ L.T + [lv[2], 0, 0]
    q = np.array([1, 1, 1, 0, 0, 0], float)
    def app(q, X): Y = X * q[:3]; c, s = np.cos(q[3]), np.sin(q[3]); return np.stack([Y[:, 0], Y[:, 1] * c - Y[:, 2] * s + q[4], Y[:, 1] * s + Y[:, 2] * c + q[5]], 1)
    for it in range(60):
        Y = app(q, P); d, j = TR.query(Y, workers=4); k = d < np.percentile(d, 80 if hull else 55)
        q = least_squares(lambda x: ((app(x, P[k]) - REF[j[k]]) / [1, 1, 1]).ravel(), q, max_nfev=6).x
    d = TR.query(app(q, P))[0]; db = cKDTree(app(q, P)).query(REF[::10])[0]
    res[f] = dict(level=lv.tolist(), sym_med=sym, scale=q[:3].tolist(), pitch_deg=float(np.degrees(q[3])), shift=q[4:].tolist(), med=float(np.median(d)), p90=float(np.percentile(d, 90)), p95=float(np.percentile(d, 95)), back_med=float(np.median(db)), back_p90=float(np.percentile(db, 90)))
    np.savez(f"{D}/{f}_al.npz", v=app(q, v1), t=t, o=o, n=np.array(n)); print(f, json.dumps({k: (np.round(x, 4).tolist()) for k, x in res[f].items()}))
json.dump(res, open(f"{D}/aliniere.json", "w"), indent=1)
