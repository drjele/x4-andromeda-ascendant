# A separate copy of some collection's objects (asked: the PS part and its legs also on their own, to finish that part):
# linked copies (same mesh data, nothing heavier) of every object of SRC put in the collection DEST, moved by DX in x.
# Usage: blender -b <f.blend> --python copie_separata.py -- <out.blend> <src collection> <dest collection> <dx>
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT, SRC, DEST, DX = a[0], a[1], a[2], float(a[3]); sc = bpy.context.scene
d = bpy.data.collections.get(DEST) or bpy.data.collections.new(DEST)
if d.name not in sc.collection.children: sc.collection.children.link(d)
for o in list(d.objects): bpy.data.objects.remove(o)
for o in bpy.data.collections[SRC].objects:
    c = o.copy(); c.name = "sep_" + o.name; d.objects.link(c); c.location.x += DX; print("COPIE", c.name, "x %+.0f" % DX)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
