# The lofted nacelle put on the ship (in place of the red ribs and plates, which are hidden), with one material: red, and
# dark red stripes exactly where the ribs were (a stripe image read along the band's length, from the stripes file);
# renders the original and the new from the same cameras for comparison; saves the scene.
# Usage: blender -b <A.blend> --python nacelle_scene.py -- <nacela.obj> <stripes.json> <out.blend> <render_prefix>
import bpy, sys, json, math, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OBJ, SJ, OUT, RP = a; sc = bpy.context.scene; ST = json.load(open(SJ))
imgs = {}
def isred(o, step=1):
    me = o.data; uv = me.uv_layers.active.data; res = []
    for p in me.polygons:
        m = me.materials[p.material_index] if me.materials else None; tl = [n for n in m.node_tree.nodes if n.type == "TEX_IMAGE"] if m and m.node_tree else []
        if not tl or not tl[0].image: return np.array([False])
        t = tl[0].image
        if t.name not in imgs: imgs[t.name] = np.array(t.pixels[:], np.float32).reshape(t.size[1], t.size[0], t.channels)
        A = imgs[t.name]; u, v = uv[p.loop_start].uv; c = A[int((v % 1) * (A.shape[0] - 1)), int((u % 1) * (A.shape[1] - 1)), :3]
        res.append(c[0] > 0.25 and c[0] > 1.8 * max(c[1], c[2]))
    return np.array(res)
W = 4096; img = bpy.data.images.new("dungi_nacela", W, 4); px = np.zeros((4, W, 4), np.float32); px[..., 3] = 1
red, dark = np.array([0.70, 0.05, 0.05]), np.array([0.22, 0.01, 0.02]); col = np.tile(red, (W, 1))
for u, w in ST["stripes"]:
    i0, i1 = int((u - w / 2) * W), int((u + w / 2) * W) + 1; col[max(i0, 0):min(i1, W)] = dark
px[..., :3] = col[None]; img.pixels = px.ravel(); img.pack()
m = bpy.data.materials.new("nacela_rosie"); m.use_nodes = True; nt = m.node_tree; tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = "Closest"
nt.links.new(tex.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"]); nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.45
bpy.ops.wm.obj_import(filepath=OBJ, forward_axis="Y", up_axis="Z"); nac = bpy.context.selected_objects[0]; nac.name = "nacela_rosie"
nac.data.materials.clear(); nac.data.materials.append(m); bpy.context.view_layer.objects.active = nac; bpy.ops.object.shade_smooth()
ribs = [o for o in sc.objects if o.type == "MESH" and o.name != "nacela_rosie" and o.data.uv_layers and len(o.data.polygons) < 400 and isred(o).all()]
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.render.resolution_x = 1100; sc.render.resolution_y = 800; sc.eevee.taa_render_samples = 16
w = sc.world or bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun); sun.rotation_euler = (math.radians(40), 0, math.radians(-30)); sun.data.energy = 4
for o in sc.objects:
    if o.type == "FONT": o.hide_render = True
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = "ORTHO"; cam.data.clip_end = 50000
shots = [("34", (-1300, 1500, 1200), (60, 0, -140), 900), ("sus", (-330, 350, 4000), (0, 0, 0), 700), ("lat", (-1800, 350, 400), (80, 0, -90), 700), ("fata", (-330, 3000, 200), (90, 0, 180), 700)]
for tag in ("orig", "nou"):
    nac.hide_render = tag == "orig"
    for o in ribs: o.hide_render = tag == "nou"
    for n, l, r, s in shots:
        cam.location = l; cam.rotation_euler = [math.radians(x) for x in r]; cam.data.ortho_scale = s; sc.render.filepath = f"{RP}_{tag}_{n}.png"; bpy.ops.render.render(write_still=True)
for o in ribs:
    o.hide_render = True
    if o.name in bpy.context.view_layer.objects: o.hide_set(True)
nac.hide_render = False
cp = nac.copy(); cp.data = nac.data; cp.name = "nacela_rosie_alaturi"; sc.collection.objects.link(cp); cp.location.x -= 1700   # a copy beside the ship, to see it alone
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SCENA", len(ribs), "nervuri originale ascunse")
