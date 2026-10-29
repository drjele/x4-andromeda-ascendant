# The PS itself extended into the ear on ONE side (asked: no new objects, only the PS lengthened - one side built, the other
# keeps the guides): the PS's side wall between the attach lines (103's inner edges, taken onto the PS's section) is first
# subdivided (pymeshlab midpoint, only there), then every point of it, at its height y, is moved onto the ear's profile at
# the same fraction of the arc: the top curve carrying on the PS's own section (point, direction, curvature - quintic), the
# rounded blade MARGINE m at the outer edge (in one plane), the bottom curve back. Fades in from the PS's end (y0) over FADE m
# and out at the nose. Then a light Taubin there. Writes the new PS (world coordinates).
# Usage: python ps_ureche.py <pieces.npz> <103_D.npz> <out.npz> ; env UR_MARGINE=4 UR_SUBDIV=2 UR_FADE=40
import sys, os, numpy as np, trimesh, pymeshlab
from scipy.sparse import coo_matrix
D = np.load(sys.argv[1]); R = np.load(sys.argv[2])["v"].astype(float).reshape(-1, 4, 3); OUT = sys.argv[3]; MX = -1700.0
MG, SUB, FADE = float(os.environ.get("UR_MARGINE", "4")), int(os.environ.get("UR_SUBDIV", "2")), float(os.environ.get("UR_FADE", "40"))
v0 = D["PS__v"].astype(float) - [MX, 0, 0]; f0 = D["PS__f"].astype(np.int64)       # ship coordinates (right half: x > 0)
ps0 = trimesh.Trimesh(v0, f0, process=False)
edge = (R[:, 1] + R[:, 2]) / 2; A_ = np.c_[edge[:, 0], edge[:, 1], np.ones(len(edge))]; edge[:, 2] = A_ @ np.linalg.lstsq(A_, edge[:, 2], rcond=None)[0]
ry = R[:, 0, 1]; o = np.argsort(ry)
def at(y, P): return np.array([np.interp(y, ry[o], P[o, k]) for k in range(3)])
YMIN, YMAX = v0[:, 1].min() + 2, min(R[:, :, 1].max(), v0[:, 1].max()) - 2
def section_arc(y):                                    # the PS's right outline at y between the two attach points (outwards)
    s = ps0.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: return None
    tA, bA = at(y, R[:, 0])[[0, 2]], at(y, R[:, 3])[[0, 2]]; best = None
    for e in s.discrete:
        e = e[:, [0, 2]]
        if e[:, 0].max() < 1: continue
        it, ib = np.argmin(np.linalg.norm(e - tA, axis=1)), np.argmin(np.linalg.norm(e - bA, axis=1))
        d = np.linalg.norm(e[it] - tA) + np.linalg.norm(e[ib] - bA)
        if best is None or d < best[0]: best = (d, e, it, ib)
    if best is None or best[0] > 12: return None
    _, e, it, ib = best; n = len(e) - 1; e = e[:-1] if np.allclose(e[0], e[-1]) else e; n = len(e)
    p1 = [(it + k) % n for k in range((ib - it) % n + 1)]; p2 = [(it - k) % n for k in range((it - ib) % n + 1)]
    arc = e[p1] if e[p1][:, 0].max() >= e[p2][:, 0].max() else e[p2]          # the outer way round
    return arc
def quintic(p0, t0, k0, p1, n=40):
    L = np.linalg.norm(p1 - p0); k0 = np.clip(k0, -0.8 / L, 0.8 / L); n0 = np.array([-t0[1], t0[0]])
    d0, dd0, d1 = L * t0, L * L * k0 * n0, np.array([L, 0.0]); s_ = np.linspace(0, 1, n)[:, None]
    h = [1 - 10*s_**3 + 15*s_**4 - 6*s_**5, s_ - 6*s_**3 + 8*s_**4 - 3*s_**5, 0.5*s_**2 - 1.5*s_**3 + 1.5*s_**4 - 0.5*s_**5,
         10*s_**3 - 15*s_**4 + 6*s_**5, -4*s_**3 + 7*s_**4 - 3*s_**5]
    return h[0] * p0 + h[1] * d0 + h[2] * dd0 + h[3] * p1 + h[4] * d1
def _incoming(y, p):                                   # the PS's section arriving at p from the inside: direction, curvature
    s = ps0.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0]); best = None
    for e in s.discrete:
        e = e[:, [0, 2]]; d = np.linalg.norm(e - p, axis=1); i = np.argmin(d)
        if best is None or d[i] < best[0]: best = (d[i], e, i)
    _, e, i = best; n = len(e); a_, c_ = e[(i - 10) % n], e[(i + 10) % n]
    q = a_ if a_[0] < c_[0] else c_                   # the neighbour further in (smaller x) = where the curve comes from
    t = p - q; t /= np.linalg.norm(t); r = c_ if q is a_ else a_
    u, w = p - q, r - p; k = 2 * np.arctan2(u[0] * w[1] - u[1] * w[0], u @ w) / (np.linalg.norm(u) + np.linalg.norm(w) + 1e-9)
    return t, -k                                      # carried on outwards: the PS's turn continues the same way
