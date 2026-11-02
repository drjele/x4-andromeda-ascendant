# The 055 pad on PS up close (asked: clean lines on the decorations - 055 had a shaky outline and an end cut straight): PS grey,
# 055 dark, hood and ear light; from above, oblique from the front and the back, low from the side.
# Usage: blender -b <f.blend> --python render_055.py -- <out_prefix> [centre x,y,z ship = -49,375,300]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; C = Vector([float(q) for q in (a[1] if len(a) > 1 else "-49,375,300").split(",")]); sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = {"an_PS": (.75, .75, .78), "an_PS_rama": (.7, .7, .74), "an_comp_055_S": (.25, .3, .45), "an_capac_086": (.85, .8, .6), "an_ureche_S": (.7, .72, .78), "an_brat_fata_S": (.7, .72, .78)}
for o in sc.objects:
    o.hide_render = o.name not in col
    if o.name in col: o.color = (*col[o.name], 1)
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 20000; cam.lens = 50
c = C - Vector((1600, 0, 0))
for n, d, R in (("sus", (0, -.05, 1), 260), ("fata", (-.3, 1, .6), 230), ("spate", (-.3, -1, .6), 230), ("lateral", (-1, .1, .3), 230)):
    co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
