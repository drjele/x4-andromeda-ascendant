# The flat guide's lines made straight after their curve (asked: the head stays curved, after its curve ends the lines are
# completely straight, half as long as now; then the same for the whole outline, all in one plane): from ghid_plan2.py's
# line, two runs from the middle line - the outer one from the nose tip down the outside, the inner one from the U between
# the arms down the inside - each kept curved until its curvature dies out (|k| < KMIN), then a straight line of half the
# run's current length (to the bottom of the arm). Variant A: the straight line is the curve's own tangent there. Variant
# B: one arc of radius RB, turning the same way as the curve, on to the side's mean direction (least squares over the
# reference side), then straight. Each run mirrored: one open line, side - middle - side; z is set when drawing.
# Usage: python ghid_drept.py <ghid.npz> <out.npz> [png]   -> A, B (outer), A_int, B_int (inner)
import sys, os, numpy as np, cv2
G = np.load(sys.argv[1]); OUT = sys.argv[2]; PNG = sys.argv[3] if len(sys.argv) > 3 else None
KMIN, RB = float(os.environ.get("GHID_KMIN", "0.0012")), float(os.environ.get("GHID_RAZA_B", "300"))
g = G["contur"]; n = len(g); R = g[:n // 2 + 1]
if R[5, 0] < 0: R = np.vstack([g[:1], g[::-1][:n // 2]])               # right half: nose tip ... U (both on x = 0)
def line(p, d, L, step=1.0): return p + np.outer(np.arange(step, L + 1e-9, step), d)
def straighten(Rn, name):                                              # Rn: from the middle point down the side
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Rn, axis=0), axis=1))]; t = np.gradient(Rn, axis=0); a = np.unwrap(np.arctan2(t[:, 1], t[:, 0]))
    k = np.gradient(a) / np.gradient(s)
    ie = int(np.nonzero((s > 20) & (np.abs(k) < KMIN))[0][0])           # the curve ends here
    ib = int(np.nonzero(np.diff(Rn[ie:, 1]) > 0)[0][0]) + ie            # bottom of the side (it stops going down)
    Lh = 0.5 * (s[ib] - s[ie]); cur = Rn[:ie + 1]; pe = Rn[ie]; te = t[ie] / np.linalg.norm(t[ie])
    A = np.vstack([cur, line(pe, te, Lh)])
    side = Rn[ie + 50:ib]; c = side.mean(0); d = np.linalg.svd(side - c)[2][0]; d = d if d[1] < 0 else -d
    cr = te[0] * d[1] - te[1] * d[0]; nrm = np.array([te[1], -te[0]]) if cr < 0 else np.array([-te[1], te[0]])   # turning side
    cc = pe + nrm * RB; ang = np.arccos(np.clip(te @ d, -1, 1))
    arc = np.array([cc + RB * (np.cos(q) * (-nrm) + np.sin(q) * te) for q in np.linspace(0, ang, 40)])
    B = np.vstack([cur, arc[1:], line(arc[-1], d, max(Lh - RB * ang, 1.0))])
    print("%s: curb pana la (%.1f, %.1f), tangenta %.1f grade; latura de acum %.0f m -> dreapta %.0f m; A capat (%.0f, %.0f); B arc %.1f grade spre %.1f grade, capat (%.0f, %.0f)" % (
        name, pe[0], pe[1], np.degrees(np.arctan2(te[1], te[0])), s[ib] - s[ie], Lh, *A[-1], np.degrees(ang), np.degrees(np.arctan2(d[1], d[0])), *B[-1]))
    return A, B
full = lambda H: np.vstack([H[::-1][:-1] * [-1, 1], H])                # left side up to the middle, then the right side down
A, B = straighten(R, "EXTERIOR")
Ai, Bi = straighten(R[::-1], "INTERIOR")
np.savez(OUT, A=full(A), B=full(B), A_int=full(Ai), B_int=full(Bi), centru=G["centru"])
if PNG:
    XM, Y0, Y1, sc = 700.0, -1450.0, 560.0, 0.5; im = np.full((int((Y1 - Y0) * sc) + 20, int(2 * XM * sc) + 20, 3), 255, np.uint8)
    f = lambda Q: np.stack([(Q[:, 0] + XM) * sc + 10, (Y1 - Q[:, 1]) * sc + 10], 1).astype(np.int32)
    cv2.polylines(im, [f(g)], True, (190, 190, 190), 1)
    for Q in (full(B), full(Bi)): cv2.polylines(im, [f(Q)], False, (220, 80, 0), 2)
    cv2.imwrite(PNG, im)
