# The two ears as NEW separate pieces built from the confirmed ribs (asked: the arms and the PS left alone; the ears from the
# guides, going from the outside inwards and stopping where they touch the arms and the PS). At every rib (parameters every
# 2 m from coaste_ghidaje.py CO_PARAM_OUT) the right rib is walked from its outer edge upwards and downwards until it enters
# or comes within TOUCH m of the PS / arm section there; that stretch of rib is the ear's section, its two ends carried
# IN m further along the rib (into the piece, hidden) and closed straight. Ribs whose edge is already inside the PS (the nose)
# are kept until the edge is 4 m deep (front cap hidden); the back end draws in onto the arm over UR_COADA m; contact angles
# smoothed along y (always further in, never short - no gaps, no rings). Sections joined into a watertight piece, ends capped; the left ear = mirror. Ship coordinates, centred.
# Usage: python urechi_piese.py <pieces.npz> <rib_params.npz> <out_D.npz> <out_S.npz> ; env UR_TOUCH=1 UR_IN=2 UR_N=48
import sys, os, numpy as np, trimesh
from matplotlib.path import Path
D = np.load(sys.argv[1]); Q = np.load(sys.argv[2]); OD, OS = sys.argv[3], sys.argv[4]; MX = -1700.0
TOUCH, IN, N = float(os.environ.get("UR_TOUCH", "1")), float(os.environ.get("UR_IN", "2")), int(os.environ.get("UR_N", "48"))
mesh = trimesh.util.concatenate([trimesh.Trimesh(D[n + "__v"] - [MX, 0, 0], D[n + "__f"], process=False) for n in ("PS", "brat_spate_D", "brat_spate_S")])
def rib(p, th):                                        # right rib point at angle th (0 = outer edge, +pi/2 top, -pi/2 bottom)
    c, s = np.cos(th), np.sin(th); ax = np.where(c >= 0, p["a"], p["ai"]); bz = np.where(s >= 0, p["bt"], p["bb"])
    return np.c_[p["cx"] + ax * c, p["zc"] + bz * s]
def blocked(pts, loops, segs):                         # inside the section, or within TOUCH m of its outline
    ins = np.zeros(len(pts), bool)
    for L in loops: ins |= Path(L).contains_points(pts)
    A0, A1 = segs; sg = A1 - A0; L2 = (sg ** 2).sum(1) + 1e-12
    t = np.clip(((pts[:, None] - A0[None]) * sg[None]).sum(2) / L2[None], 0, 1); d = np.linalg.norm(pts[:, None] - (A0[None] + t[..., None] * sg[None]), axis=2).min(1)
    return ins | (d < TOUCH)
th = np.linspace(0, np.pi, 721)
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
br = trimesh.Trimesh(D["brat_spate_D__v"] - [MX, 0, 0], D["brat_spate_D__f"], process=False)
yq = Q["y"]; yend = yq.min(); TAPER = float(os.environ.get("UR_COADA", "40"))
rows = []
for i, y in enumerate(yq):
    p = {k: float(Q[k][i]) for k in ("cx", "a", "ai", "bt", "bb", "zc")}
    if y < yend + TAPER:                               # the back end draws in onto the arm (2 m under its outer side)
        sa = br.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
        if sa is not None:
            ra = max([e[:, 0].max() for e in sa.discrete]) - p["cx"]; t_ = 1 - (y - yend) / TAPER; t_ = t_ * t_ * (3 - 2 * t_)
            p["a"] = (1 - t_) * p["a"] + t_ * (ra - 2)
    s = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: continue
    loops = [e[:, [0, 2]] for e in s.discrete]; segs = (np.vstack([L[:-1] for L in loops]), np.vstack([L[1:] for L in loops]))
    e0 = rib(p, np.array([0.0]))
    ins = any(Path(L).contains_points(e0)[0] for L in loops)
    if ins:                                            # the edge inside the PS: kept until 4 m deep (front cap hidden in the nose)
        A0, A1 = segs; sg = A1 - A0; t = np.clip(((e0 - A0) * sg).sum(1) / ((sg ** 2).sum(1) + 1e-12), 0, 1)
        if np.linalg.norm(e0 - (A0 + t[:, None] * sg), axis=1).min() > 4: continue
    up = blocked(rib(p, th), loops, segs); dn = blocked(rib(p, -th), loops, segs)
    tu = th[np.argmax(up)] if up.any() else th[-1]; td = th[np.argmax(dn)] if dn.any() else th[-1]
    if ins: tu = td = 0.05
    rows.append((y, p, tu, td, loops))
