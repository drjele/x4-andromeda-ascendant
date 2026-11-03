# Oblique look up into a blade compartment (asked: each blade set in its own compartment, nothing of the arm's inside seen with the
# hatch open): perspective camera below and to the side of the hatch, aimed at its middle, hatch blue / blades yellow / columns red /
# hull grey, at the given frames. Usage: blender -b <scene> --python render_compartiment_oblic.py -- <out_prefix> <hatch> <frames>
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, HN, FR = a[0], a[1], [int(x) for x in a[2].split(",")]
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = set(bpy.data.collections["ATELIER_LAME"].objects)
for o in sc.objects: o.hide_render = o not in col
for o in col: o.color = (1, .85, 0, 1) if "_lama_" in o.name else (.85, .08, .08, 1) if "spinare" in o.name else (.1, .5, 1, 1) if "_usa_" in o.name else (.72, .72, .75, 1)
h = bpy.data.objects[HN]; sc.frame_set(1); P = [h.matrix_world @ v.co for v in h.data.vertices]; c = sum(P, Vector()) / len(P)
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 30
for nm, off in (("a", Vector((120, -260, -220))), ("b", Vector((-260, 120, -160)))):
    co.location = c + off; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    for fr in FR: sc.frame_set(fr); sc.render.filepath = "%s_%s_c%03d.png" % (OUT, nm, fr); bpy.ops.render.render(write_still=True)
