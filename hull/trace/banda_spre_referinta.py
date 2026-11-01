# The band turned towards the reference (asked: _49 and _36 stay; between them the band comes closer to the reference, so that the
# nacelle's V point - which lies on the band's line - follows lucru_nacela_rosie's, more uniform): the reference nacelle turned with
# the head (ref_rot npz "nacela"); per spine station its V point = its point farthest from the spine in the section, smoothed; the band
# line's angle about the spine (in the section) that passes through it, smoothed, 0 at the head (_49) and from _36 on (eased over
# RAMPA m), and over the lips' V up to _36 eased to 0. Exterior and interior turned with it about the spine. Writes the station
# arrays old -> new (_kor_*, for mapeaza_trei.py), the width (_latime_*) and the reference V points (_ref_nacela_varf).
# Usage: python banda_spre_referinta.py <guides npz> <trei_linii current> <ref_rot npz> <out> ; env NETEZ=15 RAMPA=80 SECT_FIX=36
import sys, os, numpy as np
from scipy.ndimage import gaussian_filter1d
G = np.load(sys.argv[1]); K = np.load(sys.argv[2]); RN = np.load(sys.argv[3])["nacela"]; OUT = sys.argv[4]; e = lambda k, d: float(os.environ.get(k, d))
sm = lambda w: w * w * (3 - 2 * w)
S, E, I, st, W = K["_kor_spinare_noua"], K["_kor_exterior_nou"], K["_kor_interior_nou"], K["_latime_s"], K["_latime_w"]
T = np.gradient(S, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
BZ = G["buze_gura_brat_fata_D"]; iv = int(np.argmax([np.linalg.norm(BZ[i] - BZ[0]) + np.linalg.norm(BZ[i] - BZ[-1]) for i in range(len(BZ))])); VX = BZ[iv]
sV = st[int(np.argmin(np.abs(np.einsum("ij,ij->i", VX - S, T)) + 1e-3 * np.linalg.norm(S - VX, axis=1)))]
s36 = st[int(np.argmin(np.linalg.norm(S - G["sectiune_brat_fata_D_%02d" % int(e("SECT_FIX", "36"))].mean(0), axis=1)))]
REF = np.full((len(st), 3), np.nan); dl = np.zeros(len(st)); has = np.zeros(len(st), bool)
for j in range(len(st)):
    if st[j] >= sV: continue
    q = RN - S[j]; m = np.abs(q @ T[j]) < 1.0
    if m.sum() < 5: continue
    Q = q[m]; Q = Q - np.outer(Q @ T[j], T[j]); k = int(np.argmax(np.linalg.norm(Q, axis=1))); REF[j] = S[j] + Q[k]
    u = I[j] - S[j]; u /= np.linalg.norm(u); v = np.cross(T[j], u); r = Q[k] / np.linalg.norm(Q[k]); dl[j] = np.arctan2(r @ v, r @ u); has[j] = True
dl = np.where(has, dl, np.interp(st, st[has], dl[has])); dl = gaussian_filter1d(dl, e("NETEZ", "15"), mode="nearest")
RP = e("RAMPA", "80"); w = sm(np.clip(st / RP, 0, 1)) * sm(np.clip((s36 - st) / max(s36 - sV, 1), 0, 1)) ** 0 * (st < s36)
w = w * np.where(st > sV, sm(np.clip((s36 - st) / max(s36 - sV, 1), 0, 1)), 1.0)
dl = dl * w
def rot(P, j, a):                                                          # P turned about the spine point S[j], axis T[j], by a
    v = P - S[j]; c, s_ = np.cos(a), np.sin(a); return S[j] + v * c + np.cross(T[j], v) * s_ + T[j] * (v @ T[j]) * (1 - c)
E1 = np.array([rot(E[j], j, dl[j]) for j in range(len(st))]); I1 = np.array([rot(I[j], j, dl[j]) for j in range(len(st))])
out = {k: G[k] for k in ("spinare_brat_fata_D",)}
def tail(L, q):
    j = int(np.argmin(np.linalg.norm(L - q, axis=1))); return L[j + 1:]
out["spinare_brat_fata_D"] = np.vstack([S, tail(G["spinare_brat_fata_D"], S[-1])])
out["contur_exterior_brat_fata_D"] = np.vstack([E1, tail(G["contur_exterior_brat_fata_D"], E[-1])])
out["contur_interior_brat_fata_D"] = np.vstack([I1, tail(G["contur_interior_brat_fata_D"], I[-1])])
out["_kor_spinare_veche"], out["_kor_exterior_vechi"], out["_kor_interior_vechi"] = S, E, I
out["_kor_spinare_noua"], out["_kor_exterior_nou"], out["_kor_interior_nou"] = S, E1, I1
out["_latime_s"], out["_latime_w"], out["_ref_nacela_varf"] = st, W, REF
print("BANDA spre referinta: unghiul benzii in jurul spinarii max %.2f grd (la s %.0f), 0 la cap si de la _36 (s %.0f); exteriorul mutat max %.1f, "
      "interiorul max %.1f m" % (np.degrees(np.abs(dl).max()), st[np.argmax(np.abs(dl))], s36, np.linalg.norm(E1 - E, axis=1).max(), np.linalg.norm(I1 - I, axis=1).max()))
for k in [k for k in out if not k.startswith("_")]: out[k.replace("_D", "_S")] = out[k] * [-1, 1, 1]
np.savez(OUT, **out)
