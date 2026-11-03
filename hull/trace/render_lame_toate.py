# All blades open / stowed (asked: open front and back to see how they look): our ship grey with red nacelles, blades yellow; and the
# reference (blades red) for comparison; at frame FR: above, oblique front, oblique back, below. Usage: ... -- <out_prefix> <FR> [ref]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, FR = a[0], int(a[1]); REF = len(a) > 2
sc = bpy.context.scene; sc.frame_set(FR); sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
objs = set(bpy.data.collections["REFERINTA" if REF else "ASAMBLAT_NOU"].all_objects)
for o in sc.objects: o.hide_render = o not in objs
for o in objs:
    if REF: o.color = (1, .85, 0, 1) if o.name.startswith("Circle") else (.72, .72, .75, 1)
    else: o.color = (1, .85, 0, 1) if o.name.startswith("an_lama") else (.45, .04, .04, 1) if "nacela_inchis" in o.name else (.9, .4, .4, 1) if "nacela_deschis" in o.name else (.72, .72, .75, 1)
sc.render.resolution_x, sc.render.resolution_y = 900, 700
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 35
c = Vector((0 if REF else -1600, 150, 150))
for n, d, R in (("sus", (0, -.05, 1), 2300), ("oblic_fata", (-.45, 1, .55), 2000), ("oblic_spate", (-.5, -1, .6), 2000), ("jos", (-.3, .4, -1), 2100)):
    co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
