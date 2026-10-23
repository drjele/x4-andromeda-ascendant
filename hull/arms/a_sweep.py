# Arm members as swept tubes with elliptical sections (width outboard-level, height up), voxelized by
# ray parity for the smooth union, with the exact distance to the tube in a band around its surface; the
# body and the V plate are voxelized too, so the roots can be filleted onto them.
import bpy, bmesh, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{D}/arms/a_params.json"))
def catmull(pts, n):
    p = np.array(pts, float); p = np.vstack([p[:1], p, p[-1:]]); out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1:i + 3]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    out.append(p[-2]); return np.array(out)
def tube(m):
    C = catmull(m["path"], 10); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]; f = s / s[-1]
    S = np.array(m["sections"], float); W = np.interp(f, S[:, 0], S[:, 1]); H = np.interp(f, S[:, 0], S[:, 2])
    bm = bmesh.new(); rings = []; K = 32
    for i, c in enumerate(C):
        t = C[min(i + 1, len(C) - 1)] - C[max(i - 1, 0)]; t /= np.linalg.norm(t)
        w = np.cross(t, [0, 0, 1.0]); w = w / np.linalg.norm(w) if np.linalg.norm(w) > 1e-3 else np.array([1.0, 0, 0]); u = np.cross(w, t)
        rings.append([bm.verts.new(c + w * W[i] / 2 * math.cos(a) + u * H[i] / 2 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, K, endpoint=False)])
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
