# Orthographic renders of our ship for the ref-01 views (nose to the left in top/bottom/side), each as the whole
# ship, as a silhouette mask and as one mask per component group, for fitting onto the designer sheet.
# Usage: blender -b --python ortho_views.py -- <out_dir>
import bpy, json, sys
from mathutils import Vector
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; OUT = sys.argv[sys.argv.index("--") + 1]
P = json.load(open(f"{D}/body/parts.json"))
GROUPS = {"body": "C", "vplate": "V", "links": "LHW", "arms": "A", "upper": "U", "uarch": "G"}
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc
white = bpy.data.materials.new("w"); white.diffuse_color = (1, 1, 1, 1); grey = bpy.data.materials.new("g"); grey.diffuse_color = (0.62, 0.62, 0.64, 1)
parts = [o for o in sc.objects if o.type == "MESH" and not o.name.startswith("source")]
for o in sc.objects:
    if o.type == "MESH": o.hide_render = o.name.startswith("source")
def group_of(o): return next((g for g, pre in GROUPS.items() if P.get(o.name, ["?"])[0][0] in pre), "body")
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sc.render.film_transparent = True; sc.view_settings.view_transform = "Standard"
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.clip_end = 30000
VIEWS = {"top": ((0, 0, 6000), 3000, 1), "bottom": ((0, 0, -6000), 3000, -1), "side": ((-6000, 0, 0), 3000, 0), "front": ((0, 6000, 0), 2000, 0), "back": ((0, -6000, 0), 2000, 0)}
spec = {}
for name, (loc, scale, rot) in VIEWS.items():
    cam.location = loc; cam.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); cam.data.ortho_scale = scale
    sc.render.resolution_x = sc.render.resolution_y = 1200
    spec[name] = {"scale": scale, "res": 1200, "rot": rot}
    def shoot(tag, mat, visible):
        for o in parts:
            o.hide_render = o not in visible
            o.data.materials.clear(); o.data.materials.append(mat)
        sh.light = "FLAT" if mat is white else "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = mat is grey
        sc.render.filepath = f"{OUT}/{name}_{tag}.png"; bpy.ops.render.render(write_still=True)
    shoot("mask", white, set(parts)); shoot("shaded", grey, set(parts))
    for g in GROUPS: shoot(g, white, {o for o in parts if group_of(o) == g})
json.dump(spec, open(f"{OUT}/views.json", "w"), indent=1); print("ORTHO ok")
