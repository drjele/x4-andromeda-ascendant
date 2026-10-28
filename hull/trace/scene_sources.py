# One Blender scene with the three sources side by side in the same world frame: our current model (V17, its parts in
# their collections), the external model aligned to it (Binkley-Piratepants, Sketchfab, CC BY), the user's confirmed
# outlines as curves on the faces of the proportion box (one collection per view), plus a text object with the credits.
# Usage: blender -b <V17.blend> --python scene_sources.py -- <binkley.obj> <contururi_3d.json> <out.blend> [moreno.obj]
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]; OBJ, CJ, OUT = a[:3]; MOR = a[3] if len(a) > 3 else None
def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
    return c
v17 = coll("SURSA_1_V17")
for o in list(bpy.context.scene.collection.objects):
    if o.type == "MESH": bpy.context.scene.collection.objects.unlink(o); v17.objects.link(o)
for c in list(bpy.context.scene.collection.children):
    if c.name not in ("SURSA_1_V17",) and not c.name.startswith(("SURSA", "CONTURURI")): bpy.context.scene.collection.children.unlink(c); v17.children.link(c)
bk = coll("SURSA_2_Binkley-Piratepants_CC-BY")
bpy.ops.wm.obj_import(filepath=OBJ, forward_axis="Y", up_axis="Z")                 # the OBJ is already in the world frame (z up)
for o in bpy.context.selected_objects:
    for c in o.users_collection: c.objects.unlink(o)
    bk.objects.link(o); o.name = "binkley_nava"
    m = bpy.data.materials.new("binkley"); m.diffuse_color = (1, 0.3, 1, 0.5); o.data.materials.append(m)
mo = coll("SURSA_3_morenostefanuto_Sketchfab" if MOR else "SURSA_3_morenostefanuto (de descarcat)")
if MOR:
    bpy.ops.wm.obj_import(filepath=MOR, forward_axis="Y", up_axis="Z"); mm = bpy.data.materials.new("moreno"); mm.diffuse_color = (0.2, 1, 0.9, 0.5)
    for o in bpy.context.selected_objects:
        for c in o.users_collection: c.objects.unlink(o)
        mo.objects.link(o); o.data.materials.clear(); o.data.materials.append(mm)
cc = coll("CONTURURI_confirmate")
cols = {"top": (1, 0.85, 0, 1), "bottom": (0.4, 1, 0.4, 1), "side": (1, 0.5, 1, 1), "back": (0.2, 0.8, 1, 1), "front": (1, 0.6, 0.2, 1)}
for view, lines in json.load(open(CJ)).items():
    sub = bpy.data.collections.new("contur_" + view); cc.children.link(sub)
    cu = bpy.data.curves.new("contur_" + view, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 3
    for l in lines:
        sp = cu.splines.new("POLY"); sp.points.add(len(l) - 1)
        for i, p in enumerate(l): sp.points[i].co = (p[0], p[1], p[2], 1)
    ob = bpy.data.objects.new("contur_" + view, cu); sub.objects.link(ob)
    m = bpy.data.materials.new("contur_" + view); m.diffuse_color = cols[view]; cu.materials.append(m)
t = bpy.data.curves.new("credite", "FONT"); t.body = "Surse: V17 (noi), Binkley-Piratepants (Sketchfab, CC BY), morenostefanuto (Sketchfab), DJPicasso (Printables, CC BY-SA), grannyte (original)"
to = bpy.data.objects.new("credite", t); to.location = (-700, -1700, 0); to.scale = (40, 40, 40); bpy.context.scene.collection.objects.link(to)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
