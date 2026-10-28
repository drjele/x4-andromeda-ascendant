# The PS assembled from its confirmed components: copies of the comp_* objects of PS_NOU_EXPLODAT brought back to their
# place on the ship (the exploded offset removed: they were built in ship coordinates), kept as separate hidden pieces in
# PS_PIESE (undo / explode again), and joined into one object PS with the integer face attribute "piesa" (index into the
# custom property "piese" = the component names), so the joined object can be separated again by that attribute. The
# replaced parts (ps_punte, ps_tub_*) hidden. Collection PS_ASAMBLAT; the exploded set untouched.
# Usage: blender -b <file.blend> --python ps_asamblare.py -- <out.blend>
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
def coll(n):
    c = bpy.data.collections.get(n) or bpy.data.collections.new(n)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
ca, cp = coll("PS_ASAMBLAT"), coll("PS_PIESE")
for c in (ca, cp):
    for o in list(c.objects): bpy.data.objects.remove(o)
src = [o for o in bpy.data.collections["PS_NOU_EXPLODAT"].objects if o.name.startswith("comp_") and not o.hide_get() and o.type == "MESH"]
names = sorted(o.name for o in src); copies = []
for o in sorted(src, key=lambda o: o.name):
    c = o.copy(); c.data = o.data.copy(); c.location = (0, 0, 0); c.name = "piesa_" + o.name; cp.objects.link(c)
    at = c.data.attributes.get("piesa") or c.data.attributes.new("piesa", "INT", "FACE")
    at.data.foreach_set("value", [names.index(o.name)] * len(c.data.polygons)); copies.append(c)
bpy.ops.object.select_all(action="DESELECT")
js = []
for c in copies:
    j = c.copy(); j.data = c.data.copy(); ca.objects.link(j); j.hide_set(False); j.select_set(True); js.append(j)
bpy.context.view_layer.objects.active = js[0]; bpy.ops.object.join(); ps = bpy.context.view_layer.objects.active; ps.name = "PS"; ps["piese"] = names
for c in copies: c.hide_set(True); c.hide_render = True
for n in ("ps_punte", "ps_tub_S", "ps_tub_D"):
    o = bpy.data.objects.get(n)
    if o: o.hide_set(True); o.hide_render = True
bpy.context.view_layer.layer_collection.children["PS_NOU_EXPLODAT"].exclude = True
print("PS ASAMBLAT: %d componente (%s), %d varfuri, %d fete" % (len(names), ", ".join(n[5:] for n in names), len(ps.data.vertices), len(ps.data.polygons)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
