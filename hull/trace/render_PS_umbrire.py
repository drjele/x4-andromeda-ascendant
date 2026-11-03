# PS shading check (asked: clean surfaces pass - the diagonal streaks on PS's top): PS alone, grey, smooth shaded, from above
# (orthographic) and grazing from the left-back and right-front, where streaks show most. Usage: ... -- <out_prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.show_cavity = False; sh.color_type = "OBJECT"; sh.show_specular_highlight = True
p = bpy.data.objects["an_PS"]
for o in sc.objects: o.hide_render = o is not p
p.color = (.8, .8, .82, 1); sc.render.resolution_x, sc.render.resolution_y = 1200, 900
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 20000
c = Vector((-1600, 200, 310))
for n, d, t in (("sus", (0, -.001, 1), "O"), ("razant_stanga_spate", (-.7, -.7, .35), "P"), ("razant_dreapta_fata", (.7, .7, .3), "P")):
    co.location = c + Vector(d).normalized() * 900; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    if t == "O": cam.type = "ORTHO"; cam.ortho_scale = 680
    else: cam.type = "PERSP"; cam.lens = 40
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
