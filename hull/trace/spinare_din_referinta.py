# Clean lines + parity with the reference (asked: lucru_brat_fata's bend head -> tip is smoother than our spine and interior): the
# spine taken back from the clean fit to the reference's real rib centres (trei_linii v22: one-sign curvature, turned with the head)
# instead of being pulled along by the interior; the exterior kept; the interior rebuilt on the line exterior -> spine at the linear
# width W(s) (the confirmed one), then smoothed (third differences, MU). Per station of the current lines (the plane across the spine):
# the v22 spine's crossing. Writes the new lines + station arrays old -> new (_kor_*) + the width (_latime_*).
# Usage: python spinare_din_referinta.py <guides npz> <trei_linii current (_kor_*, _latime_*)> <trei_linii v22> <out> ; env MU=1e-4
import sys, os, numpy as np
G = np.load(sys.argv[1]); K = np.load(sys.argv[2]); K22 = np.load(sys.argv[3]); OUT = sys.argv[4]; e = lambda k, d: float(os.environ.get(k, d))
MU = e("MU", "1e-4"); sm = lambda w: w * w * (3 - 2 * w)
S0, E0, I0, st, W = K["_kor_spinare_noua"], K["_kor_exterior_nou"], K["_kor_interior_nou"], K["_latime_s"], K["_latime_w"]
SP22 = K22["spinare_brat_fata_D"]; T0 = np.gradient(S0, axis=0); T0 /= np.linalg.norm(T0, axis=1)[:, None]
def cross(L, p, n):
    sd = (L - p) @ n; k = np.where(np.sign(sd[:-1]) != np.sign(sd[1:]))[0]
    if not len(k): return None
    X = L[k] + (L[k + 1] - L[k]) * (sd[k] / (sd[k] - sd[k + 1]))[:, None]; return X[np.argmin(np.linalg.norm(X - p, axis=1))]
S2 = np.array([cross(SP22, S0[j], T0[j]) if j else SP22[0] for j in range(len(S0))], dtype=object)
ok = np.array([q is not None for q in S2]); S2 = np.array([q if q is not None else S0[j] for j, q in enumerate(S2)], float)
s38 = st[np.argmin(np.linalg.norm(S0 - G["sectiune_brat_fata_D_%02d" % int(e("SECT_LIN", "38"))].mean(0), axis=1))]
wl = sm(np.clip((s38 - st) / e("TRECERE", "80"), 0, 1)) * ok               # (the bulb from _38 on: the current lines)
S2 = S2 * wl[:, None] + S0 * (1 - wl[:, None])
S2 = S2 - T0 * np.einsum("ij,ij->i", S2 - S0, T0)[:, None]                   # (in the station's plane)
u = S2 - E0; u /= np.linalg.norm(u, axis=1)[:, None]; I2 = E0 + u * W[:, None]
def smooth(L, f0=1, f1=3):
    m = len(L); D = np.diff(np.eye(m), 3, axis=0); A = D.T @ D + MU * np.eye(m); fx = np.zeros(m, bool); fx[:f0] = True; fx[m - f1:] = True
    fr = ~fx; X = L.copy()
    for k in range(3): X[fr, k] = np.linalg.solve(A[np.ix_(fr, fr)], MU * L[fr, k] - A[np.ix_(fr, fx)] @ L[fx, k])
    return X
I2 = I2 * wl[:, None] + I0 * (1 - wl[:, None]); I2 = smooth(I2); f = np.einsum("ij,ij->i", S2 - E0, I2 - E0) / np.einsum("ij,ij->i", I2 - E0, I2 - E0)
from scipy.ndimage import gaussian_filter1d                             # (the spine's place on the line smoothed - clean line)
fs = gaussian_filter1d(f, e("NETEZ_SPINARE", "30"), mode="nearest"); wf = sm(np.clip((st[-1] - st) / 30, 0, 1)); f = f * (1 - wf) + fs * wf
S2 = E0 + (I2 - E0) * f[:, None]
def tail(L, q):
    j = int(np.argmin(np.linalg.norm(L - q, axis=1))); return L[j + 1:]
out = {"spinare_brat_fata_D": np.vstack([S2, tail(G["spinare_brat_fata_D"], S0[-1])]),
       "contur_exterior_brat_fata_D": np.vstack([E0, tail(G["contur_exterior_brat_fata_D"], E0[-1])]),
       "contur_interior_brat_fata_D": np.vstack([I2, tail(G["contur_interior_brat_fata_D"], I0[-1])])}
out["_kor_spinare_veche"], out["_kor_exterior_vechi"], out["_kor_interior_vechi"] = S0, E0, I0
out["_kor_spinare_noua"], out["_kor_exterior_nou"], out["_kor_interior_nou"] = S2, E0, I2
out["_latime_s"], out["_latime_w"] = st, W
print("SPINARE din referinta: spinarea mutata max %.1f m, interiorul max %.1f m; latimea fata de cea liniara max %.2f m" % (
    np.linalg.norm(S2 - S0, axis=1).max(), np.linalg.norm(I2 - I0, axis=1).max(), np.abs(np.linalg.norm(I2 - E0, axis=1) - W).max()))
for k in [k for k in out if not k.startswith("_")]: out[k.replace("_D", "_S")] = out[k] * [-1, 1, 1]
np.savez(OUT, **out)
