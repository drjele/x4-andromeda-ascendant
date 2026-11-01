# The three band lines (contur_interior, spinare, contur_exterior) brought to a smooth bend (asked: their ends stay where they are,
# only the curvature made smooth after the head's turn): each line, from its head end to Y_LOB (the lobe, left as it is), refitted by
# a least-squares smoother on third differences (the curvature's change kept small) held near the line (weight MU), its first 2
# points (position + the head's direction) and the last 3 before the lobe (position, direction, curvature) fixed; the interior in its
# two segments, its V kept. Prints per line the max move, the bend-direction changes seen from above and the curvature range.
# Usage: python netezeste_trei.py <guides npz> <out npz> [S|D] ; env MU=1e-6 Y_LOB=1180 PAS=2
import sys, os, numpy as np
G = np.load(sys.argv[1]); OUT = sys.argv[2]; SD = sys.argv[3] if len(sys.argv) > 3 else "S"
MU, YL, PAS = float(os.environ.get("MU", "1e-6")), float(os.environ.get("Y_LOB", "1180")), float(os.environ.get("PAS", "2"))
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
def even(L, step=PAS):
    d = arclen(L); u = np.r_[np.arange(0, d[-1], step), d[-1]]; return np.c_[[np.interp(u, d, L[:, k]) for k in range(3)]].T
def smooth(L, fix0=2, fix1=3):
    n = len(L); D = np.diff(np.eye(n), 3, axis=0); A = D.T @ D + MU * np.eye(n); fx = np.zeros(n, bool); fx[:fix0] = True; fx[n - fix1:] = True
    fr = ~fx; X = L.copy()
    for k in range(3): X[fr, k] = np.linalg.solve(A[np.ix_(fr, fr)], MU * L[fr, k] - A[np.ix_(fr, fx)] @ L[fx, k])
    return X
def part(L):                                                               # smoothed from the head end up to the lobe; the rest kept
    L = even(L); j = int(np.argmax(L[:, 1] >= YL)) if (L[:, 1] >= YL).any() else len(L)
    return np.vstack([smooth(L[:j + 1]), L[j + 1:]]) if j > 10 else L
def bend(L):
    d = arclen(L); u = np.arange(0, d[-1], 2.0); Q = np.c_[[np.interp(u, d, L[:, k]) for k in range(3)]].T; t = np.gradient(Q[:, :2], axis=0)
    k = np.degrees(np.gradient(np.unwrap(np.arctan2(t[:, 1], t[:, 0])))) / 2; m = Q[:, 1] < YL; k = k[m]; sg = np.sign(k[np.abs(k) > 0.005])
    return int(np.sum(sg[1:] != sg[:-1])), k.min(), k.max()
out = {}
VX = G["buze_gura_brat_fata_%s" % SD]; iv = int(np.argmax([np.linalg.norm(VX[i] - VX[0]) + np.linalg.norm(VX[i] - VX[-1]) for i in range(len(VX))])); VX = VX[iv]
for nm in ("spinare", "contur_exterior", "contur_interior"):
    k_ = "%s_brat_fata_%s" % (nm, SD); L = G[k_]
    if nm == "contur_interior":                                            # (two segments at the lips' V)
        jv = int(np.argmin(np.linalg.norm(L - VX, axis=1))); A_ = even(L[:jv + 1]); B_ = part(L[jv:])
        N = np.vstack([smooth(A_, 2, 2), B_[1:]])
    else: N = part(L)
    mv = np.min(np.linalg.norm(N[:, None] - L[None], axis=2), axis=1).max(); b0, b1 = bend(L), bend(N)
    print("%-16s mutata max %.2f m; schimbari de sens (de sus, pana la lob) %d -> %d; curbura %.2f..%.2f -> %.2f..%.2f grd/m" % (
        nm, mv, b0[0], b1[0], b0[1], b0[2], b1[1], b1[2]))
    out[k_] = N
np.savez(OUT, **out)
