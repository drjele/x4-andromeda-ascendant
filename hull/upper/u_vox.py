# The upper wing (pylon) that rises from the body top to the arm's upper member: a lens-section plate
# ruled between a line on the body and the arm's centreline, voxelized with the body and the arm.
import bpy, bmesh, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{D}/upper/u_params.json")); A = json.load(open(f"{D}/arms/a_params.json"))["members"]["arm"]["path"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
def tree(n): b = bmesh.new(); b.from_mesh(sc.objects[n].data); return BVHTree.FromBMesh(b)
def union(names):
    b = bmesh.new()
    for n in names: b.from_mesh(sc.objects[n].data)
    return BVHTree.FromBMesh(b)
CT, AT = union(P.get("bases", ["corp"])), tree("arm_r")                 # the pylon fillets onto the rear deck and the crescent as well
A = np.array(A, float)
# the pylon follows the source's open C in the x-z plane: nearly upright off the body, then curving out to the arm
def soft(xq, xk, yk, w):
    # the tables are polylines; sampled finely and run through a triangular window they lose their creases
    g = np.linspace(xk[0], xk[-1], 400); v = np.interp(g, xk, yk); n = max(int(w / (g[1] - g[0])), 1); box = np.ones(n) / n
    pad = np.r_[np.full(n, v[0]), v, np.full(n, v[-1])]; v = np.convolve(np.convolve(pad, box, "same"), box, "same")[n:-n]
    return np.interp(xq, g, v)
K = np.array(P["curve"], float); kl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(K, axis=0), axis=1))]; kl /= kl[-1]
Cz = np.array(P["chord_z"], float); Tz = np.array(P["thick_z"], float); W = P["smooth"]
ss = np.linspace(0, 1, 260); us = np.linspace(-1, 1, 81); SAMPLES = []
KX, KZ = soft(ss, kl, K[:, 0], W["curve"]), soft(ss, kl, K[:, 1], W["curve"])
# the top of the pylon follows the arm's centreline in x, so it meets the arm the same way along its length
hi = (A[:, 1] < -150) & (A[:, 2] > 200); Ay, Ax = A[hi][np.argsort(A[hi][:, 1])][:, 1], A[hi][np.argsort(A[hi][:, 1])][:, 0]
for k, s in enumerate(ss):
    x, z = KX[k], KZ[k]; tx, tz = KX[min(k + 1, len(ss) - 1)] - KX[max(k - 1, 0)], KZ[min(k + 1, len(ss) - 1)] - KZ[max(k - 1, 0)]
    nrm = np.array([tz, 0.0, -tx]); nrm /= np.linalg.norm(nrm)
    y0, y1 = soft(z, Cz[:, 0], Cz[:, 1], W["chord"]), soft(z, Cz[:, 0], Cz[:, 2], W["chord"]); th = soft(z, Tz[:, 0], Tz[:, 1], W["thick"])
    f = np.clip((z - P["follow"][0]) / (P["follow"][1] - P["follow"][0]), 0, 1) ** 2
    for u in us:
        y = (y0 + y1) / 2 + u * (y1 - y0) / 2; h = th / 2 * math.sqrt(max(0.0, 1 - u * u)) + 0.01
        p = np.array([x + f * (np.interp(y, Ay, Ax) - KX[-1]), y, z])
        SAMPLES.append((*p, h))
G = P["grid"]; st = G["step"]; xs = np.arange(*G["x"], st); ys = np.arange(*G["y"], st); zs = np.arange(*G["z"], st); out = {}
for key, T in (("body", CT), ("arm", AT)):
    occ = np.zeros((len(xs), len(ys), len(zs)), bool)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            hits = []; o = Vector((x + 0.013, y + 0.017, 1500))
            while True:
                h = T.ray_cast(o, Vector((0, 0, -1)), 3000)[0]
                if h is None: break
                hits.append(h.z); o = h - Vector((0, 0, 0.01))
            if len(hits) >= 2: occ[i, j] = (np.array(hits)[None, :] > zs[:, None]).sum(1) % 2 == 1
    out[key] = occ
# the plate is kept as sphere samples on its mid-surface: a bent thick plate folds as a shell, spheres don't
np.savez_compressed(f"{D}/upper/uvox.npz", xs=xs, ys=ys, zs=zs, plate=np.array(SAMPLES), **out)
print("UVOX", {k: int(v.sum()) for k, v in out.items()})
