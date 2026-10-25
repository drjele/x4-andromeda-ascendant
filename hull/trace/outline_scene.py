# Blender scene of the outline-only ship (visual hull) beside V4, plus top / side / three-quarter renders.
# Usage: blender -b --python outline_scene.py -- <hull.npz> <out.blend> <render_dir>
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; H = np.load(a[0]); OUT, RD = a[1], a[2]; T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene; sc.name = "contur"
def mesh(name, v, f, rgb, col):
    me = bpy.data.meshes.new(name); me.from_pydata(v.tolist(), [], f[:, ::-1].tolist()); me.update()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); col.objects.link(o); m = bpy.data.materials.new(name); m.diffuse_color = (*rgb, 1); me.materials.append(m); return o
cc = bpy.data.collections.new("din_contur"); sc.collection.children.link(cc)
mesh("nava_din_contur", H["ship_v"], H["ship_f"], (0.75, 0.76, 0.8), cc); mesh("corp_din_contur", H["body_v"], H["body_f"], (0.95, 0.6, 0.3), cc)
vc = bpy.data.collections.new("nava_V4"); sc.collection.children.link(vc)
with bpy.data.libraries.load(f"{T}/versions/V4.blend") as (src, dst): dst.collections = [src.collections[0]]
first = [c for c in bpy.data.collections if c.library is None and c.name.startswith("V4")][0].name
for o in list(bpy.data.collections[first].objects):
    vc.objects.link(o); m = bpy.data.materials.new(o.name); m.diffuse_color = (0.35, 0.55, 0.95, 1); o.data.materials.clear(); o.data.materials.append(m)
bpy.data.collections.remove(bpy.data.collections[first])
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True
sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 1800, 1000
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 30000
SHOTS = (("sus", (0, 0, 9000), 3200), ("profil", (-9000, 0, 0), 3200), ("fata", (0, 9000, 0), 2000), ("3_4", (2600, 3400, 2200), None))
lay = bpy.context.view_layer.layer_collection.children
for tag, shown in (("contur", "din_contur"), ("V4", "nava_V4")):
    for c in ("din_contur", "nava_V4"): lay[c].exclude = c != shown
    for name, loc, ortho in SHOTS:
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho: cam.data.ortho_scale = ortho
        else: cam.data.lens = 38
        cam.location = loc; cam.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = f"{RD}/{tag}_{name}.png"; bpy.ops.render.render(write_still=True)
lay["din_contur"].exclude = False; lay["nava_V4"].exclude = False; lay["nava_V4"].hide_viewport = True
for scr in bpy.data.screens:
    for area in [a for a in scr.areas if a.type == "VIEW_3D"]:
        # the ship is ~3 km: the default 1 km clip range cuts it when zooming
        sp = area.spaces[0]; sp.clip_start = 1.0; sp.clip_end = 60000; sp.shading.color_type = "MATERIAL"; sp.region_3d.view_distance = 5200
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("SCENE ok")
