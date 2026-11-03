# Stowed blades against the arm's contour (asked: the back blades did not follow the arm's contour, stowed ones stuck out of the
# arms): ATELIER_STRANSE only, from above / below / front-side, each normal (anything showing = sticking out) and X-ray (the blades
# seen through the ship, to compare their outline with the arm's). Usage: ... -- <out_prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = set(bpy.data.collections["ATELIER_STRANSE"].objects)
for o in sc.objects: o.hide_render = o not in col
for o in col: o.color = (1, .85, 0, 1) if "_lama_" in o.name else (.85, .08, .08, 1) if "spinare" in o.name else (.72, .72, .75, 1)
sc.render.resolution_x, sc.render.resolution_y = 1000, 760
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 35
for xr in (False, True):
    sh.show_xray = xr; sh.xray_alpha = .35
    for n, c, d, R in (("sus", (-11000, 150, 150), (0, -.05, 1), 2300), ("jos", (-11000, 150, 150), (0, -.05, -1), 2300), ("lateral", (-11300, 200, 200), (-1, .1, .05), 1500)):
        c = Vector(c); co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = "%s_%s%s.png" % (OUT, n, "_xray" if xr else ""); bpy.ops.render.render(write_still=True)
