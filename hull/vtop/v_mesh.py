import bpy, bmesh, json
import numpy as np
from mathutils import Vector
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/vtop"
d = np.load(f"{D}/vplate.npz"); xs, ys, m, mid, half = d["xs"], d["ys"], d["mask"], d["mid"], d["half"]
bpy.ops.wm.open_mainfile(filepath="/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body/body_v2.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name == "v_plate"]: bpy.data.objects.remove(o)
bm = bmesh.new(); T = {}; B = {}
for i in range(len(ys)):
    for j in range(len(xs)):
        if not m[i, j]: continue
        T[(i, j)] = bm.verts.new((xs[j], ys[i], mid[i, j] + half[i, j]))
        B[(i, j)] = bm.verts.new((xs[j], ys[i], mid[i, j] - half[i, j]))
for i in range(len(ys) - 1):
    for j in range(len(xs) - 1):
        q = [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]
        if not all(x in T for x in q): continue
        bm.faces.new([T[x] for x in q]); bm.faces.new([B[x] for x in q][::-1])
# seal the rim: boundary top and bottom verts sit together, merge them
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.3)
bmesh.ops.dissolve_degenerate(bm, dist=0.05, edges=bm.edges[:])
# rim band: 8 rings in from the outline, relaxed in all axes so the grid staircase disappears;
# the flat underside is held in z, so it stays a plane
ring = {v for v in bm.verts if v.is_boundary}; band = set(ring); front = set(ring)
for _ in range(8):
    front = {o for v in front for e in v.link_edges for o in e.verts} - band; band |= front
under = {v for v in bm.verts if all(f.normal.z < -0.7 for f in v.link_faces) and v.link_faces}
bm.normal_update()
under = {v for v in band if v.link_faces and sum(f.normal.z for f in v.link_faces) / len(v.link_faces) < -0.9}
for _ in range(25):
    bmesh.ops.smooth_vert(bm, verts=list(band - under), factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bmesh.ops.smooth_vert(bm, verts=list(under), factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=False)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("v_plate"); bm.to_mesh(me)
for p in me.polygons: p.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("v_plate", me))
bpy.data.libraries.write(f"{D}/v_scene.blend", {sc}, fake_user=True)
print("VPLATE", len(me.polygons))
