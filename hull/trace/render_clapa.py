# The arm flap / sliding door opening before the blades and closing after (asked: the arms open before the blades come out, close after; one side
# flap): ATELIER_LAME, arm grey, flap blue, blades yellow, hinges red; oblique from below-outside, frames given. Usage: ... -- <out_prefix> <frames>
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, FR = a[0], [int(x) for x in a[1].split(",")]
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = set(bpy.data.collections["ATELIER_LAME"].objects)
for o in sc.objects: o.hide_render = o not in col
for o in col: o.color = (1, .85, 0, 1) if "_lama_" in o.name else (.85, .08, .08, 1) if "spinare" in o.name else (.1, .5, 1, 1) if ("clapa" in o.name or "usa_brat" in o.name) else (.72, .72, .75, 1)
sc.render.resolution_x, sc.render.resolution_y = 900, 680
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 30
c = Vector((-7330, 120, 200)); co.location = c + Vector((-.7, -.6, -.45)).normalized() * 1300; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
for fr in FR:
    sc.frame_set(fr); sc.render.filepath = "%s_c%03d.png" % (OUT, fr); bpy.ops.render.render(write_still=True)
