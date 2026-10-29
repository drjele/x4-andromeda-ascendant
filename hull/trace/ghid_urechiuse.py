# Guides for the little ears between the keel and the rim (asked: a few little ears between gp_PS_carena and gp_PS_rama,
# at 45 deg to the keel's axis, starting from the line across the keel through the tip of its small base, 2 a side). Each
# ear a strip WE m wide at ANG deg to the axis, going out and back (DIR=-1) or out and forward (DIR=1), its front edge
# starting where the line y = (floor tip - k*S) meets the keel's big side; clipped between the keel's big side (IN m into
# it) and the rim's inner outline (OUT m into it); flat at z ZT (top on the body), TH m thick. Right side, left = mirror.
# Usage: python ghid_urechiuse.py <carena npz (_asamblat)> <rama npz> <out.npz> ; env WE=10 S=30 N=2 ANG=45 DIR=-1 Y_FATA=0 IN=2 OUT=1 TH=4 DZ=0
import sys, os, numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
C = np.load(sys.argv[1]); R = np.load(sys.argv[2]); OUT_ = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d))
WE, S, N, ANG, DIR, IN, OUT, TH, DZ = e("WE", "10"), e("S", "30"), int(e("N", "2")), np.radians(e("ANG", "45")), e("DIR", "-1"), e("IN", "2"), e("OUT", "1"), e("TH", "4"), e("DZ", "0")
K = C["contur_carena_sus"]; ZT = float(K[0, 2]); y0 = float(C["contur_carena_jos"][:, 1].max()); RI = R["contur_rama_interior"]
PX = 0.25; X0, Y0 = -200.0, -80.0; W_, H_ = int(400 / PX), int(600 / PX)
px = lambda q: np.c_[(q[:, 0] - X0) / PX, (q[:, 1] - Y0) / PX].astype(np.int32)
def mask(P): m = np.zeros((H_, W_), np.uint8); cv2.fillPoly(m, [px(P[:, :2])], 1); return m
def grow(m, r): r = int(abs(r) / PX); k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)); return cv2.dilate(m, k) if r else m
def shrink(m, r): r = int(abs(r) / PX); k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)); return cv2.erode(m, k) if r else m
Mk = mask(K); Mr = mask(RI); ring = (grow(Mr, OUT).astype(bool)) & ~(shrink(Mk, IN).astype(bool))       # between keel and rim (+ overlaps)
jj, ii = np.mgrid[0:H_, 0:W_]; X = ii * PX + X0; Y = jj * PX + Y0
def xk(y):                                              # the keel's big side, right half-width at y
    q = np.vstack([K, K[:1]])[:, :2]; xs = [a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) for a, b in zip(q[:-1], q[1:]) if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]]
    xs = [x for x in xs if x > 0]; return max(xs)
d = np.array([np.sin(ANG), DIR * np.cos(ANG)]); nrm = np.array([-d[1], d[0]])                  # along the ear, across it
if nrm[1] > 0: nrm = -nrm                                                                       # across = towards the back
out = {}
for k in range(N):
    ys = y0 + e("Y_FATA", "0") - k * S; A = np.array([xk(ys), ys])                 # (Y_FATA: the first moved towards the tip)
    u = (X - A[0]) * d[0] + (Y - A[1]) * d[1]; v = (X - A[0]) * nrm[0] + (Y - A[1]) * nrm[1]
    m = ring & (v >= 0) & (v <= WE) & (u > -40) & (X > 0)
    n_, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8)); m = lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
    c = np.c_[c[:, 0] * PX + X0, c[:, 1] * PX + Y0]; c = np.c_[gaussian_filter1d(c[:, 0], 1.0 / PX, mode="wrap"), gaussian_filter1d(c[:, 1], 1.0 / PX, mode="wrap")]
    c = np.vstack([c, c[:1]]); L = np.linalg.norm(np.diff(c, axis=0), axis=1).sum()
    for sd, sg in (("D", 1), ("S", -1)):
        out["contur_urechiusa_%d_%s" % (k + 1, sd)] = np.c_[c[:, 0] * sg, c[:, 1], np.full(len(c), ZT)]
        mid = c.mean(0); a1 = mid - d * 30; a2 = mid + d * 30                                   # a section across the ear (its thickness)
        out["sectiune_urechiusa_%d_%s" % (k + 1, sd)] = np.array([[mid[0] * sg, mid[1], ZT], [mid[0] * sg, mid[1], ZT - TH]]) * 1.0
    print("URECHIUSA %d: incepe la y %.1f pe carena (x %.1f), %.0f grd fata de axa, latime %.0f m; x %.0f..%.0f y %.0f..%.0f, arie %.0f m2" % (
        k + 1, ys, A[0], np.degrees(ANG), WE, c[:, 0].min(), c[:, 0].max(), c[:, 1].min(), c[:, 1].max(), m.sum() * PX * PX))
out["z_urechiuse"] = np.array([[ZT, ZT - TH, 0.0]])
for kk in out: out[kk] = out[kk] + [0, 0, DZ] if kk != "z_urechiuse" else out[kk]
print("linia de start: y %.1f (varful bazei mici a carenei); grosime %.0f m (z %.0f..%.0f)" % (y0, TH, ZT - TH, ZT))
np.savez(OUT_, **out)
