# Close-ups of a few parts alone: blender -b --python iso.py -- <out_dir> <name,name,...> <tag>:<lx,ly,lz>:<tx,ty,tz>[:<lens>|ortho<scale>] ...
import bpy, json, sys
from mathutils import Vector
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
args = sys.argv[sys.argv.index("--") + 1:]; OUT, names = args[0], set(args[1].split(","))
P = json.load(open(f"{D}/body/parts.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc
for o in sc.objects:
    if o.type != "MESH": continue
    o.hide_render = o.name not in names
    mm = bpy.data.materials.new(o.name); mm.diffuse_color = (*P.get(o.name, ["", (0.8, 0.6, 0.3)])[1], 1); o.data.materials.clear(); o.data.materials.append(mm)
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.render.resolution_x, sc.render.resolution_y = 1100, 800
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 30000
for spec in args[2:]:
    f = spec.split(":"); loc = tuple(map(float, f[1].split(","))); tgt = tuple(map(float, f[2].split(",")))
    if len(f) > 3 and f[3].startswith("ortho"): cam.data.type = "ORTHO"; cam.data.ortho_scale = float(f[3][5:])
    else: cam.data.type = "PERSP"; cam.data.lens = float(f[3]) if len(f) > 3 else 45
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{OUT}/{f[0]}.png"; bpy.ops.render.render(write_still=True)
