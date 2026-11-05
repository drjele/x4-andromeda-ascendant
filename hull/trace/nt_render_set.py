# Isolated reference pieces rendered from a few views, one row per spec, as a sheet. Spec = "label:regex" (regex on object name, in REFERINTA).
# Usage: blender -b <scene> --python nt_render_set.py -- <out_dir> <scale> <views,comma> spec spec ...   env COL=REFERINTA XO=0 RES=700
import bpy, sys, os, re
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OD, SC, VW = a[0], float(a[1]), a[2].split(","); XO = float(os.environ.get("XO", 0))
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.show_object_outline = True; sh.color_type = os.environ.get("CT", "RANDOM")
R = [o for c in os.environ.get("COL", "REFERINTA").split(",") for o in bpy.data.collections[c].all_objects]
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get("RES", 700)); os.makedirs(OD, exist_ok=True)
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.type = "ORTHO"; cam.ortho_scale = SC
DV = {"jos": (0, 0, -1), "sus": (0, 0, 1), "lat": (-1, 0, 0), "fata": (0, 1, 0), "spate": (0, -1, 0), "ojos": (-.5, .5, -.7), "osus": (-.5, -.5, .7), "ojos2": (-.5, -.5, -.7), "osus2": (-.5, .5, .7)}
sc.frame_set(int(os.environ.get("FR", 1)))
for spec in a[3:]:
    lab, rx = spec.split(":", 1); r = re.compile(rx)
    for o in sc.objects: o.hide_render = True
    S = [o for o in R if r.search(o.name)]
    for o in S: o.hide_render = False
    pts = [o.matrix_world @ Vector(b) for o in S for b in o.bound_box]; c = sum(pts, Vector()) / len(pts) if pts else Vector()
    if os.environ.get("CENTER0"): c = Vector((XO, 0, 0))
    if os.environ.get("CEN"): c = Vector([float(t) for t in os.environ["CEN"].split(",")])
    for k in VW:
        d = Vector(DV[k]).normalized(); co.location = c + d * 5000; co.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler(); sc.render.filepath = os.path.join(OD, lab + "_" + k + ".png"); bpy.ops.render.render(write_still=True)
