# Guide lines on the REFERENCE body 169_C (asked: straight sides, at most one curve where two of them meet): its outline
# seen from above (raster of the sampled shell, small gaps closed), read per row: the outer edge (farthest from the middle)
# and, behind the arms' meeting point, the arms' inner edge (the gap's side). Both sides pooled (|x|: symmetric). Each edge
# fitted by the best polyline with NS straight segments (least squares, dynamic programming over the breakpoints), then
# every corner rounded by one circle arc whose radius fits the reference outline there. The outer line: from the arm's end
# up one side, round the tip, down the other; the inner line: down one arm, round the U between the arms, down the other.
# Usage: python ghid_ref_contur.py <esantion_punte.npz> <out.npz> [y_end]
import sys, os, numpy as np, cv2
D = np.load(sys.argv[1]); OUT = sys.argv[2]; YE = float(sys.argv[3]) if len(sys.argv) > 3 else -450.0
NSE, NSI, PX = int(os.environ.get("GHID_SEG_EXT", "3")), int(os.environ.get("GHID_SEG_INT", "1")), 1.0
XMAXE, YU = float(os.environ.get("GHID_XMAX", "260")), float(os.environ.get("GHID_Y_U", "-30"))
P = D["ps"]; P = P[P[:, 1] > YE - 5]; X = np.abs(P[:, 0])
x0, y0 = 0.0, YE - 5; W, H = int(X.max() / PX) + 10, int((P[:, 1].max() - y0) / PX) + 10
m = np.zeros((H, W), np.uint8); m[((P[:, 1] - y0) / PX).astype(int), (X / PX).astype(int)] = 1
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
ext, inn = [], []
for r in range(H):
    xs = np.nonzero(m[r])[0]
    if len(xs) < 3: continue
    y = y0 + r * PX; xe = xs[xs * PX < XMAXE]                             # leave out the loops' outer branches (far out)
    if len(xe) and y > YE: ext.append((xe.max() * PX, y))
    if xs.min() * PX > 4 and y < YU: inn.append((xs.min() * PX, y))     # the arms' gap only behind the U (the deck has a hole)
ext, inn = np.array(ext), np.array(inn)
def polyfit(Q, ns):                                                    # best ns-segment polyline (indices of the corners)
    n = len(Q); E = np.full((n, n), np.inf)
    for i in range(n):
        d = Q[i + 1:] - Q[i]; L = np.linalg.norm(d, axis=1)
        for jj, j in enumerate(range(i + 1, n)):
            w = Q[i + 1:j] - Q[i]; E[i, j] = float(np.sum((w[:, 0] * d[jj, 1] - w[:, 1] * d[jj, 0]) ** 2) / max(L[jj], 1e-9) ** 2)
    best = np.full((ns + 1, n), np.inf); arg = np.zeros((ns + 1, n), int); best[0, 0] = 0
    for s in range(1, ns + 1):
        for j in range(1, n):
            c = best[s - 1, :j] + E[:j, j]; i = int(np.argmin(c)); best[s, j], arg[s, j] = c[i], i
    idx = [n - 1]
    for s in range(ns, 0, -1): idx.append(arg[s, idx[-1]])
    return idx[::-1]
def lines_from(Q, idx):                                                # least-squares straight line through each segment's points
    out = []
    for a, b in zip(idx[:-1], idx[1:]):
        S = Q[a:b + 1]; c = S.mean(0); u = np.linalg.svd(S - c)[2][0]; out.append((c, u))
    return out
def meet(l1, l2):                                                      # intersection of two lines (point + direction)
    (c1, u1), (c2, u2) = l1, l2; A = np.array([u1, -u2]).T; t = np.linalg.lstsq(A, c2 - c1, rcond=None)[0]; return c1 + u1 * t[0]
