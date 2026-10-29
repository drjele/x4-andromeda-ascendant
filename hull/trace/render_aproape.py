# Close-up check renders of sep_PS at given y (oblique from the side, above and below): plain grey, guides optional.
# Usage: blender -b <f.blend> --python render_aproape.py -- <out_prefix> <y1,y2,...> [cu_ghidaje]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, YS, G = a[0], [float(q) for q in a[1].split(",")], len(a) > 2; sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
show = {"sep_PS": (.75, .75, .78), "sep_brat_spate_D": (.55, .65, .85), "sep_brat_spate_S": (.55, .65, .85), "sep_capac_086": (.8, .7, .4)}
for o in sc.objects:
    g = G and o.name.startswith(("g_vp_sep_", "g_umm_sep_")); o.hide_render = not (o.name in show or g)
    if o.name in show: o.color = (*show[o.name], 1)
sc.render.resolution_x, sc.render.resolution_y = 1400, 900
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.lens = 35; cam.clip_end = 20000
X = -4300
for y in YS:
    for n, off in (("sus", (260, 60, 160)), ("jos", (260, 60, -150))):
        co.location = Vector((X + off[0], y + off[1], 293 + off[2])); co.rotation_euler = (Vector((X + 140, y, 293)) - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = f"{OUT}_y{int(y)}_{n}.png"; bpy.ops.render.render(write_still=True)
