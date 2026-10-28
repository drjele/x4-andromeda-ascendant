# The PS's components exploded, so each can be discussed on its own: copies of the reference pieces that make the PS (the
# body 169_C, plate 086, strips 103, nose strips 055, blades 118/117 and the deck decorations), moved beside the ship
# (x + DX), each pushed away from the deck's centre (sideways for the side pieces, upward for those on top) and labelled
# with its name; the body stays in place. Collection PS_EXPLODAT, the reference untouched.
# Usage: blender -b <file.blend> --python ps_explode.py -- <out.blend> <dx>
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, DX = a[0], float(a[1]); sc = bpy.context.scene
PIECES = ["R002 169_C", "R082 086_S", "R034 103_S", "R033 103_D", "R122 055_S", "R121 055_D", "R076 118_S", "R075 117_D",
          "R025 141_S", "R026 141_D", "R030 158_S", "R029 158_D", "R088 096_S", "R087 096_D", "R109 099_S", "R108 099_D",
          "R131 087_S", "R129 087_D", "R145 104_S", "R144 104_D", "R125 100_S", "R236 102_S", "R249 101_S"]
col = bpy.data.collections.get("PS_EXPLODAT") or bpy.data.collections.new("PS_EXPLODAT")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
C0 = Vector((0, 0, 290)); EXP = 1.0
for i, n in enumerate(PIECES):
    o = bpy.data.objects[n]; c = o.copy(); c.data = o.data.copy(); c.name = "expl_" + n; col.objects.link(c); c.hide_set(False); c.hide_render = False
    cen = sum((o.matrix_world @ Vector(b) for b in o.bound_box), Vector()) / 8
    off = Vector((DX, 0, 0))
    if n != "R002 169_C":
        d = cen - C0; side = Vector((d.x, 0, 0)); up = Vector((0, 0, 1))
        off += (side.normalized() * (320 + 90 * (i % 2)) if abs(d.x) > 60 else Vector()) + up * (160 + 110 * (i % 4))
        if n in ("R076 118_S", "R075 117_D"): off += side.normalized() * 200 + up * 150   # apart from the strips 103
    c.location = o.location + off
    t = bpy.data.curves.new("eticheta_" + n, "FONT"); t.body = n.split()[-1] + "  (" + n.split()[0] + ")"; t.size = 18; t.align_x = "CENTER"
    to = bpy.data.objects.new("eticheta_" + n, t); col.objects.link(to); to.location = cen + off + Vector((0, 0, 40))
    print("EXPL", n, "deplasat", tuple(round(v) for v in off))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
