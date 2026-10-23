# Ad-hoc close-ups: blender -b --python closeup.py -- <out_dir> <tags> <name>:<lx,ly,lz>:<tx,ty,tz>[:<lens>] ...
# tags: a = ours, b = ours + see-through original, o = original alone
import bpy, json, sys
from mathutils import Vector
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
args = sys.argv[sys.argv.index("--") + 1:]; OUT, TAGS = args[0], args[1]
P = json.load(open(f"{D}/body/parts.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc
for o in sc.objects:
    if o.type != "MESH": continue
    rgb, alpha = ((0.55, 0.55, 0.6), 0.45) if o.name == "source" else (tuple(P.get(o.name, ["", (0.8, 0.6, 0.3)])[1]), 1.0)
    mm = bpy.data.materials.new(o.name); mm.diffuse_color = (*rgb, alpha); o.data.materials.clear(); o.data.materials.append(mm)
    for p in o.data.polygons: p.material_index = 0
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.render.resolution_x, sc.render.resolution_y = 1100, 800
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 30000
src = sc.objects["source"]
for spec in args[2:]:
    f = spec.split(":"); name = f[0]; loc = tuple(map(float, f[1].split(","))); tgt = tuple(map(float, f[2].split(","))); cam.data.lens = float(f[3]) if len(f) > 3 else 45
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    for t in TAGS:
        src.hide_render = t == "a"; src.data.materials[0].diffuse_color[3] = 1.0 if t == "o" else 0.45
        for o in sc.objects:
            if o.type == "MESH" and o.name != "source": o.hide_render = t == "o" or o.name == "source_edited"
        sc.render.filepath = f"{OUT}/{name}_{t}.png"; bpy.ops.render.render(write_still=True)
