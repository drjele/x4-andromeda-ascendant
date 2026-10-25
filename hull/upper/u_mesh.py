# Upper wings: the union surface minus what lies on or inside the body and the arm; mirrored to the left.
import bpy, bmesh, json
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{D}/upper/u_params.json"))["mesh"]; d = np.load(f"{D}/upper/usurf.npz")
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in ("upper_r", "upper_l")]: bpy.data.objects.remove(o)
trees = []
for names, cap in ((json.load(open(f"{D}/upper/u_params.json")).get("bases", ["corp"]), 1e9), (["arm_r"], P["cap"])):
    b = bmesh.new()
    for n in names: b.from_mesh(sc.objects[n].data)
    trees.append((BVHTree.FromBMesh(b), cap))
me = bpy.data.meshes.new("upper_r"); me.from_pydata(d["v"].tolist(), [], d["f"].tolist())
bm = bmesh.new(); bm.from_mesh(me)
kill = []
for v in bm.verts:
    for T, cap in trees:
        loc, nrm, _, dist = T.find_nearest(v.co)
        # the arm is open at its roots, so its side test only counts close to its skin
        if loc is not None and dist < cap and (v.co - loc).dot(nrm) < 0.8: kill.append(v); break
bmesh.ops.delete(bm, geom=kill, context="VERTS")
for _ in range(P["smooth"]): bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.to_mesh(me)
ob = bpy.data.objects.new("upper_r", me); sc.collection.objects.link(ob)
# the marching-cubes slivers shade in bands; collapsing them to fewer, even triangles shades smoothly
bpy.context.window.scene = sc; md = ob.modifiers.new("dec", "DECIMATE"); md.ratio = P["decimate"]
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]): bpy.ops.object.modifier_apply(modifier="dec")
for p in me.polygons: p.use_smooth = True
ml = me.copy(); ml.name = "upper_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("upper_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("UPPER ok", len(me.polygons))
