# The welded guides copied to their assembled places at x XA (explode offsets taken off) and welded into one object,
# g_asamblat_ghidaje_sudate (collection GHIDAJE_ASAMBLATE); an old one is replaced. The originals are left as they are.
# Usage: blender -b <in> --python asambleaza_ghidaje.py -- <out.blend> [XA=-7700]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; X = float(a[1]) if len(a) > 1 else -7700.0
for o in [o for o in bpy.data.objects if o.name.startswith("g_asamblat_")]: bpy.data.objects.remove(o)
plan = {"g_psr_sep_ghidaje_sudate": (X + 6000, 0, 0), "g_cap_sep_ghidaje_sudate": (X + 6000, 0, -90), "g_car_sep_ghidaje_sudate": (X + 6000, 0, 110),
        "g_rama_sep_ghidaje_sudate": (X + 5450, 0, 0)}
for o in bpy.data.objects:
    if o.name.startswith("g_br_sep_"): plan[o.name] = (X + 6000 + (-80 if ("_D_" in o.name or o.name.endswith("_D")) else 80), 120, 0)
    if o.name.startswith("g_ure_sep_"): plan[o.name] = (X + 6000 + (-70 if o.name.endswith("_D") else 70), 0, 75)
c = bpy.data.collections.get("GHIDAJE_ASAMBLATE") or bpy.data.collections.new("GHIDAJE_ASAMBLATE")
if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
cp = []
for n, d in plan.items():
    o = bpy.data.objects.get(n)
    if o is None: continue
    k = o.copy(); k.data = o.data.copy(); c.objects.link(k); k.hide_set(False); k.matrix_world = o.matrix_world.copy(); k.location += Vector(d); cp.append(k)
bpy.context.view_layer.update(); bpy.ops.object.select_all(action="DESELECT")
for k in cp: k.select_set(True)
bpy.context.view_layer.objects.active = cp[0]; bpy.ops.object.join(); j = bpy.context.view_layer.objects.active; j.name = "g_asamblat_ghidaje_sudate"
print("ASAMBLATE %d ghidaje -> %s (%d linii) la x %.0f" % (len(cp), j.name, len(j.data.splines), X))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
