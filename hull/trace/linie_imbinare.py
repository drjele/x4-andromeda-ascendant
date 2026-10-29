# The joint line between a piece and its neighbour (asked: the line where 103 meets the PS clear and straight): where the
# piece's surface crosses the neighbour's (signed distance changes sign, triangle by triangle), the longest runs kept, then
# how straight it is seen from above - deviation from its best straight line - and its height range (one clear line = one
# long run at a steady height). Usage: python linie_imbinare.py <piece.npz v,f (ship coords)> <pieces.npz> <neighbour> [dx]
import sys, numpy as np, igl
P = np.load(sys.argv[1]); D = np.load(sys.argv[2]); NB = sys.argv[3]; DX = float(sys.argv[4]) if len(sys.argv) > 4 else -1700.0
v = P["v"].astype(float) + [DX, 0, 0]; f = P["f"].astype(np.int64)
s = -igl.signed_distance(v, D[NB + "__v"].astype(float), D[NB + "__f"].astype(np.int64), sign_type=igl.SIGNED_DISTANCE_TYPE_FAST_WINDING_NUMBER)[0]
pts = []
for t in f[(np.sign(s[f]) != np.sign(s[f[:, :1]])).any(1)]:
    for i, j in ((0, 1), (1, 2), (2, 0)):
        a, b = t[i], t[j]
        if (s[a] < 0) != (s[b] < 0): u = s[a] / (s[a] - s[b]); pts.append(v[a] + u * (v[b] - v[a]))
p = np.array(pts); p[:, 0] -= DX
for nm, sel in (("sus (fata de sus a piesei)", p[:, 2] > np.median(p[:, 2])), ("jos", p[:, 2] <= np.median(p[:, 2]))):
    q = p[sel]; q = q[np.argsort(q[:, 1])]
    A = np.c_[q[:, 1], np.ones(len(q))]; k, c = np.linalg.lstsq(A, q[:, 0], rcond=None)[0]; dev = q[:, 0] - (k * q[:, 1] + c)
    print("LINIE %-26s y %5.0f..%4.0f | abatere de la dreapta (de sus): medie %.1f m, max %.1f m | z %.0f..%.0f (abatere std %.1f m)"
          % (nm, q[:, 1].min(), q[:, 1].max(), np.abs(dev).mean(), np.abs(dev).max(), q[:, 2].min(), q[:, 2].max(), q[:, 2].std()))
