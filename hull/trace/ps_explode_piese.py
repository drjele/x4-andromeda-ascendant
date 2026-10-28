# The new PS pieces exploded next to the exploded reference, each with the offset of its reference counterpart (same
# rule as ps_explode.py), so the two sets can be compared piece by piece: copies of the visible pieces of PS_PIESE (and
# the launch tube placeholders) in PS_NOU_EXPLODAT2 at x = XN (the reference set is at XR); the assembled pieces untouched.
# Usage: blender -b <file.blend> --python ps_explode_piese.py -- <out.blend> <dx_ship> <x_ref> <x_new>
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, DXS, XR, XN = a[0], float(a[1]), float(a[2]), float(a[3]); sc = bpy.context.scene
PAIR = {"169_C": "R002 169_C", "086": "R082 086_S", "launchtube": "R082 086_S", "103_118_S": "R034 103_S", "103_118_D": "R033 103_D", "055_S": "R122 055_S", "055_D": "R121 055_D"}
def ref_off(n):                                                         # the reference piece's offset in the exploded reference
    e = bpy.data.objects.get("expl_" + n); o = bpy.data.objects[n]
    return e.location - o.location - Vector((XR, 0, 0)) if e else Vector()
col = bpy.data.collections.get("PS_NOU_EXPLODAT2") or bpy.data.collections.new("PS_NOU_EXPLODAT2")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
src = list({o.name: o for o in [o for o in bpy.data.collections["PS_PIESE"].objects if not o.hide_get()] + [o for o in sc.objects if o.name.startswith("launchtube_s_")]}.values())
for o in src:
    key = next((k for k in PAIR if k in o.name), None); off = ref_off(PAIR[key]) if key else Vector((0, 0, -150))   # the belly V: below
    c = o.copy(); c.data = o.data.copy(); c.name = "expl_" + o.name; col.objects.link(c); c.location = o.location + Vector((XN - DXS, 0, 0)) + off
    print("EXPL NOU %-28s deplasare %s (pereche %s)" % (o.name, tuple(round(v) for v in off), PAIR.get(key, "-")))
lc = bpy.context.view_layer.layer_collection.children
for n in ("PS_EXPLODAT", "PS_NOU_EXPLODAT2"):
    if n in lc: lc[n].exclude = False
if "PS_NOU_EXPLODAT" in lc: lc["PS_NOU_EXPLODAT"].exclude = True
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
