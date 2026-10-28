# The new PS shown complete next to its exploded view (asked: every time both - assembled and exploded): the new body pieces
# (PS_PIESE_NOI) and the PS components (PS_PIESE: hood, front, shoulders, 055, belly V, launch tubes - not the old body) copied
# into PS_ASAMBLAT_NOU at x = XA, in place relative to each other (assembled); the exploded set stays: the new pieces at the
# new piece's spot and the components' exploded copies (PS_NOU_EXPLODAT2, the old body's left hidden). Copies share data.
# Usage: blender -b <f.blend> --python asamblat_langa.py -- <out.blend> [xa]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; XA = float(a[1]) if len(a) > 1 else 9100.0; sc = bpy.context.scene
en, on = bpy.data.objects["expl_piesa_comp_169_C"], bpy.data.objects["piesa_comp_169_C"]; XN = -1700.0 + (en.location.x - on.location.x)
col = bpy.data.collections.get("PS_ASAMBLAT_NOU") or bpy.data.collections.new("PS_ASAMBLAT_NOU")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
new = [o for o in bpy.data.collections["PS_PIESE_NOI"].objects if o.visible_get()]
comp = [o for o in bpy.data.collections["PS_PIESE"].objects if "169_C" not in o.name and "103_118" not in o.name and not o.hide_get()] + [o for o in sc.objects if o.name.startswith("launchtube_s_")]
comp = list({o.name: o for o in comp}.values())
for o in new:                                                           # the new pieces: their spot XN -> XA
    c = o.copy(); c.name = "asm_" + o.name; col.objects.link(c); c.location.x += XA - XN
for o in comp:                                                          # the components: built at the ship's -1700 -> XA
    c = o.copy(); c.name = "asm_" + o.name; col.objects.link(c); c.location.x += XA - (-1700.0)
lc = bpy.context.view_layer.layer_collection.children
if "PS_NOU_EXPLODAT2" in lc: lc["PS_NOU_EXPLODAT2"].exclude = False
for o in bpy.data.collections.get("PS_NOU_EXPLODAT2").objects if bpy.data.collections.get("PS_NOU_EXPLODAT2") else []:
    if "169_C" in o.name: o.hide_set(True); o.hide_render = True
print("ASAMBLAT la x %.0f: %d piese noi + %d componente (%s)" % (XA, len(new), len(comp), ", ".join(sorted(o.name for o in comp))))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
