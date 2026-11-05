# The reference coloured by coverage + the new ship at the same views. Usage: blender -b <scene> --python nt_render_ref.py -- <out_dir> <cov.txt> [only=regex]
import bpy, sys, os, re
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OD = a[0]; cov = {}
for l in open(a[1]):
    t = l.split()
    if t[0] == "@@" and len(t) > 3:
        try: cov[t[1].replace("_", " ", 1)] = float(t[3])
        except: pass
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.show_object_outline = True; sh.color_type = "OBJECT"
R = bpy.data.collections["REFERINTA"].objects; NA = bpy.data.collections["ASAMBLAT_NOU"].objects
for o in sc.objects: o.hide_render = True
sc.render.resolution_x = sc.render.resolution_y = 1000
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.type = "ORTHO"; cam.ortho_scale = 3200
DV = {"jos": (0, 0, -1), "sus": (0, 0, 1), "lat": (-1, 0, 0), "fata": (0, 1, 0), "spate": (0, -1, 0), "obl_jos": (-.5, .5, -.7), "obl_sus": (-.5, -.5, .7)}
sc.frame_set(1)
def shot(n, c):
    for k, d in DV.items():
        d = Vector(d).normalized(); co.location = c + d * 5000; co.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler(); sc.render.filepath = os.path.join(OD, n + "_" + k + ".png"); bpy.ops.render.render(write_still=True)
for o in R:
    o.hide_render = False; v = cov.get(o.name); o.color = (.6, .1, .9, 1) if v is None else (.75, .75, .78, 1) if v >= 70 else (1, .75, 0, 1) if v >= 20 else (.95, .1, .1, 1)
shot("ref", Vector((0, 0, 0)))
for o in R: o.hide_render = True
for o in NA: o.hide_render = False; o.color = (.75, .75, .78, 1)
shot("nou", Vector((-2400, 0, 0)))
