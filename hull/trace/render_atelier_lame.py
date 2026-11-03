# The blade workshop rendered (asked: iterate until they animate right; show front and back open): ATELIER_LAME only - hosts grey,
# nacelles red, our blades yellow, the reference blades (ref_lama_*) translucent-looking dark grey for comparison when open; at the
# given frame: above, oblique front, oblique back, below. Usage: ... -- <out_prefix> <frame> [noref]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, FR = a[0], int(a[1]); NOREF = len(a) > 2
sc = bpy.context.scene; sc.frame_set(FR); sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = set(bpy.data.collections["ATELIER_LAME"].objects)
for o in sc.objects: o.hide_render = o not in col or (NOREF and o.name.startswith("ref_lama"))
for o in col: o.color = (1, .85, 0, 1) if o.name.startswith("at_lama") else (.25, .25, .3, 1) if o.name.startswith("ref_lama") else (.45, .04, .04, 1) if "nacela_inchis" in o.name else (.9, .4, .4, 1) if "nacela_deschis" in o.name else (.72, .72, .75, 1)
sc.render.resolution_x, sc.render.resolution_y = 900, 700
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 35
c = Vector((-7000, 100, 150))
for n, d, R in (("sus", (0, -.05, 1), 2400), ("oblic_fata", (-.45, 1, .55), 2100), ("oblic_spate", (-.5, -1, .6), 2100), ("jos", (-.3, .4, -1), 2200)):
    co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
