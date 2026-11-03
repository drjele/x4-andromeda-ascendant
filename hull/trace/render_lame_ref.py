# The reference's red blades (asked: next, new animated blades equivalent to Circle.007 / lame_rosu): the reference ship grey, each
# Circle* blade in its own colour, labelled in the printout; from above, the side, oblique front and oblique back.
# Usage: blender -b <f.blend> --python render_lame_ref.py -- <out_prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
pal = [(1, .1, .1), (1, .6, 0), (1, 1, 0), (0, .8, .2), (0, .6, 1), (.8, .2, 1)]
ref = bpy.data.collections["REFERINTA"].all_objects; blades = sorted([o for o in ref if o.name.startswith("Circle")], key=lambda o: o.name)
for o in sc.objects: o.hide_render = o not in set(ref) or o.type != "MESH"
for o in ref: o.color = (.7, .7, .72, 1)
for o, c in zip(blades, pal): o.color = (*c, 1); print("LAMA", o.name, "culoare", c)
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 35
c = Vector((0, 150, 150))
for n, d in (("sus", (0, -.05, 1)), ("lateral", (-1, 0, .1)), ("oblic_fata", (-.6, 1, .6)), ("oblic_spate", (-.6, -1, .5))):
    co.location = c + Vector(d).normalized() * 3000; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
