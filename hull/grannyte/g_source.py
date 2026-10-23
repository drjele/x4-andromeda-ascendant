# Put grannyte's original hull in the working scene as the reference "source", scaled and centred
# exactly as andromeda_import.normalize does; the earlier edited hull stays as "source_edited".
import bpy
from mathutils import Vector
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
bpy.ops.wm.open_mainfile(filepath=f"{D}/seg/source.blend")
sc = bpy.data.scenes["seg"]; bpy.context.window.scene = sc
old = sc.objects.get("source")
if old is not None and "source_edited" not in sc.objects:
    old.name = "source_edited"; old.hide_render = True
elif old is not None:
    bpy.data.objects.remove(old)
before = set(bpy.data.objects)
bpy.ops.wm.obj_import(filepath="/home/adrian/x4mod/source/XMC.obj", forward_axis="Y", up_axis="Z")
new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
for o in new:
    if o.name not in sc.collection.all_objects: sc.collection.objects.link(o)
bpy.ops.object.select_all(action="DESELECT")
for o in new: o.select_set(True)
bpy.context.view_layer.objects.active = new[0]
if len(new) > 1: bpy.ops.object.join()
g = bpy.context.view_layer.objects.active; g.name = "source"; g.data.name = "source"
co = [v.co for v in g.data.vertices]
low = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co))); high = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
f = 2700.0 / (high.y - low.y); cen = (low + high) * 0.5
for v in g.data.vertices: v.co = (v.co - cen) * f
g.data.update(); g.data.materials.clear()
print("GRANNYTE", len(g.data.vertices), "scale", round(f, 4), [round(a) for a in ((low - cen) * f)], [round(a) for a in ((high - cen) * f)])
bpy.ops.wm.save_mainfile()
