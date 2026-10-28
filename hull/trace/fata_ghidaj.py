# One face of the terrain guides (ref_teren.py) as a surface, to judge its detail against the original: the top or the bottom
# field as a triangle grid over the footprint (ship coordinates, centred). Usage: python fata_ghidaj.py <teren.npz> <top|bot> <out.npz>
import sys, numpy as np
T = np.load(sys.argv[1]); F = T[sys.argv[2]]; foot = T["foot"].astype(bool); x0, y0, C = float(T["x0"]), float(T["y0"]), float(T["cell"])
ny, nx = F.shape; idx = -np.ones((ny, nx), int); ii, jj = np.nonzero(foot); idx[ii, jj] = np.arange(len(ii))
v = np.stack([x0 + (jj + 0.5) * C, y0 + (ii + 0.5) * C, F[ii, jj]], 1)
a, b, c, d = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]; ok = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
f = np.r_[np.stack([a[ok], b[ok], d[ok]], 1), np.stack([a[ok], d[ok], c[ok]], 1)]
if sys.argv[2] == "bot": f = f[:, ::-1]
np.savez(sys.argv[3], v=v.astype(np.float32), f=f.astype(np.int32)); print("FATA %s: %d varfuri, %d triunghiuri" % (sys.argv[2], len(v), len(f)))
