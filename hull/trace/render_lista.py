# Many close-ups of one block from one scene load (clean lines pass). Workbench, studio light, cavity, outline; hatch blue, blades yellow,
# columns red, hull grey when CT=OBJECT. Views file: lines "name x,y,z width dir frame [CT]" (x,y,z ship coords, XOFF added).
# Usage: blender -b <scene> --python render_lista.py -- <out_dir> <views.txt>   env COL=ASAMBLAT_NOU XOFF=-2400 RES=1100
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OD = a[0]; V = [l.split() for l in open(a[1]) if l.strip() and l[0] != "#"]
XO = float(os.environ.get("XOFF", -2400)); sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = True; sh.show_object_outline = True
col = set(o for c in os.environ.get("COL", "ASAMBLAT_NOU").split(",") for o in bpy.data.collections[c].objects)
ON = os.environ.get("ONLY", ""); col = {o for o in col if not ON or o.name in ON.split(",")}
for o in sc.objects: o.hide_render = o not in col
for o in col:
    if o.type != "CURVE": o.color = (1, .85, 0, 1) if "_lama_" in o.name else (.85, .08, .08, 1) if "spinare" in o.name else (.1, .5, 1, 1) if "_usa_" in o.name else (.72, .72, .75, 1)
if os.environ.get("PIESE"):
    CC = {"brat": (.72, .72, .75, 1), "ureche": (.9, .1, .1, 1), "PS_carena": (.6, .2, .9, 1), "PS_rama": (1, .5, 0, 1), "usa": (.1, .5, 1, 1), "lama": (1, .85, 0, 1)}
    for o in col:
        if o.type != "CURVE": o.color = next((c for k, c in CC.items() if k in o.name), (.1, .8, .2, 1) if o.name == "an_PS" else (.2, .2, .2, 1))
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get("RES", 1100))
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.type = "ORTHO"
DV = {"ojos": (-.5, .5, -.7), "osus": (-.5, -.5, .7), "lat": (-1, 0, 0), "fata": (0, 1, 0), "spate": (0, -1, 0), "jos": (0, 0, -1), "sus": (0, 0, 1), "oblic": (.5, -.5, -.7), "oblicS": (-.5, -.5, -.7), "oblicF": (-.5, .5, -.7), "oblicI": (.5, .5, -.7), "x+": (1, 0, 0), "x-": (-1, 0, 0), "y-": (0, -1, 0), "y+": (0, 1, 0)}
for v in V:
    C = Vector([float(t) for t in v[1].split(",")]); C.x += XO; d = Vector(DV[v[3]]).normalized(); sc.frame_set(int(v[4])); sh.color_type = v[5] if len(v) > 5 else "OBJECT"
    cam.ortho_scale = float(v[2]); co.location = C + d * 3000; co.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler(); sc.render.filepath = os.path.join(OD, v[0] + ".png"); bpy.ops.render.render(write_still=True)
