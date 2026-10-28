# The exploded pieces put back: every object carrying "explode_offset" moved back by it (exact original place), the
# number labels removed, and, if asked, the pieces joined into one object again.
# Usage: blender -b <exploded.blend> --python assemble_parts.py -- <out.blend> [join_name]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; JOIN = a[1] if len(a) > 1 else None
back = []
for o in bpy.data.objects:
    if "explode_offset" in o: o.location -= Vector(o["explode_offset"]); del o["explode_offset"]; back.append(o)
for o in list(bpy.data.objects):
    if o.name.startswith("e_") and o.type == "FONT": bpy.data.objects.remove(o)
if JOIN and back:
    bpy.ops.object.select_all(action="DESELECT")
    for o in back: o.select_set(True)
    bpy.context.view_layer.objects.active = back[0]; bpy.ops.object.join(); bpy.context.view_layer.objects.active.name = JOIN
print("ASAMBLAT", len(back)); bpy.ops.wm.save_as_mainfile(filepath=OUT)
