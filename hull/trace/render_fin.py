# The R109 fin on the ship, close (asked: compare the fin leaning 17.8 deg with the surface vs standing vertical): ear, PS, PS frame
# and both fins grey / fin orange, from behind (along the fin), from the side across it and oblique from above-behind.
# Usage: blender -b <f.blend> --python render_fin.py -- <out_prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = {"an_PS": (.75, .75, .78), "an_PS_rama": (.7, .7, .74), "an_ureche_S": (.7, .72, .78), "an_ureche_D": (.7, .72, .78),
       "an_capac_086": (.75, .75, .78), "an_R109_S": (.95, .55, .15), "an_R109_D": (.95, .55, .15)}
for o in sc.objects:
    o.hide_render = o.name not in col
    if o.name in col: o.color = (*col[o.name], 1)
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 20000
c = Vector((-150 - 1600, 75, 320))
for n, d, R, lens in (("spate", (0, -1, .12), 420, 50), ("spate_ambele", (0, -1, .25), 900, 50), ("lateral", (-1, .05, .1), 420, 35), ("oblic", (-.6, -.7, .5), 420, 35)):
    cc = Vector((-1600, 75, 320)) if n == "spate_ambele" else c
    co.location = cc + Vector(d).normalized() * R; co.rotation_euler = (cc - co.location).to_track_quat("-Z", "Y").to_euler(); cam.lens = lens
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
