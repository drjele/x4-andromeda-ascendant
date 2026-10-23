# The nacelle on the outer flank of each lower arm: a raised rounded housing seen from outboard, with a
# recessed slot along it (where the cyan grille goes), lifted along the arm's normal.
import bpy, bmesh, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
N = json.load(open(f"{D}/arms/a_deco.json"))["nacelle"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in ("nacelle_r", "nacelle_l")]: bpy.data.objects.remove(o)
b = bmesh.new(); b.from_mesh(sc.objects["arm_r"].data); T = BVHTree.FromBMesh(b)
def rrect(Y, Z, y, z, r):
    # signed distance inside a rounded rectangle in the y-z plane (positive inside)
    cy, cz = (y[0] + y[1]) / 2, (z[0] + z[1]) / 2; hy, hz = (y[1] - y[0]) / 2 - r, (z[1] - z[0]) / 2 - r
    qy, qz = np.abs(Y - cy) - hy, np.abs(Z - cz) - hz
    out = np.hypot(np.maximum(qy, 0), np.maximum(qz, 0)) + np.minimum(np.maximum(qy, qz), 0) - r
    return -out
S = N["slot"]; M = 14
ys = np.arange(N["y"][0] - M, N["y"][1] + M, 1.5); zs = np.arange(N["z"][0] - M, N["z"][1] + M, 1.5); Y, Z = np.meshgrid(ys, zs)
d = rrect(Y, Z, N["y"], N["z"], 22)
u = np.clip(d / N["rim"], 0, 1); L = N["lift"] * np.sin(u * np.pi / 2)
ds = rrect(Y, Z, S["y"], S["z"], 10); us = np.clip(ds / S["rim"], 0, 1); L = L - S["depth"] * us * us * (3 - 2 * us)
L = L - 0.8 * (d < 0)
bm = bmesh.new(); G = {}
for i in range(len(zs)):
    for j in range(len(ys)):
        hit, nrm, _, _ = T.ray_cast(Vector((1200, ys[j], zs[i])), Vector((-1, 0, 0)), 1500)
        if hit is not None: G[(i, j)] = bm.verts.new(hit + nrm * float(L[i, j]))
for (i, j) in list(G):
    q = [G.get((i, j)), G.get((i, j + 1)), G.get((i + 1, j + 1)), G.get((i + 1, j))]
    if None not in q: bm.faces.new(q)
for _ in range(2): bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("nacelle_r"); bm.to_mesh(me)
for p in me.polygons: p.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("nacelle_r", me))
ml = me.copy(); ml.name = "nacelle_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("nacelle_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("NACELLE ok")
