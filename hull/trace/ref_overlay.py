# A .blend comparing a frozen version with ref 01: each ref view (top, bottom, side, front, back) on a plane placed
# in the ship's world frame through the corrected fit (fit_ref01.json, the bottom view mirrored), behind the ship as
# seen from that view, with an ortho camera per view; and a render of each view with the ship half transparent over
# the drawing. Front/back are drawn in perspective in ref 01, so they only roughly line up.
# Usage: blender -b --python ref_overlay.py -- <version> <out.blend> <render_dir>
import bpy, sys, json
import numpy as np
from mathutils import Vector, Matrix
VER, OUT, RD = sys.argv[sys.argv.index("--") + 1:][:3]; T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
FIT = json.load(open(f"{T}/trace/fit_ref01.json")); ORTHO = json.load(open(f"{T}/view/ref01/views.json")); AX = json.load(open(f"{T}/trace/cam_axes.json"))
DIST = {"top": 700, "bottom": 700, "side": 1300, "front": 1700, "back": 1700}
bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
with bpy.data.libraries.load(f"{T}/versions/{VER}.blend") as (src, dst): dst.collections = [src.collections[0]]
ship = [c for c in bpy.data.collections if c.library is None and c.name == VER][0]; sc.collection.children.link(ship)
# the ship made local and given one light material, so in texture shading it shows its form over the drawings
nava = bpy.data.materials.new("nava"); nava.diffuse_color = (0.85, 0.85, 0.88, 1.0)
for o in list(ship.all_objects):
    if o.type != "MESH": continue
    if o.data.library: o.data = o.data.copy()
    o.data.materials.clear(); o.data.materials.append(nava)
def world(view, px, py):
    # a pixel of the 1x ref crop -> world point in the view's plane (the inverse of outline_hull.to_ref)
    n, s, k = ORTHO[view]["res"], ORTHO[view]["scale"], ORTHO[view]["rot"]; sx, sy, tx, ty = FIT[view]["p"]
    j = (px - tx) / sx; i = (py - ty) / sy
    if FIT[view].get("flip"): j = n - j
    row, col = {0: (i, j), 1: (j, n - i), -1: (n - j, i)}[k]
    r, u = Vector(AX[view]["right"]), Vector(AX[view]["up"]); look = -r.cross(u)
    return r * ((col - n / 2) * s / n) + u * ((n / 2 - row) * s / n) + look * DIST[view], r, u, look
refs = bpy.data.collections.new("ref01"); sc.collection.children.link(refs); cams = {}
for view in FIT:
    img = bpy.data.images.load(f"{T}/overlay/ref01/{view}.png"); W, H = img.size
    corners = [world(view, x, y)[0] for x, y in ((0, H), (W, H), (W, 0), (0, 0))]   # image bottom-left first, like the UVs
    me = bpy.data.meshes.new(f"ref01 {view}"); me.from_pydata([c[:] for c in corners], [], [(0, 1, 2, 3)]); me.update()
    uv = me.uv_layers.new();
    for li, (a, b) in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))): uv.data[li].uv = (a, b)
    mat = bpy.data.materials.new(f"ref01 {view}"); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; em = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs["Emission"], out.inputs["Surface"]); me.materials.append(mat)
    col = bpy.data.collections.new(f"ref01 {view}"); refs.children.link(col); ob = bpy.data.objects.new(f"ref01 {view}", me); col.objects.link(ob)
    # the camera for this view, ortho, framing the drawing
    _, r, u, look = world(view, 0, 0); c = sum(corners, Vector()) / 4
    wx = max(abs((a - b).dot(r)) for a in corners for b in corners); wy = max(abs((a - b).dot(u)) for a in corners for b in corners); size = max(wx, wy)
    cam = bpy.data.objects.new(f"cam {view}", bpy.data.cameras.new(f"cam {view}")); cam.data.type = "ORTHO"; cam.data.ortho_scale = size * 1.02
    cam.data.clip_start, cam.data.clip_end = 1, 60000; z = -look; p = c - look * (DIST[view] + 3000)   # on the viewer's side, looking along `look`
    cam.matrix_world = Matrix(((r.x, u.x, z.x, p.x), (r.y, u.y, z.y, p.y), (r.z, u.z, z.z, p.z), (0, 0, 0, 1))); col.objects.link(cam); cams[view] = (cam, wx, wy)
for a in (s for w in bpy.context.window_manager.windows for s in w.screen.areas if s.type == "VIEW_3D"):
    for sp in a.spaces:
        if sp.type == "VIEW_3D": sp.clip_start, sp.clip_end = 1, 60000; sp.shading.color_type = "TEXTURE"; sp.shading.show_xray = True; sp.shading.xray_alpha = 0.5
bpy.ops.wm.save_as_mainfile(filepath=OUT)
# renders: the drawing alone and the ship alone (studio light, transparent background), blended 50/50 where the
# ship is, with the ship's outline in orange, so both read exactly on top of each other
import numpy as np, os
def png(path):
    im = bpy.data.images.load(path); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)[::-1]; bpy.data.images.remove(im); return a
def save(path, a):
    im = bpy.data.images.new("out", a.shape[1], a.shape[0]); im.pixels = a[::-1].ravel().tolist(); im.filepath_raw = path; im.file_format = "PNG"; im.save(); bpy.data.images.remove(im)
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sc.render.image_settings.color_mode = "RGBA"
for view, (cam, W, H) in cams.items():
    sc.camera = cam; sc.render.resolution_x, sc.render.resolution_y = (1600, int(1600 * H / W)) if W >= H else (int(1600 * W / H), 1600)
    for v2 in cams: bpy.data.objects[f"ref01 {v2}"].hide_render = v2 != view
    tmp = [f"{RD}/_ref.png", f"{RD}/_ship.png"]
    # pass 1: only the drawing, flat
    sh.light = "FLAT"; sh.color_type = "TEXTURE"; sh.show_xray = False; sc.render.film_transparent = False
    for o in ship.all_objects: o.hide_render = True
    sc.render.filepath = tmp[0]; bpy.ops.render.render(write_still=True)
    # pass 2: only the ship, lit, on a transparent background
    for o in ship.all_objects: o.hide_render = False
    bpy.data.objects[f"ref01 {view}"].hide_render = True; sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sc.render.film_transparent = True
    sc.render.filepath = tmp[1]; bpy.ops.render.render(write_still=True)
    ref, shp = png(tmp[0]), png(tmp[1]); m = shp[..., 3:4]
    out = ref.copy(); out[..., :3] = ref[..., :3] * (1 - 0.5 * m) + shp[..., :3] * 0.5 * m
    inside = m[..., 0] > 0.5; edge = inside & ~(np.roll(inside, 1, 0) & np.roll(inside, -1, 0) & np.roll(inside, 1, 1) & np.roll(inside, -1, 1))
    out[edge, :3] = (1.0, 0.45, 0.1); out[..., 3] = 1; save(f"{RD}/ref01_{VER}_{view}.png", out)
    for t in tmp: os.remove(t)
print("REF OVERLAY", OUT)
