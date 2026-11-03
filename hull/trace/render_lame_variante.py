# Blade variants open / stowed on the ship (asked: blades slide out of the red nacelles; try both shapes): for each state only that
# blade pair shown (red) with the ship grey and the nacelles in their reds; from above, oblique front-above and oblique front-below.
# Usage: blender -b <f.blend> --python render_lame_variante.py -- <out_prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
blades = {"A_deschis": "an_lama_nacela_%s", "A_strans": "an_lama_nacela_%s_strans", "B_deschis": "an_lama_%s", "B_strans": "an_lama_%s_strans"}
allb = {b % sd for b in blades.values() for sd in "SD"}
ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if o.name not in allb]
for o in ship: o.color = (.45, .04, .04, 1) if "nacela_inchis" in o.name else (.9, .4, .4, 1) if "nacela_deschis" in o.name else (.72, .72, .75, 1)
sc.render.resolution_x, sc.render.resolution_y = 1200, 900
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 40
c = Vector((-1600 - 250, 420, 200))
for st, pat in blades.items():
    show = set(ship) | {bpy.data.objects[pat % sd] for sd in "SD"}
    for o in sc.objects: o.hide_render = o not in show
    for sd in "SD": bpy.data.objects[pat % sd].color = (1, .05, .05, 1)
    for n, d, R in (("sus", (0, -.05, 1), 1200), ("oblic", (-.5, 1, .55), 1100), ("jos", (-.5, .8, -.6), 1000)):
        co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = "%s_%s_%s.png" % (OUT, st, n); bpy.ops.render.render(write_still=True)
