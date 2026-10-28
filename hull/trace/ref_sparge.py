# The reference PS split in two (asked: its underside apart, and how it joins the top): every face goes to the top part or
# the bottom part by its centre against the middle surface between the confirmed top and bottom guides (ref_teren.py); the
# joint = the mesh edges shared by a top face and a bottom face (yellow), the free edges of each part where the two faces do
# not meet (open). The parts placed exploded at XE (the top lifted DZ), the joint drawn on both. Prints the joint's length.
# Usage: blender -b <f.blend> --python ref_sparge.py -- <out.blend> <teren.npz> <source obj> <xship> <xe> [dz]
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, T, SRC, XS, XE = a[0], np.load(a[1]), a[2], float(a[3]), float(a[4]); DZ = float(a[5]) if len(a) > 5 else 90.0
top, bot = T["top"], T["bot"]; x0, y0, C = float(T["x0"]), float(T["y0"]), float(T["cell"]); ny, nx = top.shape; mid = (top + bot) / 2
col = bpy.data.collections["ORIGINAL_ANALIZA"]; src = bpy.data.objects[SRC]
for n in ("orig_PS_sus", "orig_PS_jos", "orig_PS_imbinare", "orig_PS_imbinare_sus"):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
b = bmesh.new(); b.from_mesh(src.data); b.transform(src.matrix_world); b.faces.ensure_lookup_table()
def zmid(x, y):
    i = int(np.clip((y - y0) / C, 0, ny - 1)); j = int(np.clip((x - XS - x0) / C, 0, nx - 1)); return mid[i, j]
lab = np.array([f.calc_center_median().z >= zmid(f.calc_center_median().x, f.calc_center_median().y) for f in b.faces])
seam = [(e.verts[0].co.copy(), e.verts[1].co.copy()) for e in b.edges if len(e.link_faces) == 2 and lab[e.link_faces[0].index] != lab[e.link_faces[1].index]]
def part(name, keep, dz, dx):
    c = bmesh.new(); c.from_mesh(src.data); c.transform(src.matrix_world); c.faces.ensure_lookup_table()
    bmesh.ops.delete(c, geom=[f for f in c.faces if lab[f.index] != keep], context="FACES")
    bmesh.ops.delete(c, geom=[v for v in c.verts if not v.link_faces], context="VERTS")
    fb = sum(1 for e in c.edges if e.is_boundary); bmesh.ops.translate(c, verts=c.verts[:], vec=(dx, 0, dz))
    me = bpy.data.meshes.new(name); c.to_mesh(me); c.free()
    for m in src.data.materials: me.materials.append(m)
    o = bpy.data.objects.new(name, me); col.objects.link(o); print("PARTE %s: %d fete, muchii libere %d" % (name, len(me.polygons), fb)); return o
part("orig_PS_sus", True, DZ, XE - XS); part("orig_PS_jos", False, 0.0, XE - XS)
def edges(name, dz, dx):
    V = []; E = []
    for p, q in seam: V += [(p.x + dx, p.y, p.z + dz), (q.x + dx, q.y, q.z + dz)]; E.append((len(V) - 2, len(V) - 1))
    me = bpy.data.meshes.new(name); me.from_pydata(V, E, []); o = bpy.data.objects.new(name, me); col.objects.link(o)
    cu = o; m = bpy.data.materials.get("ghid_imbinare") or bpy.data.materials.new("ghid_imbinare"); m.diffuse_color = (1, 0.85, 0, 1)
    me.materials.append(m); mod = o.modifiers.new("w", "SKIN") if False else None; return o
edges("orig_PS_imbinare", 0.0, XE - XS); edges("orig_PS_imbinare_sus", DZ, XE - XS)
L = sum((p - q).length for p, q in seam)
print("IMBINARE: %d muchii comune sus/jos, %.0f m; fete sus %d, jos %d" % (len(seam), L, lab.sum(), (~lab).sum()))
for o in bpy.context.selected_objects: o.select_set(False)             # only the joint lines get converted (not whatever was selected)
for o in bpy.data.objects:
    if o.name.startswith("orig_PS_imbinare"):
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.object.convert(target="CURVE"); o.data.bevel_depth = 0.8; o.data.materials.clear(); o.data.materials.append(bpy.data.materials["ghid_imbinare"]); o.select_set(False)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
