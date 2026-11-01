# Clean lines for the green guides (asked: clean lines for the green and the blue ones): the exterior and the interior smoothed on
# third differences along the spine (stations every PAS m in the planes across it, MU), the head end (3 stations: position and the
# head's direction) and the snout beyond the last station fixed; the spine put back on the line exterior -> interior, its place along
# it smoothed. Writes the new lines + station arrays old -> new (_kor_*, for mapeaza_trei.py) + the linear width of the earlier step
# (_latime_*, for nacela_offset.py) re-sampled on the new stations.
# Usage: python curata_verzi.py <guides npz> <trei_linii with _latime_*> <out npz> ; env PAS=2 MU=1e-4 NETEZ_SPINARE=30
import sys, os, numpy as np
from scipy.ndimage import gaussian_filter1d
G = np.load(sys.argv[1]); K0 = np.load(sys.argv[2]); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d))
PAS, MU = e("PAS", "2"), e("MU", "1e-4")
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
SP, EX, IN = (G["%s_brat_fata_D" % k] for k in ("spinare", "contur_exterior", "contur_interior")); dS = arclen(SP)
def cross(L, p, n):
    sd = (L - p) @ n; k = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    if not len(k): return None
    X = L[k] + (L[k + 1] - L[k]) * (sd[k] / (sd[k] - sd[k + 1]))[:, None]; X = X[np.linalg.norm(X - p, axis=1) < 300]
    return X[np.argmin(np.linalg.norm(X - p, axis=1))] if len(X) else None
st, P0, E0, I0 = [], [], [], []
for s0 in np.arange(0, dS[-1], PAS):
    i = min(max(int(np.searchsorted(dS, s0)), 1), len(SP) - 2); p = np.array([np.interp(s0, dS, SP[:, k]) for k in range(3)])
    n = SP[i + 1] - SP[i - 1]; n /= np.linalg.norm(n)
    a, b = (EX[0], IN[0]) if s0 == 0 else (cross(EX, p, n), cross(IN, p, n))
    if a is None or b is None or np.linalg.norm(a - b) < 6: break
    st.append(s0); P0.append(p); E0.append(a); I0.append(b)
st, P0, E0, I0 = map(np.array, (st, P0, E0, I0))
cm = G["sectiune_brat_fata_D_%02d" % int(e("SECT_CAPAT", "46"))].mean(0); smax = st[np.argmin(np.linalg.norm(P0 - cm, axis=1))]
m_ = st <= smax; st, P0, E0, I0 = st[m_], P0[m_], E0[m_], I0[m_]; n_ = len(st)   # (up to the snout's ribs; past them the lines stay)
def smooth(L, f0=3, f1=3):
    m = len(L); D = np.diff(np.eye(m), 3, axis=0); A = D.T @ D + MU * np.eye(m); fx = np.zeros(m, bool); fx[:f0] = True; fx[m - f1:] = True
    fr = ~fx; X = L.copy()
    for k in range(3): X[fr, k] = np.linalg.solve(A[np.ix_(fr, fr)], MU * L[fr, k] - A[np.ix_(fr, fx)] @ L[fx, k])
    return X
F0 = int(e("FIX_CAP", "1")); E1, I1 = smooth(E0, F0), smooth(I0, F0)   # (at the head: its position only)
fe = np.einsum("ij,ij->i", P0 - E0, I0 - E0) / np.einsum("ij,ij->i", I0 - E0, I0 - E0)
fs = gaussian_filter1d(fe, e("NETEZ_SPINARE", "30"), mode="nearest"); sm = lambda w: w * w * (3 - 2 * w)
w = sm(np.clip((st[-1] - st) / 30, 0, 1)); S1 = E1 + (I1 - E1) * (fe * (1 - w) + fs * w)[:, None]
def tail(L, q):
    j = int(np.argmin(np.linalg.norm(L - q, axis=1))); return L[j + 1:]
out = {"spinare_brat_fata_D": np.vstack([S1, tail(SP, P0[-1])]), "contur_exterior_brat_fata_D": np.vstack([E1, tail(EX, E0[-1])]),
       "contur_interior_brat_fata_D": np.vstack([I1, tail(IN, I0[-1])])}
out["_kor_spinare_veche"], out["_kor_exterior_vechi"], out["_kor_interior_vechi"] = P0, E0, I0
out["_kor_spinare_noua"], out["_kor_exterior_nou"], out["_kor_interior_nou"] = S1, E1, I1
out["_latime_s"], out["_latime_w"] = st, np.interp(st, K0["_latime_s"], K0["_latime_w"])
def bend(L, plane):
    d = arclen(L); u = np.arange(0, d[-1], 2.0); Q = np.c_[[np.interp(u, d, L[:, k]) for k in range(3)]].T
    t = np.gradient(Q[:, :2], axis=0) if plane == "sus" else np.c_[np.linalg.norm(np.gradient(Q[:, :2], axis=0), axis=1), np.gradient(Q[:, 2])]
    k = np.degrees(np.gradient(np.unwrap(np.arctan2(t[:, 1], t[:, 0])))) / 2; return np.abs(np.diff(k)).max()
for k_, a_, b_ in (("exterior", E0, E1), ("interior", I0, I1), ("spinare", P0, S1)):
    print("%-9s mutat max %.2f m; salt maxim de curbura (grd/m pe 2 m) de sus %.3f -> %.3f, profil %.3f -> %.3f" % (
        k_, np.linalg.norm(b_ - a_, axis=1).max(), bend(a_, "sus"), bend(b_, "sus"), bend(a_, "profil"), bend(b_, "profil")))
for k in [k for k in out if not k.startswith("_")]: out[k.replace("_D", "_S")] = out[k] * [-1, 1, 1]
np.savez(OUT, **out)
