# See-through check of a ship: rendered flat from the 6 axis directions with back faces hidden and shown; where they
# differ the camera sees a back face (a hole or a face turned inside out), which the game would show as a hole.
# Usage: blender -b <file.blend> --python hole_check.py -- <out_prefix> <collection_prefix>  (compare *_cull vs *_all)
import bpy, sys, math
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PREF = a
sc = bpy.context.scene
for c in sc.collection.children: bpy.context.view_layer.layer_collection.children[c.name].exclude = not c.name.startswith(PREF)
for o in sc.objects:
    if o.type == "FONT": o.hide_render = True
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = 900; sc.render.resolution_y = 900
sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "SINGLE"; sh.single_color = (1, 1, 1); sc.render.film_transparent = False
sc.world = sc.world or bpy.data.worlds.new("w"); sh.background_type = "VIEWPORT"; sh.background_color = (0, 0, 0)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = "ORTHO"; cam.data.ortho_scale = 3000; cam.data.clip_end = 30000
X = 900 if PREF.startswith("B") else -900
views = {"sus": ((X, 0, 6000), (0, 0, 0)), "jos": ((X, 0, -6000), (math.pi, 0, 0)), "stanga": ((X - 6000, 0, 0), (math.pi / 2, 0, -math.pi / 2)), "dreapta": ((X + 6000, 0, 0), (math.pi / 2, 0, math.pi / 2)), "fata": ((X, 6000, 0), (math.pi / 2, 0, math.pi)), "spate": ((X, -6000, 0), (math.pi / 2, 0, 0))}
for n, (loc, rot) in views.items():
    cam.location = loc; cam.rotation_euler = rot
    for cull in (True, False):
        sh.show_backface_culling = cull; sc.render.filepath = f"{OUT}_{n}_{'cull' if cull else 'all'}.png"; bpy.ops.render.render(write_still=True)
