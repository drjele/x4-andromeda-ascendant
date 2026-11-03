# Clean lines of every reference blade (asked: our blades follow the reference blades' angles, all of them): per blade (S half) in
# its own best-fit plane - outline rasterised (0.25 m), skeleton, its longest path ordered from end to end, the 3D middle line
# (plane point + the mean height of the reference surface off the plane there), Gaussian-smoothed SIG m, resampled every 1 m; the
# width along it from the distance transform, smoothed; the in-plane across direction. Writes <out.npz>: <blade>_mid, _w, _across, _n.
# Usage: python lame_ref_linii.py <lame_ref.npz> <out.npz> ; env SIG=15 (numpy, cv2, skimage, scipy)
import sys, os, numpy as np, cv2
from skimage.morphology import skeletonize
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree
from scipy.sparse.csgraph import shortest_path
from scipy.sparse import coo_matrix
Z = np.load(sys.argv[1]); OUT = sys.argv[2]; SIG = float(os.environ.get("SIG", 15)); out = {}
for key in Z.files:
    T = Z[key]; P = T.reshape(-1, 3); c = P.mean(0); _, _, Wt = np.linalg.svd(P - c); e1, e2, n = Wt
    Q = np.einsum("ijk,lk->ijl", T - c, np.array([e1, e2])); res = .25; lo = Q.reshape(-1, 2).min(0) - 5; sz = ((Q.reshape(-1, 2).max(0) + 5 - lo) / res).astype(int) + 1
    M = np.zeros((sz[1], sz[0]), np.uint8)
    for t in Q: cv2.fillPoly(M, [((t - lo) / res).astype(np.int32)], 1)
    dt = cv2.distanceTransform(M, cv2.DIST_L2, 5) * res; sk = skeletonize(M > 0); ys, xs = np.nonzero(sk); pts = np.c_[xs, ys]
    kd = cKDTree(pts); pr = kd.query_pairs(1.5, output_type="ndarray"); w_ = np.linalg.norm(pts[pr[:, 0]] - pts[pr[:, 1]], axis=1)
    G = coo_matrix((np.r_[w_, w_], (np.r_[pr[:, 0], pr[:, 1]], np.r_[pr[:, 1], pr[:, 0]])), shape=(len(pts), len(pts))).tocsr()
    d0 = shortest_path(G, indices=0, unweighted=False); d0[np.isinf(d0)] = -1; a = int(np.argmax(d0))
    da, pred = shortest_path(G, indices=a, return_predecessors=True); da[np.isinf(da)] = -1; b = int(np.argmax(da))
    path = [b]
    while path[-1] != a: path.append(pred[path[-1]])
    path = np.array(path[::-1]); P2 = pts[path] * res + lo; W2 = 2 * dt[pts[path, 1], pts[path, 0]]
    tri3 = P - c; h_kd = cKDTree(tri3 @ np.array([e1, e2]).T); hh = tri3 @ n
    H = np.array([hh[h_kd.query_ball_point(p, 6)].mean() if h_kd.query_ball_point(p, 6) else 0 for p in P2])
    X = c + np.outer(P2[:, 0], e1) + np.outer(P2[:, 1], e2) + np.outer(H, n)
    trim = int(np.ceil(np.median(W2) / 2 / (res)))                     # the skeleton runs into the ends' corners: keep them, smooth
    Xs = np.c_[[gaussian_filter1d(X[:, k], SIG / res, mode="nearest") for k in range(3)]].T
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Xs, axis=0), axis=1))]; u = np.arange(0, d[-1], 1.0)
    mid = np.c_[[np.interp(u, d, Xs[:, k]) for k in range(3)]].T; w = gaussian_filter1d(np.interp(u, d, W2), SIG, mode="nearest")
    Tg = np.gradient(mid, axis=0); Tg /= np.linalg.norm(Tg, axis=1)[:, None]; ac = np.cross(n, Tg); ac /= np.linalg.norm(ac, axis=1)[:, None]
    nm = key[4:]; out[nm + "_mid"], out[nm + "_w"], out[nm + "_across"], out[nm + "_n"] = mid, w, ac, np.tile(n, (len(mid), 1))
    print("LINII %s: %.0f m, latime %.1f..%.1f m (mediana %.1f), plan n %s, abatere de la plan %.1f m" % (nm, d[-1], w.min(), w.max(), np.median(w), n.round(2), np.abs(hh).max()))
np.savez(OUT, **out)
