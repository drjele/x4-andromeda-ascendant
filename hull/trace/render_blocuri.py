# One render per block (asked: render everywhere): the welded guides (x -6000), the assembled guides (x -7700), the pieces
# assembled (x -9400) and exploded (x -11200) - oblique from above, plus the assembled pieces from below. Curves get a
# bevel for the render only (not saved). Usage: blender -b <f.blend> --python render_blocuri.py -- <out prefix>
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"; sc.render.resolution_x, sc.render.resolution_y = 1400, 900
for o in bpy.data.objects:
    if o.type == "CURVE": o.data.bevel_depth = max(o.data.bevel_depth, 1.2)
cam = bpy.data.objects.new("cam_blocuri", bpy.data.cameras.new("cam_blocuri")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 35; cam.data.clip_end = 30000
views = [("ghidaje_sudate", (-6000, -300, 100), (1100, 1600, 1100), lambda n: n.startswith(("g_psr_sep_", "g_cap_sep_", "g_car_sep_", "g_br_sep_", "g_rama_sep_ghidaje"))),
         ("ghidaje_asamblate", (-7700, -300, 100), (900, 1400, 900), lambda n: n.startswith("g_asamblat_")),
         ("piese_asamblate", (-9400, -300, 100), (900, 1400, 900), lambda n: n.startswith("gp_")),
         ("piese_asamblate_jos", (-9400, -300, 100), (700, 1300, -900), lambda n: n.startswith("gp_")),
         ("piese_explodate", (-11200, -300, 100), (1100, 1600, 1100), lambda n: n.startswith("gpe_"))]
for nm, tgt, off, keep in views:
    for o in bpy.data.objects: o.hide_render = not keep(o.name)
    cam.hide_render = False; t = Vector(tgt); p = t + Vector(off); cam.location = p; cam.rotation_euler = (t - p).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = OUT + "_" + nm + ".png"; bpy.ops.render.render(write_still=True)
