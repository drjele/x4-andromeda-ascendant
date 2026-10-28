# The exploded pieces laid side by side from the biggest to the smallest, to go through them one by one: pieces sorted by
# their size (bounding box diagonal), packed in rows (left to right, rows going down in y) with a gap; each move added to
# the piece's "explode_offset" so assemble_parts.py still puts it back exactly; the number label moved over it; each
# piece renamed with its rank in front ("R001 095_S"), so the Outliner lists them in size order.
# Usage: blender -b <exploded.blend> --python layout_parts.py -- <out.blend> [row_width_m] [gap_m] [delete names...]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; ROW = float(a[1]) if len(a) > 1 else 6000; GAP = float(a[2]) if len(a) > 2 else 60; DEL = a[3:]
for n in DEL:
    for o in [o for o in bpy.data.objects if o.name.split(" ")[-1] in (n, "e_" + n) or o.name in (n, "e_" + n)]: bpy.data.objects.remove(o)
parts = [o for o in bpy.data.objects if o.type == "MESH" and "explode_offset" in o]
def box(o):
    vs = [o.matrix_world @ Vector(b) for b in o.bound_box]; lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)]); return lo, hi
info = {o: box(o) for o in parts}; parts.sort(key=lambda o: -(info[o][1] - info[o][0]).length)
x = y = 0.0; row_h = 0.0
for rank, o in enumerate(parts, 1):
    lo, hi = info[o]; w, h = hi.x - lo.x, hi.y - lo.y
    if x > 0 and x + w > ROW: x = 0.0; y -= row_h + GAP * 3; row_h = 0.0
    target = Vector((x - lo.x, y - hi.y, -lo.z)); o.location += target; o["explode_offset"] = list(Vector(o["explode_offset"]) + target)
    base = o.name.split(" ")[-1]; o.name = "R%03d %s" % (rank, base); o["rang"] = rank
    lab = bpy.data.objects.get("e_" + base)
    if lab: lab.location = Vector((x + w / 2, y + 10, hi.z - lo.z + 20)); lab.data.body = "R%03d  %s" % (rank, base); lab.scale = (max(10, min(60, w / 8)),) * 3
    x += w + GAP; row_h = max(row_h, h)
print("ASEZATE %d piese de la mare la mic; sterse: %s" % (len(parts), " ".join(DEL)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
