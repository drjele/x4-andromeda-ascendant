# The PS's outline from above without its two shoulders (asked: the guide starts at the tip on the current outline, and at the
# first shoulder it does not turn in but goes straight to the second one; the same, built the same way, on R002 169_C - not its
# raw jagged outline). Per piece: its outline (right half, max x per 2 m of y; for the reference a rolling max over 10 m + light
# smoothing, its holes would make spikes), the first shoulder K1 = the last widest point before the outline pulls in (going
# back from the tip), the second K2 = the outer point once the outline has stepped out again at the back; guide = outline from
# the tip to K1, then a straight line to K2, the join eased over BL m. Both sides (mirror about the piece's own axis).
# Usage: python ghid_umar.py <guides_ps.npz> <ref.npz> <out.npz> ; env UM_BL=20 UM_XREF=-4.7 UM_YEND=-48
import sys, os, numpy as np
from scipy.ndimage import maximum_filter1d, gaussian_filter1d
G = np.load(sys.argv[1]); RF = np.load(sys.argv[2]); OUT = sys.argv[3]
BL, XR, YE = float(os.environ.get("UM_BL", "20")), float(os.environ.get("UM_XREF", "-4.7")), float(os.environ.get("UM_YEND", "-48"))
C = G["contur_PS_sus"]; ZT = C[0, 2]; R = C[C[:, 0] >= 0]; R = R[np.argsort(-R[:, 1])]
ys = np.arange(np.floor(R[:, 1].max()), YE, -2.0)
xp = np.interp(-ys, -R[:, 1], R[:, 0])
v = RF["R002 169_C__v"].astype(float); v[:, 0] -= XR; xr = []
for y in ys:
    s = v[(np.abs(v[:, 1] - y) < 1.0) & (v[:, 0] > 0)]; xr.append(s[:, 0].max() if len(s) else np.nan)
xr = np.array(xr); ok = np.isfinite(xr); xr = np.interp(np.arange(len(xr)), np.where(ok)[0], xr[ok]); xr = gaussian_filter1d(maximum_filter1d(xr, 5), 1.5)
def guide(x, nm):
    i1 = next(i for i in range(len(x) - 6) if ys[i] < 400 and x[i + 6] < x[i] - 4)   # going back: pulls in > 4 m over 12 m
    i1 = int(np.argmax(x[: i1 + 1] == x[: i1 + 1].max())) if x[: i1 + 1].max() > x[i1] + 0.5 else i1
    i2 = next(i for i in range(len(x) - 1, i1, -1) if x[i - 3] < x[i] - 8) if any(x[i - 3] < x[i] - 8 for i in range(len(x) - 1, i1 + 3, -1)) else len(x) - 1
    K1, K2 = np.array([x[i1], ys[i1]]), np.array([x[i2], ys[i2]])
    g = x.copy(); seg = (np.arange(len(x)) > i1) & (np.arange(len(x)) <= i2)
    g[seg] = K1[0] + (K2[0] - K1[0]) * (ys[seg] - K1[1]) / (K2[1] - K1[1])
    w = np.exp(-0.5 * ((ys - K1[1]) / (BL / 2)) ** 2); g = (1 - w) * g + w * gaussian_filter1d(g, BL / 4)   # eased join at K1
    keep = np.arange(len(x)) <= i2
    a1 = np.degrees(np.arctan((x[i1] - x[max(i1 - 5, 0)]) / (ys[max(i1 - 5, 0)] - ys[i1]))); a2 = np.degrees(np.arctan((K2[0] - K1[0]) / (K1[1] - K2[1])))
    print("%-5s umar 1 la (x %.1f, y %.0f), umar 2 la (x %.1f, y %.0f); conturul vine la %.1f grd de axa, dreapta pleaca la %.1f grd; mutat max %.1f m (y %.0f)" % (
        nm, K1[0], K1[1], K2[0], K2[1], a1, a2, (g - x)[keep].max(), ys[keep][np.argmax((g - x)[keep])]))
    P = np.c_[g[keep], ys[keep]]; yt = YT[nm]                 # closed at the tip: on the axis at the nose
    return np.vstack([[0.0, yt], P]) if P[0, 1] < yt - 0.5 else P
YT = {"PS": R[:, 1].max(), "R002": v[np.abs(v[:, 0]) < 15, 1].max()}
out = {}
for nm, x in (("PS", xp), ("R002", xr)):
    P = guide(x, nm); out["contur_umar_%s_D" % nm] = np.c_[P, np.full(len(P), ZT)]; out["contur_umar_%s_S" % nm] = np.c_[-P[:, 0], P[:, 1], np.full(len(P), ZT)]
np.savez(OUT, **out)
