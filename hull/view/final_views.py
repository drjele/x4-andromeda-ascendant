# Final review renders: the whole ship from the six standard views and close-ups of every joint, each once
# without (a) and once with the original (grey, see-through) overlaid (b), or the original alone (o).
# Usage: blender -b --python final_views.py -- <out_dir> [overall|joints|all] [tags, e.g. abo]
import bpy, json, sys
from mathutils import Vector
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = args[0] if args else f"{D}/view/final"; WHAT = args[1] if len(args) > 1 else "all"; TAGS = args[2] if len(args) > 2 else "ab"
P = json.load(open(f"{D}/body/parts.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc
for o in sc.objects:
    if o.type != "MESH": continue
    rgb, alpha = ((0.55, 0.55, 0.6), 0.45) if o.name == "source" else (tuple(P.get(o.name, ["", (0.8, 0.6, 0.3)])[1]), 1.0)
    mm = bpy.data.materials.new(o.name); mm.diffuse_color = (*rgb, alpha); o.data.materials.clear(); o.data.materials.append(mm)
    for p in o.data.polygons: p.material_index = 0
    o.hide_render = o.name == "source_edited"
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_xray = False; sc.render.film_transparent = False
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 30000
src = sc.objects["source"]
def shoot(name, loc, tgt, res, ortho=None, lens=50):
    sc.render.resolution_x, sc.render.resolution_y = res
    cam.data.type = "ORTHO" if ortho else "PERSP"; cam.data.lens = lens
    if ortho: cam.data.ortho_scale = ortho
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    for t in TAGS:
        src.hide_render = t == "a"; src.data.materials[0].diffuse_color[3] = 1.0 if t == "o" else 0.45
        for o in sc.objects:
            if o.type == "MESH" and o.name != "source": o.hide_render = t == "o" or o.name == "source_edited"
        sc.render.filepath = f"{OUT}/{name}_{t}.png"; bpy.ops.render.render(write_still=True)
if WHAT in ("all", "overall"):
    c = (0, -100, 0)
    shoot("top", (0, -100, 6000), c, (1400, 1900), ortho=2900); shoot("under", (0, -100, -6000), c, (1400, 1900), ortho=2900)
    shoot("side", (6000, -100, 0), c, (1900, 900), ortho=2900); shoot("front", (0, 6000, 0), c, (1600, 900), ortho=1800)
    shoot("q_front", (2500, 2400, 1300), (0, -200, -50), (1600, 1200), lens=60); shoot("q_rear", (2500, -2600, 1100), (0, 0, -80), (1600, 1200), lens=60)
    shoot("q_under", (2300, 2000, -1500), (0, -200, -50), (1600, 1200), lens=60)
if WHAT in ("all", "joints"):
    J = [("j_arc_root", (700, 700, 500), (330, 180, 180)), ("j_arc_root_top", (300, 500, 900), (330, 160, 200)), ("j_tip", (900, 1700, 200), (470, 1300, -220)),
         ("j_tip_under", (800, 1600, -500), (470, 1300, -230)), ("j_loop_rear", (1100, -1700, 500), (430, -1250, 120)), ("j_wing_loop", (1200, -900, 300), (650, -550, -150)),
         ("j_arm_outer", (1300, 100, -200), (700, 0, -250)), ("j_uarch_end", (1000, -900, -700), (520, -850, -70)), ("j_uarch_mid", (300, -1300, -800), (0, -300, -250)),
         ("j_upper_arm", (700, -900, 800), (230, -700, 300)), ("j_upper_body", (500, -300, 800), (120, -650, 220)), ("j_link_root", (600, 300, 350), (300, -150, 60)),
         ("j_hangar", (900, 500, 100), (420, -250, 0)), ("j_vplate", (500, 700, 700), (0, 300, 250)), ("j_keel", (600, 400, -700), (0, 300, -220)),
         ("j_wing_front", (1000, 700, 250), (650, 250, -150)), ("j_wing_arm_under", (1100, -200, -700), (680, -200, -200))]
    for n, loc, tgt in J: shoot(n, loc, tgt, (1100, 800), lens=45)
print("VIEWS ok", OUT)
