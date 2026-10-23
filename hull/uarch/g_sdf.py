# The U arch as one surface: signed distances (exact near the tubes, voxel distance further out),
# smooth union of the members, then fillets onto the arms that end cleanly under their skin, marching cubes.
import json, numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
from skimage.measure import marching_cubes
P = json.load(open("g_params.json")); d = np.load("gvox.npz"); s = float(d["xs"][1] - d["xs"][0])
def sdf(n):
    o = d[n]; e = (distance_transform_edt(~o) - distance_transform_edt(o)) * s
    if n + "_b" not in d: return e
    # the exact distance holds within two cells of the surface and hands over to the voxel distance beyond
    ex = np.where(d[n + "_b"], np.sign(e) * d[n + "_d"].astype(np.float64), e); w = np.clip(np.abs(e) / s - 2, 0, 1)
    return ex * (1 - w) + e * w
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)
names = list(P["members"]); F = sdf(names[0])
for n in names[1:]: F = smin(F, sdf(n), P["blend"]["members"])
La = F
for key, k in P["blend"]["unions"].items(): B = sdf(key); F = smin(F, B, k)
# the fillet skin would feather to nothing on the hull: where it gets thin it dives under the skin instead
# (the mesh step clips it there into a clean edge), and nothing of the hull's own skin is kept beyond reach
c = P["blend"]["cut"]; Lc = gaussian_filter(La, c["blur"]); t = c["lip"] + c["slope"] * (c["at"] - Lc)
dive = np.minimum(B - t, c["lip"] + c["slope"] * c["at"] - B)
F = -smin(-F, -np.maximum(dive, Lc - c["reach"]), c["round"])
F = gaussian_filter(F, P["blend"]["soften"])
v, f, _, _ = marching_cubes(F, 0.0, spacing=(s, s, s)); v += np.array([d["xs"][0], d["ys"][0], d["zs"][0]])
np.savez("gsurf.npz", v=v, f=f); print("GSURF", len(v))
