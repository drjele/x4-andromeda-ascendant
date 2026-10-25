# Local fillet pieces of the arm, step 1 of 3: voxels (ray parity) of the swept arm, the extra tube members and
# the hull inside each joint's box (the tip pod and the root into the crown), written for a_joints_sdf.py.
import bpy, bmesh, json, math, sys
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
sys.path.insert(0, f"{D}/arms"); from a_frame import member, frame, ring
P = json.load(open(f"{D}/arms/a_params.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc
def tree(names):
    b = bmesh.new()
    for n in names: b.from_mesh(sc.objects[n].data)
    return BVHTree.FromBMesh(b)
def tube(m):
    C, f, W, H, R = member(m); bm = bmesh.new(); rings = []; K = 32
    for i, c in enumerate(C):
        _, w, u = frame(C, i); rings.append([bm.verts.new(c + w * x + u * z) for x, z in ring(W[i], H[i], R[i], K)])
    for a, b in zip(rings, rings[1:]):
        for k in range(K): bm.faces.new((a[k], a[(k + 1) % K], b[(k + 1) % K], b[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); return BVHTree.FromBMesh(bm)
def parity(T, xs, ys, zs):
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
AT = tree(["arm_r"]); out = {}
for name, J in P["joints"].items():
    s = J["step"]; xs, ys, zs = (np.arange(*J["box"][c], s) for c in ("x", "y", "z"))
    out[name + "_arm"] = parity(AT, xs, ys, zs)
    for m in J.get("members", []): out[f"{name}_m_{m}"] = parity(tube(P["members"][m]), xs, ys, zs)
    if J.get("hull"): out[name + "_hull"] = parity(tree(J["hull"]), xs, ys, zs)
np.savez_compressed(f"{D}/arms/ajoints.npz", **out); print("AJOINTS", {k: int(v.sum()) for k, v in out.items()})
