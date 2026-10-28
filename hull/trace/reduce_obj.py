# A regenerated shell reduced to a triangle budget with Blender's error-driven collapse (symmetric in x), shaded smooth with
# an auto-smooth angle (sharp edges stay sharp), written back as OBJ.
# Usage: blender -b --python reduce_obj.py -- <in.obj> <out.obj> <target_tris>
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; IN, OUT, TGT = a[0], a[1], int(a[2])
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.wm.obj_import(filepath=IN, forward_axis="Y", up_axis="Z")
o = bpy.context.selected_objects[0]; bpy.context.view_layer.objects.active = o; n0 = len(o.data.polygons)
md = o.modifiers.new("d", "DECIMATE"); md.ratio = min(1.0, TGT / n0); md.use_symmetry = True; md.symmetry_axis = "X"; bpy.ops.object.modifier_apply(modifier=md.name)
bpy.ops.object.shade_smooth_by_angle(angle=0.6)
bpy.ops.wm.obj_export(filepath=OUT, forward_axis="Y", up_axis="Z", export_materials=False, export_normals=True, export_uv=False)
print("REDUS %d -> %d" % (n0, len(o.data.polygons)))
