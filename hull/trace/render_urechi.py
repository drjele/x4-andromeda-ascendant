# Check renders of the ears on the separate copy (sep_*): oblique front / back, front, top, below; guides optional.
# Usage: blender -b <f.blend> --python render_urechi.py -- <out_prefix> [cu_ghidaje] [ref]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; G = len(a) > 1; sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.color_type = "OBJECT"
show = {"sep_PS": (.75, .75, .78), "sep_brat_spate_D": (.55, .65, .85), "sep_brat_spate_S": (.55, .65, .85), "sep_capac_086": (.8, .7, .4),
        "sep_comp_055_D": (.4, .7, .5), "sep_comp_055_S": (.4, .7, .5), "sep_ureche_D": (.45, .45, .5), "sep_ureche_S": (.45, .45, .5)}
for o in sc.objects:
    g = G and o.name.startswith(("g_co_sep_", "g_pb_sep_", "g_pv_sep_", "g_v_sep_", "g_um_sep_", "g_umm_sep_", "g_vp_sep_")); o.hide_render = not (o.name in show or g)
    if o.name in show: o.color = (*show[o.name], 1)
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
def shot(n, loc, tgt, ortho=None, lens=40):
    co.location = Vector(loc); co.rotation_euler = (Vector(tgt) - co.location).to_track_quat("-Z", "Y").to_euler()
    if ortho: cam.type = "ORTHO"; cam.ortho_scale = ortho
    else: cam.type = "PERSP"; cam.lens = lens
    cam.clip_end = 20000; sc.render.filepath = f"{OUT}_{n}.png"; bpy.ops.render.render(write_still=True)
X = -4300
if len(a) > 2 and a[2] == "ref":                     # the reference R002 169_C (at x 0) with its guides instead
    show = {"R002 169_C": (.75, .75, .78)}; X = 0
    for o in sc.objects: o.hide_render = not (o.name in show or o.name.startswith(("g_v_ref_", "g_um_ref_")))
shot("oblic", (X + 800, 650, 700), (X, 60, 290)); shot("spate", (X + 700, -900, 600), (X, -150, 290)); shot("fata", (X, 1500, 300), (X, 0, 300), ortho=480)
shot("sus", (X, 0, 3000), (X, 0.01, 0), ortho=850); shot("jos", (X + 600, 300, -300), (X, 0, 280))
