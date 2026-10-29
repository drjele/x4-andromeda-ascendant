# Objects moved into their own collection, excluded from the view (kept in the file for later, back with one tick).
# Usage: blender -b <f.blend> --python muta_ascunde.py -- <out.blend> <collection> <object> ...
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT, COL = a[0], a[1]; sc = bpy.context.scene
c = bpy.data.collections.get(COL) or bpy.data.collections.new(COL)
if c.name not in sc.collection.children: sc.collection.children.link(c)
for n in a[2:]:
    o = bpy.data.objects[n]
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o); print("MUTAT", n, "->", COL)
def walk(lc):
    for ch in lc.children:
        if ch.name == COL: ch.exclude = True
        walk(ch)
walk(bpy.context.view_layer.layer_collection); bpy.ops.wm.save_as_mainfile(filepath=OUT)
