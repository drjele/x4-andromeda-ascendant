# The keel back to its own triangular shape and its ears at their original angle (asked: the keel was triangular, about the
# shape of sep_PS - the shield broke it; the ears are no longer at their original angle). From the keel's old big side (its
# plan where the heightmap Zk exists): the 2 ears = the shelf beyond the keel's straight slanted side (outline at y YA ->
# the notch in front of the ear); the keel's big
# side = the old one without the ears (straight back, rounded tip kept), the floor = the same shape x SC (same back-to-tip
# axis, floor box as before); each ear in its own shape, its outer edge pushed out (normal to it) until it reaches the rim's
# inner outline (+1 m), its inner end kept in the keel. Left = mirror of the right. Replaces carena_* / ureche_* in <in.npz>.
# Usage: python carena_triunghi.py <fund_harta.npz> <fund_contururi in.npz> <out.npz> ; env YA=215 EY1=295 SC=0.6
import sys, os, numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
H = np.load(sys.argv[1]); C = dict(np.load(sys.argv[2])); OUT = sys.argv[3]; e = lambda k, d: float(os.environ.get(k, d))
EY1, SC = e("EY1", "295"), e("SC", "0.6")
xs, ys, Zk = H["xs"], H["ys"], H["Zk"]; PX = 0.25; X0, Y0 = -200.0, -80.0; W_, H_ = int(400 / PX), int(580 / PX)
def to_px(p): return np.c_[(p[:, 0] - X0) / PX, (p[:, 1] - Y0) / PX].astype(np.int32)
def from_px(c): return np.c_[c[:, 0] * PX + X0, c[:, 1] * PX + Y0]
def mask_poly(p): m = np.zeros((H_, W_), np.uint8); cv2.fillPoly(m, [to_px(p)], 1); return m.astype(bool)
def contour(m, sm=2.0, n=400):
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = from_px(max(cs, key=cv2.contourArea)[:, 0, :].astype(float))
    c = np.c_[gaussian_filter1d(c[:, 0], sm / PX, mode="wrap"), gaussian_filter1d(c[:, 1], sm / PX, mode="wrap")]; cc = np.vstack([c, c[:1]])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cc, axis=0), axis=1))]; u = np.linspace(0, d[-1], n, endpoint=False)
    p = np.c_[np.interp(u, d, cc[:, 0]), np.interp(u, d, cc[:, 1])]; p = np.roll(p, -np.argmax(p[:, 1]), 0)
    a = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]); return p if a > 0 else np.r_[p[:1], p[1:][::-1]]
gx, gy = np.meshgrid(xs, ys); P = np.c_[gx[~np.isnan(Zk)], gy[~np.isnan(Zk)]]; M = np.zeros((H_, W_), np.uint8); st = int(np.ceil((xs[1] - xs[0]) / PX))
for q in to_px(P): cv2.rectangle(M, tuple(q - st // 2 - 1), tuple(q + st // 2 + 1), 1, -1)
M = cv2.morphologyEx(M, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(bool); M = M | np.flip(M, 1)
yy = (np.arange(H_) * PX + Y0)[:, None] * np.ones((1, W_)); xx = (np.arange(W_) * PX + X0)[None, :] * np.ones((H_, 1))
YA = e("YA", "215")                                  # the keel's slanted side: from y YA on its outline to the notch in front of
def xr_m(m, y):                                        # the ear (min x of the outline in EY1-25..EY1) - the ear = what is beyond it
    j = int(round((y - Y0) / PX)); c = np.where(m[j] & (xx[j] > 0))[0]; return xx[j, c.max()] if len(c) else np.nan
A = np.array([xr_m(M, YA), YA]); cand = [(xr_m(M, y), y) for y in np.arange(EY1 - 25, EY1, PX)]; B = np.array(min(cand))
side = (xx - A[0]) * (B[1] - A[1]) - (yy - A[1]) * (B[0] - A[0])                # > 0 = outside the line A-B (right side)
ear = M & (xx > 0) & (yy >= A[1]) & (yy <= B[1] + 6) & (side > 0)
ear = cv2.morphologyEx(ear.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))).astype(bool)
n_, lab, sts, _ = cv2.connectedComponentsWithStats(ear.astype(np.uint8)); ear = lab == 1 + np.argmax(sts[1:, cv2.CC_STAT_AREA])
top = M & ~(ear | np.flip(ear, 1)); sus = contour(top, 2.0, 240)
y0, y1 = sus[:, 1].min(), sus[:, 1].max(); jos = np.c_[sus[:, 0] * SC, y1 - (y1 - sus[:, 1]) * SC - (1 - SC) * (y1 - y0) / 2]   # x SC, centred on the old floor
rows = [j for j in range(H_) if ear[j].any()]; oe = np.array([(xx[j, np.where(ear[j])[0].max()], yy[j, 0]) for j in rows])
k_ = np.polyfit(oe[:, 1], oe[:, 0], 1)[0]; d = np.array([1.0, -k_]) / np.hypot(1, k_)                  # normal of the outer edge, outwards
ang = np.degrees(np.arctan(k_)); Ri = mask_poly(C["rama_interior"]); ext = ear.copy(); sh = ear.copy(); tt = 0.0
while tt < 80:
    tt += 0.5; dx, dy = d * tt / PX; Mt = np.float32([[1, 0, dx], [0, 1, dy]]); sh = cv2.warpAffine(ear.astype(np.uint8), Mt, (W_, H_)).astype(bool); ext |= sh
    if (sh & ~Ri).any(): break
dx, dy = d * (tt + 1) / PX; ext |= cv2.warpAffine(ear.astype(np.uint8), np.float32([[1, 0, dx], [0, 1, dy]]), (W_, H_)).astype(bool)
ur = contour(ext, 1.0, 160)
C.update(carena_sus=sus, carena_jos=jos, ureche_D=ur, ureche_S=np.r_[ur[:1], ur[1:][::-1]] * [-1, 1])
qe = from_px(np.argwhere(ear)[:, ::-1].astype(float))
print("CARENA SUS (fara urechi): x %.0f..%.0f, y %.0f..%.0f; JOS x%.1f: x %.0f..%.0f, y %.0f..%.0f" % (sus[:, 0].min(), sus[:, 0].max(), y0, y1, SC, jos[:, 0].min(), jos[:, 0].max(), jos[:, 1].min(), jos[:, 1].max()))
print("LATURA CARENEI: A (%.1f, %.0f) -> B (%.1f, %.0f)" % (A[0], A[1], B[0], B[1]))
print("URECHE originala: x %.0f..%.0f, y %.0f..%.0f, arie %.0f m2, marginea exterioara la %.0f grd fata de axa navei; impinsa %.1f m perpendicular pe ea pana la rama -> x %.0f..%.0f, y %.0f..%.0f" % (
    qe[:, 0].min(), qe[:, 0].max(), qe[:, 1].min(), qe[:, 1].max(), ear.sum() * PX * PX, ang, tt + 1, ur[:, 0].min(), ur[:, 0].max(), ur[:, 1].min(), ur[:, 1].max()))
np.savez(OUT, **C)
