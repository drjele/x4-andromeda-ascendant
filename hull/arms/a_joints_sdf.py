# Local fillet pieces of the arm, step 2 of 3: per joint the smooth union of the swept arm with the pod tube or
# with the hull, the fillet diving under the hull skin where it thins, marching cubes, written for a_joints_mesh.py.
import json, numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
from skimage.measure import marching_cubes
P = json.load(open("a_params.json")); d = np.load("ajoints.npz"); out = {}
def sdf(occ, s): return gaussian_filter((distance_transform_edt(~occ) - distance_transform_edt(occ)) * s, 0.8)
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)
for name, J in P["joints"].items():
    s = J["step"]; La = sdf(d[name + "_arm"], s); F = La
    for m in J.get("members", []): F = smin(F, sdf(d[f"{name}_m_{m}"], s), J["blend"])
    if name + "_hull" in d:
        B = sdf(d[name + "_hull"], s); F = smin(F, B, J["blend"])
        c = J["cut"]; Lc = gaussian_filter(La, c["blur"]); t = c["lip"] + c["slope"] * (c["at"] - Lc)
        dive = np.minimum(B - t, c["lip"] + c["slope"] * c["at"] - B); F = -smin(-F, -np.maximum(dive, Lc - c["reach"]), c["round"])
    F = gaussian_filter(F, J["soften"]); v, f, _, _ = marching_cubes(F, 0.0, spacing=(s, s, s))
    out[name + "_v"] = v + np.array([J["box"]["x"][0], J["box"]["y"][0], J["box"]["z"][0]]); out[name + "_f"] = f; print("JSURF", name, len(v))
np.savez("ajsurf.npz", **out)
