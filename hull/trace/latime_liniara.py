# The interior set by a linear width (asked: the exterior stays where it is; from rib _38 - just past the bulb - to the head the
# distance exterior -> interior grows steadily, linearly; the green lines exactly in one plane; the bulb's lines clean between _45
# and _46). Along the spine every PAS m, in the plane across it: the exterior E and interior I crossings. Width W(s) = |E - I| set
# linear from the head (its own width) to _38 (its own width), eased into the bulb's own width over BLEND m past _38; I = E + (I - E)
# direction * W. In the bulb (from _43 to the tip) the exterior and interior smoothed (third differences, MU), the tip fixed. The spine
# put on the line E-I in its section (its place along it kept). Writes the new lines + the station-by-station old -> new arrays
# (_kor_*, for mapeaza_trei.py) + the width function (for the nacelle's V point).
# Usage: python latime_liniara.py <guides npz> <out npz> ; env PAS=2 BLEND=40 MU=1e-3 SECT_LIN=38 SECT_BULB=43
import sys, os, numpy as np
G = np.load(sys.argv[1]); OUT = sys.argv[2]; e = lambda k, d: float(os.environ.get(k, d))
PAS, BL, MU = e("PAS", "2"), e("BLEND", "40"), e("MU", "1e-3"); SL, SB = int(e("SECT_LIN", "38")), int(e("SECT_BULB", "43"))
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
SP, EX, IN = (G["%s_brat_fata_D" % k] for k in ("spinare", "contur_exterior", "contur_interior"))
dS = arclen(SP); sm = lambda w: w * w * w * (10 - 15 * w + 6 * w * w)
def cross(L, p, n):
    sd = (L - p) @ n; k = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    if not len(k): return None
    X = L[k] + (L[k + 1] - L[k]) * (sd[k] / (sd[k] - sd[k + 1]))[:, None]; X = X[np.linalg.norm(X - p, axis=1) < 300]
    return X[np.argmin(np.linalg.norm(X - p, axis=1))] if len(X) else None
st, P0, E0, I0, T0 = [], [], [], [], []
for s0 in np.r_[np.arange(0, dS[-1], PAS)]:
    i = min(max(int(np.searchsorted(dS, s0)), 1), len(SP) - 2); p = np.array([np.interp(s0, dS, SP[:, k]) for k in range(3)])
    n = SP[i + 1] - SP[i - 1]; n /= np.linalg.norm(n)
    a, b = (EX[0], IN[0]) if s0 == 0 else (cross(EX, p, n), cross(IN, p, n))
    if a is None or b is None or np.linalg.norm(a - b) < 6: break
    st.append(s0); P0.append(p); E0.append(a); I0.append(b); T0.append(n)
st, P0, E0, I0, T0 = map(np.array, (st, P0, E0, I0, T0)); n_ = len(st)
sof = lambda k: st[np.argmin(np.linalg.norm(P0 - G["sectiune_brat_fata_D_%02d" % k].mean(0), axis=1))]
s38, s43 = sof(SL), sof(SB)
W0 = np.linalg.norm(E0 - I0, axis=1); U = (I0 - E0) / W0[:, None]
from scipy.ndimage import gaussian_filter1d                             # (the direction smoothed up to _38: the old interior's corners
sU = float(e("NETEZ_DIRECTIE", "15")); Us = np.c_[[gaussian_filter1d(U[:, k], sU, mode="nearest") for k in range(3)]].T   # at the mouth)
Us -= T0 * np.einsum("ij,ij->i", Us, T0)[:, None]; Us /= np.linalg.norm(Us, axis=1)[:, None]
wU = sm(np.clip(st / 30, 0, 1)) * (1 - sm(np.clip((st - (np.max(st) * 0 + 1e9)) / 1, 0, 1)))
Wl = W0[0] + (np.interp(s38, st, W0) - W0[0]) * st / s38                    # the linear width (head -> _38)
wb = sm(np.clip((st - s38) / BL, 0, 1)); W = np.where(st <= s38, Wl, Wl * (1 - wb) + W0 * wb)
s38_ = st[np.argmin(np.linalg.norm(P0 - G["sectiune_brat_fata_D_%02d" % SL].mean(0), axis=1))]
wU = sm(np.clip(st / 30, 0, 1)) * (1 - sm(np.clip((st - s38_) / BL, 0, 1)))   # (head end and from _38 on: its own direction)
U = U * (1 - wU[:, None]) + Us * wU[:, None]; U /= np.linalg.norm(U, axis=1)[:, None]
E1, I1 = E0.copy(), E0 + U * W[:, None]
def smooth(L, j0, MU=MU):                                                         # third differences from station j0 to the end, ends fixed
    X = L.copy(); m = len(L) - j0; D = np.diff(np.eye(m), 3, axis=0); A = D.T @ D + MU * np.eye(m)
    fx = np.zeros(m, bool); fx[:3] = True; fx[-1] = True; fr = ~fx; Y = L[j0:]
    for k in range(3): X[j0:][fr, k] = np.linalg.solve(A[np.ix_(fr, fr)], MU * Y[fr, k] - A[np.ix_(fr, fx)] @ Y[fx, k])
    return X