def profile(y, arc):                                   # ear profile at y: top (PS-continued) -> blade -> bottom, by arc length
    e = at(y, edge)[[0, 2]]; et, eb = e + [0, MG / 2], e - [0, MG / 2]
    tu, ku = _incoming(y, arc[0]); td, kd = _incoming(y, arc[-1])
    up = quintic(arc[0], tu, ku, et); dn = quintic(arc[-1], td, kd, eb)
    ang = np.linspace(np.pi / 2, -np.pi / 2, 9)[1:-1]; tip = e + np.c_[(MG / 2) * np.cos(ang), (MG / 2) * np.sin(ang)]
    P = np.vstack([up, tip, dn[::-1]]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; return P, d / d[-1]
# 1) which vertices are on the side wall (right half, between the attach points): per 1 m slice
def classify(v):
    lab = np.zeros(len(v)); arcs = {}
    for yb in np.arange(np.floor(YMIN), np.ceil(YMAX) + 1):
        arc = section_arc(yb)
        if arc is None or len(arc) < 4: continue
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(arc, axis=0), axis=1))]; arcs[yb] = (arc, d / d[-1])
    for yb, (arc, s) in arcs.items():
        sel = (np.abs(v[:, 1] - yb) <= 0.5) & (v[:, 0] > 1)
        if not sel.any(): continue
        p = v[sel][:, [0, 2]]; dd = np.linalg.norm(p[:, None] - arc[None], axis=2); j = dd.argmin(1); ok = dd.min(1) < 3
        idx = np.where(sel)[0][ok]; lab[idx] = 1
    return lab, arcs
lab, arcs = classify(v0)
ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(vertex_matrix=v0, face_matrix=f0, v_scalar_array=lab))
ms.compute_selection_by_condition_per_vertex(condselect="q > 0.5"); ms.compute_selection_transfer_vertex_to_face()
ms.apply_selection_dilatation()
for _ in range(SUB): ms.meshing_surface_subdivision_midpoint(iterations=1, threshold=pymeshlab.PureValue(0.5), selected=True)
m = ms.current_mesh(); v, f = m.vertex_matrix().astype(float), m.face_matrix().astype(np.int64)
print("PS: %d -> %d varfuri dupa subdivizare (peretele lateral, dreapta)" % (len(v0), len(v)))
# 2) move the wall onto the ear profile, same fraction of the arc
from scipy.ndimage import gaussian_filter1d                 # one grid of profiles (y x fraction), smoothed along y, so a
NS = 200; fs = np.linspace(0, 1, NS); ys = np.array(sorted(arcs)); G = np.zeros((len(ys), NS, 2))   # face over two slices
for k, yb in enumerate(ys):                                   # is not pulled two ways
    P, sp = profile(yb, arcs[yb][0]); G[k] = np.c_[np.interp(fs, sp, P[:, 0]), np.interp(fs, sp, P[:, 1])]
G = gaussian_filter1d(G, float(os.environ.get("UR_NET_Y", "3")), axis=0, mode="nearest")
V = v.copy(); moved = np.zeros(len(v), bool)
for yb, (arc, s) in arcs.items():
    sel = (np.abs(v[:, 1] - yb) <= 0.5) & (v[:, 0] > 1)
    if not sel.any(): continue
    p = v[sel][:, [0, 2]]; A0, A1 = arc[:-1], arc[1:]; sg = A1 - A0; L2 = (sg ** 2).sum(1) + 1e-12   # projection onto the
    tt = np.clip(((p[:, None] - A0[None]) * sg[None]).sum(2) / L2[None], 0, 1)                            # arc's segments:
    q = A0[None] + tt[..., None] * sg[None]; dd = np.linalg.norm(p[:, None] - q, axis=2); j = dd.argmin(1)  # a continuous
    tj = tt[np.arange(len(p)), j]; fr = s[j] + tj * (s[j + 1] - s[j])                                     # fraction
    ok = (dd.min(1) < 1.5) & (fr > 0.002) & (fr < 0.998)   # only the wall itself (not the deck / belly next to its ends)
    if not ok.any(): continue
    idx = np.where(sel)[0][ok]; fr = fr[ok]; yv = v[idx, 1]
    kf = np.clip(np.interp(yv, ys, np.arange(len(ys))), 0, len(ys) - 1); k0 = np.floor(kf).astype(int); k1 = np.minimum(k0 + 1, len(ys) - 1); a_ = (kf - k0)[:, None]
    fi = fr * (NS - 1); i0 = np.floor(fi).astype(int); i1 = np.minimum(i0 + 1, NS - 1); b_ = (fi - i0)[:, None]
    g = lambda k_: G[k_, i0] * (1 - b_) + G[k_, i1] * b_
    tgt = g(k0) * (1 - a_) + g(k1) * a_
    w = np.clip((yv - YMIN) / FADE, 0, 1); w = w * w * (3 - 2 * w)
    V[idx, 0] = v[idx, 0] + w * (tgt[:, 0] - v[idx, 0]); V[idx, 2] = v[idx, 2] + w * (tgt[:, 1] - v[idx, 2]); moved[idx] = True
# 3) light Taubin on what moved (slices -> smooth along y)
E = np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]; Aj = coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(len(V),) * 2).tocsr(); Aj.data[:] = 1
deg = np.asarray(Aj.sum(1)).ravel(); inner = moved & ~(((Aj @ (~moved).astype(float)) > 0))
for _ in range(int(os.environ.get("UR_TAUBIN", "15"))):
    for lam in (0.5, -0.53): V[inner] += lam * ((Aj @ V) / deg[:, None] - V)[inner]
n0 = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); n1 = np.cross(V[f[:, 1]] - V[f[:, 0]], V[f[:, 2]] - V[f[:, 0]])
t = trimesh.Trimesh(V, f, process=False)
print("PS cu urechea (dreapta): %d varfuri mutate, x max %.0f (era %.0f), fete intoarse %d, degenerate %d, etans %s" % (
    moved.sum(), V[:, 0].max(), v[:, 0].max(), ((n0 * n1).sum(1) < 0).sum(), (t.area_faces < 1e-6).sum(), t.is_watertight))
np.savez(OUT, v=(V + [MX, 0, 0]).astype(np.float32), f=f.astype(np.int32))
