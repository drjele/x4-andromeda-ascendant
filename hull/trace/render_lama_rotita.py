# The blade stowed by turning about a pivot (asked: hinge further back than now): for each pivot y and its angle, the blade turned
# about the vertical through (-59.6, y, root z), ship grey with red nacelles, the blade bright red; above, oblique front, below.
# A case may be x:y:angle (pivot x given; default x -59.6).
# Usage: blender -b <f.blend> --python render_lama_rotita.py -- <out_prefix> <y:angle | x:y:angle,...>
import bpy, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; CASES = [(lambda t: t if len(t) == 3 else (-59.6,) + t)(tuple(float(x) for x in q.split(":"))) for q in a[1].split(",")]
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
blade = bpy.data.objects["an_lama_S"]; ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if not o.name.startswith("an_lama")]
for o in sc.objects: o.hide_render = not (o in ship or o is blade)
for o in ship:
    if o.name.startswith(("marcaj_", "eticheta_")): o.hide_render = True
for o in ship: o.color = (.45, .04, .04, 1) if "nacela_inchis" in o.name else (.9, .4, .4, 1) if "nacela_deschis" in o.name else (.72, .72, .75, 1)
blade.color = (1, .85, 0, 1); M0 = blade.matrix_world.copy(); z0 = 291.9
piv = bpy.data.objects.new("pivot", None); sc.collection.objects.link(piv)
sc.render.resolution_x, sc.render.resolution_y = 1000, 750
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 40
c = Vector((-1600 - 250, 420, 200))
for px, y, ang in CASES:
    P = Vector((px - 1600, y, z0)); blade.matrix_world = Matrix.Translation(P) @ Matrix.Rotation(math.radians(ang), 4, "Z") @ Matrix.Translation(-P) @ M0
    for n, d, R in (("sus", (0, -.05, 1), 1150), ("oblic", (-.5, 1, .55), 1050), ("jos", (-.5, .8, -.6), 950)):
        co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = "%s_x%.0f_y%.0f_%+.0f_%s.png" % (OUT, px, y, ang, n); bpy.ops.render.render(write_still=True)
