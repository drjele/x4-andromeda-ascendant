# A ship mesh made of many loose pieces exploded into named objects for the user to pick from: every connected piece
# separated; pieces of at least MIN_FACES faces become their own objects, numbered from bow to stern, a left piece and
# its mirror twin (mirrored centroid and similar face count) sharing the number (S = left, D = right, C = on the centre
# line); the tiny ones joined per zone (bow / middle / stern x left / centre / right). Each object then moved away from the
# ship's centre by FACTOR times its centroid offset, the move stored on the object ("explode_offset") so assemble_parts.py
# puts everything back exactly; a number label floats over each piece. Collections: piese_mari, piese_medii, marunte.
# Usage: blender -b <in.blend> --python explode_parts.py -- <object> <out.blend> [min_faces] [factor]
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; NAME, OUT = a[0], a[1]; MINF = int(a[2]) if len(a) > 2 else 100; FACTOR = float(a[3]) if len(a) > 3 else 0.6
sc = bpy.context.scene; src = bpy.data.objects[NAME]
bpy.ops.object.select_all(action="DESELECT"); src.select_set(True); bpy.context.view_layer.objects.active = src
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.separate(type="LOOSE"); bpy.ops.object.mode_set(mode="OBJECT")
parts = [o for o in bpy.context.selected_objects if o.type == "MESH"]
def info(o):
    me = o.data; c = sum((o.matrix_world @ v.co for v in me.vertices), Vector()) / max(len(me.vertices), 1); return c, len(me.polygons)
data = {o: info(o) for o in parts}
allc = [c for c, _ in data.values()]; ys = [c.y for c in allc]; xs = [c.x for c in allc]; zs = [c.z for c in allc]
centre = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)); L = max(ys) - min(ys)
def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
cm, cmed, cs = coll("piese_mari"), coll("piese_medii"), coll("marunte")
def move_to(o, c):
    for x in o.users_collection: x.objects.unlink(o)
    c.objects.link(o)
big = [o for o in parts if data[o][1] >= MINF]; tiny = [o for o in parts if data[o][1] < MINF]
# numbering bow (+y) to stern, twins paired
big.sort(key=lambda o: -data[o][0].y); used = set(); num = 0; names = []
for o in big:
    if o in used: continue
    c, n = data[o]; num += 1; used.add(o)
    if abs(c.x - centre.x) < 3: o.name = "%03d_C" % num; names.append(o); continue
    want = Vector((2 * centre.x - c.x, c.y, c.z)); twin = None; best = 1e9
    for p in big:
        if p in used: continue
        cp, np_ = data[p]; d = (cp - want).length
        if d < best and abs(np_ - n) <= max(4, 0.15 * n): best, twin = d, p
    side = "S" if c.x < centre.x else "D"; o.name = "%03d_%s" % (num, side); names.append(o)
    if twin is not None and best < max(15.0, 0.02 * L): used.add(twin); twin.name = "%03d_%s" % (num, "D" if side == "S" else "S"); names.append(twin)
for o in names: move_to(o, cm if data[o][1] >= 1000 else cmed)
# tiny pieces joined per zone
zones = {}
for o in tiny:
    c, _ = data[o]; t = (c.y - min(ys)) / max(L, 1e-6); zy = "pupa" if t < 1 / 3 else ("mijloc" if t < 2 / 3 else "prova")
    zx = "C" if abs(c.x - centre.x) < 3 else ("S" if c.x < centre.x else "D"); zones.setdefault((zy, zx), []).append(o)
for (zy, zx), obs in zones.items():
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.join(); j = bpy.context.view_layer.objects.active
    j.name = "marunte_%s_%s" % (zy, zx); move_to(j, cs); data[j] = info(j)
# explode, offset stored; labels
lab = coll("etichete")
for o in [o for o in sc.objects if o.type == "MESH" and any(c.name in ("piese_mari", "piese_medii", "marunte") for c in o.users_collection)]:
    c, _ = data.get(o) or info(o); off = (c - centre) * FACTOR; o.location += off; o["explode_offset"] = list(off)
    if not o.name.startswith("marunte"):
        t = bpy.data.curves.new("e_" + o.name, "FONT"); t.body = o.name; t.align_x = "CENTER"; to = bpy.data.objects.new("e_" + o.name, t)
        lab.objects.link(to); to.location = c + off + Vector((0, 0, 25)); to.scale = (12, 12, 12)
print("EXPLODAT: %d piese numerotate (%d numere), %d marunte in %d zone" % (len(names), num, len(tiny), len(zones)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
