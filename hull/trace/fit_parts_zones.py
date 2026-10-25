# Generator parameters fitted to the confirmed zones (profile + bottom), for the parts after the arms:
#  - U arch legs: each control point's x/y moved onto the centre line of the ARC U zone (bottom view), strap width
#    from the zone's local width (kept within +-25 %), z kept;
#  - upper wings: the chord table (z -> front y, back y) read from the AS zone in profile at each z level;
#  - the bridge (V plate): its lift set so its top in profile meets the PUNTE zone's top (mean over its length).
# Writes the parameter files in place; the old ones are copied next to the zones first.
# Usage: python fit_parts_zones.py <mesh.npz> <backup_dir>
import sys, json, numpy as np, cv2
from scipy.ndimage import distance_transform_edt
from skimage.morphology import skeletonize
MESH, BK = sys.argv[1:3]; T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
src = open(f"{T}/trace/fit_zones.py").read(); src = src[:src.index("GROUPS = {")]; sys.argv = ["x", MESH, BK]; exec(src)
import shutil
for f in ("uarch/g_params.json", "upper/u_params.json", "vtop/v_params.json"): shutil.copy(f"{T}/{f}", f"{BK}/{f.split('/')[1]}")
# --- U arch legs
arc = sample("bottom", bmask(["ARC U"]))                                    # [x, y]
sk = skeletonize(arc); dt = distance_transform_edt(arc) * VOX; pts = np.argwhere(sk); XY = np.stack([g[0][pts[:, 0]], g[1][pts[:, 1]]], 1); WD = 2 * dt[pts[:, 0], pts[:, 1]]
G = json.load(open(f"{T}/uarch/g_params.json")); moved = []
for m in ("leg_l", "leg_r"):
    path = np.array(G["members"][m]["path"], float)
    for i, p in enumerate(path):
        d = np.hypot(*(XY - p[:2]).T); k = int(np.argmin(d))
        if d[k] < 80: moved.append(d[k]); path[i, :2] += (XY[k] - p[:2]) * 0.8
    k3 = 3; ker = np.ones(k3) / k3                                              # light smoothing along the leg
    for c in (0, 1): path[1:-1, c] = np.convolve(np.pad(path[:, c], 1, mode="edge"), ker, "valid")[1:-1]
    G["members"][m]["path"] = np.round(path).astype(int).tolist()
    secs = G["members"][m]["sections"]; L_ = len(path)
    for row in secs:
        q = path[min(int(row[0] * (L_ - 1)), L_ - 1)][:2]; k = int(np.argmin(np.hypot(*(XY - q).T)))
        row[1] = int(round(float(np.clip(WD[k], row[1] * 0.75, row[1] * 1.25))))
json.dump(G, open(f"{T}/uarch/g_params.json", "w")); print("U ARCH legs: points moved mean %.0f m" % np.mean(moved))
# --- upper wings: front/back y of the AS zone at each z
AS = sample("side", side_mask(["AS"]))                                      # [y, z]
U = json.load(open(f"{T}/upper/u_params.json")); new = []
for z, yf, yb in U["chord_z"]:
    col = AS[:, np.argmin(abs(g[2] - z))]; ys = g[1][col]
    if len(ys) > 3: new.append([z, int(round(0.7 * ys.max() + 0.3 * yf)), int(round(0.7 * ys.min() + 0.3 * yb))])
    else: new.append([z, yf, yb])
print("UPPER chord:", U["chord_z"], "->", new); U["chord_z"] = new; json.dump(U, open(f"{T}/upper/u_params.json", "w"))
# --- bridge lift
PU = sample("side", side_mask(["PUNTE"])); M_ = np.load(MESH); v = M_["v|V1|v_plate"]
dz = []
for i, y in enumerate(g[1]):
    zs = g[2][PU[i]]; sel = np.abs(v[:, 1] - y) < VOX
    if len(zs) and sel.any(): dz.append(zs.max() - v[sel, 2].max())
VP = json.load(open(f"{T}/vtop/v_params.json")); d = float(np.median(dz)) if dz else 0.0; d = float(np.clip(d, -25, 25))
VP["lift"] = round(VP.get("lift", 0) + d, 1); json.dump(VP, open(f"{T}/vtop/v_params.json", "w")); print("BRIDGE lift %+.1f -> %.1f (%d samples)" % (d, VP["lift"], len(dz)))
