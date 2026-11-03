# Close look at the blade hinges (columns) under PS during the motion (asked: shorter hinges, blades close to at_PS_carena / at_PS):
# ATELIER_LAME only, one camera from below-side, frames 1 / 20 / 40 / 60. Usage: ... -- <out_prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = set(bpy.data.collections["ATELIER_LAME"].objects)
for o in sc.objects: o.hide_render = o not in col
for o in col: o.color = (1, .85, 0, 1) if "_lama_" in o.name else (.85, .08, .08, 1) if "spinare" in o.name else (.72, .72, .75, 1)
sc.render.resolution_x, sc.render.resolution_y = 900, 680
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 35
c = Vector((-7060, 70, 230)); co.location = c + Vector((-1, -.15, -.35)).normalized() * 520; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
for fr in (1, 20, 40, 60):
    sc.frame_set(fr); sc.render.filepath = "%s_c%02d.png" % (OUT, fr); bpy.ops.render.render(write_still=True)
