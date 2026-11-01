# The reference arm's own band (asked: draw g_bfs_banda_spinare's equivalent for lucru_brat_fata, to compare): along a path through
# the reference arm (a spine npz), every PAS m the arm's section across it (exact cut of the mesh); an ellipse fitted to the cut;
# the band row = the ellipse's major axis, end to end (outer end = the exterior, inner end = the interior; along the mouth the cut is
# open and the fitted ellipse closes it). Also writes the three lines (exterior / centre / interior). Right arm, the left mirrored.
# Usage: python banda_referinta.py <arms npz (brat_fata_D__v/__f)> <path npz key> <out npz> ; env PAS=4 NB=17
import sys, os, numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brat_fata_lib import ellipse_fit
Z = np.load(sys.argv[1]); pth, key = sys.argv[2].split(":"); OUT = sys.argv[3]; PAS, NB = float(os.environ.get("PAS", "4")), int(os.environ.get("NB", "17"))
m = trimesh.Trimesh(Z["brat_fata_D__v"], Z["brat_fata_D__f"], process=False); SP = np.load(pth)[key]
arclen = lambda L: np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]; dS = arclen(SP)
E, C, I, rows = [], [], [], []
for s0 in np.arange(max(PAS, float(os.environ.get("START", "30"))), dS[-1] - PAS, PAS):   # (the first metres cut into the PS funnel)
    i = min(max(int(np.searchsorted(dS, s0)), 1), len(SP) - 2); p = np.array([np.interp(s0, dS, SP[:, k]) for k in range(3)])
    n = SP[i + 1] - SP[i - 1]; n /= np.linalg.norm(n); e1 = np.cross(n, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(e1, n)
    seg = trimesh.intersections.mesh_plane(m, n, p)
    if len(seg) < 10: continue
    Q = seg.reshape(-1, 3); Q = Q[np.linalg.norm(Q - p, axis=1) < 260]
    if len(Q) < 20: continue
    q2 = np.c_[(Q - p) @ e1, (Q - p) @ e2]
    try: c2, r, an = ellipse_fit(q2)
    except Exception: continue
    if not np.all(np.isfinite(r)) or r.max() > 400: continue
    if r[0] < r[1]: an += np.pi / 2
    a = r.max(); d2 = np.array([np.cos(an), np.sin(an)]); d3 = e1 * d2[0] + e2 * d2[1]; c3 = p + e1 * c2[0] + e2 * c2[1]
    P1, P2 = c3 + d3 * a, c3 - d3 * a
    out_ = np.array([-1.0, 0, 0])                                          # (the exterior: the end farther from the ship's middle, x = 0)
    if abs(P1[0]) < abs(P2[0]): P1, P2 = P2, P1
    E.append(P1); C.append(c3); I.append(P2); rows.append(np.linspace(P1, P2, NB))
R = np.array(rows); nr = len(R); V = R.reshape(-1, 3); F = []
for r_ in range(nr - 1):
    for j in range(NB - 1):
        q = [r_ * NB + j, r_ * NB + j + 1, (r_ + 1) * NB + j + 1, (r_ + 1) * NB + j]; F += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
F = np.array(F)
np.savez(OUT, v=V * [-1, 1, 1], f=F[:, ::-1], v_D=V, f_D=F, exterior_D=np.array(E), centru_D=np.array(C), interior_D=np.array(I))
w = np.linalg.norm(np.array(E) - np.array(I), axis=1)
print("BANDA referinta: %d randuri (la %.0f m), latime %.0f..%.0f m" % (nr, PAS, w.min(), w.max()))
