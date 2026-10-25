# Local fillet pieces of the arm, step 3 of 3: each joint surface into the scene, keeping only the skin outside
# the swept arm and the hull and away from the box walls; mirrored to the left.
import bpy, bmesh, json
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{D}/arms/a_params.json")); d = np.load(f"{D}/arms/ajsurf.npz")
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc
def tree(names):
    b = bmesh.new()
    for n in names: b.from_mesh(sc.objects[n].data)
    return BVHTree.FromBMesh(b)
AT = tree(["arm_r"])
for name, J in P["joints"].items():
    for o in [o for o in sc.objects if o.name in (f"{name}_r", f"{name}_l")]: bpy.data.objects.remove(o)
    HT = tree(J["hull"]) if J.get("hull") else None; s = J["step"]
    me = bpy.data.meshes.new(f"{name}_r"); me.from_pydata(d[name + "_v"].tolist(), [], d[name + "_f"].tolist()); bm = bmesh.new(); bm.from_mesh(me); kill = []
    for vt in bm.verts:
        loc, nrm, _, _ = AT.find_nearest(vt.co); inside = (vt.co - loc).dot(nrm) < -J["depth"]
        if not inside and HT is not None:
            loc, nrm, _, _ = HT.find_nearest(vt.co); inside = (vt.co - loc).dot(nrm) < -J["depth"]
        if inside or not all(J["box"][c][0] + 2 * s < vt.co[i] < J["box"][c][1] - 3 * s for i, c in enumerate("xyz")): kill.append(vt)
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    for _ in range(J["smooth"]): bmesh.ops.smooth_vert(bm, verts=[x for x in bm.verts if not x.is_boundary], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(me)
    ob = bpy.data.objects.new(f"{name}_r", me); sc.collection.objects.link(ob)
    md = ob.modifiers.new("dec", "DECIMATE"); md.ratio = J["decimate"]
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]): bpy.ops.object.modifier_apply(modifier="dec")
    for p in me.polygons: p.use_smooth = True
    ml = me.copy(); ml.name = f"{name}_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
    sc.collection.objects.link(bpy.data.objects.new(f"{name}_l", ml)); print("JOINT", name, len(me.polygons))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
