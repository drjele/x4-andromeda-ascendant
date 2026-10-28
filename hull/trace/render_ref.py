# Check renders of chosen objects alone (the reference pieces before rebuilding them): from above, below, the side, the
# front and oblique, textures, back faces shown. Usage: blender -b <f.blend> --python render_ref.py -- <out_dir> <prefix> <obj,obj,...>
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PRE, NAMES = a[0], a[1], a[2].split(","); sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.color_type = "TEXTURE"; sh.show_cavity = True; sh.light = "STUDIO"; sh.show_backface_culling = False
P = []
for n in NAMES:
    o = bpy.data.objects[n]; P += [o.matrix_world @ Vector(c) for c in o.bound_box]
P = np.array([tuple(p) for p in P]); c = (P.min(0) + P.max(0)) / 2; ext = np.ptp(P, 0).max() * 1.15
cam = bpy.data.cameras.new("c"); cam.type = "ORTHO"; cam.clip_end = 40000; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
for o in sc.objects: o.hide_render = o.name not in NAMES and o.name != "c"
for nm, d in (("sus", (0, 0, 1)), ("jos", (0, 0, -1)), ("lateral", (1, 0, 0)), ("fata", (0, 1, 0)), ("spate", (0, -1, 0)), ("oblic", (0.8, -1.2, 1.0))):
    d = Vector(d).normalized(); co.location = Vector(c) + d * 3000; cam.ortho_scale = ext
    up = "Y" if abs(d.z) < 0.99 else "Y"; co.rotation_euler = (Vector(c) - co.location).to_track_quat("-Z", "Z" if abs(d.z) < 0.99 else "Y").to_euler()
    sc.render.resolution_x, sc.render.resolution_y = 1400, 1000; sc.render.filepath = "%s/%s_%s.png" % (OUT, PRE, nm); bpy.ops.render.render(write_still=True)
