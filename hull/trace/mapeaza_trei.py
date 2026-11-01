# The rest of the front arm carried onto the three refitted band lines (asked: the ribs touching the new green lines / the head, the
# nacelle's V point in the plane of the band and the green lines): per spine station the old lines -> the new ones (_kor_* arrays from
# trei_din_referinta.py) give a local frame change - origin spine -> spine, the band direction (spine -> exterior) turned onto the new
# one, the scale along it on each side (exterior side by the exterior's distance, interior side by the interior's; along the mouth,
# where the interior line is the lips' middle, the same), the across direction kept perpendicular, the thickness kept. A point is
# placed by its continuous position along the old spine, blended between its two stations; past the last station (the lobe) and
# at the head (both lines fixed there) nothing moves. Maps guide npz files (every array, right arm) and meshes (v / f or <k>__v).
# Usage: python mapeaza_trei.py <trei_linii npz> <in.npz> <out.npz> [<in> <out> ...]
import sys, numpy as np
from scipy.spatial import cKDTree
K = np.load(sys.argv[1]); arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
S0, E0, I0, S1, E1, I1 = (K["_kor_%s" % k] for k in ("spinare_veche", "exterior_vechi", "interior_vechi", "spinare_noua", "exterior_nou", "interior_nou"))
def frames(Sp, E):
    T = np.gradient(Sp, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]; D = E - Sp; D -= T * np.einsum("ij,ij->i", D, T)[:, None]
    D /= np.linalg.norm(D, axis=1)[:, None]; N = np.cross(T, D); return T, D, N
T0, D0, N0 = frames(S0, E0); T1, D1, N1 = frames(S1, E1)
I0f = np.where(np.isfinite(I0), I0, S0 - (E0 - S0)); I1f = np.where(np.isfinite(I1), I1, S1 - (E1 - S1))
_, Di0, Ni0 = frames(S0, 2 * S0 - I0f); _, Di1, Ni1 = frames(S1, 2 * S1 - I1f)   # (interior side: its own direction, spine -> interior)
se = np.linalg.norm(E1 - S1, axis=1) / np.linalg.norm(E0 - S0, axis=1)
si = np.linalg.norm(I1 - S1, axis=1) / np.linalg.norm(I0 - S0, axis=1); si = np.where(np.isfinite(si), si, se)
ds0 = arclen(S0); dense = np.linspace(0, ds0[-1], 20 * len(S0)); SD = np.c_[[np.interp(dense, ds0, S0[:, k]) for k in range(3)]].T; KD = cKDTree(SD)
def move(P):
    P = np.asarray(P, float); sh = P.shape; Q = P.reshape(-1, 3); s_ = dense[KD.query(Q)[1]]
    i = np.clip(np.searchsorted(ds0, s_) - 1, 0, len(S0) - 2); f = np.clip((s_ - ds0[i]) / (ds0[i + 1] - ds0[i]), 0, 1); R = np.zeros_like(Q)
    for j, w in ((i, 1 - f), (i + 1, f)):
        v = Q - S0[j]; a = np.einsum("ij,ij->i", v, T0[j]); b = np.einsum("ij,ij->i", v, D0[j]); c = np.einsum("ij,ij->i", v, N0[j])
        pe = S1[j] + a[:, None] * T1[j] + (b * se[j])[:, None] * D1[j] + c[:, None] * N1[j]
        bi = np.einsum("ij,ij->i", v, Di0[j]); ci = np.einsum("ij,ij->i", v, Ni0[j])
        pi = S1[j] + a[:, None] * T1[j] + (bi * si[j])[:, None] * Di1[j] + ci[:, None] * Ni1[j]
        R += w[:, None] * np.where((b >= 0)[:, None], pe, pi)
    end = s_ >= ds0[-1]; R[end] = Q[end]; return R.reshape(sh)
for a_, b_ in zip(sys.argv[2::2], sys.argv[3::2]):
    Z = np.load(a_); o = {}
    for k in Z.files:
        if k.endswith("__f") or k == "f" or k.startswith("_"): o[k] = Z[k]; continue
        if k.endswith("_S") or "_S_" in k or k.endswith("_S__v"): continue
        o[k] = move(Z[k])
    for k in list(o):                                                      # the left arm = the mirror
        if (k.endswith("_D") or "_D_" in k) and not k.endswith(("__v", "__f")): o[k.replace("_D", "_S")] = o[k] * [-1, 1, 1]
        if k.endswith("_D__v"): o[k.replace("_D__v", "_S__v")] = o[k] * [-1, 1, 1]; o[k.replace("_D__v", "_S__f")] = Z[k.replace("__v", "__f")][:, ::-1]
    for k in ("spinare_brat_fata_D", "contur_exterior_brat_fata_D", "contur_interior_brat_fata_D"):   # the three lines themselves: the new ones
        if k in o: o[k] = K[k]; o[k.replace("_D", "_S")] = K[k] * [-1, 1, 1]
    np.savez(b_, **o); print("MUTAT %s -> %s (%d chei)" % (a_.split("/")[-1], b_.split("/")[-1], len(o)))