TU = np.array([r[2] for r in rows]); TD = np.array([r[3] for r in rows]); SM = float(os.environ.get("UR_NET", "4"))
def seal(pt, loops):                                   # a closing end not yet inside the PS / arm: pushed towards the middle of
    best = None                                        # the nearest loop until it is 3 m inside (no slit between ear and piece)
    for L in loops:
        if Path(L).contains_points(pt[None])[0]: return pt
        d = np.linalg.norm(L - pt, axis=1).min()
        if best is None or d < best[0]: best = (d, L)
    L = best[1]; c = L.mean(0); dirn = c - pt; dist = np.linalg.norm(dirn); dirn /= dist + 1e-9
    for k in np.arange(0.5, dist, 0.5):
        q = pt + k * dirn
        if Path(L).contains_points(q[None])[0]: return pt + (k + 3) * dirn
    return pt
TU = np.minimum(gaussian_filter1d(maximum_filter1d(TU, 9), SM), np.pi); TD = np.minimum(gaussian_filter1d(maximum_filter1d(TD, 9), SM), np.pi)
secs, ys = [], []                                      # (contact angles smoothed along y, always a bit further in - no gaps)
for (y, p, _, _, loops), tu, td in zip(rows, TU, TD):
    du = IN / np.hypot(p["a"], p["bt"]) * 2; dd = IN / np.hypot(p["a"], p["bb"]) * 2
    T = np.linspace(-(td + dd), tu + du, N); P = rib(p, T)
    a0, a1 = seal(P[0], loops), seal(P[-1], loops); k_ = max(3, N // 16)        # the last few points eased onto the sealed ends
    wv = np.linspace(1, 0, k_)[:, None] ** 2
    P[:k_] = P[:k_] + wv * (a0 - P[0]); P[-k_:] = P[-k_:] + wv[::-1] * (a1 - P[-1])
    secs.append(np.c_[P[:, 0], np.full(N, y), P[:, 1]]); ys.append(y)
L = np.array(secs); n = len(L)
if n < 2: sys.exit("prea putine sectiuni")
o = np.argsort(np.array(ys))[::-1]; L = L[o]                              # front to back
V = L.reshape(-1, 3); F = []
for i in range(n - 1):
    a = i * N + np.arange(N); b = a + N; F += [np.c_[a, np.roll(a, -1), np.roll(b, -1)], np.c_[a, np.roll(b, -1), b]]
c0, c1 = L[0].mean(0), L[-1].mean(0); V = np.vstack([V, c0, c1]); i0, i1 = len(V) - 2, len(V) - 1; a = np.arange(N)
F.append(np.c_[np.roll(a, -1), a, np.full(N, i0)]); b = (n - 1) * N + a; F.append(np.c_[b, np.roll(b, -1), np.full(N, i1)])
t = trimesh.Trimesh(V, np.vstack(F), process=True); trimesh.repair.fix_winding(t); trimesh.repair.fix_normals(t)
V, F = np.asarray(t.vertices), np.asarray(t.faces); ang = np.degrees(t.face_adjacency_angles)
print("URECHE: %d sectiuni (y %.0f..%.0f), %d triunghiuri, etans %s, volum %.0f m3, x %.0f..%.0f z %.0f..%.0f, falduri >120 grd %d" % (
    n, L[:, 0, 1].max(), L[:, 0, 1].min(), len(F), t.is_watertight, t.volume, V[:, 0].min(), V[:, 0].max(), V[:, 2].min(), V[:, 2].max(), (ang > 120).sum()))
np.savez(OD, v=V.astype(np.float32), f=F.astype(np.int32)); np.savez(OS, v=(V * [-1, 1, 1]).astype(np.float32), f=F[:, ::-1].astype(np.int32))
