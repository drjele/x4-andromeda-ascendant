# Textures back on every PS / arm piece (asked: "pune texturile la toate, sunt scoase"): the materials were on, the 3D views
# showed the objects' flat colour. Each piece gets its original's material (169_C/086 Material_8, 103/118 Material_6, 055
# Material_7 - counted on the reference), the views show the image textures. Linked copies (sep_*) share the meshes.
# Usage: blender -b <f.blend> --python texturi_toate.py -- <out.blend> <piece=material> ...
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
for spec in a[1:]:
    n, mn = spec.split("="); o = bpy.data.objects[n]; me = o.data
    me.materials.clear(); me.materials.append(bpy.data.materials[mn])
    for p in me.polygons: p.material_index = 0
    print("MATERIAL", n, mn, "uv" if me.uv_layers else "FARA UV")
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type == "VIEW_3D": sp.shading.type = "SOLID"; sp.shading.color_type = "TEXTURE"; sp.shading.light = "STUDIO"; sp.shading.show_cavity = True
bpy.context.scene.display.shading.color_type = "TEXTURE"
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SALVAT", OUT)
