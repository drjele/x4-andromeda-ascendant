# Two frozen versions side by side per component, in the part colours: top, side, front and three-quarter views,
# the component's parts opaque and the rest faint. Usage: blender -b --python compare_versions.py -- <out_dir> <A> <B>
import bpy, json, sys
from mathutils import Vector
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; args = sys.argv[sys.argv.index("--") + 1:]; OUT, A, B = args[0], args[1], args[2]
P = json.load(open(f"{D}/body/parts.json")); GROUPS = {"body": "C", "vplate": "V", "links": "LHW", "arms": "A", "upper": "U", "uarch": "G"}
bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene; GAP = 2100
def group_of(o):
    n = o.name.split("_", 1)[1]; lab = P.get(n, ["?"])[0][0]; return next((g for g, pre in GROUPS.items() if lab in pre), "body")
cols = {}
for i, n in enumerate((A, B)):
    with bpy.data.libraries.load(f"{D}/versions/{n}.blend") as (src, dst): first = src.collections[0]; dst.collections = [first]
    col = bpy.data.collections[first]; col.name = n; sc.collection.children.link(col); cols[n] = col
    for o in col.objects:
        o.location.x += (i - 0.5) * GAP; base = o.name.split("_", 1)[1]; rgb = P.get(base, ["", (0.8, 0.6, 0.3)])[1]
        m = bpy.data.materials.new(o.name); m.diffuse_color = (*rgb, 1); o.data.materials.clear(); o.data.materials.append(m)
    c = bpy.data.curves.new(n, "FONT"); c.body = n; c.size = 260; c.align_x = "CENTER"; t = bpy.data.objects.new(n, c); t.location = ((i - 0.5) * GAP, -1750, 0); sc.collection.objects.link(t)
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True; sh.cavity_type = "BOTH"
sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = False
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 60000
VIEWS = (("top", (0, -100, 9000), (0, -100, 0), 4600, (2400, 1500)), ("front", (0, 9000, 0), (0, 0, 0), 4600, (2400, 1000)), ("back", (0, -9000, 0), (0, 0, 0), 4600, (2400, 1000)), ("q", (1500, 3600, 2200), (0, -300, 0), None, (2400, 1200)))
for g in GROUPS:
    for col in cols.values():
        for o in col.objects:
            mine = group_of(o) == g; o.hide_render = False
            o.data.materials[0].diffuse_color[3] = 1.0 if mine else 0.18
    sh.show_xray = False
    for name, loc, tgt, ortho, res in VIEWS:
        cam.data.type = "ORTHO" if ortho else "PERSP"
        if ortho: cam.data.ortho_scale = ortho
        else: cam.data.lens = 40
        cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.render.resolution_x, sc.render.resolution_y = res; sc.render.filepath = f"{OUT}/{g}_{name}.png"; bpy.ops.render.render(write_still=True)
    for i, n in enumerate((A, B)):
        x = (i - 0.5) * GAP; cam.data.type = "ORTHO"; cam.data.ortho_scale = 3000; cam.location = (x + 9000, -100, 0)
        cam.rotation_euler = (Vector((x, -100, 0)) - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
        for m, col in cols.items():
            for o in col.objects: o.hide_render = m != n
        sc.render.resolution_x, sc.render.resolution_y = (1800, 900); sc.render.filepath = f"{OUT}/{g}_side_{n}.png"; bpy.ops.render.render(write_still=True)
print("COMPARE ok")
