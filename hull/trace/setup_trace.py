# Tracing scene: the frozen ship version with each part a separate, named object in its part colour, and the ref-01
# views as reference images placed in the ship's world frame through the ortho fit (ref01/fit.json), each visible
# only when looking along its axis from its own side. The user traces on one annotation layer per view.
# Usage: blender -b --python setup_trace.py -- <version> <out.blend>
import bpy, json, sys
from mathutils import Vector, Matrix, Color
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; args = sys.argv[sys.argv.index("--") + 1:]; V, OUT = args[0], args[1]
P = json.load(open(f"{D}/body/parts.json")); FIT = json.load(open(f"{D}/overlay/ref01/fit.json"))
REF = json.load(open(f"{D}/overlay/ref01/views.json")); ORTHO = json.load(open(f"{D}/view/ref01/views.json"))
# same cameras as view/ortho_views.py, which the fit was made against
CAMS = {"top": (0, 0, 6000), "bottom": (0, 0, -6000), "side": (-6000, 0, 0), "front": (0, 6000, 0), "back": (0, -6000, 0)}
TRACE_PARTS = ["C0 corp", "C16 semiluna", "C22 nivel spate", "C17 romb prova", "V1 placa V", "L1 legatura Y", "H1 hangar", "W1 soclu",
               "A1 brat", "A9 varf", "A7 aripa rosie", "A6 grila cyan bucla", "U1 aripa sus", "G1 arc U", "G2 nacela cyan"]

bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene; sc.name = "trasare"; sc.unit_settings.system = "METRIC"
ship = bpy.data.collections.new("nava"); sc.collection.children.link(ship)
with bpy.data.libraries.load(f"{D}/versions/{V}.blend") as (src, dst): first = src.collections[0]; dst.collections = [first]
for o in list(bpy.data.collections[first].objects):
    name = o.name.split("_", 1)[1]; label, rgb = P.get(name, ["?", (0.7, 0.7, 0.7)])
    o.name = f"{label} {name}"; o.data.name = o.name; ship.objects.link(o)
    m = bpy.data.materials.new(o.name); m.diffuse_color = (*rgb, 1); o.data.materials.clear(); o.data.materials.append(m)
bpy.data.collections.remove(bpy.data.collections[first])

def cam_frame(view):
    loc = Vector(CAMS[view]); rot = (-loc).to_track_quat("-Z", "Y").to_matrix(); return loc, rot
def ref_to_world(view, u, v):
    # ref crop pixel -> rotated ortho render (inverse fit) -> ortho render pixel (undo rot90) -> world
    sx, sy, tx, ty = FIT[view]["p"]; x, y = (u - tx) / sx, (v - ty) / sy; k = ORTHO[view]["rot"]; n = ORTHO[view]["res"]
    row, col = {0: (y, x), 1: (x, n - y), -1: (n - x, y)}[k]
    s = ORTHO[view]["scale"]; loc, rot = cam_frame(view); right, up = rot.col[0], rot.col[1]
    return right * ((col - n / 2) / n * s) + up * ((n / 2 - row) / n * s)

refs = bpy.data.collections.new("referinta_01"); sc.collection.children.link(refs)
for view, spec in REF.items():
    W, H = spec["size"]; img = bpy.data.images.load(f"{D}/overlay/ref01/{view}.png"); img.name = f"ref01_{view}"; img.pack()
    a, b, c = ref_to_world(view, 0, H), ref_to_world(view, W, H), ref_to_world(view, 0, 0)   # bottom-left, bottom-right, top-left
    ex, ey = b - a, c - a; loc, rot = cam_frame(view)
    e = bpy.data.objects.new(f"ref01_{view}", None); refs.objects.link(e)
    e.empty_display_type = "IMAGE"; e.data = img; e.empty_display_size = 1.0; e.empty_image_offset = (0, 0)
    # the image spans 1 unit along its longer side (width); stretch it onto the fitted extents
    basis = Matrix((ex / 1.0, ey / (H / W), rot.col[2])).transposed()
    e.matrix_world = Matrix.Translation(a) @ basis.to_4x4()
    e.empty_image_depth = "FRONT"; e.empty_image_side = "FRONT"; e.show_empty_image_only_axis_aligned = True
    e.hide_select = True

# the user traces on the bare reference; the ship is one eye-click away in the Outliner
bpy.context.view_layer.layer_collection.children["nava"].hide_viewport = True
gp = bpy.data.grease_pencils.new("Trasari"); sc.grease_pencil = gp
# one layer per part; the view of each stroke is read from its plane, so the user only picks the part
for i, name in enumerate(TRACE_PARTS):
    c = Color(); c.hsv = ((i * 0.61803) % 1, 0.85, 1); lay = gp.layers.new(name); lay.color = c; lay.thickness = 3
gp.layers.active = gp.layers[TRACE_PARTS[0]]
ts = sc.tool_settings; ts.annotation_stroke_placement_view3d = "CURSOR"; sc.cursor.location = (0, 0, 0)

# open on the top view, ortho, solid shading in part colours
for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type != "VIEW_3D": continue
        sp = area.spaces[0]; sp.shading.type = "SOLID"; sp.shading.color_type = "MATERIAL"; sp.clip_end = 30000; sp.overlay.show_floor = False
        r3 = sp.region_3d; r3.view_perspective = "ORTHO"; r3.view_rotation = cam_frame("top")[1].to_quaternion(); r3.view_distance = 3200; r3.view_location = (0, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("TRACE ok", OUT, len(ship.objects))
