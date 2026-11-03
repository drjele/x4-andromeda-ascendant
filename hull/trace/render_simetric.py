# Left / right comparison renders of the animated workshop (asked: test how they look yourself, keep symmetry - front blades alike
# left / right, back blades alike): ATELIER_LAME from straight below, straight above and straight from the front (along y), camera on
# the symmetry plane, ortho, given frames. Blades yellow, hinges red, doors blue (TEX=1: real arm texture, to see the doors blend in). Usage: ... -- <out_prefix> <frames>
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, FR = a[0], [int(x) for x in a[1].split(",")]
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "TEXTURE" if os.environ.get("TEX") else "OBJECT"
col = set(bpy.data.collections["ATELIER_LAME"].objects)
for o in sc.objects: o.hide_render = o not in col
for o in col: o.color = (1, .85, 0, 1) if "_lama_" in o.name else (.85, .08, .08, 1) if "spinare" in o.name else (.1, .5, 1, 1) if "_usa_" in o.name else (.72, .72, .75, 1)
sc.render.resolution_x, sc.render.resolution_y = 900, 600
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.type = "ORTHO"; cam.ortho_scale = 1700
for n, loc, rot in (("jos", (-7000, 250, -2000), (3.14159, 0, 0)), ("sus", (-7000, 250, 3000), (0, 0, 0)), ("fata", (-7000, -3000, 200), (1.5708, 0, 0))):
    co.location, co.rotation_euler = loc, rot
    for fr in FR:
        sc.frame_set(fr); sc.render.filepath = "%s_%s_c%03d.png" % (OUT, n, fr); bpy.ops.render.render(write_still=True)
