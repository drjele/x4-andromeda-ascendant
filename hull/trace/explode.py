# Exploded view of a frozen version: every part copied (sharing its mesh) into an "explodat" collection, moved away by
# group (body decorations up/down, V plate high above, arms/links/upper wings sideways, U arch below), each with its label.
# Usage: blender <version.blend> --python explode.py -- <collection> <out.blend>
import bpy, sys
from mathutils import Vector
COL, OUT = sys.argv[sys.argv.index("--") + 1:][:2]
TOP = ["C22", "C1", "C2", "C4", "C16", "C3", "C12", "C13", "C13b", "C17", "C8", "C9", "C10"]
BELLY = ["C5", "C6", "C7", "C11", "C15", "C14"]
ARM = {"A1": (0, 0), "A2": (0, 0), "A10": (450, 0), "A3": (1050, 250), "A5": (1500, 0), "A6": (1050, -250), "A7": (1050, -600), "A9": (1500, 650)}
def offset(label, c):
    s = 1 if c.x >= 0 else -1
    if label == "C0": return Vector()
    if label in TOP: return Vector((0, 0, 250 + 110 * TOP.index(label)))
    if label in BELLY: return Vector((0, 0, -250 - 110 * BELLY.index(label)))
    if label[0] == "V": return Vector((0, 0, 1900 + 120 * int(label[1:])))
    if label in ARM: dx, dz = ARM[label]; return Vector((s * (900 + dx), 0, dz))
    if label[0] == "L": return Vector((s * 450, 0, 0))
    if label[0] == "H": return Vector((s * 450, 0, -500))
    if label[0] == "U": return Vector((s * 550, 0, 550))
    if label == "G1": return Vector((0, 0, -1300))
    if label == "G2": return Vector((0, 0, -1700))
    return Vector((0, 0, 0))
src = bpy.data.collections[COL]; ex = bpy.data.collections.new("explodat"); bpy.context.scene.collection.children.link(ex)
mat = bpy.data.materials.new("eticheta"); mat.diffuse_color = (1, 0.85, 0.2, 1)
for o in list(src.objects):
    if o.type != "MESH": continue
    name = o.name[len(COL) + 1:]; label = name.split()[0]
    c = o.matrix_world @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8)
    d = offset(label, c); n = o.copy(); n.name = f"x {name}"; n.matrix_world.translation += d; ex.objects.link(n)
    top = max((o.matrix_world @ Vector(b)).z for b in o.bound_box)
    t = bpy.data.curves.new(f"t {name}", "FONT"); t.body = name; t.size = 28; t.align_x = "CENTER"
    to = bpy.data.objects.new(f"t {name}", t); to.location = Vector((c.x, c.y, top + 15)) + d; to.data.materials.append(mat); ex.objects.link(to)
# grid: each part alone (the right one of a left/right pair), centred in its cell, rows by group, labelled underneath
gr = bpy.data.collections.new("grila"); bpy.context.scene.collection.children.link(gr); parts = []
for o in src.objects:
    name = o.name[len(COL) + 1:]
    if o.type == "MESH" and not name.endswith("_l") and "arm_l" not in name: parts.append((name, o))
key = lambda n: ("CVAGLHUW".index(n[0]) if n[0] in "CVAGLHUW" else 9, int("".join(ch for ch in n.split()[0][1:] if ch.isdigit()) or 0))
parts.sort(key=lambda p: key(p[0])); x = y = 0.0; row = None; rowh = 0.0; GAP = 150
for name, o in parts:
    W = [o.matrix_world @ Vector(b) for b in o.bound_box]; lo = Vector([min(v[i] for v in W) for i in range(3)]); hi = Vector([max(v[i] for v in W) for i in range(3)])
    if row is not None and (name[0] != row or x > 3500): x, y, rowh = 0.0, y - rowh - GAP - 80, 0.0
    row = name[0]; size = hi - lo; n = o.copy(); n.name = f"g {name}"; gr.objects.link(n)
    n.matrix_world.translation += Vector((x - lo.x, y - hi.y, -lo.z))
    t = bpy.data.curves.new(f"gt {name}", "FONT"); t.body = name; t.size = 30
    to = bpy.data.objects.new(f"gt {name}", t); to.location = (x, y - size.y - 50, 0); to.data.materials.append(mat); gr.objects.link(to)
    x += size.x + GAP; rowh = max(rowh, size.y)
for c in bpy.data.collections:
    if c is gr: bpy.context.view_layer.layer_collection.children[c.name].hide_viewport = True
    elif c is not ex: bpy.context.view_layer.layer_collection.children[c.name].hide_viewport = True
for a in (s for w in bpy.context.window_manager.windows for s in w.screen.areas if s.type == "VIEW_3D"):
    for sp in a.spaces:
        if sp.type == "VIEW_3D": sp.clip_start, sp.clip_end = 1, 60000
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("EXPLODED", len(ex.objects) // 2, "parts")
