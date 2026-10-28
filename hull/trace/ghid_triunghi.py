# Outer guide of PS as the reference reads from above with all its pieces (asked: a slightly rounded triangle, a rectangle
# behind it, then the arms in a V/U): the nose curve of the flat guide (ghid_plan2.py) to where its curvature ends, then
# its tangent straight to the triangle's back corner on x = XR (the rectangle's side), the side straight (parallel) down
# to Y2, then the arm's straight line at the arm's direction (ARM deg) down to YE; each corner rounded by one arc.
# Mirrored: one open flat line. Usage: python ghid_triunghi.py <ghid_plan.npz> <ghid_drept.npz> <out.npz> [png] [ref pts]
import sys, os, numpy as np, cv2
G = np.load(sys.argv[1]); GD = np.load(sys.argv[2]); OUT = sys.argv[3]; PNG = sys.argv[4] if len(sys.argv) > 4 else None
env = lambda k, d: float(os.environ.get(k, d))
XR, Y2, YE, ARM, R1, R2, KMIN = env("TRI_X", "205"), env("TRI_Y2", "-280"), env("TRI_YE", "-491"), env("TRI_BRAT", "-82"), env("TRI_R1", "80"), env("TRI_R2", "120"), 0.0012
g = G["contur"]; n = len(g); R = g[:n // 2 + 1]
if R[5, 0] < 0: R = np.vstack([g[:1], g[::-1][:n // 2]])
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(R, axis=0), axis=1))]; t = np.gradient(R, axis=0); a = np.unwrap(np.arctan2(t[:, 1], t[:, 0])); k = np.gradient(a) / np.gradient(s)
ie = int(np.nonzero((s > 60) & (np.abs(k) < KMIN))[0][0]); nose = R[:ie + 1]; pe = R[ie]; te = t[ie] / np.linalg.norm(t[ie])
C1 = pe + te * (XR - pe[0]) / te[0]; C2 = np.array([XR, Y2]); da = np.array([np.cos(np.radians(ARM)), np.sin(np.radians(ARM))])
E = C2 + da * (YE - Y2) / da[1]
def fillet(P0, C, P1, r):
    u1, u2 = (P0 - C) / np.linalg.norm(P0 - C), (P1 - C) / np.linalg.norm(P1 - C); ang = np.arccos(np.clip(u1 @ u2, -1, 1))
    dt = r / np.tan(ang / 2); t1, t2 = C + u1 * dt, C + u2 * dt; cc = C + (u1 + u2) / np.linalg.norm(u1 + u2) * r / np.sin(ang / 2)
    q1, q2 = np.arctan2(*(t1 - cc)[::-1]), np.arctan2(*(t2 - cc)[::-1])
    if q2 - q1 > np.pi: q2 -= 2 * np.pi
    if q1 - q2 > np.pi: q2 += 2 * np.pi
    return np.array([cc + r * np.array([np.cos(q), np.sin(q)]) for q in np.linspace(q1, q2, 30)])
seg = lambda p, q: p + np.outer(np.linspace(0, 1, max(int(np.linalg.norm(q - p)), 2))[1:], q - p)
f1, f2 = fillet(pe, C1, C2, R1), fillet(C1, C2, E, R2)
H = np.vstack([nose, seg(pe, f1[0]), f1, seg(f1[-1], f2[0]), f2, seg(f2[-1], E)])
full = np.vstack([H[::-1][:-1] * [-1, 1], H]); np.savez(OUT, B=full, B_int=GD["B_int"], centru=G["centru"])
print("TRIUNGHI: nas curb pana la (%.0f, %.0f), latura dreapta pana la coltul (%.0f, %.0f) [arc R %.0f]; dreptunghi x %.0f pana la y %.0f [arc R %.0f]; brat %.0f grade pana la (%.0f, %.0f)" % (*pe, *C1, R1, XR, Y2, R2, ARM, *E))
if PNG:
    Z = np.load(sys.argv[5]); P = Z["P"].copy(); P[:, 0] -= float(G["centru"]); lab = Z["lab"]
    XM, Y0, Y1, sc = 330.0, -620.0, 500.0, 1.0; W, Hh = int(2 * XM * sc) + 20, int((Y1 - Y0) * sc) + 20; im = np.full((Hh, W, 3), 255, np.uint8)
    f = lambda x, y: (((x + XM) * sc + 10).astype(int), ((Y1 - y) * sc + 10).astype(int))
    cols = np.random.default_rng(3).random((lab.max() + 1, 3)) * 150 + 70
    xs, ys = f(P[:, 0], P[:, 1]); ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < Hh); im[ys[ok], xs[ok]] = cols[lab[ok]].astype(np.uint8)
    for Q, c in ((GD["B"], (160, 160, 160)), (full, (0, 0, 230)), (GD["B_int"], (200, 90, 0))):
        x_, y_ = f(Q[:, 0], Q[:, 1]); cv2.polylines(im, [np.stack([x_, y_], 1).astype(np.int32)], False, c, 2)
    cv2.imwrite(PNG, im)
