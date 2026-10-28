# The source's materials and textures onto the regenerated parts, so they look like the final ship: for every new part
# the reference pieces it replaces are copied, moved beside the ship (x + DX) and joined into one temporary source; each
# face of the new part takes the material of the nearest source face (each piece keeps its own material: hull, strips,
# blades, red ribs), and the UVs are carried over from the nearest source face corners (Data Transfer, interpolated), so
# the packed textures land where they were. The temporary source is removed; the viewport shows textures.
# Usage: blender -b <file.blend> --python tex_transfer.py -- <inlocuite.json> <out.blend> <dx>
import bpy, bmesh, sys, json
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; RJ, OUT, DX = a[0], a[1], float(a[2])
res = json.load(open(RJ)); key = lambda n: n.split()[-1]
ribs = sorted({key(n)[:-2] for f, n, c, nf in res if f > 0.7 and c == "piese_medii" and nf <= 200 and key(n).endswith("_S")})
ribs = [o.name for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith(("nou_", "nervura", "banda")) and key(o.name)[:-2] in ribs and key(o.name)[-2:] in ("_S", "_D") and o.name[0] == "R"]
PS = ["R002 169_C", "R082 086_S", "R034 103_S", "R033 103_D", "R122 055_S", "R121 055_D", "R076 118_S", "R075 117_D"]
ARM = ["R004 022_S", "R003 019_D", "R047 085_S", "R046 085_D", "R060 098_S", "R059 098_D"]
TARGETS = {"ps_punte": PS, "ps_tub_S": ["R002 169_C"], "ps_tub_D": ["R002 169_C"], "brat_fata_S": ARM, "brat_fata_D": ARM, "nacela_rosie_S": ribs, "nacela_rosie_D": ribs}
sc = bpy.context.scene
def source(names):
    objs = []
    for n in names:
        o = bpy.data.objects[n]; c = o.copy(); c.data = o.data.copy(); sc.collection.objects.link(c)
        c.data.transform(o.matrix_world); c.matrix_world.identity(); c.location.x = DX; objs.append(c)
    bpy.ops.object.select_all(action="DESELECT")
    for c in objs: c.hide_set(False); c.hide_viewport = False; c.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); return bpy.context.view_layer.objects.active
for tn, names in TARGETS.items():
    t = bpy.data.objects.get(tn)
    if t is None: print("LIPSA", tn); continue
    src = source(names); src.data.transform(src.matrix_world); src.matrix_world.identity()
    bm = bmesh.new(); bm.from_mesh(src.data); bm.faces.ensure_lookup_table(); bvh = BVHTree.FromBMesh(bm); fmat = [f.material_index for f in bm.faces]
    t.data.materials.clear()
    for m in src.data.materials: t.data.materials.append(m)
    Mw = t.matrix_world; used = {}
    for p in t.data.polygons:
        loc, nrm, fi, d = bvh.find_nearest(Mw @ p.center); p.material_index = fmat[fi] if fi is not None else 0; used[p.material_index] = used.get(p.material_index, 0) + 1
    bm.free()
    if not t.data.uv_layers: t.data.uv_layers.new(name="UVMap")
    md = t.modifiers.new("uv_sursa", "DATA_TRANSFER"); md.object = src; md.use_object_transform = True
    md.use_loop_data = True; md.data_types_loops = {"UV"}; md.loop_mapping = "POLYINTERP_NEAREST"
    bpy.context.view_layer.objects.active = t; t.hide_set(False); bpy.ops.object.modifier_apply(modifier=md.name)
    print("TEXTURI %s: din %d piese sursa, materiale %s" % (tn, len(names), ", ".join("%s %d%%" % (t.data.materials[i].name, 100 * c // len(t.data.polygons)) for i, c in sorted(used.items(), key=lambda x: -x[1]))))
    bpy.data.objects.remove(src)
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type == "VIEW_3D": sp.shading.type = "SOLID"; sp.shading.color_type = "TEXTURE"
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
