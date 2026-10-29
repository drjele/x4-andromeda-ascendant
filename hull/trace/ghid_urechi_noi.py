# Guides for the new big ears (asked: first the guides for the new ears - starting from g_psr_sep_ghidaje_sudate's big
# bottom side and following its curve). Right side: the inner edge = the PS's outer bottom outline (z of the base) from
# y Y0 (front) back to its back corner; the outer edge = the same stretch moved W m outwards along its normals (follows the
# curve); the two ends closed straight across (normal to the outline) - one closed line in the base plane. Left = mirror.
# Usage: python ghid_urechi_noi.py <ps guide npz (contur_rama_exterior_pe_PS)> <out.npz> ; env Y0=293 W=45 DZ=0
import sys, os, numpy as np
from scipy.ndimage import gaussian_filter1d
G = np.load(sys.argv[1]); OUT = sys.argv[2]; e = lambda k, d: float(os.environ.get(k, d)); Y0, W, DZ = e("Y0", "293"), e("W", "45"), e("DZ", "0")
E = G["contur_rama_exterior_pe_PS"]; ZB = float(E[:, 2].min())
P = E[:, :2]; P = P[:-1] if np.allclose(P[0], P[-1]) else P
j0 = int(np.argmax(P[:, 1] - 5 * np.abs(P[:, 0]))); P = np.roll(P, -j0, 0)                    # from the tip
a = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
if a > 0: P = np.r_[P[:1], P[1:][::-1]]                                                        # clockwise: tip -> right side -> back
R = P[P[:, 0] > 0]                                                                             # the right half, tip -> back
i_a = int(np.argmin(np.abs(R[:, 1] - Y0) + 1000 * (R[:, 0] < 1)))                              # the front end at y Y0
yb = R[:, 1].min(); i_b = int(np.where(R[:, 1] <= yb + 0.5)[0][0])                             # the back corner (first point at the back)
S_ = R[i_a:i_b + 1]; d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(S_, axis=0), axis=1))]; u = np.arange(0, d[-1], 1.0)
S_ = np.c_[np.interp(u, d, S_[:, 0]), np.interp(u, d, S_[:, 1])]
tg = np.gradient(S_, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]; nout = np.c_[-tg[:, 1], tg[:, 0]]   # clockwise: outward = left
nout = np.c_[gaussian_filter1d(nout[:, 0], 8, mode="nearest"), gaussian_filter1d(nout[:, 1], 8, mode="nearest")]; nout /= np.linalg.norm(nout, axis=1)[:, None]
O_ = S_ + W * nout
def cap(p, q, n=20): return np.linspace(p, q, n)[1:-1]
loop = np.vstack([S_, cap(S_[-1], O_[-1]), O_[::-1], cap(O_[0], S_[0])]); loop = np.vstack([loop, loop[:1]])
out = {"contur_ureche_noua_D": np.c_[loop, np.full(len(loop), ZB)], "contur_ureche_noua_S": np.c_[loop * [-1, 1], np.full(len(loop), ZB)],
       "contur_ureche_noua_interior_D": np.c_[S_, np.full(len(S_), ZB)], "contur_ureche_noua_interior_S": np.c_[S_ * [-1, 1], np.full(len(S_), ZB)]}
for kk in out: out[kk] = out[kk] + [0, 0, DZ]
print("URECHE NOUA (ghidaj): margine interioara = conturul de jos al PS (z %.0f) de la y %.0f pana in coltul din spate (y %.0f), %.0f m; margine exterioara la %.0f m in afara, pe aceeasi curba (x pana la %.0f); capete drepte" % (
    ZB, S_[0, 1], S_[-1, 1], d[-1], W, O_[:, 0].max()))
np.savez(OUT, **out)
