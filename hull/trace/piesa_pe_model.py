# The arm's surface put onto the guides' own model (asked: the upper arms' surface looked uneven, wavy - the waves came from the
# station-by-station moves, so smoothing the mesh could not remove them): per section across the spine an ellipse - major axis
# exterior -> interior (the green lines' crossings), its minor radius b(s) interpolated smoothly between the ribs; along the mouth
# its exterior end on the exterior, its axis towards the interior and its size putting it through the two lips. Every vertex of the
# piece moved, within its section, onto that ellipse at the same ellipse angle; its offset along the spine kept. From rib SECT_A on
# the move fades out, past SECT_B (the bulb) nothing moves. Right arm computed, the left mirrored.
# Usage: python piesa_pe_model.py <guides npz> <piece npz> <out npz> ; env PAS=1 SECT_A=43 SECT_B=46
import sys, os, numpy as np, trimesh
from scipy.spatial import cKDTree
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d
G = np.load(sys.argv[1]); Z = np.load(sys.argv[2]); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d)); sm = lambda w: w * w * (3 - 2 * w)
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
SP, EX, IN, BZ = (G["%s_brat_fata_D" % k] for k in ("spinare", "contur_exterior", "contur_interior", "buze_gura"))
iv = int(np.argmax([np.linalg.norm(BZ[i] - BZ[0]) + np.linalg.norm(BZ[i] - BZ[-1]) for i in range(len(BZ))])); LIPS = (BZ[:iv + 1], BZ[iv:]); VX = BZ[iv]
dS = arclen(SP); TS = np.gradient(SP, axis=0); TS /= np.linalg.norm(TS, axis=1)[:, None]
def cross(L, p, n, ref=None):
    sd = (L - p) @ n; k = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    if not len(k):
        j = int(np.argmin(np.abs(sd))); return L[j] if abs(sd[j]) < 1.0 else None
    X = L[k] + (L[k + 1] - L[k]) * (sd[k] / (sd[k] - sd[k + 1]))[:, None]; r = p if ref is None else ref
    X = X[np.linalg.norm(X - p, axis=1) < 300]; return X[np.argmin(np.linalg.norm(X - r, axis=1))] if len(X) else None
sof = lambda q: dS[int(np.argmin(np.linalg.norm(SP - q, axis=1)))]
sV = sof(VX)
# minor radius per rib: in its own plane, axis exterior -> interior
sk, bk = [], []
for k in sorted([k for k in G.files if k.startswith("sectiune_brat_fata_D")], key=lambda q: int(q.split("_")[-1])):
    X = G[k]; c = X.mean(0); n = np.linalg.svd(X - c)[2][2]; E_, I_ = cross(EX, c, n, c), cross(IN, c, n, c)
    if E_ is None or I_ is None: continue
    ex = (E_ - I_) / np.linalg.norm(E_ - I_); ey = np.cross(n, ex); ey /= np.linalg.norm(ey)
    sk.append(sof(c)); bk.append(np.abs((X - (E_ + I_) / 2) @ ey).max())
o_ = np.argsort(sk); sk, bk = np.array(sk)[o_], np.array(bk)[o_]; u_ = np.r_[True, np.diff(sk) > 1]; sk, bk = sk[u_], bk[u_]
bf = PchipInterpolator(sk, bk, extrapolate=True)
sA = sof(G["sectiune_brat_fata_D_%02d" % int(e("SECT_A", "43"))].mean(0)); sB = sof(G["sectiune_brat_fata_D_%02d" % int(e("SECT_B", "46"))].mean(0))
# the model per station
st = np.arange(0, sB, e("PAS", "1")); ST = []
for s0 in st:
    i = min(max(int(np.searchsorted(dS, s0)), 1), len(SP) - 2); p = np.array([np.interp(s0, dS, SP[:, k]) for k in range(3)]); n = TS[i]
    E_, I_ = cross(EX, p, n), cross(IN, p, n)
    if E_ is None or I_ is None: ST.append(None); continue
    ex = (E_ - I_) / np.linalg.norm(E_ - I_); ey = np.cross(n, ex); ey /= np.linalg.norm(ey); b = float(bf(s0))
    a = np.linalg.norm(E_ - I_) / 2; m = (E_ + I_) / 2
    if s0 < sV:                                                           # (along the mouth: through the lips)
        aa = []
        for L in LIPS:
            q = cross(L, p, n)
            if q is None: continue
            u = (E_ - q) @ ex; y = (q - E_) @ ey; r = max(1 - (y / b) ** 2, 1e-4); aa.append(u / (1 + np.sqrt(r)))
        if aa: a = float(np.mean(aa)); m = E_ - ex * a
    ST.append((p, n, m, ex, ey, a, b))
ok = np.array([q is not None for q in ST])
for k_ in range(len(ST)):                                                  # (gaps filled from the nearest station)
    if ST[k_] is None: ST[k_] = ST[int(np.argmin(np.where(ok, np.abs(np.arange(len(ST)) - k_), 1e9)))]
A_ = np.array([q[5] for q in ST]); A_ = np.where(st < sV, gaussian_filter1d(A_, 3, mode="nearest"), A_)   # (the lips' small jitter)
V = Z["brat_fata_D__v"].copy(); V0 = V.copy(); kd = cKDTree(SP); jj = kd.query(V)[1]; sv = dS[jj] + np.einsum("ij,ij->i", V - SP[jj], TS[jj])
w = 1 - sm(np.clip((sv - sA) / max(sB - sA, 1), 0, 1)); w[sv >= sB] = 0
idx = np.clip(np.round(sv / e("PAS", "1")).astype(int), 0, len(st) - 1)
for i in np.where(w > 0)[0]:
    p, n, m, ex, ey, a, b = ST[idx[i]]; a = A_[idx[i]]
    if st[idx[i]] < sV: m = (m + ex * ST[idx[i]][5]) - ex * a                # (E stays; the smoothed a)
    q = V[i] - m; t_ = q @ n; x, y = q @ ex, q @ ey; th = np.arctan2(y / b, x / a)
    V[i] = V0[i] * (1 - w[i]) + (m + n * t_ + ex * a * np.cos(th) + ey * b * np.sin(th)) * w[i]
mv = np.linalg.norm(V - V0, axis=1); t3 = trimesh.Trimesh(V, Z["brat_fata_D__f"], process=False); cn = np.unique(t3.edges_sorted, axis=0, return_counts=True)[1]
np.savez(OUT, brat_fata_D__v=V, brat_fata_D__f=Z["brat_fata_D__f"], brat_fata_S__v=V * [-1, 1, 1], brat_fata_S__f=Z["brat_fata_D__f"][:, ::-1])
ks = [k for k in G.files if k.startswith("sectiune_brat_fata_D")]; kd2 = cKDTree(V)
print("PIESA pe model: mutata medie %.2f, max %.2f m; vertebrele pe piesa max %.2f m; ne-manifold %d; bulbul de la s %.0f neatins" % (
    mv.mean(), mv.max(), max(kd2.query(G[k])[0].max() for k in ks), int((cn > 2).sum()), sB))
