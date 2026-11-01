# The red nacelle's surface from its guides (contur_nacela_capat1 / varf / capat2): a V-shaped sheet, rows across lip -> V point ->
# lip, cut into ribs of equal width along the V point's line; light and dark alternate, a dark rib bulged outwards (half-sine across
# the rib's width and along its V, RELIEF m in its middle, its edges flush with the light ribs). Two meshes (dark / light), both arms.
# Usage: python nacela_piesa.py <guides npz> <out.npz> ; env LATIME=5.25 RELIEF=1.0 DS=0.75 NV=21
import sys, os, numpy as np
G = np.load(sys.argv[1]); OUT = sys.argv[2]; e = lambda k, d: float(os.environ.get(k, d))
LAT, REL, DS, NV = e("LATIME", "5.25"), e("RELIEF", "1.0"), e("DS", "0.75"), int(e("NV", "21"))
A, T, B = (G["contur_nacela_%s_D" % k] for k in ("capat1", "varf", "capat2"))
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
dT = arclen(T); n = len(T)
nr = max(1, int(round(dT[-1] / LAT))); lat = dT[-1] / nr; nper = max(2, int(round(lat / DS)))
sq = np.linspace(0, dT[-1], nr * nper + 1)
at = lambda L: np.c_[[np.interp(sq, dT, L[:, k]) for k in range(3)]].T
A, T, B = at(A), at(T), at(B)
u = np.r_[np.linspace(0, 1, NV)[:-1], np.linspace(1, 2, NV)]                # across: lip -> point (0..1) -> lip (1..2)
P = np.where(u[None, :, None] <= 1, A[:, None] + (T - A)[:, None] * np.minimum(u, 1)[None, :, None],
             T[:, None] + (B - T)[:, None] * np.maximum(u - 1, 0)[None, :, None])
# outwards: from the lips' middle to the V point (zero at the V, where the three meet -> the previous row's direction)
O = T - (A + B) / 2; ln = np.linalg.norm(O, axis=1)
for i in range(len(O) - 2, -1, -1):
    if ln[i] < 1e-6: O[i], ln[i] = O[i + 1], ln[i + 1]
for i in range(len(O)):
    if ln[i] < 1e-6: O[i], ln[i] = O[i - 1], ln[i - 1]
O /= ln[:, None]
out = {}
for dark in (True, False):
    V_, F_ = [], []
    for r in range(nr):
        if (r % 2 == 0) != dark: continue
        rows = np.arange(r * nper, (r + 1) * nper + 1); Q = P[rows].copy()
        if dark and REL > 0:
            w = np.sin(np.linspace(0, np.pi, len(rows)))[:, None] * np.sin(np.pi * u / 2)[None, :]   # 0 on the rib's edges and the lips
            Q = Q + w[..., None] * O[rows][:, None] * REL
        b0 = sum(len(v) for v in V_); V_.append(Q.reshape(-1, 3)); m = len(u)
        for i in range(len(rows) - 1):
            for j in range(m - 1):
                q = [b0 + i * m + j, b0 + i * m + j + 1, b0 + (i + 1) * m + j + 1, b0 + (i + 1) * m + j]; F_ += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
    V_ = np.vstack(V_); F_ = np.array(F_); k = "nacela_%s" % ("inchis" if dark else "deschis")
    out[k + "_D__v"], out[k + "_D__f"] = V_, F_; out[k + "_S__v"], out[k + "_S__f"] = V_ * [-1, 1, 1], F_[:, ::-1]
print("NACELA piesa: %d nervuri de %.2f m (%d inchise bombate %.1f m, %d deschise), %d + %d fete pe parte" % (
    nr, lat, (nr + 1) // 2, REL, nr // 2, len(out["nacela_inchis_D__f"]), len(out["nacela_deschis_D__f"])))
np.savez(OUT, **out)
