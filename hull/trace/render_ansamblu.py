# Check renders of the new PS both ways (asked: always assembled and exploded side by side): the exploded set (new pieces
# at their spot + the components' exploded copies) and the assembled copy (PS_ASAMBLAT_NOU), each oblique and from above,
# materials' colours. Images <prefix>_explodat_oblic / _explodat_sus / _asamblat_oblic / _asamblat_sus.
# Usage: blender -b <f.blend> --python render_ansamblu.py -- <out_dir> <prefix>
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PRE = a[0], a[1]; sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.color_type = "TEXTURE"; sh.show_cavity = True; sh.light = "STUDIO"
asm = set(o.name for o in bpy.data.collections["PS_ASAMBLAT_NOU"].objects)
expl = set(o.name for o in bpy.data.collections["PS_PIESE_NOI"].objects) | set(o.name for o in bpy.data.collections["PS_NOU_EXPLODAT2"].objects if "169_C" not in o.name)
xa = bpy.data.objects[sorted(asm)[0]].location.x if asm else 9100.0
xa = [o for o in bpy.data.collections["PS_ASAMBLAT_NOU"].objects if o.name.startswith("asm_piesa_169_C_PS")][0].location.x
xe = bpy.data.objects["piesa_169_C_PS"].location.x
cam = bpy.data.cameras.new("c"); cam.type = "ORTHO"; cam.clip_end = 40000
co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
def shot(n, keep, cx, loc, tgt, scale, rx, ry):
    for o in sc.objects: o.hide_render = o.name not in keep or "103_118" in o.name
    sc.render.resolution_x, sc.render.resolution_y = rx, ry; cam.ortho_scale = scale; co.location = Vector((cx + loc[0], loc[1], loc[2]))
    co.rotation_euler = (Vector((cx + tgt[0], tgt[1], tgt[2])) - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = "%s/%s_%s.png" % (OUT, PRE, n); bpy.ops.render.render(write_still=True)
for nm, keep, cx in (("explodat", expl, xe), ("asamblat", asm, xa)):
    shot(nm + "_oblic", keep, cx, (0, -1900, 1300), (0, -350, 250), 1900, 1600, 1100)
    shot(nm + "_sus", keep, cx, (0, -450, 6000), (0, -450, 0), 2100, 1100, 1300)
    shot(nm + "_aproape", keep, cx, (0, -900, 900), (0, 150, 300), 900, 1600, 1100)
    shot(nm + "_lateral", keep, cx, (1500, 150, 330), (0, 150, 330), 800, 1600, 700)
    shot(nm + "_fata", keep, cx, (300, 1400, 600), (0, 200, 320), 700, 1400, 1000)