j43 = int(np.searchsorted(st, s43)); E1 = smooth(E1, j43, e("MU_EXT", "1e-5"))
I1 = smooth(I1, int(np.searchsorted(st, s38 - e("INT_NETEZ_INAINTE", "40"))), )   # (the interior from just before _38: the bulb's neck eased into the linear part)
f_ = np.einsum("ij,ij->i", P0 - E1, I1 - E1) / np.einsum("ij,ij->i", I1 - E1, I1 - E1)   # the spine onto the line E-I, its place kept
fe = np.einsum("ij,ij->i", P0 - E0, I0 - E0) / np.einsum("ij,ij->i", I0 - E0, I0 - E0)
from scipy.ndimage import gaussian_filter1d                             # (its place smoothed: the old interior had a corner at the lips' V)
fs = gaussian_filter1d(fe, float(e("NETEZ_SPINARE", "20")), mode="nearest"); wE = sm(np.clip(st / 40, 0, 1)) * sm(np.clip((st[-1] - st) / 40, 0, 1))
S1 = E1 + (I1 - E1) * (fe * (1 - wE) + fs * wE)[:, None]
def tail(L, q):
    j = int(np.argmin(np.linalg.norm(L - q, axis=1))); return L[j + 1:]
out = {"spinare_brat_fata_D": np.vstack([S1, tail(SP, P0[-1])]), "contur_exterior_brat_fata_D": np.vstack([E1, tail(EX, E0[-1])]),
       "contur_interior_brat_fata_D": np.vstack([I1, tail(IN, I0[-1])])}
out["_kor_spinare_veche"], out["_kor_exterior_vechi"], out["_kor_interior_vechi"] = P0, E0, I0
out["_kor_spinare_noua"], out["_kor_exterior_nou"], out["_kor_interior_nou"] = S1, E1, I1
out["_latime_s"], out["_latime_w"] = st, W
dev = np.linalg.norm(np.cross(I1 - E1, S1 - E1), axis=1) / np.linalg.norm(I1 - E1, axis=1)
print("LATIME liniara de la cap (%.0f m) la _38 (s %.0f, %.0f m), trecere %.0f m; bulb netezit de la _43 (s %.0f); exteriorul mutat max %.2f m "
      "(in bulb), interiorul max %.1f m; spinarea mutata max %.2f m, fata de dreapta E-I %.3f m; %d statii pana la s %.0f" % (
      W0[0], s38, np.interp(s38, st, W0), BL, s43, np.linalg.norm(E1 - E0, axis=1).max(), np.linalg.norm(I1 - I0, axis=1).max(),
      np.linalg.norm(S1 - P0, axis=1).max(), dev.max(), n_, st[-1]))
for k in [k for k in out if not k.startswith("_")]: out[k.replace("_D", "_S")] = out[k] * [-1, 1, 1]
np.savez(OUT, **out)
