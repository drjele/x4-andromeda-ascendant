# The U arch into the scene: what lies inside the arms is dropped, so the end fillets end just under their
# skin, then the triangles are collapsed to an even mesh; one symmetric piece from arm to arm.
import bpy, bmesh, json
import numpy as np
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{D}/uarch/g_params.json")); d = np.load(f"{D}/uarch/gsurf.npz")
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name == "uarch"]: bpy.data.objects.remove(o)
trees = []
for n in sum(P["unions"].values(), []):
    b = bmesh.new(); b.from_mesh(sc.objects[n].data); trees.append(BVHTree.FromBMesh(b))
me = bpy.data.meshes.new("uarch"); me.from_pydata(d["v"].tolist(), [], d["f"].tolist())
bm = bmesh.new(); bm.from_mesh(me)
kill = []
for v in bm.verts:
    for T in trees:
        loc, nrm, _, dist = T.find_nearest(v.co)
        # the arms are open at their roots, so the side test only counts close to their skin
        if loc is not None and dist < P["mesh"]["cap"] and (v.co - loc).dot(nrm) < -P["mesh"]["depth"]: kill.append(v); break
bmesh.ops.delete(bm, geom=kill, context="VERTS")
for _ in range(P["mesh"]["smooth"]): bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.to_mesh(me)
ob = bpy.data.objects.new("uarch", me); sc.collection.objects.link(ob)
# the marching-cubes slivers shade in bands; collapsing them to fewer, even triangles shades smoothly
bpy.context.window.scene = sc; md = ob.modifiers.new("dec", "DECIMATE"); md.ratio = P["mesh"]["decimate"]
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]): bpy.ops.object.modifier_apply(modifier="dec")
for p in me.polygons: p.use_smooth = True
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("UARCH ok", len(me.polygons))
