# Scene: V4 with its body group swapped for the outline-fitted one, beside plain V4; renders and a .blend for the user.
# Usage: blender -b --python body_scene.py -- <body_fit.npz> <out.blend> <render_dir>
import bpy, sys, json, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; FITB = np.load(a[0]); OUT, RD = a[1], a[2]; T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{T}/body/parts.json")); GAP = 1800
bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
def load(tag, dx, fitted):
    with bpy.data.libraries.load(f"{T}/versions/V4.blend") as (src, dst): dst.collections = [src.collections[0]]
    lib = [c for c in bpy.data.collections if c.library is None and c.name.startswith("V4") and c.name not in ("V4_nou", "V4_vechi")][0]
    col = bpy.data.collections.new(tag); sc.collection.children.link(col)
    for o in list(lib.objects):
        name = o.name.split("_", 1)[1]; label = P.get(name, ["?"])[0]; o.name = f"{tag} {label} {name}"
        body = label.startswith("C")
        if fitted and body and name in FITB.files:
            M = o.matrix_world.inverted(); v = FITB[name]
            for vert, p in zip(o.data.vertices, v): vert.co = M @ Vector(p.tolist())
        o.location.x += dx; col.objects.link(o)
        m = bpy.data.materials.new(o.name); m.diffuse_color = ((0.95, 0.6, 0.3, 1) if body else (0.62, 0.64, 0.7, 1)); o.data.materials.clear(); o.data.materials.append(m)
    bpy.data.collections.remove(lib)
load("V4_vechi", -GAP / 2, False); load("V4_nou", GAP / 2, True)
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True
sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 2200, 1100
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 40000
for name, loc, tgt, ortho in (("sus", (0, 0, 9000), (0, 0, 0), 4300), ("profil", (-12000, 0, 0), (0, 0, 0), 3400), ("3_4", (3200, 4800, 2600), (0, -100, -100), None)):
    cam.data.type = "ORTHO" if ortho else "PERSP"
    if ortho: cam.data.ortho_scale = ortho
    else: cam.data.lens = 34
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if name == "profil":
        # one ship at a time in profile, they would hide each other
        for tag in ("V4_vechi", "V4_nou"):
            for c in bpy.data.collections:
                if c.name in ("V4_vechi", "V4_nou"): c.hide_render = c.name != tag
            cam.location = (loc[0], 0, 0); cam.location.x += (-GAP / 2 if tag == "V4_vechi" else GAP / 2)
            cam.rotation_euler = (Vector((cam.location.x + 1, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = f"{RD}/corp_{name}_{tag}.png"; bpy.ops.render.render(write_still=True)
        for c in bpy.data.collections: c.hide_render = False
        continue
    sc.render.filepath = f"{RD}/corp_{name}.png"; bpy.ops.render.render(write_still=True)
for scr in bpy.data.screens:
    for area in [a for a in scr.areas if a.type == "VIEW_3D"]:
        # the ship is ~3 km: the default 1 km clip range cuts it when zooming
        sp = area.spaces[0]; sp.clip_start = 1.0; sp.clip_end = 60000; sp.shading.color_type = "MATERIAL"; sp.region_3d.view_distance = 5200
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("BODY SCENE ok")
