# The spiral-staircase blades (asked: round pivots perpendicular to PS, two spines, blades come down out of the front arms then turn):
# ATELIER_DESCHISE and ATELIER_STRANSE - ship grey, blades yellow, spines red; each from above, below and oblique below. Usage: ... -- <out_prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = set(bpy.data.collections["ATELIER_DESCHISE"].objects) | set(bpy.data.collections["ATELIER_STRANSE"].objects)
for o in sc.objects: o.hide_render = o not in col
for o in col: o.color = (1, .85, 0, 1) if o.name[2:].startswith("lama") else (.85, .08, .08, 1) if "spinare" in o.name else (.45, .04, .04, 1) if "nacela_inchis" in o.name else (.9, .4, .4, 1) if "nacela_deschis" in o.name else (.72, .72, .75, 1)
sc.render.resolution_x, sc.render.resolution_y = 1000, 760
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 35
for pre, x in (("deschise", -9000), ("stranse", -11000)):
    for n, c, d, R in (("sus", (x, 150, 150), (0, -.05, 1), 2300), ("jos", (x, 150, 150), (0, -.05, -1), 2300), ("oblic_jos", (x, 150, 200), (-.5, .7, -.6), 1600)):
        c = Vector(c); co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = "%s_%s_%s.png" % (OUT, pre, n); bpy.ops.render.render(write_still=True)
