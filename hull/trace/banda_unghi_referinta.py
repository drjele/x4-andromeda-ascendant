# Our band's angle about the spine matched to the reference's (asked: analyse the deviation between the two bands and fit
# g_bfs_banda_spinare to the reference): the reference band (banda_referinta.py on the reference arm turned with the head, its
# sections on our spine) gives per station the major axis' direction; our band (exterior -> interior) turned about the spine onto it,
# the angle smoothed (NETEZ stations), eased in from the head over CAP_RAMPA m and out to 0 at _36 (kept in place) over FIX_RAMPA m.
# The width stays (the linear one). Writes station arrays old -> new (_kor_*), _latime_* and the reference nacelle V points carried.
# Usage: python banda_unghi_referinta.py <guides npz> <trei_linii current> <reference band npz> <out> ; env NETEZ=10 CAP_RAMPA=40 FIX_RAMPA=150
import sys, os, numpy as np
from scipy.ndimage import gaussian_filter1d
G = np.load(sys.argv[1]); K = np.load(sys.argv[2]); B = np.load(sys.argv[3]); OUT = sys.argv[4]; e = lambda k, d: float(os.environ.get(k, d))
sm = lambda w: w * w * (3 - 2 * w)
S, E, I, st = K["_kor_spinare_noua"], K["_kor_exterior_nou"], K["_kor_interior_nou"], K["_latime_s"]
T = np.gradient(S, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]; RE, RC, RI = B["exterior_D"], B["centru_D"], B["interior_D"]
s36 = st[int(np.argmin(np.linalg.norm(S - G["sectiune_brat_fata_D_%02d" % int(e("SECT_FIX", "36"))].mean(0), axis=1)))]
ang = np.full(len(st), np.nan)
for j in range(len(st)):
    sd = np.abs((RC - S[j]) @ T[j]); k = int(np.argmin(sd + 0.02 * np.linalg.norm(RC - S[j], axis=1)))
    if sd[k] > 6: continue
    u = E[j] - I[j]; u -= T[j] * (u @ T[j]); u /= np.linalg.norm(u); v = np.cross(T[j], u)
    ur = RE[k] - RI[k]; ur -= T[j] * (ur @ T[j]); ur /= np.linalg.norm(ur); ang[j] = np.arctan2(ur @ v, ur @ u)
ok = np.isfinite(ang); ang = np.interp(st, st[ok], ang[ok]); ang = gaussian_filter1d(ang, e("NETEZ", "10"), mode="nearest")
w = sm(np.clip(st / e("CAP_RAMPA", "40"), 0, 1)) * sm(np.clip((s36 - st) / e("FIX_RAMPA", "150"), 0, 1)); dl = ang * w
def rot(P, j, a):
    v = P - S[j]; c, s_ = np.cos(a), np.sin(a); return S[j] + v * c + np.cross(T[j], v) * s_ + T[j] * (v @ T[j]) * (1 - c)
E1 = np.array([rot(E[j], j, dl[j]) for j in range(len(st))]); I1 = np.array([rot(I[j], j, dl[j]) for j in range(len(st))])
def tail(L, q):
    j = int(np.argmin(np.linalg.norm(L - q, axis=1))); return L[j + 1:]
out = {"spinare_brat_fata_D": np.vstack([S, tail(G["spinare_brat_fata_D"], S[-1])]),
       "contur_exterior_brat_fata_D": np.vstack([E1, tail(G["contur_exterior_brat_fata_D"], E[-1])]),
       "contur_interior_brat_fata_D": np.vstack([I1, tail(G["contur_interior_brat_fata_D"], I[-1])])}
out["_kor_spinare_veche"], out["_kor_exterior_vechi"], out["_kor_interior_vechi"] = S, E, I
out["_kor_spinare_noua"], out["_kor_exterior_nou"], out["_kor_interior_nou"] = S, E1, I1
out["_latime_s"], out["_latime_w"] = st, K["_latime_w"]
if "_ref_nacela_varf" in K.files: out["_ref_nacela_varf"] = K["_ref_nacela_varf"]
rest = (ang - dl)[st < s36]
print("BANDA unghi dupa referinta: rotita cu %.1f..%.1f grd; ramas fata de referinta (pana la _36) max %.1f grd (langa _36, tinut pe loc); "
      "exteriorul mutat max %.1f, interiorul max %.1f m" % (np.degrees(dl.min()), np.degrees(dl.max()), np.degrees(np.abs(rest).max()),
      np.linalg.norm(E1 - E, axis=1).max(), np.linalg.norm(I1 - I, axis=1).max()))
for k in [k for k in out if not k.startswith("_")]: out[k.replace("_D", "_S")] = out[k] * [-1, 1, 1]
np.savez(OUT, **out)
