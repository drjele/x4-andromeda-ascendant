# The 086 hood from its confirmed guides, sitting on the piece under it: top = the hood's confirmed top face, bottom = the
# piece's top face under it lowered EMB m (so the hood is seated in it, no gap), inside the hood's confirmed smoothed
# outline. Writes a terrain that ps_din_ghidaje.py builds. Usage: python capac_pe_ps.py <teren_086.npz> <teren_ps.npz> <out.npz> [emb]
import sys, numpy as np
from scipy.ndimage import map_coordinates
H = dict(np.load(sys.argv[1])); P = np.load(sys.argv[2]); OUT = sys.argv[3]; EMB = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
ny, nx = H["top"].shape; C, x0, y0 = float(H["cell"]), float(H["x0"]), float(H["y0"]); yy, xx = np.mgrid[0:ny, 0:nx]
X, Y = x0 + (xx + 0.5) * C, y0 + (yy + 0.5) * C
pt = map_coordinates(P["top"].astype(float), [(Y - float(P["y0"])) / float(P["cell"]) - 0.5, (X - float(P["x0"])) / float(P["cell"]) - 0.5], order=1, mode="nearest")
H["bot"] = (pt - EMB).astype(np.float32); H["top"] = np.maximum(H["top"].astype(float), pt + 0.5).astype(np.float32)
np.savez(OUT, **H); f = H["foot"].astype(bool)
print("CAPAC pe PS: sus %.0f..%.0f, jos (fata PS - %.0f m) %.0f..%.0f" % (H["top"][f].min(), H["top"][f].max(), EMB, H["bot"][f].min(), H["bot"][f].max()))
