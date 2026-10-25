# A .blend for the user: one frozen version shown in the part colours, another loaded hidden for comparison.
# Usage: blender -b --python version_scene.py -- <shown> <hidden> <out.blend>
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]; SHOW, HIDE, OUT = a; T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{T}/body/parts.json")); bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
for V in (SHOW, HIDE):
    with bpy.data.libraries.load(f"{T}/versions/{V}.blend") as (src, dst): dst.collections = [src.collections[0]]
    col = [c for c in bpy.data.collections if c.library is None and c.name == V][0]; sc.collection.children.link(col)
    for o in col.objects:
        name = o.name.split("_", 1)[1]; label, rgb = P.get(name, ["?", (0.7, 0.7, 0.7)]); o.name = f"{V} {label} {name}"
        m = bpy.data.materials.new(o.name); m.diffuse_color = (*rgb, 1); o.data.materials.clear(); o.data.materials.append(m)
bpy.context.view_layer.layer_collection.children[HIDE].hide_viewport = True
for scr in bpy.data.screens:
    for area in [x for x in scr.areas if x.type == "VIEW_3D"]:
        # the ship is ~3 km: the default 1 km clip range cuts it when zooming
        sp = area.spaces[0]; sp.clip_start = 1.0; sp.clip_end = 60000; sp.shading.type = "SOLID"; sp.shading.color_type = "MATERIAL"
        sp.overlay.show_floor = False; sp.region_3d.view_distance = 4200; sp.region_3d.view_location = (0, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("VERSION SCENE ok")
