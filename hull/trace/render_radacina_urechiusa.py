# The stowed blade's root over the back ear tab (asked: the root must sit right above an_urechiusa_2_S): stowed blade yellow, the
# ear tabs blue, only the PS frame around them (the rest hides the root); from above and below (orthographic) and oblique. Usage: blender -b <f.blend> --python render_radacina_urechiusa.py -- <out_prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
ship = [o for o in bpy.data.collections["ASAMBLAT_NOU"].objects if not o.name.startswith("an_lama")]
for o in ship: o.color = (.72, .72, .75, 1)
bpy.data.objects["an_urechiusa_2_S"].color = (.2, .45, 1, 1); bpy.data.objects["an_urechiusa_1_S"].color = (.5, .7, 1, 1); bl = bpy.data.objects["lama_stransa_S"]; bl.color = (1, .85, 0, 1)
sc.render.resolution_x, sc.render.resolution_y = 1100, 850
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.lens = 45
c = Vector((-1600 - 95, 200, 285))
keep = {"an_PS_rama", "an_urechiusa_2_S", "an_urechiusa_1_S"}
for n, d, R, only in (("sus_doar_rama", (0, -.001, 1), 600, True), ("jos_doar_rama", (0, -.001, -1), 600, True), ("oblic_doar_rama", (-.6, -.5, .6), 330, True)):
    for o in sc.objects: o.hide_render = not ((o.name in keep) or o is bl)
    co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    cam.type = "ORTHO" if n != "oblic_doar_rama" else "PERSP"; cam.ortho_scale = 260
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)
