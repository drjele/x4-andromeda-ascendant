import bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc
for o in sc.objects:
    if o.type != "MESH": continue
    rgb = (0.75, 0.75, 0.78) if o.name == "source" else (0.9, 0.3, 0.45) if o.name == "uarch" else (0.35, 0.55, 0.95) if o.name.startswith("arm") else (0.25, 0.75, 0.45) if o.name.startswith("link") else (0.82, 0.62, 0.4)
    mm = bpy.data.materials.new(o.name); mm.diffuse_color = (*rgb, 1); o.data.materials.clear(); o.data.materials.append(mm)
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.render.resolution_x, sc.render.resolution_y = 1000, 800
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 2000; cam.data.clip_end = 20000
src = sc.objects["source"]
for v, loc, tgt, os_ in [("front", (0, 5000, -100), (0, 0, -100), 1800), ("under", (0, -350, -5000), (0, -350, 0), 2200), ("side", (5000, -350, -100), (0, -350, -100), 2200), ("q", (1800, 900, -1300), (0, -400, -200), 2400)]:
    cam.data.ortho_scale = os_; cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    for t, show in (("a", False), ("b", True)):
        src.hide_render = not show
        sc.render.filepath = f"/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/uarch/gv_{v}_{t}.png"; bpy.ops.render.render(write_still=True)
