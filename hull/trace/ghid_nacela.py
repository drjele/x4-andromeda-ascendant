# Guides for the red nacelle on the new mouth (asked: from buze_gura, ribs alternating light and dark red, the dark ones bulged
# slightly outwards). The nacelle = a V-shaped band in the mouth: its two ends on the two lips, its point (the V's fold) out of the
# mouth along the band (away from the spine), as deep - relative to the mouth - as the old nacelle's (old rails, regen/ghidaje.json),
# going to 0 at the lips' V where the three rails meet. Ribs of equal width all along; light and dark alternate; a dark rib's V is
# pushed out by RELIEF m in its middle (ends kept on the lips). Right arm (mirror of the old rails, which are the left one).
# Usage: python ghid_nacela.py <arm guides npz (_D)> <old rails json> <out.npz> ; env LATIME=5.24 RELIEF=1.0
import sys, os, json, numpy as np
from scipy.ndimage import gaussian_filter1d
G = np.load(sys.argv[1]); RJ = json.load(open(sys.argv[2])); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d))
B, SP, INn = G["buze_gura_brat_fata_D"], G["spinare_brat_fata_D"], G["contur_interior_brat_fata_D"]
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
def bez(c, t): c = np.array(c); t = np.atleast_1d(t)[:, None]; return (1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3]
def resample(L, n): d_ = arclen(L); return np.c_[[np.interp(np.linspace(0, d_[-1], n), d_, L[:, k]) for k in range(3)]].T
# the lips: lower (PS corner -> V) and upper (PS corner -> V)
iv = int(np.argmax([np.linalg.norm(B[i] - B[0]) + np.linalg.norm(B[i] - B[-1]) for i in range(len(B))])); V = B[iv]
L1, L2 = B[:iv + 1], B[iv:][::-1]; N = 400; L1, L2 = resample(L1, N), resample(L2, N); MID = (L1 + L2) / 2
# the old nacelle's depth: old rails (left arm) mirrored; per old mid point (between its two end rails) the distance of its V-point
# rail, as a fraction of the old mouth's opening there, against the fraction of the way to the V
old = [bez(r["control"], np.linspace(0, 1, 300)) * [-1, 1, 1] for r in RJ["rails"]]   # capat1, varf, capat2
oM = (old[0] + old[2]) / 2; oW = np.linalg.norm(old[0] - old[2], axis=1); oD = np.linalg.norm(old[1] - oM, axis=1)
oapex = np.array(RJ["apex"]) * [-1, 1, 1]; ofr = 1 - np.linalg.norm(oM - oapex, axis=1) / np.linalg.norm(oM - oapex, axis=1).max()   # 0 far, 1 at the V
rel = oD / np.maximum(oW, 1e-6); o_ = np.argsort(ofr); RELF = np.interp(np.linspace(0, 1, N), ofr[o_], rel[o_])
# direction out of the mouth: from the spine to the lips' middle, in the section, smoothed
SPr = SP[np.argmin(np.linalg.norm(SP[None] - MID[:, None], axis=2), axis=1)]; U = MID - SPr; U /= np.linalg.norm(U, axis=1)[:, None]
U = np.c_[[gaussian_filter1d(U[:, k], 10, mode="nearest") for k in range(3)]].T; U /= np.linalg.norm(U, axis=1)[:, None]
fr = arclen(MID) / arclen(MID)[-1]; W = np.linalg.norm(L1 - L2, axis=1)
DEP = gaussian_filter1d(np.interp(fr, np.linspace(0, 1, N), RELF) * W, 6, mode="nearest"); DEP[-1] = 0
TIP = MID + U * DEP[:, None]; TIP[-1] = V
out = {"contur_nacela_capat1_D": L1, "contur_nacela_varf_D": TIP, "contur_nacela_capat2_D": L2}
# ribs: equal width along the V-point rail, alternating; each rib = its V (lower lip -> point -> upper lip) at its middle
LAT, REL = e("LATIME", "5.24"), e("RELIEF", "1.0"); dT = arclen(TIP); nr = int(dT[-1] // LAT); edges = np.linspace(0, dT[-1], nr + 1)
k_ = 0
for i in range(nr):
    m_ = (edges[i] + edges[i + 1]) / 2; j = int(np.argmin(np.abs(dT - m_)))
    a_, p_, b_ = L1[j], TIP[j], L2[j]; seg = np.vstack([np.linspace(a_, p_, 30)[:-1], np.linspace(p_, b_, 30)])
    dark = i % 2 == 0
    if dark and REL > 0:                                                  # the dark rib bulged out (middle by REL m, ends on the lips)
        w_ = np.sin(np.linspace(0, np.pi, len(seg))); seg = seg + np.outer(w_, U[j]) * REL
    out["nacela_nervura_%s_%03d_D" % ("inchisa" if dark else "deschisa", i)] = seg; k_ += 1
for kk in list(out): out[kk.replace("_D", "_S")] = out[kk] * [-1, 1, 1]
print("NACELA ghidaje: 3 linii (capete pe buze, varful V-ului afara din gura pana la %.0f m, toate in V-ul buzelor), %d nervuri de %.2f m alternand (inchise bombate %.1f m)" % (
    DEP.max(), nr, dT[-1] / nr, REL))
np.savez(OUT, **out)
