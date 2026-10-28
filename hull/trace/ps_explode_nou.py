# Our deck (ps_punte) exploded next to the exploded reference, to compare component by component: a copy of ps_punte,
# every face labelled with the reference piece nearest to it (the pieces it was built from: body 169_C, plate 086, strips
# 103, nose strips 055, blades 118/117), split into one object per piece ("equivalent"), each moved by the same offset as
# that piece in ps_explode.py, the whole set at x = XN instead of beside the ship. The face label is kept as the integer
# face attribute "piesa" on the copy too. Collection PS_NOU_EXPLODAT; ps_punte itself untouched.
# Usage: blender -b <file.blend> --python ps_explode_nou.py -- <out.blend> <dx_ship> <x_explodat>
import bpy, bmesh, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, DXS, XN = a[0], float(a[1]), float(a[2]); sc = bpy.context.scene
PIECES = ["R002 169_C", "R082 086_S", "R034 103_S", "R033 103_D", "R122 055_S", "R121 055_D", "R076 118_S", "R075 117_D"]
ALLP = ["R002 169_C", "R082 086_S", "R034 103_S", "R033 103_D", "R122 055_S", "R121 055_D", "R076 118_S", "R075 117_D",
        "R025 141_S", "R026 141_D", "R030 158_S", "R029 158_D", "R088 096_S", "R087 096_D", "R109 099_S", "R108 099_D",
        "R131 087_S", "R129 087_D", "R145 104_S", "R144 104_D", "R125 100_S", "R236 102_S", "R249 101_S"]   # ps_explode.py order
C0 = Vector((0, 0, 290))
def offset(n):                                                          # same rule as ps_explode.py
    i = ALLP.index(n); o = bpy.data.objects[n]; cen = sum((o.matrix_world @ Vector(b) for b in o.bound_box), Vector()) / 8
    if n == "R002 169_C": return Vector(), cen
    d = cen - C0; side = Vector((d.x, 0, 0))
    off = (side.normalized() * (320 + 90 * (i % 2)) if abs(d.x) > 60 else Vector()) + Vector((0, 0, 1)) * (160 + 110 * (i % 4))
    if n in ("R076 118_S", "R075 117_D"): off += side.normalized() * 200 + Vector((0, 0, 150))   # apart from the strips 103
    return off, cen
trees = []
for n in PIECES:
    o = bpy.data.objects[n]; bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); trees.append(BVHTree.FromBMesh(bm)); bm.free()
src = bpy.data.objects["ps_punte"]; me = src.data.copy(); M = src.matrix_world
lab = []
for p in me.polygons:
    c = M @ p.center - Vector((DXS, 0, 0)); best = min(range(len(trees)), key=lambda j: (trees[j].find_nearest(c)[3] or 1e9)); lab.append(best)
at = me.attributes.new("piesa", "INT", "FACE"); at.data.foreach_set("value", lab)
col = bpy.data.collections.get("PS_NOU_EXPLODAT") or bpy.data.collections.new("PS_NOU_EXPLODAT")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
for j, n in enumerate(PIECES):
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); L = bm.faces.layers.int["piesa"]
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[L] != j], context="FACES")
    if not bm.faces: bm.free(); print("GOL", n); continue
    m2 = bpy.data.meshes.new("echiv_" + n); bm.to_mesh(m2); bm.free()
    for m_ in me.materials: m2.materials.append(m_)                       # keep the transferred textures
    o = bpy.data.objects.new("echiv_" + n, m2); col.objects.link(o); o.matrix_world = M.copy()
    off, cen = offset(n); o.location = M.translation + Vector((XN - DXS, 0, 0)) + off
    t = bpy.data.curves.new("et_" + n, "FONT"); t.body = "nou " + n.split()[-1]; t.size = 18; t.align_x = "CENTER"
    to = bpy.data.objects.new("et_nou_" + n, t); col.objects.link(to); to.location = cen + Vector((XN, 0, 40)) + off
    print("ECHIV %-12s %6d fete, deplasat %s" % (n, len(m2.polygons), tuple(round(v) for v in off)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)
