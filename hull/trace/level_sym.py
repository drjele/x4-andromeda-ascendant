# A model leveled by its own left/right symmetry: small rolls (about the length axis y) and yaws (about z) searched so
# the mirror image across the centre plane x = c lies on the model itself (mean distance of mirrored surface points to
# the nearest point), coarse then fine; applied about the model's centre, written back in place. Prints the angles.
# Usage: python level_sym.py <model.obj> [<model.obj> ...]
import sys, numpy as np
from scipy.spatial import cKDTree
def rot(roll, yaw):
    cr, sr, cy, sy = np.cos(roll), np.sin(roll), np.cos(yaw), np.sin(yaw)
    Ry = np.array([[cr, 0, sr], [0, 1, 0], [-sr, 0, cr]]); Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]]); return Rz @ Ry
for p in sys.argv[1:]:
    L = open(p).read().split("\n"); V = np.array([l.split()[1:4] for l in L if l.startswith("v ")], float)
    cen = (V.min(0) + V.max(0)) / 2; P = V[np.random.default_rng(0).choice(len(V), min(len(V), 60000), replace=False)] - cen
    def cost(r, y):
        Q = P @ rot(r, y).T; c = np.median(Q[:, 0]); M = Q.copy(); M[:, 0] = 2 * c - M[:, 0]
        d, _ = cKDTree(Q).query(M); return np.mean(np.minimum(d, 80))
    best = (cost(0, 0), 0.0, 0.0); start = best[0]
    for step in np.radians([4, 1.5, 0.5, 0.2]):
        improved = True
        while improved:
            improved = False
            for dr, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
                v = cost(best[1] + dr, best[2] + dy)
                if v < best[0] - 1e-3: best = (v, best[1] + dr, best[2] + dy); improved = True
    R = rot(best[1], best[2]); W = (V - cen) @ R.T; W[:, 0] -= np.median(W[:, 0]); W += [0, cen[1], cen[2]]; it = iter(W); out = []
    for l in L: out.append("v %.3f %.3f %.3f" % tuple(next(it)) if l.startswith("v ") else l)
    open(p, "w").write("\n".join(out)); print(p.split("/")[-1], "asimetrie %.1f -> %.1f m" % (start, best[0]), "roll %.2f yaw %.2f grade" % tuple(np.degrees(best[1:])))
