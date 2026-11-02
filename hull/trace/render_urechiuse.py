# The small ear tabs under the PS frame from below (asked: finish the decorations): tab 1 blue, tab 2 orange, with PS, its frame,
# the ear, the front arm and the nacelle around them. Usage: blender -b <f.blend> --python render_urechiuse.py
import bpy
from mathutils import Vector
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
col = {"an_urechiusa_1_S": (.2, .35, .8), "an_urechiusa_2_S": (.9, .5, .1), "an_brat_fata_S": (.6, .62, .66), "an_nacela_inchis_S": (.45, .05, .05), "an_nacela_deschis_S": (.9, .4, .4), "an_PS": (.78, .78, .8), "an_PS_rama": (.7, .7, .74), "an_PS_carena": (.72, .74, .7), "an_ureche_S": (.66, .7, .76)}
for o in sc.objects:
    o.hide_render = o.name not in col
    if o.name in col: o.color = (*col[o.name], 1)
sc.render.resolution_x, sc.render.resolution_y = 1600, 1100
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 20000; cam.lens = 40
c = Vector((-85 - 1600, 250, 277))
for n, d, R in (("jos", (0, -.05, -1), 260), ("jos_oblic", (-.6, -.3, -.75), 230)):
    co.location = c + Vector(d).normalized() * R; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "/home/adrian/Documents/Andromeda/2026-11-02-decor-clean/r227_urechiuse_S_" + n + ".png"; bpy.ops.render.render(write_still=True)
