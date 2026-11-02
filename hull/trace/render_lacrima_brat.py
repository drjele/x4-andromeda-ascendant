# The front arm's teardrop up close (asked: clean lines on the decorations - compare old / new): arm grey, teardrop dark, R060 panel
# light, from above, from the side (outside of the arm) and along the arm from the tip.
# Usage: blender -b <f.blend> --python render_lacrima_brat.py -- <out_prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = {"an_brat_fata_S": (.75, .75, .78), "an_lacrima_brat_S": (.25, .3, .45), "an_decor_R060_S": (.85, .8, .6), "an_nacela_inchis_S": (.4, .05, .05), "an_nacela_deschis_S": (.9, .4, .4)}
for o in sc.objects:
    o.hide_render = o.name not in col
    if o.name in col: o.color = (*col[o.name], 1)
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 20000; cam.lens = 35
c = Vector((-520 - 1600, 1100, -140))
for n, d, R in (("sus", (0, -.15, 1), 750), ("lateral", (-1, -.1, .35), 650), ("din_varf", (-.25, 1, .45), 650), ("lob", (-.8, .4, .3), 320)):
    cc = Vector((-560 - 1600, 1450, -230)) if n == "lob" else c
    co.location = cc + Vector(d).normalized() * R; co.rotation_euler = (cc - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
