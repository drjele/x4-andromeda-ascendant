# Texture coordinates for exploded components: the reference pieces a component replaces are copied to where that
# component sits (reference + ship offset DX + the component's exploded offset), joined, and the component's UVs carried
# over from them (Data Transfer, nearest face, interpolated); the copies are removed. Materials stay as set.
# Usage: blender -b <file.blend> --python comp_uv.py -- <out.blend> <dx> <target=src1,src2;target2=...>
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT, DX = a[0], float(a[1]); sc = bpy.context.scene
for spec in a[2].split(";"):
    tn, srcs = spec.split("="); t = bpy.data.objects[tn]; cps = []
    for n in srcs.split(","):
        o = bpy.data.objects[n]; c = o.copy(); c.data = o.data.copy(); sc.collection.objects.link(c)
        c.data.transform(o.matrix_world); c.matrix_world.identity(); c.location = t.location.copy(); c.location.x += DX; cps.append(c)
    bpy.ops.object.select_all(action="DESELECT")
    for c in cps: c.hide_set(False); c.select_set(True)
    bpy.context.view_layer.objects.active = cps[0]; bpy.ops.object.join(); src = bpy.context.view_layer.objects.active
    if not t.data.uv_layers: t.data.uv_layers.new(name="UVMap")
    md = t.modifiers.new("uv", "DATA_TRANSFER"); md.object = src; md.use_object_transform = True
    md.use_loop_data = True; md.data_types_loops = {"UV"}; md.loop_mapping = "POLYINTERP_NEAREST"
    t.hide_set(False); bpy.context.view_layer.objects.active = t; bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(src); print("UV", tn, "din", srcs)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
