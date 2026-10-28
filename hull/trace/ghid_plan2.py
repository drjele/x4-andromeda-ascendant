# Flat guide line of the body 169_C, by the outline rules (memory feedback_outline_lines): the outline comes from the
# reference negative (seen from above, raster 1 m), gaps between pieces closed (a notch is not shape); ONE half taken
# (the cleaner side, by its small-scale roughness) and mirrored - never averaged; the half from the nose tip down the
# outside, round the loop, up the inside to the U, fitted by one smoothing spline (pieces of ellipse, no tremor) with
# mirrored run-on past both ends so the mirrored line crosses the middle as one curve. Several tolerances; for each:
# distance to that side's outline (mean / 95 % / max), smallest radius, largest turn per 2 m.
# Usage: python ghid_plan2.py <esantion_punte.npz> <out_prefix> [tol ...]   -> <out_prefix>_t<tol>.npz + .png
import sys, os, numpy as np, cv2
from scipy.interpolate import splprep, splev
from scipy.spatial import cKDTree
D = np.load(sys.argv[1]); PRE = sys.argv[2]; TOL = [float(v) for v in sys.argv[3:]] or [0.5, 1.0, 2.0]
CL = float(os.environ.get("GHID_INCHIDERE", "40"))
P = D["ps"][:, :2]; rows = np.round(P[:, 1] / 10).astype(int); cs = []
for r in np.unique(rows):
    q = P[rows == r]; q = q[np.abs(q[:, 0]) < 200]
    if len(q) > 20 and q[:, 1].mean() > -400: cs.append((q[:, 0].min() + q[:, 0].max()) / 2)
cen = float(np.median(cs)); P = P - [cen, 0]
PX = 1.0; XM, Y0, Y1 = np.abs(P[:, 0]).max() + 30, P[:, 1].min() - 30, P[:, 1].max() + 30
W, H = int(2 * XM / PX), int((Y1 - Y0) / PX)
m = np.zeros((H, W), np.uint8); m[((P[:, 1] - Y0) / PX).astype(int), ((P[:, 0] + XM) / PX).astype(int)] = 1
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(CL) | 1,) * 2))
cnt = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0].astype(float)
C = np.stack([cnt[:, 0] * PX - XM, cnt[:, 1] * PX + Y0], 1)
def half(sg):                                                          # the run from the nose tip to the U, on side sg (+1 / -1)
    it = int(np.argmax(C[:, 1] - 1e3 * np.abs(C[:, 0])))               # nose tip
    near = np.nonzero((np.abs(C[:, 0]) < 1.5) & (C[:, 1] < C[it, 1] - 50))[0]; iu = near[np.argmax(C[near, 1])]   # top of the U
    n = len(C); a = [(it + k) % n for k in range(n)]; b = a[:a.index(iu) + 1]
    R = C[b] if np.mean(C[b, 0]) * sg > 0 else C[[(it - k) % n for k in range(n)][:[(it - k) % n for k in range(n)].index(iu) + 1]]
    R = R * [sg, 1]                                                    # as the right side
    return R[R[:, 0] >= 0] if R[0, 0] >= 0 else R
def rough(R):                                                          # small-scale roughness: distance to its own 6 m smoothing
    k = np.exp(-0.5 * (np.arange(-18, 19) / 6.0) ** 2); k /= k.sum(); Z = np.stack([np.convolve(np.pad(R[:, i], 18, mode="edge"), k, "valid") for i in range(2)], 1)
    return float(np.mean(np.linalg.norm(R - Z, axis=1)))
HR, HL = half(1), half(-1); side = "dreapta" if rough(HR) <= rough(HL) else "stanga"; Hh = HR if side == "dreapta" else HL
print("JUMATATE aleasa: %s (asperitate dreapta %.2f m, stanga %.2f m), %d puncte" % (side, rough(HR), rough(HL), len(Hh)))
def resample(Q, step, closed=False):
    Qc = np.vstack([Q, Q[:1]]) if closed else Q; s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Qc, axis=0), axis=1))]; n = max(int(s[-1] / step), 2)
    u = np.linspace(0, s[-1], n, endpoint=not closed); return np.stack([np.interp(u, s, Qc[:, i]) for i in range(2)], 1)
Hh = resample(Hh, 1.0); RUN = 40
ext = np.vstack([Hh[1:RUN][::-1] * [-1, 1], Hh, Hh[-RUN:-1][::-1] * [-1, 1]])   # mirrored run-on at both ends
for tol in TOL:
    tck, _ = splprep(ext.T, s=len(ext) * tol ** 2, k=3); F = np.array(splev(np.linspace(0, 1, len(ext) * 4), tck)).T
    i0 = np.nonzero(np.diff(np.sign(F[:, 0])))[0]; F = F[i0[0] + 1:i0[-1] + 1]; F = np.vstack([[0, F[0, 1]], F, [0, F[-1, 1]]])
    full = np.vstack([F, F[::-1][1:-1] * [-1, 1]])                     # right half, then the mirror back: one closed line
    d = cKDTree(resample(full, 0.25, True)).query(Hh)[0]
    Qr = resample(full, 2.0, True); t = np.diff(np.vstack([Qr, Qr[:1]]), axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
    turn = np.degrees(np.arccos(np.clip(np.sum(t * np.roll(t, 1, 0), 1), -1, 1))); rad = 2.0 / np.maximum(np.radians(turn), 1e-9)
    np.savez("%s_t%g.npz" % (PRE, tol), contur=full, centru=cen, jumatate=Hh)
    print("VARIANTA toleranta %.1f m: abatere fata de referinta medie %.2f / 95%% %.2f / max %.2f m; raza minima %.1f m; intoarcere max %.1f grade la 2 m; la mijloc (nas, U) unghi %.1f / %.1f grade" % (
        tol, d.mean(), np.percentile(d, 95), d.max(), rad.min(), turn.max(), np.degrees(np.arctan2(*(F[2] - F[0])[::-1])), np.degrees(np.arctan2(*(F[-3] - F[-1])[::-1]))))
    sc = 0.5; im = np.full((int((Y1 - Y0) * sc) + 20, int(2 * XM * sc) + 20, 3), 255, np.uint8)
    f = lambda Q: np.stack([(Q[:, 0] + XM) * sc + 10, (Y1 - Q[:, 1]) * sc + 10], 1).astype(np.int32)
    im[((Y1 - P[::7, 1]) * sc + 10).astype(int), ((P[::7, 0] + XM) * sc + 10).astype(int)] = (190, 190, 190)
    cv2.polylines(im, [f(C)], True, (0, 0, 220), 1); cv2.polylines(im, [f(full)], True, (0, 0, 0), 1)
    cv2.imwrite("%s_t%g.png" % (PRE, tol), im)
