import bpy, json, math
from mathutils import Vector
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body"
bpy.ops.wm.open_mainfile(filepath=f"/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc
P = json.load(open(f"{D}/parts.json"))
for name, (l, rgb) in P.items():
    if name not in sc.objects: continue
    m = bpy.data.materials.new(name); m.diffuse_color = (*rgb, 1); sc.objects[name].data.materials.clear(); sc.objects[name].data.materials.append(m)
sc.objects["source"].hide_render = True
import os
SHOWSRC = True
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.render.resolution_x, sc.render.resolution_y = 1000, 600
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50; cam.data.clip_end = 20000
for v, loc, tgt in (("hero", (900, 1700, 450), (40, 750, -60)), ("side", (1400, 750, -40), (0, 750, -60)), ("front", (300, 2100, 100), (0, 900, -60)), ("top", (0, 780, 900), (0, 790, -60)), ("prof", (1300, 850, -60), (0, 850, -60)), ("srcprof", (1300, 850, -60), (0, 850, -60))):
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.objects["source"].hide_render = v != "srcprof"
    if v == "srcprof":
        for o in sc.objects:
            if o.name not in ("source", "corp", "c"): o.hide_render = True
        ms = bpy.data.materials.new("sw"); ms.diffuse_color = (0.3, 0.3, 0.35, 1); src = sc.objects["source"]; src.data.materials.clear(); src.data.materials.append(ms)
        sc.display.shading.show_xray = True; sc.display.shading.xray_alpha = 0.5
    sc.render.filepath = f"{D}/nose_{v}.png"; bpy.ops.render.render(write_still=True)
