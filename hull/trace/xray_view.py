# Viewport set to see a piece's outline through the others (asked: focus on lama_stransa_S when reopening, to see its contour):
# X-ray on in every 3D view (alpha XA), solid shading, the given object selected / active and every other object deselected.
# Usage: blender -b <f.blend> --python xray_view.py -- <object[,object...]> ; env XA=0.35 (saves the file in place; the first one active)
import bpy, sys, os
n = sys.argv[sys.argv.index("--") + 1]; xa = float(os.environ.get("XA", .35))
for o in bpy.context.scene.objects: o.select_set(False)
for k in n.split(","): bpy.data.objects[k].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects[n.split(",")[0]]
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type == "VIEW_3D": sp.shading.type = "SOLID"; sp.shading.show_xray = True; sp.shading.xray_alpha = xa
bpy.ops.wm.save_mainfile(); print("XRAY", n, xa)
