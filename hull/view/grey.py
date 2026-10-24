# Neutral-grey renders of the whole ship from the cameras fitted to the series references (overlay/fit/cams.json),
# plus a hand-set camera standing in for reference 10. Usage: blender -b --python grey.py -- <out_dir>
import bpy, json, sys
from mathutils import Vector, Matrix
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
OUT = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc
grey = bpy.data.materials.new("grey"); grey.diffuse_color = (0.62, 0.62, 0.64, 1)
for o in sc.objects:
    if o.type != "MESH": continue
    o.hide_render = o.name.startswith("source")
    o.data.materials.clear(); o.data.materials.append(grey)
    for p in o.data.polygons: p.material_index = 0
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True; sh.cavity_type = "BOTH"; sh.show_specular_highlight = True
sc.render.film_transparent = False; sc.view_settings.view_transform = "Standard"
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = 10; cam.data.clip_end = 200000; cam.data.sensor_fit = "HORIZONTAL"; cam.data.sensor_width = 36
cams = json.load(open(f"{D}/overlay/fit/cams.json"))
for name in ("02_Andromeda_Ascendant", "13_Andromedaorthographicbottom", "14_Andromedaorthographictop", "15_Andromedaorthographicfront", "16_Andromedaorthographicside"):
    c = cams[name]; k = 2 if c["size"][0] < 1000 else 1
    sc.render.resolution_x, sc.render.resolution_y = c["size"][0] * k, c["size"][1] * k
    # OpenCV camera from the fit: rows of R are right, down, forward
    ang = Vector(c["rvec"]).length; R = Matrix.Rotation(ang, 3, Vector(c["rvec"]).normalized())
    cam.data.type = "PERSP"; cam.data.lens = c["f"] * 36 / c["size"][0] * (0.8 if name.startswith("15") else 1.0)   # 15 is zoomed out so the tips stay in frame
    cam.location = c["c"]; cam.rotation_euler = Matrix((R[0], -R[1], -R[2])).transposed().to_euler()
    sc.render.filepath = f"{OUT}/{name[:2]}_grey.png"; bpy.ops.render.render(write_still=True)
sc.render.resolution_x, sc.render.resolution_y = 1704, 960; cam.data.lens = 40
cam.location = (2900, 1500, 650); cam.rotation_euler = (Vector((0, -150, -40)) - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()   # nose to the right, as in the reference
sc.render.filepath = f"{OUT}/10_grey.png"; bpy.ops.render.render(write_still=True)
print("GREY ok")
