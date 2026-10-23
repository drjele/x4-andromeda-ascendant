# Voxel fields of the body and of the arm, swept on all three axes: the inside parity (a vote of the three sweeps, so a
# ray grazing an edge cannot leave a false column) and the along-axis distance to the nearest crossing, so
# the signed distance is sub-voxel exact near the surface, not stepped.
import bpy, bmesh, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
G = json.load(open(f"{D}/links/l_params.json"))["grid"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
trees = {}
for key, n in (("body", "corp"), ("arm", "arm_r")):
    b = bmesh.new(); b.from_mesh(bpy.data.scenes["seg"].objects[n].data); trees[key] = BVHTree.FromBMesh(b)
s = G["step"]; A = [np.arange(G["x"][0], G["x"][1], s), np.arange(G["y"][0], G["y"][1], s), np.arange(G["z"][0], G["z"][1], s)]
shape = tuple(len(a) for a in A); FAR = 200.0
def sweep(T, ax, acc, occ):
    u, v = [i for i in range(3) if i != ax]; t = A[ax]; dv = Vector((0, 0, 0)); dv[ax] = -1.0
    for i, a in enumerate(A[u]):
        for j, b in enumerate(A[v]):
            o = Vector((0, 0, 0)); o[u] = a + 0.013; o[v] = b + 0.017; o[ax] = t[-1] + 50; hits = []
            while True:
                h = T.ray_cast(o, dv, 2000)[0]
                if h is None: break
                hits.append(h[ax]); o = h + dv * 0.01
            if not hits: continue
            hz = np.array(hits); idx = [slice(None)] * 3; idx[u] = i; idx[v] = j; idx = tuple(idx)
            acc[idx] += 1.0 / np.abs(t[:, None] - hz[None, :]).min(1) ** 2
            if len(hz) >= 2: occ[idx] += (hz[None, :] > t[:, None]).sum(1) % 2 == 1
out = {}
for key, T in trees.items():
    acc = np.zeros(shape, np.float64); votes = np.zeros(shape, np.uint8)
    for ax in (2, 0, 1): sweep(T, ax, acc, votes)
    occ = votes >= 2
    # the intercepts on the three axes give the distance to the local tangent plane
    with np.errstate(divide="ignore"): dist = np.minimum(1.0 / np.sqrt(acc), FAR)
    if key == "arm":
        # only the arm's outer run counts: its roots are open shells (cut at the hull) that fool the parity
        keep = (A[0] > G["arm_x_min"])[:, None, None]; occ = occ & keep; dist = np.where(keep, dist, FAR)
    out[key] = occ; out[key + "_d"] = dist.astype(np.float16)
np.savez_compressed(f"{D}/links/lvox.npz", xs=A[0], ys=A[1], zs=A[2], **out)
print("LVOX", {k: int(v.sum()) for k, v in out.items() if v.dtype == bool})
