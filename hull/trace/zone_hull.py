# The confirmed zones (profile + bottom) sampled on the world grids the fitting scripts use (arm_fit.py: hull.npz with
# arms_top / arms_side, 5 m cells), so the arm path and strap sizes can be fitted to them.
# Usage: python zone_hull.py <out_dir>
import sys, json, numpy as np
OD = sys.argv[1]; T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
src = open(f"{T}/trace/fit_zones.py").read(); src = src[:src.index("GROUPS = {")]
sys.argv = ["x", "/dev/null", OD]; exec(src)
VOX = 5.0; g[:] = [np.arange(-1100, 1100 + VOX / 2, VOX), np.arange(-1500, 1500 + VOX / 2, VOX), np.arange(-500, 500 + VOX / 2, VOX)]
arms_side = sample("side", side_mask(["BRAT"])); arms_top = sample("bottom", bmask(["BRAT", "BS"]))   # the footprint seen from below = from above
np.savez_compressed(f"{OD}/hull.npz", arms_side=arms_side, arms_top=arms_top); print("ZONE HULL", arms_side.shape, arms_top.shape, arms_side.sum(), arms_top.sum())
