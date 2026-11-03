# The blade animation in stills (asked: one rotation from hinge 7, animated): ship grey with red nacelles, the blades yellow, at the
# given frames, from above, oblique front and from below. Usage: blender -b <f.blend> --python render_lama_anim.py -- <out_prefix> <frames,...>
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, FR = a[0], [int(q) for q in a[1].split(",")]
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = bpy.data.collections["ASAMBLAT_NOU"].objects
for o in sc.objects: o.hide_render = o not in set(col)
for o in col: o.color = (1, .85, 0, 1) if o.name.startswith("an_lama") else (.45, .04, .04, 1) if "nacela_inchis" in o.name else (.9, .4, .4, 1) if "nacela_deschis" in o.name else (.72, .72, .75, 1)
sc.render.resolution_x, sc.render.resolution_y = 900, 700
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 40
c = Vector((-1600, 380, 200))
for fr in FR:
    sc.frame_set(fr)
    for n, d, R in (("sus", (0, -.05, 1), 1500), ("oblic", (-.5, 1, .55), 1250), ("jos", (-.4, .8, -.6), 1150)):
        co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = "%s_f%03d_%s.png" % (OUT, fr, n); bpy.ops.render.render(write_still=True)
