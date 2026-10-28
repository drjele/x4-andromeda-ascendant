# The two reference models and our model, all at the average proportions, side by side in one Blender scene (spaced
# across x), each in its own collection with the author in the name, plus a text with the credits; saved and rendered
# from above, the side, behind and at an angle.
# Usage: blender -b --python scene_side_by_side.py -- <out.blend> <render_prefix> <name>=<obj> ...
import bpy, sys, math
a = sys.argv[sys.argv.index("--") + 1:]; OUT, RP = a[:2]; ITEMS = [x.split("=", 1) for x in a[2:]]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
cols = [(1, 0.35, 1, 1), (0.2, 0.9, 0.8, 1), (1, 0.75, 0.3, 1)]; GAP = 1700
for k, (name, path) in enumerate(ITEMS):
    c = bpy.data.collections.new(name); sc.collection.children.link(c)
    bpy.ops.wm.obj_import(filepath=path, forward_axis="Y", up_axis="Z"); m = bpy.data.materials.new(name); m.diffuse_color = cols[k % 3]
    for o in bpy.context.selected_objects:
        for cc in o.users_collection: cc.objects.unlink(o)
        c.objects.link(o); o.location.x += (k - (len(ITEMS) - 1) / 2) * GAP; o.data.materials.clear(); o.data.materials.append(m)
    t = bpy.data.curves.new(name, "FONT"); t.body = name; to = bpy.data.objects.new("eticheta_" + name, t); c.objects.link(to)
    to.location = ((k - (len(ITEMS) - 1) / 2) * GAP - 500, -1700, 0); to.scale = (90, 90, 90)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = 1800; sc.render.resolution_y = 900; sc.display.shading.color_type = "MATERIAL"
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = "ORTHO"; cam.data.ortho_scale = 5400; cam.data.clip_end = 30000
for n, loc, rot in [("sus", (0, -100, 8000), (0, 0, 0)), ("fata_3_4", (-3000, 6500, 3500), (math.radians(62), 0, math.radians(200))), ("spate_3_4", (3000, -6500, 3500), (math.radians(62), 0, math.radians(20)))]:
    cam.location = loc; cam.rotation_euler = rot; sc.render.filepath = f"{RP}_{n}.png"; bpy.ops.render.render(write_still=True)
print("SAVED", OUT)
