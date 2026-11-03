# Close-up of one hatch and its cutout from straight below (asked: clean lines on at_usa_spate_S and its cutout in at_brat_fata_S):
# ortho camera framed on the hatch, at the given frames (1 = closed, 1+FO = slid open: the cutout is seen); TEX=1 real arm texture,
# otherwise hatch blue / blades yellow / columns red with cavity + outline. Usage: ... -- <out_prefix> <hatch object> <frames>
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, HN, FR = a[0], a[1], [int(x) for x in a[2].split(",")]
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True
sh.show_object_outline = True; sh.color_type = "TEXTURE" if os.environ.get("TEX") else "OBJECT"
col = set(bpy.data.collections["ATELIER_LAME"].objects)
for o in sc.objects: o.hide_render = o not in col
for o in col: o.color = (1, .85, 0, 1) if "_lama_" in o.name else (.85, .08, .08, 1) if "spinare" in o.name else (.1, .5, 1, 1) if "_usa_" in o.name else (.72, .72, .75, 1)
h = bpy.data.objects[HN]; sc.frame_set(1); P = [h.matrix_world @ v.co for v in h.data.vertices]
lo = Vector([min(p[k] for p in P) for k in range(3)]); hi = Vector([max(p[k] for p in P) for k in range(3)]); c = (lo + hi) / 2
sc.render.resolution_x, sc.render.resolution_y = 1400, 1400
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000
cam.type = "ORTHO"; cam.ortho_scale = max(hi.x - lo.x, hi.y - lo.y) * 1.15; co.location = (c.x, c.y, lo.z - 1500); co.rotation_euler = (3.14159, 0, 0)
for fr in FR:
    sc.frame_set(fr); sc.render.filepath = "%s_c%03d.png" % (OUT, fr); bpy.ops.render.render(write_still=True)
