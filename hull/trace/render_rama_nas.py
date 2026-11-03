# The PS frame's nose against PS (asked: an_PS_rama at the nose must be exactly like an_PS): PS grey, frame orange, hull pad blue;
# from below, oblique from the front-below, and from below without PS (the frame's own outline). Usage: ... -- <out_prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = {"an_PS_rama": (.95, .6, .2), "an_PS": (.78, .78, .8), "an_PS_carena": (.6, .65, .75)}
for o in sc.objects:
    o.hide_render = o.name not in col
    if o.name in col: o.color = (*col[o.name], 1)
sc.render.resolution_x, sc.render.resolution_y = 1200, 900
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 20000; cam.lens = 50
c = Vector((-1600, 430, 280))
for n, d, R, ps in (("jos", (0, -.1, -1), 230, True), ("oblic_fata_jos", (-.3, 1, -.45), 220, True), ("sus_fara_PS", (0, -.1, 1), 230, False)):
    bpy.data.objects["an_PS"].hide_render = not ps
    co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
