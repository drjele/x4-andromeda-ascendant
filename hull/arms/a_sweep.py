# The arm as a direct swept surface: the rounded-rectangle strap section carried along the smoothed path at a
# uniform arc-length step, a quad tube with capped ends, subdivided once; the joints (tip pod, root into the
# crown) are separate local fillet pieces (a_joints.py), so the long runs keep their clean flow lines.
import bpy, bmesh, json, sys
import numpy as np
from mathutils import Matrix
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
sys.path.insert(0, f"{D}/arms"); from a_frame import member, frame, ring
P = json.load(open(f"{D}/arms/a_params.json")); M = P["mesh"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc
for o in [o for o in sc.objects if o.name in ("arm_r", "arm_l")]: bpy.data.objects.remove(o)
C, f, W, H, R = member(P["members"]["arm"], 10); K = M.get("ring", 48)
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]; t = np.r_[np.arange(0, s[-1], M.get("step", 6.0)), s[-1]]
Cu = np.stack([np.interp(t, s, C[:, c]) for c in range(3)], 1); Wu, Hu, Ru = (np.interp(t, s, v) for v in (W, H, R))
bm = bmesh.new(); rings = []
for i, c in enumerate(Cu):
    _, w, u = frame(Cu, i); rings.append([bm.verts.new(c + w * x + u * z) for x, z in ring(Wu[i], Hu[i], Ru[i], K)])
for a, b in zip(rings, rings[1:]):
    for k in range(K): bm.faces.new((a[k], a[(k + 1) % K], b[(k + 1) % K], b[k]))
bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("arm_r"); bm.to_mesh(me); ob = bpy.data.objects.new("arm_r", me); sc.collection.objects.link(ob)
md = ob.modifiers.new("sub", "SUBSURF"); md.levels = M.get("subdiv", 1)
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]): bpy.ops.object.modifier_apply(modifier="sub")
for p in me.polygons: p.use_smooth = True
ml = me.copy(); ml.name = "arm_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("arm_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("ARMS ok", len(me.polygons), "rings", len(rings))
