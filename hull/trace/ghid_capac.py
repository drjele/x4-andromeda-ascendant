# Guides for the 086 hood (asked: create guides for sep_capac_086 too). Each line in one plane, closed, lightly smoothed
# (SM m, ends wrap), symmetric where the hood is: the base outline seen from above (z = the hood's lowest, the plan
# silhouette), the middle profile (plane x = 0, outer loop), and across every PAS m (planes y = const) the outer section
# and the chambers' sections inside it. Optional DZ shifts them (to draw them on the exploded hood).
# Usage: python ghid_capac.py <hood npz v,f (ship coords)> <out.npz> ; env PAS=20 SM=1 DZ=0
import sys, os, numpy as np, trimesh, cv2
from scipy.ndimage import gaussian_filter1d
D = np.load(sys.argv[1]); OUT = sys.argv[2]; PAS, SM, DZ = (float(os.environ.get(k, d)) for k, d in (("PAS", "20"), ("SM", "1"), ("DZ", "0")))
t = trimesh.Trimesh(D["v"], D["f"], process=False); z0 = t.bounds[0, 2]; y0, y1 = t.bounds[0, 1], t.bounds[1, 1]
def smooth(L, sm=SM):
    L = L[:-1] if np.allclose(L[0], L[-1]) else L; c = np.vstack([L, L[:1]]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    u = np.arange(0, d[-1], 0.25); P = np.c_[[np.interp(u, d, c[:, k]) for k in range(L.shape[1])]].T
    if sm > 0: P = np.c_[[gaussian_filter1d(P[:, k], sm / 0.25, mode="wrap") for k in range(P.shape[1])]].T
    return np.vstack([P, P[:1]])
out = {}
PX = 0.25; X0, Y0 = -100.0, y0 - 10; M = np.zeros((int((y1 - y0 + 20) / PX), int(200 / PX)), np.uint8)
px = lambda q: np.c_[(q[:, 0] - X0) / PX, (q[:, 1] - Y0) / PX].astype(np.int32)
for tri in t.vertices[t.faces][:, :, :2]: cv2.fillConvexPoly(M, px(tri), 1)
M = M | np.flip(M, 1); cs, _ = cv2.findContours(M, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
B = smooth(np.c_[c[:, 0] * PX + X0, c[:, 1] * PX + Y0], 2.0); out["contur_capac_baza"] = np.c_[B, np.full(len(B), z0)]
s = t.section(plane_origin=[0, 0, 0], plane_normal=[1, 0, 0]); L = max(s.discrete, key=lambda q: np.ptp(q[:, 1]))
out["spinare_capac_mijloc"] = np.c_[np.zeros(len(smooth(L[:, 1:]))), smooth(L[:, 1:])]
k = 0
for y in np.arange(np.ceil((y0 + 4) / PAS) * PAS, y1 - 2, PAS):
    s = t.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: continue
    loops = sorted([q[:, [0, 2]] for q in s.discrete], key=lambda q: -np.ptp(q[:, 0]) * np.ptp(q[:, 1]))
    big = loops[0]; out["sectiune_capac_%02d" % k] = np.c_[smooth(big)[:, 0], np.full(len(smooth(big)), y), smooth(big)[:, 1]]
    def inside(q):
        from matplotlib.path import Path
        return Path(big).contains_point(q.mean(0))
    ch = [q for q in loops[1:] if inside(q) and np.ptp(q[:, 0]) > 3]
    for j, q in enumerate(sorted(ch, key=lambda q: q[:, 0].mean())):
        sq = smooth(q); out["sectiune_capac_%02d_camera_%s" % (k, "S" if q[:, 0].mean() < 0 else "D")] = np.c_[sq[:, 0], np.full(len(sq), y), sq[:, 1]]
    k += 1
for kk in out: out[kk] = out[kk] + [0, 0, DZ]
print("GHIDAJE CAPAC 086: baza (de sus, z %.1f) x %.0f..%.0f y %.0f..%.0f; spinarea de la mijloc (x 0) y %.0f..%.0f z %.0f..%.0f; %d sectiuni la %.0f m (y %.0f..%.0f), %d contururi de camere" % (
    z0, B[:, 0].min(), B[:, 0].max(), B[:, 1].min(), B[:, 1].max(), L[:, 1].min(), L[:, 1].max(), L[:, 2].min(), L[:, 2].max(), k, PAS,
    np.ceil((y0 + 4) / PAS) * PAS, y1 - 2, sum(1 for kk in out if "camera" in kk)))
np.savez(OUT, **out)
