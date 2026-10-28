# The whole body from one field (sectiuni_corp_tot.py) into Blender as the new PS body: one object, no stitch, placed where
# the exploded new piece is (that one hidden), UVs from the reference (Data Transfer, nearest face) and its material.
# Checks: free edges, non-manifold edges, roughness (95 % of neighbour-face angles).
# Usage: blender -b <f.blend> --python sectiuni_import2.py -- <corp_tot.npz> <out.blend> [name]
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; Z = np.load(a[0]); OUT = a[1]; NAME = a[2] if len(a) > 2 else "piesa_169_C_sectiuni"
en, on = bpy.data.objects["expl_piesa_comp_169_C"], bpy.data.objects["piesa_comp_169_C"]; XN = -1700.0 + (en.location.x - on.location.x)
for x in [o_ for o_ in bpy.data.objects if o_.name == NAME or o_.name.startswith(NAME + ".")]: bpy.data.objects.remove(x)   # the earlier version first
me = bpy.data.meshes.new(NAME); v, f = Z["v"].astype(float), Z["f"]
me.vertices.add(len(v)); me.vertices.foreach_set("co", v.ravel()); me.loops.add(len(f) * 3); me.loops.foreach_set("vertex_index", f.ravel())
me.polygons.add(len(f)); me.polygons.foreach_set("loop_start", np.arange(0, len(f) * 3, 3)); me.polygons.foreach_set("loop_total", np.full(len(f), 3))
me.update(); me.validate()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
fb = sum(1 for e in bm.edges if e.is_boundary); nm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
ang = np.degrees([e.calc_face_angle(0) for e in bm.edges if len(e.link_faces) == 2]); bm.to_mesh(me); bm.free()
o = bpy.data.objects.new(NAME, me); o.location.x = XN
col = bpy.data.collections.get("PS_SECTIUNI") or bpy.data.collections.new("PS_SECTIUNI")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
col.objects.link(o)
for p in me.polygons: p.use_smooth = True
if en.material_slots: me.materials.append(en.material_slots[0].material)
src = bpy.data.objects["expl_R002 169_C"]; c = src.copy(); c.data = src.data.copy(); bpy.context.scene.collection.objects.link(c)
c.data.transform(src.matrix_world); c.matrix_world.identity(); c.location.x = XN - (-4.68 + (src.location.x - bpy.data.objects["R002 169_C"].location.x))
me.uv_layers.new(name="UVMap"); md = o.modifiers.new("uv", "DATA_TRANSFER"); md.object = c; md.use_object_transform = True
md.use_loop_data = True; md.data_types_loops = {"UV"}; md.loop_mapping = "POLYINTERP_NEAREST"
bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name); bpy.data.objects.remove(c)
en.hide_set(True); en.hide_render = True
print("CORP %s: %d varfuri, %d fete; muchii libere %d, nemanifold %d; asperitate 95%% %.1f grade, max %.0f" % (NAME, len(me.vertices), len(me.polygons), fb, nm, np.percentile(ang, 95), ang.max()))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
