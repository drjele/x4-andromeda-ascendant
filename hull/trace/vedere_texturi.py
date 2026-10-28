# The saved file opens with the real textures in the 3D views (solid shading, colour from the image textures, cavity), not
# the materials' flat (dark) base colour. Usage: blender -b <f.blend> --python vedere_texturi.py
import bpy
for scr in bpy.data.screens:
    for ar in scr.areas:
        if ar.type == "VIEW_3D":
            for sp in ar.spaces:
                if sp.type == "VIEW_3D": sp.shading.type = "SOLID"; sp.shading.color_type = "TEXTURE"; sp.shading.light = "STUDIO"; sp.shading.show_cavity = True
bpy.context.scene.display.shading.color_type = "TEXTURE"; bpy.ops.wm.save_mainfile(); print("VEDERE cu texturi")
