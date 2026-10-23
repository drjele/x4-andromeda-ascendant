# The pylon with fillets onto the body and the arm: smooth unions, marching cubes.
import json, numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
from skimage.measure import marching_cubes
P = json.load(open("u_params.json")); d = np.load("uvox.npz"); s = float(d["xs"][1] - d["xs"][0])
def sdf(o): return gaussian_filter((distance_transform_edt(~o) - distance_transform_edt(o)) * s, 1.0)
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)
from scipy.spatial import cKDTree
S = d["plate"]; X, Y, Z = np.meshgrid(d["xs"], d["ys"], d["zs"], indexing="ij"); G = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
dist, idx = cKDTree(S[:, :3]).query(G, k=6); PL = (dist - S[idx, 3]).min(1).reshape(X.shape)
F = smin(smin(gaussian_filter(PL, 0.8), sdf(d["body"]), P["blend"]["body"]), sdf(d["arm"]), P["blend"]["arm"])
F = gaussian_filter(F, P["blend"]["soften"])
v, f, _, _ = marching_cubes(F, 0.0, spacing=(s, s, s)); v += np.array([d["xs"][0], d["ys"][0], d["zs"][0]])
np.savez("usurf.npz", v=v, f=f); print("USURF", len(v))
