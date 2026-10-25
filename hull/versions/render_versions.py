# Side-by-side renders of the frozen versions (V0..V3) in neutral grey from the top, side, front and a three-quarter
# view, each version labelled. Usage: blender -b --python render_versions.py -- <out_dir>
import bpy, os, sys
from mathutils import Vector
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/versions"; OUT = sys.argv[sys.argv.index("--") + 1]
NAMES = [n for n in ("V0", "V1", "V2", "V3") if os.path.exists(f"{D}/{n}.blend")]; GAP = 2200
bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
grey = bpy.data.materials.new("grey"); grey.diffuse_color = (0.62, 0.62, 0.64, 1)
for i, n in enumerate(NAMES):
    with bpy.data.libraries.load(f"{D}/{n}.blend") as (src, dst): dst.collections = [n]
    col = bpy.data.collections[n]; sc.collection.children.link(col); x = (i - (len(NAMES) - 1) / 2) * GAP
    for o in col.objects:
        o.location.x += x; o.data.materials.clear(); o.data.materials.append(grey)
    c = bpy.data.curves.new(n, "FONT"); c.body = n; c.size = 300; c.align_x = "CENTER"; t = bpy.data.objects.new(n, c); t.location = (x, -1800, 0); sc.collection.objects.link(t)
    t.data.materials.append(grey)
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True; sh.cavity_type = "BOTH"
sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = False
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 60000
span = GAP * len(NAMES) + 400
for name, loc, tgt, ortho, res in (("top", (0, -100, 9000), (0, -100, 0), span, (3600, 1500)), ("side", (0, -100, 0), (0, -100, 0), 3000, (1800, 900)),
                                   ("front", (0, 9000, 0), (0, 0, 0), span, (3600, 1100)), ("q", (span * 0.35, 4200, 2600), (0, -300, 0), None, (3600, 1600))):
    if name == "side":
        # the versions sit along x, so each is shot from its own side and the frames are tiled
        for i, n in enumerate(NAMES):
            x = (i - (len(NAMES) - 1) / 2) * GAP; cam.data.type = "ORTHO"; cam.data.ortho_scale = 3000
            cam.location = (x + 9000, -100, 0); cam.rotation_euler = (Vector((x, -100, 0)) - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
            for j, m in enumerate(NAMES):
                for o in bpy.data.collections[m].objects: o.hide_render = m != n
            sc.render.resolution_x, sc.render.resolution_y = res; sc.render.filepath = f"{OUT}/versions_side_{n}.png"; bpy.ops.render.render(write_still=True)
        for m in NAMES:
            for o in bpy.data.collections[m].objects: o.hide_render = False
        continue
    cam.data.type = "ORTHO" if ortho else "PERSP"
    if ortho: cam.data.ortho_scale = ortho
    else: cam.data.lens = 35
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.filepath = f"{OUT}/versions_{name}.png"; bpy.ops.render.render(write_still=True)
print("VERSIONS ok", NAMES)
