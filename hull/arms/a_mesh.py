# The arm surface into the scene: what lies inside the body or the V plate is dropped, so the root fillets
# end just under their skin, then the triangles are collapsed to an even mesh; the left arm mirrors the right.
import bpy, bmesh, json
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{D}/arms/a_params.json")); d = np.load(f"{D}/arms/asurf.npz")
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in ("arm_r", "arm_l")]: bpy.data.objects.remove(o)
trees = []
for n in sum(P["unions"].values(), []):
    b = bmesh.new(); b.from_mesh(sc.objects[n].data); trees.append(BVHTree.FromBMesh(b))
me = bpy.data.meshes.new("arm_r"); me.from_pydata(d["v"].tolist(), [], d["f"].tolist())
bm = bmesh.new(); bm.from_mesh(me)
kill = []
for v in bm.verts:
    for T in trees:
        loc, nrm, _, _ = T.find_nearest(v.co)
        if loc is not None and (v.co - loc).dot(nrm) < -P["mesh"]["depth"]: kill.append(v); break
bmesh.ops.delete(bm, geom=kill, context="VERTS")
for _ in range(P["mesh"]["smooth"]): bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.to_mesh(me)
ob = bpy.data.objects.new("arm_r", me); sc.collection.objects.link(ob)
# the marching-cubes slivers shade in bands; collapsing them to fewer, even triangles shades smoothly
bpy.context.window.scene = sc; md = ob.modifiers.new("dec", "DECIMATE"); md.ratio = P["mesh"]["decimate"]
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]): bpy.ops.object.modifier_apply(modifier="dec")
for p in me.polygons: p.use_smooth = True
ml = me.copy(); ml.name = "arm_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("arm_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("ARMS ok", len(me.polygons))
