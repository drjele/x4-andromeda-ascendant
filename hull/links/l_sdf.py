# One surface from the fields: the branches as level sets of their heightfields, the body as a signed
# distance from its voxels, a smooth union of the two branches and of the link with the body (the fillets),
# a clean end of the fillet skin on the body, then marching cubes.
import json, numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.interpolate import RegularGridInterpolator
from skimage.measure import marching_cubes
P = json.load(open("l_params.json")); d = np.load("lvox.npz"); s = float(d["xs"][1] - d["xs"][0])
X, Y, Z = np.meshgrid(d["xs"], d["ys"], d["zs"], indexing="ij")
def field(npz):
    # a branch as a pseudo distance with a bounded gradient: in the section across the outline its profile is
    # an ellipse (the rounded rim), measured in units of the smaller semi-axis; in plane it ends at its outline
    p = np.load(npz); g = (p["ys"], p["xs"]); q = np.stack([Y[:, :, 0], X[:, :, 0]], -1); rim = float(p["rim"])
    at = lambda k: RegularGridInterpolator(g, p[k], bounds_error=False, fill_value=None)(q)[:, :, None]
    hf = np.maximum(at("hf"), 1.0); u = np.maximum(rim - at("sd"), 0) / rim; v = (Z - at("mid")) / hf
    return np.maximum((np.hypot(u, v) - 1) * np.minimum(rim, hf), -at("sdm"))
def vox(o): return (distance_transform_edt(~o) - distance_transform_edt(o)) * s
def sdf(key):
    e = vox(d[key]); a = np.abs(e)
    # the swept tangent-plane distance is exact near the surface but jumps further out, where an axis ray
    # may miss a thin branch, so beyond a voxel it hands over to the smoothed voxel distance
    near = np.sign(e) * np.minimum(d[key + "_d"].astype(np.float64), a + s); w = np.clip(a / s - 1, 0, 1)
    return near * (1 - w) + gaussian_filter(e, 1.0) * w
def smin(a, b, k):
    k = np.maximum(k, 1e-3); h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)
# the body and the arm together are the hull the link fillets onto and ends in
W, K, B = field("lplate.npz"), field("ldeck.npz"), np.minimum(sdf("body"), sdf("arm"))
L = smin(W, K, P["blend"]["fork"])
# only a hairline fillet onto the body inside the hangar tunnel, so the flank stays bare there yet the
# ceiling's crease does not alias; the tunnel fades out slowly toward the stern, where the Y closes
t = P["blend"]["tunnel"]
def box(v, lo, hi, r): return np.clip(np.minimum((v - lo) / r, (hi - v) / r), 0, 1)
tun = box(Y, *t["y"], t["ramp_y"]) * box(Z, *t["z"], t["ramp"]) * box(X, -1e9, t["x_max"], t["ramp"])
F = smin(L, B, P["blend"]["body"] * (1 - tun) + t["k"] * tun)
# the fillet skin would feather to nothing on the body: where it gets thin it dives into the body instead,
# and the solid keeps the body's inside so the mesh step can clip it there into a clean edge
# the cut is shaped far from the link, where the swept distance is not smooth, so it takes the voxel distance
c = P["blend"]["cut"]; Lc = gaussian_filter(np.minimum(W, K), c["blur"]); t = c["lip"] + c["slope"] * (c["at"] - Lc)
dive = np.minimum(B - t, c["lip"] + c["slope"] * c["at"] - B)
F = -smin(-F, -np.maximum(dive, Lc - c["reach"]), c["round"])
F = gaussian_filter(F, P["blend"]["soften"])
v, f, _, _ = marching_cubes(F, 0.0, spacing=(s, s, s))
v += np.array([d["xs"][0], d["ys"][0], d["zs"][0]])
np.savez("lsurf.npz", v=v, f=f)
print("LSURF", len(v), len(f))
