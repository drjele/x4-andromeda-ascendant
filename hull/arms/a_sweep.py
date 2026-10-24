# Arm members as swept straps (rounded-rectangle sections: width outboard-level, height up, flat top and
# bottom), voxelized by ray parity for the smooth union, with the exact distance to the strap in a band around
# its surface; the body and the V plate are voxelized too, so the roots can be filleted onto them.
import bpy, bmesh, json, math, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
sys.path.insert(0, f"{D}/arms"); from a_frame import member, frame, ring
P = json.load(open(f"{D}/arms/a_params.json"))
def tube(m):
    C, f, W, H, R = member(m); bm = bmesh.new(); rings = []; K = 48
    for i, c in enumerate(C):
        t, w, u = frame(C, i)
        rings.append([bm.verts.new(c + w * x + u * z) for x, z in ring(W[i], H[i], R[i], K)])
    for a, b in zip(rings, rings[1:]):
        for k in range(K): bm.faces.new((a[k], a[(k + 1) % K], b[(k + 1) % K], b[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); return bm
G = P["grid"]; st = G["step"]; xs = np.arange(*G["x"], st); ys = np.arange(*G["y"], st); zs = np.arange(*G["z"], st)
def parity(T):
    occ = np.zeros((len(xs), len(ys), len(zs)), bool)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            hits = []; o = Vector((x + 0.013, y + 0.017, zs[-1] + 50))
            while True:
                h = T.ray_cast(o, Vector((0, 0, -1)), 3000)[0]
                if h is None: break
                hits.append(h.z); o = h - Vector((0, 0, 0.01))
            if len(hits) >= 2: occ[i, j] = (np.array(hits)[None, :] > zs[:, None]).sum(1) % 2 == 1
    return occ
def near(T, occ, R=4):
    # the voxel distance is stepped at the grid pitch; within R cells of the surface the true distance is taken
    grow = lambda a, op: op(op(op(a, np.roll(a, 1, 0)), op(np.roll(a, -1, 0), np.roll(a, 1, 1))), op(op(np.roll(a, -1, 1), np.roll(a, 1, 2)), np.roll(a, -1, 2)))
    dil, ero = occ, occ
    for _ in range(R): dil, ero = grow(dil, np.logical_or), grow(ero, np.logical_and)
    band = dil & ~ero; d = np.zeros(occ.shape, np.float32)
    for i, j, k in zip(*np.nonzero(band)): d[i, j, k] = T.find_nearest(Vector((xs[i], ys[j], zs[k])))[3]
    return band, d.astype(np.float16)
out = {}
for name, m in P["members"].items():
    T = BVHTree.FromBMesh(tube(m)); out[name] = parity(T); out[name + "_b"], out[name + "_d"] = near(T, out[name])
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]
for key, names in P["unions"].items():
    b = bmesh.new()
    for n in names: b.from_mesh(sc.objects[n].data)
    T = BVHTree.FromBMesh(b); out[key] = parity(T); out[key + "_b"], out[key + "_d"] = near(T, out[key])
np.savez_compressed(f"{D}/arms/avox.npz", xs=xs, ys=ys, zs=zs, **out)
print("AVOX", {k: int(v.sum()) for k, v in out.items() if v.dtype == bool})
