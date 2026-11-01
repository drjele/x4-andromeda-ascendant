# The arm's surface carried after ribs that were moved (here: the open ribs put on the lips): every rib point's move (new - old,
# same index) spread to the surface's vertices by inverse-square distance over the K nearest rib points, faded out to nothing at
# FADE m from the nearest moved point. (Move of a rib point = to its nearest point on the new rib.) Right arm computed, the left one mirrored.
# Usage: python piesa_dupa_vertebre.py <old guides npz> <new guides npz> <piece npz (brat_fata_D__v/__f)> <out npz> ; env K=8 FADE=30
import sys, os, numpy as np
from scipy.spatial import cKDTree
A, B, Z = np.load(sys.argv[1]), np.load(sys.argv[2]), np.load(sys.argv[3]); OUT = sys.argv[4]
K, FD = int(os.environ.get("K", "8")), float(os.environ.get("FADE", "30"))
P, D = [], []
for k in A.files:
    if k.startswith("sectiune_brat_fata_D") and k in B.files:              # (each old point's move = to its nearest point on the new rib)
        Bn = B[k]; Bd = np.vstack([np.linspace(Bn[i], Bn[i + 1], 6)[:-1] for i in range(len(Bn) - 1)] + [Bn[-1:]])
        P.append(A[k]); D.append(Bd[cKDTree(Bd).query(A[k])[1]] - A[k])
P, D = np.vstack(P), np.vstack(D); mv = np.linalg.norm(D, axis=1) > 1e-6; kd = cKDTree(P); kdm = cKDTree(P[mv])
V = Z["brat_fata_D__v"].copy(); d, i = kd.query(V, K); w = 1 / np.maximum(d, 0.5) ** 2; w /= w.sum(1)[:, None]
dm = kdm.query(V)[0]; f = np.clip(1 - dm / FD, 0, 1); f = f * f * (3 - 2 * f)
V += (np.einsum("ij,ijk->ik", w, D[i])) * f[:, None]
np.savez(OUT, brat_fata_D__v=V, brat_fata_D__f=Z["brat_fata_D__f"], brat_fata_S__v=V * [-1, 1, 1], brat_fata_S__f=Z["brat_fata_D__f"][:, ::-1])
print("PIESA dupa vertebre: varfuri mutate max %.2f m" % np.linalg.norm(V - Z["brat_fata_D__v"], axis=1).max())
