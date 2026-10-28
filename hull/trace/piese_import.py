# New pieces into Blender as separate objects (asked: PS and the arms apart): each <name>=<file.npz>:<vkey>,<fkey> (faces may
# be triangles or quads) placed where the exploded new piece is, smooth shaded, UVs from the reference (Data Transfer,
# nearest face), its material; the earlier one-piece bodies hidden. Checks per piece: free edges (open ends), non-manifold.
# Usage: blender -b <f.blend> --python piese_import.py -- <out.blend> <name=file:vkey,fkey> [...]
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
en, on = bpy.data.objects["expl_piesa_comp_169_C"], bpy.data.objects["piesa_comp_169_C"]; XN = -1700.0 + (en.location.x - on.location.x)
src = bpy.data.objects["expl_R002 169_C"]; mat = en.material_slots[0].material if en.material_slots else None
col = bpy.data.collections.get("PS_PIESE_NOI") or bpy.data.collections.new("PS_PIESE_NOI")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
c = src.copy(); c.data = src.data.copy(); bpy.context.scene.collection.objects.link(c)
c.data.transform(src.matrix_world); c.matrix_world.identity(); c.location.x = XN - (-4.68 + (src.location.x - bpy.data.objects["R002 169_C"].location.x))
for spec in a[1:]:
    name, rest = spec.split("="); fn, keys = rest.split(":"); vk, fk = keys.split(","); Z = np.load(fn); v, f = Z[vk].astype(float), Z[fk]
    for x in [o_ for o_ in bpy.data.objects if o_.name == name or o_.name.startswith(name + ".")]: bpy.data.objects.remove(x)
    me = bpy.data.meshes.new(name); me.from_pydata(v.tolist(), [], f.tolist()); me.validate()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    fb = sum(1 for e in bm.edges if e.is_boundary); nm = sum(1 for e in bm.edges if len(e.link_faces) > 2); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location.x = XN; col.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    if mat: me.materials.append(mat)
    me.uv_layers.new(name="UVMap"); md = o.modifiers.new("uv", "DATA_TRANSFER"); md.object = c; md.use_object_transform = True
    md.use_loop_data = True; md.data_types_loops = {"UV"}; md.loop_mapping = "POLYINTERP_NEAREST"
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
    print("PIESA %s: %d varfuri, %d fete; muchii libere %d, nemanifold %d" % (name, len(me.vertices), len(me.polygons), fb, nm))
bpy.data.objects.remove(c)
for n in ("piesa_169_C_sectiuni", "piesa_169_C_joc", "expl_piesa_comp_169_C"):
    o = bpy.data.objects.get(n)
    if o: o.hide_set(True); o.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
