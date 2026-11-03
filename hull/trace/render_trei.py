import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; sc.frame_set(1)
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
show = set()
for cn in ("ATELIER_LAME", "ATELIER_DESCHISE", "ATELIER_STRANSE"): show |= {o for o in bpy.data.collections[cn].objects if not o.name.startswith("ref_lama")}
for o in sc.objects: o.hide_render = o not in show
for o in show: o.color = (1, .85, 0, 1) if "_lama_" in o.name else (.45, .04, .04, 1) if "nacela_inchis" in o.name else (.9, .4, .4, 1) if "nacela_deschis" in o.name else (.72, .72, .75, 1)
sc.render.resolution_x, sc.render.resolution_y = 1800, 700
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.type = "ORTHO"; cam.ortho_scale = 6600
for n, loc, rot in (("sus", (-9000, 150, 3000), (0, 0, 0)),):
    co.location = loc; co.rotation_euler = rot; sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
cam.type = "PERSP"; cam.lens = 30; c = Vector((-9000, 150, 150)); co.location = c + Vector((-.35, 1, .5)).normalized() * 6500; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
sc.render.filepath = "%s_oblic.png" % OUT; bpy.ops.render.render(write_still=True)