def fillet(P0, C, P1, Qref, rmax):                                     # one arc at corner C between directions to P0 and P1, radius
    u1, u2 = (P0 - C) / np.linalg.norm(P0 - C), (P1 - C) / np.linalg.norm(P1 - C); ang = np.arccos(np.clip(u1 @ u2, -1, 1))
    best = None                                                        # fitted to the reference points near the corner
    for r in np.linspace(1, rmax, 120):
        dt = r / np.tan(ang / 2); t1, t2 = C + u1 * dt, C + u2 * dt; bis = (u1 + u2) / np.linalg.norm(u1 + u2); cc = C + bis * r / np.sin(ang / 2)
        near = Qref[np.linalg.norm(Qref - C, axis=1) < dt * 1.2]
        if not len(near): continue
        err = np.mean((np.linalg.norm(near - cc, axis=1) - r) ** 2)
        if best is None or err < best[0]: best = (err, r, t1, t2, cc)
    _, r, t1, t2, cc = best; a1, a2 = np.arctan2(*(t1 - cc)[::-1]), np.arctan2(*(t2 - cc)[::-1])
    if a2 - a1 > np.pi: a2 -= 2 * np.pi
    if a1 - a2 > np.pi: a2 += 2 * np.pi
    return r, t1, t2, np.array([cc + r * np.array([np.cos(a), np.sin(a)]) for a in np.linspace(a1, a2, 24)])
# outer line (right side): segments from the arm's end to the tip; the tip = where the last segment meets its mirror
ie = polyfit(ext, NSE); LE = lines_from(ext, ie)
pts = [np.array([LE[0][0][0] + LE[0][1][0] * (ext[0, 1] - LE[0][0][1]) / LE[0][1][1], ext[0, 1]])]
for k in range(len(LE) - 1): pts.append(meet(LE[k], LE[k + 1]))
mir = (LE[-1][0] * [-1, 1], LE[-1][1] * [-1, 1]); tip = meet(LE[-1], mir); tip[0] = 0.0
corners = pts[1:] + [tip]; arcs = []; seq = [pts[0]]
allc = pts + [tip]
for k, C in enumerate(corners):
    P0 = allc[k]; P1 = allc[k + 2] if k < len(corners) - 1 else np.array([-P0[0], P0[1]])   # at the tip: the mirrored side
    r, t1, t2, arc = fillet(P0, C, P1, ext, 120.0); arcs.append((C, r)); seq += list(arc)
    if k == len(corners) - 1: seq = seq[:len(seq) - len(arc) // 2] + [np.array([0.0, arc[len(arc) // 2][1]])]   # stop at the axis
right = np.array(seq); outer = np.vstack([right * [-1, 1], right[::-1][1:]])
# inner line: one straight line per arm, meeting its mirror on the axis; one arc there (the U)
ii = polyfit(inn, NSI); LI = lines_from(inn, ii); li = LI[0]; mi = (li[0] * [-1, 1], li[1] * [-1, 1]); U = meet(li, mi); U[0] = 0.0
end = np.array([li[0][0] + li[1][0] * (inn[0, 1] - li[0][1]) / li[1][1], inn[0, 1]])
r, t1, t2, arc = fillet(end, U, end * [-1, 1], inn, 120.0)
inner = np.vstack([[end * [-1, 1]], arc[::-1] if arc[0, 0] > 0 else arc, [end]])
dev = lambda Qr, L: np.median([np.min(np.linalg.norm(L - q, axis=1)) for q in Qr[::3]])
np.savez(OUT, outer=outer, inner=inner)
print("EXTERIOR: %d laturi drepte, colturi %s, raze arc %s; abatere mediana fata de referinta %.1f m" % (NSE, [tuple(np.round(c).astype(int)) for c, _ in arcs], [round(r_) for _, r_ in arcs], dev(ext, right)))
print("INTERIOR: 2 laturi drepte unite la y %.0f prin arc R %.0f; capete (+-%.0f, %.0f); abatere mediana %.1f m" % (U[1], r, end[0], end[1], dev(inn, inner)))
