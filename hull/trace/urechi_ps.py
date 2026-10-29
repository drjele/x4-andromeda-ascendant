# The two ears redrawn from the confirmed ribs, on the PS and the rear arms themselves (asked: "folosind ghidajele,
# redesenează cele 2 urechi"; no new objects). The ribs' parameters every 2 m (coaste_ghidaje.py CO_PARAM_OUT: centre cx, outer
# / inner half-widths a / ai, top / bottom half-heights bt / bb, centre height zc) give at every y an ellipse per side. Each
# vertex is looked at from its side's rib centre in the rib's own (ellipse-scaled) measure rho: rho < 1 = inside the rib.
# The surface only grows: rho -> smooth max(rho, 1) along the ray from the centre (a balloon blown up to the rib; where the
# piece is already outside - keel, deck corners - it stays); this cannot fold a section. The PS's band that has to grow a lot
# is subdivided first (pymeshlab midpoint). Faded in over FADE m at both ends of the ribs. Pieces stay separate.
# Usage: python urechi_ps.py <pieces.npz> <rib_params.npz> <out.npz> ; env UR_K=0.04 UR_FADE=30 UR_SUBDIV=2 UR_TAUBIN=8
import sys, os, numpy as np, trimesh, pymeshlab
from scipy.sparse import coo_matrix
D = np.load(sys.argv[1]); Q = np.load(sys.argv[2]); OUT = sys.argv[3]; MX = -1700.0
K, FADE, SUB, TB = float(os.environ.get("UR_K", "0.04")), float(os.environ.get("UR_FADE", "30")), int(os.environ.get("UR_SUBDIV", "2")), int(os.environ.get("UR_TAUBIN", "8"))
o = np.argsort(Q["y"]); qy = Q["y"][o]; P_ = {k: Q[k][o] for k in ("cx", "a", "ai", "bt", "bb", "zc")}
def par(y): return {k: np.interp(y, qy, P_[k]) for k in P_}
def fade(y):
    t = np.clip(np.minimum(y - qy[0], qy[-1] - y) / FADE, 0, 1); return t * t * (3 - 2 * t)
def rho_of(v):                                          # ship coordinates; each vertex measured from its own side's rib
    p = par(v[:, 1]); s = np.where(v[:, 0] >= 0, 1.0, -1.0); cx = s * p["cx"]
    dx, dz = v[:, 0] - cx, v[:, 2] - p["zc"]; outer = (dx * s) >= 0
    ax = np.where(outer, p["a"], p["ai"]); bz = np.where(dz >= 0, p["bt"], p["bb"])
    u, w = dx / ax, dz / bz; r = np.hypot(u, w); inside = (v[:, 1] >= qy[0]) & (v[:, 1] <= qy[-1])
    return r, cx, p["zc"], inside
def smax(a, b, k):                                      # polynomial smooth maximum
    h = np.clip(k - np.abs(a - b), 0, None) / k; return np.maximum(a, b) + h * h * k / 4
R0, R1 = [float(x_) for x_ in os.environ.get("UR_RHO", "0.45,0.7").split(",")]   # deep inside the rib (caps) stays put
def grow(v, inside_end=False):
    r, cx, zc, ins = rho_of(v); tgt = 1.0
    if inside_end:                                     # the PS's end inside the arms: a hair inside the rib (no coincident skins)
        g_ = np.clip((-30 - v[:, 1]) / 10, 0, 1); tgt = 1 - 0.02 * g_
    r2 = smax(r, tgt, K); f = np.where(ins & (r > 1e-6), r2 / np.maximum(r, 1e-6), 1.0)
    wr = np.clip((r - R0) / (R1 - R0), 0, 1); wr = wr * wr * (3 - 2 * wr)
    f = 1 + (f - 1) * fade(v[:, 1]) * wr; V = v.copy(); V[:, 0] = cx + (v[:, 0] - cx) * f; V[:, 2] = zc + (v[:, 2] - zc) * f
    return V, np.linalg.norm(V - v, axis=1)
def taubin(V, f, move, it):
    E = np.r_[f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]; A = coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(len(V),) * 2).tocsr(); A.data[:] = 1
    deg = np.asarray(A.sum(1)).ravel(); inner = move & ~((A @ (~move).astype(float)) > 0)
    for _ in range(it):
        for lam in (0.5, -0.53): V[inner] += lam * ((A @ V) / deg[:, None] - V)[inner]
    return V
out = {}
for nm in ("PS", "brat_spate_D", "brat_spate_S"):
    v0 = D[nm + "__v"].astype(float) - [MX, 0, 0]; f0 = D[nm + "__f"].astype(np.int64)
    _, dm = grow(v0, nm == "PS")
    if SUB and dm.max() > 2:                            # subdivide where the piece grows by more than 2 m
        ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(vertex_matrix=v0, face_matrix=f0, v_scalar_array=(dm > 2).astype(float)))
        ms.compute_selection_by_condition_per_vertex(condselect="q > 0.5"); ms.compute_selection_transfer_vertex_to_face(); ms.apply_selection_dilatation()
        for _ in range(SUB): ms.meshing_surface_subdivision_midpoint(iterations=1, threshold=pymeshlab.PureValue(0.5), selected=True)
        m = ms.current_mesh(); v, f = m.vertex_matrix().astype(float), m.face_matrix().astype(np.int64)
    else: v, f = v0, f0
    V, dm = grow(v, nm == "PS"); V = taubin(V, f, dm > 0.05, TB)
    t = trimesh.Trimesh(V, f, process=False); ang = np.degrees(t.face_adjacency_angles)
    print("%-13s %6d -> %6d varfuri, crescute %d (max %.1f m), etans %s, falduri >120 grd %d, >60 grd %d, x %.0f..%.0f" % (
        nm, len(v0), len(V), (dm > 0.05).sum(), dm.max(), t.is_watertight, (ang > 120).sum(), (ang > 60).sum(), V[:, 0].min(), V[:, 0].max()))
    out[nm + "__v"] = (V + [MX, 0, 0]).astype(np.float32); out[nm + "__f"] = f.astype(np.int32)
np.savez(OUT, **out)
