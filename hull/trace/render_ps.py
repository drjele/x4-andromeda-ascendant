# Check renders of the new PS body next to the exploded reference, with the flat guides (collection GHIDAJE_PLAN_169_C, when
# present): from above (both), the loop close up, oblique. Plain grey for the shape. Images <prefix>_sus / _bucla / _oblic.
# Usage: blender -b <f.blend> --python render_ps.py -- <out_dir> <prefix> [piece,piece,...]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PRE = a[0], a[1]; PIECES = (a[2] if len(a) > 2 else "piesa_169_C_sectiuni").split(","); PIECE = PIECES[0]; sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.color_type = "MATERIAL"; sh.show_cavity = True; sh.light = "STUDIO"
g = bpy.data.collections.get("GHIDAJE_PLAN_169_C"); keep = set(PIECES) | {"expl_R002 169_C"} | ({o.name for o in g.objects} if g else set())
for o in sc.objects: o.hide_render = o.name not in keep
for n in PIECES + ["expl_R002 169_C"]:
    o = bpy.data.objects[n]; m = bpy.data.materials.new("g"); m.diffuse_color = (0.62, 0.62, 0.66, 1)
    for s in o.material_slots: s.link = "OBJECT"; s.material = m
cam = bpy.data.cameras.new("c"); cam.type = "ORTHO"; cam.clip_end = 40000
co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
xn = bpy.data.objects[PIECE].location.x
def shot(n, loc, tgt, scale, rx, ry):
    sc.render.resolution_x, sc.render.resolution_y = rx, ry; cam.ortho_scale = scale; co.location = Vector(loc)
    co.rotation_euler = (Vector(tgt) - co.location).to_track_quat("-Z", "Y").to_euler(); sc.render.filepath = "%s/%s_%s.png" % (OUT, PRE, n); bpy.ops.render.render(write_still=True)
shot("sus", ((1895 + xn) / 2, -450, 6000), ((1895 + xn) / 2, -450, 0), 4800, 1800, 1000)
shot("bucla", (xn + 700, -1700, 600), (xn + 420, -950, 0), 1300, 1400, 1100)
shot("oblic", (xn, -2600, 1200), (xn, -500, 100), 2000, 1600, 1100)
